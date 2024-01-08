from sqlmodel import Field, SQLModel


class Submission(SQLModel, table=True):
    """Submission Schema"""

    id: int = Field(
        default=None,
        primary_key=True,
        title="The Id used in this API",
        max_length=10,
    )
    submission_id: str = Field(
        default=None,
        title="The Id obtained from the Reddit Crawler, actual Id used on Reddit",
    )
    title: str
    selftext: str
    created_utc: int
    permalink: str
    score: int = Field(index=True)
