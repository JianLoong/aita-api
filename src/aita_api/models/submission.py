from typing import Optional

from sqlalchemy import Column, Index, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    """Submission Schema"""

    __table_args__ = (
        Index('idx_submission_search', 'search_vector', postgresql_using='gin'),
    )

    id: int = Field(
        default=None,
        primary_key=True,
        title="The Id used in this API",
        max_length=10,
    )
    submission_id: str = Field(
        max_length=10,
        unique=True,
        title="The Id obtained from the Reddit Crawler, actual Id used on Reddit",
    )
    title: str = Field(
        title="The title of the submission",
    )
    selftext: str
    created_utc: float
    permalink: str
    score: int = Field(title="The score")
    search_vector: Optional[str] = Field(
        default=None,
        sa_column=Column(
            TSVECTOR,
            server_default=text("to_tsvector('english', '')"),
        )
    )
