import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

def get_engine() -> Engine:
    uri = os.getenv("MIDGARD_SQLALCHEMY_URI")
    if uri:
        return create_engine(uri)

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    db = os.getenv("POSTGRES_DB", "midgard")
    user = os.getenv("POSTGRES_USER", "midgard")
    pwd = os.getenv("POSTGRES_PASSWORD", "midgard_password")

    return create_engine(f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}")
