select
  transition_id,
  issue_id,
  from_status,
  to_status,
  changed_at,
  actor,
  source_hash,

  case
    when lower(to_status) like '%done%'
      or lower(to_status) like '%shipped%'
      or lower(to_status) like '%complete%'
      then 'done'

    when lower(to_status) like '%review%'
      or lower(to_status) like '%qa%'
      or lower(to_status) like '%test%'
      then 'review'

    when lower(to_status) like '%block%'
      or lower(to_status) like '%imped%'
      then 'blocked'

    when lower(to_status) like '%progress%'
      or lower(to_status) like '%doing%'
      or lower(to_status) like '%dev%'
      then 'in_progress'

    else 'todo'
  end as canonical_status

from public.raw_transitions
