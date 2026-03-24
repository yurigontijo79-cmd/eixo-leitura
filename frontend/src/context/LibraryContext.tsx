import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import {
  completeReadingState,
  createReadingReflections,
  createReadingSession,
  generateReadingFeedback,
  getBooks,
  getCompletedBooks,
  getCurrentReadingReflections,
  getCurrentReadingSessions,
  getCurrentReadingTrajectory,
  getReadingState,
  getSuggestions,
  updateReadingState,
} from '../services/api';
import type {
  ActiveReadingState,
  Book,
  CompletedBookSummary,
  CurrentReadingReflectionsSnapshot,
  CurrentReadingSessionsSnapshot,
  CurrentReadingTrajectorySnapshot,
  FeelingValue,
  ReadingReflectionInput,
  ReadingStateSnapshot,
  SuggestionsSnapshot,
} from '../types/book';

type LibraryContextValue = {
  books: Book[];
  readingState: ReadingStateSnapshot;
  readingSessions: CurrentReadingSessionsSnapshot;
  readingReflections: CurrentReadingReflectionsSnapshot;
  readingTrajectory: CurrentReadingTrajectorySnapshot;
  completedBooks: CompletedBookSummary[];
  suggestions: SuggestionsSnapshot;
  loading: boolean;
  error: string | null;
  refreshAll: () => Promise<void>;
  setBookState: (bookId: number, state: ActiveReadingState) => Promise<void>;
  completeCurrentReading: (bookId: number) => Promise<void>;
  saveReadingSession: (payload: {
    bookId: number;
    progressText: string;
    feeling: FeelingValue;
    note: string;
  }) => Promise<void>;
  saveReadingReflections: (payload: {
    readingSessionId: number;
    reflections: ReadingReflectionInput[];
  }) => Promise<void>;
  generateSessionFeedback: (readingSessionId: number) => Promise<string>;
};

const emptyReadingState: ReadingStateSnapshot = {
  current_reading: null,
  shortlist: [],
  rejected_count: 0,
};

const emptyReadingSessions: CurrentReadingSessionsSnapshot = {
  current_book: null,
  last_session: null,
  recent_sessions: [],
};

const emptyReadingReflections: CurrentReadingReflectionsSnapshot = {
  current_book: null,
  current_session: null,
  suggested_questions: [],
};

const emptyReadingTrajectory: CurrentReadingTrajectorySnapshot = {
  current_book: null,
  session_count: 0,
  recent_feelings: [],
  dominant_feeling: null,
  trajectory_label: null,
  trajectory_text: null,
};

const emptyCompletedBooks: CompletedBookSummary[] = [];
const emptySuggestions: SuggestionsSnapshot = {
  featured: [],
  shortlist_candidates: [],
  fallback_candidates: [],
  suggestion_context: null,
};

const LibraryContext = createContext<LibraryContextValue | undefined>(undefined);

function mergeBooksWithState(books: Book[], snapshot: ReadingStateSnapshot): Book[] {
  const stateMap = new Map<number, Book['state']>();

  if (snapshot.current_reading) {
    stateMap.set(snapshot.current_reading.id, snapshot.current_reading.state);
  }

  snapshot.shortlist.forEach((book) => {
    stateMap.set(book.id, book.state);
  });

  return books.map((book) => ({
    ...book,
    state:
      stateMap.get(book.id) ??
      (book.state === 'rejected' || book.state === 'completed' ? book.state : null),
  }));
}

export function LibraryProvider({ children }: { children: ReactNode }) {
  const [books, setBooks] = useState<Book[]>([]);
  const [readingState, setReadingState] = useState<ReadingStateSnapshot>(emptyReadingState);
  const [readingSessions, setReadingSessions] = useState<CurrentReadingSessionsSnapshot>(emptyReadingSessions);
  const [readingReflections, setReadingReflections] = useState<CurrentReadingReflectionsSnapshot>(
    emptyReadingReflections,
  );
  const [readingTrajectory, setReadingTrajectory] = useState<CurrentReadingTrajectorySnapshot>(
    emptyReadingTrajectory,
  );
  const [completedBooks, setCompletedBooks] = useState<CompletedBookSummary[]>(emptyCompletedBooks);
  const [suggestions, setSuggestions] = useState<SuggestionsSnapshot>(emptySuggestions);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshAll = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const [booksResponse, stateResponse, sessionsResponse, reflectionsResponse, trajectoryResponse, completedResponse, suggestionsResponse] =
        await Promise.all([
          getBooks(),
          getReadingState(),
          getCurrentReadingSessions(),
          getCurrentReadingReflections(),
          getCurrentReadingTrajectory(),
          getCompletedBooks(),
          getSuggestions(),
        ]);
      setBooks(mergeBooksWithState(booksResponse, stateResponse));
      setReadingState(stateResponse);
      setReadingSessions(sessionsResponse);
      setReadingReflections(reflectionsResponse);
      setReadingTrajectory(trajectoryResponse);
      setCompletedBooks(completedResponse);
      setSuggestions(suggestionsResponse);
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Não foi possível retomar seu percurso agora.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  const setBookState = useCallback(async (bookId: number, state: ActiveReadingState) => {
    const stateSnapshot = await updateReadingState(bookId, state);
    const [sessionsSnapshot, reflectionsSnapshot, trajectorySnapshot, completedSnapshot, suggestionsSnapshot] = await Promise.all([
      getCurrentReadingSessions(),
      getCurrentReadingReflections(),
      getCurrentReadingTrajectory(),
      getCompletedBooks(),
      getSuggestions(),
    ]);

    setReadingState(stateSnapshot);
    setReadingSessions(sessionsSnapshot);
    setReadingReflections(reflectionsSnapshot);
    setReadingTrajectory(trajectorySnapshot);
    setCompletedBooks(completedSnapshot);
    setSuggestions(suggestionsSnapshot);
    setBooks((currentBooks) =>
      currentBooks.map((book) => {
        if (stateSnapshot.current_reading?.id === book.id) {
          return { ...book, state: 'current' };
        }

        if (stateSnapshot.shortlist.some((item) => item.id === book.id)) {
          return { ...book, state: 'shortlist' };
        }

        if (book.id === bookId && state === 'rejected') {
          return { ...book, state: 'rejected' };
        }

        if (book.state === 'current' && stateSnapshot.current_reading?.id !== book.id) {
          return { ...book, state: null };
        }

        if (book.state === 'shortlist' && !stateSnapshot.shortlist.some((item) => item.id === book.id)) {
          return { ...book, state: null };
        }

        if (book.id === bookId && book.state === 'completed') {
          return { ...book, state: null };
        }

        return book;
      }),
    );
  }, []);

  const completeCurrentReading = useCallback(async (bookId: number) => {
    const stateSnapshot = await completeReadingState(bookId);
    const [booksResponse, sessionsSnapshot, reflectionsSnapshot, trajectorySnapshot, completedSnapshot, suggestionsSnapshot] =
      await Promise.all([
        getBooks(),
        getCurrentReadingSessions(),
        getCurrentReadingReflections(),
        getCurrentReadingTrajectory(),
        getCompletedBooks(),
        getSuggestions(),
      ]);

    setReadingState(stateSnapshot);
    setReadingSessions(sessionsSnapshot);
    setReadingReflections(reflectionsSnapshot);
    setReadingTrajectory(trajectorySnapshot);
    setCompletedBooks(completedSnapshot);
    setSuggestions(suggestionsSnapshot);
    setBooks(mergeBooksWithState(booksResponse, stateSnapshot));
  }, []);

  const saveReadingSession = useCallback(
    async (payload: { bookId: number; progressText: string; feeling: FeelingValue; note: string }) => {
      const sessionsSnapshot = await createReadingSession(payload);
      const [reflectionsSnapshot, trajectorySnapshot] = await Promise.all([
        getCurrentReadingReflections(),
        getCurrentReadingTrajectory(),
      ]);
      setReadingSessions(sessionsSnapshot);
      setReadingReflections(reflectionsSnapshot);
      setReadingTrajectory(trajectorySnapshot);
    },
    [],
  );

  const saveReadingReflections = useCallback(
    async (payload: { readingSessionId: number; reflections: ReadingReflectionInput[] }) => {
      const reflectionsSnapshot = await createReadingReflections(payload);
      const [sessionsSnapshot, trajectorySnapshot] = await Promise.all([
        getCurrentReadingSessions(),
        getCurrentReadingTrajectory(),
      ]);
      setReadingReflections(reflectionsSnapshot);
      setReadingSessions(sessionsSnapshot);
      setReadingTrajectory(trajectorySnapshot);
    },
    [],
  );

  const generateSessionFeedback = useCallback(async (readingSessionId: number) => {
    const response = await generateReadingFeedback(readingSessionId);
    const [sessionsSnapshot, trajectorySnapshot] = await Promise.all([
      getCurrentReadingSessions(),
      getCurrentReadingTrajectory(),
    ]);
    setReadingSessions(sessionsSnapshot);
    setReadingTrajectory(trajectorySnapshot);
    return response.feedback_text;
  }, []);

  const value = useMemo(
    () => ({
      books,
      readingState,
      readingSessions,
      readingReflections,
      readingTrajectory,
      completedBooks,
      suggestions,
      loading,
      error,
      refreshAll,
      setBookState,
      completeCurrentReading,
      saveReadingSession,
      saveReadingReflections,
      generateSessionFeedback,
    }),
    [
      books,
      readingState,
      readingSessions,
      readingReflections,
      readingTrajectory,
      completedBooks,
      suggestions,
      loading,
      error,
      refreshAll,
      setBookState,
      completeCurrentReading,
      saveReadingSession,
      saveReadingReflections,
      generateSessionFeedback,
    ],
  );

  return <LibraryContext.Provider value={value}>{children}</LibraryContext.Provider>;
}

export function useLibrary() {
  const context = useContext(LibraryContext);

  if (!context) {
    throw new Error('useLibrary deve ser usado dentro de LibraryProvider.');
  }

  return context;
}
