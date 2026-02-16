select 'raw_issues' as table_name, count(*) as n from raw_issues
union all select 'raw_transitions', count(*) from raw_transitions
union all select 'raw_sprints',     count(*) from raw_sprints
union all select 'raw_issue_sprint',count(*) from raw_issue_sprint
union all select 'raw_blockers',    count(*) from raw_blockers
order by table_name;
