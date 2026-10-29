from sqlalchemy import text
from db import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print("Connected! Postgres version:", result.scalar())
    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
    conn.commit()
    print("pgvector extension enabled.")