from fastapi import Query, HTTPException
from sqlmodel import Session, SQLModel, create_engine, desc, select

from models.submission import Submission


class SubmissionEndPoints:
    def create_db_and_tables(self):
        SQLModel.metadata.create_all(self.engine)

    def configure_database(self):
        self.sqlite_file_name = "AmItheAsshole.db"
        self.sqlite_url = f"sqlite:///database//{self.sqlite_file_name}"

        self.engine = create_engine(self.sqlite_url, echo=False)

    def read_submission(self, id: int):
        with Session(self.engine) as session:
            submission = session.get(Submission, id)
            if not submission:
                raise HTTPException(status_code=404, detail="Submission not found")
            return submission

    def read_submissions(
        self, offset: int = 0, limit: int = Query(default=100, le=100)
    ):
        with Session(self.engine) as session:
            submissions = session.exec(
                select(Submission)
                .offset(offset)
                .limit(limit)
                .order_by(desc(Submission.created_utc))
            ).all()
            return submissions

    def create_submission(self, submission: Submission):
        with Session(self.engine) as session:
            submission.id = None
            session.add(submission)
            session.commit()
            session.refresh(submission)
            return submission
