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

const API_URL = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';

async function parseResponse<T>(response: Response, fallbackMessage: string): Promise<T> {
  if (!response.ok) {
    let message = fallbackMessage;

    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        message = body.detail;
      }
    } catch {
      // resposta sem JSON utilizável
    }

    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

export async function getBooks(): Promise<Book[]> {
  const response = await fetch(`${API_URL}/books`);
  return parseResponse<Book[]>(response, 'Não foi possível carregar o catálogo.');
}

export async function getSuggestions(): Promise<SuggestionsSnapshot> {
  const response = await fetch(`${API_URL}/suggestions`);
  return parseResponse<SuggestionsSnapshot>(response, 'Não foi possível carregar as sugestões.');
}

export async function getReadingState(): Promise<ReadingStateSnapshot> {
  const response = await fetch(`${API_URL}/reading-state`);
  return parseResponse<ReadingStateSnapshot>(response, 'Não foi possível carregar o estado de leitura.');
}

export async function updateReadingState(
  bookId: number,
  state: ActiveReadingState,
): Promise<ReadingStateSnapshot> {
  const response = await fetch(`${API_URL}/reading-state`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ book_id: bookId, state }),
  });

  return parseResponse<ReadingStateSnapshot>(response, 'Não foi possível atualizar o estado do livro.');
}

export async function completeReadingState(bookId: number): Promise<ReadingStateSnapshot> {
  const response = await fetch(`${API_URL}/reading-state/complete`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ book_id: bookId }),
  });

  return parseResponse<ReadingStateSnapshot>(response, 'Não foi possível concluir a leitura atual.');
}

export async function getCurrentReadingSessions(): Promise<CurrentReadingSessionsSnapshot> {
  const response = await fetch(`${API_URL}/reading-sessions/current`);
  return parseResponse<CurrentReadingSessionsSnapshot>(
    response,
    'Não foi possível carregar as sessões de leitura.',
  );
}

export async function createReadingSession(payload: {
  bookId: number;
  progressText: string;
  feeling: FeelingValue;
  note: string;
}): Promise<CurrentReadingSessionsSnapshot> {
  const response = await fetch(`${API_URL}/reading-sessions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      book_id: payload.bookId,
      progress_text: payload.progressText,
      feeling: payload.feeling,
      note: payload.note,
    }),
  });

  return parseResponse<CurrentReadingSessionsSnapshot>(
    response,
    'Não foi possível salvar a sessão de leitura.',
  );
}

export async function getCurrentReadingReflections(): Promise<CurrentReadingReflectionsSnapshot> {
  const response = await fetch(`${API_URL}/reading-reflections/current`);
  return parseResponse<CurrentReadingReflectionsSnapshot>(
    response,
    'Não foi possível carregar a mediação da leitura.',
  );
}

export async function getCurrentReadingTrajectory(): Promise<CurrentReadingTrajectorySnapshot> {
  const response = await fetch(`${API_URL}/reading-trajectory/current`);
  return parseResponse<CurrentReadingTrajectorySnapshot>(
    response,
    'Não foi possível carregar o percurso da leitura.',
  );
}

export async function getCompletedBooks(): Promise<CompletedBookSummary[]> {
  const response = await fetch(`${API_URL}/completed-books`);
  return parseResponse<CompletedBookSummary[]>(response, 'Não foi possível carregar os livros concluídos.');
}

export async function createReadingReflections(payload: {
  readingSessionId: number;
  reflections: ReadingReflectionInput[];
}): Promise<CurrentReadingReflectionsSnapshot> {
  const response = await fetch(`${API_URL}/reading-reflections`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      reading_session_id: payload.readingSessionId,
      reflections: payload.reflections,
    }),
  });

  return parseResponse<CurrentReadingReflectionsSnapshot>(
    response,
    'Não foi possível salvar as reflexões da sessão.',
  );
}

export async function generateReadingFeedback(readingSessionId: number): Promise<{ feedback_text: string }> {
  const response = await fetch(`${API_URL}/reading-feedback/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reading_session_id: readingSessionId }),
  });

  return parseResponse<{ feedback_text: string }>(
    response,
    'Não foi possível gerar um retorno sobre a leitura.',
  );
}
