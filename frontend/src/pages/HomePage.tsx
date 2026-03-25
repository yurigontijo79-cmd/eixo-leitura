import { Link } from 'react-router-dom';
import { BookCard } from '../components/BookCard';
import { useLibrary } from '../context/LibraryContext';

export function HomePage() {
  const { completedBooks, readingState, readingSessions, suggestions, loading, error, refreshAll } = useLibrary();

  const shortlistPreview = readingState.shortlist.slice(0, 4);
  const hasCurrentReading = Boolean(readingState.current_reading);

  return (
    <div className="page-stack module-page reading-central">
      <header className="page-header home-header compact-module-header">
        <p className="eyebrow">Central de leitura</p>
        <h2>{hasCurrentReading ? 'Sessão em andamento' : 'Escolha seu próximo caminho'}</h2>
      </header>

      <div className="reading-central-layout">
        <section className={hasCurrentReading ? 'panel central-axis central-axis-reading' : 'central-axis-list'}>
          {hasCurrentReading ? (
            <>
              <div className="panel-header">
                <h3>Leitura atual</h3>
                <span>eixo principal</span>
              </div>

              <div className="central-current-block">
                <p className="book-state-chip">Em leitura</p>
                <h3>{readingState.current_reading?.title}</h3>
                <p className="book-meta">{readingState.current_reading?.author}</p>
                <p className="placeholder subtle-copy">
                  {readingSessions.last_session
                    ? `Último ponto: ${readingSessions.last_session.progress_text}`
                    : 'Ainda sem sessão registrada para este livro.'}
                </p>

                <div className="central-actions">
                  <Link className="action-button" to="/current">
                    continuar leitura
                  </Link>
                  <Link className="ghost-button command-secondary" to="/current">
                    registrar sessão
                  </Link>
                </div>
              </div>

              <div className="central-next-list">
                <div className="panel-header compact-gap">
                  <h3>Próximos caminhos</h3>
                  <span>{suggestions.featured.length}</span>
                </div>
                {loading && <p className="placeholder">Carregando caminhos...</p>}
                {error && (
                  <div className="stacked-copy">
                    <p className="placeholder">{error}</p>
                    <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
                      tentar de novo
                    </button>
                  </div>
                )}
                {!loading && !error && (
                  <div className="book-list">
                    {suggestions.featured.slice(0, 5).map((book) => (
                      <BookCard key={book.id} book={book} />
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <div className="panel-header">
                <h3>Lista de caminhos</h3>
                <span>eixo principal</span>
              </div>

              <p className="placeholder subtle-copy">
                Sem leitura ativa, esta lista vira seu ponto principal de decisão.
              </p>

              {loading && <p className="placeholder">Reunindo caminhos...</p>}
              {error && (
                <div className="stacked-copy">
                  <p className="placeholder">{error}</p>
                  <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
                    tentar de novo
                  </button>
                </div>
              )}

              {!loading && !error && suggestions.featured.length > 0 ? (
                <div className="book-list central-path-list">
                  {suggestions.featured.map((book) => (
                    <BookCard key={book.id} book={book} />
                  ))}
                </div>
              ) : (
                !loading && !error && <p className="placeholder">Sem caminhos em destaque agora.</p>
              )}
            </>
          )}
        </section>

        <aside className="central-support">
          <section className="panel panel-soft compact-panel support-panel">
            <div className="panel-header compact-gap">
              <h3>Guardados</h3>
              <span>{readingState.shortlist.length}</span>
            </div>
            {shortlistPreview.length > 0 ? (
              <div className="mini-list">
                {shortlistPreview.map((book) => (
                  <Link key={book.id} className="mini-list-item" to={`/books/${book.id}`}>
                    <strong>{book.title}</strong>
                    <span>{book.author}</span>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="placeholder">Nenhum guardado no momento.</p>
            )}
          </section>

          <section className="panel panel-soft compact-panel support-panel">
            <div className="panel-header compact-gap">
              <h3>Talvez depois</h3>
            </div>
            <p className="placeholder subtle-copy">Itens fora do foco imediato continuam acessíveis pelos detalhes.</p>
          </section>

          <section className="central-memory-strip">
            {completedBooks.length > 0 ? (
              <>
                <p className="eyebrow soft">Memória</p>
                <p className="placeholder emphasis">{completedBooks[0].closing_text}</p>
                <Link className="text-link" to="/completed">
                  abrir concluídos
                </Link>
              </>
            ) : (
              <p className="placeholder subtle-copy">Sem memória de concluídos por enquanto.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
