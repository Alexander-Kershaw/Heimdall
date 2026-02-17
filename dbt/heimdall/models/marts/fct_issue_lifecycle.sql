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

base as (

    select
        i.issue_id,
        i.issue_key,
        i.project_key,
        i.team,
        i.created_at,
        fi.first_in_progress_at,
        d.done_at
    from {{ ref('stg_issues') }} i
    left join last_done d using(issue_id)
    left join first_in_progress fi using(issue_id)

),

blocked_overlap as (

    select
        b.issue_id,

        sum(
            extract(epoch from
                greatest(
                    interval '0 seconds',
                    least(coalesce(b.blocked_end, base.done_at), base.done_at)
                    - greatest(b.blocked_start, base.first_in_progress_at)
                )
            )
        ) / 3600.0 as blocked_hours

    from {{ ref('stg_blockers') }} b
    join base on base.issue_id = b.issue_id

    where base.first_in_progress_at is not null
      and base.done_at is not null
      and b.blocked_start < base.done_at
      and coalesce(b.blocked_end, base.done_at) > base.first_in_progress_at

    group by b.issue_id

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
    base.issue_id,
    base.issue_key,
    base.project_key,
    base.team,
    base.created_at,
    base.first_in_progress_at,
    base.done_at,

    extract(epoch from base.done_at - base.first_in_progress_at) / 3600.0 as cycle_time_hours,

    coalesce(bo.blocked_hours, 0) as blocked_hours,

    coalesce(r.reopen_count, 0) as reopen_count

from base
left join blocked_overlap bo using(issue_id)
left join reopens r using(issue_id)
