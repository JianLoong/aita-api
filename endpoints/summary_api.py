from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from models.summary import Summary


class SummaryAPI:
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

    def __init__(self, engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_summary_routes()

    def _setup_summary_routes(self) -> None:
        self.router.add_api_route(
            "/summary/{id}",
            self.read_summary,
            methods=["GET"],
            tags=["Summary"],
        )

    def create_summary(self, summary: Summary):
        with Session(self.engine) as session:
            session.add(summary)
            session.commit()
            session.refresh(summary)
            return summary

    def read_summary(
        self,
        id: int,
    ) -> Summary:
        with Session(self.engine) as session:
            summary = session.get(Summary, id)
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            return summary

    def upsert_summary(self, id: int, summary: Summary) -> Summary:
        """
        Upsert a summary

        Creates a summary in the databse if does not already exists,
        else it is used to update the existing one

        Args:
            id:
                The summary id
            summary:
                The Summary

        """
        with Session(self.engine) as session:
            db_summary = session.get(Summary, id)

            if not db_summary:
                db_summary = summary

            summary_data = summary.model_dump(exclude_unset=True)
            for key, value in summary_data.items():
                setattr(db_summary, key, value)

            session.add(db_summary)
            session.commit()
            session.refresh(db_summary)

            return db_summary

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
