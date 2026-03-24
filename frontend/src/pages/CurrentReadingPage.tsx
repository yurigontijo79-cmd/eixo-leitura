import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useLibrary } from '../context/LibraryContext';
import type { FeelingValue } from '../types/book';

const feelings: Array<{ value: FeelingValue; label: string }> = [
  { value: 'fluida', label: 'Fluida' },
  { value: 'densa', label: 'Densa' },
  { value: 'travada', label: 'Travada' },
  { value: 'empolgante', label: 'Empolgante' },
  { value: 'confusa', label: 'Confusa' },
];

function formatSessionDate(value: string) {
  return new Intl.DateTimeFormat('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function formatFeelingLabel(value: FeelingValue) {
  return `leitura ${value}`;
}

export function CurrentReadingPage() {
  const {
    readingState,
    readingSessions,
    readingReflections,
    readingTrajectory,
    loading,
    error,
    refreshAll,
    saveReadingSession,
    saveReadingReflections,
    generateSessionFeedback,
    completeCurrentReading,
  } = useLibrary();
  const navigate = useNavigate();
  const currentBook = readingState.current_reading;
  const [progressText, setProgressText] = useState('');
  const [feeling, setFeeling] = useState<FeelingValue>('fluida');
  const [note, setNote] = useState('');
  const [feedback, setFeedback] = useState<string | null>(null);
  const [feedbackTone, setFeedbackTone] = useState<'success' | 'error'>('success');
  const [reflectionFeedback, setReflectionFeedback] = useState<string | null>(null);
  const [reflectionFeedbackTone, setReflectionFeedbackTone] = useState<'success' | 'error'>('success');
  const [generatedFeedback, setGeneratedFeedback] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [savingReflections, setSavingReflections] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [reflectionAnswers, setReflectionAnswers] = useState<Record<string, string>>({});

  const suggestedQuestions = readingReflections.suggested_questions;
  const currentReflectionSession = readingReflections.current_session;
  const lastSessionFeedback = readingSessions.last_session?.feedback_text ?? null;

  useEffect(() => {
    const nextAnswers = suggestedQuestions.reduce<Record<string, string>>((accumulator, question) => {
      accumulator[question.question_key] = '';
      return accumulator;
    }, {});
    setReflectionAnswers(nextAnswers);
  }, [suggestedQuestions]);

  useEffect(() => {
    setGeneratedFeedback(lastSessionFeedback);
  }, [lastSessionFeedback]);

  const recentSessions = useMemo(() => readingSessions.recent_sessions, [readingSessions.recent_sessions]);
  const trajectoryMeta = useMemo(() => {
    if (!readingTrajectory.current_book || readingTrajectory.session_count === 0) {
      return null;
    }

    const pieces = [`${readingTrajectory.session_count} sessões`];
    if (readingTrajectory.dominant_feeling) {
      pieces.push(`predomínio de ${formatFeelingLabel(readingTrajectory.dominant_feeling)}`);
    }
    return pieces.join(' · ');
  }, [readingTrajectory]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentBook) return;

    setSubmitting(true);
    setFeedback(null);
    setFeedbackTone('success');
    setReflectionFeedback(null);
    setGeneratedFeedback(null);

    try {
      await saveReadingSession({
        bookId: currentBook.id,
        progressText,
        feeling,
        note,
      });
      setFeedback('Sessão guardada no fio da leitura.');
      setProgressText('');
      setFeeling('fluida');
      setNote('');
    } catch (requestError) {
      setFeedbackTone('error');
      setFeedback(
        requestError instanceof Error ? requestError.message : 'Não foi possível guardar esta sessão agora.',
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSaveReflections(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!currentReflectionSession || suggestedQuestions.length === 0) return;

    setSavingReflections(true);
    setReflectionFeedback(null);
    setReflectionFeedbackTone('success');

    try {
      await saveReadingReflections({
        readingSessionId: currentReflectionSession.id,
        reflections: suggestedQuestions.map((question) => ({
          question_key: question.question_key,
          question_text: question.question_text,
          answer_text: reflectionAnswers[question.question_key] ?? '',
        })),
      });
      setReflectionFeedback('Reflexão guardada junto da sessão.');

      try {
        const feedbackText = await generateSessionFeedback(currentReflectionSession.id);
        setGeneratedFeedback(feedbackText);
      } catch (requestError) {
        setReflectionFeedbackTone('error');
        setReflectionFeedback(
          requestError instanceof Error
            ? requestError.message
            : 'A reflexão foi salva, mas o retorno breve não pôde ser gerado agora.',
        );
      }
    } catch (requestError) {
      setReflectionFeedbackTone('error');
      setReflectionFeedback(
        requestError instanceof Error ? requestError.message : 'Não foi possível guardar a reflexão agora.',
      );
    } finally {
      setSavingReflections(false);
    }
  }

  async function handleCompleteReading() {
    if (!currentBook) return;

    const shouldComplete = window.confirm(
      `Concluir a leitura de "${currentBook.title}" e guardar o percurso vivido até aqui?`,
    );
    if (!shouldComplete) {
      return;
    }

    setCompleting(true);
    setFeedback(null);
    setFeedbackTone('success');

    try {
      await completeCurrentReading(currentBook.id);
      await navigate('/completed', {
        state: {
          notice: `A leitura de "${currentBook.title}" foi encerrada e permaneceu guardada no seu percurso.`,
        },
      });
    } catch (requestError) {
      setFeedbackTone('error');
      setFeedback(
        requestError instanceof Error ? requestError.message : 'Não foi possível concluir a leitura agora.',
      );
    } finally {
      setCompleting(false);
    }
  }

  if (loading) {
    return <p className="placeholder">Carregando leitura atual...</p>;
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
        <p className="eyebrow">Leitura atual</p>
        <h2>{currentBook ? currentBook.title : 'Você ainda não iniciou uma leitura'}</h2>
        {currentBook && <p className="book-meta large">{currentBook.author}</p>}
      </header>

      <section className="panel reading-focus-panel">
        {currentBook ? (
          <div className="reading-session-layout">
            <div className="stacked-copy relaxed">
              <p className="book-state-chip">Em leitura</p>
              <p className="book-description">{currentBook.description}</p>
              <Link className="ghost-button" to={`/books/${currentBook.id}`}>
                ver detalhes do livro
              </Link>
            </div>

            <div className="session-column">
              <div className="panel-header compact-gap">
                <h3>Guardar esta sessão</h3>
              </div>
              <form className="session-form" onSubmit={handleSubmit}>
                <label className="field-group">
                  <span>Até onde fui</span>
                  <input
                    required
                    value={progressText}
                    onChange={(event) => setProgressText(event.target.value)}
                    placeholder="capítulo 2, página 48, introdução..."
                  />
                </label>

                <label className="field-group">
                  <span>Como foi a leitura?</span>
                  <select value={feeling} onChange={(event) => setFeeling(event.target.value as FeelingValue)}>
                    {feelings.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="field-group">
                  <span>Nota rápida</span>
                  <textarea
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    rows={3}
                    placeholder="Opcional. Uma impressão breve para lembrar o tom da leitura."
                  />
                </label>

                <button className="action-button session-submit" type="submit" disabled={submitting}>
                  {submitting ? 'guardando...' : 'Guardar sessão'}
                </button>
                <button
                  className="ghost-button completion-button"
                  type="button"
                  disabled={completing}
                  onClick={handleCompleteReading}
                >
                  {completing ? 'concluindo...' : 'Concluir leitura'}
                </button>
              </form>

              {feedback && <p className={`status-note status-note-${feedbackTone}`}>{feedback}</p>}
            </div>
          </div>
        ) : (
          <div className="stacked-copy">
            <p className="placeholder">
              Quando um livro entrar em leitura, este espaço passa a guardar o percurso com mais nitidez.
            </p>
            <Link className="ghost-button" to="/">
              voltar ao início
            </Link>
          </div>
        )}
      </section>

      {currentBook && readingTrajectory.trajectory_text && (
        <section className="panel compact-panel trajectory-panel">
          <div className="panel-header compact-gap">
            <div>
              <p className="eyebrow soft">Seu percurso até aqui</p>
              <h3>Memória breve da leitura</h3>
            </div>
          </div>
          <p className="placeholder emphasis">{readingTrajectory.trajectory_text}</p>
          {trajectoryMeta && <p className="placeholder subtle-copy">{trajectoryMeta}</p>}
        </section>
      )}

      {currentBook && currentReflectionSession && (
        <section className="panel reflection-panel">
          <div className="panel-header compact-gap">
            <div>
              <p className="eyebrow soft">Pensando no que você leu</p>
              <h3>Mediação curta</h3>
              <p className="placeholder subtle-note">As perguntas mudam discretamente conforme o percurso recente.</p>
            </div>
          </div>

          {suggestedQuestions.length > 0 ? (
            <form className="reflection-form" onSubmit={handleSaveReflections}>
              {suggestedQuestions.map((question) => (
                <label key={question.question_key} className="field-group">
                  <span>{question.question_text}</span>
                  <textarea
                    required
                    rows={2}
                    value={reflectionAnswers[question.question_key] ?? ''}
                    onChange={(event) =>
                      setReflectionAnswers((current) => ({
                        ...current,
                        [question.question_key]: event.target.value,
                      }))
                    }
                    placeholder="Resposta breve, só o suficiente para guardar o fio da leitura."
                  />
                </label>
              ))}

              <button className="action-button session-submit" type="submit" disabled={savingReflections}>
                {savingReflections ? 'guardando...' : 'Guardar reflexão'}
              </button>
            </form>
          ) : (
            <p className="placeholder">
              A sessão mais recente já recebeu a camada breve de mediação prevista por agora.
            </p>
          )}

          {reflectionFeedback && (
            <p className={`status-note status-note-${reflectionFeedbackTone}`}>{reflectionFeedback}</p>
          )}
          {generatedFeedback && (
            <div className="feedback-echo">
              <p className="eyebrow soft">Um retorno sobre sua leitura</p>
              <p>{generatedFeedback}</p>
            </div>
          )}
        </section>
      )}

      {currentBook && (
        <div className="split-panels session-history-grid">
          <section className="panel compact-panel">
            <div className="panel-header compact-gap">
              <h3>Última sessão</h3>
            </div>
            {readingSessions.last_session ? (
              <article className="session-card featured-session">
                <p className="session-meta">{formatSessionDate(readingSessions.last_session.created_at)}</p>
                <h4>{readingSessions.last_session.progress_text}</h4>
                <p className="book-state-chip subtle">{formatFeelingLabel(readingSessions.last_session.feeling)}</p>
                {readingSessions.last_session.reflections_count > 0 && (
                  <p className="reflection-marker">Com reflexão registrada</p>
                )}
                {readingSessions.last_session.has_feedback && <p className="feedback-marker">Com retorno salvo</p>}
                {readingSessions.last_session.feedback_text && (
                  <p className="placeholder emphasis">{readingSessions.last_session.feedback_text}</p>
                )}
                {readingSessions.last_session.note && (
                  <p className="placeholder emphasis">{readingSessions.last_session.note}</p>
                )}
              </article>
            ) : (
              <p className="placeholder">A primeira sessão guardada aparece aqui assim que o percurso começar.</p>
            )}
          </section>

          <section className="panel compact-panel">
            <div className="panel-header compact-gap">
              <h3>Sessões recentes</h3>
              <span>{recentSessions.length} lembranças</span>
            </div>
            {recentSessions.length > 0 ? (
              <div className="session-list">
                {recentSessions.map((session) => (
                  <article key={session.id} className="session-card">
                    <p className="session-meta">{formatSessionDate(session.created_at)}</p>
                    <strong>{session.progress_text}</strong>
                    <span className="session-feeling">{formatFeelingLabel(session.feeling)}</span>
                    {session.reflections_count > 0 && <p className="reflection-marker">Com reflexão</p>}
                    {session.has_feedback && <p className="feedback-marker">Com retorno</p>}
                    {session.note && <p className="placeholder">{session.note}</p>}
                  </article>
                ))}
              </div>
            ) : (
              <p className="placeholder">Ainda não há outras marcas deste percurso por aqui.</p>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
