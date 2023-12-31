from typing import Optional

from sqlmodel import Field, SQLModel

class Submission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    submission_id: str
    title: str
    selftext: str
    created_utc: int
    permalink: str
    score: int
