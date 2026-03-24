import { Link, useLocation } from 'react-router-dom';
import { useLibrary } from '../context/LibraryContext';

function formatCompletedDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(new Date(value));
}

export function CompletedBooksPage() {
  const { completedBooks, loading, error, refreshAll } = useLibrary();
  const location = useLocation();
  const notice = (location.state as { notice?: string } | null)?.notice ?? null;

  if (loading) {
    return <p className="placeholder">Reunindo os percursos concluídos...</p>;
  }

  if (error) {
    return (
      <section className="panel compact-panel">
        <div className="stacked-copy">
          <p className="placeholder">{error}</p>
          <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
            tentar de novo
          </button>
        </div>
      </section>
    );
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <p className="eyebrow">Concluídos</p>
        <h2>Livros que já encontraram um fechamento</h2>
      </header>

      {notice && <p className="status-note status-note-success">{notice}</p>}

      <section className="panel compact-panel">
        <div className="panel-header compact-gap">
          <h3>Memória dos percursos encerrados</h3>
          <span>{completedBooks.length} concluídos</span>
        </div>

        {completedBooks.length > 0 ? (
          <div className="completed-list">
            {completedBooks.map((book) => (
              <article key={book.id} className="session-card completed-card">
                <div className="completed-card-header">
                  <div>
                    <h4>{book.title}</h4>
                    <p className="book-meta">{book.author}</p>
                  </div>
                  <p className="session-meta">{formatCompletedDate(book.completed_at)}</p>
                </div>
                <p className="placeholder emphasis">{book.closing_text}</p>
                <p className="placeholder subtle-copy">
                  {book.total_sessions} sessões
                  {book.dominant_feeling ? ` · predominância de leitura ${book.dominant_feeling}` : ''}
                </p>
                <Link className="text-link" to={`/books/${book.id}`}>
                  ver livro
                </Link>
              </article>
            ))}
          </div>
        ) : (
          <p className="placeholder">
            Quando uma leitura se encerrar, ela deixa aqui uma memória breve do caminho que encontrou.
          </p>
        )}
      </section>
    </div>
  );
}
