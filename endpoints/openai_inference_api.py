import logging
import os
from fastapi import APIRouter, HTTPException

from dotenv import dotenv_values
from sqlmodel import Session, SQLModel, create_engine

from models.openai_analytics import OpenAIAnalysis


class OpenAIInferenceAPI:
    def __init__(self):
        logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

        self._configure_database()
        self._create_db_and_tables()
        self.router = APIRouter()

        self._setup_openai_analysis_routes()

    def _create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def _configure_database(self):
        config = dotenv_values(".env")
        self.sqlite_file_name = config.get("DATABASE_NAME")
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

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

    def read_openai_inference(self, id: int):
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
