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
      <header className="page-header">
        <p className="eyebrow">Início</p>
        <h2>Que caminho faz sentido agora?</h2>
      </header>

      <div className="home-workspace">
        <div className="home-primary-stack">
          <section className={`panel home-axis${hasCurrentReading ? '' : ' home-axis-empty'}`}>
            <div className="panel-header">
              <h3>{hasCurrentReading ? 'Continuidade' : 'Retomada'}</h3>
              <span>{hasCurrentReading ? 'leitura em curso' : 'sem leitura ativa'}</span>
            </div>
            {hasCurrentReading ? (
              <div className="home-hero-body">
                <div>
                  <p className="book-state-chip">Em leitura</p>
                  <h3>{readingState.current_reading?.title}</h3>
                  <p className="book-meta">{readingState.current_reading?.author}</p>
                  <p className="placeholder subtle-copy">
                    {readingSessions.last_session
                      ? `Você parou em: ${readingSessions.last_session.progress_text}`
                      : 'Abra uma sessão breve e deixe o fio da leitura visível.'}
                  </p>
                </div>
                <Link className="action-button" to="/current">
                  abrir leitura atual
                </Link>
              </div>
            ) : (
              <div className="home-hero-body">
                <p className="placeholder emphasis">Nenhuma leitura está em andamento agora.</p>
                <p className="placeholder subtle-copy">
                  Pode ser um bom momento para retomar um livro guardado ou abrir espaço para outro começo.
                </p>
              </div>
            )}
          </section>

          <section className="panel panel-soft">
            <div className="panel-header">
              <h3>Novos caminhos</h3>
              <span>{suggestions.featured.length} em destaque</span>
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
                      ? 'Sem muito histórico ainda, o produto abre caminhos novos com delicadeza.'
                      : 'O percurso recente ajusta discretamente o que faz mais sentido agora.'}
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
          </section>
        </div>

        <aside className="home-secondary-stack">
          <section className="panel panel-soft compact-panel">
            <div className="panel-header">
              <h3>Continuidade</h3>
            </div>

            {readingState.current_reading ? (
              <div className="stacked-copy">
                <p className="placeholder emphasis">Tudo pronto para continuar o livro em curso.</p>
                {readingSessions.last_session && (
                  <p className="placeholder subtle-copy">
                    Última sensação: leitura {readingSessions.last_session.feeling}
                  </p>
                )}
                {readingTrajectory.trajectory_text && (
                  <p className="placeholder subtle-copy">{readingTrajectory.trajectory_text}</p>
                )}
                <Link className="ghost-button command-secondary" to="/current">
                  abrir leitura atual
                </Link>
              </div>
            ) : (
              <div className="stacked-copy">
                <p className="placeholder emphasis">Nenhuma leitura está em andamento agora.</p>
                <p className="placeholder subtle-copy">
                  Pode ser um bom momento para retomar um livro guardado ou abrir espaço para outro começo.
                </p>
              </div>
            )}
          </section>

          <section className={`panel panel-soft compact-panel${!hasCurrentReading ? ' shortlist-emphasis' : ''}`}>
            <div className="panel-header">
              <h3>{hasCurrentReading ? 'Shortlist' : 'Próximo passo possível'}</h3>
              <span>{readingState.shortlist.length} guardados</span>
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
              <p className="placeholder">Quando algo merecer ficar por perto, ele pode repousar aqui.</p>
            )}
          </section>

          <section className="panel panel-soft compact-panel">
            <div className="panel-header compact-gap">
              <h3>Concluídos</h3>
              <span>{completedBooks.length} memórias</span>
            </div>
            {completedBooks.length > 0 ? (
              <div className="stacked-copy">
                <p className="placeholder emphasis">{completedBooks[0].closing_text}</p>
                <p className="placeholder subtle-copy">
                  Último encerramento: {completedBooks[0].title}, em {completedBooks[0].author}
                </p>
                <Link className="ghost-button command-secondary" to="/completed">
                  ver concluídos
                </Link>
              </div>
            ) : (
              <p className="placeholder">Os livros concluídos deixam aqui uma memória breve do que se encerrou.</p>
            )}
          </section>
        </aside>
      </div>

      {(suggestions.shortlist_candidates.length > 0 || suggestions.fallback_candidates.length > 0) && (
        <div className="split-panels suggestion-support-grid">
          {suggestions.shortlist_candidates.length > 0 && (
            <section className="panel compact-panel">
              <div className="panel-header compact-gap">
                <h3>Da sua shortlist</h3>
              </div>
              <div className="mini-list">
                {suggestions.shortlist_candidates.map((book) => (
                  <Link key={book.id} className="mini-list-item" to={`/books/${book.id}`}>
                    <strong>{book.title}</strong>
                    <span>{book.author}</span>
                  </Link>
                ))}
              </div>
            </section>
          )}

          {suggestions.fallback_candidates.length > 0 && (
            <section className="panel compact-panel">
              <div className="panel-header compact-gap">
                <h3>Outros caminhos possíveis</h3>
              </div>
              <div className="mini-list">
                {suggestions.fallback_candidates.map((book) => (
                  <Link key={book.id} className="mini-list-item" to={`/books/${book.id}`}>
                    <strong>{book.title}</strong>
                    <span>{book.author}</span>
                  </Link>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      <div className="split-panels three-columns">
        <section className="panel compact-panel">
          <div className="panel-header">
            <h3>Estado do catálogo</h3>
            <span>{suggestions.featured.length + readingState.shortlist.length} itens em foco</span>
          </div>
          <p className="placeholder subtle-copy">
            O módulo organiza caminhos, continuidade e memória para manter o percurso de leitura estável.
          </p>
        </section>
      </div>
    </div>
  );
}
