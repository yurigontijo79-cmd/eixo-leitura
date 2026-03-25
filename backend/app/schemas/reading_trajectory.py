from typing import Literal

from pydantic import BaseModel

from app.schemas.book import Book
from app.schemas.reading_session import FeelingValue

TrajectoryLabel = Literal["forming", "continuity", "resistance", "assimilation", "oscillating", "open"]


class CurrentReadingTrajectorySnapshot(BaseModel):
    current_book: Book | None
    session_count: int
    recent_feelings: list[FeelingValue]
    dominant_feeling: FeelingValue | None
    trajectory_label: TrajectoryLabel | None
    trajectory_text: str | None
