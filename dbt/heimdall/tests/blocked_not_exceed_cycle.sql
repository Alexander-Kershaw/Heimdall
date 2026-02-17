select *
from {{ ref('fct_issue_lifecycle') }}
where cycle_time_hours is not null
  and blocked_hours is not null
  and blocked_hours > cycle_time_hours


