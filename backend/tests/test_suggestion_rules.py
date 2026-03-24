import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@dataclass
class Book:
    id: int
    title: str
    author: str
    description: str
    state: str | None = None


@dataclass
class SuggestionsSnapshot:
    featured: list[Book]
    shortlist_candidates: list[Book]
    fallback_candidates: list[Book]
    suggestion_context: str | None = None


book_module = types.ModuleType("app.schemas.book")
book_module.Book = Book

suggestion_module = types.ModuleType("app.schemas.suggestion")
suggestion_module.SuggestionsSnapshot = SuggestionsSnapshot

sys.modules.setdefault("app.schemas.book", book_module)
sys.modules.setdefault("app.schemas.suggestion", suggestion_module)

from app.services.suggestion_rules import build_suggestions_snapshot


class SuggestionRuleTests(unittest.TestCase):
    def test_shortlist_books_are_featured_first(self) -> None:
        snapshot = build_suggestions_snapshot(
            [
                {"id": 1, "title": "A", "author": "Autor", "description": "", "state": "shortlist", "state_updated_at": "2026-03-20T00:00:00+00:00", "latest_session_at": None},
                {"id": 2, "title": "B", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
                {"id": 3, "title": "C", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
            ]
        )

        self.assertEqual([book.id for book in snapshot.featured], [1, 2, 3])
        self.assertEqual(snapshot.suggestion_context, "shortlist_em_primeiro_plano")

    def test_current_and_rejected_do_not_enter_featured(self) -> None:
        snapshot = build_suggestions_snapshot(
            [
                {"id": 1, "title": "A", "author": "Autor", "description": "", "state": "current", "state_updated_at": "2026-03-20T00:00:00+00:00", "latest_session_at": "2026-03-20T00:00:00+00:00"},
                {"id": 2, "title": "B", "author": "Autor", "description": "", "state": "rejected", "state_updated_at": "2026-03-19T00:00:00+00:00", "latest_session_at": None},
                {"id": 3, "title": "C", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
                {"id": 4, "title": "D", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
            ]
        )

        self.assertEqual([book.id for book in snapshot.featured], [3, 4])

    def test_most_recent_completed_book_does_not_return_as_featured(self) -> None:
        snapshot = build_suggestions_snapshot(
            [
                {"id": 1, "title": "A", "author": "Autor", "description": "", "state": "completed", "state_updated_at": "2026-03-21T00:00:00+00:00", "latest_session_at": "2026-03-20T00:00:00+00:00"},
                {"id": 2, "title": "B", "author": "Autor", "description": "", "state": "completed", "state_updated_at": "2026-03-10T00:00:00+00:00", "latest_session_at": "2026-03-09T00:00:00+00:00"},
                {"id": 3, "title": "C", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
                {"id": 4, "title": "D", "author": "Autor", "description": "", "state": None, "state_updated_at": None, "latest_session_at": None},
            ]
        )

        self.assertEqual([book.id for book in snapshot.featured], [3, 4, 2])
        self.assertNotIn(1, [book.id for book in snapshot.featured])


if __name__ == "__main__":
    unittest.main()
