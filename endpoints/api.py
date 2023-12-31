from fastapi import APIRouter, HTTPException
from sqlmodel import SQLModel, Session, create_engine, select


from models.submission import Submission
from models.summary import Summary
from models.comment import Comment

class API:

    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def configure_database(self):

        self.sqlite_file_name = "AmItheAsshole.db"
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=True)

    def __init__(self):

        self.configure_database()
        self.create_db_and_tables()
        self.router = APIRouter()
        self.router.add_api_route("/submission/{id}", self.read_submission, methods=["GET"])
        self.router.add_api_route("/submission/", self.create_submission, methods=["POST"])
        self.router.add_api_route("/search", self.search_submission, methods=["GET"])
        self.router.add_api_route("/submission/{id}", self.update_submission, methods=["PATCH"])
        self.router.add_api_route("/comment/{id}", self.read_comment, methods=["GET"])
        self.router.add_api_route("/summary/{id}", self.read_summary, methods=["GET"])

    def read_submission(self, id: int):
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    def create_submission(self, submission: Submission):
        with Session(self.engine) as session:
            session.add(submission)
            session.commit()

            return submission

    def update_submission(self, id: int, submission: Submission):
        with Session(self.engine) as session:
            db_submission = session.get(Submission, id)
            if not db_submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            submission_data = submission.model_dump(exclude_unset=True)
            for key, value in submission_data.items():
                setattr(db_submission, key, value)
            session.add(db_submission)
            session.commit()
            session.refresh(db_submission)
            return db_submission

    def search_submission(self, submission_id: str = None, created_utc: int = None, limit: int = 10):
        with Session(self.engine) as session:

            if submission_id is not None:
                statement = select(Submission).where(Submission.submission_id == (submission_id))
                results = session.exec(statement).all()
                return results
            # 1664646465
            # 1701692714000

            if created_utc is not None:

                statement = select(Submission).where(Submission.created_utc >= (created_utc)).limit(limit)
                results = session.exec(statement).all()
                return results

        raise HTTPException(status_code=404, detail="Submission not found")

    def read_comment(self, id: int):
        with Session(self.engine) as session:
            comment = session.get(Comment, id)
            if not comment:
                raise HTTPException(status_code=404, detail="Comment not found")
            return comment

    def read_summary(self, id: int):
        with Session(self.engine) as session:
            summary = session.get(Summary, id)
            if not summary:
                raise HTTPException(status_code=404, detail="Summary not found")
            return summary
