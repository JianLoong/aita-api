import logging
import os


from dotenv import load_dotenv, find_dotenv
from sqlalchemy import Engine
from sqlmodel import SQLModel, create_engine


class DatabaseConfig:
    _instance = None

    def _setup_database(self):
        load_dotenv(find_dotenv())
        # config = dotenv_values(".env")
        sqlite_file_name = os.environ.get("DATABASE_NAME")
        sqlite_url = f"sqlite:///database//{sqlite_file_name}"

        self.engine = create_engine(sqlite_url, echo=False)

        SQLModel.metadata.create_all(self.engine)

    def get_engine(self) -> Engine:
        return self.engine

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConfig, cls).__new__(cls)
            # logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

            cls._instance._setup_database()

        return cls._instance
