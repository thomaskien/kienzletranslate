# Whisper large-v3 versus SeamlessM4T

Completed on 9 November 2026 after the user released the RTX 3090 for this comparison.

**Whisper large-v3 improved aggregate transcription error rates and ran faster in the tested configuration. SeamlessM4T produced better English-translation reference scores.** The results do not support replacing the current translator wholesale with Whisper. The application remains on SeamlessM4T, and its model was restored to the ready state after the benchmark.

All **240 ASR tasks and 220 English-translation tasks completed without execution errors**. They used exactly the same recordings and PCM16 input bytes as the earlier Seamless run. Whisper was the full large-v3 model, FP16, executed with faster-whisper/CTranslate2; no turbo, distilled or INT8 model was used.

## Main results

| Measurement | SeamlessM4T v2 Large | Whisper large-v3 |
|---|---:|---:|
| ASR WER, 240 recordings ↓ | 8.16% | **7.18%** |
| ASR CER, 240 recordings ↓ | 4.35% | **2.30%** |
| Exact normalized ASR matches | 74 / 240 | **86 / 240** |
| English translation chrF++, 220 recordings ↑ | **57.95** | 53.37 |
| English translation BLEU ↑ | **31.80** | 26.03 |
| English translation TER ↓ | **56.09** | 62.74 |
| ASR computation median | 0.770 s | **0.359 s** |
| English translation computation median | 0.642 s | **0.258 s** |

ASR WER fell by **0.98 percentage points**, from 466 to 410 word edits against 5,709 reference words. CER fell by 2.05 points, from 1,310 to 693 character edits. By recording, Whisper had fewer word edits on **85**, the same number on **93**, and more on **62**.

For translation, Whisper's pooled chrF++ fell by **4.58 points**, BLEU by 5.77 points, and TER increased by 6.65 points. Sentence chrF++ improved on **67** recordings, tied on **3**, and declined on **150**. These are metric comparisons, **not counts of semantically correct or incorrect translations**. Reference overlap can penalize valid paraphrases and miss important local errors.

The ASR comparison covers all twelve source languages. Translation compares only the 220 non-English recordings with English targets. The earlier 20 English → German translations are outside this paired comparison: Whisper's direct translation task targets English. See the [official Whisper usage guide](https://github.com/openai/whisper#command-line-usage).

## Results by source language

There are 20 recordings per language. ASR WER is lower-is-better; English-translation chrF++ is higher-is-better.

| Source | Seamless WER | Whisper WER | Seamless → English chrF++ | Whisper → English chrF++ |
|---|---:|---:|---:|---:|
| Arabic | 13.72% | 14.88% | 59.36 | 51.20 |
| German | 5.47% | 3.64% | 62.34 | 57.93 |
| English | 7.39% | 5.13% | — | — |
| Spanish | 3.36% | 2.05% | 53.25 | 51.14 |
| Persian | 10.63% | 17.84% | 55.61 | 43.98 |
| French | 7.72% | 7.22% | 59.94 | 56.19 |
| Italian | 5.61% | 2.61% | 52.93 | 52.68 |
| Polish | 11.14% | 4.27% | 48.11 | 45.96 |
| Romanian | 7.81% | 9.52% | 67.57 | 59.52 |
| Russian | 8.71% | 6.47% | 60.75 | 54.84 |
| Turkish | 11.25% | 6.39% | 56.19 | 52.89 |
| Ukrainian | 7.24% | 5.68% | 61.20 | 60.81 |

Whisper improved ASR WER in nine of twelve groups. Arabic, Persian and Romanian regressed; Persian is the clearest exception to the aggregate improvement. Character error rates sometimes tell a different story because word segmentation and number formatting affect WER. The normalization preserves digit-versus-spelled-number differences and diacritics for both systems.

Seamless achieved higher corpus chrF++ in all eleven English-translation groups in this test. The [full paired tables](benchmarks/whisper-large-v3-2026-11-09/comparison/comparison.md) also include per-language CER, BLEU and recording-level outcome counts. “Baseline” means Seamless; “candidate” means Whisper.

## Observed meaning differences

The following are diagnostic text comparisons of previously identified difficult cases. They are not a representative human bilingual audit, and no new listening assessment was conducted.

| Sample | Comparison |
|---|---|
| `tr_tr/10553789323222308394.wav` | Whisper restores `Mendoza was shot.`, which Seamless omitted. Its first sentence still differs from the reference. |
| `pl_pl/10577070186203717497.wav` | Seamless produces `the Alpine and the Spinach` and `slopes`; Whisper instead mentions climbing activities and skis, improving key terms. |
| `fa_ir/10130894543333251273.wav` | The reference describes atoms with unstable nuclei. Seamless says unstable atoms; Whisper changes the subject further to `Some animals have an unstable body`. |
| `ar_eg/10035416633083120372.wav` | The reference describes bus departures and times. Seamless retains the topic with errors; Whisper produces an unrelated description of Bumthang as a populous city. |
| `de_de/10009182821551087671.wav` | Both fail the German idiom `war ihm nicht gewachsen`: Seamless says `hadn't grown on him`, Whisper `was not grown to him`. |
| `fa_ir/10393579599779364314.wav` | Both fail the ironing example. Seamless invents a towel/table; Whisper introduces a shower/table instead of the iron and ironing board. |

This mixture matters: better ASR does not automatically mean better direct speech translation. Both models generate target text directly from audio in this comparison; their displayed source transcript is not the input to the translation pass. Existing source/target reference discrepancies, described in the [translation baseline report](TRANSLATION_QUALITY_BENCHMARK.md), also remain relevant. No references were selectively rewritten to favor either model.

The [paired translation file](benchmarks/whisper-large-v3-2026-11-09/comparison/translation-paired.csv) contains every reference and both outputs. The [paired ASR file](benchmarks/whisper-large-v3-2026-11-09/comparison/asr-paired.csv) retains every transcript and edit difference.

## Timing and GPU memory

| Comparable inference stage | Seamless median / P95 | Whisper median / P95 |
|---|---:|---:|
| ASR, 240 recordings | 0.770 / 1.136 s | 0.359 / 0.574 s |
| English translation, 220 recordings | 0.642 / 0.927 s | 0.258 / 0.360 s |

Whisper's measured medians were approximately **2.14× faster for ASR** and **2.49× faster for English translation**. These are comparisons of the tested systems: Seamless uses Transformers/PyTorch, Whisper uses faster-whisper/CTranslate2. They do not isolate intrinsic model speed. Both timers include their inference-stage work, but Whisper's translation call extracts audio features again while Seamless reuses features from the first pass. There is no HTTP or app-level request overhead in the Whisper timings.

Whisper spent 90.13 seconds in ASR calls and 58.46 seconds in translation calls. The complete two-phase loop took **150.09 seconds**. This loop time should not be compared directly with the earlier 372.30-second app benchmark, which additionally included 20 German-target translations, API traffic and polling. Model construction took **1.99 seconds**, measured after model-file checksum reads; the operating-system cache may have been warm. This is not a cold-disk loading claim. Downloading the checkpoint took about 99 seconds separately.

For Whisper, total device memory was sampled with `nvidia-smi` every 100 ms:

- Before loading: **418 MiB**; the unloaded Seamless process retained a small CUDA context.
- After loading: **4,295 MiB**.
- Maximum sampled total device use: **4,697 MiB**, approximately **4.59 GiB**.
- After the Whisper process exited: **418 MiB**, before reloading Seamless.

This measurement includes CUDA reservation and other device use. Framework-level allocated/reserved memory is unavailable from the current CTranslate2 instrumentation and is not reported as a PyTorch-equivalent statistic. Brief peaks between samples could be missed. The earlier Seamless figures—6,193 MiB peak PyTorch allocation and 7,562 MiB total device use afterward—use different measurement definitions and are not a precise like-for-like memory comparison.

The observed Whisper footprint is encouraging for an 8 GB deployment, but **no physical 8 GB card was tested**, and simultaneous residency with Seamless was not tested. The result does not establish that both models fit together on such a card.

## Reproducible setup

| Component | Tested setting |
|---|---|
| GPU / driver | NVIDIA RTX 3090, 24,576 MiB / 580.178.04 |
| CPU | AMD Ryzen 9 5900X |
| Whisper checkpoint | `Systran/faster-whisper-large-v3` |
| Checkpoint revision | `edaa852ec7e145841d8ffdb056a99866b5f0a478` |
| Runtime | faster-whisper 1.2.1, CTranslate2 4.8.5, Python 3.12.3 |
| Compute | CUDA FP16, eight CPU threads, one worker, serial inference |
| Decoding | `beam_size=1`, `best_of=1`, `temperature=0.0` |
| Context / filtering | `condition_on_previous_text=false`, no initial prompt, `vad_filter=false` |
| Segmentation | Full audio, 30-second windows, `without_timestamps=true` |
| Length limit | Model maximum 448 tokens; longest returned segment had 142 tokens |
| Source language | Known dataset label in both systems |

The [Systran checkpoint card](https://huggingface.co/Systran/faster-whisper-large-v3) identifies this as the FP16 CTranslate2 conversion of `openai/whisper-large-v3`. The implementation and GPU library requirements are documented by [faster-whisper](https://github.com/SYSTRAN/faster-whisper). Existing cuBLAS 12.4.5.8, cuDNN 9.1.0.70 and CUDA runtime 12.4.127 libraries were reused without changing production packages.

The baseline used SeamlessM4T v2 Large, revision `5f8cc790b19fc3f67a61c105133b20b34e3dcb76`, Transformers 4.46.3 and PyTorch 2.6.0+cu124, FP16, `num_beams=1`, `max_new_tokens=256`. This comparison deliberately uses **single-beam decoding for both models**. It is a measured greedy-decoding baseline, not a tuned best-quality comparison or the default five-beam faster-whisper profile. No additional beam search or temperature-fallback sweep was run after seeing the results.

The same FLEURS revision, sample selection, references and scoring normalization were retained. All original WAV and transmitted PCM16 SHA-256 values match the baseline. Both recordings longer than 30 seconds were processed through their final windows, ending at 43.38 and 46.50 seconds respectively. The corpus contains 51 minutes 42 seconds of audio; its non-English translation subset contains 48 minutes 3 seconds. FLEURS attribution and CC BY 4.0 terms are recorded in [SOURCE.json](benchmarks/whisper-large-v3-2026-11-09/SOURCE.json).

## Validation and artifacts

There was one full GPU pass for each task, with no selected reruns. Six focused comparison tests passed. The comparison tool rejects mismatched IDs, references, language groups and inconsistent aggregate counts. All **720 ASR metric values** matched an independent JiWER calculation; the **three pooled translation metrics** matched the SacreBLEU command line using the same library. Original and PCM16 checksums and full input duration were checked for all 460 task records.

- [Model, decoder and file-hash metadata](benchmarks/whisper-large-v3-2026-11-09/metadata.json)
- [Raw ASR records](benchmarks/whisper-large-v3-2026-11-09/asr-records.jsonl) and [raw translation records](benchmarks/whisper-large-v3-2026-11-09/translation-records.jsonl)
- [ASR metrics](benchmarks/whisper-large-v3-2026-11-09/asr/summary.json), [translation metrics](benchmarks/whisper-large-v3-2026-11-09/translation/summary.json), and [paired comparison](benchmarks/whisper-large-v3-2026-11-09/comparison/comparison.json)
- [Input validation](benchmarks/whisper-large-v3-2026-11-09/input-validation.json), [JiWER validation](benchmarks/whisper-large-v3-2026-11-09/asr-metric-validation.json), and [translation CLI validation](benchmarks/whisper-large-v3-2026-11-09/translation/metric-validation.json)
- [Timing and memory summary](benchmarks/whisper-large-v3-2026-11-09/finished.json), [sampled device memory](benchmarks/whisper-large-v3-2026-11-09/gpu-memory-samples.json), and [Seamless restoration record](benchmarks/whisper-large-v3-2026-11-09/lifecycle.json)
- [Inference environment](benchmarks/whisper-large-v3-2026-11-09/requirements.lock.txt), [evaluation environment](benchmarks/whisper-large-v3-2026-11-09/evaluation-requirements.lock.txt), and [CUDA libraries](benchmarks/whisper-large-v3-2026-11-09/cuda-libraries.json)

Re-score the public records without a GPU, from the repository root:

```bash
python3 scripts/evaluate_asr.py \
  --input docs/benchmarks/whisper-large-v3-2026-11-09/asr-records.jsonl \
  --output-dir /tmp/whisper-asr --title 'Whisper large-v3 ASR'
runtime/translation-eval-venv/bin/python scripts/evaluate_translation.py \
  --input docs/benchmarks/whisper-large-v3-2026-11-09/translation-records.jsonl \
  --output-dir /tmp/whisper-translation --title 'Whisper large-v3 translation'
python3 scripts/compare_speech_benchmarks.py \
  --baseline-asr-dir docs/benchmarks/seamless-asr-2026-11-09 \
  --candidate-asr-dir /tmp/whisper-asr \
  --baseline-translation-dir docs/benchmarks/seamless-translation-2026-11-09 \
  --candidate-translation-dir /tmp/whisper-translation \
  --output-dir /tmp/whisper-comparison
```

The translation evaluator requires the existing separate environment with `sacrebleu==2.5.1`. The GPU runner is [benchmark_whisper_gpu.py](../scripts/benchmark_whisper_gpu.py); its inputs are the original prepared manifest, saved baseline records, pinned local model directory, a new output directory and the explicit run date. A future GPU rerun requires available hardware and an authorized lifecycle transition; the current run has finished and Seamless is ready again.

These findings apply to the selected 20 recordings per source language. They do not establish statistical significance or broad performance on spontaneous/noisy conversation. The concrete result for the current project is to retain Seamless for translation and treat Whisper as a separately evaluated ASR option, especially where its language-specific results help.
