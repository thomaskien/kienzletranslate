# Kompakte Abnahme

Ein kleiner automatisierter Kern, ein echter GPU-Lebenszyklus und ein kurzer
iPad-Durchlauf. Wiederholungen nur bei betroffenen Fehlerkorrekturen.

## Automatisch

- PCM-Ringpuffer: 0/250/1000/3000 ms, Wrap-around, Ausschnittgrenzen, Abbruch,
  native Samplerate im WAV. Generationsschutz und Sprachrichtung.
- Backend: WAV-Validierung, Sitzungsisolation, Löschung/TTL, überholte Anfragen,
  Entladen während Verarbeitung, authentifizierte API.
- Installer: DE/EN-Lizenzannahme und Ablehnung, Namen/Ports/Pfade, Webkonfiguration.
- PHP-/Python-/JavaScript-Syntax und gezielter Diff-Review.

## Auf dem Zielserver

- Neuinstallation und ein Update mit Konfigurations-/CA-Erhalt.
- HTTP-Einrichtung mit erneuter Lizenzbestätigung, HTTPS-Zertifikatsprüfung,
  Anmeldung/CSRF, API-Sitzung und Erreichbarkeit.
- Ein Modell laden; kurze künstliche DE/EN-Aufnahmen übersetzen, Audio an/aus,
  einmal Ziel ohne Audioausgabe. Entladen und tatsächlichen VRAM prüfen,
  erneut laden/übersetzen. Testsprache aus demselben Seamless-Checkpoint erzeugt.
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
