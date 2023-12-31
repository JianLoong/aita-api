from fastapi import FastAPI, HTTPException

from sqlmodel import SQLModel, Session, create_engine
from models.comment import Comment

from models.submission import Submission
from models.summary import Summary

sqlite_file_name = "AmItheAsshole.db"
sqlite_url = f"sqlite:///database//{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

create_db_and_tables()

url_versioning = "/v2"

@app.get(url_versioning + "/submissions/{submission_id}")
def read_submission(submission_id: int):
    with Session(engine) as session:
        submission = session.get(Submission, submission_id)
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        return submission


@app.get(url_versioning + "/comments/{comment_id}")
def read_comment(comment_id: int):
    with Session(engine) as session:
        comment = session.get(Comment, comment_id)
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
        return comment

@app.get(url_versioning + "/summaries/{summary_id}")
def read_summary(summary_id: int):
    with Session(engine) as session:
        summary = session.get(Summary, summary_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Summary not found")
        return summary
