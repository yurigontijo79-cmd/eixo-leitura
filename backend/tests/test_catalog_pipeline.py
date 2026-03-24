import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import normalize_text, score_pt_br_confidence


class CatalogPipelineRulesTests(unittest.TestCase):
    def test_normalize_text_removes_accents_and_noise(self):
        result = normalize_text("  Edição: Àrvore   do   Saber! ")
        self.assertEqual(result, "edicao arvore do saber")

    def test_ptbr_confidence_scores_language_and_region(self):
        score, reason = score_pt_br_confidence(
            language_code="pt",
            language_region="BR",
            publisher="Editora Record",
            title="Leitura guiada",
            description="Uma leitura para quem quer seguir com calma",
            source_name="google_books",
            source_url="https://example.com",
        )
        self.assertGreaterEqual(score, 60)
        self.assertIn("language_code=pt", reason)
        self.assertIn("language_region=BR", reason)

    def test_ptbr_confidence_remains_low_without_signals(self):
        score, reason = score_pt_br_confidence(
            language_code="en",
            language_region=None,
            publisher="Unknown Publisher",
            title="Random title",
            description="short text",
            source_name="open_library",
            source_url="https://example.org",
        )
        self.assertLess(score, 40)
        self.assertTrue(reason)


if __name__ == "__main__":
    unittest.main()
