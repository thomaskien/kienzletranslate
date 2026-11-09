"""Download a compact, reproducible selection of original FLEURS test recordings.

Only public benchmark audio is saved, never application conversation data.
The compressed archives are streamed; only selected WAV files are retained.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

REVISION = '70bb2e84b976b7e960aa89f1c648e09c59f894dd'
BASE = f'https://huggingface.co/datasets/google/fleurs/resolve/{REVISION}'
LANGUAGES = {
    'de_de': 'de', 'en_us': 'en', 'fr_fr': 'fr', 'es_419': 'es',
    'it_it': 'it', 'pl_pl': 'pl', 'ro_ro': 'ro', 'tr_tr': 'tr',
    'ar_eg': 'ar', 'ru_ru': 'ru', 'uk_ua': 'uk', 'fa_ir': 'fa',
}


def open_url(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={
        'User-Agent': 'kienzletranslate-offline-benchmark/1.0'}), timeout=120)


def download_language(root, config, count, minimum_seconds):
    folder = root / 'audio' / config
    folder.mkdir(parents=True, exist_ok=True)
    manifest = root / f'{config}.jsonl'
    if manifest.exists():
        existing = [json.loads(line) for line in manifest.read_text().splitlines()]
        if len(existing) == count and all(
            (root / row['audio_path']).exists() and
            hashlib.sha256((root / row['audio_path']).read_bytes()).hexdigest() == row['sha256']
            for row in existing
        ):
            print(f'{config}: reuse {count} recordings', flush=True)
            return existing
    with open_url(f'{BASE}/data/{config}/test.tsv') as response:
        metadata_bytes = response.read()
    (root / f'{config}-test.tsv').write_bytes(metadata_bytes)
    metadata = {}
    for row in csv.reader(io.StringIO(metadata_bytes.decode('utf-8')), delimiter='\t', quoting=csv.QUOTE_NONE):
        if len(row) != 7:
            raise ValueError(f'Unexpected TSV format: {config}')
        metadata[row[1]] = row
    selected, sentence_ids = [], set()
    archive_url = f'{BASE}/data/{config}/audio/test.tar.gz'
    with open_url(archive_url) as response, tarfile.open(fileobj=response, mode='r|gz') as archive:
        for member in archive:
            name = Path(member.name).name
            if not member.isfile() or name not in metadata:
                continue
            row = metadata[name]
            if int(row[5]) < minimum_seconds * 16000 or row[0] in sentence_ids:
                continue
            if not 0 < member.size < 32 * 1024 * 1024:
                raise ValueError('Unexpected audio file size')
            stream = archive.extractfile(member)
            if stream is None:
                continue
            audio = stream.read()
            output = folder / name
            output.write_bytes(audio)
            selected.append({
                'sample_id': f'{config}/{name}', 'language': LANGUAGES[config],
                'dataset_config': config, 'sentence_id': int(row[0]),
                'audio_path': output.relative_to(root).as_posix(),
                'duration_seconds': int(row[5]) / 16000,
                'raw_transcription': row[2], 'transcription': row[3], 'gender': row[6],
                'sha256': hashlib.sha256(audio).hexdigest(),
                'dataset': 'google/fleurs', 'revision': REVISION, 'split': 'test',
                'source_member': member.name,
            })
            sentence_ids.add(row[0])
            if len(selected) == count:
                break
    if len(selected) != count:
        raise ValueError(f'{config}: only {len(selected)} eligible recordings')
    manifest.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in selected))
    print(f'{config}: downloaded {len(selected)} recordings', flush=True)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--per-language', type=int, default=20)
    parser.add_argument('--minimum-seconds', type=float, default=8)
    parser.add_argument('--languages', nargs='+', choices=list(LANGUAGES), default=list(LANGUAGES))
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--mark-speech', action='store_true', help='Also prepare CPU VAD onset metadata; requires faster-whisper and soundfile')
    args = parser.parse_args()
    if args.per_language < 1 or args.minimum_seconds < 0 or not 1 <= args.workers <= 8:
        parser.error('Invalid sample count, minimum duration or worker count')
    args.output.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        groups = list(executor.map(lambda config: download_language(
            args.output, config, args.per_language, args.minimum_seconds), args.languages))
    rows = [row for group in groups for row in group]
    references = {}
    for config in args.languages:
        with (args.output / f'{config}-test.tsv').open() as metadata:
            for fields in csv.reader(metadata, delimiter='\t', quoting=csv.QUOTE_NONE):
                references.setdefault(int(fields[0]), {})[LANGUAGES[config]] = fields[2]
    for row in rows:
        row['reference_translations'] = references.get(row['sentence_id'], {})
    if args.mark_speech:
        import time
        import soundfile as sf
        from faster_whisper.vad import get_speech_timestamps, VadOptions
        for row in rows:
            audio, rate = sf.read(args.output / row['audio_path'], dtype='float32')
            if rate != 16000 or audio.ndim != 1:
                raise ValueError('Expected original mono 16 kHz audio')
            start = time.perf_counter()
            segments = get_speech_timestamps(audio, VadOptions(
                min_speech_duration_ms=250, min_silence_duration_ms=300, speech_pad_ms=0))
            row['vad_ms'] = (time.perf_counter()-start)*1000
            row['speech_segments'] = segments
            row['start_sample'] = segments[0]['start'] if segments else len(audio)
            row['speech_seconds'] = sum(s['end']-s['start'] for s in segments)/rate
            row['available_after_onset_seconds'] = (len(audio)-row['start_sample'])/rate
        eligible = [row for row in rows if row['available_after_onset_seconds'] >= args.minimum_seconds]
        (args.output / 'manifest-speech.jsonl').write_text(''.join(
            json.dumps(row, ensure_ascii=False) + '\n' for row in eligible))
        print(f'Speech-onset manifest: {len(eligible)} eligible recordings', flush=True)
    (args.output / 'manifest.jsonl').write_text(''.join(
        json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    source = {
        'dataset': 'google/fleurs', 'revision': REVISION,
        'url': 'https://huggingface.co/datasets/google/fleurs',
        'paper': 'https://arxiv.org/abs/2205.12446',
        'attribution': 'FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech, Conneau et al., Google, 2022.',
        'license': 'CC-BY-4.0', 'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'split': 'test', 'recordings': len(rows), 'languages': args.languages,
        'selection': f'First {args.per_language} eligible archive members per language; distinct sentence IDs; duration >= {args.minimum_seconds}s. Not a random or representative population sample.',
        'audio_changes': 'None: original WAV bytes retained; SHA-256 recorded.',
        'benchmark_subset': 'First 10 eligible rows per language from manifest-speech.jsonl (>=8 s remaining after VAD onset); other recordings unused in the initial benchmark.',
        'vad': 'faster-whisper bundled Silero VAD on CPU, min_speech_duration_ms=250, min_silence_duration_ms=300, speech_pad_ms=0. Offline onset annotation; no internal pauses removed. Detection timings exclude this separately recorded preprocessing cost.' if args.mark_speech else None,
        'parallel_reference_note': 'reference_translations joins original FLEURS test transcriptions across languages by sentence ID. Selected audio need not contain every sentence in every language; reference text availability is explicit per entry.',
    }
    (args.output / 'SOURCE.json').write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
    print(f'Library ready: {len(rows)} originals, {sum((args.output/r["audio_path"]).stat().st_size for r in rows)/1024**2:.1f} MiB', flush=True)


if __name__ == '__main__':
    main()
