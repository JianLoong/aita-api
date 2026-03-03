import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine


class DatabaseConfig:
    _instance = None

    def _setup_database(self):
        load_dotenv(find_dotenv())

        # PostgreSQL connection
        db_host = os.environ.get("POSTGRES_HOST", "localhost")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "example")
        db_user = os.environ.get("POSTGRES_USER", "postgres")
        db_password = os.environ.get("POSTGRES_PASSWORD", "postgres")

        postgres_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )

        self.engine = create_engine(postgres_url, echo=False)

        SQLModel.metadata.create_all(self.engine)

    def get_engine(self) -> Engine:
        return self.engine

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            cls._instance._setup_database()

        return cls._instance
