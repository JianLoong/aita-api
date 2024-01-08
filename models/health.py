from datetime import datetime
import time
from sqlmodel import Field, Column, SQLModel, JSON
from typing import Dict, List


class Health(SQLModel, table=False):
    message: str = Field(default="It Works")
    description: str = Field(default="AITA API Health Check")
    timestamp: str = Field(default=datetime.now())
    uptime: str = Field(default=time.monotonic())
    engine: str = None
    counts: Dict = Field(default={}, sa_column=Column(JSON))
    disk: List
