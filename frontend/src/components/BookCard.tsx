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
    <Link className="book-row" to={`/books/${book.id}`}>
      <div className="book-row-main">
        <h3>{book.title}</h3>
        <p className="book-meta">{book.author}</p>
      </div>
      <div className="book-row-side">
        {book.state && <p className="book-state-chip subtle">{stateLabel[book.state]}</p>}
        <span className="book-row-open">abrir</span>
      </div>
    </Link>
  );
}
