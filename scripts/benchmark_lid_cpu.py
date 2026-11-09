#!/usr/bin/env python3
"""Offline CPU INT8 language-identification benchmark for faster-whisper."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import random
import resource
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

# This must happen before faster_whisper (or ctranslate2) is imported.
os.environ["CUDA_VISIBLE_DEVICES"] = ""

SCORE_THRESHOLD = 0.8
MARGIN_THRESHOLD = 0.2
SEED = 20261109
REQUIRED_FIELDS = {
    "sample_id", "language", "dataset_config", "sentence_id", "audio_path",
    "duration_seconds", "raw_transcription", "transcription", "gender", "sha256",
}


def percentile(values: Iterable[float], percent: float) -> float | None:
    """Return a deterministic linearly interpolated percentile."""
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * percent / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def meets_threshold(record: dict[str, Any]) -> bool:
    return (record.get("status") == "ok"
            and record["score"] >= SCORE_THRESHOLD
            and record["margin"] >= MARGIN_THRESHOLD)


def policy_decision(records_by_duration: dict[float, dict[str, Any]],
                    durations: list[float]) -> dict[str, Any]:
    """Apply the sequential heuristic without consulting the true language."""
    cumulative_ms = 0.0
    cumulative_cpu_ms = 0.0
    for index, duration in enumerate(durations):
        current = records_by_duration.get(duration)
        if current and current.get("status") == "ok":
            cumulative_ms += float(current["detect_ms"])
            cumulative_cpu_ms += float(current.get("detect_cpu_ms", current["detect_ms"]))
        if index == 0 or not current:
            continue
        previous = records_by_duration.get(durations[index - 1])
        if (previous and meets_threshold(previous) and meets_threshold(current)
                and previous["prediction"] == current["prediction"]):
            return {
                "accepted": True,
                "prediction": current["prediction"],
                "accepted_duration": duration,
                "cumulative_detect_ms": cumulative_ms,
                "cumulative_cpu_ms": cumulative_cpu_ms,
            }
    return {
        "accepted": False,
        "prediction": None,
        "accepted_duration": None,
        "cumulative_detect_ms": cumulative_ms,
        "cumulative_cpu_ms": cumulative_cpu_ms,
    }


def _metrics(records: list[dict[str, Any]], total_samples: int) -> dict[str, Any]:
    accepted = [record for record in records if meets_threshold(record)]
    correct = sum(bool(record["correct"]) for record in accepted)
    runtimes = [float(record["detect_ms"]) for record in records]
    return {
        "attempted": len(records),
        "top1_accuracy": (sum(bool(r["correct"]) for r in records) / len(records)
                          if records else None),
        "single_threshold_accepted": len(accepted),
        "single_threshold_coverage": len(accepted) / total_samples if total_samples else None,
        "single_threshold_accuracy": correct / len(accepted) if accepted else None,
        "detect_ms_median": statistics.median(runtimes) if runtimes else None,
        "detect_ms_p95": percentile(runtimes, 95),
    }


def summarize_records(records: list[dict[str, Any]],
                      durations: list[float]) -> dict[str, Any]:
    """Summarize primary speech calls; warmups, controls and full are excluded."""
    primary = [r for r in records if r.get("event") == "detection" and not r.get("control")]
    grouped: dict[str, dict[float, dict[str, Any]]] = defaultdict(dict)
    sample_info: dict[str, dict[str, str]] = {}
    for record in primary:
        sample_id = record["sample_id"]
        sample_info[sample_id] = {"language": record["language"]}
        if isinstance(record.get("checkpoint_seconds"), (int, float)):
            grouped[sample_id][float(record["checkpoint_seconds"])] = record

    decisions = []
    wrong = []
    for sample_id in sorted(sample_info):
        decision = policy_decision(grouped[sample_id], durations)
        truth = sample_info[sample_id]["language"]
        decision.update({"sample_id": sample_id, "language": truth})
        decision["correct"] = decision["accepted"] and decision["prediction"] == truth
        decisions.append(decision)
        if decision["accepted"] and not decision["correct"]:
            wrong.append({
                "sample_id": sample_id,
                "truth": truth,
                "prediction": decision["prediction"],
                "accepted_duration": decision["accepted_duration"],
            })

    accepted = [decision for decision in decisions if decision["accepted"]]
    correct_accepted = sum(bool(decision["correct"]) for decision in accepted)
    total = len(decisions)
    policy = {
        "description": "Heuristic, not a guarantee: two consecutive matching predictions, each score >= 0.8 and margin >= 0.2.",
        "total": total,
        "accepted": len(accepted),
        "correct_accepted": correct_accepted,
        "wrong_accepted": len(accepted) - correct_accepted,
        "abstained": total - len(accepted),
        "coverage": len(accepted) / total if total else None,
        "accuracy_among_accepted": correct_accepted / len(accepted) if accepted else None,
        "accepted_audio_seconds_median": statistics.median(
            [d["accepted_duration"] for d in accepted]) if accepted else None,
        "accepted_audio_seconds_p95": percentile(
            [d["accepted_duration"] for d in accepted], 95),
        "cumulative_detect_ms_median": statistics.median(
            [d["cumulative_detect_ms"] for d in decisions]) if decisions else None,
        "cumulative_detect_ms_p95": percentile(
            [d["cumulative_detect_ms"] for d in decisions], 95),
        "cumulative_cpu_ms_median": statistics.median(
            [d["cumulative_cpu_ms"] for d in decisions]) if decisions else None,
        "cumulative_cpu_ms_p95": percentile(
            [d["cumulative_cpu_ms"] for d in decisions], 95),
        "wrong_accepted_examples": wrong,
    }
    per_duration = {}
    for duration in durations:
        calls = [by_duration[duration] for by_duration in grouped.values()
                 if duration in by_duration and by_duration[duration].get("status") == "ok"]
        per_duration[str(duration)] = _metrics(calls, total)

    per_language = {}
    for language in sorted({info["language"] for info in sample_info.values()}):
        ids = {sample_id for sample_id, info in sample_info.items()
               if info["language"] == language}
        language_decisions = [d for d in decisions if d["sample_id"] in ids]
        language_accepted = [d for d in language_decisions if d["accepted"]]
        item: dict[str, Any] = {}
        for duration in (5.0, 8.0):
            calls = [grouped[sample_id][duration] for sample_id in ids
                     if duration in grouped[sample_id]
                     and grouped[sample_id][duration].get("status") == "ok"]
            item[str(duration)] = _metrics(calls, len(ids))
        correct = sum(bool(d["correct"]) for d in language_accepted)
        item["sequential_policy"] = {
            "total": len(ids),
            "accepted": len(language_accepted),
            "abstained": len(ids) - len(language_accepted),
            "coverage": len(language_accepted) / len(ids) if ids else None,
            "accuracy_among_accepted": correct / len(language_accepted)
            if language_accepted else None,
        }
        per_language[language] = item
    return {"policy": policy, "per_duration": per_duration, "per_language": per_language}


def parse_durations(value: str) -> list[float]:
    try:
        durations = [float(part.strip()) for part in value.split(",")]
    except ValueError as exc:
        raise argparse.ArgumentTypeError("durations must be comma-separated numbers") from exc
    if not durations or any(not math.isfinite(d) or d <= 0 for d in durations):
        raise argparse.ArgumentTypeError("durations must be positive finite numbers")
    if len(set(durations)) != len(durations):
        raise argparse.ArgumentTypeError("durations must not repeat")
    if durations != sorted(durations):
        raise argparse.ArgumentTypeError("durations must be strictly increasing")
    return durations


def load_manifest(path: Path, per_language: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    counts: dict[str, int] = defaultdict(int)
    seen_ids: set[str] = set()
    seen_sentences: dict[str, set[str]] = defaultdict(set)
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"{path}:{line_number}: each line must contain a JSON object")
            missing = REQUIRED_FIELDS - item.keys()
            if missing:
                raise ValueError(f"{path}:{line_number}: missing fields: {sorted(missing)}")
            sample_id = item["sample_id"]
            language = item["language"]
            if not isinstance(sample_id, str) or not sample_id or sample_id in seen_ids:
                raise ValueError(f"{path}:{line_number}: sample_id must be a unique nonempty string")
            seen_ids.add(sample_id)
            if not isinstance(language, str) or not language:
                raise ValueError(f"{path}:{line_number}: language must be a nonempty string")
            sentence_id = str(item["sentence_id"])
            if sentence_id in seen_sentences[language]:
                raise ValueError(f"{path}:{line_number}: repeated sentence_id for {language}")
            seen_sentences[language].add(sentence_id)
            if not isinstance(item["audio_path"], str) or not item["audio_path"]:
                raise ValueError(f"{path}:{line_number}: audio_path must be a nonempty string")
            audio_path = (path.parent / item["audio_path"]).resolve()
            if not audio_path.is_file():
                raise ValueError(f"{path}:{line_number}: audio file not found: {audio_path}")
            if counts[language] < per_language:
                copied = dict(item)
                copied["resolved_audio_path"] = str(audio_path)
                selected.append(copied)
                counts[language] += 1
    if not selected:
        raise ValueError("manifest contains no samples")
    return selected


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _peak_rss_mib() -> float | None:
    if sys.platform != "linux":
        return None
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def _model_property(model: Any, name: str) -> str | None:
    for candidate in (model, getattr(model, "model", None)):
        value = getattr(candidate, name, None)
        if value is not None and not callable(value):
            return str(value)
    return None


def _write_jsonl(handle: Any, record: dict[str, Any]) -> None:
    handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    handle.flush()


def _detect(model: Any, audio: Any) -> tuple[
        str, float, dict[str, Any] | None, float, list[dict[str, Any]], float, float]:
    started = time.perf_counter()
    cpu_started = time.process_time()
    prediction, score, probabilities = model.detect_language(
        audio=audio, vad_filter=False, language_detection_segments=1)
    cpu_ms = (time.process_time() - cpu_started) * 1000
    elapsed_ms = (time.perf_counter() - started) * 1000
    pairs = probabilities.items() if hasattr(probabilities, "items") else probabilities
    ranked = sorted(pairs, key=lambda item: (-item[1], item[0]))
    top5 = [{"language": language, "score": float(value)} for language, value in ranked[:5]]
    runner_up = ({"language": ranked[1][0], "score": float(ranked[1][1])}
                 if len(ranked) > 1 else None)
    runner_score = float(ranked[1][1]) if len(ranked) > 1 else 0.0
    return (prediction, float(score), runner_up, float(score) - runner_score,
            top5, elapsed_ms, cpu_ms)


def run(args: argparse.Namespace) -> None:
    # Heavy dependencies stay out of policy-only imports and tests.
    import numpy as np
    import soundfile as sf
    from faster_whisper import WhisperModel

    selected = load_manifest(args.manifest, args.per_language)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, Any] = {
        "manifest": str(args.manifest.resolve()), "model_path": args.model,
        "model_label": args.model_label, "threads": args.threads,
        "per_language": args.per_language, "durations": args.durations,
        "include_full": args.include_full, "controls": args.controls,
        "speech_onset": args.speech_onset,
        "duration_origin": "Precomputed VAD speech onset" if args.speech_onset else "Original file start",
        "seed": SEED, "cuda_visible_devices": os.environ["CUDA_VISIBLE_DEVICES"],
        "thread_environment": {key: os.environ.get(key) for key in
                               ("OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "OMP_NUM_THREADS")},
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "platform": platform.platform(), "python": platform.python_version(),
        "cpu": {"machine": platform.machine(), "processor": platform.processor(),
                "logical_count": os.cpu_count()},
        "packages": {name: _package_version(name) for name in
                     ("faster-whisper", "ctranslate2", "numpy", "soundfile")},
        "loadavg_start": os.getloadavg(), "selected_samples": len(selected),
        "selected_per_language": dict(sorted(
            (language, sum(sample["language"] == language for sample in selected))
            for language in {sample["language"] for sample in selected})),
        "score_note": "Detector scores are raw model outputs, not calibrated probabilities.",
    }
    records: list[dict[str, Any]] = []
    cache: dict[str, tuple[Any, int]] = {}
    with args.output.open("w", encoding="utf-8") as output:
        _write_jsonl(output, {"event": "metadata_start", **metadata})
        load_started = time.perf_counter()
        model = WhisperModel(args.model, device="cpu", compute_type="int8",
                             cpu_threads=args.threads, num_workers=1,
                             local_files_only=True)
        metadata["model_load_seconds"] = time.perf_counter() - load_started
        metadata["actual_device"] = _model_property(model, "device")
        metadata["actual_compute_type"] = _model_property(model, "compute_type")
        if metadata["actual_device"] and metadata["actual_device"].lower() != "cpu":
            raise RuntimeError(f"model device is not CPU: {metadata['actual_device']}")
        if (metadata["actual_compute_type"]
                and not metadata["actual_compute_type"].lower().startswith("int8")):
            raise RuntimeError(f"model compute type is not INT8: {metadata['actual_compute_type']}")

        def audio_for(sample: dict[str, Any]) -> tuple[Any, int]:
            sample_id = sample["sample_id"]
            if sample_id not in cache:
                started = time.perf_counter()
                audio, sample_rate = sf.read(sample["resolved_audio_path"], dtype="float32",
                                             always_2d=False)
                decode_ms = (time.perf_counter() - started) * 1000
                if sample_rate != 16000 or getattr(audio, "ndim", 1) != 1:
                    raise ValueError(f"{sample_id}: expected mono 16 kHz WAV")
                offset = int(sample['start_sample']) if args.speech_onset else 0
                if not 0 <= offset < len(audio):
                    raise ValueError(f"{sample_id}: invalid speech onset")
                audio = audio[offset:]
                cache[sample_id] = (audio, sample_rate)
                _write_jsonl(output, {"event": "audio_decode", "sample_id": sample_id,
                                      "decode_ms": decode_ms, "frames": len(audio),
                                      "start_sample": offset,
                                      "sample_rate": sample_rate})
            return cache[sample_id]

        warm_audio, warm_rate = audio_for(selected[0])
        warm_prefix = warm_audio[:min(len(warm_audio), 5 * warm_rate)]
        for warmup_number in (1, 2):
            prediction, score, runner, margin, top5, detect_ms, cpu_ms = _detect(
                model, warm_prefix)
            _write_jsonl(output, {"event": "warmup", "warmup_number": warmup_number,
                                  "sample_id": selected[0]["sample_id"],
                                  "prefix_seconds": len(warm_prefix) / warm_rate,
                                  "prediction": prediction, "score": score,
                                  "runner_up": runner, "margin": margin,
                                  "top5": top5, "detect_ms": detect_ms,
                                  "detect_cpu_ms": cpu_ms})

        jobs = [(sample, duration) for sample in selected for duration in args.durations]
        if args.include_full:
            jobs.extend((sample, "full") for sample in selected)
        random.Random(SEED).shuffle(jobs)
        completed = 0
        for sample, checkpoint in jobs:
            audio, sample_rate = audio_for(sample)
            requested_frames = len(audio) if checkpoint == "full" else round(checkpoint * sample_rate)
            if checkpoint != "full" and len(audio) < requested_frames:
                record = {"event": "detection", "status": "skipped_too_short",
                          "sample_id": sample["sample_id"], "language": sample["language"],
                          "checkpoint_seconds": checkpoint,
                          "available_seconds": len(audio) / sample_rate, "control": False}
            else:
                prefix = audio[:requested_frames]
                prediction, score, runner, margin, top5, detect_ms, cpu_ms = _detect(
                    model, prefix)
                record = {"event": "detection", "status": "ok",
                          "sample_id": sample["sample_id"], "language": sample["language"],
                          "checkpoint_seconds": checkpoint,
                          "prefix_seconds": len(prefix) / sample_rate,
                          "prediction": prediction, "score": score,
                          "runner_up": runner, "margin": margin, "top5": top5,
                          "correct": prediction == sample["language"],
                          "detect_ms": detect_ms, "detect_cpu_ms": cpu_ms,
                          "control": False}
            records.append(record)
            _write_jsonl(output, record)
            completed += 1
            if completed % 100 == 0 or completed == len(jobs):
                print(f"primary calls: {completed}/{len(jobs)}", file=sys.stderr, flush=True)

        if args.controls:
            rng = np.random.default_rng(SEED)
            for kind in ("silence", "gaussian_noise"):
                for seconds in (3, 8):
                    audio = (np.zeros(seconds * 16000, dtype=np.float32) if kind == "silence"
                             else rng.normal(0, 1e-4, seconds * 16000).astype(np.float32))
                    prediction, score, runner, margin, top5, detect_ms, cpu_ms = _detect(
                        model, audio)
                    record = {"event": "control_detection", "status": "ok",
                              "control": True, "control_kind": kind,
                              "checkpoint_seconds": seconds, "prefix_seconds": seconds,
                              "prediction": prediction, "score": score,
                              "runner_up": runner, "margin": margin, "top5": top5,
                              "detect_ms": detect_ms, "detect_cpu_ms": cpu_ms}
                    records.append(record)
                    _write_jsonl(output, record)

        metadata["loadavg_end"] = os.getloadavg()
        metadata["peak_rss_mib_linux"] = _peak_rss_mib()
        summary = {"metadata": metadata, **summarize_records(records, args.durations),
                   "controls": [r for r in records if r.get("control")]}
        summary_path = args.output.with_suffix(".summary.json")
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2,
                                           sort_keys=True) + "\n", encoding="utf-8")
        _write_jsonl(output, {"event": "metadata_final", **metadata,
                              "summary_path": str(summary_path)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-label", choices=("tiny", "base"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--per-language", type=int, default=10)
    parser.add_argument("--durations", type=parse_durations, default=parse_durations("1,2,3,5,8"))
    parser.add_argument("--include-full", action="store_true")
    parser.add_argument("--controls", action="store_true")
    parser.add_argument("--speech-onset", action="store_true",
                        help="Measure prefixes from the precomputed manifest start_sample")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.threads <= 0:
        parser.error("--threads must be positive")
    if args.per_language <= 0:
        parser.error("--per-language must be positive")
    if not args.manifest.is_file():
        parser.error(f"manifest not found: {args.manifest}")
    if args.output.resolve() == args.manifest.resolve():
        parser.error("output must not overwrite the manifest")
    try:
        run(args)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
