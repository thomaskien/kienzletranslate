import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "evaluate_asr.py"
SPEC = importlib.util.spec_from_file_location("evaluate_asr", MODULE_PATH)
evaluation = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(evaluation)


def sample(sample_id, reference, hypothesis, language="en", status="complete",
           audio_seconds=2.0, asr_seconds=0.5):
    return {
        "event": "sample",
        "sample_id": sample_id,
        "language": language,
        "source_lang": {"en": "eng", "tr": "tur", "fa": "pes"}.get(
            language, language),
        "status": status,
        "reference": reference,
        "reference_normalized": reference.lower(),
        "hypothesis": hypothesis,
        "translated_text": "unused",
        "target_lang": "deu",
        "audio_seconds": audio_seconds,
        "metrics": {
            "asr_seconds": asr_seconds,
            "translation_seconds": 0.2,
            "peak_vram_mib": 1234.0,
        },
        "request_seconds": 0.8,
        "error": "runner failed" if status == "error" else None,
    }


class EditDistanceTest(unittest.TestCase):
    def test_substitution_insertion_deletion_and_exact_counts(self):
        substitution = evaluation.edit_distance(["one"], ["two"], True)
        self.assertEqual(
            (substitution["substitutions"], substitution["deletions"],
             substitution["insertions"], substitution["hits"]),
            (1, 0, 0, 0))
        self.assertEqual(substitution["operations"][0]["operation"], "substitution")

        insertion = evaluation.edit_distance(["one"], ["one", "two"])
        self.assertEqual(
            (insertion["substitutions"], insertion["deletions"],
             insertion["insertions"], insertion["hits"]),
            (0, 0, 1, 1))

        deletion = evaluation.edit_distance(["one", "two"], ["one"])
        self.assertEqual(
            (deletion["substitutions"], deletion["deletions"],
             deletion["insertions"], deletion["hits"]),
            (0, 1, 0, 1))

        exact = evaluation.edit_distance(["one", "two"], ["one", "two"])
        self.assertEqual(exact["errors"], 0)
        self.assertEqual(exact["hits"], 2)


class NormalizationTest(unittest.TestCase):
    def test_strict_retains_case_and_punctuation_while_primary_does_not(self):
        reference = "Hello, WORLD!"
        hypothesis = "hello world"
        self.assertEqual(evaluation.normalize_text(reference, "en"), hypothesis)
        self.assertEqual(evaluation.strict_normalize(reference), reference)
        primary = evaluation._score(
            evaluation.normalize_text(reference, "en").split(), hypothesis.split())
        strict = evaluation._score(
            evaluation.strict_normalize(reference).split(),
            evaluation.strict_normalize(hypothesis).split())
        self.assertEqual(primary["rate"], 0)
        self.assertEqual(strict["rate"], 1)

    def test_turkish_dotted_and_dotless_i(self):
        self.assertEqual(evaluation.normalize_text("I İ", "tr"), "ı i")
        self.assertNotEqual(evaluation.normalize_text("I İ", "en"), "ı i")

    def test_arabic_persian_apostrophe_zwnj_and_controls(self):
        source = "می\u200cروم، كِتاب\u200d 'X' ★ دنیا"
        normalized = evaluation.normalize_text(source, "fa")
        self.assertEqual(normalized, "می روم كِتاب x دنیا")
        self.assertIn("ِ", normalized)
        self.assertNotIn("\u200d", normalized)
        self.assertEqual(evaluation.normalize_text("d’Artagnan", "fr"), "dartagnan")


class EvaluationTest(unittest.TestCase):
    def write_jsonl(self, directory, records):
        path = Path(directory) / "runner.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return path

    def test_corpus_weighting_differs_from_naive_sample_average(self):
        records = [
            sample("long", "one two three four", "one two three X"),
            sample("short", "one", "X"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            samples, metadata = evaluation.load_jsonl(
                self.write_jsonl(temporary, records))
        summary = evaluation.build_summary(samples, metadata, "Fixture")
        sample_average = sum(item["word"]["rate"] for item in samples) / 2
        self.assertAlmostEqual(summary["aggregate"]["wer"], 2 / 5)
        self.assertAlmostEqual(sample_average, (0.25 + 1) / 2)
        self.assertNotEqual(summary["aggregate"]["wer"], sample_average)

    def test_error_sample_is_empty_hypothesis_and_all_deletions(self):
        record = sample("failed", "one two three", "must be ignored", status="error")
        with tempfile.TemporaryDirectory() as temporary:
            samples, _ = evaluation.load_jsonl(
                self.write_jsonl(temporary, [record]))
        scored = samples[0]
        self.assertEqual(scored["hypothesis"], "")
        self.assertEqual(scored["word"]["deletions"], 3)
        self.assertEqual(scored["word"]["substitutions"], 0)
        self.assertEqual(scored["word"]["insertions"], 0)
        self.assertEqual(scored["word"]["rate"], 1)

    def test_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_jsonl(temporary, [
                sample("same", "one", "one"),
                sample("same", "two", "two"),
            ])
            with self.assertRaisesRegex(ValueError, "duplicate sample_id"):
                evaluation.load_jsonl(path)

    def test_outputs_include_failures_metadata_and_all_languages(self):
        metadata = {
            "event": "metadata", "model": "local fixture", "max_tokens": 32,
            "api_token": "do not copy",
        }
        records = [
            metadata,
            sample("english", "Hello, world", "hello world", language="en"),
            sample("persian", "سلام دنیا", "ignored", language="fa", status="error"),
        ]
        with tempfile.TemporaryDirectory() as temporary:
            input_path = self.write_jsonl(temporary, records)
            output_path = Path(temporary) / "results"
            summary = evaluation.evaluate(input_path, output_path, "Fixture report")
            self.assertEqual(summary["failed_sample_ids"], ["persian"])
            self.assertEqual(set(summary["per_language"]), {"en", "fa"})
            self.assertNotIn("api_token", summary["metadata"])
            self.assertEqual(summary["metadata"]["model"], "local fixture")
            self.assertEqual(summary["metadata"]["max_tokens"], 32)
            self.assertEqual(
                {path.name for path in output_path.iterdir()},
                {"report.md", "summary.json", "per-language.csv", "per-sample.csv"})
            report = (output_path / "report.md").read_text(encoding="utf-8")
            self.assertIn("ASR with known source languages", report)
            self.assertIn("not a language-identification", report)
            with (output_path / "per-sample.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(rows[0]["reference_normalized_input"], "hello, world")
            self.assertTrue(json.loads(rows[0]["word_operations"]))

    def test_nan_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "runner.jsonl"
            path.write_text(
                '{"event":"sample","sample_id":"x","language":"en",'
                '"status":"complete","reference":"one","hypothesis":"one",'
                '"audio_seconds":NaN}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid JSON"):
                evaluation.load_jsonl(path)


if __name__ == "__main__":
    unittest.main()
