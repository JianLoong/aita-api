from pydantic import BaseModel


class RateLimit(BaseModel):
    error: str = "Rate limit exceeded"
