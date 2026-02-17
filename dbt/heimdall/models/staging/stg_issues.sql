select
  issue_id,
  issue_key,
  project_key,
  team,
  issue_type,
  priority,
  created_at,
  resolved_at,
  assignee,
  reporter,
  estimate_points,
  summary,
  source_hash
from public.raw_issues
