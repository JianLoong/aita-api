from typing import Optional

from sqlmodel import Field, SQLModel


class Breakdown(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nta_count: int
    yta_count: int
    esh_count: int
    info_count: int
    nah_count: int
