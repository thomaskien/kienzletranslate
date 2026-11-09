# kienzletranslate v1.2

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
<tr><th width="50%">New in v1.2</th><th width="50%">Neu in v1.2</th></tr>
<tr>
<td>Tap a flag to select both the interface language and the doctor's language (bottom speaking area). All 18 frequently used languages are available, with native language names. The compact start dialog explains push-to-talk in one sentence. Flags also appear in the language menus.</td>
<td>Ein Tipp auf die Fahne stellt gleichzeitig die Oberfläche und die Arzt-Sprache (untere Sprechfläche) ein. Alle 18 häufigen Sprachen sind mit ihren Eigennamen verfügbar. Der kompakte Startdialog erklärt Push-to-Talk in einem Satz. Fahnen erscheinen auch in den Sprachmenüs.</td>
</tr>
<tr>
<td>German, English, Turkish, Arabic, Russian, Ukrainian, Polish, Romanian, Italian, Bulgarian, Croatian, Bosnian, Serbian, Kurdish (Sorani), Persian, Greek, French and Spanish. Flags are visual shortcuts; the language name identifies the choice.</td>
<td>Deutsch, Englisch, Türkisch, Arabisch, Russisch, Ukrainisch, Polnisch, Rumänisch, Italienisch, Bulgarisch, Kroatisch, Bosnisch, Serbisch, Kurdisch (Sorani), Persisch, Griechisch, Französisch und Spanisch. Fahnen dienen als Orientierung; der Sprachname bezeichnet die Auswahl.</td>
</tr>
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
<li>Tap your flag: this sets the interface and the doctor's language at the bottom. The top language remains separate; the defaults are Ukrainian at the top and German at the bottom.</li>
<li>Enable the microphone. Hold your speaking area, speak, then release to translate. Green means recording; processing starts on release.</li>
<li>The original text appears on the speaker's side and the translation opposite. The upper conversation text is rotated; controls stay upright. Text shrinks to fit the available area.</li>
<li>Toggle translated speech with the speaker button. A new recording interrupts playback.</li>
</ol></td>
<td><ol>
<li>Eigene Fahne antippen: Das setzt die Oberfläche und die Arzt-Sprache unten. Die obere Sprache bleibt separat; voreingestellt sind Ukrainisch oben und Deutsch unten.</li>
<li>Mikrofon aktivieren. Eigene Sprechfläche gedrückt halten, sprechen und zum Übersetzen loslassen. Grün bedeutet Aufnahme; die Verarbeitung beginnt beim Loslassen.</li>
<li>Der Originaltext erscheint auf der Sprecherseite, die Übersetzung gegenüber. Der obere Gesprächstext ist gedreht, Bedienelemente bleiben aufrecht. Text wird passend zur verfügbaren Fläche verkleinert.</li>
<li>Übersetzte Sprachausgabe über den Lautsprecher umschalten. Eine neue Aufnahme unterbricht die Wiedergabe.</li>
</ol></td>
</tr>
<tr>
<td>Frequently used languages in Germany appear first, followed by other languages; both groups are alphabetically sorted. Settings include the same flags, audio pre-roll (0–3 seconds in 250 ms steps, default 1 second), and model loading/unloading. Preferences are saved locally.</td>
<td>Häufig in Deutschland verwendete Sprachen stehen zuerst, weitere darunter; beide Gruppen sind alphabetisch sortiert. Die Einstellungen enthalten dieselben Fahnen, den Audio-Vorlauf (0–3 Sekunden in 250-ms-Schritten, Standard 1 Sekunde) und das Laden/Entladen des Modells. Einstellungen werden lokal gespeichert.</td>
</tr>
<tr>
<td>The microphone stays active in the foreground for the temporary local pre-roll buffer. No audio is transmitted while idle. Recordings are limited to 60 seconds including pre-roll. Language selection is manual; there is no live transcription or automatic speaker/language detection. Targets without speech synthesis receive text only.</td>
<td>Das Mikrofon bleibt im Vordergrund für den flüchtigen lokalen Vorlaufpuffer geöffnet. Im Leerlauf werden keine Audiodaten übertragen. Aufnahmen sind einschließlich Vorlauf auf 60 Sekunden begrenzt. Die Sprachwahl erfolgt manuell; keine Live-Transkription oder automatische Sprecher-/Spracherkennung. Ziele ohne Sprachsynthese erhalten nur Text.</td>
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
