#!/usr/bin/env python3
"""Compare paired ASR and direct-English speech-translation evaluations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Sequence


ASR_OUTPUT = "asr-paired.csv"
TRANSLATION_OUTPUT = "translation-paired.csv"
SUMMARY_OUTPUT = "comparison.json"
REPORT_OUTPUT = "comparison.md"
FLOAT_TOLERANCE = 1e-10
OUTCOME_TOLERANCE = 1e-9

ASR_FIELDS = [
    "sample_id", "language", "reference", "baseline_hypothesis",
    "candidate_hypothesis", "baseline_word_errors", "candidate_word_errors",
    "delta_word_errors", "baseline_wer", "candidate_wer", "delta_wer_pp",
    "baseline_cer", "candidate_cer", "baseline_asr_seconds",
    "candidate_asr_seconds", "candidate_outcome",
]
TRANSLATION_FIELDS = [
    "sample_id", "source_language", "target_language", "reference",
    "baseline_hypothesis", "candidate_hypothesis", "baseline_chrfpp",
    "candidate_chrfpp", "delta_chrfpp", "candidate_outcome",
]


def _json_constant(value: str) -> None:
    raise ValueError(f"unsupported numeric constant {value}")


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), parse_constant=_json_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("missing CSV header")
            if len(reader.fieldnames) != len(set(reader.fieldnames)):
                raise ValueError("duplicate CSV column")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        raise ValueError(f"{path}: invalid CSV: {exc}") from exc
    if not rows:
        raise ValueError(f"{path}: no sample rows")
    return rows


def _require_columns(path: Path, rows: list[dict[str, str]], columns: set[str]) -> None:
    missing = columns - set(rows[0])
    if missing:
        raise ValueError(f"{path}: missing columns: {', '.join(sorted(missing))}")


def _text(row: dict[str, str], field: str, location: str, *, nonempty: bool = True) -> str:
    value = row.get(field)
    if value is None or (nonempty and not value.strip()):
        qualifier = "nonempty " if nonempty else ""
        raise ValueError(f"{location}: {field} must be a {qualifier}string")
    return value


def _number(value: Any, field: str, location: str, *, nonnegative: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{location}: {field} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{location}: {field} must be a number") from exc
    if not math.isfinite(number) or (nonnegative and number < 0):
        suffix = " and nonnegative" if nonnegative else ""
        raise ValueError(f"{location}: {field} must be finite{suffix}")
    return number


def _optional_number(value: Any, field: str, location: str) -> float | None:
    if value in (None, ""):
        return None
    return _number(value, field, location, nonnegative=True)


def _integer(value: Any, field: str, location: str) -> int:
    number = _number(value, field, location, nonnegative=True)
    if not number.is_integer():
        raise ValueError(f"{location}: {field} must be an integer")
    return int(number)


def _object(value: Any, field: str, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{location}: {field} must be an object")
    return value


def _close(actual: float, expected: float, field: str, location: str,
           tolerance: float = FLOAT_TOLERANCE) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance):
        raise ValueError(
            f"{location}: {field} mismatch: found {actual!r}, expected {expected!r}")


def _status(row: dict[str, str], location: str) -> str:
    value = row.get("status")
    if value not in {"complete", "error"}:
        raise ValueError(f"{location}: status must be 'complete' or 'error'")
    return value


def _unique(rows: Iterable[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        sample_id = row["sample_id"]
        if sample_id in indexed:
            raise ValueError(f"{label}: duplicate sample_id {sample_id!r}")
        indexed[sample_id] = row
    return indexed


def _load_asr(directory: Path, label: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    csv_path = directory / "per-sample.csv"
    summary_path = directory / "summary.json"
    rows = _read_csv(csv_path)
    _require_columns(csv_path, rows, {
        "sample_id", "language", "status", "audio_seconds", "reference_words",
        "word_substitutions", "word_deletions", "word_insertions", "word_hits",
        "wer", "cer", "asr_seconds", "reference", "hypothesis",
        "normalized_reference",
    })
    parsed: list[dict[str, Any]] = []
    for line, row in enumerate(rows, 2):
        location = f"{csv_path}:{line}"
        counts = {
            key: _integer(row[f"word_{key}"], f"word_{key}", location)
            for key in ("substitutions", "deletions", "insertions", "hits")
        }
        reference_words = _integer(row["reference_words"], "reference_words", location)
        if reference_words <= 0:
            raise ValueError(f"{location}: reference_words must be positive")
        if counts["substitutions"] + counts["deletions"] + counts["hits"] != reference_words:
            raise ValueError(f"{location}: reference_words is inconsistent with word counts")
        errors = counts["substitutions"] + counts["deletions"] + counts["insertions"]
        wer = _number(row["wer"], "wer", location, nonnegative=True)
        _close(wer, errors / reference_words, "wer", location)
        parsed.append({
            "sample_id": _text(row, "sample_id", location),
            "language": _text(row, "language", location),
            "status": _status(row, location),
            "audio_seconds": _number(
                row["audio_seconds"], "audio_seconds", location, nonnegative=True),
            "reference_words": reference_words,
            "counts": counts,
            "word_errors": errors,
            "wer": wer,
            "cer": _number(row["cer"], "cer", location, nonnegative=True),
            "asr_seconds": _optional_number(row["asr_seconds"], "asr_seconds", location),
            "reference": _text(row, "reference", location),
            "normalized_reference": _text(row, "normalized_reference", location),
            "hypothesis": _text(row, "hypothesis", location, nonempty=False),
        })
    _unique(parsed, label)
    summary = _load_json(summary_path)
    _validate_asr_summary(parsed, summary, summary_path)
    return parsed, summary


def _validate_asr_group(rows: list[dict[str, Any]], group: dict[str, Any],
                        location: str) -> None:
    n = _integer(group.get("n"), "n", location)
    if n != len(rows):
        raise ValueError(f"{location}: n mismatch: found {n}, expected {len(rows)}")
    completed = _integer(group.get("completed"), "completed", location)
    expected_completed = sum(row["status"] == "complete" for row in rows)
    if completed != expected_completed:
        raise ValueError(f"{location}: completed count mismatch")
    failures = _integer(group.get("failures"), "failures", location)
    if failures != len(rows) - expected_completed:
        raise ValueError(f"{location}: failures count mismatch")
    reference_words = sum(row["reference_words"] for row in rows)
    if _integer(group.get("reference_words"), "reference_words", location) != reference_words:
        raise ValueError(f"{location}: reference_words mismatch")
    word = _object(group.get("word"), "word", location)
    expected_counts = {
        key: sum(row["counts"][key] for row in rows)
        for key in ("substitutions", "deletions", "insertions", "hits")
    }
    expected_errors = sum(row["word_errors"] for row in rows)
    expected_word = {
        **expected_counts, "errors": expected_errors, "reference_units": reference_words,
    }
    for field, expected in expected_word.items():
        if _integer(word.get(field), f"word.{field}", location) != expected:
            raise ValueError(f"{location}: word.{field} mismatch")
    wer = _number(group.get("wer"), "wer", location, nonnegative=True)
    _close(wer, expected_errors / reference_words, "wer", location)
    _number(group.get("cer"), "cer", location, nonnegative=True)
    _optional_number(group.get("asr_latency_seconds_median"),
                     "asr_latency_seconds_median", location)


def _validate_asr_summary(rows: list[dict[str, Any]], summary: dict[str, Any],
                          path: Path) -> None:
    aggregate = _object(summary.get("aggregate"), "aggregate", str(path))
    _validate_asr_group(rows, aggregate, f"{path}:aggregate")
    per_language = _object(summary.get("per_language"), "per_language", str(path))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["language"]].append(row)
    if set(per_language) != set(grouped):
        raise ValueError(f"{path}: per_language keys do not match CSV languages")
    for language in sorted(grouped):
        group = _object(per_language[language], language, f"{path}:per_language")
        _validate_asr_group(grouped[language], group, f"{path}:per_language.{language}")


def _load_translation(directory: Path, label: str, *, candidate: bool
                      ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    csv_path = directory / "per-sample.csv"
    summary_path = directory / "summary.json"
    rows = _read_csv(csv_path)
    _require_columns(csv_path, rows, {
        "sample_id", "source_language", "target_language", "status",
        "sentence_chrfpp", "translation_reference", "translation_hypothesis",
        "scoring_reference",
    })
    parsed: list[dict[str, Any]] = []
    for line, row in enumerate(rows, 2):
        location = f"{csv_path}:{line}"
        parsed.append({
            "sample_id": _text(row, "sample_id", location),
            "source_language": _text(row, "source_language", location),
            "target_language": _text(row, "target_language", location),
            "status": _status(row, location),
            "chrfpp": _number(
                row["sentence_chrfpp"], "sentence_chrfpp", location, nonnegative=True),
            "translation_reference": _text(row, "translation_reference", location),
            "scoring_reference": _text(row, "scoring_reference", location),
            "hypothesis": _text(row, "translation_hypothesis", location, nonempty=False),
        })
    _unique(parsed, label)
    if candidate and any(row["target_language"] != "eng" for row in parsed):
        raise ValueError(f"{csv_path}: candidate translation rows must all target 'eng'")
    summary = _load_json(summary_path)
    _validate_translation_summary(parsed, summary, summary_path)
    english = [row for row in parsed if row["target_language"] == "eng"]
    if not english:
        raise ValueError(f"{csv_path}: no target_language 'eng' rows")
    _unique(english, f"{label} English targets")
    return parsed, english, summary


def _translation_summary_group(value: Any, field: str, location: str,
                               rows: list[dict[str, Any]]) -> dict[str, Any]:
    group = _object(value, field, location)
    samples = _integer(group.get("samples"), "samples", location)
    if samples != len(rows):
        raise ValueError(f"{location}: samples mismatch: found {samples}, expected {len(rows)}")
    completed = _integer(group.get("completed"), "completed", location)
    expected_completed = sum(row["status"] == "complete" for row in rows)
    if completed != expected_completed:
        raise ValueError(f"{location}: completed count mismatch")
    metrics = _object(group.get("metrics"), "metrics", location)
    for name in ("bleu", "chrfpp", "ter"):
        metric = _object(metrics.get(name), f"metrics.{name}", location)
        _number(metric.get("score"), f"metrics.{name}.score", location, nonnegative=True)
    _optional_number(group.get("translation_seconds_median"),
                     "translation_seconds_median", location)
    return group


def _validate_translation_summary(rows: list[dict[str, Any]], summary: dict[str, Any],
                                  path: Path) -> None:
    samples = _integer(summary.get("samples"), "samples", str(path))
    if samples != len(rows):
        raise ValueError(f"{path}: samples mismatch: found {samples}, expected {len(rows)}")
    by_target = _object(summary.get("by_target"), "by_target", str(path))
    english = [row for row in rows if row["target_language"] == "eng"]
    if "eng" not in by_target:
        raise ValueError(f"{path}: by_target.eng is required")
    _translation_summary_group(
        by_target["eng"], "eng", f"{path}:by_target.eng", english)
    by_pair = _object(summary.get("by_pair"), "by_pair", str(path))
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in english:
        grouped[f"{row['source_language']}->eng"].append(row)
    for pair, pair_rows in sorted(grouped.items()):
        if pair not in by_pair:
            raise ValueError(f"{path}: by_pair.{pair} is required")
        _translation_summary_group(
            by_pair[pair], pair, f"{path}:by_pair.{pair}", pair_rows)


def _match_ids(baseline: dict[str, dict[str, Any]], candidate: dict[str, dict[str, Any]],
               label: str) -> None:
    missing = sorted(set(baseline) - set(candidate))
    extra = sorted(set(candidate) - set(baseline))
    if missing or extra:
        details = []
        if missing:
            details.append("missing candidate IDs: " + ", ".join(missing))
        if extra:
            details.append("extra candidate IDs: " + ", ".join(extra))
        raise ValueError(f"{label}: sample ID sets differ ({'; '.join(details)})")


def _pair_asr(baseline_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]
             ) -> list[dict[str, Any]]:
    baseline = _unique(baseline_rows, "baseline ASR")
    candidate = _unique(candidate_rows, "candidate ASR")
    _match_ids(baseline, candidate, "ASR")
    paired = []
    for sample_id in baseline:
        left, right = baseline[sample_id], candidate[sample_id]
        for field in ("language", "reference", "normalized_reference"):
            if left[field] != right[field]:
                raise ValueError(f"ASR sample {sample_id!r}: {field} mismatch")
        if left["reference_words"] != right["reference_words"]:
            raise ValueError(f"ASR sample {sample_id!r}: reference_words mismatch")
        if abs(left["audio_seconds"] - right["audio_seconds"]) > 1e-6:
            raise ValueError(f"ASR sample {sample_id!r}: audio_seconds mismatch")
        delta_errors = right["word_errors"] - left["word_errors"]
        outcome = "better" if delta_errors < 0 else "worse" if delta_errors > 0 else "tie"
        paired.append({
            "sample_id": sample_id,
            "language": left["language"],
            "reference": left["reference"],
            "baseline_hypothesis": left["hypothesis"],
            "candidate_hypothesis": right["hypothesis"],
            "baseline_word_errors": left["word_errors"],
            "candidate_word_errors": right["word_errors"],
            "delta_word_errors": delta_errors,
            "baseline_wer": left["wer"],
            "candidate_wer": right["wer"],
            "delta_wer_pp": 100 * (right["wer"] - left["wer"]),
            "baseline_cer": left["cer"],
            "candidate_cer": right["cer"],
            "baseline_asr_seconds": left["asr_seconds"],
            "candidate_asr_seconds": right["asr_seconds"],
            "candidate_outcome": outcome,
            "_baseline_status": left["status"],
            "_candidate_status": right["status"],
            "_reference_words": left["reference_words"],
        })
    return sorted(paired, key=lambda row: (row["language"], row["sample_id"]))


def _validate_paired_asr_aggregates(rows: list[dict[str, Any]],
                                    baseline_summary: dict[str, Any],
                                    candidate_summary: dict[str, Any]) -> None:
    reference_words = sum(row["_reference_words"] for row in rows)
    for side, summary in (
            ("baseline", baseline_summary), ("candidate", candidate_summary)):
        errors = sum(row[f"{side}_word_errors"] for row in rows)
        paired_wer = errors / reference_words
        supplied_wer = _number(
            summary["aggregate"]["wer"], "aggregate.wer", f"{side} ASR summary",
            nonnegative=True)
        _close(supplied_wer, paired_wer, "aggregate.wer", f"{side} paired ASR")


def _pair_translation(baseline_rows: list[dict[str, Any]],
                      candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    baseline = _unique(baseline_rows, "baseline English translation")
    candidate = _unique(candidate_rows, "candidate English translation")
    _match_ids(baseline, candidate, "translation")
    paired = []
    for sample_id in baseline:
        left, right = baseline[sample_id], candidate[sample_id]
        if left["target_language"] != "eng" or right["target_language"] != "eng":
            raise ValueError(f"translation sample {sample_id!r}: target_language must be 'eng'")
        for field in ("source_language", "translation_reference", "scoring_reference"):
            if left[field] != right[field]:
                raise ValueError(f"translation sample {sample_id!r}: {field} mismatch")
        delta = right["chrfpp"] - left["chrfpp"]
        if delta > OUTCOME_TOLERANCE:
            outcome = "better"
        elif delta < -OUTCOME_TOLERANCE:
            outcome = "worse"
        else:
            outcome = "tie"
        paired.append({
            "sample_id": sample_id,
            "source_language": left["source_language"],
            "target_language": "eng",
            "reference": left["translation_reference"],
            "baseline_hypothesis": left["hypothesis"],
            "candidate_hypothesis": right["hypothesis"],
            "baseline_chrfpp": left["chrfpp"],
            "candidate_chrfpp": right["chrfpp"],
            "delta_chrfpp": delta,
            "candidate_outcome": outcome,
            "_baseline_status": left["status"],
            "_candidate_status": right["status"],
        })
    return sorted(paired, key=lambda row: (row["source_language"], row["sample_id"]))


def _outcomes(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(row["candidate_outcome"] for row in rows)
    return {name: counts[name] for name in ("better", "tie", "worse")}


def _statuses(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    return {
        side: {
            "complete": sum(row[f"_{side}_status"] == "complete" for row in rows),
            "error": sum(row[f"_{side}_status"] == "error" for row in rows),
        }
        for side in ("baseline", "candidate")
    }


def _asr_metrics(group: dict[str, Any]) -> dict[str, float]:
    return {
        "wer": _number(group["wer"], "wer", "ASR summary", nonnegative=True),
        "cer": _number(group["cer"], "cer", "ASR summary", nonnegative=True),
    }


def _translation_metrics(group: dict[str, Any]) -> dict[str, float]:
    return {
        name: _number(group["metrics"][name]["score"], name, "translation summary",
                      nonnegative=True)
        for name in ("bleu", "chrfpp", "ter")
    }


def _metric_comparison(baseline: dict[str, float], candidate: dict[str, float],
                       multiplier: float = 1.0) -> dict[str, Any]:
    return {
        "baseline": baseline,
        "candidate": candidate,
        "difference_points": {
            key: multiplier * (candidate[key] - baseline[key]) for key in baseline
        },
    }


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_metadata(directories: dict[str, Path]) -> dict[str, Any]:
    return {
        label: {
            "directory_basename": directory.name,
            "files": {
                filename: {"sha256": _hash(directory / filename)}
                for filename in ("summary.json", "per-sample.csv")
            },
        }
        for label, directory in directories.items()
    }


def _build_comparison(directories: dict[str, Path], asr_rows: list[dict[str, Any]],
                      translation_rows: list[dict[str, Any]],
                      baseline_asr: dict[str, Any], candidate_asr: dict[str, Any],
                      baseline_translation: dict[str, Any],
                      candidate_translation: dict[str, Any]) -> dict[str, Any]:
    asr_languages = sorted({row["language"] for row in asr_rows})
    translation_languages = sorted({row["source_language"] for row in translation_rows})
    asr_by_language = {}
    for language in asr_languages:
        rows = [row for row in asr_rows if row["language"] == language]
        metrics = _metric_comparison(
            _asr_metrics(baseline_asr["per_language"][language]),
            _asr_metrics(candidate_asr["per_language"][language]), 100.0)
        asr_by_language[language] = {
            "paired_samples": len(rows), "outcomes": _outcomes(rows),
            "statuses": _statuses(rows), **metrics,
        }
    translation_by_language = {}
    for language in translation_languages:
        rows = [row for row in translation_rows if row["source_language"] == language]
        pair = f"{language}->eng"
        metrics = _metric_comparison(
            _translation_metrics(baseline_translation["by_pair"][pair]),
            _translation_metrics(candidate_translation["by_pair"][pair]))
        translation_by_language[language] = {
            "paired_samples": len(rows), "outcomes": _outcomes(rows),
            "statuses": _statuses(rows), **metrics,
            "timing_median_seconds": {
                "baseline": baseline_translation["by_pair"][pair].get(
                    "translation_seconds_median"),
                "candidate": candidate_translation["by_pair"][pair].get(
                    "translation_seconds_median"),
            },
        }
    asr_overall = _metric_comparison(
        _asr_metrics(baseline_asr["aggregate"]),
        _asr_metrics(candidate_asr["aggregate"]), 100.0)
    translation_overall = _metric_comparison(
        _translation_metrics(baseline_translation["by_target"]["eng"]),
        _translation_metrics(candidate_translation["by_target"]["eng"]))
    return {
        "metadata": {
            "sources": _source_metadata(directories),
            "metric_directions": {
                "wer": "lower is better", "cer": "lower is better",
                "bleu": "higher is better", "chrfpp": "higher is better",
                "ter": "lower is better",
            },
            "pairing": "Exact sample IDs after restricting translation to target eng.",
        },
        "asr": {
            "paired_samples": len(asr_rows), "outcomes": _outcomes(asr_rows),
            "statuses": _statuses(asr_rows),
            **asr_overall,
            "timing_median_seconds": {
                "baseline_asr": baseline_asr["aggregate"].get(
                    "asr_latency_seconds_median"),
                "candidate_asr": candidate_asr["aggregate"].get(
                    "asr_latency_seconds_median"),
            },
            "by_language": asr_by_language,
        },
        "translation": {
            "target_language": "eng", "paired_samples": len(translation_rows),
            "outcomes": _outcomes(translation_rows), "statuses": _statuses(translation_rows),
            **translation_overall,
            "timing_median_seconds": {
                "baseline_translation": baseline_translation["by_target"]["eng"].get(
                    "translation_seconds_median"),
                "candidate_translation": candidate_translation["by_target"]["eng"].get(
                    "translation_seconds_median"),
            },
            "by_source_language": translation_by_language,
        },
    }


def _format_percent(value: float) -> str:
    return f"{100 * value:.2f}%"


def _format_score(value: float) -> str:
    return f"{value:.2f}"


def _format_time(value: Any) -> str:
    return "n/a" if value is None else f"{float(value):.4f}"


def _outcome_cells(outcomes: dict[str, int]) -> str:
    return f"{outcomes['better']}/{outcomes['tie']}/{outcomes['worse']}"


def _render_report(comparison: dict[str, Any]) -> str:
    asr = comparison["asr"]
    translation = comparison["translation"]
    lines = [
        "# Paired speech benchmark comparison", "",
        "All rows are paired by exact sample ID. Candidate outcomes are better/tie/worse; "
        "lower edit errors are better for ASR and higher sentence chrF++ is better for "
        "translation.", "", "## ASR quality", "",
        "| Source | Samples | Baseline WER | Candidate WER | Baseline CER | Candidate CER | Better/tie/worse |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for language, item in asr["by_language"].items():
        lines.append(
            f"| {language} | {item['paired_samples']} | {_format_percent(item['baseline']['wer'])} | "
            f"{_format_percent(item['candidate']['wer'])} | {_format_percent(item['baseline']['cer'])} | "
            f"{_format_percent(item['candidate']['cer'])} | {_outcome_cells(item['outcomes'])} |")
    lines.append(
        f"| **Overall** | **{asr['paired_samples']}** | **{_format_percent(asr['baseline']['wer'])}** | "
        f"**{_format_percent(asr['candidate']['wer'])}** | **{_format_percent(asr['baseline']['cer'])}** | "
        f"**{_format_percent(asr['candidate']['cer'])}** | **{_outcome_cells(asr['outcomes'])}** |")
    lines.extend([
        "", "## Direct-English translation quality", "",
        "| Source | Samples | Baseline chrF++ | Candidate chrF++ | Baseline BLEU | Candidate BLEU | Better/tie/worse |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for language, item in translation["by_source_language"].items():
        lines.append(
            f"| {language} | {item['paired_samples']} | {_format_score(item['baseline']['chrfpp'])} | "
            f"{_format_score(item['candidate']['chrfpp'])} | {_format_score(item['baseline']['bleu'])} | "
            f"{_format_score(item['candidate']['bleu'])} | {_outcome_cells(item['outcomes'])} |")
    lines.append(
        f"| **Pooled English** | **{translation['paired_samples']}** | "
        f"**{_format_score(translation['baseline']['chrfpp'])}** | "
        f"**{_format_score(translation['candidate']['chrfpp'])}** | "
        f"**{_format_score(translation['baseline']['bleu'])}** | "
        f"**{_format_score(translation['candidate']['bleu'])}** | "
        f"**{_outcome_cells(translation['outcomes'])}** |")
    lines.extend([
        "", "## Reported timing medians", "",
        "| Stage | Baseline (s) | Candidate (s) |", "|---|---:|---:|",
        f"| ASR computation | {_format_time(asr['timing_median_seconds']['baseline_asr'])} | "
        f"{_format_time(asr['timing_median_seconds']['candidate_asr'])} |",
        f"| Direct-English translation | {_format_time(translation['timing_median_seconds']['baseline_translation'])} | "
        f"{_format_time(translation['timing_median_seconds']['candidate_translation'])} |",
        "", "These are supplied stage medians only. Runtime depends on hardware and software "
        "configuration, and unlike whole-request timings must not be used for model-speed claims.",
        "", "## Caveats", "",
        "This is a small, non-random corpus, so differences should not be generalized to all "
        "speech or ranked as broad language performance. WER and CER are edit error rates. "
        "chrF++ and BLEU measure reference overlap, not semantic accuracy. Translation compares "
        "only target `eng`; baseline German-target rows are excluded before pairing.", "",
    ])
    return "\n".join(lines)


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: "" if row[field] is None else row[field] for field in fields})


def compare(baseline_asr_dir: Path, candidate_asr_dir: Path,
            baseline_translation_dir: Path, candidate_translation_dir: Path,
            output_dir: Path) -> dict[str, Any]:
    directories = {
        "baseline_asr": baseline_asr_dir,
        "candidate_asr": candidate_asr_dir,
        "baseline_translation": baseline_translation_dir,
        "candidate_translation": candidate_translation_dir,
    }
    baseline_asr_rows, baseline_asr_summary = _load_asr(
        baseline_asr_dir, "baseline ASR")
    candidate_asr_rows, candidate_asr_summary = _load_asr(
        candidate_asr_dir, "candidate ASR")
    _, baseline_translation_rows, baseline_translation_summary = _load_translation(
        baseline_translation_dir, "baseline translation", candidate=False)
    _, candidate_translation_rows, candidate_translation_summary = _load_translation(
        candidate_translation_dir, "candidate translation", candidate=True)
    asr_rows = _pair_asr(baseline_asr_rows, candidate_asr_rows)
    _validate_paired_asr_aggregates(
        asr_rows, baseline_asr_summary, candidate_asr_summary)
    translation_rows = _pair_translation(
        baseline_translation_rows, candidate_translation_rows)
    comparison = _build_comparison(
        directories, asr_rows, translation_rows, baseline_asr_summary,
        candidate_asr_summary, baseline_translation_summary,
        candidate_translation_summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / ASR_OUTPUT, ASR_FIELDS, asr_rows)
    _write_csv(output_dir / TRANSLATION_OUTPUT, TRANSLATION_FIELDS, translation_rows)
    with (output_dir / SUMMARY_OUTPUT).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(comparison, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
    with (output_dir / REPORT_OUTPUT).open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_render_report(comparison))
    return comparison


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-asr-dir", required=True, type=Path)
    parser.add_argument("--candidate-asr-dir", required=True, type=Path)
    parser.add_argument("--baseline-translation-dir", required=True, type=Path)
    parser.add_argument("--candidate-translation-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        comparison = compare(
            args.baseline_asr_dir, args.candidate_asr_dir,
            args.baseline_translation_dir, args.candidate_translation_dir,
            args.output_dir)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "asr_paired_samples": comparison["asr"]["paired_samples"],
        "translation_paired_samples": comparison["translation"]["paired_samples"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
