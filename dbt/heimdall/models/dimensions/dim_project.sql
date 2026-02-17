select distinct
    project_key,
project_key as project_name
from {{ ref('stg_issues') }}
