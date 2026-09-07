import os

from dotenv import load_dotenv
from sqlalchemy import create_engine


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL must be configured in the environment or .env file")

engine = create_engine(
    DATABASE_URL,
    echo=True
)