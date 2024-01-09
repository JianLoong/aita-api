import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Engine
from sqlmodel import Session
from models.message import Message

from models.openai_analytics import OpenAIAnalysis


class OpenAIInferenceAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()

        self._setup_openai_analysis_routes()

    def _setup_openai_analysis_routes(self) -> None:
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

        self.router.add_api_route(
            "/openai-analysis/{id}",
            self.read_openai_inference,
            methods=["GET"],
            tags=["OpenAI"],
            description="Obtains OpenAI GPT3.5 Turbo Inference",
        )

        self.router.add_api_route(
            "/openai-analysis/{id}",
            self.read_openai_inference,
            methods=["POST"],
            tags=["OpenAI"],
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/openai-analysis/{id}",
            self.update_open_ai_analysis,
            methods=["PATCH"],
            tags=["OpenAI"],
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/openai-analysis/{id}",
            self.upsert_open_ai_analysis,
            methods=["PUT"],
            tags=["OpenAI"],
            responses={status.HTTP_201_CREATED: {"model": Message}},
            dependencies=[Depends(oauth2_scheme)],
        )

        self.router.add_api_route(
            "/openai-analysis/{id}",
            self.delete_open_ai_analysis,
            methods=["DELETE"],
            tags=["OpenAI"],
            description="Deletes a OpenAI",
            dependencies=[Depends(oauth2_scheme)],
            responses={
                status.HTTP_200_OK: {"model": Message},
                status.HTTP_401_UNAUTHORIZED: {"model": Message},
            },
        )

    def create_opeai_analysis(self, open_ai_analysis: OpenAIAnalysis) -> OpenAIAnalysis:
        with Session(self.engine) as session:
            logging.info("Creating OPENAI for " + str(open_ai_analysis.id))
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

    def update_open_ai_analysis(
        self, id: int, open_ai_analysis: OpenAIAnalysis
    ) -> OpenAIAnalysis:
        with Session(self.engine) as session:
            db_openai_inference = session.get(OpenAIAnalysis, id)
            if not db_openai_inference:
                raise HTTPException(status_code=404, detail="Submission not found")
            submission_data = open_ai_analysis.model_dump(exclude_unset=True)
            for key, value in submission_data.items():
                setattr(db_openai_inference, key, value)
            session.add(db_openai_inference)
            session.commit()
            session.refresh(db_openai_inference)
            return db_openai_inference

    def delete_open_ai_analysis(self, id: int):
        with Session(self.engine) as session:
            db_openai_inference = session.get(OpenAIAnalysis, id)
            if not db_openai_inference:
                raise HTTPException(status_code=404, detail="OpenAIAnalysis not found")
            session.delete(db_openai_inference)
            session.commit()

            return {"ok": True}

    def upsert_open_ai_analysis(
        self, id: int, open_ai_analysis: OpenAIAnalysis
    ) -> OpenAIAnalysis:
        """
        Upsert a open_ai_analysis

        Creates a open_ai_analysis in the database if does not already exists,
        else it is used to update the existing one

        """
        with Session(self.engine) as session:
            db_summary = session.get(OpenAIAnalysis, id)

            if not db_summary:
                db_summary = open_ai_analysis

            summary_data = open_ai_analysis.model_dump(exclude_unset=True)
            for key, value in summary_data.items():
                setattr(db_summary, key, value)

            session.add(db_summary)
            session.commit()
            session.refresh(db_summary)

            return db_summary
