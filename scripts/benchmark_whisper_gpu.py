"""Full-audio Whisper large-v3 FP16 comparison against saved Seamless records.

Run only after explicit GPU authorization and unloading other resident models.
No service lifecycle or production configuration is changed by this script.
"""
import argparse
import gc
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import subprocess
import threading
import time
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def gpu_snapshot():
    return subprocess.check_output([
        'nvidia-smi', '--query-gpu=name,memory.total,memory.used,utilization.gpu,driver_version',
        '--format=csv,noheader'], text=True).strip()


class MemoryMonitor:
    """Sample total device use, not framework allocated/reserved memory."""
    def __init__(self):
        self.readings = []
        self.ready = threading.Event()
        self.process = subprocess.Popen([
            'nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits',
            '--loop-ms=100'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, bufsize=1)
        self.thread = threading.Thread(target=self._read, daemon=True)
        self.thread.start()
        if not self.ready.wait(5):
            self.close()
            raise RuntimeError('GPU memory sampler did not start')

    def _read(self):
        for line in self.process.stdout:
            try:
                self.readings.append((time.perf_counter(), float(line.strip())))
                self.ready.set()
            except ValueError:
                continue

    def peak_since(self, started):
        values = [value for stamp, value in self.readings if stamp >= started]
        return max(values) if values else None

    def close(self):
        self.process.terminate()
        self.process.wait(timeout=5)
        self.thread.join(timeout=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--run-date', required=True, help='User-facing YYYY-MM-DD date')
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error('Use a new output directory')
    import numpy as np
    import soundfile as sf
    from faster_whisper import WhisperModel
    import ctranslate2

    rows = [json.loads(line) for line in args.manifest.read_text().splitlines() if line.strip()]
    baseline = [json.loads(line) for line in args.baseline.read_text().splitlines() if line.strip()]
    baseline = [row for row in baseline if row.get('event') == 'sample']
    original = {row['sample_id']: row for row in baseline}
    if len(original) != len(baseline) or len({row['sample_id'] for row in rows}) != len(rows):
        raise ValueError('Duplicate sample IDs')
    if set(original) != {row['sample_id'] for row in rows}:
        raise ValueError('Manifest and baseline must contain exactly the same samples')
    for row in rows:
        reference = original[row['sample_id']]
        if (row['language'] != reference['language'] or row['raw_transcription'] != reference['reference']
                or row['sha256'] != reference['audio_sha256']
                or sha256(args.manifest.parent / row['audio_path']) != row['sha256']):
            raise ValueError('Source mismatch: ' + row['sample_id'])
    model_source = json.loads((args.model / 'benchmark-source.json').read_text())
    if model_source['repository'] != 'Systran/faster-whisper-large-v3':
        raise ValueError('Expected the full large-v3 model')
    options = dict(beam_size=1, best_of=1, temperature=0.0,
                   condition_on_previous_text=False, vad_filter=False,
                   without_timestamps=True, word_timestamps=False,
                   chunk_length=30, max_new_tokens=None,
                   compression_ratio_threshold=2.4, log_prob_threshold=-1.0,
                   no_speech_threshold=0.6, initial_prompt=None, prefix=None,
                   suppress_blank=True, suppress_tokens=[-1])
    metadata = {
        'event': 'metadata', 'date': args.run_date, 'model': 'Whisper large-v3',
        'checkpoint': model_source['repository'], 'checkpoint_revision': model_source['revision'],
        'model_source': model_source, 'model_files_sha256': {
            name: sha256(args.model / name) for name in
            ['model.bin', 'config.json', 'preprocessor_config.json', 'tokenizer.json', 'vocabulary.json']},
        'manifest_sha256': sha256(args.manifest), 'baseline_sha256': sha256(args.baseline),
        'script_sha256': sha256(Path(__file__)), 'samples': len(rows),
        'dataset': 'google/fleurs', 'dataset_revision': rows[0]['revision'], 'dataset_license': 'CC-BY-4.0',
        'source_language': 'Known dataset label, no automatic language identification',
        'audio': 'Full original 16 kHz recordings converted to the exact PCM16 WAV bytes used by Seamless, then decoded to float32; no trimming or VAD.',
        'decoding': options, 'compute_type': 'float16', 'cpu_threads': 8, 'num_workers': 1,
        'runtime': {name: importlib.metadata.version(name) for name in
                    ['faster-whisper', 'ctranslate2', 'numpy', 'soundfile', 'tokenizers', 'av']},
        'python': platform.python_version(), 'platform': platform.platform(),
        'gpu_before_load': gpu_snapshot(), 'pid': os.getpid(),
        'memory_note': 'nvidia-smi total device memory sampled every 100 ms. Not PyTorch allocated or reserved memory; these are unavailable for this CTranslate2 run.',
        'timing_note': 'Wall time covers feature extraction, full lazy segment iteration and text decoding. Audio file/PCM conversion, model load, API/HTTP overhead excluded. No extra warmup pass; first measured request includes first-use overhead.',
    }
    args.output_dir.mkdir(parents=True)
    monitor = MemoryMonitor()
    started_load = time.perf_counter()
    try:
        model = WhisperModel(str(args.model), device='cuda', device_index=0,
                             compute_type='float16', cpu_threads=8, num_workers=1,
                             local_files_only=True)
    except BaseException:
        monitor.close()
        raise
    metadata['load_seconds'] = time.perf_counter() - started_load
    metadata['actual_compute_type'] = model.model.compute_type
    metadata['model_max_length'] = model.max_length
    metadata['gpu_after_load'] = gpu_snapshot()
    metadata['supported_compute_types'] = sorted(ctranslate2.get_supported_compute_types('cuda'))
    (args.output_dir / 'metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps({'loaded': True, 'load_seconds': metadata['load_seconds'],
                      'compute_type': metadata['actual_compute_type']}), flush=True)
    asr_outputs = {}
    phase_results = {}
    started_all = time.perf_counter()
    try:
        for task, filename in [('transcribe', 'asr-records.jsonl'), ('translate', 'translation-records.jsonl')]:
            selected = rows if task == 'transcribe' else [r for r in rows if r['language'] != 'en']
            phase_started = time.perf_counter()
            failed = 0
            with (args.output_dir / filename).open('x', encoding='utf-8') as output:
                output.write(json.dumps({**metadata, 'task': task, 'samples': len(selected)}) + '\n')
                for index, row in enumerate(selected, 1):
                    ref = original[row['sample_id']]
                    audio, rate = sf.read(args.manifest.parent / row['audio_path'], dtype='float32')
                    if rate != 16000 or audio.ndim != 1 or not np.isfinite(audio).all():
                        raise ValueError('Expected finite mono 16 kHz audio')
                    buffer = io.BytesIO()
                    sf.write(buffer, np.clip(audio, -1, 1), rate, format='WAV', subtype='PCM_16')
                    if hashlib.sha256(buffer.getvalue()).hexdigest() != ref['pcm16_sha256']:
                        raise ValueError('PCM16 bytes differ from Seamless input: ' + row['sample_id'])
                    buffer.seek(0)
                    decoded, _ = sf.read(buffer, dtype='float32')
                    record = {key: ref[key] for key in ['sample_id', 'language', 'source_lang',
                              'reference', 'reference_normalized', 'audio_seconds', 'audio_sha256', 'pcm16_sha256']}
                    record.update(event='sample', task=task, status='complete', metrics={})
                    start = time.perf_counter()
                    try:
                        segments, info = model.transcribe(decoded, language=row['language'], task=task, **options)
                        segments = list(segments)  # Inference is lazy; time the entire iteration.
                        text = ''.join(segment.text for segment in segments).strip()
                        elapsed = time.perf_counter() - start
                        record['segments'] = [{'start': s.start, 'end': s.end, 'text': s.text,
                                              'tokens': len(s.tokens), 'avg_logprob': s.avg_logprob,
                                              'no_speech_prob': s.no_speech_prob} for s in segments]
                        record['processed_duration_seconds'] = info.duration
                    except RuntimeError as exc:
                        text = ''
                        elapsed = time.perf_counter() - start
                        record.update(status='error', error=str(exc))
                        failed += 1
                    record['gpu_total_used_mib_peak_sampled'] = monitor.peak_since(start)
                    if task == 'transcribe':
                        record.update(hypothesis=text, target_lang=ref['source_lang'])
                        record['metrics']['asr_seconds'] = elapsed
                        asr_outputs[row['sample_id']] = text
                    else:
                        record.update(hypothesis=asr_outputs[row['sample_id']], translated_text=text,
                                      target_lang='eng', translation_reference=ref['translation_reference'])
                        record['metrics']['translation_seconds'] = elapsed
                    output.write(json.dumps(record, ensure_ascii=False) + '\n')
                    output.flush()
                    if index % 20 == 0 or index == len(selected):
                        print(json.dumps({'task': task, 'processed': index, 'total': len(selected),
                                          'failures': failed, 'elapsed_seconds': round(time.perf_counter()-phase_started, 2)}), flush=True)
                phase_results[task] = {'samples': len(selected), 'failures': failed,
                                       'elapsed_seconds': time.perf_counter() - phase_started,
                                       'gpu_total_used_mib_peak_sampled': monitor.peak_since(phase_started)}
                output.write(json.dumps({'event': 'finished', **phase_results[task]}) + '\n')
        finish = {'event': 'finished', 'phases': phase_results,
                  'elapsed_inference_loop_seconds': time.perf_counter() - started_all,
                  'gpu_total_used_mib_peak_sampled': monitor.peak_since(started_load),
                  'gpu_before_unload': gpu_snapshot(),
                  'compute_processes_before_unload': subprocess.check_output([
                      'nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                      '--format=csv,noheader'], text=True).strip()}
    finally:
        del model
        gc.collect()
        monitor.close()
    (args.output_dir / 'finished.json').write_text(json.dumps(finish, indent=2) + '\n')
    (args.output_dir / 'gpu-memory-samples.json').write_text(json.dumps([
        {'seconds_after_load_start': stamp-started_load, 'device_used_mib': value}
        for stamp, value in monitor.readings], separators=(',', ':')) + '\n')
    print(json.dumps(finish), flush=True)


if __name__ == '__main__':
    main()
