from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.book import Book

ActiveReadingState = Literal["current", "shortlist", "rejected"]
StoredReadingState = Literal["current", "shortlist", "rejected", "completed"]


class ReadingStateUpdate(BaseModel):
    book_id: int
    state: ActiveReadingState


class ReadingStateRecord(BaseModel):
    id: int
    book_id: int
    state: StoredReadingState
    created_at: datetime
    updated_at: datetime


class ReadingStateSnapshot(BaseModel):
    current_reading: Book | None
    shortlist: list[Book]
    rejected_count: int
