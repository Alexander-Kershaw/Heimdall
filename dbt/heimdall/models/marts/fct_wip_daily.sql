with days as (
select
generate_series(
    (select min(created_at) from {{ ref('stg_issues') }}),
    (select max(changed_at) from {{ ref('stg_transitions') }}),
    interval '1 day'
) as day
),

status as (
select
    issue_id,
    changed_at,
    canonical_status,
    lead(changed_at) over(partition by issue_id order by changed_at) as next_change
from {{ ref('stg_transitions') }}
)

select
    d.day,
    count(distinct s.issue_id) as wip_count
from days d
join status s
on d.day between s.changed_at and coalesce(s.next_change, now())
where canonical_status in ('in_progress','review','blocked')
group by d.day
