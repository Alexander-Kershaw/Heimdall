from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def engine_from_env() -> str:
    user = os.getenv("POSTGRES_USER", "midgard")
    pwd = os.getenv("POSTGRES_PASSWORD", "midgard_password")
    db = os.getenv("POSTGRES_DB", "midgard")
    port = os.getenv("POSTGRES_PORT", "5432")
    return f"postgresql+psycopg2://{user}:{pwd}@localhost:{port}/{db}"

def ensure_schema(engine) -> None:
    schema_sql = Path("bifrost/schema.sql").read_text()
    with engine.begin() as conn:
        for stmt in schema_sql.split(";"):
            s = stmt.strip()
            if s:
                conn.execute(text(s))

def truncate_raw(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("truncate table raw_blockers, raw_issue_sprint, raw_transitions, raw_sprints, raw_issues restart identity cascade;"))
