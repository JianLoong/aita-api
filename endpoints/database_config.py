import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine


class DatabaseConfig:
    _instance = None

    def _setup_database(self, use_test_db: bool = False):
        load_dotenv(find_dotenv(), override=True)
        # sqlite_file_name = os.environ.get("DATABASE_NAME")

        # sqlite_url = f"sqlite:///database//{sqlite_file_name}"
        url = "postgresql+psycopg://postgres:postgres@host.docker.internal/aita"

        # if use_test_db is True:
        #     sqlite_url = f"sqlite:///database//{sqlite_file_name}" + ".test"

        self.engine = create_engine(url, echo=False)

        SQLModel.metadata.create_all(self.engine)

    def get_engine(self) -> Engine:
        return self.engine

    def __new__(cls, use_test_db: bool = False):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            cls._instance._setup_database(use_test_db)

        return cls._instance
