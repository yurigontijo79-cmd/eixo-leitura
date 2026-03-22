from typing import Literal

from pydantic import BaseModel

ReadingStateValue = Literal["current", "shortlist", "rejected", "completed"]


class Book(BaseModel):
    id: int
    title: str
    author: str
    description: str
    state: ReadingStateValue | None = None
