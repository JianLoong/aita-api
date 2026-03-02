import time
from datetime import datetime
from typing import Dict

from sqlmodel import JSON, Column, Field, SQLModel


class Health(SQLModel, table=False):
    message: str = Field(default="It Works")
    description: str = Field(default="AITA API Health Check")
    timestamp: datetime = Field(default=datetime.now())
    uptime: float = Field(default=time.monotonic())
    engine: str = None
    counts: Dict = Field(default={}, sa_column=Column(JSON))
