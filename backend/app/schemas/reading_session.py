from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.book import Book

FeelingValue = Literal["fluida", "densa", "travada", "empolgante", "confusa"]


class ReadingSessionCreate(BaseModel):
    book_id: int
    progress_text: str
    feeling: FeelingValue
    note: str = ""


class ReadingSession(BaseModel):
    id: int
    book_id: int
    progress_text: str
    feeling: FeelingValue
    note: str | None = None
    created_at: datetime
    reflections_count: int = 0
    has_feedback: bool = False
    feedback_text: str | None = None


class CurrentReadingSessionsSnapshot(BaseModel):
    current_book: Book | None
    last_session: ReadingSession | None
    recent_sessions: list[ReadingSession]
