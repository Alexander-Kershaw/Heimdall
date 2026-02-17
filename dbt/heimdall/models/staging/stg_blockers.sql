select
  blocker_id,
  issue_id,
  reason,
  blocked_start,
  blocked_end,
  logged_at,
  source_hash
from public.raw_blockers
