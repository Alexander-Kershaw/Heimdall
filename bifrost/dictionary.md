# BIFROST Raw Data Dictionary

These tables represent synthetic Jira-style delivery logs. They is intentional mess injected into the tables to simulate realistic operations.

## raw_issues
One row per issue.
- issue_key: like `VALHALLA-123`
- team: owning team 
- resolved_at: may be null even if issue is “done” in transitions (mess)
- estimate_points: often null (missing estimates)

## raw_transitions
Event log of status changes.
- from_status/to_status: team-specific strings
- changed_at: timestamp of transition
- Note: some issues may reach Done without a clean In Progress path.

## raw_sprints
One row per sprint per team.

## raw_issue_sprint
Membership log for issues in sprints.
- added_at/removed_at: supports mid-sprint adds and removals.

## raw_blockers
Blocked windows for issues.
- logged_at may be later than blocked_start (late logging).
