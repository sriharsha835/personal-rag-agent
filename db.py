import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

# .get() with a default, not os.environ[...], so importing this module never crashes
# in an environment with no .env file (e.g. a CI runner) — it just falls back sensibly.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@127.0.0.1:55432/postgres",
)

engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=2)