# Native Installation und Betrieb

## Voraussetzungen

- Ubuntu/Debian 64 Bit, Python 3, Administratorrechte, NVIDIA-GPU mit
  funktionierendem Treiber. Der Installer ersetzt keinen NVIDIA-Treiber.
- Internet für apt, Python-Abhängigkeiten und den einmaligen Modelldownload.
- Lokales Netz mit Verbindung vom iPad zum Server; feste IP empfohlen.
- Root-CA pro Installation. DNS-Namen müssen separat im lokalen DNS auflösbar sein.
  Ein bloßes `*` als Zertifikatsname ist nicht erlaubt.

`sudo bash install.sh` führt Neuinstallation oder Aktualisierung durch. Die
Sprachabfrage steht am Anfang. Ohne exakte Lizenzbestätigung entstehen keine
Systemänderungen. Der Installer prüft Portkollisionen, sichert bestehenden Stand,
verwendet ein Python-venv und erstellt einen eigenen PHP-FPM-Pool.

Standardpfade:

| Pfad | Inhalt |
| --- | --- |
| `/opt/kienzletranslate/current` | Aktive Veröffentlichung als Symlink |
| `/opt/kienzletranslate/releases` | Quellstände |
| `/opt/kienzletranslate/backups` | Vorherige Konfiguration/CA, nur root |
| `/opt/kienzletranslate/venv` | Isolierte Modell-Abhängigkeiten |
| `/opt/kienzletranslate/lid-venv` | Isolierte CPU-Spracherkennungs-Abhängigkeiten |
| `/var/lib/kienzletranslate/model` | Separat geladene Modellgewichte |
| `/var/lib/kienzletranslate/lid-model` | Gepinntes CPU-Spracherkennungsmodell |
| `/etc/kienzletranslate/config.json` | Konfiguration, Passwort-Hash, Dienstgeheimnisse |
| `/etc/kienzletranslate/tls` | Lokale CA, private Schlüssel und Serverzertifikat |
| `/root/kienzletranslate-access.json` | Aufrufadressen und gegebenenfalls erzeugtes Passwort |

Modellservice: `127.0.0.1:8765` (konfigurierbar), Bearer-Token ausschließlich
zwischen PHP und Python. Kein produktiver ungeschützter Modellport im LAN.
App: HTTPS, Cookie mit HttpOnly/Secure/SameSite=Strict und CSRF-Schutz.
Passwortschutz ist bei neuen Installationen standardmäßig ausgeschaltet. Die App
öffnet dann direkt und vergibt getrennte signierte Browsersitzungen. Der Installer
kann den Schutz optional einschalten (`password_required: true`); bestehende
Einstellungen bleiben bei Updates erhalten. Anonyme Sitzungen berechtigen nach
späterem Einschalten des Passwortschutzes nicht zum Zugang. Anmeldeversuche werden
durch nginx begrenzt. Es gibt keine Benutzer-/Rollenverwaltung.

## iPad-Zertifikat

1. HTTP-Adresse mit gewähltem Port öffnen, etwa `http://10.0.83.140`.
2. DE/EN wählen, Modelllizenz erneut mit dem angezeigten Wort bestätigen.
3. Öffentliche CA herunterladen. Fingerabdruck unabhängig mit Installer-Ausgabe
   vergleichen, da der HTTP-Download selbst nicht authentifiziert ist.
4. Einstellungen → Profil geladen → Installieren.
5. Einstellungen → Allgemein → Info → Zertifikatsvertrauenseinstellungen →
   volles Vertrauen für „kienzletranslate Local CA“ einschalten.
6. HTTPS-Adresse öffnen, nur bei aktiviertem Passwortschutz anmelden und zum
   Home-Bildschirm hinzufügen.

Nur das öffentliche Zertifikat wird bereitgestellt. Private Schlüssel dürfen
nicht auf iPads oder ins Git-Repository kopiert werden. Updates behalten die CA.
Ein täglicher systemd-Timer erneuert das 365 Tage gültige Serverzertifikat, sobald
weniger als 30 Tage verbleiben. Die CA selbst gilt zehn Jahre und erfordert dann
einen bewussten Austausch samt erneuter Vertrauensinstallation.

Der Installer prüft vor Paketinstallation und Downloads den freien Platz der
betroffenen Dateisysteme mit Reserve. Die Prüfung ist eine Mindestprüfung und
keine Zusage, dass eine GPU mit 8 GB Speicher für das Hauptmodell ausreicht.
Das verpflichtende CPU-Modell `Systran/faster-whisper-base` wird in Revision
`ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66` unter MIT-Lizenz installiert. Es
verwendet ein eigenes venv ohne GPU-Torch und setzt keine Benchmark-Umgebung
voraus.

## Dienste und GPU-Konfiguration

`systemctl status kienzletranslate` zeigt den Backenddienst. GPU-Modell und
CPU-Spracherkennung laufen in getrennten Kindprozessen des Backends. Standardmäßig
wird das GPU-Modell nicht beim Serverstart, aber bei Nutzung der Webapp geladen.
Ohne verbundene Geräte wird es nach 90 Sekunden entladen; trotz geöffneter App
nach fünf Minuten Inaktivität. Der feste Heartbeat beträgt 15 Sekunden. Entladen
wird bei aktiver Verarbeitung/Warteschlange abgewiesen.

Die Werte `model_autoload`, `model_load_on_use`, `model_auto_unload`,
`model_disconnect_seconds` (30–3600), `model_idle_seconds` (60–86400) und
`model_min_free_mib` (mindestens 1024, Standard 8192) stehen in der Konfiguration.
Der letzte Wert ist über `--answers` konfigurierbar, wird aber nicht zusätzlich
interaktiv abgefragt. `lid_python` verweist auf das separate LID-venv;
`lid_model_path` ist wie der Hauptmodellpfad über `--answers` anpassbar.

Für den ersten Einsatz wurden auf Benutzerauftrag konkurrierende GPU-Dienste
angehalten, ohne ihre Autostart-Konfiguration zu ändern. Welche Dienste das sind,
steht im Betriebsnachweis. Der generische Installer stoppt keine fremden Dienste.

## Automatisierte Installation

Für ausdrücklich autorisierte Administration unterstützt der Installer
`--answers /geschuetzter/pfad.json` oder `--answers -` (JSON über stdin).
`language` und `license_acceptance` müssen ausdrücklich enthalten sein, etwa
`{"language":"de","license_acceptance":"AKZEPTIEREN"}`.
Weitere Schlüssel entsprechen `deploy/install.py`. Kennwörter nicht in
Shellargumenten oder ungeschützten Dateien ablegen. `--check` validiert die
Eingaben ohne Installation oder Systemänderungen.

## Deinstallation

`sudo bash uninstall.sh` startet den deutsch/englischen Uninstaller. Er zeigt
vorher konkret alle verwalteten Dienste und Pfade und nimmt erst nach Eingabe von
`DEINSTALLIEREN` beziehungsweise `UNINSTALL` Änderungen vor. Standardmäßig
werden App, venvs und ausschließlich eigene nginx-, PHP-, tmpfiles- und
systemd-Dateien entfernt. Konfiguration, lokale CA, Backups sowie beide
Modellcaches bleiben erhalten. Fremde Dienste, Systempakete, GPU-Treiber und
Benchmarkordner werden nicht entfernt.

Konfiguration/CA/Backups und Modelle können in zwei getrennten Fragen explizit
zur Entfernung ausgewählt werden. Verdächtige Pfade, Symlinks oder Dateien ohne
kienzletranslate-Marker führen vor der ersten Änderung zum Abbruch. Für einen
reproduzierbaren Plan unterstützt der Uninstaller `--answers DATEI` (oder `-`)
mit `language`, `remove_data` und `remove_models`. `--check` und `--dry-run`
validieren und zeigen den Plan ohne Änderungen; auf einem echten Server sollte
so zunächst geprüft werden.

## Update und Rückkehr

Neuen Quellstand beziehen, `sudo bash install.sh` ausführen und bestehende Werte
übernehmen. Aktive Anfragen können beim Dienstneustart abbrechen; Updates daher
zwischen Gesprächen durchführen. Vorherige Releases bleiben zunächst erhalten.
Ein fehlgeschlagener abschließender Gesundheitscheck löst einen Rückkehrversuch
zum vorherigen Quellstand und zur vorherigen Konfiguration aus. Paketinstallationen
sind davon nicht umfasst. Backups enthalten Geheimnisse und bleiben root-exklusiv.
