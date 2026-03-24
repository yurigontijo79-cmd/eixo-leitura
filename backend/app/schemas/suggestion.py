from pydantic import BaseModel

from app.schemas.book import Book


class SuggestionsSnapshot(BaseModel):
    featured: list[Book]
    shortlist_candidates: list[Book]
    fallback_candidates: list[Book]
    suggestion_context: str | None = None
