CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE reading_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL UNIQUE,
    state TEXT NOT NULL CHECK (state IN ('current', 'shortlist', 'rejected', 'completed')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id)
);

CREATE TABLE reading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    progress_text TEXT NOT NULL,
    feeling TEXT NOT NULL CHECK (feeling IN ('fluida', 'densa', 'travada', 'empolgante', 'confusa')),
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(book_id) REFERENCES books(id)
);

CREATE TABLE reading_reflections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_session_id INTEGER NOT NULL,
    question_key TEXT NOT NULL,
    question_text TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(reading_session_id) REFERENCES reading_sessions(id)
);

CREATE TABLE reading_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_session_id INTEGER NOT NULL UNIQUE,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(reading_session_id) REFERENCES reading_sessions(id)
);
