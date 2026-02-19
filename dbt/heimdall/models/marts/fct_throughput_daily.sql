select 
    date_trunc('day', done_at) as day,
    team,
    count(*) as issues_done
from {{ ref('fct_issue_lifecycle') }}
where done_at is not null 
group by 1,2