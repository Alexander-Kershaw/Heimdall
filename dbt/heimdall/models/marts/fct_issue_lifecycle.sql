with transitions as (

    select *
    from {{ ref('stg_transitions') }}

),

last_done as (

    select
        issue_id,
        max(changed_at) as done_at
    from transitions
    where canonical_status = 'done'
    group by issue_id

),

first_in_progress as (

    select
        t.issue_id,
        min(t.changed_at) as first_in_progress_at
    from transitions t
    join last_done d using(issue_id)
    where t.canonical_status = 'in_progress'
      and t.changed_at <= d.done_at
    group by t.issue_id

),

blocked_time as (

    select
        issue_id,
        sum(
            extract(epoch from coalesce(blocked_end, now()) - blocked_start)
        ) / 3600 as blocked_hours
    from {{ ref('stg_blockers') }}
    group by issue_id

),

reopens as (

    select
        issue_id,
        count(*) as reopen_count
    from transitions
    where canonical_status = 'in_progress'
      and changed_at >
          (
            select min(changed_at)
            from transitions t2
            where t2.issue_id = transitions.issue_id
              and canonical_status = 'done'
          )
    group by issue_id

)

select

    i.issue_id,
    i.issue_key,
    i.project_key,
    i.team,
    i.created_at,

    fi.first_in_progress_at,

    d.done_at,

    extract(epoch from d.done_at - fi.first_in_progress_at) / 3600
        as cycle_time_hours,

    coalesce(bt.blocked_hours, 0) as blocked_hours,

    coalesce(r.reopen_count, 0) as reopen_count

from {{ ref('stg_issues') }} i
left join last_done d using(issue_id)
left join first_in_progress fi using(issue_id)
left join blocked_time bt using(issue_id)
left join reopens r using(issue_id)
