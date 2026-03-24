from datetime import datetime

from pydantic import BaseModel

from app.schemas.reading_session import FeelingValue


class ReadingCompleteRequest(BaseModel):
    book_id: int


class CompletedBookSummary(BaseModel):
    id: int
    title: str
    author: str
    completed_at: datetime
    total_sessions: int
    dominant_feeling: FeelingValue | None
    closing_text: str
