import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Generator

from fastapi import HTTPException

from app.core.config import DATABASE_DIR, DATABASE_PATH
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
                description TEXT NOT NULL
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
            """
        )

        existing_count = connection.execute("SELECT COUNT(*) AS total FROM books").fetchone()["total"]
        if existing_count == 0:
            connection.executemany(
                "INSERT INTO books (id, title, author, description) VALUES (:id, :title, :author, :description)",
                [book.model_dump(exclude={"state"}) for book in MOCK_BOOKS],
            )


def fetch_books() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT books.id, books.title, books.author, books.description, reading_state.state
            FROM books
            LEFT JOIN reading_state ON reading_state.book_id = books.id
            ORDER BY books.id
            """
        ).fetchall()
    return [dict(row) for row in rows]


def fetch_suggestion_candidates() -> SuggestionsSnapshot:
    with get_connection() as connection:
        rows = connection.execute(
            """
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
