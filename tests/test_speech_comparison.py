import csv
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "compare_speech_benchmarks", ROOT / "scripts" / "compare_speech_benchmarks.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def asr_row(sample_id="a.wav", language="de", words=2, errors=1,
            status="complete", reference="hello world", normalized="hello world",
            hypothesis="hello", cer=0.2):
    return {
        "sample_id": sample_id, "language": language, "source_lang": language,
        "status": status, "audio_seconds": "2.5", "reference_words": str(words),
        "word_substitutions": str(errors), "word_deletions": "0",
        "word_insertions": "0", "word_hits": str(words - errors),
        "wer": str(errors / words), "cer": str(cer), "strict_wer": str(errors / words),
        "exact_normalized_match": str(errors == 0), "asr_seconds": "0.5",
        "request_seconds": "1.0", "peak_allocated_mib": "10", "reference": reference,
        "reference_normalized_input": normalized, "hypothesis": hypothesis,
        "normalized_reference": normalized, "normalized_hypothesis": hypothesis,
        "word_operations": "[]", "error": "" if status == "complete" else "failed",
    }


def asr_group(rows, cer=0.1):
    substitutions = sum(int(row["word_substitutions"]) for row in rows)
    deletions = sum(int(row["word_deletions"]) for row in rows)
    insertions = sum(int(row["word_insertions"]) for row in rows)
    hits = sum(int(row["word_hits"]) for row in rows)
    reference_words = sum(int(row["reference_words"]) for row in rows)
    errors = substitutions + deletions + insertions
    return {
        "n": len(rows),
        "completed": sum(row["status"] == "complete" for row in rows),
        "failures": sum(row["status"] == "error" for row in rows),
        "reference_words": reference_words,
        "word": {
            "substitutions": substitutions, "deletions": deletions,
            "insertions": insertions, "hits": hits, "errors": errors,
            "reference_units": reference_words,
        },
        "wer": errors / reference_words, "cer": cer,
        "asr_latency_seconds_median": 0.5,
    }


def write_asr(directory, rows, *, aggregate_cer=0.1):
    write_csv(directory / "per-sample.csv", rows)
    languages = sorted({row["language"] for row in rows})
    summary = {
        "aggregate": asr_group(rows, aggregate_cer),
        "per_language": {
            language: asr_group(
                [row for row in rows if row["language"] == language], aggregate_cer)
            for language in languages
        },
    }
    (directory / "summary.json").write_text(
        json.dumps(summary) + "\n", encoding="utf-8")
    return summary


def translation_row(sample_id="t.wav", source="de", target="eng", score=40.0,
                    reference="Good morning", scoring_reference="Good morning",
                    hypothesis="Morning", status="complete"):
    return {
        "sample_id": sample_id, "source_language": source, "target_language": target,
        "status": status, "sentence_chrfpp": str(score), "source_reference": "Guten Morgen",
        "source_asr": "Guten Morgen", "translation_reference": reference,
        "translation_hypothesis": hypothesis, "scoring_reference": scoring_reference,
        "scoring_hypothesis": hypothesis if status == "complete" else "",
    }


def translation_group(rows, offset=0.0):
    return {
        "samples": len(rows),
        "completed": sum(row["status"] == "complete" for row in rows),
        "empty_outputs": sum(not row["scoring_hypothesis"] for row in rows),
        "metrics": {
            "bleu": {"score": 20.0 + offset, "signature": "test"},
            "chrfpp": {"score": 40.0 + offset, "signature": "test"},
            "ter": {"score": 60.0 - offset, "signature": "test"},
        },
        "translation_seconds_median": 0.7,
    }


def write_translation(directory, rows, *, offset=0.0):
    write_csv(directory / "per-sample.csv", rows)
    english = [row for row in rows if row["target_language"] == "eng"]
    pairs = sorted({f"{row['source_language']}->eng" for row in english})
    summary = {
        "samples": len(rows),
        "by_target": {"eng": translation_group(english, offset)},
        "by_pair": {
            pair: translation_group(
                [row for row in english
                 if f"{row['source_language']}->eng" == pair], offset)
            for pair in pairs
        },
    }
    (directory / "summary.json").write_text(
        json.dumps(summary) + "\n", encoding="utf-8")
    return summary


class SpeechComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.baseline_asr = self.root / "baseline-asr"
        self.candidate_asr = self.root / "candidate-asr"
        self.baseline_translation = self.root / "baseline-translation"
        self.candidate_translation = self.root / "candidate-translation"
        self.output = self.root / "output"

    def tearDown(self):
        self.temporary.cleanup()

    def write_base(self):
        write_asr(self.baseline_asr, [asr_row(errors=1, hypothesis="hello")])
        write_asr(self.candidate_asr, [asr_row(errors=0, hypothesis="hello world", cer=0.0)])
        write_translation(self.baseline_translation, [
            translation_row(score=40.0),
            translation_row("english.wav", source="en", target="deu", score=55.0,
                            reference="Guten Morgen", scoring_reference="Guten Morgen"),
        ])
        write_translation(
            self.candidate_translation, [translation_row(score=50.0, hypothesis="Good morning")],
            offset=5.0)

    def compare(self):
        return MODULE.compare(
            self.baseline_asr, self.candidate_asr, self.baseline_translation,
            self.candidate_translation, self.output)

    def test_matching_improvements_have_expected_signs_and_exclude_german_target(self):
        self.write_base()
        result = self.compare()
        self.assertEqual(result["asr"]["outcomes"], {"better": 1, "tie": 0, "worse": 0})
        self.assertEqual(result["translation"]["paired_samples"], 1)
        with (self.output / "asr-paired.csv").open(encoding="utf-8", newline="") as handle:
            asr = next(csv.DictReader(handle))
        self.assertEqual(asr["delta_word_errors"], "-1")
        self.assertEqual(float(asr["delta_wer_pp"]), -50.0)
        with (self.output / "translation-paired.csv").open(
                encoding="utf-8", newline="") as handle:
            translation = list(csv.DictReader(handle))
        self.assertEqual(len(translation), 1)
        self.assertEqual(translation[0]["target_language"], "eng")
        self.assertEqual(float(translation[0]["delta_chrfpp"]), 10.0)
        self.assertEqual(translation[0]["candidate_outcome"], "better")
        hashes = result["metadata"]["sources"]
        self.assertTrue(all(
            len(file_info["sha256"]) == 64
            for source in hashes.values() for file_info in source["files"].values()))

    def test_duplicate_id_is_rejected(self):
        self.write_base()
        duplicate = asr_row(errors=1)
        write_asr(self.baseline_asr, [asr_row(errors=1), duplicate])
        with self.assertRaisesRegex(ValueError, "duplicate sample_id"):
            self.compare()

    def test_missing_candidate_id_is_rejected(self):
        self.write_base()
        rows = [asr_row(), asr_row("b.wav", reference="another text",
                                  normalized="another text")]
        write_asr(self.baseline_asr, rows)
        with self.assertRaisesRegex(ValueError, "sample ID sets differ"):
            self.compare()

    def test_changed_translation_reference_is_rejected(self):
        self.write_base()
        write_translation(self.candidate_translation, [
            translation_row(score=50.0, reference="Changed", scoring_reference="Changed")
        ], offset=5.0)
        with self.assertRaisesRegex(ValueError, "translation_reference mismatch"):
            self.compare()

    def test_weighted_asr_aggregate_is_not_naive_sample_average(self):
        self.write_base()
        baseline_rows = [
            asr_row("short.wav", "de", words=1, errors=1, reference="one", normalized="one"),
            asr_row("long.wav", "fr", words=9, errors=0, reference="one two three four five six seven eight nine",
                    normalized="one two three four five six seven eight nine", hypothesis="all good"),
        ]
        candidate_rows = [dict(row) for row in baseline_rows]
        write_asr(self.baseline_asr, baseline_rows)
        write_asr(self.candidate_asr, candidate_rows)
        result = self.compare()
        self.assertAlmostEqual(result["asr"]["baseline"]["wer"], 0.1)
        self.assertNotAlmostEqual(result["asr"]["baseline"]["wer"], 0.5)

    def test_mismatched_summary_is_rejected(self):
        self.write_base()
        path = self.candidate_asr / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        summary["aggregate"]["n"] = 2
        path.write_text(json.dumps(summary) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "n mismatch"):
            self.compare()


if __name__ == "__main__":
    unittest.main()
