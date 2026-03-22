import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

reading_session_module = types.ModuleType("app.schemas.reading_session")
reading_session_module.FeelingValue = str


@dataclass
class ReflectionQuestion:
    question_key: str
    question_text: str


reading_reflection_module = types.ModuleType("app.schemas.reading_reflection")
reading_reflection_module.ReflectionQuestion = ReflectionQuestion

sys.modules.setdefault("app.schemas.reading_session", reading_session_module)
sys.modules.setdefault("app.schemas.reading_reflection", reading_reflection_module)

from app.services.feedback_rules import build_feedback_text
from app.services.reflection_bank import select_questions_for_feeling


class ReflectionVariationTests(unittest.TestCase):
    def test_avoids_recent_questions_when_alternatives_exist(self) -> None:
        recent_question_history = [
            "continuity_desire",
            "continuity_next_step",
            "rhythm_pace",
            "curiosity_pull",
        ]

        questions = select_questions_for_feeling(
            "fluida",
            used_question_keys=set(),
            recent_question_history=recent_question_history,
            cycle_index=2,
            limit=2,
        )

        self.assertEqual(
            [question.question_key for question in questions],
            ["continuity_return", "rhythm_breath"],
        )

    def test_rotates_question_choice_when_candidates_are_equally_available(self) -> None:
        first_batch = select_questions_for_feeling(
            "travada",
            used_question_keys=set(),
            recent_question_history=[],
            cycle_index=0,
            limit=2,
        )
        second_batch = select_questions_for_feeling(
            "travada",
            used_question_keys=set(),
            recent_question_history=[],
            cycle_index=1,
            limit=2,
        )

        self.assertEqual(
            [question.question_key for question in first_batch],
            ["difficulty_block", "difficulty_weight"],
        )
        self.assertEqual(
            [question.question_key for question in second_batch],
            ["difficulty_weight", "difficulty_friction"],
        )


class FeedbackVariationTests(unittest.TestCase):
    def test_avoids_repeating_immediate_previous_feedback(self) -> None:
        feedback_text = build_feedback_text(
            "fluida",
            reflection_answers=["Leitura leve, mas sem muita novidade."],
            recent_feedback_texts=["A leitura parece ter fluído com naturalidade."],
            cycle_index=0,
        )

        self.assertEqual(feedback_text, "Hoje a leitura parece ter encontrado um ritmo sereno.")

    def test_keyword_variation_uses_history_and_rotates(self) -> None:
        feedback_text = build_feedback_text(
            "empolgante",
            reflection_answers=["Fiquei com muita curiosidade e vontade de continuar."],
            recent_feedback_texts=[
                "Você parece ter encontrado algo que puxou sua curiosidade.",
                "Há um ponto dessa leitura que claramente te chamou para continuar.",
            ],
            cycle_index=2,
        )

        self.assertEqual(feedback_text, "Parece que a leitura deixou uma vontade viva de seguir em frente.")


if __name__ == "__main__":
    unittest.main()
