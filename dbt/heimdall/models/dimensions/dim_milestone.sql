select distinct
    sprint_id as milestone_key,
    sprint_name as milestone_name,
    team,
    start_at,
    end_at
from {{ ref('stg_sprints') }}
