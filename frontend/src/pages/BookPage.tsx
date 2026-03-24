import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useLibrary } from '../context/LibraryContext';
import type { ActiveReadingState, Book } from '../types/book';

const actions: Array<{ value: ActiveReadingState; label: string }> = [
  { value: 'current', label: 'Começar por aqui' },
  { value: 'shortlist', label: 'Guardar para depois' },
  { value: 'rejected', label: 'Tirar do foco' },
];

type VisibleState = Exclude<Book['state'], null>;

const stateCopy: Partial<Record<VisibleState, string>> = {
  current: 'Este é o livro que acompanha seu percurso agora.',
  shortlist: 'Este livro está guardado por perto para outro momento.',
  rejected: 'Este livro saiu do foco por enquanto.',
  completed: 'Este livro já encontrou um fechamento no seu percurso.',
};

export function BookPage() {
  const { id } = useParams();
  const { books, loading, error, refreshAll, setBookState } = useLibrary();
  const book = books.find((item) => item.id === Number(id));
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackTone, setFeedbackTone] = useState<'success' | 'error'>('success');
  const [submitting, setSubmitting] = useState<ActiveReadingState | null>(null);

  async function handleAction(action: ActiveReadingState) {
    if (!book) return;

    setSubmitting(action);
    setFeedback(null);
    setFeedbackTone('success');

    try {
      await setBookState(book.id, action);
      const messages: Record<ActiveReadingState, string> = {
        current: 'A leitura pode começar por aqui.',
        shortlist: 'Este livro ficou guardado para mais adiante.',
        rejected: 'Tudo bem deixar este livro fora do foco agora.',
      };
      setFeedback(messages[action]);
    } catch (requestError) {
      setFeedbackTone('error');
      setFeedback(
        requestError instanceof Error ? requestError.message : 'Não foi possível ajustar esse lugar do livro agora.',
      );
    } finally {
      setSubmitting(null);
    }
  }

  if (loading) {
    return <p className="placeholder">Abrindo o livro...</p>;
  }

  if (error) {
    return (
      <section className="panel">
        <p className="placeholder">{error}</p>
        <div className="actions-row">
          <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
            tentar de novo
          </button>
          <Link className="ghost-button command-secondary" to="/">
            voltar ao início
          </Link>
        </div>
      </section>
    );
  }

  if (!book) {
    return (
      <section className="panel">
        <p className="placeholder">Esse livro não apareceu por aqui.</p>
        <Link className="ghost-button command-secondary" to="/">
          voltar ao início
        </Link>
      </section>
    );
  }

  return (
    <div className="page-stack module-page">
      <header className="page-header">
        <p className="eyebrow">Livro</p>
        <h2>{book.title}</h2>
        <p className="book-meta large">{book.author}</p>
      </header>

      <section className="panel book-detail-panel">
        <p className="book-description">{book.description}</p>
        {book.state && <p className="book-state-chip">{stateCopy[book.state]}</p>}

        <div className="actions-row">
          {actions.map((action) => (
            <button
              key={action.value}
              type="button"
              className={`action-button${book.state === action.value ? ' action-button-active' : ''}`}
              disabled={submitting !== null}
              onClick={() => handleAction(action.value)}
            >
              {submitting === action.value ? 'salvando...' : action.label}
            </button>
          ))}
        </div>

        {feedback && <p className={`status-note status-note-${feedbackTone}`}>{feedback}</p>}
      </section>
    </div>
  );
}
