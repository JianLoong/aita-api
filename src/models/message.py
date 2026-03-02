from sqlmodel import Field, SQLModel


class Message(SQLModel, table=False):
    details: str = Field(default="Message")
