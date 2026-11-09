"""Score saved speech translations locally; no inference or server connection."""
import argparse
import csv
import hashlib
import json
import platform
import statistics
import time
import unicodedata
from collections import defaultdict
from pathlib import Path

import sacrebleu
from sacrebleu.metrics import BLEU, CHRF, TER


def normalize(text):
    return ' '.join(unicodedata.normalize('NFC', text).split())


def read_records(path):
    samples, seen = [], set()
    for line_number, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get('event') != 'sample':
            continue
        for field in ('sample_id', 'language', 'target_lang', 'translation_reference'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f'Line {line_number}: missing {field}; refusing silent exclusion')
        if row['sample_id'] in seen:
            raise ValueError('Duplicate sample_id: ' + row['sample_id'])
        if row.get('status') not in ('complete', 'error'):
            raise ValueError('Unsupported status: ' + row['sample_id'])
        if not isinstance(row.get('translated_text', ''), str):
            raise ValueError('Translation must be text: ' + row['sample_id'])
        seen.add(row['sample_id'])
        sample = dict(row)
        sample['scoring_reference'] = normalize(row['translation_reference'])
        sample['scoring_hypothesis'] = normalize(row.get('translated_text', '')) if row['status'] == 'complete' else ''
        samples.append(sample)
    if not samples:
        raise ValueError('No sample records')
    return samples


def metrics():
    return {
        'bleu': BLEU(lowercase=False, tokenize='13a', smooth_method='exp', effective_order=False),
        'chrfpp': CHRF(char_order=6, word_order=2, beta=2, lowercase=False,
                       whitespace=False, eps_smoothing=False),
        'ter': TER(normalized=False, no_punct=False, asian_support=False, case_sensitive=False),
    }


def score_group(rows):
    hypotheses = [r['scoring_hypothesis'] for r in rows]
    references = [[r['scoring_reference'] for r in rows]]
    scores = {}
    for name, metric in metrics().items():
        result = metric.corpus_score(hypotheses, references)
        scores[name] = {'score': result.score, 'signature': str(metric.get_signature())}
    durations = [r['metrics']['translation_seconds'] for r in rows
                 if isinstance(r.get('metrics', {}).get('translation_seconds'), (int, float))]
    return {
        'samples': len(rows), 'completed': sum(r['status'] == 'complete' for r in rows),
        'empty_outputs': sum(not r['scoring_hypothesis'] for r in rows),
        'metrics': scores,
        'translation_seconds_median': statistics.median(durations) if durations else None,
    }


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def evaluate(path, output, title='SeamlessM4T saved translation quality evaluation'):
    started = time.perf_counter()
    rows = read_records(path)
    pairs, targets = defaultdict(list), defaultdict(list)
    chrf = metrics()['chrfpp']
    sample_output = []
    for row in rows:
        pair = f'{row["language"]}->{row["target_lang"]}'
        pairs[pair].append(row)
        targets[row['target_lang']].append(row)
        sample_output.append({
            'sample_id': row['sample_id'], 'source_language': row['language'],
            'target_language': row['target_lang'], 'status': row['status'],
            'sentence_chrfpp': chrf.sentence_score(row['scoring_hypothesis'], [row['scoring_reference']]).score,
            'source_reference': row.get('reference', ''),
            'source_asr': row.get('hypothesis', ''),
            'translation_reference': row['translation_reference'],
            'translation_hypothesis': row.get('translated_text', ''),
            'scoring_reference': row['scoring_reference'],
            'scoring_hypothesis': row['scoring_hypothesis'],
        })
    summary = {
        'title': title,
        'samples': len(rows), 'failed_requests': sum(r['status'] != 'complete' for r in rows),
        'input_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'evaluator_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sacrebleu_version': sacrebleu.__version__, 'python_version': platform.python_version(),
        'normalization': 'Symmetric NFC and whitespace collapse. Preserve case, punctuation and numbers; metric-specific tokenization follows each signature.',
        'scope': 'Existing direct speech-to-text translation outputs; no new model inference. Single reference per sample. Metric scores are not semantic accuracy percentages.',
        'by_pair': {pair: score_group(items) for pair, items in sorted(pairs.items())},
        'by_target': {target: score_group(items) for target, items in sorted(targets.items())},
        'mixed_targets_descriptive_only': score_group(rows),
        'elapsed_scoring_seconds': time.perf_counter() - started,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv(output / 'per-sample.csv', sample_output)
    write_csv(output / 'per-pair.csv', [
        {'direction': pair, 'samples': item['samples'], 'completed': item['completed'],
         **{key: value['score'] for key, value in item['metrics'].items()},
         'translation_seconds_median': item['translation_seconds_median']}
        for pair, item in summary['by_pair'].items()
    ])
    # Plain files permit an independent command-line check of corpus grouping.
    for target, items in targets.items():
        for suffix, key in [('references', 'scoring_reference'), ('hypotheses', 'scoring_hypothesis')]:
            (output / f'{target}.{suffix}.txt').write_text(
                '\n'.join(r[key] for r in items) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output-dir', required=True, type=Path)
    parser.add_argument('--title', default='SeamlessM4T saved translation quality evaluation')
    args = parser.parse_args()
    summary = evaluate(args.input, args.output_dir, args.title)
    print(json.dumps({'samples': summary['samples'], 'by_target': summary['by_target']}, indent=2))


if __name__ == '__main__':
    main()
