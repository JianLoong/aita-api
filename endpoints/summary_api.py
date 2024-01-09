from enum import Enum
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import OAuth2PasswordBearer
import sqlalchemy
from sqlmodel import Session, asc, desc, select

from models.summary import Summary


class SummaryAPI:
    def __init__(self, engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_summary_routes()

    def _setup_summary_routes(self) -> None:
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

        self.router.add_api_route(
            "/summary/{id}",
            self.read_summary,
            methods=["GET"],
            tags=["Summary"],
        )

        self.router.add_api_route(
            "/summaries/",
            self.read_summaries,
            methods=["GET"],
            tags=["Summary"],
        )

        self.router.add_api_route(
            "/summaries",
            self.create_summary,
            methods=["POST"],
            tags=["Summary"],
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/summary/{id}",
            self.upsert_summary,
            methods=["PUT"],
            tags=["Summary"],
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/summary/{id}",
            self.update_summary,
            methods=["PATCH"],
            tags=["Summary"],
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/summary/{id}",
            self.delete_summary,
            methods=["DELETE"],
            tags=["Summary"],
            dependencies=[Depends(oauth2_scheme)],
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

    class _OrderBy(str, Enum):
        asc = "asc"
        desc = "desc"

    def read_summaries(
        self,
        response: Response = Response(),
        offset: int = Query(default=0, le=100),
        limit: int = Query(default=10, le=100),
        order_by: _OrderBy = Query(alias="orderBy", default=_OrderBy.desc),
    ) -> List[Summary]:
        match order_by:
            case "desc":
                order = desc
            case "asc":
                order = asc
            case _:
                order = desc

        with Session(self.engine) as session:
            summary_count = session.exec(
                select(sqlalchemy.func.count(Summary.id))
            ).one()

            submissions = session.exec(
                select(Summary).offset(offset).limit(limit).order_by(order(Summary.id))
            ).all()

            response.headers["X-Limit"] = str(limit)
            response.headers["X-Offset"] = str(offset)
            response.headers["X-Count"] = str(summary_count)

        return submissions

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

    def delete_summary(self, id: int):
        with Session(self.engine) as session:
            summary = session.get(Summary, id)
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            session.delete(summary)
            session.commit()

            return {"ok": True}
