CREATE TABLE books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    description TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'mock',
    external_edition_id INTEGER,
    is_catalog_active INTEGER NOT NULL DEFAULT 1
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

CREATE TABLE works (
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

CREATE TABLE editions (
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

CREATE TABLE source_records (
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

CREATE TABLE ingestion_batches (
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

CREATE TABLE staging_source_records (
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
