import logging
from fastapi import APIRouter, HTTPException

from sqlalchemy import Engine
from sqlmodel import Session

from models.openai_analytics import OpenAIAnalysis


class OpenAIInferenceAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_openai_analysis_routes()

    def _setup_openai_analysis_routes(self) -> None:
        self.router.add_api_route(
            "/openai_analysis/{id}",
            self.read_openai_inference,
            methods=["GET"],
            tags=["OpenAI"],
            description="Obtains OpenAI GPT3.5 Turbo Inference",
        )

    def create_opeai_analysis(self, open_ai_analysis: OpenAIAnalysis):
        with Session(self.engine) as session:
            logging.info("Creating analysis for " + str(open_ai_analysis.id))
            session.add(open_ai_analysis)
            session.commit()
            session.refresh(open_ai_analysis)
            return open_ai_analysis

    def read_openai_inference(self, id: int) -> OpenAIAnalysis:
        with Session(self.engine) as session:
            open_ai_inference = session.get(OpenAIAnalysis, id)
            if not open_ai_inference:
                raise HTTPException(
                    status_code=404, detail="OpenAI Inference not found"
                )
            return open_ai_inference

    def update_submission(self, id: int, submission: OpenAIAnalysis):
        with Session(self.engine) as session:
            db_openai_inference = session.get(OpenAIAnalysis, id)
            if not db_openai_inference:
                raise HTTPException(status_code=404, detail="Submission not found")
            submission_data = submission.model_dump(exclude_unset=True)
            for key, value in submission_data.items():
                setattr(db_openai_inference, key, value)
            session.add(db_openai_inference)
            session.commit()
            session.refresh(db_openai_inference)
            return db_openai_inference
