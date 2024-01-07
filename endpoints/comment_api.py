from sqlalchemy import Engine
from dotenv import dotenv_values
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, SQLModel, create_engine, select

from models.comment import Comment


class CommentAPI:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.router = APIRouter()
        self._setup_comment_routes()

    def _create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def _configure_database(self):
        config = dotenv_values(".env")
        self.sqlite_file_name = config.get("DATABASE_NAME")
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    def _setup_comment_routes(self) -> None:
        self.router.add_api_route(
            "/comment/{id}", self.read_comment, methods=["GET"], tags=["Comment"]
        )

        self.router.add_api_route(
            "/comments/search", self.search_comments, methods=["GET"], tags=["Comment"]
        )

    def read_comment(self, id: int):
        with Session(self.engine) as session:
            comment = session.get(Comment, id)
            if not comment:
                raise HTTPException(status_code=404, detail="Comment not found")
            return comment

    def create_comment(self, comment: Comment):
        with Session(self.engine) as session:
            comment.id = None
            session.add(comment)
            session.commit()
            session.refresh(comment)
            return comment

    def search_comments(
        self,
        submission_id: str = None,
    ):
        with Session(self.engine) as session:
            if submission_id is not None:
                statement = select(Comment).where(
                    Comment.submission_id == (submission_id)
                )
                results = session.exec(statement).all()
                return results
            # 1664646465
            # 1701692714000

            return []
