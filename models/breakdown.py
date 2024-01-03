from typing import Optional

from sqlmodel import Field, SQLModel


class Breakdown(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nta: int
    yta: int
    esh: int
    info: int
    nah: int
