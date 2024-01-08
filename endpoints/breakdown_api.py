from fastapi import APIRouter, HTTPException
from sqlalchemy import Engine
from sqlmodel import Session

from models.breakdown import Breakdown


class BreakdownAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_breakdown_routes()

    def _setup_breakdown_routes(self) -> None:
        ...

    def create_breakdown(self, breakdown: Breakdown):
        with Session(self.engine) as session:
            session.add(breakdown)
            session.commit()
            session.refresh(breakdown)
            return breakdown

    def upsert_breakdown(self, id: int, breakdown: Breakdown) -> Breakdown:
        with Session(self.engine) as session:
            db_breakdown = session.get(Breakdown, id)

            if not db_breakdown:
                db_breakdown = breakdown

            breakdown_data = breakdown.model_dump(exclude_unset=True)
            for key, value in breakdown_data.items():
                setattr(db_breakdown, key, value)
            session.add(db_breakdown)
            session.commit()
            session.refresh(db_breakdown)
            return db_breakdown

    def update_breakdown(self, id: int, summary: Breakdown):
        with Session(self.engine) as session:
            db_breakdown = session.get(Breakdown, id)
            if not db_breakdown:
                raise HTTPException(status_code=404, detail="Summary not found")
            summary_data = summary.model_dump(exclude_unset=True)
            for key, value in summary_data.items():
                setattr(db_breakdown, key, value)
            session.add(db_breakdown)
            session.commit()
            session.refresh(db_breakdown)
            return db_breakdown
