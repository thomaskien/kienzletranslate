# Automatic language identification: evidence and development handoff

Status on 9 November 2026: **integrated in v1.6 as a single optional patient-side attempt.**
The Automatic tile spans four flag columns under the common-language heading. The next
patient-side push-to-talk recording is examined once after release. Success fixes the
language and translates the original complete recording; uncertainty, short/no speech,
unsupported language or a detector failure restores manual flags without Automatic.
Only operator refresh restores the offer. Your language and microphone permission persist.

The CPU worker uses the measured 3/5/8-second prefix policy, plus production VAD gating:
at least half of each inspected prefix must contain speech. This extra gate was not part
of the original benchmark and can increase abstention. Explicit code mappings live in
`backend/lid.py`; unsupported or ambiguous labels (including a generic Kurdish label)
are rejected, not coerced into a supported dialect. Manual selection retains all 96 languages.
Whisper base runs in its own CPU-only environment/process. Seamless runs in a separate
GPU child process that exits on idle to release its CUDA context. See
[installation settings](INSTALLATION.md) and [release checks](VERIFICATION.md).

The sections below preserve the original research findings and pre-integration design notes;
where they describe unresolved choices, the v1.6 behavior above now takes precedence.

## Evidence-based starting point

Use **multilingual Whisper base on the CPU** as the candidate language detector, while keeping SeamlessM4T on the GPU for translation. The current Seamless integration requires an explicit source language for the original transcript and does not return a separately validated language-identification result. No reliable Seamless-only language-identification path has been demonstrated by these experiments.

Whisper base was more accurate than tiny in the measured short-audio comparison. The later large-v3 GPU comparison tested transcription and translation **with known source languages**. It provides no evidence that large-v3 is a better language detector and does not replace the CPU language-identification results.

| Experiment | What it establishes | Evidence |
|---|---|---|
| CPU tiny/base, 120 recordings × 5 prefix lengths per model | Detection accuracy and elapsed computation versus available audio | [Original CPU report](CPU_LANGUAGE_IDENTIFICATION.md), [tiny results](benchmarks/lid-cpu-2026-11-09/tiny.summary.json), [base results](benchmarks/lid-cpu-2026-11-09/base.summary.json) |
| CPU base, 60 additional recordings | Follow-up of the revised conservative decision rule | [Holdout results](benchmarks/lid-cpu-2026-11-09/base-holdout.summary.json) |
| Seamless, 240 full recordings | Transcription quality with supplied languages | [GPU transcription report](GPU_TRANSCRIPTION_BENCHMARK.md) |
| Saved Seamless translations | Translation-reference scores and diagnostic meaning errors | [Translation report](TRANSLATION_QUALITY_BENCHMARK.md) |
| Full Whisper large-v3 GPU comparison | Faster aggregate ASR, but lower English-translation scores in the tested configuration | [Paired comparison](WHISPER_LARGE_V3_COMPARISON.md) |

## Measured detector performance

The initial comparison used ten recordings per source language, twelve languages, with the same inputs for tiny and base. Detection was not restricted to those twelve languages. Durations are elapsed audio **after a precomputed speech onset**, including internal pauses; they are not five or eight seconds of concatenated speech-only frames.

| Prefix duration | tiny top-1 correct | base top-1 correct | base elapsed median, initial configuration |
|---|---:|---:|---:|
| 1 s | 39.2% | 51.7% | 224 ms |
| 2 s | 71.7% | 78.3% | 229 ms |
| 3 s | 83.3% | 87.5% | 268 ms |
| 5 s | 90.0% | 96.7% | 278 ms |
| 8 s | 93.3% | 97.5% | 279 ms |

These top-1 figures include uncertain predictions. An initial rule that also allowed decisions at two seconds accepted a wrong Ukrainian → Russian prediction even with base. Tiny accepted four wrong predictions. This is why the revised rule does not accept before five seconds.

The revised rule was checked once on **60 different recordings**, five per language:

- **53 accepted correctly, 0 accepted incorrectly, 7 left undecided**: 88.3% coverage in this sample.
- 46 accepted at five seconds, seven at eight seconds; the remaining seven require fallback.
- Undecided cases: four Ukrainian, two Romanian and one Arabic recording.
- One five-second-prefix call: **0.209 s median / 0.219 s P95** elapsed time.
- Cumulative detection work until acceptance or abstention: **0.422 s median / 0.641 s P95**.
- No extra GPU memory; peak benchmark-process RAM about **345 MiB**, including cached recordings.

The follow-up limited math-library threads, unlike the initial comparison, so the timing improvement is not a pure difference in audio length. Measurements were made on the server's Ryzen 9 5900X with eight CTranslate2 CPU threads. “0.422 s” is elapsed wall time, not the sum of CPU time across all threads. The model was already resident during detection; its local-cache load took about 0.225 s separately.

Zero wrong acceptances among 53 accepted cases is **not a guarantee of safe identification**. The two overlapping prefixes are correlated observations. Model scores are not calibrated correctness probabilities.

## Exact tested decision rule

Evaluate prefixes at **3, 5, then 8 seconds**, stopping once accepted:

1. Rank the detector's full language-score distribution. Record the top language, its raw score, and the runner-up score.
2. A checkpoint qualifies only if the top score is **at least 0.8** and its margin over the runner-up is **at least 0.2**.
3. Accept at five seconds only if the three- and five-second checkpoints both qualify and predict the same language.
4. Otherwise, accept at eight seconds only if the five- and eight-second checkpoints both qualify and predict the same language.
5. Otherwise abstain. Do not force the top label into the app or relax thresholds automatically.

The tested implementation is [`policy_decision`](../scripts/benchmark_lid_cpu.py). A confident eight-second result alone does not satisfy this two-checkpoint rule. The threshold policy is a candidate for integration, not a universal optimum.

For a completed five-second utterance, the two prefix calls can run after release of the push-to-talk area: approximately five seconds of recorded audio plus 0.42 seconds of detection work, **plus transport and VAD**, followed by translation. A third call adds more computation; “under half a second” does not describe every decision or the whole translation request. No streaming implementation or timing overlap with ongoing recording was tested.

## Audio preparation and resource isolation

The benchmark used CPU Silero VAD to annotate speech onset, with 250 ms minimum speech, 300 ms minimum silence and no padding. Original audio files were retained. Internal pauses were not removed. Offline VAD over full recordings took roughly 13 ms median after the first call; this is not a streaming-VAD measurement and was excluded from detector timing.

Silence and low-level synthetic noise still produced language labels, but their observed scores were below the acceptance threshold. This small control set does not establish rejection of arbitrary music, television, mixed speech or room noise. Production speech gating and short-utterance behavior remain to be checked.

The tested detector setup is:

```text
Model: Systran/faster-whisper-base
Revision: ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66
faster-whisper: 1.2.1
CTranslate2: 4.8.5
Device: cpu
Requested compute type: int8; actual: int8_float32
CPU threads: 8; workers: 1
CUDA_VISIBLE_DEVICES=""
OPENBLAS_NUM_THREADS=1
MKL_NUM_THREADS=1
OMP_NUM_THREADS=8
```

Keep GPU masking and thread settings confined to the detector's own process. **Do not import the benchmark module directly into the production GPU service:** it sets `CUDA_VISIBLE_DEVICES` at import time. Extract the pure policy logic or place detection in a separate CPU worker, keeping the GPU service environment intact. The process boundary and production dependency packaging are implementation work, not existing app behavior.

No physical 8 GB GPU was validated. CPU language identification adds no GPU model, which preserves scarce VRAM. The measured large-v3 GPU footprint does not justify loading it alongside Seamless for language identification on an 8 GB card. Both transcription/translation GPU reports explain their memory measurement limits.

## Proposed integration behavior and unresolved choices

A compact first implementation should preserve manual selection and the existing push-to-talk lifecycle. Detect only from the submitted recording, preserve the complete recording for translation, and treat “insufficient audio,” “uncertain,” and “unsupported language” as explicit outcomes. Manual correction must remain available. An uncertain result must not silently reuse a stale language from another speaker or session.

The following product and integration choices still need to be settled before app implementation:

- Whether automatic detection applies to the opposite speaker only or can be enabled independently on both sides; the exact start-dialog and fallback interaction.
- Whether an accepted language is retained for that speaker/session, when it is reset, and how intentional language changes are handled.
- Behavior for utterances shorter than five seconds or those with very little speech inside a long prefix; do not silently concatenate unrelated turns into the tested prefix policy.
- The permitted automatically detected languages. Only twelve were tested; the app's broader language list is not thereby validated. Keep the full ranking for score/margin computation, then explicitly reject unsupported results instead of forcing the nearest supported language.
- A verified mapping from Whisper language codes to the installed Seamless source/target codes, including ambiguous dialect or regional choices. The twelve benchmark mappings are recorded in [`benchmark_seamless_asr.py`](../scripts/benchmark_seamless_asr.py); broader coverage remains work.
- CPU-worker startup, resident-model lifetime, timeout/cancellation, concurrency limits, session/speaker ownership and stale-result handling. Reuse existing utterance IDs/generation handling rather than allowing late detection to overwrite a newer manual choice.
- Installer/update handling for the optional detector model and dependencies. Benchmark packages currently live separately from production.

These are open implementation decisions; no production integration has been performed.

## Compact integration acceptance checks

After the choices above are settled, reuse the existing policy tests and add only targeted checks: successful acceptance, disagreement/abstention, insufficient speech, unsupported code, manual override, cancellation and session isolation. A short iPhone/iPad check should cover the actual microphone, resulting language display and correction flow. Include silence/background sound and a few deliberately confusable Ukrainian/Russian and Persian/Arabic examples.

Use fresh recordings for acceptance rather than repeatedly tuning thresholds on the same holdout. Measure total user-visible latency and the combined detection → translation outcome, since the existing experiments measure those stages separately. Confirm the detector remains CPU-only and does not alter the GPU service's environment. No additional model comparison or repeated full GPU benchmark is required just to integrate the tested CPU policy.

## Corpus and reproducibility

The library contains **240 FLEURS recordings**, 20 each in Arabic, German, English, Spanish, Persian, French, Italian, Polish, Romanian, Russian, Turkish and Ukrainian. There are 215 recordings with at least eight seconds remaining after VAD onset. CPU LID used 120 initial recordings and 60 additional recordings; **60 of the original 240 have not been tested for LID**. GPU ASR later used all 240, which does not change that LID coverage.

Audio, language labels, source transcripts and available parallel references are known. The selection is non-random read speech, not representative conversation. Dataset revision, CC BY 4.0 attribution, model revisions, frozen dependencies and per-language measurements are linked from the [original CPU report](CPU_LANGUAGE_IDENTIFICATION.md) and [benchmark artifacts](benchmarks/lid-cpu-2026-11-09/SOURCE.json).

Server test environment: `/opt/kienzletranslate-bench/venv`; corpus: `/var/lib/kienzletranslate-bench/fleurs-12`; detector models: `/var/lib/kienzletranslate-bench/models/{tiny,base}`. Raw CPU results are on the server under `/var/lib/kienzletranslate-bench/results/2026-11-09` and locally under the ignored `runtime/lid-benchmark-2026-11-09` directory. Published summaries are sufficient to inspect the reported outcomes; original audio and weights remain outside Git.
