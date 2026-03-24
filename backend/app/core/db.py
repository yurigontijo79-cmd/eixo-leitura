import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import re
import unicodedata
from urllib import parse, request
from typing import Generator

from fastapi import HTTPException

from app.core.config import CATALOG_SOURCE, DATABASE_DIR, DATABASE_PATH
from app.schemas.completed_book import CompletedBookSummary, ReadingCompleteRequest
from app.schemas.reading_feedback import ReadingFeedbackGenerate, ReadingFeedbackResponse
from app.schemas.reading_reflection import CurrentReadingReflectionsSnapshot, ReadingReflectionsCreate
from app.schemas.reading_session import CurrentReadingSessionsSnapshot, ReadingSessionCreate
from app.schemas.reading_state import ReadingStateSnapshot, ReadingStateUpdate
from app.schemas.reading_trajectory import CurrentReadingTrajectorySnapshot
from app.schemas.suggestion import SuggestionsSnapshot
from app.services.catalog import MOCK_BOOKS
from app.services.closing_rules import build_closing_text
from app.services.feedback_rules import build_feedback_text
from app.services.reflection_bank import select_questions_for_feeling
from app.services.suggestion_rules import build_suggestions_snapshot
from app.services.trajectory_rules import build_reading_trajectory


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                description TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'mock',
                external_edition_id INTEGER,
                is_catalog_active INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS reading_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL UNIQUE,
                state TEXT NOT NULL CHECK (state IN ('current', 'shortlist', 'rejected', 'completed')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS reading_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                progress_text TEXT NOT NULL,
                feeling TEXT NOT NULL CHECK (feeling IN ('fluida', 'densa', 'travada', 'empolgante', 'confusa')),
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(book_id) REFERENCES books(id)
            );

            CREATE TABLE IF NOT EXISTS reading_reflections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_session_id INTEGER NOT NULL,
                question_key TEXT NOT NULL,
                question_text TEXT NOT NULL,
                answer_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(reading_session_id) REFERENCES reading_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS reading_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reading_session_id INTEGER NOT NULL UNIQUE,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(reading_session_id) REFERENCES reading_sessions(id)
            );

            CREATE TABLE IF NOT EXISTS works (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_title TEXT NOT NULL,
                canonical_author TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                normalized_author TEXT NOT NULL,
                language_primary TEXT NOT NULL DEFAULT 'pt',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS editions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_id INTEGER NOT NULL,
                edition_title TEXT NOT NULL,
                subtitle TEXT,
                publisher TEXT,
                published_date TEXT,
                isbn10 TEXT,
                isbn13 TEXT,
                format_type TEXT,
                language_code TEXT,
                language_region TEXT,
                is_pt_br_confident INTEGER NOT NULL DEFAULT 0,
                pt_br_confidence_score INTEGER NOT NULL DEFAULT 0,
                activation_status TEXT NOT NULL DEFAULT 'inactive',
                cover_url TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(work_id) REFERENCES works(id)
            );

            CREATE TABLE IF NOT EXISTS source_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                edition_id INTEGER NOT NULL,
                source_name TEXT NOT NULL,
                source_record_id TEXT NOT NULL,
                source_url TEXT,
                source_payload_json TEXT NOT NULL,
                availability_hint TEXT,
                kindle_available INTEGER NOT NULL DEFAULT 0,
                fetched_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                UNIQUE(source_name, source_record_id),
                FOREIGN KEY(edition_id) REFERENCES editions(id)
            );

            CREATE TABLE IF NOT EXISTS ingestion_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name TEXT NOT NULL,
                query_context TEXT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                records_fetched INTEGER NOT NULL DEFAULT 0,
                records_promoted INTEGER NOT NULL DEFAULT 0,
                records_retained INTEGER NOT NULL DEFAULT 0,
                records_discarded INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS staging_source_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ingestion_batch_id INTEGER NOT NULL,
                source_name TEXT NOT NULL,
                source_record_id TEXT NOT NULL,
                raw_payload_json TEXT NOT NULL,
                raw_title TEXT,
                raw_author TEXT,
                raw_language_code TEXT,
                raw_language_region TEXT,
                raw_publisher TEXT,
                raw_published_date TEXT,
                raw_isbn10 TEXT,
                raw_isbn13 TEXT,
                raw_source_url TEXT,
                raw_cover_url TEXT,
                normalized_title TEXT,
                normalized_author TEXT,
                pt_br_confidence_score INTEGER NOT NULL DEFAULT 0,
                pt_br_confidence_reason TEXT,
                staging_status TEXT NOT NULL DEFAULT 'retained',
                discard_reason TEXT,
                dedupe_match_type TEXT,
                dedupe_work_id INTEGER,
                dedupe_edition_id INTEGER,
                fetched_at TEXT NOT NULL,
                promoted_at TEXT,
                FOREIGN KEY(ingestion_batch_id) REFERENCES ingestion_batches(id)
            );
            """
        )

        for alter_sql in (
            "ALTER TABLE books ADD COLUMN source_type TEXT NOT NULL DEFAULT 'mock'",
            "ALTER TABLE books ADD COLUMN external_edition_id INTEGER",
            "ALTER TABLE books ADD COLUMN is_catalog_active INTEGER NOT NULL DEFAULT 1",
        ):
            try:
                connection.execute(alter_sql)
            except sqlite3.OperationalError:
                pass

        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_works_normalized ON works(normalized_title, normalized_author)"
        )
        connection.execute("CREATE INDEX IF NOT EXISTS idx_editions_isbn10 ON editions(isbn10)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_editions_isbn13 ON editions(isbn13)")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_staging_batch_status ON staging_source_records(ingestion_batch_id, staging_status)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_staging_norm ON staging_source_records(normalized_title, normalized_author)"
        )

        existing_count = connection.execute("SELECT COUNT(*) AS total FROM books").fetchone()["total"]
        if existing_count == 0:
            connection.executemany(
                "INSERT INTO books (id, title, author, description, source_type, is_catalog_active) VALUES (:id, :title, :author, :description, 'mock', 1)",
                [book.model_dump(exclude={"state"}) for book in MOCK_BOOKS],
            )


def fetch_books() -> list[dict]:
    where_clause = ""
    params: tuple[object, ...] = ()
    if CATALOG_SOURCE == "mock":
        where_clause = "WHERE books.source_type = 'mock' AND books.is_catalog_active = 1"
    elif CATALOG_SOURCE == "real":
        where_clause = "WHERE books.source_type = 'external' AND books.is_catalog_active = 1"
    else:
        where_clause = "WHERE books.is_catalog_active = 1"

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT books.id, books.title, books.author, books.description, reading_state.state
            FROM books
            LEFT JOIN reading_state ON reading_state.book_id = books.id
            {where_clause}
            ORDER BY books.id
            """,
            params,
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_suggestion_candidates() -> SuggestionsSnapshot:
    where_clause = ""
    if CATALOG_SOURCE == "mock":
        where_clause = "WHERE books.source_type = 'mock' AND books.is_catalog_active = 1"
    elif CATALOG_SOURCE == "real":
        where_clause = "WHERE books.source_type = 'external' AND books.is_catalog_active = 1"
    else:
        where_clause = "WHERE books.is_catalog_active = 1"

    with get_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT
                books.id,
                books.title,
                books.author,
                books.description,
                reading_state.state,
                reading_state.updated_at AS state_updated_at,
                MAX(reading_sessions.created_at) AS latest_session_at
            FROM books
            LEFT JOIN reading_state ON reading_state.book_id = books.id
            LEFT JOIN reading_sessions ON reading_sessions.book_id = books.id
            {where_clause}
            GROUP BY books.id, reading_state.id
            ORDER BY books.id
            """
        ).fetchall()

    return build_suggestions_snapshot([dict(row) for row in rows])


def fetch_completed_book_rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT books.id, books.title, books.author, reading_state.updated_at AS completed_at
        FROM reading_state
        JOIN books ON books.id = reading_state.book_id
        WHERE reading_state.state = 'completed'
        ORDER BY reading_state.updated_at DESC
        """
    ).fetchall()


def book_exists(connection: sqlite3.Connection, book_id: int) -> bool:
    row = connection.execute("SELECT 1 FROM books WHERE id = ?", (book_id,)).fetchone()
    return row is not None


def fetch_current_book_row(connection: sqlite3.Connection) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT books.id, books.title, books.author, books.description, reading_state.state
        FROM reading_state
        JOIN books ON books.id = reading_state.book_id
        WHERE reading_state.state = 'current'
        ORDER BY reading_state.updated_at DESC
        LIMIT 1
        """
    ).fetchone()


def fetch_session_row(connection: sqlite3.Connection, reading_session_id: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            reading_sessions.id,
            reading_sessions.book_id,
            reading_sessions.progress_text,
            reading_sessions.feeling,
            reading_sessions.note,
            reading_sessions.created_at,
            COUNT(DISTINCT reading_reflections.id) AS reflections_count,
            CASE WHEN reading_feedback.id IS NOT NULL THEN 1 ELSE 0 END AS has_feedback,
            reading_feedback.text AS feedback_text
        FROM reading_sessions
        LEFT JOIN reading_reflections ON reading_reflections.reading_session_id = reading_sessions.id
        LEFT JOIN reading_feedback ON reading_feedback.reading_session_id = reading_sessions.id
        WHERE reading_sessions.id = ?
        GROUP BY reading_sessions.id, reading_feedback.id
        """,
        (reading_session_id,),
    ).fetchone()


def fetch_recent_sessions_for_book(
    connection: sqlite3.Connection,
    book_id: int,
    limit: int = 5,
) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            reading_sessions.id,
            reading_sessions.book_id,
            reading_sessions.progress_text,
            reading_sessions.feeling,
            reading_sessions.note,
            reading_sessions.created_at,
            COUNT(DISTINCT reading_reflections.id) AS reflections_count,
            CASE WHEN reading_feedback.id IS NOT NULL THEN 1 ELSE 0 END AS has_feedback,
            reading_feedback.text AS feedback_text
        FROM reading_sessions
        LEFT JOIN reading_reflections ON reading_reflections.reading_session_id = reading_sessions.id
        LEFT JOIN reading_feedback ON reading_feedback.reading_session_id = reading_sessions.id
        WHERE reading_sessions.book_id = ?
        GROUP BY reading_sessions.id, reading_feedback.id
        ORDER BY reading_sessions.created_at DESC
        LIMIT ?
        """,
        (book_id, limit),
    ).fetchall()


def count_sessions_for_book(connection: sqlite3.Connection, book_id: int) -> int:
    row = connection.execute(
        "SELECT COUNT(*) AS total FROM reading_sessions WHERE book_id = ?",
        (book_id,),
    ).fetchone()
    return row["total"]


def fetch_used_reflection_keys(connection: sqlite3.Connection, reading_session_id: int) -> set[str]:
    rows = connection.execute(
        "SELECT question_key FROM reading_reflections WHERE reading_session_id = ?",
        (reading_session_id,),
    ).fetchall()
    return {row["question_key"] for row in rows}


def fetch_reflection_answers(connection: sqlite3.Connection, reading_session_id: int) -> list[str]:
    rows = connection.execute(
        "SELECT answer_text FROM reading_reflections WHERE reading_session_id = ? ORDER BY id ASC",
        (reading_session_id,),
    ).fetchall()
    return [row["answer_text"] for row in rows]


def fetch_feedback_row(connection: sqlite3.Connection, reading_session_id: int) -> sqlite3.Row | None:
    return connection.execute(
        "SELECT id, reading_session_id, text, created_at FROM reading_feedback WHERE reading_session_id = ?",
        (reading_session_id,),
    ).fetchone()


def fetch_latest_feedback_text_for_book(connection: sqlite3.Connection, book_id: int) -> str | None:
    row = connection.execute(
        """
        SELECT reading_feedback.text
        FROM reading_feedback
        JOIN reading_sessions ON reading_sessions.id = reading_feedback.reading_session_id
        WHERE reading_sessions.book_id = ?
        ORDER BY reading_sessions.created_at DESC
        LIMIT 1
        """,
        (book_id,),
    ).fetchone()
    return row["text"] if row else None


def fetch_recent_question_keys_for_book(
    connection: sqlite3.Connection,
    book_id: int,
    exclude_session_id: int,
    session_limit: int = 3,
) -> list[str]:
    session_rows = connection.execute(
        """
        SELECT id
        FROM reading_sessions
        WHERE book_id = ? AND id != ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (book_id, exclude_session_id, session_limit),
    ).fetchall()
    session_ids = [row["id"] for row in session_rows]
    if not session_ids:
        return []

    placeholders = ", ".join("?" for _ in session_ids)
    rows = connection.execute(
        f"""
        SELECT question_key
        FROM reading_reflections
        WHERE reading_session_id IN ({placeholders})
        ORDER BY created_at DESC, id DESC
        """,
        session_ids,
    ).fetchall()
    return [row["question_key"] for row in rows]


def fetch_recent_feedback_texts_for_book(
    connection: sqlite3.Connection,
    book_id: int,
    exclude_session_id: int,
    limit: int = 3,
) -> list[str]:
    rows = connection.execute(
        """
        SELECT reading_feedback.text
        FROM reading_feedback
        JOIN reading_sessions ON reading_sessions.id = reading_feedback.reading_session_id
        WHERE reading_sessions.book_id = ? AND reading_sessions.id != ?
        ORDER BY reading_sessions.created_at DESC
        LIMIT ?
        """,
        (book_id, exclude_session_id, limit),
    ).fetchall()
    return [row["text"] for row in rows]


def count_previous_sessions_for_book(
    connection: sqlite3.Connection,
    book_id: int,
    exclude_session_id: int,
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM reading_sessions
        WHERE book_id = ? AND id != ?
        """,
        (book_id, exclude_session_id),
    ).fetchone()
    return row["total"]


def count_previous_feedback_for_book(
    connection: sqlite3.Connection,
    book_id: int,
    exclude_session_id: int,
) -> int:
    row = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM reading_feedback
        JOIN reading_sessions ON reading_sessions.id = reading_feedback.reading_session_id
        WHERE reading_sessions.book_id = ? AND reading_sessions.id != ?
        """,
        (book_id, exclude_session_id),
    ).fetchone()
    return row["total"]


def fetch_reading_state() -> ReadingStateSnapshot:
    with get_connection() as connection:
        current_row = fetch_current_book_row(connection)

        shortlist_rows = connection.execute(
            """
            SELECT books.id, books.title, books.author, books.description, reading_state.state
            FROM reading_state
            JOIN books ON books.id = reading_state.book_id
            WHERE reading_state.state = 'shortlist'
            ORDER BY reading_state.updated_at DESC, books.title ASC
            """
        ).fetchall()

        rejected_count = connection.execute(
            "SELECT COUNT(*) AS total FROM reading_state WHERE state = 'rejected'"
        ).fetchone()["total"]

    return ReadingStateSnapshot(
        current_reading=dict(current_row) if current_row else None,
        shortlist=[dict(row) for row in shortlist_rows],
        rejected_count=rejected_count,
    )


def upsert_reading_state(payload: ReadingStateUpdate) -> ReadingStateSnapshot:
    now = utc_now_iso()
    with get_connection() as connection:
        if not book_exists(connection, payload.book_id):
            raise HTTPException(status_code=404, detail="Livro não encontrado.")

        if payload.state == "current":
            connection.execute(
                "DELETE FROM reading_state WHERE state = 'current' AND book_id != ?",
                (payload.book_id,),
            )

        existing = connection.execute(
            "SELECT id FROM reading_state WHERE book_id = ?",
            (payload.book_id,),
        ).fetchone()

        if existing:
            connection.execute(
                "UPDATE reading_state SET state = ?, updated_at = ? WHERE book_id = ?",
                (payload.state, now, payload.book_id),
            )
        else:
            connection.execute(
                "INSERT INTO reading_state (book_id, state, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (payload.book_id, payload.state, now, now),
            )

    print(f"[reading_state] book_id={payload.book_id} state={payload.state} updated_at={now}")
    return fetch_reading_state()


def fetch_current_reading_sessions() -> CurrentReadingSessionsSnapshot:
    with get_connection() as connection:
        current_book = fetch_current_book_row(connection)
        if not current_book:
            return CurrentReadingSessionsSnapshot(
                current_book=None,
                last_session=None,
                recent_sessions=[],
            )

        recent_sessions = fetch_recent_sessions_for_book(connection, current_book["id"])

    recent_session_dicts = [dict(row) for row in recent_sessions]
    return CurrentReadingSessionsSnapshot(
        current_book=dict(current_book),
        last_session=recent_session_dicts[0] if recent_session_dicts else None,
        recent_sessions=recent_session_dicts,
    )


def fetch_current_reading_trajectory() -> CurrentReadingTrajectorySnapshot:
    with get_connection() as connection:
        current_book = fetch_current_book_row(connection)
        if not current_book:
            return build_reading_trajectory(current_book=None, recent_feelings=[], session_count=0)

        recent_sessions = fetch_recent_sessions_for_book(connection, current_book["id"], limit=5)
        recent_feelings = [row["feeling"] for row in recent_sessions]
        session_count = count_sessions_for_book(connection, current_book["id"])

    return build_reading_trajectory(
        current_book=dict(current_book),
        recent_feelings=recent_feelings,
        session_count=session_count,
    )


def fetch_completed_books() -> list[CompletedBookSummary]:
    with get_connection() as connection:
        completed_rows = fetch_completed_book_rows(connection)
        summaries: list[CompletedBookSummary] = []

        for row in completed_rows:
            recent_sessions = fetch_recent_sessions_for_book(connection, row["id"], limit=5)
            recent_feelings = [session["feeling"] for session in recent_sessions]
            total_sessions = count_sessions_for_book(connection, row["id"])
            trajectory = build_reading_trajectory(
                current_book={
                    "id": row["id"],
                    "title": row["title"],
                    "author": row["author"],
                    "description": "",
                    "state": "completed",
                },
                recent_feelings=recent_feelings,
                session_count=total_sessions,
            )
            closing_text = build_closing_text(
                total_sessions=total_sessions,
                trajectory_label=trajectory.trajectory_label,
                dominant_feeling=trajectory.dominant_feeling,
                last_feedback_text=fetch_latest_feedback_text_for_book(connection, row["id"]),
            )
            summaries.append(
                CompletedBookSummary(
                    id=row["id"],
                    title=row["title"],
                    author=row["author"],
                    completed_at=row["completed_at"],
                    total_sessions=total_sessions,
                    dominant_feeling=trajectory.dominant_feeling,
                    closing_text=closing_text,
                )
            )

    return summaries


def create_reading_session(payload: ReadingSessionCreate) -> CurrentReadingSessionsSnapshot:
    progress_text = payload.progress_text.strip()
    note = payload.note.strip()

    if not progress_text:
        raise HTTPException(status_code=400, detail="Informe até onde você foi na leitura.")

    with get_connection() as connection:
        if not book_exists(connection, payload.book_id):
            raise HTTPException(status_code=404, detail="Livro não encontrado.")

        current_book = fetch_current_book_row(connection)
        if not current_book or current_book["id"] != payload.book_id:
            raise HTTPException(
                status_code=400,
                detail="Só é possível registrar sessão para o livro em leitura atual.",
            )

        created_at = utc_now_iso()
        connection.execute(
            """
            INSERT INTO reading_sessions (book_id, progress_text, feeling, note, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (payload.book_id, progress_text, payload.feeling, note or None, created_at),
        )

    print(
        f"[reading_session] book_id={payload.book_id} progress={progress_text} feeling={payload.feeling} created_at={created_at}"
    )
    return fetch_current_reading_sessions()


def complete_current_reading(payload: ReadingCompleteRequest) -> ReadingStateSnapshot:
    now = utc_now_iso()
    with get_connection() as connection:
        if not book_exists(connection, payload.book_id):
            raise HTTPException(status_code=404, detail="Livro não encontrado.")

        current_book = fetch_current_book_row(connection)
        if not current_book or current_book["id"] != payload.book_id:
            raise HTTPException(status_code=400, detail="Só é possível concluir o livro em leitura atual.")

        connection.execute(
            "UPDATE reading_state SET state = 'completed', updated_at = ? WHERE book_id = ?",
            (now, payload.book_id),
        )

    print(f"[reading_complete] book_id={payload.book_id} completed_at={now}")
    return fetch_reading_state()


def fetch_current_reading_reflections() -> CurrentReadingReflectionsSnapshot:
    with get_connection() as connection:
        current_book = fetch_current_book_row(connection)
        if not current_book:
            return CurrentReadingReflectionsSnapshot(
                current_book=None,
                current_session=None,
                suggested_questions=[],
            )

        recent_sessions = fetch_recent_sessions_for_book(connection, current_book["id"], limit=1)
        if not recent_sessions:
            return CurrentReadingReflectionsSnapshot(
                current_book=dict(current_book),
                current_session=None,
                suggested_questions=[],
            )

        current_session = recent_sessions[0]
        used_keys = fetch_used_reflection_keys(connection, current_session["id"])
        recent_question_history = fetch_recent_question_keys_for_book(
            connection,
            current_book["id"],
            current_session["id"],
        )
        session_cycle_index = count_previous_sessions_for_book(
            connection,
            current_book["id"],
            current_session["id"],
        )
        remaining_slots = max(0, 2 - len(used_keys))
        suggested_questions = []
        if remaining_slots > 0:
            suggested_questions = select_questions_for_feeling(
                current_session["feeling"],
                used_keys,
                recent_question_history,
                cycle_index=session_cycle_index,
                limit=remaining_slots,
            )

    return CurrentReadingReflectionsSnapshot(
        current_book=dict(current_book),
        current_session=dict(current_session),
        suggested_questions=suggested_questions,
    )


def create_reading_reflections(payload: ReadingReflectionsCreate) -> CurrentReadingReflectionsSnapshot:
    if not payload.reflections:
        raise HTTPException(status_code=400, detail="Envie ao menos uma reflexão.")

    if len(payload.reflections) > 2:
        raise HTTPException(status_code=400, detail="No máximo 2 reflexões por sessão nesta fase.")

    trimmed_reflections: list[tuple[str, str, str]] = []
    seen_keys: set[str] = set()
    for reflection in payload.reflections:
        question_key = reflection.question_key.strip()
        question_text = reflection.question_text.strip()
        answer_text = reflection.answer_text.strip()

        if not question_key or not question_text:
            raise HTTPException(status_code=400, detail="Pergunta inválida para a reflexão.")
        if not answer_text:
            raise HTTPException(status_code=400, detail="Toda reflexão precisa de uma resposta breve.")
        if question_key in seen_keys:
            raise HTTPException(status_code=400, detail="Não repita a mesma pergunta na mesma sessão.")

        seen_keys.add(question_key)
        trimmed_reflections.append((question_key, question_text, answer_text))

    with get_connection() as connection:
        session_row = fetch_session_row(connection, payload.reading_session_id)
        if not session_row:
            raise HTTPException(status_code=404, detail="Sessão de leitura não encontrada.")

        existing_keys = fetch_used_reflection_keys(connection, payload.reading_session_id)
        if len(existing_keys) >= 2:
            raise HTTPException(status_code=400, detail="Esta sessão já recebeu as reflexões previstas.")

        if existing_keys.intersection(seen_keys):
            raise HTTPException(status_code=400, detail="Esta pergunta já foi respondida para a sessão.")

        if len(existing_keys) + len(trimmed_reflections) > 2:
            raise HTTPException(status_code=400, detail="Esta sessão aceita no máximo 2 reflexões.")

        created_at = utc_now_iso()
        connection.executemany(
            """
            INSERT INTO reading_reflections (reading_session_id, question_key, question_text, answer_text, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (payload.reading_session_id, question_key, question_text, answer_text, created_at)
                for question_key, question_text, answer_text in trimmed_reflections
            ],
        )

    print(
        f"[reading_reflection] session_id={payload.reading_session_id} count={len(trimmed_reflections)} created_at={created_at}"
    )
    return fetch_current_reading_reflections()


def generate_reading_feedback(payload: ReadingFeedbackGenerate) -> ReadingFeedbackResponse:
    with get_connection() as connection:
        session_row = fetch_session_row(connection, payload.reading_session_id)
        if not session_row:
            raise HTTPException(status_code=404, detail="Sessão de leitura não encontrada.")

        existing_feedback = fetch_feedback_row(connection, payload.reading_session_id)
        if existing_feedback:
            raise HTTPException(status_code=400, detail="Esta sessão já possui um retorno salvo.")

        reflection_answers = fetch_reflection_answers(connection, payload.reading_session_id)
        if not reflection_answers:
            raise HTTPException(status_code=400, detail="Salve ao menos uma reflexão antes do retorno.")

        recent_feedback_texts = fetch_recent_feedback_texts_for_book(
            connection,
            session_row["book_id"],
            payload.reading_session_id,
        )
        feedback_cycle_index = count_previous_feedback_for_book(
            connection,
            session_row["book_id"],
            payload.reading_session_id,
        )
        feedback_text = build_feedback_text(
            session_row["feeling"],
            reflection_answers,
            recent_feedback_texts,
            cycle_index=feedback_cycle_index,
        )
        created_at = utc_now_iso()
        connection.execute(
            "INSERT INTO reading_feedback (reading_session_id, text, created_at) VALUES (?, ?, ?)",
            (payload.reading_session_id, feedback_text, created_at),
        )

    print(
        f"[reading_feedback] session_id={payload.reading_session_id} text={feedback_text} created_at={created_at}"
    )
    return ReadingFeedbackResponse(feedback_text=feedback_text)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    lowered = value.lower().strip()
    normalized = unicodedata.normalize("NFKD", lowered)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    collapsed = re.sub(r"[\(\)\[\]\{\}:;,'\"`~!@#$%^&*_+=|<>?/\\.-]+", " ", without_accents)
    collapsed = re.sub(r"\s+", " ", collapsed)
    return collapsed.strip()


def _extract_isbn(identifiers: list[dict] | None) -> tuple[str | None, str | None]:
    isbn10: str | None = None
    isbn13: str | None = None
    for identifier in identifiers or []:
        kind = (identifier.get("type") or "").upper()
        value = (identifier.get("identifier") or "").replace("-", "").strip()
        if not value:
            continue
        if kind == "ISBN_10" and len(value) == 10:
            isbn10 = value
        if kind == "ISBN_13" and len(value) == 13:
            isbn13 = value
    return isbn10, isbn13


def _publisher_is_br(publisher: str | None) -> bool:
    if not publisher:
        return False
    marker = normalize_text(publisher)
    keywords = (
        "editora",
        "companhia das letras",
        "record",
        "intrinseca",
        "rocco",
        "objetiva",
        "sextante",
        "planeta do brasil",
    )
    return any(keyword in marker for keyword in keywords)


def _text_looks_ptbr(*values: str | None) -> bool:
    text = normalize_text(" ".join(value or "" for value in values))
    return any(token in text for token in (" nao ", " que ", " para ", " com ", " uma ", " leitura "))


def score_pt_br_confidence(
    language_code: str | None,
    language_region: str | None,
    publisher: str | None,
    title: str | None,
    description: str | None,
    source_name: str,
    source_url: str | None,
) -> tuple[int, str]:
    score = 0
    reasons: list[str] = []
    lang = (language_code or "").lower()
    region = (language_region or "").upper()
    if lang == "pt":
        score += 45
        reasons.append("language_code=pt")
    if region == "BR":
        score += 25
        reasons.append("language_region=BR")
    if _publisher_is_br(publisher):
        score += 20
        reasons.append("editora_brasileira")
    if _text_looks_ptbr(title, description):
        score += 10
        reasons.append("texto_com_sinal_pt")
    source_url_norm = (source_url or "").lower()
    if "amazon.com.br" in source_url_norm:
        score += 15
        reasons.append("marketplace_brasileiro")
    if source_name == "google_books":
        score += 2
    if source_name == "open_library":
        score += 1
    return score, ",".join(reasons) if reasons else "sem_sinal_forte"


def _parse_google_books_item(item: dict) -> dict:
    volume = item.get("volumeInfo", {})
    isbn10, isbn13 = _extract_isbn(volume.get("industryIdentifiers"))
    language = (volume.get("language") or "").lower()
    return {
        "source_name": "google_books",
        "source_record_id": str(item.get("id") or ""),
        "source_url": volume.get("infoLink"),
        "title": volume.get("title") or "Sem título",
        "author": ", ".join(volume.get("authors") or ["Autor desconhecido"]),
        "description": volume.get("description") or "",
        "language_code": language if len(language) == 2 else (language[:2] if language else None),
        "language_region": "BR" if ".br" in (volume.get("canonicalVolumeLink") or "").lower() else None,
        "publisher": volume.get("publisher"),
        "published_date": volume.get("publishedDate"),
        "isbn10": isbn10,
        "isbn13": isbn13,
        "cover_url": (volume.get("imageLinks") or {}).get("thumbnail"),
        "format_type": "kindle" if item.get("saleInfo", {}).get("isEbook") else "print",
        "availability_hint": item.get("saleInfo", {}).get("saleability"),
        "kindle_available": bool(item.get("saleInfo", {}).get("isEbook")),
        "payload": item,
    }


def _parse_open_library_doc(doc: dict) -> dict:
    isbn_values = doc.get("isbn") or []
    isbn10 = next((value for value in isbn_values if len(value.replace("-", "")) == 10), None)
    isbn13 = next((value for value in isbn_values if len(value.replace("-", "")) == 13), None)
    languages = doc.get("language") or []
    language_code = None
    if languages:
        first_lang = str(languages[0]).lower()
        if "/pt" in first_lang or first_lang.endswith("pt"):
            language_code = "pt"
    title = doc.get("title") or "Sem título"
    author = ", ".join(doc.get("author_name") or ["Autor desconhecido"])
    key = doc.get("key") or ""
    source_url = f"https://openlibrary.org{key}" if key else None
    return {
        "source_name": "open_library",
        "source_record_id": key or normalize_text(f"{title}-{author}"),
        "source_url": source_url,
        "title": title,
        "author": author,
        "description": "",
        "language_code": language_code,
        "language_region": None,
        "publisher": ", ".join(doc.get("publisher")[:1]) if doc.get("publisher") else None,
        "published_date": str(doc.get("first_publish_year")) if doc.get("first_publish_year") else None,
        "isbn10": isbn10.replace("-", "") if isbn10 else None,
        "isbn13": isbn13.replace("-", "") if isbn13 else None,
        "cover_url": f"https://covers.openlibrary.org/b/id/{doc.get('cover_i')}-L.jpg" if doc.get("cover_i") else None,
        "format_type": "unknown",
        "availability_hint": "bibliographic",
        "kindle_available": False,
        "payload": doc,
    }


def fetch_google_books_records(query: str, max_results: int = 20) -> list[dict]:
    url = (
        "https://www.googleapis.com/books/v1/volumes?"
        + parse.urlencode({"q": query, "maxResults": max(1, min(max_results, 40))})
    )
    with request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = payload.get("items") or []
    return [_parse_google_books_item(item) for item in items if item.get("id")]


def fetch_open_library_records(query: str, limit: int = 20) -> list[dict]:
    url = "https://openlibrary.org/search.json?" + parse.urlencode({"q": query, "limit": max(1, min(limit, 50))})
    with request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    docs = payload.get("docs") or []
    return [_parse_open_library_doc(doc) for doc in docs]


def _find_existing_edition(connection: sqlite3.Connection, parsed: dict) -> tuple[int | None, str | None]:
    if parsed.get("isbn13"):
        row = connection.execute("SELECT id FROM editions WHERE isbn13 = ?", (parsed["isbn13"],)).fetchone()
        if row:
            return row["id"], "isbn13"
    if parsed.get("isbn10"):
        row = connection.execute("SELECT id FROM editions WHERE isbn10 = ?", (parsed["isbn10"],)).fetchone()
        if row:
            return row["id"], "isbn10"

    normalized_title = normalize_text(parsed.get("title"))
    normalized_author = normalize_text(parsed.get("author"))
    row = connection.execute(
        """
        SELECT editions.id
        FROM editions
        JOIN works ON works.id = editions.work_id
        WHERE works.normalized_title = ? AND works.normalized_author = ?
        LIMIT 1
        """,
        (normalized_title, normalized_author),
    ).fetchone()
    if row:
        return row["id"], "title_author"
    return None, None


def _ensure_work(connection: sqlite3.Connection, parsed: dict) -> int:
    normalized_title = normalize_text(parsed.get("title"))
    normalized_author = normalize_text(parsed.get("author"))
    row = connection.execute(
        "SELECT id FROM works WHERE normalized_title = ? AND normalized_author = ? LIMIT 1",
        (normalized_title, normalized_author),
    ).fetchone()
    now = utc_now_iso()
    if row:
        connection.execute("UPDATE works SET updated_at = ? WHERE id = ?", (now, row["id"]))
        return row["id"]

    cursor = connection.execute(
        """
        INSERT INTO works (
            canonical_title, canonical_author, normalized_title, normalized_author, language_primary, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (
            parsed.get("title") or "Sem título",
            parsed.get("author") or "Autor desconhecido",
            normalized_title,
            normalized_author,
            parsed.get("language_code") or "pt",
            now,
            now,
        ),
    )
    return int(cursor.lastrowid)


def _ensure_edition(connection: sqlite3.Connection, work_id: int, parsed: dict, activation_status: str, score: int) -> int:
    now = utc_now_iso()
    cursor = connection.execute(
        """
        INSERT INTO editions (
            work_id, edition_title, subtitle, publisher, published_date, isbn10, isbn13, format_type, language_code, language_region,
            is_pt_br_confident, pt_br_confidence_score, activation_status, cover_url, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            work_id,
            parsed.get("title") or "Sem título",
            None,
            parsed.get("publisher"),
            parsed.get("published_date"),
            parsed.get("isbn10"),
            parsed.get("isbn13"),
            parsed.get("format_type"),
            parsed.get("language_code"),
            parsed.get("language_region"),
            1 if activation_status == "active" else 0,
            score,
            activation_status,
            parsed.get("cover_url"),
            now,
            now,
        ),
    )
    return int(cursor.lastrowid)


def _upsert_source_record(connection: sqlite3.Connection, edition_id: int, parsed: dict, fetched_at: str) -> None:
    existing = connection.execute(
        "SELECT id FROM source_records WHERE source_name = ? AND source_record_id = ?",
        (parsed["source_name"], parsed["source_record_id"]),
    ).fetchone()
    if existing:
        connection.execute(
            """
            UPDATE source_records
            SET edition_id = ?, source_url = ?, source_payload_json = ?, availability_hint = ?, kindle_available = ?, last_seen_at = ?
            WHERE id = ?
            """,
            (
                edition_id,
                parsed.get("source_url"),
                json.dumps(parsed.get("payload"), ensure_ascii=False),
                parsed.get("availability_hint"),
                1 if parsed.get("kindle_available") else 0,
                fetched_at,
                existing["id"],
            ),
        )
        return

    connection.execute(
        """
        INSERT INTO source_records (
            edition_id, source_name, source_record_id, source_url, source_payload_json, availability_hint, kindle_available, fetched_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            edition_id,
            parsed["source_name"],
            parsed["source_record_id"],
            parsed.get("source_url"),
            json.dumps(parsed.get("payload"), ensure_ascii=False),
            parsed.get("availability_hint"),
            1 if parsed.get("kindle_available") else 0,
            fetched_at,
            fetched_at,
        ),
    )


def _ensure_book_entry(connection: sqlite3.Connection, edition_id: int, parsed: dict, active: bool) -> None:
    existing = connection.execute("SELECT id FROM books WHERE external_edition_id = ?", (edition_id,)).fetchone()
    description = parsed.get("description") or "Registro importado de fonte externa para o catálogo interno canônico."
    if existing:
        connection.execute(
            """
            UPDATE books SET title = ?, author = ?, description = ?, source_type = 'external', is_catalog_active = ?
            WHERE id = ?
            """,
            (parsed.get("title") or "Sem título", parsed.get("author") or "Autor desconhecido", description, 1 if active else 0, existing["id"]),
        )
        return

    connection.execute(
        """
        INSERT INTO books (title, author, description, source_type, external_edition_id, is_catalog_active)
        VALUES (?, ?, ?, 'external', ?, ?)
        """,
        (
            parsed.get("title") or "Sem título",
            parsed.get("author") or "Autor desconhecido",
            description,
            edition_id,
            1 if active else 0,
        ),
    )


def create_ingestion_batch(source_name: str, query_context: str | None = None) -> int:
    started_at = utc_now_iso()
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO ingestion_batches (source_name, query_context, status, started_at)
            VALUES (?, ?, 'running', ?)
            """,
            (source_name, query_context, started_at),
        )
        return int(cursor.lastrowid)


def ingest_catalog_records(source_name: str, query: str, max_results: int = 20) -> dict:
    if source_name not in {"google_books", "open_library"}:
        raise HTTPException(status_code=400, detail="Fonte não suportada para ingestão nesta fase.")

    batch_id = create_ingestion_batch(source_name, query_context=query)
    try:
        if source_name == "google_books":
            records = fetch_google_books_records(query, max_results=max_results)
        else:
            records = fetch_open_library_records(query, limit=max_results)
    except Exception as fetch_error:
        finished_at = utc_now_iso()
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE ingestion_batches
                SET status = 'failed', finished_at = ?, records_fetched = 0, records_promoted = 0, records_retained = 0, records_discarded = 0
                WHERE id = ?
                """,
                (finished_at, batch_id),
            )
        return {
            "batch_id": batch_id,
            "source_name": source_name,
            "query_context": query,
            "status": "failed",
            "records_fetched": 0,
            "records_promoted": 0,
            "records_retained": 0,
            "records_discarded": 0,
            "examples": [],
            "error": str(fetch_error),
        }

    promoted = 0
    retained = 0
    discarded = 0
    with get_connection() as connection:
        for parsed in records:
            fetched_at = utc_now_iso()
            score, reason = score_pt_br_confidence(
                parsed.get("language_code"),
                parsed.get("language_region"),
                parsed.get("publisher"),
                parsed.get("title"),
                parsed.get("description"),
                parsed["source_name"],
                parsed.get("source_url"),
            )
            if score >= 60:
                staging_status = "promoted"
            elif score >= 40:
                staging_status = "retained"
            else:
                staging_status = "discarded"

            edition_id, match_type = _find_existing_edition(connection, parsed)
            work_id = None
            if staging_status == "promoted":
                if edition_id:
                    work_row = connection.execute("SELECT work_id FROM editions WHERE id = ?", (edition_id,)).fetchone()
                    work_id = work_row["work_id"] if work_row else None
                    connection.execute(
                        """
                        UPDATE editions
                        SET updated_at = ?, is_pt_br_confident = 1, pt_br_confidence_score = MAX(pt_br_confidence_score, ?), activation_status = 'active'
                        WHERE id = ?
                        """,
                        (fetched_at, score, edition_id),
                    )
                else:
                    work_id = _ensure_work(connection, parsed)
                    edition_id = _ensure_edition(connection, work_id, parsed, activation_status="active", score=score)
                    match_type = "new_record"

                _upsert_source_record(connection, edition_id, parsed, fetched_at)
                _ensure_book_entry(connection, edition_id, parsed, active=True)
                promoted += 1
            elif staging_status == "retained":
                retained += 1
            else:
                discarded += 1

            connection.execute(
                """
                INSERT INTO staging_source_records (
                    ingestion_batch_id, source_name, source_record_id, raw_payload_json, raw_title, raw_author, raw_language_code,
                    raw_language_region, raw_publisher, raw_published_date, raw_isbn10, raw_isbn13, raw_source_url, raw_cover_url,
                    normalized_title, normalized_author, pt_br_confidence_score, pt_br_confidence_reason, staging_status, discard_reason,
                    dedupe_match_type, dedupe_work_id, dedupe_edition_id, fetched_at, promoted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    batch_id,
                    parsed["source_name"],
                    parsed["source_record_id"],
                    json.dumps(parsed.get("payload"), ensure_ascii=False),
                    parsed.get("title"),
                    parsed.get("author"),
                    parsed.get("language_code"),
                    parsed.get("language_region"),
                    parsed.get("publisher"),
                    parsed.get("published_date"),
                    parsed.get("isbn10"),
                    parsed.get("isbn13"),
                    parsed.get("source_url"),
                    parsed.get("cover_url"),
                    normalize_text(parsed.get("title")),
                    normalize_text(parsed.get("author")),
                    score,
                    reason,
                    staging_status,
                    "baixa_confianca_ptbr" if staging_status == "discarded" else None,
                    match_type,
                    work_id,
                    edition_id,
                    fetched_at,
                    fetched_at if staging_status == "promoted" else None,
                ),
            )

        finished_at = utc_now_iso()
        connection.execute(
            """
            UPDATE ingestion_batches
            SET status = 'completed', finished_at = ?, records_fetched = ?, records_promoted = ?, records_retained = ?, records_discarded = ?
            WHERE id = ?
            """,
            (finished_at, len(records), promoted, retained, discarded, batch_id),
        )

    return summarize_ingestion_batch(batch_id)


def summarize_ingestion_batch(batch_id: int) -> dict:
    with get_connection() as connection:
        batch = connection.execute("SELECT * FROM ingestion_batches WHERE id = ?", (batch_id,)).fetchone()
        if not batch:
            raise HTTPException(status_code=404, detail="Lote de ingestão não encontrado.")
        examples = connection.execute(
            """
            SELECT books.id, books.title, books.author, editions.id AS edition_id
            FROM staging_source_records
            JOIN editions ON editions.id = staging_source_records.dedupe_edition_id
            JOIN books ON books.external_edition_id = editions.id
            WHERE staging_source_records.ingestion_batch_id = ? AND staging_source_records.staging_status = 'promoted'
            ORDER BY staging_source_records.id ASC
            LIMIT 5
            """,
            (batch_id,),
        ).fetchall()

    return {
        "batch_id": batch["id"],
        "source_name": batch["source_name"],
        "query_context": batch["query_context"],
        "status": batch["status"],
        "records_fetched": batch["records_fetched"],
        "records_promoted": batch["records_promoted"],
        "records_retained": batch["records_retained"],
        "records_discarded": batch["records_discarded"],
        "examples": [dict(row) for row in examples],
    }
