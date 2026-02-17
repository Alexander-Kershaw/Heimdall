select
    s.sprint_id,
    s.team,
count(distinct isp.issue_id) as committed,
count(distinct case when l.done_at <= s.end_at then isp.issue_id end) as completed,
count(distinct case when l.done_at > s.end_at then isp.issue_id end) as spillover
from {{ ref('stg_sprints') }} s

left join {{ ref('stg_issue_sprint') }} isp using(sprint_id)
left join {{ ref('fct_issue_lifecycle') }} l using(issue_id)
group by s.sprint_id, s.team
