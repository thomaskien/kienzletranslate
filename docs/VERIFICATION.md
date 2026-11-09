# Prüfstand — v1.3, 09.11.2026

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
