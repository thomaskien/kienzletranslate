"""Cross-check every published ASR score against JiWER 4.0.0, without inference."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import math
import unicodedata
from pathlib import Path

import jiwer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='per-sample.csv')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    totals = {name: {'errors': 0, 'reference_units': 0}
              for name in ('wer', 'cer', 'strict_wer')}
    with args.input.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError('No samples to validate')
    for row in rows:
        ref, hyp = row['normalized_reference'], row['normalized_hypothesis']
        strict_ref = ' '.join(unicodedata.normalize('NFC', row['reference']).split())
        strict_hyp = ' '.join(unicodedata.normalize('NFC', row['hypothesis']).split())
        checks = {
            'wer': (jiwer.process_words(ref, hyp), len(ref.split())),
            'cer': (jiwer.process_characters(''.join(ref.split()), ''.join(hyp.split())),
                    len(''.join(ref.split()))),
            'strict_wer': (jiwer.process_words(strict_ref, strict_hyp), len(strict_ref.split())),
        }
        for name, (score, units) in checks.items():
            errors = score.substitutions + score.deletions + score.insertions
            if not math.isclose(errors / units, float(row[name]), abs_tol=1e-12):
                raise ValueError(f'{row["sample_id"]}: {name} disagrees with JiWER')
            totals[name]['errors'] += errors
            totals[name]['reference_units'] += units
    result = {
        'validator': 'JiWER', 'version': importlib.metadata.version('jiwer'),
        'input_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'samples': len(rows), 'comparisons': len(rows) * 3, 'mismatches': 0,
        'scope': 'Independent edit-distance calculation on the same normalized text; '
                 'does not validate normalization policy or reference correctness.',
        'totals': totals,
    }
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
