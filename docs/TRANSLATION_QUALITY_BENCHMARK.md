# SeamlessM4T translation quality

Evaluated on 9 November 2026 using the 240 translations already recorded during the [GPU transcription benchmark](GPU_TRANSCRIPTION_BENCHMARK.md). This evaluation ran on the local computer's CPU. No new speech inference, GPU access, or server changes were needed.

The saved outputs contain useful translations, but the diagnostic text review also finds **material meaning errors, omitted information and mistranslated terms**. Good source transcription does not guarantee a faithful translation. These results establish a reproducible baseline for the planned Whisper large-v3 comparison; they do not establish a percentage of semantically correct translations.

## Results

All **240 outputs have a target-language reference**, and none are empty. There are 220 translations from eleven languages into English and 20 from English into German. These directions are reported separately because the target languages differ.

| Target group | Recordings | chrF++ ↑ | BLEU ↑ | TER ↓ |
|---|---:|---:|---:|---:|
| Eleven languages → English | 220 | **57.95** | **31.80** | **56.09** |
| English → German | 20 | **58.43** | **33.64** | **53.17** |

Higher chrF++ and BLEU indicate greater reference overlap; lower TER indicates fewer edits to the reference. **None of these numbers is a semantic accuracy percentage.** Valid paraphrases can score poorly, and a critical local error can remain inside a high-scoring sentence. The measures and their reproducible signatures are provided by [SacreBLEU](https://github.com/mjpost/sacrebleu).

| Direction | Recordings | chrF++ ↑ | BLEU ↑ | TER ↓ |
|---|---:|---:|---:|---:|
| Arabic → English | 20 | 59.36 | 33.80 | 52.55 |
| German → English | 20 | 62.34 | 38.67 | 48.11 |
| English → German | 20 | 58.43 | 33.64 | 53.17 |
| Spanish → English | 20 | 53.25 | 25.56 | 63.72 |
| Persian → English | 20 | 55.61 | 29.53 | 54.16 |
| French → English | 20 | 59.94 | 31.85 | 56.13 |
| Italian → English | 20 | 52.93 | 23.23 | 70.77 |
| Polish → English | 20 | 48.11 | 22.30 | 66.40 |
| Romanian → English | 20 | 67.57 | 42.43 | 42.64 |
| Russian → English | 20 | 60.75 | 35.48 | 53.24 |
| Turkish → English | 20 | 56.19 | 30.09 | 55.87 |
| Ukrainian → English | 20 | 61.20 | 34.34 | 54.06 |

Each row is a corpus-level score, not an average of sentence scores. The small, non-random sets contain different sentence selections, so the table is not a robust ranking of language support. The JSON also retains a mixed-target aggregate for completeness; it is not the primary comparison result.

## What the text review found

A diagnostic review examined **48 text pairs**: the first two recordings in each language plus the two lowest sentence-level chrF++ results among that language's remaining recordings. This deliberately over-samples difficult cases. A separate AI worker annotated them and the lead checked the text pairs and findings. This is an AI-assisted text review, **not a human bilingual audit or an audio listening test**. Its categories must not be extrapolated into a quality rate for all 240 recordings.

Examples checked against the stored source and target texts:

| Sample | Observation | Interpretation |
|---|---|---|
| `de_de/10009182821551087671.wav` | German `war ihm nicht gewachsen`; output `hadn't grown on him` | The source idiom was transcribed correctly, but its meaning was lost in translation. |
| `fa_ir/10393579599779364314.wav` | Reference describes ironing clothes and borrowing an iron/ironing board; output says `Wetting wet clothes` and `a towel and a towel table` | Substantive mistranslation of the action and objects. |
| `tr_tr/10553789323222308394.wav` | Source and reference include a final statement that Mendoza was shot; output omits that statement entirely | Whole-statement omission. |
| `ar_eg/10035416633083120372.wav` | Departure times `06:30` and `07:30` become `between 6 and 7`; place names also change | Lost timing precision and corrupted names. |
| `en_us/10052240106321793346.wav` | The German pronoun `Sie` becomes `sagen für Sie` in the German output | A local meaning error despite sentence chrF++ of 71.19. |
| `uk_ua/10108055665962923730.wav` | Plants producing oxygen and absorbing exhaled carbon dioxide are described with different wording | Meaning is preserved despite sentence chrF++ of only 32.42. |
| `it_it/10011138801715101183.wav` | 15 metres, August 2011 and March 2017 are written out as words | The numeric information is retained; lexical overlap understates that agreement. |

Named entities and technical terms also fail in some examples, including the German `Chhappan Bhog Bhajan` phrase and Polish skiing terminology. Elsewhere the model produces sensible paraphrases. A low text-overlap score alone cannot distinguish these situations.

**Reference mismatch matters.** For `fr_fr/10043298898524273336.wav`, the French source itself says `incendie malveillant`, and the output follows it with `malicious fire`; the English reference instead says `hostile fire`. For `uk_ua/10479653954828478799.wav`, the English reference describes Martelly swearing in a council, while the Ukrainian source and output describe him taking an oath in it. Such disagreements should not automatically be attributed to the model. The published scores retain the original references without selectively correcting difficult examples.

The [48 annotated reviews](benchmarks/seamless-translation-2026-11-09/qualitative-review.json) include evidence and uncertainty notes. The [complete per-recording table](benchmarks/seamless-translation-2026-11-09/per-sample.csv) contains all 240 source transcripts, translation references, outputs and sentence chrF++ scores.

## Scope and interpretation

The installed model performs two separate generation passes from audio features: one for the source-language transcript and one for the target-language text. The displayed ASR output is **not** fed into the translation pass. Therefore, matching errors in both outputs are observations, not proof that an ASR error caused a translation error.

This evaluation measures the existing **direct speech-to-text translation** outputs against one target reference per recording. It does not isolate text-to-text translation quality, assess speech synthesis, or test automatic source-language identification. Source languages were known during the original run. There was no new decoding, tuning, or selective rerunning for this evaluation.

The dataset is the same 240-recording, 12-language [FLEURS](https://huggingface.co/datasets/google/fleurs) test selection, revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`. Target references were joined by the original sentence ID. FLEURS is credited to Conneau et al., Google, 2022, and distributed under CC BY 4.0. The [source record](benchmarks/seamless-translation-2026-11-09/SOURCE.json) describes selection and derived text. The set is read speech, with no claim of representative noisy conversation or specialist-domain coverage.

For the model, hardware, audio conversion, checkpoint revision and measured GPU memory, see the [original benchmark](GPU_TRANSCRIPTION_BENCHMARK.md). Previously recorded translation-pass latency was a median of **0.642 s** for English targets and **0.722 s** for German targets. These are existing inference measurements, not the cost of this offline evaluation. CPU metric calculation took approximately **1.52 s** locally, excluding environment setup and qualitative review.

## Scoring and checks

The evaluator uses **SacreBLEU 2.5.1**. Both sides receive Unicode NFC normalization and whitespace collapse; case, punctuation, digits and spelling differences remain. BLEU uses `13a` tokenization, mixed case, exponential smoothing and corpus effective order disabled. chrF++ uses character order 6, word order 2, beta 2, mixed case and no whitespace characters. TER uses the standard case-insensitive `tercom` settings without additional normalization. See [SacreBLEU's metric documentation](https://github.com/mjpost/sacrebleu) and [chrF implementation](https://github.com/mjpost/sacrebleu/blob/master/sacrebleu/metrics/chrf.py).

Missing references and duplicate sample IDs cause an error rather than silent exclusion. Failed requests would be scored with an empty hypothesis; this run has no failures. Four focused tests passed, covering correct target-reference use, perfect matches, failed outputs, invalid input and normalization boundaries. The exported target groups were also scored through the SacreBLEU command line: **all six target-group metric values matched** the Python API results. This checks grouping and CLI/API consistency within the same library; it is not an independent metric implementation.

Artifacts include [summary and signatures](benchmarks/seamless-translation-2026-11-09/summary.json), [direction-level results](benchmarks/seamless-translation-2026-11-09/per-pair.csv), [validation evidence](benchmarks/seamless-translation-2026-11-09/metric-validation.json), and [dependency versions](benchmarks/seamless-translation-2026-11-09/requirements.lock.txt). The raw translations remain in the [original saved records](benchmarks/seamless-asr-2026-11-09/records.jsonl); input and evaluator SHA-256 hashes are recorded.

## Reproduce without a GPU

From the repository root:

```bash
python3 -m venv runtime/translation-eval-venv
runtime/translation-eval-venv/bin/python -m pip install sacrebleu==2.5.1
runtime/translation-eval-venv/bin/python scripts/evaluate_translation.py \
  --input docs/benchmarks/seamless-asr-2026-11-09/records.jsonl \
  --output-dir /tmp/kienzletranslate-translation-evaluation

runtime/translation-eval-venv/bin/python -m sacrebleu \
  /tmp/kienzletranslate-translation-evaluation/eng.references.txt \
  -i /tmp/kienzletranslate-translation-evaluation/eng.hypotheses.txt \
  -m bleu chrf ter --chrf-word-order 2 --width 12
```

Repeat the last command with `deu` filenames for the German target group. No server credentials or audio files are required for scoring saved texts.

## Follow-up: Whisper large-v3 comparison

**Status: completed on 9 November 2026 after explicit GPU authorization.** See the [Whisper large-v3 comparison](WHISPER_LARGE_V3_COMPARISON.md) for the actual results. The scope below records the predeclared comparison plan.

The authorized comparison used the same full recordings and references:

1. **ASR: all 240 recordings.** Whisper large-v3, known source language, FP16, serial processing. Use the same WER/CER evaluator and unchanged normalization as the Seamless baseline. Preserve complete recordings, including those longer than 30 seconds; record chunking and decoding settings.
2. **Speech translation: 220 non-English recordings → English.** Score the exact same target references with the evaluator above. Whisper's translation task targets English; it cannot directly supply the English → German comparison. That limitation is documented in the [official Whisper usage guide](https://github.com/openai/whisper#command-line-usage). Adding a separate German translation model would be a different system comparison.
3. **Performance:** report transcription and translation times separately, median/P95 latency, model load time, allocated/reserved/total GPU memory, and errors. Use the full large-v3 model, with the runtime version and checkpoint pinned and recorded. Hardware and decoding differences must accompany any speed claim.
4. **Execution:** one complete pass per task, one model resident at a time, no interference with other GPU tests. Compare paired per-recording results; investigate only actual failures or a small set of disagreements. Publish the results in English.

The baseline above is retained unchanged; the separate comparison report documents the measured quality, speed, memory and final restored service state.
