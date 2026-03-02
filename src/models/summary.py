from typing import Dict, Optional
from sqlmodel import Field, Column, SQLModel, JSON


class Summary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    afinn: float
    emotion: Dict = Field(default={}, sa_column=Column(JSON))
    word_freq: Dict = Field(default={}, sa_column=Column(JSON))
    counts: Dict = Field(default={}, sa_column=Column(JSON))
