import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    'translation_eval', Path(__file__).parents[1] / 'scripts/evaluate_translation.py')
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


class TranslationEvaluationTest(unittest.TestCase):
    def read(self, records):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'input.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in records))
            return evaluation.read_records(path)

    def row(self, **changes):
        return dict({'event': 'sample', 'sample_id': 'one', 'language': 'de',
                     'target_lang': 'eng', 'status': 'complete',
                     'translation_reference': 'The train arrives at five today.',
                     'translated_text': 'The train arrives at five today.',
                     'reference': 'irrelevant source language text'}, **changes)

    def test_uses_translation_reference_and_preserves_perfect_match(self):
        scores = evaluation.score_group(self.read([self.row()]))['metrics']
        self.assertAlmostEqual(scores['bleu']['score'], 100)
        self.assertAlmostEqual(scores['chrfpp']['score'], 100)
        self.assertAlmostEqual(scores['ter']['score'], 0)

    def test_failure_counts_as_empty_translation(self):
        group = evaluation.score_group(self.read([self.row(status='error')]))
        self.assertEqual(group['completed'], 0)
        self.assertEqual(group['empty_outputs'], 1)
        self.assertEqual(group['metrics']['chrfpp']['score'], 0)
        self.assertEqual(group['metrics']['ter']['score'], 100)

    def test_missing_reference_and_duplicates_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing translation_reference'):
            self.read([self.row(translation_reference='')])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.read([self.row(), self.row()])

    def test_normalization_does_not_hide_semantic_or_numeric_changes(self):
        self.assertEqual(evaluation.normalize(' Cafe\u0301\n  17! '), 'Café 17!')
        self.assertNotEqual(evaluation.normalize('17'), evaluation.normalize('seventeen'))
        self.assertNotEqual(evaluation.normalize('not safe'), evaluation.normalize('safe'))


if __name__ == '__main__':
    unittest.main()
