# src/resources/postgres.py

import os
from dotenv import load_dotenv
from .database import DatabaseManager

load_dotenv() # Load environment variables from .env file

# Load PostgreSQL DSN from environment variables
POSTGRES_DSN = os.getenv("POSTGRES_DSN")

if not POSTGRES_DSN:
    raise ValueError("POSTGRES_DSN environment variable not set.")

postgres_db_manager = DatabaseManager(POSTGRES_DSN)

async def get_postgres_session():
    """
    FastAPI dependency to provide an asynchronous PostgreSQL session.
    """
    async for session in postgres_db_manager.get_session():
        yield session
