import logging
import os
from fastapi import APIRouter, HTTPException

from dotenv import dotenv_values
from sqlmodel import Session, SQLModel, create_engine

from models.summary import Summary


class SummaryAPI:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self._configure_database()
        self._create_db_and_tables()
        self.router = APIRouter()

        self._setup_summary_routes()

    def _create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def _configure_database(self):
        config = dotenv_values(".env")
        self.sqlite_file_name = config.get("DATABASE_NAME")
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    def _setup_summary_routes(self) -> None:
        self.router.add_api_route(
            "/summary/{id}", self.read_summary, methods=["GET"], tags=["Summary"]
        )

    def create_summary(self, summary: Summary):
        with Session(self.engine) as session:
            session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary

    def read_summary(self, id: int):
        with Session(self.engine) as session:
            summary = session.get(Summary, id)
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            return summary

    def update_summary(self, id: int, summary: Summary):
        with Session(self.engine) as session:
            db_summary = session.get(Summary, id)
            if not db_summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            summary_data = summary.model_dump(exclude_unset=True)
            for key, value in summary_data.items():
                setattr(db_summary, key, value)
            session.add(db_summary)
            session.commit()
            session.refresh(db_summary)
            return db_summary
