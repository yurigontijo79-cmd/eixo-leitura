from collections import Counter

from app.schemas.reading_session import FeelingValue
from app.schemas.reading_trajectory import CurrentReadingTrajectorySnapshot, TrajectoryLabel

POSITIVE_FEELINGS: set[FeelingValue] = {"fluida", "empolgante"}
RESISTANT_FEELINGS: set[FeelingValue] = {"travada", "confusa"}


def _dominant_feeling(recent_feelings: list[FeelingValue]) -> FeelingValue | None:
    if not recent_feelings:
        return None

    counts = Counter(recent_feelings)
    dominant, dominant_count = counts.most_common(1)[0]
    tied_feelings = [feeling for feeling, count in counts.items() if count == dominant_count]
    if len(tied_feelings) > 1:
        return None
    return dominant


def _label_and_text(
    session_count: int,
    recent_feelings: list[FeelingValue],
    dominant_feeling: FeelingValue | None,
) -> tuple[TrajectoryLabel, str]:
    if session_count <= 2:
        return ("forming", "Sua leitura ainda está se formando, mas já começou a ganhar ritmo.")

    positive_count = sum(feeling in POSITIVE_FEELINGS for feeling in recent_feelings)
    resistant_count = sum(feeling in RESISTANT_FEELINGS for feeling in recent_feelings)
    dense_count = sum(feeling == "densa" for feeling in recent_feelings)
    latest_feeling = recent_feelings[0]
    recent_positive_after_density = "densa" in recent_feelings[1:] and latest_feeling in POSITIVE_FEELINGS
    mixed_recently = len(set(recent_feelings[:4])) >= 3 and dominant_feeling is None

    if positive_count >= 3 and positive_count >= resistant_count + 1:
        return ("continuity", "Há sinais de continuidade viva nesse percurso.")

    if resistant_count >= 2 and dominant_feeling in RESISTANT_FEELINGS:
        return ("resistance", "Essa leitura parece pedir mais desaceleração e retomada.")

    if dense_count >= 2 and recent_positive_after_density:
        return ("assimilation", "O caminho parece denso, mas algo começou a se abrir com mais corpo.")

    if mixed_recently:
        return ("oscillating", "O caminho ainda está um pouco oscilante, mas algo começa a se firmar.")

    if dominant_feeling == "densa" or dense_count >= 2:
        return ("assimilation", "Sua leitura parece estar num tempo de assimilação cuidadosa.")

    return ("open", "Seu percurso segue aberto, com um fio de leitura começando a se firmar.")


def build_reading_trajectory(
    current_book: dict | None,
    recent_feelings: list[FeelingValue],
    session_count: int,
) -> CurrentReadingTrajectorySnapshot:
    if not current_book:
        return CurrentReadingTrajectorySnapshot(
            current_book=None,
            session_count=0,
            recent_feelings=[],
            dominant_feeling=None,
            trajectory_label=None,
            trajectory_text=None,
        )

    dominant_feeling = _dominant_feeling(recent_feelings)
    trajectory_label, trajectory_text = _label_and_text(session_count, recent_feelings, dominant_feeling)

    return CurrentReadingTrajectorySnapshot(
        current_book=current_book,
        session_count=session_count,
        recent_feelings=recent_feelings,
        dominant_feeling=dominant_feeling,
        trajectory_label=trajectory_label,
        trajectory_text=trajectory_text,
    )
