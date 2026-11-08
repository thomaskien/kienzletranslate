# Prüfstand — 08.11.2026

## Zielsystem

- Ubuntu 24.04.5 LTS, Python 3.12.3, NVIDIA RTX 3090 24 GB.
- NVIDIA-Treiber 580.178.04; PyTorch 2.6.0+cu124; Transformers 4.46.3.
- Ein kompletter Checkpoint `facebook/seamless-m4t-v2-large`, Revision
  `5f8cc790b19fc3f67a61c105133b20b34e3dcb76`, FP16.
- PHP 8.3-FPM, nginx, ein Uvicorn-Prozess; Modellport nur auf Loopback.

## Bestanden

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
