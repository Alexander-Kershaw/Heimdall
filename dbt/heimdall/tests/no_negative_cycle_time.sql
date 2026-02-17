select *
from {{ ref('fct_issue_lifecycle') }}
where cycle_time_hours < 0


