import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "benchmark_lid_cpu.py"
SPEC = importlib.util.spec_from_file_location("benchmark_lid_cpu", MODULE_PATH)
benchmark = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(benchmark)


def call(duration, prediction, score, margin, truth="de", detect_ms=10):
    return {
        "event": "detection",
        "status": "ok",
        "sample_id": "sample",
        "language": truth,
        "checkpoint_seconds": float(duration),
        "prediction": prediction,
        "score": score,
        "margin": margin,
        "correct": prediction == truth,
        "detect_ms": detect_ms,
        "control": False,
    }


class PolicyDecisionTest(unittest.TestCase):
    durations = [1.0, 2.0, 3.0, 5.0, 8.0]

    def decide(self, rows):
        return benchmark.policy_decision(
            {row["checkpoint_seconds"]: row for row in rows}, self.durations)

    def test_high_confidence_wrong_language_is_accepted(self):
        decision = self.decide([
            call(1, "fr", 0.95, 0.7),
            call(2, "fr", 0.93, 0.6),
        ])
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["prediction"], "fr")
        self.assertEqual(decision["accepted_duration"], 2.0)

    def test_intermittent_low_confidence_prevents_early_acceptance(self):
        decision = self.decide([
            call(1, "de", 0.9, 0.5),
            call(2, "de", 0.79, 0.5),
            call(3, "de", 0.91, 0.5),
            call(5, "de", 0.92, 0.5),
        ])
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["accepted_duration"], 5.0)

    def test_later_stable_pair_is_accepted(self):
        decision = self.decide([
            call(1, "fr", 0.9, 0.4),
            call(2, "de", 0.9, 0.4),
            call(3, "it", 0.9, 0.4),
            call(5, "de", 0.91, 0.4),
            call(8, "de", 0.92, 0.4),
        ])
        self.assertTrue(decision["accepted"])
        self.assertEqual(decision["accepted_duration"], 8.0)

    def test_fully_uncertain_abstains(self):
        rows = [call(duration, "de", 0.7, 0.1) for duration in self.durations]
        self.assertFalse(self.decide(rows)["accepted"])

    def test_no_future_prediction_lookahead(self):
        early = [call(1, "fr", 0.95, 0.5), call(2, "fr", 0.95, 0.5)]
        with_future = early + [call(3, "de", 0.99, 0.8), call(5, "de", 0.99, 0.8)]
        self.assertEqual(self.decide(early), self.decide(with_future))

    def test_truth_label_does_not_affect_decision(self):
        german_truth = [call(1, "fr", 0.95, 0.5, truth="de"),
                        call(2, "fr", 0.95, 0.5, truth="de")]
        french_truth = [call(1, "fr", 0.95, 0.5, truth="fr"),
                        call(2, "fr", 0.95, 0.5, truth="fr")]
        self.assertEqual(self.decide(german_truth), self.decide(french_truth))


class AggregateTest(unittest.TestCase):
    def test_deterministic_fixture_counts_wrong_accept_and_abstention(self):
        rows = []
        for sample_id, truth, predictions, confident in (
            ("a", "de", ["de", "de"], True),
            ("b", "de", ["fr", "fr"], True),
            ("c", "fr", ["fr", "fr"], False),
        ):
            for duration, prediction in zip((1, 2), predictions):
                row = call(duration, prediction, 0.9 if confident else 0.7,
                           0.5 if confident else 0.1, truth=truth, detect_ms=duration * 10)
                row["sample_id"] = sample_id
                rows.append(row)
        summary = benchmark.summarize_records(rows, [1.0, 2.0])
        policy = summary["policy"]
        self.assertEqual(policy["total"], 3)
        self.assertEqual(policy["accepted"], 2)
        self.assertEqual(policy["correct_accepted"], 1)
        self.assertEqual(policy["wrong_accepted"], 1)
        self.assertEqual(policy["abstained"], 1)
        self.assertAlmostEqual(policy["coverage"], 2 / 3)
        self.assertEqual(policy["accuracy_among_accepted"], 0.5)
        self.assertEqual(policy["wrong_accepted_examples"][0]["sample_id"], "b")


class DetectorAdapterTest(unittest.TestCase):
    def test_list_probabilities_are_ranked_and_detector_options_are_fixed(self):
        class FakeModel:
            def detect_language(self, **kwargs):
                self.kwargs = kwargs
                return "de", 0.9, [("fr", 0.1), ("de", 0.9), ("it", 0.2)]

        model = FakeModel()
        prediction, score, runner, margin, top5, _, _ = benchmark._detect(model, [0.0])
        self.assertEqual((prediction, score), ("de", 0.9))
        self.assertEqual(runner, {"language": "it", "score": 0.2})
        self.assertAlmostEqual(margin, 0.7)
        self.assertEqual([item["language"] for item in top5], ["de", "it", "fr"])
        self.assertFalse(model.kwargs["vad_filter"])
        self.assertEqual(model.kwargs["language_detection_segments"], 1)


if __name__ == "__main__":
    unittest.main()
