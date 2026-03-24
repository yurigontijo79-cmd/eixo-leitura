from typing import Literal, TypedDict

from app.schemas.reading_reflection import ReflectionQuestion
from app.schemas.reading_session import FeelingValue

ReflectionIntention = Literal[
    "continuity",
    "difficulty",
    "impact",
    "curiosity",
    "clarity",
    "rhythm",
    "resistance",
    "opening",
]


class ReflectionQuestionSeed(TypedDict):
    question_key: str
    question_text: str
    intention: ReflectionIntention


QUESTION_BANK: list[ReflectionQuestionSeed] = [
    {"question_key": "continuity_desire", "question_text": "Você ficou com vontade de continuar?", "intention": "continuity"},
    {"question_key": "continuity_next_step", "question_text": "Qual seria o próximo passo natural da leitura?", "intention": "continuity"},
    {"question_key": "continuity_return", "question_text": "Você voltaria a esse trecho com facilidade?", "intention": "continuity"},
    {"question_key": "difficulty_block", "question_text": "Teve algo que travou sua leitura?", "intention": "difficulty"},
    {"question_key": "difficulty_weight", "question_text": "O que pareceu mais pesado hoje?", "intention": "difficulty"},
    {"question_key": "difficulty_friction", "question_text": "Onde a leitura raspou mais?", "intention": "difficulty"},
    {"question_key": "impact_lit_up", "question_text": "O que mais ficou aceso na cabeça?", "intention": "impact"},
    {"question_key": "impact_opened_closed", "question_text": "O trecho de hoje abriu ou fechou caminhos?", "intention": "impact"},
    {"question_key": "impact_trace", "question_text": "O que deixou rastro depois da leitura?", "intention": "impact"},
    {"question_key": "curiosity_pull", "question_text": "O que puxou sua curiosidade?", "intention": "curiosity"},
    {"question_key": "curiosity_resistance", "question_text": "Você sentiu mais curiosidade ou resistência?", "intention": "curiosity"},
    {"question_key": "curiosity_gap", "question_text": "O que te fez querer entender mais?", "intention": "curiosity"},
    {"question_key": "clarity_clearer", "question_text": "Algo ficou mais claro hoje?", "intention": "clarity"},
    {"question_key": "clarity_foggy", "question_text": "O que ainda ficou meio nublado?", "intention": "clarity"},
    {"question_key": "clarity_anchor", "question_text": "Teve algum ponto em que a leitura assentou melhor?", "intention": "clarity"},
    {"question_key": "rhythm_pace", "question_text": "O ritmo da leitura te puxou ou te segurou?", "intention": "rhythm"},
    {"question_key": "rhythm_breath", "question_text": "Você leu num passo tranquilo ou entre pausas?", "intention": "rhythm"},
    {"question_key": "resistance_hold", "question_text": "Teve algo que você quase largou pelo caminho?", "intention": "resistance"},
    {"question_key": "resistance_return", "question_text": "O que pediu mais insistência da sua parte?", "intention": "resistance"},
    {"question_key": "opening_window", "question_text": "Esse trecho abriu alguma janela nova?", "intention": "opening"},
    {"question_key": "opening_shift", "question_text": "Algo mudou de lugar dentro da leitura hoje?", "intention": "opening"},
]

INTENTION_PRIORITY_BY_FEELING: dict[FeelingValue, list[ReflectionIntention]] = {
    "travada": ["difficulty", "clarity", "resistance", "continuity"],
    "confusa": ["clarity", "difficulty", "opening", "impact"],
    "fluida": ["continuity", "rhythm", "curiosity", "impact"],
    "empolgante": ["curiosity", "opening", "continuity", "impact"],
    "densa": ["clarity", "impact", "rhythm", "continuity"],
}


def _question_from_seed(seed: ReflectionQuestionSeed) -> ReflectionQuestion:
    return ReflectionQuestion(question_key=seed["question_key"], question_text=seed["question_text"])


def _append_candidates(
    selected: list[ReflectionQuestion],
    candidates: list[ReflectionQuestionSeed],
    used_question_keys: set[str],
    blocked_question_keys: set[str],
    limit: int,
) -> None:
    for question in candidates:
        if question["question_key"] in used_question_keys:
            continue
        if question["question_key"] in blocked_question_keys:
            continue
        if any(item.question_key == question["question_key"] for item in selected):
            continue

        selected.append(_question_from_seed(question))
        if len(selected) == limit:
            return


def _sorted_candidates(
    candidates: list[ReflectionQuestionSeed],
    recent_question_history: list[str],
    cycle_index: int,
) -> list[ReflectionQuestionSeed]:
    if not candidates:
        return []

    recency_by_key: dict[str, int] = {}
    usage_by_key: dict[str, int] = {}
    for position, question_key in enumerate(recent_question_history):
        usage_by_key[question_key] = usage_by_key.get(question_key, 0) + 1
        recency_by_key.setdefault(question_key, position)

    rotated_indices = {
        candidate["question_key"]: (index - cycle_index) % len(candidates)
        for index, candidate in enumerate(candidates)
    }

    return sorted(
        candidates,
        key=lambda candidate: (
            0 if candidate["question_key"] not in usage_by_key else 1,
            usage_by_key.get(candidate["question_key"], 0),
            recency_by_key.get(candidate["question_key"], len(recent_question_history) + 1),
            rotated_indices[candidate["question_key"]],
        ),
    )


def select_questions_for_feeling(
    feeling: FeelingValue,
    used_question_keys: set[str],
    recent_question_history: list[str],
    cycle_index: int = 0,
    limit: int = 2,
) -> list[ReflectionQuestion]:
    priorities = INTENTION_PRIORITY_BY_FEELING[feeling]
    selected: list[ReflectionQuestion] = []
    recent_question_keys = set(recent_question_history)

    for intention in priorities:
        intention_questions = _sorted_candidates(
            [question for question in QUESTION_BANK if question["intention"] == intention],
            recent_question_history,
            cycle_index,
        )
        _append_candidates(selected, intention_questions, used_question_keys, recent_question_keys, limit)
        if len(selected) == limit:
            return selected

    for intention in priorities:
        intention_questions = _sorted_candidates(
            [question for question in QUESTION_BANK if question["intention"] == intention],
            recent_question_history,
            cycle_index,
        )
        _append_candidates(selected, intention_questions, used_question_keys, set(), limit)
        if len(selected) == limit:
            return selected

    sorted_question_bank = _sorted_candidates(QUESTION_BANK, recent_question_history, cycle_index)
    _append_candidates(selected, sorted_question_bank, used_question_keys, recent_question_keys, limit)
    if len(selected) == limit:
        return selected

    _append_candidates(selected, sorted_question_bank, used_question_keys, set(), limit)
    return selected
