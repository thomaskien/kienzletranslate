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
| `/var/lib/kienzletranslate/model` | Separat geladene Modellgewichte |
| `/etc/kienzletranslate/config.json` | Konfiguration, Passwort-Hash, Dienstgeheimnisse |
| `/etc/kienzletranslate/tls` | Lokale CA, private Schlüssel und Serverzertifikat |
| `/root/kienzletranslate-access.json` | Aufrufadressen und gegebenenfalls erzeugtes Passwort |

Modellservice: `127.0.0.1:8765` (konfigurierbar), Bearer-Token ausschließlich
zwischen PHP und Python. Kein produktiver ungeschützter Modellport im LAN.
App: HTTPS, Cookie mit HttpOnly/Secure/SameSite=Strict und CSRF-Schutz.
Anmeldeversuche werden durch nginx begrenzt. Das gemeinsame Zugangspasswort ist
für kleine vertrauenswürdige Nutzergruppen gedacht; keine Benutzerverwaltung.

## iPad-Zertifikat

1. HTTP-Adresse mit gewähltem Port öffnen, etwa `http://10.0.83.140`.
2. DE/EN wählen, Modelllizenz erneut mit dem angezeigten Wort bestätigen.
3. Öffentliche CA herunterladen. Fingerabdruck unabhängig mit Installer-Ausgabe
   vergleichen, da der HTTP-Download selbst nicht authentifiziert ist.
4. Einstellungen → Profil geladen → Installieren.
5. Einstellungen → Allgemein → Info → Zertifikatsvertrauenseinstellungen →
   volles Vertrauen für „kienzletranslate Local CA“ einschalten.
6. HTTPS-Adresse öffnen, anmelden, zum Home-Bildschirm hinzufügen.

Nur das öffentliche Zertifikat wird bereitgestellt. Private Schlüssel dürfen
nicht auf iPads oder ins Git-Repository kopiert werden. Updates behalten die CA.
Ein täglicher systemd-Timer erneuert das 365 Tage gültige Serverzertifikat, sobald
weniger als 30 Tage verbleiben. Die CA selbst gilt zehn Jahre und erfordert dann
einen bewussten Austausch samt erneuter Vertrauensinstallation.

## Dienste und GPU

`systemctl status kienzletranslate` zeigt den Modellservice. Er startet zunächst
ohne geladene Gewichte, lädt bei erster Anfrage oder über die App-Einstellungen.
Entladen wird bei aktiver Verarbeitung/Warteschlange abgewiesen. In der App
Entladen ausführen, bevor andere speicherintensive GPU-Dienste manuell starten.
Ein universeller automatischer Wechselbetrieb ist nicht Bestandteil von v1.

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

## Update und Rückkehr

Neuen Quellstand beziehen, `sudo bash install.sh` ausführen und bestehende Werte
übernehmen. Aktive Anfragen können beim Dienstneustart abbrechen; Updates daher
zwischen Gesprächen durchführen. Vorherige Releases bleiben zunächst erhalten.
Ein fehlgeschlagener abschließender Gesundheitscheck löst einen Rückkehrversuch
zum vorherigen Quellstand und zur vorherigen Konfiguration aus. Paketinstallationen
sind davon nicht umfasst. Backups enthalten Geheimnisse und bleiben root-exklusiv.
