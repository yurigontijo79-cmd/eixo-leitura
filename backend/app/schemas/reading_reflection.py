from datetime import datetime

from pydantic import BaseModel

from app.schemas.book import Book
from app.schemas.reading_session import ReadingSession


class ReflectionQuestion(BaseModel):
    question_key: str
    question_text: str


class ReadingReflectionInput(BaseModel):
    question_key: str
    question_text: str
    answer_text: str


class ReadingReflectionsCreate(BaseModel):
    reading_session_id: int
    reflections: list[ReadingReflectionInput]


class ReadingReflection(BaseModel):
    id: int
    reading_session_id: int
    question_key: str
    question_text: str
    answer_text: str
    created_at: datetime


class CurrentReadingReflectionsSnapshot(BaseModel):
    current_book: Book | None
    current_session: ReadingSession | None
    suggested_questions: list[ReflectionQuestion]
