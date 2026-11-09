# CPU-Sprachidentifizierung — 09.11.2026

The consolidated English [development handoff](AUTOMATIC_LANGUAGE_IDENTIFICATION.md) connects these measurements with the later model comparisons, the exact acceptance policy, and the remaining integration decisions.

Whisper **base auf der CPU** ist für einen ersten optionalen Automatikmodus geeignet. Eine frühe Entscheidung nach nur ein bis zwei Sekunden ist unzuverlässig. Die überprüfte vorsichtigere Regel entscheidet frühestens nach fünf Sekunden Audio ab Sprachbeginn und lässt unklare Fälle offen. Der hier dokumentierte Versuch lief getrennt von der App und änderte ihre Python-Umgebung nicht.

Seit v1.6 ist diese Erkennung optional über „Automatic“ integriert, mit eigener CPU-Umgebung und einer zusätzlichen Mindestprüfung des Sprachanteils. Die folgenden Benchmarkzahlen beziehen sich auf den ursprünglichen Versuch; die spätere Ende-zu-Ende-Prüfung steht im [Prüfstand](VERIFICATION.md).

## Tatsächlich gemessene Leistung

- Server: `10.0.83.140`, AMD Ryzen 9 5900X (12 Kerne / 24 Threads), ca. 64 GB RAM.
- Python 3.12.3, faster-whisper 1.2.1, CTranslate2 4.8.5; CPU INT8, tatsächlich `int8_float32`; acht CTranslate2-Threads, ein Worker.
- CUDA für Benchmarkprozesse ausgeblendet; Modellgerät ausdrücklich `cpu`. Kein zusätzlicher Grafikspeicher.
- Erkennungszeit einschließlich Audio-Featureberechnung; Datei-Dekodierung und VAD separat. Kein Netzwerk, kein Seamless-Lauf und keine Übersetzung in diesen Zeiten.
- Modellladen aus dem lokalen Dateicache: tiny 0,153 s, base 0,233 s. Das ist keine Messung eines kalten Serverstarts.
- Spitzen-RAM des gesamten Benchmarkprozesses: tiny 336 MiB, base 401 MiB; einschließlich zwischengespeicherter Testaufnahmen.

## Vergleich: 120 Aufnahmen in zwölf Sprachen

Je zehn Aufnahmen derselben Auswahl für beide Modelle, ohne Einschränkung auf die zwölf möglichen Sprachen. Audio-Präfixe ab vorab markiertem Sprachbeginn; Pausen innerhalb des Ausschnitts bleiben enthalten. Pro Modell 600 Erkennungen plus vier getrennte Nichtsprachkontrollen. Reihenfolge deterministisch gemischt. Zwei Aufwärmaufrufe werden nicht in die Laufzeiten eingerechnet.

| Audio ab Sprachbeginn | tiny richtig | base richtig | tiny Median / P95 | base Median / P95 |
| --- | ---: | ---: | ---: | ---: |
| 1 s | 39.2 % | 51.7 % | 115 / 129 ms | 224 / 240 ms |
| 2 s | 71.7 % | 78.3 % | 121 / 134 ms | 229 / 249 ms |
| 3 s | 83.3 % | 87.5 % | 158 / 184 ms | 268 / 289 ms |
| 5 s | 90.0 % | 96.7 % | 178 / 192 ms | 278 / 295 ms |
| 8 s | 93.3 % | 97.5 % | 178 / 191 ms | 279 / 297 ms |

Diese Trefferquoten zählen jede Top-1-Entscheidung, auch unsichere. Die erste vorab festgelegte Annahmeregel (zwei aufeinanderfolgende gleiche Ergebnisse, beide Score ≥ 0,8 und Abstand zum Zweitplatzierten ≥ 0,2; Prüfungen bei 1/2/3/5/8 s) akzeptierte bei tiny 86/120, davon vier falsch; bei base 103/120, davon eines falsch. Die base-Fehlannahme war Ukrainisch → Russisch nach zwei Sekunden. Modell-Scores sind keine kalibrierten Wahrscheinlichkeiten.

## Unabhängige Nachprüfung: 60 weitere Aufnahmen

Nach dem Vergleich wurde die Regel auf Prüfungen bei **3, 5 und gegebenenfalls 8 Sekunden** geändert. Anschließend erfolgte genau eine Nachprüfung an fünf bislang unbenutzten Aufnahmen je Sprache. Diese 60 Dateien sind von den ersten 120 verschieden. Die Regel verlangt weiterhin zwei aufeinanderfolgende gleiche Ergebnisse mit den genannten Schwellen.

- **53/60 akzeptiert, davon 53 richtig; sieben ohne automatische Entscheidung.**
- 46 Entscheidungen nach fünf Sekunden, sieben nach acht Sekunden; sieben bleiben offen.
- Zusatzwartezeit (Median der aufsummierten Erkennungsaufrufe): **0,422 s**, P95 **0,641 s**. Median Audio bis Annahme 5 s, P95 8 s.
- Einzelaufruf bei fünf Sekunden Audio: **0,209 s Median, 0,219 s P95**.
- Die zweifache Prüfung bei 3 und 5 s kann nach dem Loslassen auf dem bereits vorhandenen Audio erfolgen: ungefähr fünf Sekunden Sprechen plus 0,42 s Berechnung, zusätzlich VAD/Transport. Übersetzung und Sprachausgabe folgen separat.
- Begrenzte Mathematik-Threads: `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1`, `OMP_NUM_THREADS=8`. Im ersten Vergleich waren diese Variablen nicht gesetzt; die spätere Messung verwendet daher eine andere Threadkonfiguration. Ein kurzer Vorvergleich an derselben Datei stützte diese Änderung.
- Peak-RAM im Nachprüfungslauf: **345 MiB** (weniger Aufnahmen im Cache).

53 richtige Annahmen ohne Fehler sind ein Ergebnis dieser kleinen Stichprobe, keine Zusage von 100 % Zuverlässigkeit. Die beiden Präfixprüfungen überlappen und sind keine statistisch unabhängigen Beweise. Einzelwörter, Dialekte, Sprachmischung, Raumhall und echte iPad-Aufnahmen sind damit nicht abgenommen.

## Unterschiede nach Sprache

Jeweils richtige Top-1-Erkennungen von zehn Aufnahmen der ersten Auswahl; kein belastbares Ranking ganzer Sprachen.

| Sprache | tiny 5 s | tiny 8 s | base 5 s | base 8 s |
| --- | ---: | ---: | ---: | ---: |
| Deutsch | 10/10 | 10/10 | 10/10 | 10/10 |
| Englisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Französisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Spanisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Italienisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Polnisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Rumänisch | 6/10 | 6/10 | 10/10 | 10/10 |
| Türkisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Arabisch | 9/10 | 9/10 | 10/10 | 10/10 |
| Russisch | 10/10 | 10/10 | 10/10 | 10/10 |
| Ukrainisch | 6/10 | 8/10 | 7/10 | 8/10 |
| Persisch | 7/10 | 9/10 | 9/10 | 9/10 |

In dieser Auswahl sind Ukrainisch/Russisch besonders verwechslungsanfällig. Persisch wurde vereinzelt als Arabisch erkannt. Eine hohe Einzelbewertung darf deshalb keine automatische Übernahme erzwingen. Stille und leises synthetisches Rauschen erzeugten ebenfalls Sprachlabels, aber hier nur Scores von ungefähr 0,21–0,34; sie wurden nicht in die Sprach-Trefferquote aufgenommen. VAD gehört vor die automatische Entscheidung.

## Testbibliothek und späterer Qualitätsvergleich

[Google FLEURS](https://huggingface.co/datasets/google/fleurs) enthält echte gelesene Sprache, Sprachlabels und Transkriptionen in 102 Sprachen. Die hier heruntergeladene Auswahl besteht aus **240 unveränderten WAV-Dateien in zwölf Sprachen (189,3 MiB)**, 20 unterschiedliche Satzkennungen je Sprache. Sie stammt aus dem Test-Split. Die erste Auswahl folgt der Archiv-Reihenfolge und ist keine Zufallsstichprobe.

- Lizenz/Attribution: **CC BY 4.0**, FLEURS: Few-shot Learning Evaluation of Universal Representations of Speech, Conneau et al., Google, 2022; [Paper](https://arxiv.org/abs/2205.12446). Herkunft und SHA-256 jeder Originalaufnahme stehen in den Manifesten.
- Datensatzrevision: `70bb2e84b976b7e960aa89f1c648e09c59f894dd`.
- Führende Stille wurde nur über Metadaten markiert, nicht aus den Originaldateien entfernt. CPU-Silero-VAD: 250 ms minimale Sprachdauer, 300 ms minimale Pause, kein Padding. Median der führenden Stille 1,088 s. VAD auf den gesamten Aufnahmen etwa 13 ms Median nach dem ersten Aufruf; keine Messung einer Streaming-Lösung.
- 215 Dateien bieten mindestens acht Sekunden nach dem markierten Sprachbeginn; davon wurden 120 im Vergleich und 60 in der Nachprüfung verwendet. Insgesamt bleiben 60 der 240 Originalaufnahmen ohne LID-Test.
- `raw_transcription` und `transcription` erlauben spätere ASR-Auswertung je Sprache mit CER/WER nach dokumentierter sprachgerechter Normalisierung.
- `reference_translations` verknüpft die Texte über Satzkennungen. Alle 240 Dateien besitzen englische Referenztexte, 239 deutsche; je Aufnahme liegen 8–12 Referenzsprachen vor. Damit lässt sich anschließend auch die Seamless-Übersetzungsqualität prüfen, getrennt von der Sprachidentifizierung. Automatische Textmetriken ersetzen keine Beurteilung der Bedeutung.
- Für Vergleiche zwischen Sprachen möglichst gemeinsame Satzkennungen verwenden. Ein breiterer Abnahmetest sollte eigene, bisher unbenutzte Aufnahmen und reale Gesprächssituationen enthalten.

## Ablage und Reproduktion

Getrennte Testumgebung: `/opt/kienzletranslate-bench/venv`.
Bibliothek: `/var/lib/kienzletranslate-bench/fleurs-12`.
Modelle: `/var/lib/kienzletranslate-bench/models/{tiny,base}`.
Rohmessungen: `/var/lib/kienzletranslate-bench/results/2026-11-09`.
Lokale Kopie der Rohmessungen/Metadaten: `runtime/lid-benchmark-2026-11-09` (gitignored).

Im Repository liegen die [Zusammenfassungen und CSV-Tabellen](benchmarks/lid-cpu-2026-11-09/), genaue Modellrevisionen sowie die eingefrorenen Testabhängigkeiten. Audiodateien und Modellgewichte werden nicht ins Repository aufgenommen.

```sh
# In einer eigenen virtuellen Umgebung; niemals in der laufenden App installieren.
pip install -r docs/benchmarks/lid-cpu-2026-11-09/requirements.lock.txt
python scripts/prepare_lid_corpus.py --output /pfad/fleurs-12 --mark-speech
# Modelle mit huggingface_hub.snapshot_download aus den dokumentierten
# Systran-Repositories und Revisionen laden; config.json, model.bin,
# tokenizer.json UND vocabulary.txt gehören zum lokalen Modellverzeichnis.
CUDA_VISIBLE_DEVICES="" OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 OMP_NUM_THREADS=8 \
python scripts/benchmark_lid_cpu.py \
  --manifest /pfad/fleurs-12/manifest-speech.jsonl \
  --model /pfad/models/base --model-label base --output /pfad/base.jsonl \
  --threads 8 --per-language 10 --durations 3,5,8 --speech-onset --controls
```

Dieser Beispielaufruf verwendet die ersten zehn geeigneten Dateien je Sprache. Die unabhängige Nachprüfung nutzte stattdessen `manifest-holdout.jsonl`: die nächsten fünf geeigneten Dateien (Positionen 10–14) je Sprache und `--per-language 5`. Die originale Vergleichskurve verwendet `--durations 1,2,3,5,8` ohne die BLAS-/OMP-Umgebungsvariablen.

Werkzeuge: [Corpus-Downloader](../scripts/prepare_lid_corpus.py), [CPU-Benchmark](../scripts/benchmark_lid_cpu.py). Acht fokussierte Tests prüfen insbesondere, dass falsche Sprachannahmen als Fehler zählen und die Entscheidungsregel keine Referenzlabels oder zukünftigen Ergebnisse verwendet.
