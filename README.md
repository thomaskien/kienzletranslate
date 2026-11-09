# kienzletranslate v1.6.1

<p align="center">
  <a href="https://www.youtube.com/watch?v=YIOPyuph8j8">
    <img src="https://img.youtube.com/vi/YIOPyuph8j8/maxresdefault.jpg" width="900" alt="Watch the kienzletranslate demo video on YouTube">
  </a>
</p>

<table>
<tr><th width="50%">▶ Demo video</th><th width="50%">▶ Demo-Video</th></tr>
<tr>
<td><a href="https://www.youtube.com/watch?v=YIOPyuph8j8"><strong>Watch kienzletranslate in action on YouTube</strong></a> — local translation with SeamlessM4T on an NVIDIA RTX 3090. Click the preview above to play.</td>
<td><a href="https://www.youtube.com/watch?v=YIOPyuph8j8"><strong>kienzletranslate auf YouTube in Aktion ansehen</strong></a> — lokale Übersetzung mit SeamlessM4T auf einer NVIDIA RTX 3090. Zum Abspielen auf das Vorschaubild klicken.</td>
</tr>
</table>

<table>
<tr><th width="50%">English</th><th width="50%">Deutsch</th></tr>
<tr>
<td>A local conversation translator for two people facing each other, operated on an <strong>iPad or iPhone</strong>. The PHP web app and a central SeamlessM4T v2 Large service run on a Linux computer with an NVIDIA GPU. Native installation, no Docker.</td>
<td>Lokaler Gesprächsübersetzer für zwei gegenüber sitzende Personen, bedient auf einem <strong>iPad oder iPhone</strong>. PHP-Webapp und ein zentraler SeamlessM4T-v2-Large-Modellservice laufen auf einem Linux-Rechner mit NVIDIA-GPU. Native Installation ohne Docker.</td>
</tr>
</table>

<p align="center">
  <img src="a_clean_modern_high_contrast_user_interface_desi.png" width="640" alt="kienzletranslate interface concept: two opposing speaking areas, language selection and a green recording area">
</p>

<table>
<tr><td width="50%"><em>Interface concept · Face each other, hold, speak and translate.</em></td><td width="50%"><em>Oberflächenentwurf · Gegenübersitzen, gedrückt halten, sprechen und übersetzen.</em></td></tr>
</table>

<table>
<tr><th width="50%">Model licence</th><th width="50%">Modelllizenz</th></tr>
<tr>
<td><strong>CC BY-NC 4.0 — noncommercial use only.</strong> The application's MIT licence does not grant additional rights to the model weights. The installer and certificate setup page require explicit confirmation with <code>ACCEPT</code> or <code>AKZEPTIEREN</code>. <a href="docs/LICENSES.md">Licence details</a>.<br>Technical prototype; no medical validation. Use test data.</td>
<td><strong>CC BY-NC 4.0 — nur nichtkommerzielle Nutzung.</strong> Die MIT-Lizenz der Anwendung erlaubt keine darüber hinausgehende Nutzung der Modellgewichte. Installer und Zertifikatsseite verlangen eine ausdrückliche Bestätigung durch <code>AKZEPTIEREN</code> oder <code>ACCEPT</code>. <a href="docs/LICENSES.md">Lizenzdetails</a>.<br>Technischer Prototyp; keine medizinische Validierung. Testdaten verwenden.</td>
</tr>
</table>

<p align="center">
  <img src="docs/images/kienzletranslate-rtx-3090.png" width="900" alt="GPU monitor showing kienzletranslate load and memory use on an NVIDIA GeForce RTX 3090">
</p>

<table>
<tr><td width="50%"><em>Local GPU operation · Snapshot on an NVIDIA GeForce RTX 3090 with 24 GB VRAM.</em></td><td width="50%"><em>Lokaler GPU-Betrieb · Momentaufnahme auf einer NVIDIA GeForce RTX 3090 mit 24 GB Grafikspeicher.</em></td></tr>
</table>

<table>
<tr><th width="50%">Completed tests and benchmarks · 9 November 2026</th><th width="50%">Durchgeführte Tests und Benchmarks · 09.11.2026</th></tr>
<tr>
<td><strong>Application checks:</strong> v1.6.1 verifies the 2×2 Automatic tile in both language pickers at iPhone/iPad sizes. v1.6 passed 16 JavaScript tests, syntax checks and targeted browser checks at iPhone/iPad sizes for startup, language selection and refresh. The v1.6 update also passed installer/uninstaller and backend checks, plus real HTTPS translation with automatic language detection and GPU loading/unloading (5224 MiB down to 65 MiB). The UI checks simulate microphone activation; practical iPhone/iPad operation has also been confirmed by the user. <a href="docs/VERIFICATION.md">Results and test scope</a> · <a href="docs/TESTPLAN.md">Test plan</a>.</td>
<td><strong>App-Prüfungen:</strong> Für v1.6.1 wurde die 2×2-Schaltfläche Automatic in beiden Sprachauswahlen in iPhone-/iPad-Größen geprüft. Für v1.6 bestanden 16 JavaScript-Tests, Syntaxprüfungen und gezielte Browserprüfungen in iPhone-/iPad-Größen für Start, Sprachwahl und Refresh. Für v1.6 bestanden außerdem Installer-/Uninstaller- und Backendprüfungen sowie echte HTTPS-Übersetzung mit automatischer Sprachwahl und GPU-Laden/-Entladen (5224 MiB auf 65 MiB). Die UI-Prüfungen simulieren die Mikrofonaktivierung; den praktischen iPhone-/iPad-Betrieb hat der Nutzer ebenfalls bestätigt. <a href="docs/VERIFICATION.md">Ergebnisse und Prüfumfang</a> · <a href="docs/TESTPLAN.md">Testplan</a>.</td>
</tr>
<tr>
<td><strong>GPU transcription:</strong> all <strong>240 FLEURS recordings in 12 languages</strong> completed successfully (51 min 42 s of audio). Normalized word error rate: <strong>8.16%</strong>; character error rate: <strong>4.35%</strong>. Median ASR computation: <strong>0.77 s per recording</strong> on the RTX 3090 with the model already loaded. Source languages were supplied; translation quality was not scored. <a href="docs/GPU_TRANSCRIPTION_BENCHMARK.md">Method, per-language results and limitations</a> · <a href="docs/benchmarks/seamless-asr-2026-11-09/per-sample.csv">Per-recording measurements</a>.</td>
<td><strong>GPU-Transkription:</strong> alle <strong>240 FLEURS-Aufnahmen in zwölf Sprachen</strong> erfolgreich verarbeitet (51 min 42 s Audio). Normalisierte Wortfehlerrate: <strong>8,16 %</strong>; Zeichenfehlerrate: <strong>4,35 %</strong>. Mediane ASR-Berechnung: <strong>0,77 s je Aufnahme</strong> auf der RTX 3090 bei bereits geladenem Modell. Die Ausgangssprachen waren vorgegeben; die Übersetzungsqualität wurde nicht bewertet. <a href="docs/GPU_TRANSCRIPTION_BENCHMARK.md">Methode, Ergebnisse je Sprache und Grenzen</a> · <a href="docs/benchmarks/seamless-asr-2026-11-09/per-sample.csv">Einzelmessungen</a>.</td>
</tr>
<tr>
<td><strong>CPU language identification — separate experiment:</strong> Whisper tiny/base were compared on 120 recordings in 12 languages. With a more conservative rule, base correctly accepted <strong>53 of 60 new recordings</strong>; seven remained undecided. Earliest acceptance after five seconds of speech; median accumulated detection computation <strong>0.422 s</strong> on a Ryzen 9 5900X. No additional GPU memory. <strong>Integrated in v1.6:</strong> one optional attempt through Automatic, with manual fallback. <a href="docs/CPU_LANGUAGE_IDENTIFICATION.md">Protocol, timings and limitations</a> · <a href="docs/benchmarks/lid-cpu-2026-11-09/base-holdout.summary.json">Follow-up results</a>.</td>
<td><strong>CPU-Sprachidentifizierung — separater Versuch:</strong> Whisper tiny/base wurden an 120 Aufnahmen in zwölf Sprachen verglichen. Mit vorsichtigerer Regel akzeptierte base <strong>53 von 60 neuen Aufnahmen korrekt</strong>; sieben blieben unentschieden. Früheste Annahme nach fünf Sekunden Sprache; aufsummierte Erkennungsberechnung im Median <strong>0,422 s</strong> auf einem Ryzen 9 5900X. Kein zusätzlicher Grafikspeicher. <strong>Seit v1.6 integriert:</strong> ein optionaler Versuch über Automatic mit manueller Rückfallauswahl. <a href="docs/CPU_LANGUAGE_IDENTIFICATION.md">Vorgehen, Laufzeiten und Grenzen</a> · <a href="docs/benchmarks/lid-cpu-2026-11-09/base-holdout.summary.json">Ergebnisse der Nachprüfung</a>.</td>
</tr>
</table>

<table>
<tr><th width="50%">Language selection</th><th width="50%">Sprachauswahl</th></tr>
<tr>
<td>On opening, first select your own flag to set the interface and your language (bottom speaking area), then enable the microphone. Next, the facing person chooses a language from a rotated, scrollable grid in the upper half: four flags per row with language names underneath. The app is immediately ready to talk after that selection. The left language control opens the same choices upright for later changes. A refresh button on your side reopens only the facing person’s language selection; your language and microphone permission remain unchanged. All 18 frequently used languages are available, with native language names. The compact start dialog explains push-to-talk in one sentence. Flags also appear in the language menus.</td>
<td>Beim Öffnen zuerst mit der eigenen Fahne die Oberfläche und „Ihre Sprache“ (untere Sprechfläche) wählen und das Mikrofon aktivieren. Danach wählt die gegenüberliegende Person ihre Sprache im gedrehten, scrollbaren Raster auf der oberen Hälfte: vier Fahnen pro Reihe mit Sprachname darunter. Anschließend ist die App sofort gesprächsbereit. Das linke Sprachmenü öffnet dieselbe Auswahl aufrecht für spätere Änderungen. Ein Refresh-Knopf auf Ihrer Seite öffnet ausschließlich die Sprachwahl gegenüber erneut; Ihre Sprache und die Mikrofonfreigabe bleiben erhalten. Alle 18 häufigen Sprachen sind mit ihren Eigennamen verfügbar. Der kompakte Startdialog erklärt Push-to-Talk in einem Satz. Fahnen erscheinen auch in den Sprachmenüs.</td>
</tr>
<tr>
<td>German, English, Turkish, Arabic, Russian, Ukrainian, Polish, Romanian, Italian, Bulgarian, Croatian, Bosnian, Serbian, Kurdish (Sorani), Persian, Greek, French and Spanish. Flags are visual shortcuts; the language name identifies the choice.</td>
<td>Deutsch, Englisch, Türkisch, Arabisch, Russisch, Ukrainisch, Polnisch, Rumänisch, Italienisch, Bulgarisch, Kroatisch, Bosnisch, Serbisch, Kurdisch (Sorani), Persisch, Griechisch, Französisch und Spanisch. Fahnen dienen als Orientierung; der Sprachname bezeichnet die Auswahl.</td>
</tr>
</table>

<table>
<tr><th width="50%">GPU memory and removal</th><th width="50%">Grafikspeicher und Deinstallation</th></tr>
<tr><td>The model loads after microphone activation, subject to a free-VRAM check. A 15-second heartbeat tracks connected devices. By default the GPU process exits after 90 seconds without devices or five minutes without interaction; ordinary heartbeats do not reload it. Recording and queued jobs prevent unloading. Boot loading is off by default; the installer asks for these settings. An 8 GB GPU has not been validated.</td><td>Das Modell lädt nach Mikrofonfreigabe, sofern die Grafikspeicherprüfung genügende Reserve meldet. Ein Heartbeat alle 15 Sekunden erfasst verbundene Geräte. Standardmäßig endet der GPU-Prozess nach 90 Sekunden ohne Geräte oder fünf Minuten ohne Bedienung; gewöhnliche Heartbeats laden ihn nicht erneut. Aufnahmen und wartende Aufträge verhindern das Entladen. Laden beim Booten ist standardmäßig aus; der Installer fragt diese Einstellungen ab. Eine 8-GB-GPU wurde nicht abgenommen.</td></tr>
<tr><td><code>sudo bash uninstall.sh</code> previews removal and requires <code>UNINSTALL</code> confirmation in English. Configuration, CA, backups and models are kept by default. <a href="docs/INSTALLATION.md">Installation and removal details</a>.</td><td><code>sudo bash uninstall.sh</code> zeigt die geplante Entfernung und verlangt die Bestätigung <code>DEINSTALLIEREN</code>. Konfiguration, CA, Backups und Modelle bleiben standardmäßig erhalten. <a href="docs/INSTALLATION.md">Installation und Deinstallation</a>.</td></tr>
</table>

<table>
<tr><th width="50%">Installation / Update</th><th width="50%">Installation / Update</th></tr>
<tr>
<td>Tested server: Ubuntu 24.04, Python 3.12, NVIDIA RTX 3090 (24 GB), working NVIDIA driver. Allow about 25 GB of free disk space for the model and Python/CUDA dependencies. The installer also supports Debian, which has not been separately validated.</td>
<td>Getesteter Server: Ubuntu 24.04, Python 3.12, NVIDIA RTX 3090 (24 GB), funktionsfähiger NVIDIA-Treiber. Rund 25 GB freien Speicher für Modell und Python/CUDA-Abhängigkeiten vorsehen. Debian wird vom Installer ebenfalls unterstützt, wurde aber nicht separat abgenommen.</td>
</tr>
<tr>
<td><pre><code>git clone \
  https://github.com/\
thomaskien/kienzletranslate.git
cd kienzletranslate
sudo bash install.sh</code></pre></td>
<td><pre><code>git clone \
  https://github.com/\
thomaskien/kienzletranslate.git
cd kienzletranslate
sudo bash install.sh</code></pre></td>
</tr>
<tr>
<td>First choose German or English, then confirm the model licence. The installer asks for the server IP, optional DNS name, HTTP/HTTPS/model ports, directories and optional password protection (<strong>off by default</strong>). With protection enabled, an empty password entry retains the existing password or generates a secure one. Access details are stored in <code>/root/kienzletranslate-access.json</code>, readable only by root.</td>
<td>Zuerst Deutsch oder Englisch wählen, danach die Modelllizenz bestätigen. Der Installer fragt Server-IP, optionalen DNS-Namen, HTTP-/HTTPS-/Modellport, Pfade und optionalen Passwortschutz ab (<strong>standardmäßig aus</strong>). Bei aktiviertem Schutz erhält eine leere Passworteingabe das vorhandene Passwort oder erzeugt ein sicheres. Die Zugangsdaten liegen in <code>/root/kienzletranslate-access.json</code>, nur für root lesbar.</td>
</tr>
<tr>
<td>For updates, obtain the new source and run the same installer. Configuration, password setting and local CA are retained; the previous release is backed up. If the final health check fails, the installer attempts to restore the previous release. System packages and Python dependencies are not automatically downgraded.</td>
<td>Für Updates den neuen Quellstand holen und denselben Installer aufrufen. Konfiguration, Passwortwahl und lokale CA bleiben erhalten; der vorherige Stand wird gesichert. Scheitert der abschließende Gesundheitscheck, versucht der Installer die vorherige Version wiederherzustellen. Systempakete und Python-Abhängigkeiten werden nicht automatisch zurückgestuft.</td>
</tr>
<tr>
<td>Open the HTTP setup page on the iPad/iPhone, confirm the licence again, install the CA profile and enable full certificate trust. Then open the HTTPS app and optionally add it to the Home Screen. Model weights are downloaded separately. After setup, inference works without external services. <a href="docs/INSTALLATION.md">Detailed setup</a>.</td>
<td>Auf dem iPad/iPhone die HTTP-Einrichtungsseite öffnen, die Lizenz erneut bestätigen, das CA-Profil installieren und volles Zertifikatsvertrauen aktivieren. Danach die HTTPS-App öffnen und bei Bedarf zum Home-Bildschirm hinzufügen. Modellgewichte werden separat heruntergeladen. Nach Einrichtung läuft die Inferenz ohne externe Dienste. <a href="docs/INSTALLATION.md">Ausführliche Einrichtung</a>.</td>
</tr>
</table>

<table>
<tr><th width="50%">How to use</th><th width="50%">Bedienung</th></tr>
<tr>
<td><ol>
<li>First tap your own flag to set the interface and your language, and enable the microphone. Then choose the opposite person’s language in the upper flag grid. The app is immediately ready; the defaults are Ukrainian at the top and German at the bottom.</li>
<li>Hold your speaking area, speak, then release to translate. Green means recording; processing starts on release.</li>
<li>The original text appears on the speaker's side and the translation opposite. The upper conversation text is rotated; controls stay upright. Text shrinks to fit the available area.</li>
<li>Toggle translated speech with the speaker button. A new recording interrupts playback.</li>
</ol></td>
<td><ol>
<li>Zuerst mit der eigenen Fahne Oberfläche und „Ihre Sprache“ wählen und das Mikrofon aktivieren. Danach die Sprache der gegenüberliegenden Person im oberen Fahnenraster wählen. Die App ist sofort bereit; voreingestellt sind Ukrainisch oben und Deutsch unten.</li>
<li>Eigene Sprechfläche gedrückt halten, sprechen und zum Übersetzen loslassen. Grün bedeutet Aufnahme; die Verarbeitung beginnt beim Loslassen.</li>
<li>Der Originaltext erscheint auf der Sprecherseite, die Übersetzung gegenüber. Der obere Gesprächstext ist gedreht, Bedienelemente bleiben aufrecht. Text wird passend zur verfügbaren Fläche verkleinert.</li>
<li>Übersetzte Sprachausgabe über den Lautsprecher umschalten. Eine neue Aufnahme unterbricht die Wiedergabe.</li>
</ol></td>
</tr>
<tr>
<td>Frequently used languages in Germany appear first, followed by other languages; both groups are alphabetically sorted. Settings include the same flags, audio pre-roll (0–3 seconds in 250 ms steps, default 0.25 seconds), and model loading/unloading. Preferences are saved locally.</td>
<td>Häufig in Deutschland verwendete Sprachen stehen zuerst, weitere darunter; beide Gruppen sind alphabetisch sortiert. Die Einstellungen enthalten dieselben Fahnen, den Audio-Vorlauf (0–3 Sekunden in 250-ms-Schritten, Standard 0,25 Sekunden) und das Laden/Entladen des Modells. Einstellungen werden lokal gespeichert.</td>
</tr>
<tr>
<td>The microphone stays active in the foreground for the temporary local pre-roll buffer. No audio is transmitted while idle. Recordings are limited to 60 seconds including pre-roll. Choose a language manually or tap the large <strong>Automatic</strong> tile (two columns by two rows) for one attempt on the next opposite-side recording. Speak for at least five seconds; uncertain or unsupported results return to manual flags. Only refresh enables another attempt. No live transcription or speaker identification. Targets without speech synthesis receive text only.</td>
<td>Das Mikrofon bleibt im Vordergrund für den flüchtigen lokalen Vorlaufpuffer geöffnet. Im Leerlauf werden keine Audiodaten übertragen. Aufnahmen sind einschließlich Vorlauf auf 60 Sekunden begrenzt. Sprache manuell wählen oder die große Schaltfläche <strong>Automatic</strong> (zwei Spalten × zwei Reihen) für einen Versuch bei der nächsten Aufnahme gegenüber antippen. Mindestens fünf Sekunden sprechen; unsichere oder nicht unterstützte Ergebnisse führen zur manuellen Fahnenwahl. Erst Refresh erlaubt einen neuen Versuch. Keine Live-Transkription oder Sprechererkennung. Ziele ohne Sprachsynthese erhalten nur Text.</td>
</tr>
<tr>
<td>One shared model instance processes requests in a serial queue. Audio and results remain briefly in RAM, without conversation files. Each browser receives an isolated session, including when password protection is off.</td>
<td>Eine gemeinsame Modellinstanz verarbeitet Aufträge in einer seriellen Queue. Audio und Ergebnisse liegen kurzzeitig im RAM, ohne Gesprächsdateien. Jeder Browser erhält eine getrennte Sitzung, auch bei ausgeschaltetem Passwortschutz.</td>
</tr>
</table>

<table>
<tr><th width="50%">Operation and compact tests</th><th width="50%">Betrieb und kompakte Tests</th></tr>
<tr>
<td><pre><code>sudo systemctl status \
  kienzletranslate
sudo systemctl restart \
  kienzletranslate
sudo journalctl \
  -u kienzletranslate \
  --since today
python3 -m unittest discover \
  -s tests -p 'test_*.py'
python3 -m unittest \
  backend.tests.test_core
node --test tests/*.test.mjs
# Python dependencies required:
python3 -m unittest \
  backend.tests.test_api</code></pre></td>
<td><pre><code>sudo systemctl status \
  kienzletranslate
sudo systemctl restart \
  kienzletranslate
sudo journalctl \
  -u kienzletranslate \
  --since today
python3 -m unittest discover \
  -s tests -p 'test_*.py'
python3 -m unittest \
  backend.tests.test_core
node --test tests/*.test.mjs
# Python-Abhängigkeiten nötig:
python3 -m unittest \
  backend.tests.test_api</code></pre></td>
</tr>
<tr>
<td><a href="docs/TESTPLAN.md">Test plan</a> · <a href="docs/VERIFICATION.md">Verification</a> · <a href="docs/LIMITATIONS.md">Limitations</a> · <a href="docs/ARCHITECTURE.md">Architecture</a> · <a href="docs/CHANGELOG.md">Changes</a></td>
<td><a href="docs/TESTPLAN.md">Testplan</a> · <a href="docs/VERIFICATION.md">Prüfnachweise</a> · <a href="docs/LIMITATIONS.md">Grenzen</a> · <a href="docs/ARCHITECTURE.md">Architektur</a> · <a href="docs/CHANGELOG.md">Änderungen</a></td>
</tr>
</table>
