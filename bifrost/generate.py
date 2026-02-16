from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import yaml
from rich.console import Console
from sqlalchemy import create_engine, text

from bifrost.load import engine_from_env, ensure_schema, truncate_raw

console = Console()

UTC = timezone.utc

def sha1_row(*parts: Any) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts).encode("utf-8")
    return hashlib.sha1(raw).hexdigest()

@dataclass
class TeamCfg:
    name: str
    status_palette: List[str]

@dataclass
class Cfg:
    seed: int
    time_window_days: int
    start_date: str
    teams: List[TeamCfg]
    projects: List[str]
    n_issues: int
    mess: Dict[str, float]

def load_cfg(path: str = "bifrost/config.yml") -> Cfg:
    data = yaml.safe_load(Path(path).read_text())
    teams = [TeamCfg(**t) for t in data["teams"]]
    return Cfg(
        seed=int(data["seed"]),
        time_window_days=int(data["time_window_days"]),
        start_date=str(data["start_date"]),
        teams=teams,
        projects=list(data["projects"]),
        n_issues=int(data["n_issues"]),
        mess=dict(data["mess"]),
    )

def dt_range(cfg: Cfg) -> Tuple[datetime, datetime]:
    start = datetime.fromisoformat(cfg.start_date).replace(tzinfo=UTC)
    end = start + timedelta(days=cfg.time_window_days)
    return start, end

def choose_weighted(rng: random.Random, items: List[str], weights: List[float]) -> str:
    return rng.choices(items, weights=weights, k=1)[0]

def gen_issues(cfg: Cfg, rng: random.Random) -> pd.DataFrame:
    start, end = dt_range(cfg)
    issue_types = ["Story", "Bug", "Task", "Spike"]
    priorities = ["P0", "P1", "P2", "P3"]
    reporters = [f"user_{i:03d}" for i in range(1, 61)]
    assignees = [f"eng_{i:03d}" for i in range(1, 46)]

    rows = []
    for i in range(1, cfg.n_issues + 1):
        team = rng.choice(cfg.teams).name
        project = rng.choice(cfg.projects)
        created_at = start + timedelta(seconds=rng.randint(0, int((end - start).total_seconds())))
        issue_type = choose_weighted(rng, issue_types, [0.55, 0.25, 0.15, 0.05])
        priority = choose_weighted(rng, priorities, [0.08, 0.22, 0.45, 0.25])

        assignee = None if rng.random() < cfg.mess["missing_assignee_rate"] else rng.choice(assignees)
        estimate = None if rng.random() < cfg.mess["missing_estimate_rate"] else int(rng.choice([1,2,3,5,8,13]))

        issue_key = f"{project}-{i}"
        summary = f"{issue_type} {issue_key} synthetic"

        resolved_at = None  # mismatch with transactions are possible

        source_hash = sha1_row(i, issue_key, project, team, issue_type, priority, created_at, assignee, estimate)

        rows.append(
            dict(
                issue_id=i,
                issue_key=issue_key,
                project_key=project,
                team=team,
                issue_type=issue_type,
                priority=priority,
                created_at=created_at,
                resolved_at=resolved_at,
                assignee=assignee,
                reporter=rng.choice(reporters),
                estimate_points=estimate,
                summary=summary,
                source_hash=source_hash,
            )
        )

    df = pd.DataFrame(rows)
    return df

def gen_sprints(cfg: Cfg, rng: random.Random) -> pd.DataFrame:
    start, end = dt_range(cfg)

    # 2-week sprints, per team
    sprint_len = timedelta(days=14)
    rows = []
    sid = 1
    for team in cfg.teams:
        t = start
        n = 1
        while t + sprint_len <= end:
            s_start = t
            s_end = t + sprint_len
            sprint_name = f"{team.name} Sprint {n:02d}"
            goal = None if rng.random() < 0.3 else f"Ship increment {n:02d}"
            rows.append(
                dict(
                    sprint_id=sid,
                    team=team.name,
                    sprint_name=sprint_name,
                    start_at=s_start,
                    end_at=s_end,
                    goal=goal,
                    source_hash=sha1_row(sid, team.name, sprint_name, s_start, s_end, goal),
                )
            )
            sid += 1
            n += 1
            t = s_end
    return pd.DataFrame(rows)

def gen_transitions_and_membership(cfg: Cfg, rng: random.Random, issues: pd.DataFrame, sprints: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    start, end = dt_range(cfg)

    canonical_path = ["todo", "in_progress", "review", "done"]

    team_palette = {t.name: t.status_palette for t in cfg.teams}

    def team_label(team: str, canon: str) -> str:
        pal = team_palette[team]

        candidates = {
            "todo": [x for x in pal if x.lower() in ("to do","backlog","ready")],
            "in_progress": [x for x in pal if x.lower() in ("in progress","doing","dev")],
            "review": [x for x in pal if "review" in x.lower() or x.lower() in ("qa","test")],
            "done": [x for x in pal if x.lower() in ("done","shipped","complete")],
            "blocked": [x for x in pal if "block" in x.lower() or x.lower() in ("impeded",)],
        }.get(canon, [])

        if candidates:
            return rng.choice(candidates)
        return rng.choice(pal)

    transitions = []
    memberships = []
    blockers = []

    # sprint lookup per team
    sprints_by_team = {t: df.reset_index(drop=True) for t, df in sprints.groupby("team")}

    for row in issues.itertuples(index=False):
        issue_id = int(row.issue_id)
        team = str(row.team)
        created_at: datetime = row.created_at

        # decide if duplicate issue exists
        is_dup = rng.random() < cfg.mess["duplicate_rate"]
        # decide if done without clean in_progress path
        skip_in_progress = rng.random() < cfg.mess["done_without_in_progress_rate"]
        # decide if reopened
        will_reopen = rng.random() < cfg.mess["reopen_rate"]

        # base timeline
        t = created_at + timedelta(hours=rng.randint(1, 72))

        # status drift
        def maybe_drift(label: str) -> str:
            if rng.random() < cfg.mess["status_drift_rate"]:
                return rng.choice([f"Custom:{label}", f"{label}*", f"{label} (legacy)"])
            return label

        path = ["todo", "in_progress", "review", "done"]
        if skip_in_progress:
            path = ["todo", "review", "done"]

        prev = None
        churn_events = rng.randint(0, 3)  # small churn
        canon_labels = []
        for canon in path:
            lbl = maybe_drift(team_label(team, canon))
            canon_labels.append(lbl)

        # create transitions
        for i, lbl in enumerate(canon_labels):
            transitions.append(
                dict(
                    issue_id=issue_id,
                    from_status=prev,
                    to_status=lbl,
                    changed_at=t,
                    actor=None if rng.random() < 0.2 else f"eng_{rng.randint(1,45):03d}",
                    source_hash=sha1_row(issue_id, prev, lbl, t),
                )
            )
            prev = lbl
            # advance time by 4-72 hours, with some randomness
            t += timedelta(hours=rng.randint(4, 72))

        # bounce between review and in-progress
        for _ in range(churn_events):
            if t >= end:
                break
            a = maybe_drift(team_label(team, "in_progress"))
            b = maybe_drift(team_label(team, "review"))
            transitions.append(dict(issue_id=issue_id, from_status=prev, to_status=a, changed_at=t, actor=None, source_hash=sha1_row(issue_id, prev, a, t)))
            prev = a
            t += timedelta(hours=rng.randint(2, 24))
            transitions.append(dict(issue_id=issue_id, from_status=prev, to_status=b, changed_at=t, actor=None, source_hash=sha1_row(issue_id, prev, b, t)))
            prev = b
            t += timedelta(hours=rng.randint(2, 24))

        # reopen after done, goes back to in progress, then to done again
        if will_reopen and t + timedelta(hours=24) < end:
            done_lbl = maybe_drift(team_label(team, "done"))
            # ensure a done exists as prev else push one
            if prev != done_lbl:
                transitions.append(dict(issue_id=issue_id, from_status=prev, to_status=done_lbl, changed_at=t, actor=None, source_hash=sha1_row(issue_id, prev, done_lbl, t)))
                prev = done_lbl
                t += timedelta(hours=rng.randint(6, 48))

            back_lbl = maybe_drift(team_label(team, "in_progress"))
            transitions.append(dict(issue_id=issue_id, from_status=prev, to_status=back_lbl, changed_at=t, actor=None, source_hash=sha1_row(issue_id, prev, back_lbl, t)))
            prev = back_lbl
            t += timedelta(hours=rng.randint(6, 72))
            transitions.append(dict(issue_id=issue_id, from_status=prev, to_status=done_lbl, changed_at=t, actor=None, source_hash=sha1_row(issue_id, prev, done_lbl, t)))
            prev = done_lbl
            t += timedelta(hours=rng.randint(1, 48))

        # Chooses sprint that overlaps created_at
        team_sprints = sprints_by_team[team]
        # picks a sprint near created time
        candidates = team_sprints[(team_sprints["start_at"] <= created_at) & (team_sprints["end_at"] >= created_at)]
        if candidates.empty:
            candidates = team_sprints.iloc[[0]]

        sprint = candidates.sample(1, random_state=rng.randint(0, 10_000)).iloc[0]
        sprint_id = int(sprint["sprint_id"])
        added_at = created_at + timedelta(days=rng.randint(0, 5))
        # mid-sprint add rate
        if rng.random() < cfg.mess["mid_sprint_add_rate"]:
            added_at = sprint["start_at"] + timedelta(days=rng.randint(3, 10))

        removed_at = None
        if rng.random() < 0.08:
            removed_at = added_at + timedelta(days=rng.randint(1, 10))

        memberships.append(
            dict(
                issue_id=issue_id,
                sprint_id=sprint_id,
                added_at=added_at,
                removed_at=removed_at,
                source_hash=sha1_row(issue_id, sprint_id, added_at, removed_at),
            )
        )

        # some issues have blocked windows
        if rng.random() < 0.22:
            b_start = created_at + timedelta(days=rng.randint(1, 25))
            b_dur_h = rng.randint(6, 120)
            b_end = b_start + timedelta(hours=b_dur_h)
            # late logging
            logged_at = b_start + timedelta(hours=rng.randint(0, 72))
            if rng.random() < cfg.mess["late_blocker_log_rate"]:
                logged_at = b_start + timedelta(hours=rng.randint(24, 168))

            blockers.append(
                dict(
                    issue_id=issue_id,
                    reason=rng.choice(["Dependency", "Awaiting approval", "Env outage", "Spec unclear", "External vendor"]),
                    blocked_start=b_start,
                    blocked_end=b_end if rng.random() < 0.9 else None,
                    logged_at=logged_at,
                    source_hash=sha1_row(issue_id, b_start, b_end, logged_at),
                )
            )

        # adds a shadow issue with similar summary (partial duplicate)
        if is_dup:
            dup_id = int(issues["issue_id"].max()) + len([t for t in transitions if t["issue_id"] > issues["issue_id"].max()]) + 1
            pass

    df_t = pd.DataFrame(transitions)
    df_s = pd.DataFrame(memberships)
    df_b = pd.DataFrame(blockers)
    return df_t, df_s, df_b

def load_to_postgres(issues: pd.DataFrame, transitions: pd.DataFrame, sprints: pd.DataFrame, issue_sprint: pd.DataFrame, blockers: pd.DataFrame) -> None:
    uri = engine_from_env()
    engine = create_engine(uri)

    ensure_schema(engine)
    truncate_raw(engine)

    with engine.begin() as conn:
        issues.to_sql("raw_issues", conn, if_exists="append", index=False, method="multi", chunksize=2000)
        sprints.to_sql("raw_sprints", conn, if_exists="append", index=False, method="multi", chunksize=2000)
        transitions.to_sql("raw_transitions", conn, if_exists="append", index=False, method="multi", chunksize=4000)
        issue_sprint.to_sql("raw_issue_sprint", conn, if_exists="append", index=False, method="multi", chunksize=4000)
        blockers.to_sql("raw_blockers", conn, if_exists="append", index=False, method="multi", chunksize=4000)

    console.print("[green]Loaded raw tables into MIDGARD.[/green]")

def main() -> None:
    cfg = load_cfg()
    rng = random.Random(cfg.seed)
    np.random.seed(cfg.seed)

    console.print("[cyan]Generating synthetic Jira-style dataset...[/cyan]")
    issues = gen_issues(cfg, rng)
    sprints = gen_sprints(cfg, rng)
    transitions, issue_sprint, blockers = gen_transitions_and_membership(cfg, rng, issues, sprints)

    # Sanity checks
    console.print(f"issues: {len(issues):,}")
    console.print(f"sprints: {len(sprints):,}")
    console.print(f"transitions: {len(transitions):,}")
    console.print(f"issue_sprint: {len(issue_sprint):,}")
    console.print(f"blockers: {len(blockers):,}")

    load_to_postgres(issues, transitions, sprints, issue_sprint, blockers)

if __name__ == "__main__":
    main()
