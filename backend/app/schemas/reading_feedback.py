from datetime import datetime

from pydantic import BaseModel


class ReadingFeedbackGenerate(BaseModel):
    reading_session_id: int


class ReadingFeedback(BaseModel):
    id: int
    reading_session_id: int
    text: str
    created_at: datetime


class ReadingFeedbackResponse(BaseModel):
    feedback_text: str
