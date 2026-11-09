# Whisper large-v3 GPU transcription benchmark — 2026-11-09

## Scope and interpretation

This report evaluates ASR with known source languages: every recording is supplied with its known source language. It is not a language-identification or translation-quality evaluation. The inference pipeline may also produce translations, but they are not scored here. Full recordings are evaluated without speech-onset trimming.

WER and CER are corpus-weighted edit error rates, not accuracy. WER can exceed 100%. Low WER does not guarantee semantic correctness. The primary symmetric normalization is a project metric, not the exact published FLEURS benchmark normalization; strict WER retains case and punctuation.

The source dataset is public FLEURS (CC BY 4.0). This small, non-random sample of 20 clips per language is not a robust language ranking. Word-boundary and orthography conventions particularly affect Persian and Arabic word scores.

## Overall results

- Recordings: 240 (240 complete, 0 failed)
- Coverage: 100.00%
- Audio duration: 3101.68 seconds
- Reference units: 5709 words, 30111 non-whitespace characters
- Corpus-weighted WER: 7.18%
- Corpus-weighted CER: 2.30%
- Strict WER: 13.74%
- Macro average per-language WER: 7.14%
- Exact normalized matches: 86
- ASR real-time factor (completed recordings only): 0.0291

Model ASR computation latency and whole-request latency are kept separate: ASR median/P95 = 0.3593/0.5745 s; request median/P95 = n/a/n/a s. Peak allocated memory reported by the runner: n/a MiB.

Word diagnostic totals (S/D/I/H): 325/51/34/5333. Alignment ties prefer deletion, then substitution, then insertion.

## Per-language results

| Language | Clips | WER | CER | ASR median (s) | ASR P95 (s) |
|---|---:|---:|---:|---:|---:|
| ar | 20 | 14.88% | 4.51% | 0.4252 | 0.5869 |
| de | 20 | 3.64% | 1.24% | 0.3421 | 0.6317 |
| en | 20 | 5.13% | 2.53% | 0.2458 | 0.3249 |
| es | 20 | 2.05% | 0.62% | 0.3028 | 0.3965 |
| fa | 20 | 17.84% | 6.03% | 0.4817 | 0.6147 |
| fr | 20 | 7.22% | 2.77% | 0.3269 | 0.6211 |
| it | 20 | 2.61% | 0.71% | 0.3611 | 0.4866 |
| pl | 20 | 4.27% | 1.78% | 0.3600 | 0.4347 |
| ro | 20 | 9.52% | 3.93% | 0.4013 | 0.4849 |
| ru | 20 | 6.47% | 1.23% | 0.3292 | 0.4686 |
| tr | 20 | 6.39% | 1.64% | 0.3291 | 0.5311 |
| uk | 20 | 5.68% | 1.82% | 0.3841 | 0.5592 |

## Failed recordings

None.

## Worst normalized-WER samples

### <code>&quot;ar_eg/10366294495925707527.wav&quot;</code> (ar, WER 54.55%, S/D/I 12/0/0)

- Reference: <code>&quot;بصفته رياضيّاً شاملاً، يمكن للنّمر التّسلق (وإن لم يكن ذلك بشكلٍ جيد) والسّباحة والقفز لمسافاتٍ طويلةٍ والسّحب بقوّة خمسة أضعاف قوّة الإنسان.&quot;</code>
- Hypothesis: <code>&quot;بصفة رياضية شاملة يمكن للنمر التسلق وإن لم يكن ذلك بشكل جيد والسباحة والقفز لمسافات طويلة والسحب بقوة خمسة أضعاف قوة الإنسان&quot;</code>

### <code>&quot;ru_ru/10270509144878549012.wav&quot;</code> (ru, WER 46.15%, S/D/I 4/0/2)

- Reference: <code>&quot;Лаккха Сингх исполнил чхаппан бхог бхаджан.  Певец Раджу Кханделвал пел вместе с ним.&quot;</code>
- Hypothesis: <code>&quot;Лакха Сингх исполнил Чхаппан Пхо Пхаджан, певец Раджу. Хан Дел Вал пел вместе с ним.&quot;</code>

### <code>&quot;ar_eg/10340788584398631536.wav&quot;</code> (ar, WER 41.18%, S/D/I 7/0/0)

- Reference: <code>&quot;أدى ضاربا الكرة المتمركزين في الوسط، ساشين تيندولكار وراهول درافيد، جيدًا وأقاما شراكة أكسبت للفريق مائة نقطة.&quot;</code>
- Hypothesis: <code>&quot;أدى ضارب الكرة المتمركزين في الوسط ساشين تندولكار وراهولد رافد جيدا وأقام شراكة أكسبت للفريق 100 نقطة&quot;</code>

### <code>&quot;de_de/103625751236710165.wav&quot;</code> (de, WER 35.71%, S/D/I 5/0/0)

- Reference: <code>&quot;Lakkha Singh präsentierte den Chhappan Bhog Bhajan ebenfalls. Der Sänger Raju Khandelwal begleitete ihn.&quot;</code>
- Hypothesis: <code>&quot;Laka Singh präsentierte den Schapan-Bog Bajan ebenfalls. Der Sänger Raju Kandelwal begleitete ihn.&quot;</code>

### <code>&quot;fa_ir/10124979281588232806.wav&quot;</code> (fa, WER 33.33%, S/D/I 8/0/3)

- Reference: <code>&quot;با اینکه بنظر می‌رسد یک واکسن تجربی بتواند میزان مرگ و میر ایبولا را کاهش دهد، تا به امروز هیچ دارویی نبوده که به وضوح ثابت شود برای درمان عفونت کنونی است.&quot;</code>
- Hypothesis: <code>&quot;با این که به نظر می رسد یک واکسن تجربی به تمانت میزان مرگ و نیر ایبولا را کاهش دهد تا به امروز هیچ داروی ندوده که به وضوع ثابت شود برای درمان افونت کنونی است.&quot;</code>

### <code>&quot;fa_ir/10140044754665750794.wav&quot;</code> (fa, WER 32.00%, S/D/I 4/3/1)

- Reference: <code>&quot;سلطان مراکش شهر دارالبیضا را بازسازی کرد و بازرگانان اسپانیایی که پایگاههای تجاری‌شان را در آنجا دایر کردند نام کازابلانکا را به آن دادند.&quot;</code>
- Hypothesis: <code>&quot;سلطان مراکش شهر دارال بیزار را بازرگانان اسپانیایی که پایگاه های تجاریشان را در آنجا دایر کردند نام کازابلانکا را به آن دادند.&quot;</code>

### <code>&quot;uk_ua/10212361100311604669.wav&quot;</code> (uk, WER 29.41%, S/D/I 5/0/0)

- Reference: <code>&quot;Архіпелаг лежить 120 км на північ від півострова. Найбільший острів — Кінг-Джордж, із поселенням Вілья-лас-Естрельяс.&quot;</code>
- Hypothesis: <code>&quot;Архипелаг лежить 120 км на північ від півострова. Найбільший остров – Кінг-Дзорш із поселенням Вілля-Лас-Естреллєс.&quot;</code>

### <code>&quot;fr_fr/10334413597118469552.wav&quot;</code> (fr, WER 29.17%, S/D/I 5/2/0)

- Reference: <code>&quot;Malheureusement, il est difficile d&#x27;étudier le flux de circulation car le comportement des conducteurs ne peut être prédit avec cent pour cent de certitude.&quot;</code>
- Hypothesis: <code>&quot;Malheureusement, il est difficile d&#x27;étudier le flux de circulation car les comportements des conducteurs ne peuvent être prédits avec 100% de certitude.&quot;</code>

### <code>&quot;ro_ro/1024428599537771284.wav&quot;</code> (ro, WER 29.03%, S/D/I 7/1/1)

- Reference: <code>&quot;Aristotel, un filozof, a emis o teorie conform căreia totul este alcătuit dintr-un amestec de unul sau mai multe dintre cele patru elemente. Acestea erau apa, pământul, aerul și focul.&quot;</code>
- Hypothesis: <code>&quot;Alistair Tell, un filozof, a emis un teorie confort căia totuia scăduit într-un amestec de unul sau mai multe dintre cele patru elemente. Acestea erau apa, pământul, aerul și focul.&quot;</code>

### <code>&quot;fr_fr/10143749263702132703.wav&quot;</code> (fr, WER 26.92%, S/D/I 6/1/0)

- Reference: <code>&quot;Le rugissement du tigre ne ressemble pas au rugissement ample du lion, mais plutôt à une phrase dont les mots seraient des cris et des grondements.&quot;</code>
- Hypothesis: <code>&quot;L&#x27;enregistrement du tigre ne ressemble pas à un enregistrement en plurian, mais plutôt à une phrase dont les mots seraient des cris et des grondements.&quot;</code>

### <code>&quot;ro_ro/10078905333670677530.wav&quot;</code> (ro, WER 25.00%, S/D/I 5/0/2)

- Reference: <code>&quot;Celelalte nominalizări includ cel mai bun film, regizor, imagine, design de costume, montaj de film, coloană sonoră, design de producție, regie de sunet, mixaj sonor și scenariu original.&quot;</code>
- Hypothesis: <code>&quot;Celelalte numele de analizări includ cel mai bun film, regizor, imagini, design de costume, montaj de film, coloana sonoră, design de producție, regie de sunet, mixași onor și scenariu original.&quot;</code>

### <code>&quot;tr_tr/10406878871118112918.wav&quot;</code> (tr, WER 25.00%, S/D/I 3/0/1)

- Reference: <code>&quot;Bir örgütün işlevsel departmanlarında mümkün olan tüm kaynaklar etkin biçimde kullanıldığında yaratıcılık ve ustalık ortaya çıkabilir.&quot;</code>
- Hypothesis: <code>&quot;Bir örgütün işleysel departmanlarına mümkün olan tüm kaynaklar etkin bir çimde kullanıldığında, yaratıcılık ve ustalık ortaya çıkabilir.&quot;</code>
