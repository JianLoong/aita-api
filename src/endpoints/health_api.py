import sqlalchemy
from fastapi import APIRouter, status
from sqlmodel import Session, select

from models.comment import Comment
from models.health import Health
from models.message import Message
from models.openai_analytics import OpenAIAnalysis
from models.submission import Submission
from models.summary import Summary


class HealthAPI:
    def __init__(self, engine):
        self.engine = engine
        self.router = APIRouter()

        self.engine = engine
        self._setup_summary_routes()

    def _setup_summary_routes(self) -> None:
        self.router.add_api_route(
            "/health",
            self.read_health,
            methods=["GET"],
            tags=["Health"],
            description="Health Check for the AITA API",
        )

        self.router.add_api_route(
            "/ping",
            self.read_ping,
            methods=["GET"],
            tags=["Health"],
            description="Ping Check for the AITA API",
            responses={status.HTTP_200_OK: {"model": Message}},
        )

    def read_ping(self) -> Message:
        message = Message()
        message.details = "Pong"
        return message

    def read_health(self) -> Health:
        with Session(self.engine) as session:
            submission_count = session.exec(
                select(sqlalchemy.func.count(Submission.id))
            ).one()

            comment_count = session.exec(
                select(sqlalchemy.func.count(Comment.id))
            ).one()

            openai_analysis_count = session.exec(
                select(sqlalchemy.func.count(OpenAIAnalysis.id))
            ).one()

            summary_count = session.exec(
                select(sqlalchemy.func.count(Summary.id))
            ).one()

        counts = {
            "submissions": submission_count,
            "comments": comment_count,
            "openAIAnalysis": openai_analysis_count,
            "summaries": summary_count,
        }

        health_check = Health(counts=counts, engine=str(self.engine))

        return health_check
