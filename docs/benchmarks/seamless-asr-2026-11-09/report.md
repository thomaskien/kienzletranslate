# SeamlessM4T GPU transcription benchmark — 2026-11-09

## Scope and interpretation

This report evaluates ASR with known source languages: every recording is supplied with its known source language. It is not a language-identification or translation-quality evaluation. The inference pipeline may also produce translations, but they are not scored here. Full recordings are evaluated without speech-onset trimming.

WER and CER are corpus-weighted edit error rates, not accuracy. WER can exceed 100%. Low WER does not guarantee semantic correctness. The primary symmetric normalization is a project metric, not the exact published FLEURS benchmark normalization; strict WER retains case and punctuation.

The source dataset is public FLEURS (CC BY 4.0). This small, non-random sample of 20 clips per language is not a robust language ranking. Word-boundary and orthography conventions particularly affect Persian and Arabic word scores.

## Overall results

- Recordings: 240 (240 complete, 0 failed)
- Coverage: 100.00%
- Audio duration: 3101.68 seconds
- Reference units: 5709 words, 30111 non-whitespace characters
- Corpus-weighted WER: 8.16%
- Corpus-weighted CER: 4.35%
- Strict WER: 19.77%
- Macro average per-language WER: 8.34%
- Exact normalized matches: 74
- ASR real-time factor (completed recordings only): 0.0629

Model ASR computation latency and whole-request latency are kept separate: ASR median/P95 = 0.7700/1.1356 s; request median/P95 = 1.4739/2.0561 s. Peak allocated memory reported by the runner: 6193.0 MiB.

Word diagnostic totals (S/D/I/H): 331/47/88/5331. Alignment ties prefer deletion, then substitution, then insertion.

## Per-language results

| Language | Clips | WER | CER | ASR median (s) | ASR P95 (s) |
|---|---:|---:|---:|---:|---:|
| ar | 20 | 13.72% | 4.85% | 0.7485 | 1.0216 |
| de | 20 | 5.47% | 4.27% | 0.7730 | 1.3956 |
| en | 20 | 7.39% | 4.71% | 0.6900 | 0.8582 |
| es | 20 | 3.36% | 2.17% | 0.7270 | 0.9827 |
| fa | 20 | 10.63% | 4.21% | 0.7535 | 0.9509 |
| fr | 20 | 7.72% | 3.69% | 0.8055 | 1.4537 |
| it | 20 | 5.61% | 3.68% | 0.8245 | 1.0846 |
| pl | 20 | 11.14% | 7.33% | 0.8225 | 0.9715 |
| ro | 20 | 7.81% | 4.79% | 0.8855 | 1.0267 |
| ru | 20 | 8.71% | 3.42% | 0.7625 | 1.1356 |
| tr | 20 | 11.25% | 4.13% | 0.7510 | 1.2280 |
| uk | 20 | 7.24% | 5.20% | 0.7925 | 1.0696 |

## Failed recordings

None.

## Worst normalized-WER samples

### <code>&quot;pl_pl/10272446192914218891.wav&quot;</code> (pl, WER 60.00%, S/D/I 4/0/5)

- Reference: <code>&quot;Obecność prawdziwej „niewidzialnej drużyny” (Larson i LaFasto, 1989, s.109) to wyjątkowy element wirtualnej drużyny.&quot;</code>
- Hypothesis: <code>&quot;obecność prawdziwej niewidzialnej drużyny larson i la fasta tysiąc dziewięćset osiemdziesiąt dziewięć strona sto dziewięć to wyjątkowy element wirtualnej drużyny.&quot;</code>

### <code>&quot;ar_eg/10366294495925707527.wav&quot;</code> (ar, WER 50.00%, S/D/I 11/0/0)

- Reference: <code>&quot;بصفته رياضيّاً شاملاً، يمكن للنّمر التّسلق (وإن لم يكن ذلك بشكلٍ جيد) والسّباحة والقفز لمسافاتٍ طويلةٍ والسّحب بقوّة خمسة أضعاف قوّة الإنسان.&quot;</code>
- Hypothesis: <code>&quot;بصفته رياضيا شاملا يمكن للنمر التسلق وإن لم يكن ذلك بشكل جيد والسباحة والقفز لمسافات طويلة والسحب بقوة خمسة أضعاف قوة الإنسان.&quot;</code>

### <code>&quot;ro_ro/10414675901475030468.wav&quot;</code> (ro, WER 42.86%, S/D/I 2/0/4)

- Reference: <code>&quot;„Pe 15 august 1940, Aliații au invadat sudul Franței, invazia fiind denumită «Operațiunea Dragoon».”&quot;</code>
- Hypothesis: <code>&quot;Pe cincisprezece august o mie nouă sute patruzeci, aliații au invadat sudul Franței, invazia fiind denumită operațiunea Dragoon.&quot;</code>

### <code>&quot;uk_ua/10212361100311604669.wav&quot;</code> (uk, WER 41.18%, S/D/I 5/1/1)

- Reference: <code>&quot;Архіпелаг лежить 120 км на північ від півострова. Найбільший острів — Кінг-Джордж, із поселенням Вілья-лас-Естрельяс.&quot;</code>
- Hypothesis: <code>&quot;Архіпелаг лежить сто двадцять кілометрів на північ від півострова. Найбільший острів  Кінгджордж із поселенням Вілла  Лас Естреліас.&quot;</code>

### <code>&quot;fa_ir/10420872632796282639.wav&quot;</code> (fa, WER 38.89%, S/D/I 2/0/5)

- Reference: <code>&quot;در سال 1990، به‌دلیل خطر شنهای صحرا به فهرست میراث‌های جهانی در معرض خطر اضافه شد.&quot;</code>
- Hypothesis: <code>&quot;در سال هزار و نوزده و نود به دلیل خطر شن های صحرا به فهرست میراث های جهانی در معرض خطر اضافه شد.&quot;</code>

### <code>&quot;de_de/103625751236710165.wav&quot;</code> (de, WER 35.71%, S/D/I 5/0/0)

- Reference: <code>&quot;Lakkha Singh präsentierte den Chhappan Bhog Bhajan ebenfalls. Der Sänger Raju Khandelwal begleitete ihn.&quot;</code>
- Hypothesis: <code>&quot;Laka Singh präsentierte den Japan-Bog Bayern ebenfalls, der Sänger Raju Kandelwal begleitete ihn.&quot;</code>

### <code>&quot;ru_ru/10021068571959461962.wav&quot;</code> (ru, WER 35.00%, S/D/I 4/0/3)

- Reference: <code>&quot;В 1990 году он был добавлен в список всемирного наследия, находящегося под угрозой из-за опасности со стороны песков пустыни.&quot;</code>
- Hypothesis: <code>&quot;В тысяча девятьсот девяносто годом он Был добавлен В Список всемирного наследия, находящегося под угрозой из-за опасности со стороны песка в пустыне.&quot;</code>

### <code>&quot;ar_eg/10482686991657251883.wav&quot;</code> (ar, WER 33.33%, S/D/I 5/0/0)

- Reference: <code>&quot;يمكنك أن تسمع صوت السيّاح والبائعين هنا دائماً عادةً. فقصة الصوت والضوء تشبه قصة كتابٍ.&quot;</code>
- Hypothesis: <code>&quot;يمكنك أن تسمع صوت السياح والباعةين هنا دائما عادة، فقصة الصوت والضوء تشبه قصة كتاب.&quot;</code>

### <code>&quot;ru_ru/10270509144878549012.wav&quot;</code> (ru, WER 30.77%, S/D/I 4/0/0)

- Reference: <code>&quot;Лаккха Сингх исполнил чхаппан бхог бхаджан.  Певец Раджу Кханделвал пел вместе с ним.&quot;</code>
- Hypothesis: <code>&quot;Лакха Сингх исполнил чхапан пхо пхаджан, певец Раджу Кханделвал пел вместе с ним.&quot;</code>

### <code>&quot;fa_ir/10130894543333251273.wav&quot;</code> (fa, WER 26.32%, S/D/I 3/2/0)

- Reference: <code>&quot;بعضی اتم‌ها هسته‌های ناپایداری دارند یعنی بدون اشاره یا با اشاره‌ای کوچک تمایل به فروپاشی دارند.&quot;</code>
- Hypothesis: <code>&quot;بعضی اتمها حصه های ناپایدار دارند، یعنی بدون اشاره یا با اشاره کوچک تمایل به فروپاشی دارند.&quot;</code>

### <code>&quot;uk_ua/10693320899315936204.wav&quot;</code> (uk, WER 26.32%, S/D/I 2/0/3)

- Reference: <code>&quot;Гавань стала місцем сумнозвісного морського протистояння в 1889, коли сім суден із Німеччини, США та Британії відмовилися її залишити.&quot;</code>
- Hypothesis: <code>&quot;гавань стала Місцем сумнозвісного морського протистояння В тисячу вісімсот вісімдесят дев&#x27;ятому, коли Сім Студентів із Німеччини, США та Британії відмовилися її залишити.&quot;</code>

### <code>&quot;de_de/10371526464884803925.wav&quot;</code> (de, WER 25.00%, S/D/I 2/1/0)

- Reference: <code>&quot;Der Scotturb-Bus 403 fährt regelmäßig über Cabo da Roca nach Sintra.&quot;</code>
- Hypothesis: <code>&quot;Der Scotabus vierhundertdrei fährt regelmäßig über Cabo da Roca nach Sintra.&quot;</code>
