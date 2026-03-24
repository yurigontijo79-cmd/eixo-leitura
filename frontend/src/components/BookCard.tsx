import { Link } from 'react-router-dom';
import type { Book } from '../types/book';

type VisibleState = Exclude<Book['state'], null>;

const stateLabel: Partial<Record<VisibleState, string>> = {
  current: 'Em leitura',
  shortlist: 'Talvez depois',
  rejected: 'Oculto da prioridade',
  completed: 'Concluído',
};

export function BookCard({ book }: { book: Book }) {
  return (
    <article className="book-row">
      <div className="book-row-main">
        <h3>{book.title}</h3>
        <p className="book-meta">{book.author}</p>
        {book.state && <p className="book-state-chip subtle">{stateLabel[book.state]}</p>}
      </div>
      <Link className="ghost-button command-secondary book-row-action" to={`/books/${book.id}`}>
        abrir livro
      </Link>
    </article>
  );
}
