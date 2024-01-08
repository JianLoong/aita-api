from typing import Optional

from sqlmodel import Field, SQLModel


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: str = Field(default=None, foreign_key="submission.submission_id")
    message: str
    comment_id: str = Field(unique=True)
    parent_id: str
    created_utc: int
    score: int
