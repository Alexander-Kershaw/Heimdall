ISSUE_LOOKUP_SQL = """
select
  l.issue_id,
  l.issue_key,
  l.team,
  l.project_key,
  l.created_at,
  l.first_in_progress_at,
  l.done_at,
  l.cycle_time_hours,
  l.blocked_hours,
  l.reopen_count
from fct_issue_lifecycle l
where l.issue_key = %(issue_key)s
"""

ISSUE_TRANSITIONS_SQL = """
select
  t.issue_id,
  t.changed_at,
  t.from_status,
  t.to_status,
  t.canonical_status
from stg_transitions t
join stg_issues i on i.issue_id = t.issue_id
where i.issue_key = %(issue_key)s
order by t.changed_at asc
"""

ISSUE_BLOCKERS_SQL = """
select
  b.issue_id,
  b.reason,
  b.blocked_start,
  b.blocked_end,
  b.logged_at
from stg_blockers b
join stg_issues i on i.issue_id = b.issue_id
where i.issue_key = %(issue_key)s
order by b.blocked_start asc
"""

ISSUE_SPRINTS_SQL = """
select
  s.sprint_name,
  s.team,
  s.start_at,
  s.end_at,
  isp.added_at,
  isp.removed_at
from stg_issue_sprint isp
join stg_issues i on i.issue_id = isp.issue_id
join stg_sprints s on s.sprint_id = isp.sprint_id
where i.issue_key = %(issue_key)s
order by s.start_at asc
"""

WIP_TRIAGE_SQL = """
select
  w.issue_key,
  w.team,
  w.project_key,
  w.operational_state,
  w.canonical_status,
  w.assignee,
  round(w.age_hours::numeric, 2) as age_hours,
  round(w.time_in_current_status_hours::numeric, 2) as time_in_status_hours,
  w.last_status_change_at
from fct_wip_current w
where (%(team)s is null or w.team = %(team)s)
  and (%(status)s is null or w.operational_state = %(status)s)
order by w.age_hours desc
limit %(limit)s
"""

TEAMS_SQL = "select distinct team_key as team from dim_team order by 1;"


