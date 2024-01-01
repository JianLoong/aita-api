from fastapi import APIRouter, HTTPException, Query
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

        self.engine = create_engine(self.sqlite_url, echo=False)

    def __init__(self):
        self.configure_database()
        self.create_db_and_tables()
        self.router = APIRouter()
        self.router.add_api_route(
            "/submissions", self.read_submissions, methods=["GET"]
        )
        self.router.add_api_route(
            "/submission/{id}", self.read_submission, methods=["GET"]
        )
        self.router.add_api_route(
            "/submission/", self.create_submission, methods=["POST"]
        )
        self.router.add_api_route("/search_submission", self.search_submission, methods=["GET"])
        self.router.add_api_route("/search_comment", self.search_comments, methods=["GET"])
        self.router.add_api_route(
            "/submission/{id}", self.update_submission, methods=["PATCH"]
        )
        self.router.add_api_route("/comment/{id}", self.read_comment, methods=["GET"])
        self.router.add_api_route("/summary/{id}", self.read_summary, methods=["GET"])

    def read_submissions(
        self, offset: int = 0, limit: int = Query(default=100, le=100)
    ):
        with Session(self.engine) as session:
            submissions = session.exec(
                select(Submission)
                .offset(offset)
                .limit(limit)
                .order_by(Submission.created_utc)
            ).all()
            return submissions

    def read_submission(self, id: int):
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    def create_submission(self, submission: Submission):
        with Session(self.engine) as session:
            submission.id = None
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission

    def create_comment(self, comment: Comment):
        with Session(self.engine) as session:
            comment.id = None
            session.add(comment)
            session.commit()
            session.refresh(comment)
            return comment

    def update_submission_by_submission_id(
        self, submission_id: str, submission: Submission
    ):
        with Session(self.engine) as session:
            statement = select(Submission).where(
                Submission.submission_id == (submission_id)
            )
            result: Submission = session.exec(statement).one()
            result.score = submission.score
            session.add(result)
            session.commit()
            session.refresh(result)

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

    def search_comments(
        self,
        submission_id: str = None,
        start_utc: int = None,
        end_utc: int = None,
        offset: int = 0,
        limit: int = Query(default=100, le=500),
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

            if start_utc is not None:
                statement = (
                    select(Submission)
                    .where(Submission.created_utc >= start_utc)
                    .where(Submission.created_utc <= end_utc)
                    .offset(offset)
                    .order_by(Submission.created_utc)
                )
                results = session.exec(statement).all()
                return results

            return []

    def search_submission(
        self,
        submission_id: str = None,
        start_utc: int = None,
        end_utc: int = None,
        offset: int = 0,
        limit: int = Query(default=100, le=100),
    ):
        with Session(self.engine) as session:
            if submission_id is not None:
                statement = select(Submission).where(
                    Submission.submission_id == (submission_id)
                )
                results = session.exec(statement).one()
                return results
            # 1664646465
            # 1701692714000

            if start_utc is not None:
                statement = (
                    select(Submission)
                    .where(Submission.created_utc >= start_utc)
                    .where(Submission.created_utc <= end_utc)
                    .offset(offset)
                    .order_by(Submission.created_utc)
                )
                results = session.exec(statement).all()
                return results

            return []

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
