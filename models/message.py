from sqlmodel import Field, SQLModel


class Message(SQLModel):
    message: str = Field(default="Too many request")
