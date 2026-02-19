import pandas as pd
import streamlit as st
from streamlit_dash.common.db import get_engine
from streamlit_dash.common.queries import (
    ISSUE_LOOKUP_SQL, ISSUE_TRANSITIONS_SQL, ISSUE_BLOCKERS_SQL, ISSUE_SPRINTS_SQL
)

st.set_page_config(page_title="HEIMDALL: Issue Investigator", layout="wide")

st.title("HEIMDALL: Issue Investigator")
st.caption("Use: Inspect a specific issue lifecycle.")

issue_key = st.text_input("Issue key (e.g., VALHALLA-142)", value="")

if issue_key:
    engine = get_engine()

    issue = pd.read_sql(ISSUE_LOOKUP_SQL, engine, params={"issue_key": issue_key})
    if issue.empty:
        st.error("No issue found with that key.")
        st.stop()

    st.subheader("Lifecycle Summary")
    st.dataframe(issue, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Transitions Timeline")
        transitions = pd.read_sql(ISSUE_TRANSITIONS_SQL, engine, params={"issue_key": issue_key})
        st.dataframe(transitions, use_container_width=True)

    with col2:
        st.subheader("Blocker Windows")
        blockers = pd.read_sql(ISSUE_BLOCKERS_SQL, engine, params={"issue_key": issue_key})
        st.dataframe(blockers, use_container_width=True)

    st.subheader("Sprint History")
    sprints = pd.read_sql(ISSUE_SPRINTS_SQL, engine, params={"issue_key": issue_key})
    st.dataframe(sprints, use_container_width=True)
else:
    st.info("Enter an issue key.")
