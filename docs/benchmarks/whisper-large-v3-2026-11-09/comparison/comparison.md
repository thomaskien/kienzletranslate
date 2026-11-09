# Paired speech benchmark comparison

All rows are paired by exact sample ID. Candidate outcomes are better/tie/worse; lower edit errors are better for ASR and higher sentence chrF++ is better for translation.

## ASR quality

| Source | Samples | Baseline WER | Candidate WER | Baseline CER | Candidate CER | Better/tie/worse |
|---|---:|---:|---:|---:|---:|---:|
| ar | 20 | 13.72% | 14.88% | 4.85% | 4.51% | 4/7/9 |
| de | 20 | 5.47% | 3.64% | 4.27% | 1.24% | 7/11/2 |
| en | 20 | 7.39% | 5.13% | 4.71% | 2.53% | 8/10/2 |
| es | 20 | 3.36% | 2.05% | 2.17% | 0.62% | 6/12/2 |
| fa | 20 | 10.63% | 17.84% | 4.21% | 6.03% | 5/1/14 |
| fr | 20 | 7.72% | 7.22% | 3.69% | 2.77% | 8/5/7 |
| it | 20 | 5.61% | 2.61% | 3.68% | 0.71% | 6/10/4 |
| pl | 20 | 11.14% | 4.27% | 7.33% | 1.78% | 12/6/2 |
| ro | 20 | 7.81% | 9.52% | 4.79% | 3.93% | 5/6/9 |
| ru | 20 | 8.71% | 6.47% | 3.42% | 1.23% | 8/8/4 |
| tr | 20 | 11.25% | 6.39% | 4.13% | 1.64% | 8/9/3 |
| uk | 20 | 7.24% | 5.68% | 5.20% | 1.82% | 8/8/4 |
| **Overall** | **240** | **8.16%** | **7.18%** | **4.35%** | **2.30%** | **85/93/62** |

## Direct-English translation quality

| Source | Samples | Baseline chrF++ | Candidate chrF++ | Baseline BLEU | Candidate BLEU | Better/tie/worse |
|---|---:|---:|---:|---:|---:|---:|
| ar | 20 | 59.36 | 51.20 | 33.80 | 26.61 | 6/0/14 |
| de | 20 | 62.34 | 57.93 | 38.67 | 34.88 | 10/0/10 |
| es | 20 | 53.25 | 51.14 | 25.56 | 21.39 | 4/2/14 |
| fa | 20 | 55.61 | 43.98 | 29.53 | 16.44 | 1/0/19 |
| fr | 20 | 59.94 | 56.19 | 31.85 | 25.71 | 5/0/15 |
| it | 20 | 52.93 | 52.68 | 23.23 | 23.04 | 9/1/10 |
| pl | 20 | 48.11 | 45.96 | 22.30 | 19.64 | 9/0/11 |
| ro | 20 | 67.57 | 59.52 | 42.43 | 31.08 | 2/0/18 |
| ru | 20 | 60.75 | 54.84 | 35.48 | 26.73 | 5/0/15 |
| tr | 20 | 56.19 | 52.89 | 30.09 | 23.41 | 6/0/14 |
| uk | 20 | 61.20 | 60.81 | 34.34 | 33.96 | 10/0/10 |
| **Pooled English** | **220** | **57.95** | **53.37** | **31.80** | **26.03** | **67/3/150** |

## Reported timing medians

| Stage | Baseline (s) | Candidate (s) |
|---|---:|---:|
| ASR computation | 0.7700 | 0.3593 |
| Direct-English translation | 0.6420 | 0.2577 |

These are supplied stage medians only. Runtime depends on hardware and software configuration, and unlike whole-request timings must not be used for model-speed claims.

## Caveats

This is a small, non-random corpus, so differences should not be generalized to all speech or ranked as broad language performance. WER and CER are edit error rates. chrF++ and BLEU measure reference overlap, not semantic accuracy. Translation compares only target `eng`; baseline German-target rows are excluded before pairing.
