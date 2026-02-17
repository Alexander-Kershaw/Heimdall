select distinct
    team as team_key,
    team as team_name,
case

when team = 'AEGIR'
then 'Platform engineering team'

when team = 'FREYA'
then 'Application engineering team'

when team = 'TYR'
then 'Infrastructure engineering team'

else 'Unknown'

end as team_description
from {{ ref('stg_issues') }}
