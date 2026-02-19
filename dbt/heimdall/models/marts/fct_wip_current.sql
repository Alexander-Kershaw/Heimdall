with latest as (

    select
        issue_id,
        canonical_status,
        changed_at,
        row_number() over (partition by issue_id order by changed_at desc) as rn
    from {{ ref('stg_transitions') }}

),

current_state as (

    select
        issue_id,
        canonical_status,
        changed_at as last_status_change_at
    from latest
    where rn = 1

),

lifecycle as (

    select
        issue_id,
        first_in_progress_at
    from {{ ref('fct_issue_lifecycle') }}

)

select
    i.issue_id,
    i.issue_key,
    i.team,
    i.project_key,
    i.issue_type,
    i.priority,
    i.assignee,
    cs.canonical_status,
    cs.last_status_change_at,
    lc.first_in_progress_at,
    extract(epoch from (now() - coalesce(lc.first_in_progress_at, i.created_at))) / 3600.0 as age_hours,
    extract(epoch from (now() - cs.last_status_change_at)) / 3600.0 as time_in_current_status_hours
from {{ ref('stg_issues') }} i
join current_state cs using (issue_id)
left join lifecycle lc using (issue_id)
where cs.canonical_status in ('in_progress', 'review', 'blocked')
