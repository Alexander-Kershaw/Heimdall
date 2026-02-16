create table if not exists raw_issues (
  issue_id            bigint primary key,
  issue_key           text not null,
  project_key         text not null,
  team                text not null,
  issue_type          text not null,
  priority            text not null,
  created_at          timestamptz not null,
  resolved_at         timestamptz,
  assignee            text,
  reporter            text,
  estimate_points     integer,
  summary             text,
  source_hash         text not null
);

create table if not exists raw_transitions (
  transition_id       bigserial primary key,
  issue_id            bigint not null references raw_issues(issue_id),
  from_status         text,
  to_status           text not null,
  changed_at          timestamptz not null,
  actor               text,
  source_hash         text not null
);

create table if not exists raw_sprints (
  sprint_id           bigint primary key,
  team                text not null,
  sprint_name         text not null,
  start_at            timestamptz not null,
  end_at              timestamptz not null,
  goal                text,
  source_hash         text not null
);

create table if not exists raw_issue_sprint (
  id                  bigserial primary key,
  issue_id            bigint not null references raw_issues(issue_id),
  sprint_id           bigint not null references raw_sprints(sprint_id),
  added_at            timestamptz not null,
  removed_at          timestamptz,
  source_hash         text not null
);

create table if not exists raw_blockers (
  blocker_id          bigserial primary key,
  issue_id            bigint not null references raw_issues(issue_id),
  reason              text not null,
  blocked_start       timestamptz not null,
  blocked_end         timestamptz,
  logged_at           timestamptz not null,
  source_hash         text not null
);

create index if not exists idx_raw_transitions_issue_time on raw_transitions(issue_id, changed_at);
create index if not exists idx_raw_blockers_issue_time on raw_blockers(issue_id, blocked_start);
create index if not exists idx_raw_issue_sprint_issue on raw_issue_sprint(issue_id);


