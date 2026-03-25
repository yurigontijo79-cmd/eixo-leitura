from fastapi import APIRouter

from app.schemas.completed_book import CompletedBookSummary, ReadingCompleteRequest
from app.core.db import (
    complete_current_reading,
    create_reading_reflections,
    create_reading_session,
    fetch_books,
    fetch_completed_books,
    fetch_current_reading_reflections,
    fetch_current_reading_sessions,
    fetch_current_reading_trajectory,
    fetch_reading_state,
    fetch_suggestion_candidates,
    generate_reading_feedback,
    upsert_reading_state,
)
from app.schemas.book import Book
from app.schemas.reading_feedback import ReadingFeedbackGenerate, ReadingFeedbackResponse
from app.schemas.reading_reflection import CurrentReadingReflectionsSnapshot, ReadingReflectionsCreate
from app.schemas.reading_session import CurrentReadingSessionsSnapshot, ReadingSessionCreate
from app.schemas.reading_state import ReadingStateSnapshot, ReadingStateUpdate
from app.schemas.reading_trajectory import CurrentReadingTrajectorySnapshot
from app.schemas.suggestion import SuggestionsSnapshot

router = APIRouter()


@router.get("/books", response_model=list[Book])
def get_books() -> list[Book]:
    return [Book(**row) for row in fetch_books()]


@router.get("/suggestions", response_model=SuggestionsSnapshot)
def get_suggestions() -> SuggestionsSnapshot:
    return fetch_suggestion_candidates()


@router.get("/reading-state", response_model=ReadingStateSnapshot)
def get_reading_state() -> ReadingStateSnapshot:
    return fetch_reading_state()


@router.post("/reading-state", response_model=ReadingStateSnapshot)
def post_reading_state(payload: ReadingStateUpdate) -> ReadingStateSnapshot:
    return upsert_reading_state(payload)


@router.post("/reading-state/complete", response_model=ReadingStateSnapshot)
def post_reading_complete(payload: ReadingCompleteRequest) -> ReadingStateSnapshot:
    return complete_current_reading(payload)


@router.get("/reading-sessions/current", response_model=CurrentReadingSessionsSnapshot)
def get_current_reading_sessions() -> CurrentReadingSessionsSnapshot:
    return fetch_current_reading_sessions()


@router.post("/reading-sessions", response_model=CurrentReadingSessionsSnapshot)
def post_reading_session(payload: ReadingSessionCreate) -> CurrentReadingSessionsSnapshot:
    return create_reading_session(payload)


@router.get("/reading-reflections/current", response_model=CurrentReadingReflectionsSnapshot)
def get_current_reading_reflections() -> CurrentReadingReflectionsSnapshot:
    return fetch_current_reading_reflections()


@router.get("/reading-trajectory/current", response_model=CurrentReadingTrajectorySnapshot)
def get_current_reading_trajectory() -> CurrentReadingTrajectorySnapshot:
    return fetch_current_reading_trajectory()


@router.get("/completed-books", response_model=list[CompletedBookSummary])
def get_completed_books() -> list[CompletedBookSummary]:
    return fetch_completed_books()


@router.post("/reading-reflections", response_model=CurrentReadingReflectionsSnapshot)
def post_reading_reflections(payload: ReadingReflectionsCreate) -> CurrentReadingReflectionsSnapshot:
    return create_reading_reflections(payload)


@router.post("/reading-feedback/generate", response_model=ReadingFeedbackResponse)
def post_reading_feedback(payload: ReadingFeedbackGenerate) -> ReadingFeedbackResponse:
    return generate_reading_feedback(payload)
