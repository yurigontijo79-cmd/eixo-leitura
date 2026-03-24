import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { BookPage } from './pages/BookPage';
import { CompletedBooksPage } from './pages/CompletedBooksPage';
import { CurrentReadingPage } from './pages/CurrentReadingPage';
import { HomePage } from './pages/HomePage';

function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/books/:id" element={<BookPage />} />
        <Route path="/current" element={<CurrentReadingPage />} />
        <Route path="/completed" element={<CompletedBooksPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default App;
