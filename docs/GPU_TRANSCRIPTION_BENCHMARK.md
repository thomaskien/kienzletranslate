# SeamlessM4T GPU transcription benchmark

Measured on 9 November 2026 using the installed kienzletranslate service on `10.0.83.140`.

All **240 recordings across 12 languages** completed successfully. The corpus contains **51 minutes 42 seconds of audio**. Overall normalized word error rate (WER) was **8.16%** and character error rate (CER) was **4.35%**. Median transcription computation took **0.77 seconds per recording** on the RTX 3090.

These results support further practical testing of the current transcription pipeline. They do not establish reliability for spontaneous conversations, noisy iPad recordings, specialist terminology, or every supported language.

## Results by language

Each language has 20 recordings. Lower error rates are better. WER counts word substitutions, deletions and insertions relative to the reference word count; it should not be presented as “100% minus recognition accuracy.” CER counts non-whitespace character edits.

| Language | WER | CER | Median ASR time |
|---|---:|---:|---:|
| Arabic | 13.72% | 4.85% | 0.749 s |
| English | 7.39% | 4.71% | 0.690 s |
| French | 7.72% | 3.69% | 0.806 s |
| German | 5.47% | 4.27% | 0.773 s |
| Italian | 5.61% | 3.68% | 0.825 s |
| Persian | 10.63% | 4.21% | 0.754 s |
| Polish | 11.14% | 7.33% | 0.823 s |
| Romanian | 7.81% | 4.79% | 0.886 s |
| Russian | 8.71% | 3.42% | 0.763 s |
| Spanish | 3.36% | 2.17% | 0.727 s |
| Turkish | 11.25% | 4.13% | 0.751 s |
| Ukrainian | 7.24% | 5.20% | 0.793 s |
| **All recordings, weighted by reference length** | **8.16%** | **4.35%** | **0.770 s** |

The overall WER represents **466 edits across 5,709 reference words**: 331 substitutions, 47 deletions and 88 insertions. CER represents 1,310 edits across 30,111 reference characters. **74 of 240 transcripts matched exactly after normalization.** The unweighted average of the twelve language WERs is 8.34%. This small, non-random selection is not a reliable ranking of the languages.

## What the errors show

Formatting and lexical errors both occur. The primary metric ignores case and punctuation but deliberately retains differences between digits and spelled-out numbers. For example, the German reference contains `403`, while the output contains `vierhundertdrei`. The Polish sample with the highest WER spells out a year and a page number that appear as digits in the reference. Such cases inflate text error counts without necessarily changing the spoken meaning.

There are also substantive recognition errors. In German, `Chhappan Bhog Bhajan` became `Japan-Bog Bayern`, and `Scotturb-Bus` became `Scotabus`. Proper names and unfamiliar terms deserve particular attention in practical testing. No human semantic rating or listening audit was performed for all languages.

Arabic results are sensitive to written vowel marks retained by the primary metric. In one example, the reference contains many such marks and the output largely omits them. As a separate diagnostic, removing U+064B–U+0652 and U+0670 symmetrically from the normalized Arabic texts reduces Arabic WER from **13.72% to 6.51% (28/430 word edits)**. This diagnostic does **not** replace the primary score or establish semantic correctness. Persian word spacing also affects WER; CER provides a complementary view.

Strict WER, preserving case and punctuation, is **19.77% overall**. Its difference from normalized WER illustrates why the normalization policy must accompany the results. Examples and full reference/output pairs are available in the [generated report](benchmarks/seamless-asr-2026-11-09/report.md) and [per-recording results](benchmarks/seamless-asr-2026-11-09/per-sample.csv).

## Timing and GPU memory

| Measurement | Result |
|---|---:|
| Full recording lengths | 8.10–46.50 s |
| ASR computation, median / P95 | 0.770 / 1.136 s |
| Complete API request, median / P95 | 1.474 / 2.056 s |
| Summed ASR computation | 195.041 s |
| ASR real-time factor | 0.0629, approximately 15.9× real time |
| Complete sequential benchmark | 372.30 s, approximately 6 min 12 s |
| Maximum reported PyTorch allocated GPU memory | 6,193 MiB, approximately 6.05 GiB |
| Total GPU memory in use before / after the run | 5,234 / 7,562 MiB |
| Completed / failed requests | 240 / 0 |

The model was already resident. ASR timing includes audio feature preparation and the original-language text generation pass; it excludes model loading, recording time and CPU language identification. Each ordinary service request also generated a translation: English for non-English input, German for English input. Complete request timing includes that second pass and result polling. Speech synthesis was disabled. Only the original-language transcript is scored here.

**An 8 GB GPU has not been validated by this test.** The 6.05 GiB figure measures PyTorch allocations across both text passes, whereas total GPU use after the run was about **7.38 GiB**, including allocator reservation, CUDA and other GPU use. The post-run observation is not a continuous measurement of the total peak. Speech synthesis, other services and different audio lengths may require additional memory. CPU language identification still avoids adding another GPU model, but successful operation on an actual 8 GB card requires its own compact test.

The benchmark used one isolated session and the existing serial service. It did not load a second model or restart the application. The benchmark session was deleted afterward; the service reported `ready`, `busy=false`, and an empty queue.

## Dataset and protocol

The corpus is a local selection from the public [Google FLEURS dataset](https://huggingface.co/datasets/google/fleurs), revision `70bb2e84b976b7e960aa89f1c648e09c59f894dd`. FLEURS supplies audio and reference transcriptions under **CC BY 4.0**. Attribution: *FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech*, Conneau et al., Google, 2022. See the [source and modification record](benchmarks/seamless-asr-2026-11-09/SOURCE.json).

For each of `ar_eg`, `de_de`, `en_us`, `es_419`, `fa_ir`, `fr_fr`, `it_it`, `pl_pl`, `ro_ro`, `ru_ru`, `tr_tr`, and `uk_ua`, the corpus contains the first 20 eligible test archive members with distinct sentence IDs and at least eight seconds of audio. This is **all 240 recordings in the prepared library**, not just the smaller subset previously used for CPU language identification.

Every full original recording was tested, without VAD trimming or removal of pauses. Original mono 16 kHz floating-point WAV audio was clipped to the PCM range and converted in memory to PCM16 WAV for the existing API. Original and transmitted audio SHA-256 hashes are retained in [records.jsonl](benchmarks/seamless-asr-2026-11-09/records.jsonl).

The source language was supplied from the dataset label. This measures **transcription with a known source language**, not automatic language-identification quality. Translation outputs are retained for possible subsequent evaluation but are not scored by this report. The findings therefore do not measure combined language identification, transcription and translation accuracy.

## Model and runtime

| Component | Setting |
|---|---|
| GPU | NVIDIA GeForce RTX 3090, 24,576 MiB |
| Driver | 580.178.04 |
| CPU | AMD Ryzen 9 5900X |
| Application version reported by server | 1.5.0 |
| Model | `facebook/seamless-m4t-v2-large` |
| Checkpoint revision | `5f8cc790b19fc3f67a61c105133b20b34e3dcb76` |
| Inference precision | FP16 on CUDA |
| Generation | `num_beams=1`, `max_new_tokens=256`, `generate_speech=false` |
| Production runtime | Python 3.12.3, PyTorch 2.6.0+cu124, Transformers 4.46.3 |

The benchmark did not change the app version or production dependencies. Its audio-conversion and independent metric-validation packages are installed in `/opt/kienzletranslate-bench/venv`. [Benchmark dependency versions](benchmarks/seamless-asr-2026-11-09/requirements.lock.txt), [inference runtime versions](benchmarks/seamless-asr-2026-11-09/inference-environment.json), and backend source hashes in [summary.json](benchmarks/seamless-asr-2026-11-09/summary.json) record the tested setup.

## Scoring and validation

Primary scoring applies the same normalization to the original FLEURS reference and the model output:

1. Unicode NFKC and lower case, with Turkish dotted/dotless-I handling.
2. Remove apostrophes; turn other Unicode punctuation and symbols into spaces.
3. Convert Persian zero-width non-joiners to spaces and remove other format controls.
4. Collapse whitespace; preserve accents, vowel marks, letter variants, and digit/spelled-number differences.

WER uses whitespace-separated words. CER excludes whitespace. Corpus scores sum edits and reference units before division. Strict WER only normalizes Unicode NFC and whitespace. These are project metrics; they must not be compared directly with published benchmark numbers using different normalization. The evaluator counts failed requests as empty transcripts, although none failed in this run.

Nine focused evaluator tests passed. An independent [JiWER](https://github.com/jitsi/jiwer) 4.0.0 calculation matched **all 720 checks**: normalized WER, normalized CER and strict WER for each of the 240 recordings. This validates edit-distance calculations on the same texts, not the choice of normalization or the correctness of dataset references. The [validation record](benchmarks/seamless-asr-2026-11-09/metric-validation.json) includes input and validator hashes. There was one complete GPU inference pass; no tuning or selective rerunning was used to improve the reported scores.

## Reproduce the evaluation

From the repository root, the published records can be scored with standard Python, without a model or GPU:

```bash
python3 scripts/evaluate_asr.py \
  --input docs/benchmarks/seamless-asr-2026-11-09/records.jsonl \
  --output-dir /tmp/seamless-asr-evaluation \
  --title 'SeamlessM4T GPU transcription benchmark — 2026-11-09'
```

For the independent cross-check, use a separate environment containing `jiwer==4.0.0`:

```bash
python scripts/validate_asr_metrics.py \
  --input /tmp/seamless-asr-evaluation/per-sample.csv \
  --output /tmp/seamless-asr-evaluation/metric-validation.json
```

The measured inference run used the already loaded service and the full prepared manifest:

```bash
OPENBLAS_NUM_THREADS=1 /opt/kienzletranslate-bench/venv/bin/python \
  /opt/kienzletranslate-bench/benchmark_seamless_asr.py \
  --manifest /var/lib/kienzletranslate-bench/fleurs-12/manifest.jsonl \
  --output /var/lib/kienzletranslate-bench/results/seamless-asr-2026-11-09/records.jsonl
```

The runner reads the local backend token from `/etc/kienzletranslate/config.json` without exporting it. A rerun requires a new output filename. Its checkpoint and generation metadata describe this pinned setup and must be updated if the model configuration changes. The prepared corpus can be recreated with `scripts/prepare_lid_corpus.py`; audio remains outside Git. All published reference text is attributed to FLEURS; model transcriptions, normalized derivatives and edit alignments are explicitly identified in the data files.
