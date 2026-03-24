import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

reading_session_module = types.ModuleType("app.schemas.reading_session")
reading_session_module.FeelingValue = str

reading_trajectory_module = types.ModuleType("app.schemas.reading_trajectory")

@dataclass
class CurrentReadingTrajectorySnapshot:
    current_book: dict | None = None
    session_count: int = 0
    recent_feelings: list[str] | None = None
    dominant_feeling: str | None = None
    trajectory_label: str | None = None
    trajectory_text: str | None = None


reading_trajectory_module.CurrentReadingTrajectorySnapshot = CurrentReadingTrajectorySnapshot
reading_trajectory_module.TrajectoryLabel = str

sys.modules.setdefault("app.schemas.reading_session", reading_session_module)
sys.modules.setdefault("app.schemas.reading_trajectory", reading_trajectory_module)

from app.services.closing_rules import build_closing_text


class ClosingRuleTests(unittest.TestCase):
    def test_short_read_gets_forming_closure(self) -> None:
        self.assertEqual(
            build_closing_text(2, "forming", None, None),
            "Foi uma travessia breve, ainda em formação, mas já com sinais de abertura.",
        )

    def test_continuity_closure_uses_steady_finish(self) -> None:
        self.assertEqual(
            build_closing_text(5, "continuity", "fluida", None),
            "Essa leitura encontrou um ritmo próprio e chegou ao fim com continuidade viva.",
        )

    def test_resistance_closure_preserves_dignity(self) -> None:
        self.assertEqual(
            build_closing_text(6, "resistance", "travada", None),
            "Foi um percurso mais exigente, mas algo se consolidou ao longo do caminho.",
        )

    def test_opening_feedback_can_shape_generic_closure(self) -> None:
        self.assertEqual(
            build_closing_text(4, "open", "confusa", "Há um ponto dessa leitura que parece ter se aberto melhor agora."),
            "O percurso chegou ao fim com um sinal discreto de abertura.",
        )


if __name__ == "__main__":
    unittest.main()
