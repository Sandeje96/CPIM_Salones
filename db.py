import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from psycopg_pool import ConnectionPool
from psycopg.rows import dict_row

# The POOL is initialized here without opening it yet.
# When running in deployment, DATABASE_URL should be available.
# main.py will load dotenv before this is imported to ensure the variable is set in local dev.
pool = ConnectionPool(
    conninfo=os.environ.get("DATABASE_URL", "postgresql://localhost/cpim_salones"),
    min_size=1,
    max_size=5,
    kwargs={"row_factory": dict_row},
    open=False,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    # Initialize the schema if needed
    with pool.connection() as conn:
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if os.path.exists(schema_path):
            with open(schema_path, "r", encoding="utf-8") as f:
                conn.execute(f.read())
    yield
    pool.close()

def get_db():
    with pool.connection() as conn:
        yield conn
