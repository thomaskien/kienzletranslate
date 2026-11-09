#!/usr/bin/env python3
"""Evaluate ASR with known source languages, without external packages."""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import statistics
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


APOSTROPHES = {"'", "\u2019", "\u2018", "\u02bc"}


def normalize_text(text: str, language: str) -> str:
    """Apply the project's symmetric primary ASR normalization."""
    value = unicodedata.normalize("NFKC", text)
    if language.lower() == "tr":
        value = value.replace("I", "ı").replace("İ", "i")
    value = value.lower()
    normalized: list[str] = []
    for character in value:
        if character in APOSTROPHES:
            continue
        if character == "\u200c":
            normalized.append(" ")
            continue
        category = unicodedata.category(character)
        if category == "Cf":
            continue
        if category[0] in {"P", "S"}:
            normalized.append(" ")
        else:
            normalized.append(character)
    return " ".join("".join(normalized).split())


def strict_normalize(text: str) -> str:
    """Apply the secondary normalization: NFC plus whitespace collapse only."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def _characters(text: str) -> list[str]:
    return [character for character in text if not character.isspace()]


def edit_distance(reference: Sequence[str], hypothesis: Sequence[str],
                  include_operations: bool = False) -> dict[str, Any]:
    """Return Levenshtein S/D/I/H counts and, optionally, an alignment.

    Backtrace ties are resolved as deletion, substitution, then insertion. A
    zero-cost hit is always taken when the current items are identical.
    """
    ref_length = len(reference)
    hyp_length = len(hypothesis)
    previous = list(range(hyp_length + 1))
    # One byte per matrix cell keeps the deterministic alignment compact while
    # the numeric distance calculation itself only retains two rows.
    backtrace = [bytearray(hyp_length + 1) for _ in range(ref_length + 1)]
    for column in range(1, hyp_length + 1):
        backtrace[0][column] = ord("I")

    for row in range(1, ref_length + 1):
        current = [row] + [0] * hyp_length
        backtrace[row][0] = ord("D")
        for column in range(1, hyp_length + 1):
            if reference[row - 1] == hypothesis[column - 1]:
                current[column] = previous[column - 1]
                operation = "H"
            else:
                # Candidate order implements the documented deterministic tie-break.
                candidates = (
                    (previous[column] + 1, "D"),
                    (previous[column - 1] + 1, "S"),
                    (current[column - 1] + 1, "I"),
                )
                current[column], operation = min(candidates, key=lambda item: item[0])
            backtrace[row][column] = ord(operation)
        previous = current

    row = ref_length
    column = hyp_length
    counts = {"substitutions": 0, "deletions": 0, "insertions": 0, "hits": 0}
    operations: list[dict[str, str]] = []
    while row or column:
        operation = chr(backtrace[row][column])
        if operation == "H":
            row -= 1
            column -= 1
            counts["hits"] += 1
            if include_operations:
                operations.append({
                    "operation": "hit", "reference": reference[row],
                    "hypothesis": hypothesis[column],
                })
        elif operation == "S":
            row -= 1
            column -= 1
            counts["substitutions"] += 1
            if include_operations:
                operations.append({
                    "operation": "substitution", "reference": reference[row],
                    "hypothesis": hypothesis[column],
                })
        elif operation == "D":
            row -= 1
            counts["deletions"] += 1
            if include_operations:
                operations.append({
                    "operation": "deletion", "reference": reference[row],
                    "hypothesis": "",
                })
        elif operation == "I":
            column -= 1
            counts["insertions"] += 1
            if include_operations:
                operations.append({
                    "operation": "insertion", "reference": "",
                    "hypothesis": hypothesis[column],
                })
        else:  # pragma: no cover - guards against an implementation defect
            raise RuntimeError(f"invalid backtrace operation {operation!r}")
    result: dict[str, Any] = counts
    result["errors"] = counts["substitutions"] + counts["deletions"] + counts["insertions"]
    if include_operations:
        operations.reverse()
        result["operations"] = operations
    return result


def _score(reference: Sequence[str], hypothesis: Sequence[str],
           include_operations: bool = False) -> dict[str, Any]:
    result = edit_distance(reference, hypothesis, include_operations=include_operations)
    result["reference_units"] = len(reference)
    result["rate"] = result["errors"] / len(reference) if reference else None
    return result


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


def _finite_nonnegative(value: Any, field: str, location: str,
                        required: bool = False) -> float | None:
    if value is None and not required:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{location}: {field} must be a number")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{location}: {field} must be finite and nonnegative")
    return number


def _reject_nonfinite(value: Any, location: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{location}: NaN and infinity are unsupported")
    if isinstance(value, dict):
        for nested in value.values():
            _reject_nonfinite(nested, location)
    elif isinstance(value, list):
        for nested in value:
            _reject_nonfinite(nested, location)


def _is_sensitive_key(key: str) -> bool:
    normalized = "".join(
        character.lower() if character.isalnum() else "_" for character in key)
    parts = [part for part in normalized.split("_") if part]
    part_set = set(parts)
    if part_set & {
        "authorization", "cookie", "credential", "credentials", "passwd",
        "password", "secret", "token",
    }:
        return True
    joined = "".join(parts)
    return joined in {"apikey", "privatekey"}


def _sanitize_metadata(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _sanitize_metadata(nested)
            for key, nested in value.items()
            if isinstance(key, str)
            and not _is_sensitive_key(key)
        }
    if isinstance(value, list):
        return [_sanitize_metadata(item) for item in value]
    return value


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Load, validate and score sample records from the runner JSONL."""
    samples: list[dict[str, Any]] = []
    metadata: dict[str, Any] | None = None
    seen_ids: set[str] = set()

    def reject_constant(value: str) -> None:
        raise ValueError(f"unsupported numeric constant {value}")

    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            location = f"{path}:{line_number}"
            try:
                record = json.loads(line, parse_constant=reject_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{location}: invalid JSON: {exc}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"{location}: each line must contain a JSON object")
            _reject_nonfinite(record, location)
            if record.get("event") == "metadata" and metadata is None:
                metadata = _sanitize_metadata(record)
            if record.get("event") != "sample":
                continue

            sample_id = record.get("sample_id")
            language = record.get("language")
            reference = record.get("reference")
            if not isinstance(sample_id, str) or not sample_id.strip():
                raise ValueError(f"{location}: sample_id must be a nonempty string")
            if sample_id in seen_ids:
                raise ValueError(f"{location}: duplicate sample_id {sample_id!r}")
            seen_ids.add(sample_id)
            if not isinstance(language, str) or not language.strip():
                raise ValueError(f"{location}: language must be a nonempty string")
            if not isinstance(reference, str) or not reference.strip():
                raise ValueError(f"{location}: reference must be a nonempty string")
            status = record.get("status")
            if status not in {"complete", "error"}:
                raise ValueError(f"{location}: status must be 'complete' or 'error'")
            hypothesis_value = record.get("hypothesis", "")
            if not isinstance(hypothesis_value, str):
                raise ValueError(f"{location}: hypothesis must be a string")
            hypothesis = hypothesis_value if status == "complete" else ""
            audio_seconds = _finite_nonnegative(
                record.get("audio_seconds"), "audio_seconds", location, required=True)
            metrics = record.get("metrics")
            if metrics is None:
                metrics = {}
            if not isinstance(metrics, dict):
                raise ValueError(f"{location}: metrics must be an object")
            asr_seconds = _finite_nonnegative(
                metrics.get("asr_seconds"), "metrics.asr_seconds", location)
            peak_vram_mib = _finite_nonnegative(
                metrics.get("peak_vram_mib"), "metrics.peak_vram_mib", location)
            request_seconds = _finite_nonnegative(
                record.get("request_seconds"), "request_seconds", location)

            normalized_reference = normalize_text(reference, language)
            normalized_hypothesis = normalize_text(hypothesis, language)
            if not normalized_reference.split():
                raise ValueError(
                    f"{location}: reference is empty after primary normalization")
            strict_reference = strict_normalize(reference)
            strict_hypothesis = strict_normalize(hypothesis)
            word = _score(normalized_reference.split(), normalized_hypothesis.split(), True)
            character = _score(
                _characters(normalized_reference), _characters(normalized_hypothesis))
            strict_word = _score(strict_reference.split(), strict_hypothesis.split())
            samples.append({
                "sample_id": sample_id,
                "language": language,
                "source_lang": record.get("source_lang"),
                "status": status,
                "reference": reference,
                "reference_normalized_input": record.get("reference_normalized"),
                "hypothesis": hypothesis,
                "normalized_reference": normalized_reference,
                "normalized_hypothesis": normalized_hypothesis,
                "strict_reference": strict_reference,
                "strict_hypothesis": strict_hypothesis,
                "audio_seconds": audio_seconds,
                "asr_seconds": asr_seconds,
                "request_seconds": request_seconds,
                "peak_vram_mib": peak_vram_mib,
                "error": record.get("error"),
                "word": word,
                "character": character,
                "strict_word": strict_word,
                "exact_normalized_match": normalized_reference == normalized_hypothesis,
            })
    if not samples:
        raise ValueError(f"{path}: no sample records found")
    return samples, metadata


def _sum_counts(samples: Sequence[dict[str, Any]], key: str) -> dict[str, int]:
    names = ("substitutions", "deletions", "insertions", "hits", "errors",
             "reference_units")
    return {name: sum(int(sample[key][name]) for sample in samples) for name in names}


def summarize_group(samples: Sequence[dict[str, Any]]) -> dict[str, Any]:
    word = _sum_counts(samples, "word")
    character = _sum_counts(samples, "character")
    strict_word = _sum_counts(samples, "strict_word")
    complete = [sample for sample in samples if sample["status"] == "complete"]
    asr_values = [sample["asr_seconds"] for sample in complete
                  if sample["asr_seconds"] is not None]
    request_values = [sample["request_seconds"] for sample in samples
                      if sample["request_seconds"] is not None]
    peak_values = [sample["peak_vram_mib"] for sample in samples
                   if sample["peak_vram_mib"] is not None]
    rtf_samples = [sample for sample in complete if sample["asr_seconds"] is not None]
    completed_audio = sum(sample["audio_seconds"] for sample in rtf_samples)
    completed_asr = sum(sample["asr_seconds"] for sample in rtf_samples)
    return {
        "n": len(samples),
        "completed": len(complete),
        "failures": len(samples) - len(complete),
        "coverage": len(complete) / len(samples) if samples else None,
        "duration_seconds": sum(sample["audio_seconds"] for sample in samples),
        "reference_words": word["reference_units"],
        "reference_characters": character["reference_units"],
        "word": word,
        "wer": word["errors"] / word["reference_units"] if word["reference_units"] else None,
        "character": character,
        "cer": (character["errors"] / character["reference_units"]
                if character["reference_units"] else None),
        "strict_word": strict_word,
        "strict_wer": (strict_word["errors"] / strict_word["reference_units"]
                       if strict_word["reference_units"] else None),
        "exact_normalized_matches": sum(
            bool(sample["exact_normalized_match"]) for sample in samples),
        "asr_latency_seconds_median": statistics.median(asr_values) if asr_values else None,
        "asr_latency_seconds_p95": percentile(asr_values, 95),
        "request_latency_seconds_median": (
            statistics.median(request_values) if request_values else None),
        "request_latency_seconds_p95": percentile(request_values, 95),
        "peak_allocated_mib": max(peak_values) if peak_values else None,
        "rtf": completed_asr / completed_audio if completed_audio else None,
        "rtf_asr_seconds": completed_asr,
        "rtf_audio_seconds": completed_audio,
        "rtf_sample_count": len(rtf_samples),
    }


def build_summary(samples: list[dict[str, Any]], metadata: dict[str, Any] | None,
                  title: str) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for sample in samples:
        grouped[sample["language"]].append(sample)
    per_language = {
        language: summarize_group(grouped[language]) for language in sorted(grouped)
    }
    aggregate = summarize_group(samples)
    language_wers = [item["wer"] for item in per_language.values()
                     if item["wer"] is not None]
    aggregate["macro_average_language_wer"] = (
        sum(language_wers) / len(language_wers) if language_wers else None)
    return {
        "title": title,
        "metric_definition": {
            "primary": (
                "Project-specific symmetric NFKC/case/punctuation normalization; "
                "not the exact published FLEURS benchmark normalization."),
            "strict": "Symmetric NFC normalization with whitespace collapse only.",
            "alignment_tie_break": "deletion, then substitution, then insertion",
            "wer_formula": "sum(S + D + I) / sum(reference words)",
            "cer_formula": "sum(S + D + I) / sum(non-whitespace reference characters)",
        },
        "metadata": metadata,
        "aggregate": aggregate,
        "per_language": per_language,
        "failed_sample_ids": [sample["sample_id"] for sample in samples
                              if sample["status"] == "error"],
    }


def _format_number(value: Any, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.{digits}f}"


def _format_percent(value: float | None) -> str:
    return "n/a" if value is None else f"{value * 100:.2f}%"


def _markdown_code(value: Any) -> str:
    rendered = json.dumps(value if isinstance(value, str) else str(value), ensure_ascii=False)
    return f"<code>{html.escape(rendered, quote=True)}</code>"


def _worst_samples(samples: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_language: dict[str, int] = defaultdict(int)
    ordered = sorted(
        samples,
        key=lambda sample: (
            -float(sample["word"]["rate"]), sample["language"], sample["sample_id"]),
    )
    for sample in ordered:
        if per_language[sample["language"]] >= 2:
            continue
        selected.append(sample)
        per_language[sample["language"]] += 1
        if len(selected) == 12:
            break
    return selected


def render_report(summary: dict[str, Any], samples: Sequence[dict[str, Any]]) -> str:
    aggregate = summary["aggregate"]
    lines = [
        f"# {summary['title']}",
        "",
        "## Scope and interpretation",
        "",
        ("This report evaluates ASR with known source languages: every recording is supplied with "
         "its known source language. It is not a language-identification or translation-"
         "quality evaluation. The inference pipeline may also produce translations, but "
         "they are not scored here. Full recordings are evaluated without speech-onset "
         "trimming."),
        "",
        ("WER and CER are corpus-weighted edit error rates, not accuracy. WER can exceed "
         "100%. Low WER does not guarantee semantic correctness. The primary symmetric "
         "normalization is a project metric, not the exact published FLEURS benchmark "
         "normalization; strict WER retains case and punctuation."),
        "",
        ("The source dataset is public FLEURS (CC BY 4.0). This small, non-random sample "
         "of 20 clips per language is not a robust language ranking. Word-boundary and "
         "orthography conventions particularly affect Persian and Arabic word scores."),
        "",
        "## Overall results",
        "",
        f"- Recordings: {aggregate['n']} ({aggregate['completed']} complete, {aggregate['failures']} failed)",
        f"- Coverage: {_format_percent(aggregate['coverage'])}",
        f"- Audio duration: {_format_number(aggregate['duration_seconds'], 2)} seconds",
        f"- Reference units: {aggregate['reference_words']} words, {aggregate['reference_characters']} non-whitespace characters",
        f"- Corpus-weighted WER: {_format_percent(aggregate['wer'])}",
        f"- Corpus-weighted CER: {_format_percent(aggregate['cer'])}",
        f"- Strict WER: {_format_percent(aggregate['strict_wer'])}",
        f"- Macro average per-language WER: {_format_percent(aggregate['macro_average_language_wer'])}",
        f"- Exact normalized matches: {aggregate['exact_normalized_matches']}",
        f"- ASR real-time factor (completed recordings only): {_format_number(aggregate['rtf'])}",
        "",
        ("Model ASR computation latency and whole-request latency are kept separate: "
         f"ASR median/P95 = {_format_number(aggregate['asr_latency_seconds_median'])}/"
         f"{_format_number(aggregate['asr_latency_seconds_p95'])} s; request median/P95 = "
         f"{_format_number(aggregate['request_latency_seconds_median'])}/"
         f"{_format_number(aggregate['request_latency_seconds_p95'])} s. Peak allocated "
         f"memory reported by the runner: {_format_number(aggregate['peak_allocated_mib'], 1)} MiB."),
        "",
        ("Word diagnostic totals (S/D/I/H): "
         f"{aggregate['word']['substitutions']}/{aggregate['word']['deletions']}/"
         f"{aggregate['word']['insertions']}/{aggregate['word']['hits']}. "
         "Alignment ties prefer deletion, then substitution, then insertion."),
        "",
        "## Per-language results",
        "",
        "| Language | Clips | WER | CER | ASR median (s) | ASR P95 (s) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for language, item in summary["per_language"].items():
        word = item["word"]
        lines.append(
            f"| {language} | {item['n']} | "
            f"{_format_percent(item['wer'])} | {_format_percent(item['cer'])} | "
            f"{_format_number(item['asr_latency_seconds_median'])} | "
            f"{_format_number(item['asr_latency_seconds_p95'])} |")

    failed = summary["failed_sample_ids"]
    lines.extend(["", "## Failed recordings", ""])
    if failed:
        lines.append(
            "Failed recordings are scored with an empty hypothesis (all reference units "
            "are deletions): " + ", ".join(_markdown_code(item) for item in failed) + ".")
    else:
        lines.append("None.")

    lines.extend(["", "## Worst normalized-WER samples", ""])
    for sample in _worst_samples(samples):
        word = sample["word"]
        lines.extend([
            (f"### {_markdown_code(sample['sample_id'])} ({sample['language']}, "
             f"WER {_format_percent(word['rate'])}, S/D/I "
             f"{word['substitutions']}/{word['deletions']}/{word['insertions']})"),
            "",
            f"- Reference: {_markdown_code(sample['reference'])}",
            f"- Hypothesis: {_markdown_code(sample['hypothesis'])}",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def _csv_value(value: Any) -> Any:
    return "" if value is None else value


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(output_dir: Path, summary: dict[str, Any],
                  samples: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "summary.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    with (output_dir / "report.md").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_report(summary, samples))

    language_fields = [
        "language", "n", "completed", "failures", "coverage", "duration_seconds",
        "reference_words", "reference_characters", "word_substitutions",
        "word_deletions", "word_insertions", "word_hits", "wer", "cer",
        "strict_wer", "exact_normalized_matches", "asr_latency_seconds_median",
        "asr_latency_seconds_p95", "request_latency_seconds_median",
        "request_latency_seconds_p95", "peak_allocated_mib", "rtf",
    ]
    language_rows = []
    for language, item in summary["per_language"].items():
        language_rows.append({
            "language": language,
            "n": item["n"],
            "completed": item["completed"],
            "failures": item["failures"],
            "coverage": _csv_value(item["coverage"]),
            "duration_seconds": item["duration_seconds"],
            "reference_words": item["reference_words"],
            "reference_characters": item["reference_characters"],
            "word_substitutions": item["word"]["substitutions"],
            "word_deletions": item["word"]["deletions"],
            "word_insertions": item["word"]["insertions"],
            "word_hits": item["word"]["hits"],
            "wer": _csv_value(item["wer"]),
            "cer": _csv_value(item["cer"]),
            "strict_wer": _csv_value(item["strict_wer"]),
            "exact_normalized_matches": item["exact_normalized_matches"],
            "asr_latency_seconds_median": _csv_value(item["asr_latency_seconds_median"]),
            "asr_latency_seconds_p95": _csv_value(item["asr_latency_seconds_p95"]),
            "request_latency_seconds_median": _csv_value(item["request_latency_seconds_median"]),
            "request_latency_seconds_p95": _csv_value(item["request_latency_seconds_p95"]),
            "peak_allocated_mib": _csv_value(item["peak_allocated_mib"]),
            "rtf": _csv_value(item["rtf"]),
        })
    write_csv(output_dir / "per-language.csv", language_fields, language_rows)

    sample_fields = [
        "sample_id", "language", "source_lang", "status", "audio_seconds",
        "reference_words", "word_substitutions", "word_deletions",
        "word_insertions", "word_hits", "wer", "cer", "strict_wer",
        "exact_normalized_match", "asr_seconds", "request_seconds",
        "peak_allocated_mib", "reference", "reference_normalized_input",
        "hypothesis", "normalized_reference", "normalized_hypothesis",
        "word_operations", "error",
    ]
    sample_rows = []
    for sample in samples:
        sample_rows.append({
            "sample_id": sample["sample_id"],
            "language": sample["language"],
            "source_lang": _csv_value(sample["source_lang"]),
            "status": sample["status"],
            "audio_seconds": sample["audio_seconds"],
            "reference_words": sample["word"]["reference_units"],
            "word_substitutions": sample["word"]["substitutions"],
            "word_deletions": sample["word"]["deletions"],
            "word_insertions": sample["word"]["insertions"],
            "word_hits": sample["word"]["hits"],
            "wer": sample["word"]["rate"],
            "cer": sample["character"]["rate"],
            "strict_wer": sample["strict_word"]["rate"],
            "exact_normalized_match": sample["exact_normalized_match"],
            "asr_seconds": _csv_value(sample["asr_seconds"]),
            "request_seconds": _csv_value(sample["request_seconds"]),
            "peak_allocated_mib": _csv_value(sample["peak_vram_mib"]),
            "reference": sample["reference"],
            "reference_normalized_input": _csv_value(
                sample["reference_normalized_input"]),
            "hypothesis": sample["hypothesis"],
            "normalized_reference": sample["normalized_reference"],
            "normalized_hypothesis": sample["normalized_hypothesis"],
            "word_operations": json.dumps(
                sample["word"]["operations"], ensure_ascii=False,
                separators=(",", ":")),
            "error": _csv_value(sample["error"]),
        })
    write_csv(output_dir / "per-sample.csv", sample_fields, sample_rows)


def evaluate(input_path: Path, output_dir: Path,
             title: str = "English ASR quality evaluation") -> dict[str, Any]:
    samples, metadata = load_jsonl(input_path)
    summary = build_summary(samples, metadata, title)
    write_outputs(output_dir, summary, samples)
    return summary


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate ASR JSONL records and write an English offline report.")
    parser.add_argument("--input", required=True, type=Path, help="Runner JSONL file")
    parser.add_argument("--output-dir", required=True, type=Path,
                        help="Directory for report.md, JSON and CSV outputs")
    parser.add_argument("--title", default="English ASR quality evaluation")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = evaluate(args.input, args.output_dir, args.title)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    aggregate = summary["aggregate"]
    print(
        f"Evaluated {aggregate['n']} recordings; "
        f"coverage {_format_percent(aggregate['coverage'])}; "
        f"WER {_format_percent(aggregate['wer'])}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
