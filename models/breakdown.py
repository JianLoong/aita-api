from typing import Optional

from sqlmodel import Field, SQLModel


class Breakdown(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nta: int = Field(ge=0, title="Not the asshole")
    yta: int = Field(ge=0, title="You are the asshole")
    esh: int = Field(ge=0, title="Everyone is asshole here")
    info: int = Field(ge=0, title="Not enough info")
    nah: int = Field(ge=0, title="No assholes here")
