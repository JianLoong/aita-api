import logging
import os
from fastapi import APIRouter

from dotenv import dotenv_values
from sqlmodel import Session, SQLModel, create_engine
from models.breakdown import Breakdown


class BreakdownAPI:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self._configure_database()
        self._create_db_and_tables()
        self.router = APIRouter()

        self._setup_breakdown_routes()

    def _create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def _configure_database(self):
        config = dotenv_values(".env")
        self.sqlite_file_name = config.get("DATABASE_NAME")
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    def _setup_breakdown_routes(self) -> None:
        ...

    def create_breakdown(self, breakdown: Breakdown):
        with Session(self.engine) as session:
            session.add(breakdown)
            session.commit()
            session.refresh(breakdown)
            return breakdown
