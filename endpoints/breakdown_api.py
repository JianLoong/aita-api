from fastapi import APIRouter
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
