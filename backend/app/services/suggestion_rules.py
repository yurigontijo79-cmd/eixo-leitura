from typing import TypedDict

from app.schemas.book import Book
from app.schemas.suggestion import SuggestionsSnapshot


class SuggestionCandidate(TypedDict):
    id: int
    title: str
    author: str
    description: str
    state: str | None
    state_updated_at: str | None
    latest_session_at: str | None


def _book_from_candidate(candidate: SuggestionCandidate) -> Book:
    return Book(
        id=candidate["id"],
        title=candidate["title"],
        author=candidate["author"],
        description=candidate["description"],
        state=candidate["state"],
    )


def _sort_key(candidate: SuggestionCandidate) -> tuple[int, str, str, int]:
    session_marker = candidate["latest_session_at"] or ""
    state_marker = candidate["state_updated_at"] or ""
    return (0, state_marker, session_marker, -candidate["id"])


def build_suggestions_snapshot(candidates: list[SuggestionCandidate]) -> SuggestionsSnapshot:
    active_candidates = [candidate for candidate in candidates if candidate["state"] != "rejected"]
    shortlist_candidates = sorted(
        [candidate for candidate in active_candidates if candidate["state"] == "shortlist"],
        key=_sort_key,
        reverse=True,
    )
    current_ids = {candidate["id"] for candidate in active_candidates if candidate["state"] == "current"}
    completed_candidates = sorted(
        [candidate for candidate in active_candidates if candidate["state"] == "completed"],
        key=_sort_key,
        reverse=True,
    )
    most_recent_completed_id = completed_candidates[0]["id"] if completed_candidates else None

    untouched_candidates = [
        candidate
        for candidate in active_candidates
        if candidate["state"] is None and candidate["latest_session_at"] is None and candidate["id"] not in current_ids
    ]
    revisitable_candidates = [
        candidate
        for candidate in active_candidates
        if candidate["id"] not in current_ids
        and candidate["state"] != "shortlist"
        and candidate["state"] != "completed"
        and candidate["id"] not in {item["id"] for item in untouched_candidates}
    ]
    lower_priority_completed = [
        candidate
        for candidate in completed_candidates
        if candidate["id"] != most_recent_completed_id and candidate["id"] not in current_ids
    ]

    featured_candidates: list[SuggestionCandidate] = []
    for group in (shortlist_candidates, untouched_candidates, revisitable_candidates, lower_priority_completed):
        for candidate in group:
            if any(item["id"] == candidate["id"] for item in featured_candidates):
                continue
            featured_candidates.append(candidate)
            if len(featured_candidates) == 3:
                break
        if len(featured_candidates) == 3:
            break

    featured_ids = {candidate["id"] for candidate in featured_candidates}
    shortlist_secondary = [candidate for candidate in shortlist_candidates if candidate["id"] not in featured_ids][:3]

    fallback_pool = [
        candidate
        for candidate in (untouched_candidates + revisitable_candidates + lower_priority_completed)
        if candidate["id"] not in featured_ids
    ]
    fallback_candidates = fallback_pool[:3]

    if shortlist_candidates:
        suggestion_context = "shortlist_em_primeiro_plano"
    elif untouched_candidates:
        suggestion_context = "catalogo_aberto_com_prioridade_ao_nao_tocado"
    else:
        suggestion_context = "fallback_limpo_com_base_no_percurso"

    return SuggestionsSnapshot(
        featured=[_book_from_candidate(candidate) for candidate in featured_candidates],
        shortlist_candidates=[_book_from_candidate(candidate) for candidate in shortlist_secondary],
        fallback_candidates=[_book_from_candidate(candidate) for candidate in fallback_candidates],
        suggestion_context=suggestion_context,
    )
