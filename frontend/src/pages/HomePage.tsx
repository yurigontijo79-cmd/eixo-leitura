import { Link } from 'react-router-dom';
import { BookCard } from '../components/BookCard';
import { useLibrary } from '../context/LibraryContext';

export function HomePage() {
  const { completedBooks, readingState, readingSessions, readingTrajectory, suggestions, loading, error, refreshAll } =
    useLibrary();

  const shortlistPreview = readingState.shortlist.slice(0, 3);
  const hasCurrentReading = Boolean(readingState.current_reading);

  return (
    <div className="page-stack module-page home-module">
      <header className="page-header home-header">
        <p className="eyebrow">Início</p>
        <h2>{hasCurrentReading ? 'Retomar leitura' : 'Escolher próximo caminho'}</h2>
      </header>

      <div className="home-decision-layout">
        <section className="panel home-decision-axis">
          {hasCurrentReading ? (
            <>
              <div className="panel-header">
                <h3>Leitura atual</h3>
                <span>ação principal</span>
              </div>
              <div className="home-axis-content">
                <p className="book-state-chip">Em leitura</p>
                <h3>{readingState.current_reading?.title}</h3>
                <p className="book-meta">{readingState.current_reading?.author}</p>
                <p className="placeholder subtle-copy">
                  {readingSessions.last_session
                    ? `Você parou em: ${readingSessions.last_session.progress_text}`
                    : 'Abra uma sessão breve e registre o ponto de continuidade.'}
                </p>
                {readingTrajectory.trajectory_text && (
                  <p className="placeholder subtle-copy">{readingTrajectory.trajectory_text}</p>
                )}
                <Link className="action-button" to="/current">
                  abrir leitura atual
                </Link>
              </div>
            </>
          ) : (
            <>
              <div className="panel-header">
                <h3>Próximos caminhos</h3>
                <span>ação principal</span>
              </div>

              {loading && <p className="placeholder">Reunindo os próximos caminhos...</p>}
              {error && (
                <div className="stacked-copy">
                  <p className="placeholder">{error}</p>
                  <button className="ghost-button" type="button" onClick={() => void refreshAll()}>
                    tentar de novo
                  </button>
                </div>
              )}
              {!loading && !error && (
                <div className="stacked-copy">
                  <p className="placeholder subtle-copy">
                    {suggestions.suggestion_context === 'shortlist_em_primeiro_plano'
                      ? 'Os livros já guardados com mais intenção aparecem primeiro.'
                      : suggestions.suggestion_context === 'catalogo_aberto_com_prioridade_ao_nao_tocado'
                        ? 'Sem histórico forte, o sistema prioriza opções abertas e estáveis.'
                        : 'O percurso recente ajusta discretamente os próximos caminhos.'}
                  </p>

                  {suggestions.featured.length > 0 ? (
                    <div className="book-list">
                      {suggestions.featured.map((book) => (
                        <BookCard key={book.id} book={book} />
                      ))}
                    </div>
                  ) : (
                    <p className="placeholder">
                      Ainda não há um caminho puxando mais forte. Quando seu percurso ganhar corpo, este bloco responde.
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </section>

        <aside className="home-support-stack">
          {hasCurrentReading && (
            <section className="panel panel-soft compact-panel">
              <div className="panel-header compact-gap">
                <h3>Próximos caminhos</h3>
                <span>{suggestions.featured.length} opções</span>
              </div>
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
                <div className="book-list support-list">
                  {suggestions.featured.slice(0, 4).map((book) => (
                    <BookCard key={book.id} book={book} />
                  ))}
                </div>
              ) : (
                !loading && !error && <p className="placeholder">Sem novas opções fortes neste momento.</p>
              )}
            </section>
          )}

          {!hasCurrentReading && (
            <section className="panel panel-soft compact-panel">
              <div className="panel-header compact-gap">
                <h3>Continuidade</h3>
              </div>
              <p className="placeholder subtle-copy">
                Nenhuma leitura ativa agora. Escolha um próximo caminho para iniciar um novo percurso.
              </p>
            </section>
          )}

          <section className={`panel panel-soft compact-panel${!hasCurrentReading ? ' shortlist-emphasis' : ''}`}>
            <div className="panel-header">
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
              <p className="placeholder">Quando algo merecer ficar por perto, ele aparece aqui.</p>
            )}
          </section>

          <section className="home-memory-note">
            {completedBooks.length > 0 ? (
              <>
                <p className="eyebrow soft">Memória</p>
                <p className="placeholder emphasis">{completedBooks[0].closing_text}</p>
                <Link className="ghost-button command-secondary" to="/completed">
                  ver concluídos
                </Link>
              </>
            ) : (
              <p className="placeholder subtle-copy">Concluídos aparecem aqui como memória breve do percurso.</p>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
