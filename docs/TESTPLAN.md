# Kompakte Abnahme

Ein kleiner automatisierter Kern, ein echter GPU-Lebenszyklus und ein kurzer
iPad-Durchlauf. Wiederholungen nur bei betroffenen Fehlerkorrekturen.

## Automatisch

- PCM-Ringpuffer: 0/250/1000/3000 ms, Wrap-around, Ausschnittgrenzen, Abbruch,
  native Samplerate im WAV. Generationsschutz und Sprachrichtung.
- Backend: WAV-Validierung, Sitzungsisolation, Löschung/TTL, überholte Anfragen,
  Entladen während Verarbeitung, authentifizierte API.
- Installer: DE/EN-Lizenzannahme und Ablehnung, Namen/Ports/Pfade, Webkonfiguration.
- v1.6: einmalige Automatic-Auswahl, manueller Rückfall, Refresh, neuer Vorlaufstandard;
  Heartbeat mehrerer Geräte, versteckte Seiten, Inaktivität, Aufnahme-/Queue-Schutz,
  Speichervorprüfung, Detektor-Schwellen und Uninstaller-Pfadsicherheit.
- v1.7: Übersetzung und Audio trotz unsicherer/fehlgeschlagener LID, Antwortsprache
  separat wählen; Ergebnis und Wiedergabe bei der Fahnenwahl erhalten.
- PHP-/Python-/JavaScript-Syntax und gezielter Diff-Review.

## Auf dem Zielserver

- Neuinstallation und ein Update mit Konfigurations-/CA-Erhalt.
- HTTP-Einrichtung mit erneuter Lizenzbestätigung, HTTPS-Zertifikatsprüfung,
  Anmeldung/CSRF, API-Sitzung und Erreichbarkeit.
- Ein Modell laden; kurze künstliche DE/EN-Aufnahmen übersetzen, Audio an/aus,
  einmal Ziel ohne Audioausgabe. Entladen und tatsächlichen VRAM prüfen,
  erneut laden/übersetzen. Testsprache aus demselben Seamless-Checkpoint erzeugt.
- v1.6: drei öffentliche Sprachaufnahmen durch CPU-Erkennung → GPU-Übersetzung,
  einschließlich Sprachausgabe; Stille/Kurzaufnahme zurückweisen. Echte 90-Sekunden-
  Entladefrist, Wiederladen durch Aktivität und vollständige GPU-Prozessfreigabe.
  Uninstaller ausschließlich im unverändernden Prüfmodus.
- v1.7: eine bisher unsicher erkannte Aufnahme trotzdem vollständig zu Deutsch
  übersetzen und WAV-Ausgabe prüfen; sichere Erkennung als kurzer Vergleich.
- Mehrclient-/Race-Verhalten im kleinen automatisierten Test; kein Dauerlasttest.

## Auf dem echten iPad — manuell

- Zertifikat installieren und vertrauen; App zum Home-Bildschirm hinzufügen.
- Zwei Sprachfelder, oberer Text gedreht, Controls aufrecht.
- Halten grün, Loslassen sofort schwarz; genau ein abgeschlossener Audioblock.
- Vorlauf an kurzem gesprochenem Satz prüfen; Sliderwert nach Neustart erhalten.
- Zweiter Finger, Abbruch/Appwechsel, Netzunterbrechung und erneute Freigabe.
- Sprachausgabe hören und durch neue Aufnahme unterbrechen; keine veraltete Anzeige.

Der reale iPad-Test kann nicht durch Desktop-Simulation als bestanden ersetzt
werden. Konkrete durchgeführte Prüfungen werden in `docs/VERIFICATION.md` festgehalten.
