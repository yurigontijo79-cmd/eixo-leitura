import sys
import types
import unittest
from dataclasses import dataclass
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

reading_session_module = types.ModuleType("app.schemas.reading_session")
reading_session_module.FeelingValue = str


@dataclass
class CurrentReadingTrajectorySnapshot:
    current_book: dict | None
    session_count: int
    recent_feelings: list[str]
    dominant_feeling: str | None
    trajectory_label: str | None
    trajectory_text: str | None


reading_trajectory_module = types.ModuleType("app.schemas.reading_trajectory")
reading_trajectory_module.CurrentReadingTrajectorySnapshot = CurrentReadingTrajectorySnapshot
reading_trajectory_module.TrajectoryLabel = str

sys.modules.setdefault("app.schemas.reading_session", reading_session_module)
sys.modules.setdefault("app.schemas.reading_trajectory", reading_trajectory_module)

from app.services.trajectory_rules import build_reading_trajectory


class TrajectoryRuleTests(unittest.TestCase):
    def test_returns_empty_snapshot_without_current_book(self) -> None:
        snapshot = build_reading_trajectory(current_book=None, recent_feelings=[], session_count=0)

        self.assertIsNone(snapshot.current_book)
        self.assertEqual(snapshot.session_count, 0)
        self.assertIsNone(snapshot.trajectory_label)
        self.assertIsNone(snapshot.trajectory_text)

    def test_identifies_continuity_trajectory(self) -> None:
        snapshot = build_reading_trajectory(
            current_book={"id": 1, "title": "Livro", "author": "Autora", "description": "...", "state": "current"},
            recent_feelings=["empolgante", "fluida", "fluida", "densa"],
            session_count=4,
        )

        self.assertEqual(snapshot.dominant_feeling, "fluida")
        self.assertEqual(snapshot.trajectory_label, "continuity")
        self.assertEqual(snapshot.trajectory_text, "Há sinais de continuidade viva nesse percurso.")

    def test_identifies_resistance_trajectory(self) -> None:
        snapshot = build_reading_trajectory(
            current_book={"id": 1, "title": "Livro", "author": "Autora", "description": "...", "state": "current"},
            recent_feelings=["travada", "confusa", "travada", "densa"],
            session_count=5,
        )

        self.assertEqual(snapshot.dominant_feeling, "travada")
        self.assertEqual(snapshot.trajectory_label, "resistance")
        self.assertEqual(snapshot.trajectory_text, "Essa leitura parece pedir mais desaceleração e retomada.")

    def test_identifies_assimilation_after_dense_period(self) -> None:
        snapshot = build_reading_trajectory(
            current_book={"id": 1, "title": "Livro", "author": "Autora", "description": "...", "state": "current"},
            recent_feelings=["fluida", "densa", "densa", "confusa"],
            session_count=4,
        )

        self.assertEqual(snapshot.trajectory_label, "assimilation")
        self.assertEqual(snapshot.trajectory_text, "O caminho parece denso, mas algo começou a se abrir com mais corpo.")

    def test_identifies_oscillating_trajectory_without_dominant_pattern(self) -> None:
        snapshot = build_reading_trajectory(
            current_book={"id": 1, "title": "Livro", "author": "Autora", "description": "...", "state": "current"},
            recent_feelings=["fluida", "travada", "densa", "empolgante"],
            session_count=4,
        )

        self.assertIsNone(snapshot.dominant_feeling)
        self.assertEqual(snapshot.trajectory_label, "oscillating")
        self.assertEqual(snapshot.trajectory_text, "O caminho ainda está um pouco oscilante, mas algo começa a se firmar.")


if __name__ == "__main__":
    unittest.main()
