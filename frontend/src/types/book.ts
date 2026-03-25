export type ReadingStateValue = 'current' | 'shortlist' | 'rejected' | 'completed';
export type ActiveReadingState = 'current' | 'shortlist' | 'rejected';
export type FeelingValue = 'fluida' | 'densa' | 'travada' | 'empolgante' | 'confusa';

export type Book = {
  id: number;
  title: string;
  author: string;
  description: string;
  state: ReadingStateValue | null;
};

export type ReadingStateSnapshot = {
  current_reading: Book | null;
  shortlist: Book[];
  rejected_count: number;
};

export type ReadingSession = {
  id: number;
  book_id: number;
  progress_text: string;
  feeling: FeelingValue;
  note: string | null;
  created_at: string;
  reflections_count: number;
  has_feedback: boolean;
  feedback_text: string | null;
};

export type CurrentReadingSessionsSnapshot = {
  current_book: Book | null;
  last_session: ReadingSession | null;
  recent_sessions: ReadingSession[];
};

export type ReflectionQuestion = {
  question_key: string;
  question_text: string;
};

export type ReadingReflectionInput = {
  question_key: string;
  question_text: string;
  answer_text: string;
};

export type CurrentReadingReflectionsSnapshot = {
  current_book: Book | null;
  current_session: ReadingSession | null;
  suggested_questions: ReflectionQuestion[];
};

export type TrajectoryLabel =
  | 'forming'
  | 'continuity'
  | 'resistance'
  | 'assimilation'
  | 'oscillating'
  | 'open';

export type CurrentReadingTrajectorySnapshot = {
  current_book: Book | null;
  session_count: number;
  recent_feelings: FeelingValue[];
  dominant_feeling: FeelingValue | null;
  trajectory_label: TrajectoryLabel | null;
  trajectory_text: string | null;
};

export type CompletedBookSummary = {
  id: number;
  title: string;
  author: string;
  completed_at: string;
  total_sessions: number;
  dominant_feeling: FeelingValue | null;
  closing_text: string;
};

export type SuggestionsSnapshot = {
  featured: Book[];
  shortlist_candidates: Book[];
  fallback_candidates: Book[];
  suggestion_context: string | null;
};
