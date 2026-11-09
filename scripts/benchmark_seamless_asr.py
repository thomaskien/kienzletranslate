"""Run the complete public FLEURS library through the installed Seamless service.

Uses the existing resident GPU model and an isolated benchmark session. Source
languages are supplied from dataset labels. Scores must use original_text only.
The normal app pipeline also generates a text translation; TTS is disabled.
"""
import argparse
import hashlib
import io
import json
import platform
import secrets
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

LANGUAGES = {'de': 'deu', 'en': 'eng', 'fr': 'fra', 'es': 'spa', 'it': 'ita',
             'pl': 'pol', 'ro': 'ron', 'tr': 'tur', 'ar': 'arb', 'ru': 'rus',
             'uk': 'ukr', 'fa': 'pes'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path('/etc/kienzletranslate/config.json'))
    parser.add_argument('--timeout', type=float, default=180)
    args = parser.parse_args()
    if args.timeout <= 0 or args.output.exists():
        parser.error('Positive timeout and a new output path are required')
    import numpy as np
    import soundfile as sf
    config = json.loads(args.config.read_text())
    rows = [json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()]
    if not rows or len({r['sample_id'] for r in rows}) != len(rows):
        raise ValueError('Manifest must contain unique sample IDs')
    for row in rows:
        if row['language'] not in LANGUAGES or not row['raw_transcription'].strip():
            raise ValueError('Unsupported language or missing reference')
        path = args.manifest.parent / row['audio_path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Audio checksum mismatch: ' + row['sample_id'])
    session = secrets.token_hex(16)
    base = f'http://127.0.0.1:{config["model_port"]}'
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(path, method='GET', data=None):
        req = urllib.request.Request(base+path, method=method, data=data, headers={
            'Authorization': 'Bearer '+config['backend_token'], 'Content-Type': 'audio/wav'})
        with opener.open(req, timeout=15) as response:
            return json.load(response)

    health = request('/health')
    if health['state'] != 'ready':
        raise RuntimeError('Load the installed model before running this benchmark')
    root = Path(config['install_path']) / 'current'
    gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.used,driver_version',
                                   '--format=csv,noheader'], text=True).strip()
    metadata = {
        'event': 'metadata', 'date': '2026-11-09', 'samples': len(rows),
        'dataset': 'google/fleurs', 'dataset_revision': rows[0]['revision'],
        'dataset_license': 'CC-BY-4.0', 'manifest_sha256': hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'app_version': config.get('version'), 'model_path': config['model_path'],
        'checkpoint': 'facebook/seamless-m4t-v2-large',
        'checkpoint_revision': '5f8cc790b19fc3f67a61c105133b20b34e3dcb76',
        'gpu_before': gpu, 'platform': platform.platform(),
        'source_language': 'Known dataset label, not automatically identified',
        'audio': 'Complete original recording, no VAD/cropping, converted in RAM to mono PCM16 WAV at original 16kHz',
        'generation': {'max_new_tokens': 256, 'num_beams': 1, 'generate_speech': False, 'dtype': 'float16'},
        'pipeline': 'Existing service: original-language text pass then English translation (German for English input). TTS off.',
        'timing_note': 'asr_seconds is original-text pass including feature preprocessing. request_seconds also includes translation and polling. peak_vram_mib covers both text passes and reports PyTorch allocated memory, not total GPU reservation.',
        'backend_hashes': {f: hashlib.sha256((root/f).read_bytes()).hexdigest()
                           for f in ('backend/model.py', 'backend/app.py', 'backend/audio.py')},
        'health_before': health,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    started_all = time.perf_counter()
    completed = failures = 0
    with args.output.open('x') as output:
        def write(row):
            output.write(json.dumps(row, ensure_ascii=False)+'\n')
            output.flush()
        write(metadata)
        try:
            for index, row in enumerate(rows, 1):
                audio, rate = sf.read(args.manifest.parent/row['audio_path'], dtype='float32')
                if rate != 16000 or audio.ndim != 1 or not np.isfinite(audio).all():
                    raise ValueError('Expected finite original mono 16kHz audio')
                buffer = io.BytesIO()
                sf.write(buffer, np.clip(audio, -1, 1), rate, format='WAV', subtype='PCM_16')
                data = buffer.getvalue()
                uid = str(uuid.uuid4())
                target = 'de' if row['language'] == 'en' else 'en'
                record = {
                    'event': 'sample', 'sample_id': row['sample_id'], 'language': row['language'],
                    'source_lang': LANGUAGES[row['language']], 'target_lang': LANGUAGES[target],
                    'reference': row['raw_transcription'], 'reference_normalized': row['transcription'],
                    'translation_reference': row.get('reference_translations', {}).get(target),
                    'audio_sha256': row['sha256'], 'pcm16_sha256': hashlib.sha256(data).hexdigest(),
                    'audio_seconds': len(audio)/rate, 'hypothesis': '',
                }
                query = urllib.parse.urlencode({'utterance_id': uid, 'source_lang': LANGUAGES[row['language']],
                    'target_lang': LANGUAGES[target], 'speaker_side': 'bottom', 'tts': 'false', 'generation': index})
                start = time.perf_counter()
                try:
                    request(f'/sessions/{session}/utterances?{query}', 'POST', data)
                    while True:
                        result = request(f'/sessions/{session}/utterances/{uid}')
                        if result['status'] in ('complete', 'error'):
                            break
                        if time.perf_counter()-start > args.timeout:
                            raise TimeoutError('Inference deadline exceeded; stopping run to avoid hidden pending work')
                        time.sleep(0.1)
                    record.update(status=result['status'], hypothesis=result.get('original_text', ''),
                                  translated_text=result.get('translated_text', ''), metrics=result.get('metrics', {}))
                    if result.get('error'):
                        record['error'] = result['error']
                except urllib.error.HTTPError as exc:
                    record.update(status='error', error=f'HTTP {exc.code}')
                except (OSError, TimeoutError, ValueError) as exc:
                    record.update(status='error', error=type(exc).__name__)
                    record['request_seconds'] = time.perf_counter()-start
                    write(record)
                    raise
                record['request_seconds'] = time.perf_counter()-start
                write(record)
                if record['status'] == 'complete':
                    completed += 1
                else:
                    failures += 1
                if index % 20 == 0 or index == len(rows):
                    print(json.dumps({'processed': index, 'total': len(rows), 'language': row['language'],
                                      'completed': completed, 'failures': failures,
                                      'elapsed_seconds': round(time.perf_counter()-started_all, 1)}), flush=True)
        finally:
            request(f'/sessions/{session}', 'DELETE')
        write({'event': 'finished', 'completed': completed, 'failures': failures,
               'elapsed_seconds': time.perf_counter()-started_all, 'health_after': request('/health'),
               'gpu_after': subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.total,memory.used',
                                                     '--format=csv,noheader'], text=True).strip()})


if __name__ == '__main__':
    main()
