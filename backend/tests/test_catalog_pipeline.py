import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.db import classify_catalog_decision, normalize_text, score_pt_br_confidence


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

    def test_decision_retains_ambiguous_records_instead_of_hard_discard(self):
        status, reason = classify_catalog_decision(
            parsed={
                "language_code": None,
                "title": "Título",
                "author": "Autor",
                "isbn10": None,
                "isbn13": None,
            },
            score=42,
            confidence_reasons="sem_sinal_forte",
            dedupe_match_type=None,
        )
        self.assertEqual(status, "retained")
        self.assertEqual(reason, "ambiguidade_sem_sinal_forte")

    def test_decision_discards_incompatible_language(self):
        status, reason = classify_catalog_decision(
            parsed={
                "language_code": "en",
                "title": "Book title",
                "author": "Author",
                "isbn10": None,
                "isbn13": None,
            },
            score=80,
            confidence_reasons="language_code=en",
            dedupe_match_type=None,
        )
        self.assertEqual(status, "discarded")
        self.assertEqual(reason, "idioma_incompativel")

    def test_open_library_promotes_with_strong_signals_without_isbn(self):
        status, reason = classify_catalog_decision(
            parsed={
                "source_name": "open_library",
                "language_code": "pt",
                "title": "Memórias Póstumas de Brás Cubas",
                "author": "Machado de Assis",
                "isbn10": None,
                "isbn13": None,
            },
            score=50,
            confidence_reasons="language_code=pt,texto_com_sinal_pt",
            dedupe_match_type=None,
        )
        self.assertEqual(status, "promoted")
        self.assertIn("open_library", reason)


if __name__ == "__main__":
    unittest.main()
