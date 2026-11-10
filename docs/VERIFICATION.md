# Prüfstand — v1.8, 10.11.2026

## Gezielte Prüfung der Änderungen in v1.8

- Vier i18n-Tests bestanden: vollständige Wörterbücher aller 18 Oberflächensprachen
  einschließlich neuem Patientenhinweis. PHP-/JavaScript-/Python-Syntax und Diff geprüft.
- Browser-Fixture bei 320 × 568 und 744 × 1133: alle 18 Hinweise vollständig sichtbar,
  mit Sternchen getrennt und um 180° gedreht. Arabisch, Sorani und Persisch sind
  separat als RTL ausgezeichnet. Kein horizontaler Überlauf; Schrift passt sich an.
- Nach Automatic erscheint der Hinweis; manuelle Sprachwahl blendet ihn aus.
  Halten/Loslassen führt weiterhin zur Übersetzung. Bei simulierter unsicherer Sprache
  erscheinen Fahnen ohne Automatic, deutscher Text und gestartete WAV-Wiedergabe.
  Eigene Sprache und Mikrofonfreigabe bleiben erhalten; Refresh erlaubt den Hinweis erneut.
- Mikrofon/Modell in der UI-Fixture simuliert. Backend unverändert, daher kein
  erneuter GPU- oder Benchmarklauf. Die neuen Texte sind nicht muttersprachlich lektoriert.
- v1.8 auf dem Zielserver aktiviert. HTTPS-Assets, sichtbare/API-Version und
  unveränderte Backend-PID geprüft; Zugangseinstellungen und Root-CA erhalten.

## Gezielte Prüfung der Änderungen in v1.7

- Neun gezielte Backendprüfungen bestanden, einschließlich Übersetzung der gleichen
  Aufnahme mit source=None bei Abstention, fehlendem/werfendem Detektor, verfügbarer
  Sprachausgabe und Sitzungstrennung. Vier i18n-Tests für alle 18 Oberflächensprachen
  sowie Syntax-/Diffprüfungen bestanden. Separates Sol-Review ohne konkrete Findings.
- Browser-Fixture bei 320 × 568 und 744 × 1133: Übersetzung unten sichtbar, Fahnen
  oben ohne Automatic und ohne alte Vorauswahl. Wiedergabe startet trotz unsicherer
  Erkennung. Manuelle Wahl (Französisch/Ukrainisch) erhält Text und laufende Ausgabe;
  eigene Sprache bleibt Deutsch. Vor der Wahl wird keine Antwortaufnahme gestartet.
- Kein horizontaler Überlauf, Übersetzung vollständig sichtbar. Refresh stellt
  Automatic wieder her. Mikrofonaufnahme und Modellresultat simuliert; der Browser
  startet tatsächlich einen synthetischen WAV-Puffer über den normalen Web-Audio-Pfad.

- Drei API-Integrationstests auf dem Zielserver bestanden, einschließlich kompletter
  Antwort mit Text und abrufbarem Audio bei Abstention.
- Echte HTTPS-Prüfung mit denselben zwei öffentlichen FLEURS-Aufnahmen wie zuvor:
  Ukrainisch blieb bei der LID unsicher, lieferte jetzt trotzdem deutschen Text und
  7,98 s gültige WAV-Ausgabe; Antwortsprache separat erforderlich, Originaltranskript
  leer. Gesamtdauer 9,688 s einschließlich kaltem GPU-/CPU-Modellstart.
  Französisch sicher erkannt, Originaltext/Übersetzung und 9,94 s WAV-Ausgabe vorhanden;
  Gesamtdauer 2,295 s. Funktionsnachweis, keine neue Bewertung der Übersetzungsqualität.
- v1.7 aktiviert, HTTPS-Dateien und Version abgeglichen; Einstellungen, deaktivierter
  Passwortschutz und CA erhalten. Nur der eigene Backenddienst neu gestartet.
  Die eigene Testsitzung anschließend gelöscht; keine fremden Sitzungen verändert.

## Gezielte Prüfung der Änderungen in v1.6.1

- Browserprüfung bei 320 × 568 und 744 × 1133: „Automatic“ belegt zwei Spalten
  und zwei Reihen, sowohl in der gedrehten Patientenwahl als auch im linken Menü.
  Die vier angrenzenden Fahnen verteilen sich auf die beiden übrigen Spalten.
- Beschriftung vollständig sichtbar, kein horizontaler Überlauf; beide Auswahlen
  bleiben scrollbar. Antippen und Wiederherstellen über Refresh geprüft.
- PHP-/JavaScript-/Python-Syntax und Diff geprüft. Nur Layout und Versionsangaben
  geändert; Mikrofon im Browser simuliert, kein erneuter Modell- oder Benchmarklauf.
- v1.6.1 auf dem Zielserver aktiviert; HTTPS-Assets, sichtbare Version und API-Version
  geprüft. PHP für den neuen Releasepfad sanft neu geladen; Modellprozess/PID,
  Zugangseinstellungen und Root-CA bleiben erhalten.

## Gezielte Prüfung der Änderungen in v1.6

- 16 JavaScript-Tests bestanden, einschließlich einmaliger Automatik und 250-ms-Standard.
- 8 neue Backendprüfungen: mehrere Geräte, ausbleibender Heartbeat, Inaktivität,
  Aufnahmeschutz, automatische Annahme/Rückfall, Sitzungstrennung und GPU-Speichermangel.
  Die bestehenden 6 Backend-Kerntests bestanden ebenfalls.
- UI-Fixture bei 320 × 568 und 744 × 1133: Automatic direkt unter der Überschrift,
  volle Vier-Spalten-Breite; Erfolg setzt Französisch und zeigt das Übersetzungsergebnis.
  Fehlschlag entfernt Automatic aus beiden Auswahlen; nur Refresh stellt es wieder her.
  Eigene Sprache und Mikrofonfreigabe bleiben erhalten. Mikrofon/Erkennung im Browser
  simuliert; dies ist keine erneute Hardware-Abnahme am echten iPad.

- Installer: 7 Tests, Uninstaller: 7 Tests einschließlich tatsächlichem Entfernen
  in einem isolierten temporären Verzeichnis mit simulierten Systembefehlen;
  Konfiguration/Modelle bleiben standardmäßig erhalten, unbekannte Dateien immer.
- Zwei API-Integrationstests auf dem Server bestanden, einschließlich Heartbeat-
  Eingabeprüfung, Authentifizierung und Ablehnung von Entladen während Aufnahme.
  Der vorhandene PHP-Sitzungstest und die Syntaxprüfungen bestanden ebenfalls.
- Vollständiges Update mit dem v1.6-Installer: separates CPU-venv und gepinnter
  Whisper-base-Download erfolgreich. Ports, Zugangseinstellungen, Geheimnisse und
  Root-CA erhalten. Backend startet ohne GPU-Modell; kein Server-Reboot nötig.
- Echte HTTPS-Kette mit drei zuvor nicht für LID verwendeten FLEURS-Aufnahmen:
  Französisch nach 5-s-Präfix erkannt, gleiche vollständige Aufnahme übersetzt und
  WAV-Sprachausgabe erzeugt (3,845 s gesamte Anfrage, einschließlich kaltem CPU-Worker).
  Ukrainisch und Persisch in dieser kleinen Prüfung bewusst als unsicher abgelehnt.
  Sechs Sekunden Stille und zwei Sekunden Audio führen ebenfalls zur Fahnenwahl.
  Keine neue allgemeine Genauigkeitsmessung und kein erneutes Schwellentuning.
- Tatsächlicher Heartbeat-Ausfall: Entladen nach 91,359 s. GPU-Gesamtbelegung
  vor Laden 65 MiB, geladen 4792 MiB, nach Verarbeitung 5224 MiB, nach Entladen
  wieder 65 MiB. Laden dauerte 8,051 s. Heartbeat ohne Aktivität lädt nicht wieder;
  neue Aktivität lädt erfolgreich, anschließendes Entladen ergibt erneut 65 MiB.
- Uninstaller auf der echten Installation ausschließlich mit `--check` geprüft;
  dort keine Deinstallation ausgeführt. Modellservice bleibt im Leerlauf entladen.

## Gezielte Prüfung der Änderungen in v1.5

- 14 JavaScript-Tests bestanden; PHP-/JavaScript-Syntax und Diff geprüft.
- Startablauf bei 320 × 568 und 744 × 1133 Pixeln im Browser geprüft: zuerst
  „Ihre Sprache“ und Mikrofon, dann das gedrehte Patientenraster mit vier Spalten.
  Nach der Sprachwahl schließen alle Auswahldialoge ohne weitere Bestätigung.
- Simulierte fehlgeschlagene Mikrofonfreigabe hält den ersten Dialog geöffnet;
  die Patientenwahl erscheint erst nach erfolgreicher Aktivierung.
- Refresh öffnet ausschließlich die Patientenwahl. Eigene Sprache und Oberfläche
  Englisch bleiben erhalten; Wechsel von Französisch zu Polnisch führt direkt
  zurück zur Gesprächsoberfläche ohne erneuten Mikrofondialog.
- Lokale UI-Fixture: Mikrofonaktivierung simuliert, keine tatsächliche Aufnahme.
  Audio-Core und Modellcode unverändert; kein erneuter vollständiger GPU-Test.

- v1.5 auf dem Zielserver aktiviert und über HTTPS geprüft. Frontend-Dateien
  stimmen mit dem Release überein; Modellprozess weiterhin `ready` mit PID 178770.
  Konfiguration und CA unverändert, Passwortschutz weiterhin ausgeschaltet.

## Gezielte Prüfung der Änderungen in v1.4

- 14 JavaScript-Tests bestanden; PHP-/JavaScript-Syntax und Diff geprüft.
- Browserprüfung bei 320 × 568 und 744 × 1133 Pixeln: beide Sprachkataloge
  enthalten dieselben 96 Optionen in derselben Reihenfolge, immer vier Spalten.
  Das Start-Raster ist um 180° gedreht, der Dialog vom linken Menü bleibt aufrecht.
- Scrollen im Raster verändert die Scrollposition, ohne Aufnahme oder Fehlermeldung
  auszulösen. Vertikales Touch-Panning ist auf Scrollfläche und Sprechflächen-Vorfahren
  erlaubt. Sprachkacheln bleiben auch auf 320 Pixeln mindestens 44 Pixel breit.
- Erste Auswahl öffnet anschließend den Mikrofon-/Eigene-Sprache-Dialog. Spätere
  Änderungen über das linke Menü und den Refresh-Knopf öffnen ihn nicht erneut.
  Geprüft mit Französisch, Polnisch und Japanisch, einschließlich seltenerer Sprachen.
- Refresh öffnet das obere Raster am Listenanfang. Eigene Sprache Deutsch,
  Oberfläche Deutsch und Vorlauf 1000 ms bleiben erhalten. Schließen ohne Auswahl
  behält die Sprache und gibt den Fokus zurück; erneutes Öffnen der App zeigt
  die erste Sprachwahl erneut mit gespeicherter Vorauswahl.
- Der Browserdurchlauf nutzt eine lokale UI-Fixture ohne tatsächliche Audioaufnahme;
  das Durchlaufen des Mikrofonknopfs ist darin simuliert. Audio-Core und Modellcode
  unverändert, kein erneuter vollständiger GPU-Test.
- v1.4 auf dem Zielserver aktiviert und über HTTPS geprüft. Alle Frontend-Dateien
  stimmen mit dem Release überein; Modellprozess unverändert mit PID 178770 und
  Status `ready`. Konfiguration und CA bleiben erhalten.

## Gezielte Prüfung der Änderungen in v1.3

- Bezeichnung „Ihre Sprache“ in Startdialog, Einstellungen und unterem
  Sprachmenü, in allen 18 Oberflächensprachen neutral übersetzt.
- Drei i18n-Tests bestanden; PHP-Syntax und Diff geprüft.
- Kurzer Browsercheck bei 390 × 844 und 744 × 1133 Pixeln: neue Beschriftung,
  18 Fahnen und erreichbarer Mikrofonknopf, kein horizontaler Überlauf.
- Keine Änderungen an Sprachzuordnung, Layout oder Audio-/Modellverarbeitung.

## Gezielte Prüfung der Änderungen in v1.2

- 13 JavaScript-Tests bestanden, darunter vollständige Wörterbücher für alle
  18 Oberflächensprachen mit je 86 Einträgen und unveränderten Platzhaltern,
  96 erhaltene Sprachoptionen sowie die Zuordnung Fahne → Arzt-Sprache.
  Die 5 Python-/PHP-Grenztests bestanden ebenfalls.
- Browserprüfung mit lokaler API-Fixture bei 320 × 568, 390 × 844 und
  744 × 1133 Pixeln. Startdialog mit 18 Fahnen, Mikrofonknopf erreichbar,
  vier bzw. sechs Spalten, kein horizontaler Überlauf.
- Französisch, Arabisch, Sorani, Deutsch und Englisch über Fahnen gewechselt.
  Untere Arzt-Sprache passt sich an, obere Sprache bleibt erhalten; Auswahl
  bleibt nach erneutem Öffnen bestehen. Dasselbe Verhalten im Einstellungsmenü.
- RTL-Dialoge und weiterhin feste Gesprächsflächen geprüft. Beide nativen
  Sprachfelder enthalten 96 Optionen mit Fahnen. Vollständige Textdarstellung
  auch auf kleinster Breite ohne Rundungsbeschnitt bestätigt.
- README: acht zweispaltige Text-/Beschriftungsbereiche, Englisch links und
  Deutsch rechts; beide Bilder laden außerhalb der Tabellen über die volle Breite.
- Audio-Pipeline und Modellcode unverändert. Kein erneuter vollständiger GPU-Test.
  Die neuen Oberflächentexte sind technisch geprüft, aber nicht muttersprachlich
  lektoriert; insbesondere bei Sorani können stilistische Korrekturen folgen.
- v1.2 auf dem Zielserver aktiviert, HTTPS und alle neuen Frontend-Dateien
  geprüft. Modellservice blieb ohne Neustart im Status `ready` (PID 178770).
  CA und sämtliche Konfiguration außer der Versionsnummer unverändert;
  Passwortschutz bleibt ausgeschaltet.

## Rückmeldung aus dem Betrieb

Der Nutzer bestätigt am 09.11.2026, dass die App auf iPad und iPhone sehr gut
läuft. Die früher offene praktische Rückmeldung zum Gerätebetrieb liegt damit
vor; sie ist keine Einzelabnahme aller unten aufgeführten Audio-Randfälle.

## Gezielte Prüfung der Änderungen in v1.1

- 12 JavaScript-Tests und 5 Python/PHP-Grenztests bestanden: vorhandene
  Aufnahme-/Frontendlogik, DE/EN-Wörterbücher, vollständige und alphabetische
  Sprachgruppen, Installer-Eingaben und optionale Passwortsitzungen.
- Passwortfreier Zugang am echten HTTPS-Server: getrennte und stabile Sitzungen
  für zwei Browser, Secure/HttpOnly-Cookies und CSRF-Abweisung bestätigt.
  Eine offene Sitzung wird beim Einschalten des Passwortschutzes ungültig.
- Browserprüfung mit lokaler API-Fixture bei 744 × 1133 und 1133 × 744 Pixeln:
  Texte mit rund 1500 Zeichen bleiben vollständig innerhalb der Flächen,
  auch mit Aufnahmesymbol in der aktiven 45-Prozent-Fläche.
- DE/EN-Wechsel übersetzt Dialog und beide Sprachgruppen, behält die
  ausgewählten Übersetzungssprachen und Ergebnistexte bei und bleibt nach
  erneutem Öffnen erhalten. Alle 96 Modellsprachen sind auswählbar.
- Update auf dem Zielserver mit dem v1.1-Installer erfolgreich. Root-CA,
  Ports, Servername, Sitzungs-/Backendgeheimnisse und deaktivierter Passwortschutz
  blieben erhalten. Danach HTTPS, Sitzungsisolation, CSRF, ausgelieferte
  Frontenddateien und Modellservice erneut geprüft; Modellstatus `ready`.
- Die unveränderte Modellpipeline wurde für diese Oberfläche nicht erneut
  durch den vollständigen GPU-Test geschickt; dessen Ergebnisse stehen unten.

## Zielsystem

- Ubuntu 24.04.5 LTS, Python 3.12.3, NVIDIA RTX 3090 24 GB.
- NVIDIA-Treiber 580.178.04; PyTorch 2.6.0+cu124; Transformers 4.46.3.
- Ein kompletter Checkpoint `facebook/seamless-m4t-v2-large`, Revision
  `5f8cc790b19fc3f67a61c105133b20b34e3dcb76`, FP16.
- PHP 8.3-FPM, nginx, ein Uvicorn-Prozess; Modellport nur auf Loopback.

## Grundversion: bestanden am 08.11.2026

- 10 dependency-free JavaScript-Tests: Vorlaufgrenzen, Wrap-around,
  Abbruch/Release, Sample-Uhr, WAV-Samplerate, Generationsschutz, Sprachrichtung,
  UUIDs und Service-Worker-Ausschluss von Gesprächsdaten.
- 6 Backend-Kerntests: Audioformat, Sitzungsisolation, Löschung/TTL,
  überholte Verarbeitung und verspätete Uploads, Entladen während Verarbeitung.
- 1 API-Integrationstest mit Testmodell: Authentifizierung, Uploadprüfung,
  Sitzungsisolation und Löschung.
- 3 Installer-Tests: DE/EN-Lizenzannahme/-ablehnung, ungültige Eingaben,
  alternative Ports und Upload-Konfiguration.
- Syntaxprüfungen für PHP/Python/JavaScript sowie Diff-Review.
- Echter GPU-Zyklus mit künstlicher Sprache aus demselben Checkpoint:
  Deutsch → Englisch ohne Audio; Englisch → Deutsch mit Audio;
  Englisch → Griechisch mit transparentem Text-Fallback; entladen, erneut laden
  und nochmals Deutsch → Englisch.
- HTTPS mit geprüfter CA-Kette und IP-SAN; HTTP-Einrichtung erfordert exaktes
  Bestätigungswort vor dem CA-Download; Anmeldung mit Secure/HttpOnly-Cookie;
  CSRF-Abweisung; Laden/Entladen über PHP; vollständige WAV-Anfrage über HTTPS,
  Ergebnisabfrage und Sitzungslöschung. Diese Transportprüfung verwendet kurze
  künstliche Stille, die Sprachprüfung separat die oben genannten gesprochenen Sätze.
- Neuinstallation und Update auf dem Zielserver. Nach Update blieben Passwort,
  Backend-/Sitzungsgeheimnisse, Ports und Root-CA unverändert. HTTPS und Anmeldung
  anschließend erneut erfolgreich.
- Desktop-Layoutprüfung bei 744 × 1133 Pixeln mit lokaler API-Fixture:
  zwei Sprachfelder, gedrehter oberer Text, Vorlauf standardmäßig 1,0 s,
  Einstellungsdialog. HTTP-Einrichtungsseite am echten Server im Browser geprüft.

## Kleine Messung, keine Leistungszusage

| Messpunkt | Ergebnis |
| --- | --- |
| Laden | 5,958 s |
| NVIDIA-Speicher vor Laden | 66 MiB |
| NVIDIA-Speicher nach Laden | 4792 MiB |
| NVIDIA-Speicher nach Entladen | 414 MiB |
| Deutsch → Englisch, 3,3 s Testaudio | ASR 0,451 s + Übersetzung 0,387 s |
| Englisch → Deutsch mit Audio, 2,42 s Testaudio | ASR 0,412 s + Übersetzung/Audio 0,452 s |

Der verbleibende Speicher nach Entladen gehört unter anderem zum CUDA-Kontext;
die Modellgewichte werden freigegeben. Nach Beenden des Testprozesses beziehungsweise
Neustart des ungeladenen Dienstes lagen etwa 65 MiB Gesamtnutzung vor.
Diese kurzen synthetischen Sätze ersetzen keinen Qualitätsvergleich an natürlicher
Sprache oder einen Mehrbenutzer-Lasttest.

## Noch am echten iPad zu prüfen

Root-CA-Installation und Vertrauen, Home-Screen-Modus, echte Mikrofonfreigabe,
Halten/Loslassen, Wiedergabe und Unterbrechung, Appwechsel und Vorlauf in realer
Akustik. Der Desktop-Layoutcheck ist kein bestandener iPad-Audiotest.

## Angehaltene GPU-Dienste

Auf ausdrücklichen Benutzerauftrag gestoppt und ausgeschaltet belassen;
Autostart jeweils weiterhin `enabled`:

- `kienzledoku-commander.service`
- `kienzlefon-ai-asr-backend.service`
- `kienzlefon-kokoro-tts.service`
- `kienzlefon-ai-diarization.service`

Der generische Installer verändert diese Dienste nicht. Ein automatischer
Wechselbetrieb ist für später zurückgestellt.
