import pandas as pd
import streamlit as st
from streamlit_dash.common.db import get_engine
from streamlit_dash.common.queries import WIP_TRIAGE_SQL, TEAMS_SQL

st.set_page_config(page_title="HEIMDALL: WIP Triage", layout="wide")

st.title("HEIMDALL: WIP Triage")
st.caption("Use: retrieve the oldest or most stuck WIP items.")

engine = get_engine()

teams = pd.read_sql(TEAMS_SQL, engine)["team"].tolist()
team = st.selectbox("Team", ["(all)"] + teams)

status = st.selectbox("Operational State", ["(all)", "in_progress", "blocked"])
limit = st.slider("Row limit", min_value=10, max_value=200, value=50, step=10)

team_param = None if team == "(all)" else team
status_param = None if status == "(all)" else status

df = pd.read_sql(
    WIP_TRIAGE_SQL,
    engine,
    params={"team": team_param, "status": status_param, "limit": limit},
)

st.dataframe(df, use_container_width=True)

st.download_button(
    "Download CSV",
    df.to_csv(index=False).encode("utf-8"),
    file_name="heimdall_wip_triage.csv",
    mime="text/csv",
)
