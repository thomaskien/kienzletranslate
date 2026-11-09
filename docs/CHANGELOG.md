# Änderungen

## v1.7 — 10.11.2026

- Die erste Automatic-Aufnahme wird auch bei unsicherer, zu kurzer oder fehlgeschlagener
  Sprachbestimmung zu Ihrer Sprache übersetzt und bei aktivierter Sprachausgabe gesprochen.
- Fahnenwahl ist anschließend nur für die Antwortsprache nötig. Übersetzung und
  laufende Sprachausgabe bleiben bei der Auswahl erhalten; kein erneutes Einsprechen.
- Ohne sichere Ausgangssprache entfällt nur das zusätzliche Originaltranskript.
  2×2-Schaltfläche und einmaliger Erkennungsversuch bis zum Refresh bleiben erhalten.

## v1.6.1 — 10.11.2026

- „Automatic“ belegt jetzt zwei Spalten und zwei Reihen statt einer ganzen Reihe;
  die Beschriftung ist mittig, die Fahnen stehen daneben. Gilt für Patientenwahl
  und linkes Sprachmenü. Erkennung und Refresh-Verhalten bleiben erhalten.
- Patch-Versionsnummer v1.6.1 auf ausdrücklichen Benutzerwunsch.

## v1.6 — 09.11.2026

- Standard-Audio-Vorlauf auf 0,25 Sekunden reduziert; bewusst gespeicherte Werte bleiben erhalten.
- „Automatic“ belegt eine volle Vier-Fahnen-Reihe unter „Häufig in Deutschland“.
  Genau eine patientenseitige Aufnahme wird per Whisper base auf der CPU geprüft.
  Erfolg setzt die Sprache und übersetzt dieselbe Aufnahme; sonst manuelle Fahnenwahl.
  Erst Refresh schaltet „Automatic“ wieder frei; Ihre Sprache und Mikrofon bleiben erhalten.
- GPU-Modell in eigenem Prozess: Speichervorprüfung, Vorladen nach Mikrofonfreigabe,
  Heartbeat alle 15 Sekunden, Entladen nach 90 Sekunden ohne Geräte oder fünf Minuten
  ohne Bedienung. Aktive Aufnahmen und Warteschlange schützen das Modell.
- Installer fragt Lade-/Entladeverhalten ab und installiert die CPU-Spracherkennung
  separat. Modellstart beim Booten standardmäßig aus.
- DE/EN-Uninstaller mit Vorschau, Bestätigungswort und getrennten Optionen für
  Konfiguration/CA/Backups und Modelle; diese bleiben standardmäßig erhalten.

## v1.5 — 09.11.2026

- Startreihenfolge korrigiert: zuerst „Ihre Sprache“ und Mikrofonfreigabe,
  danach die gegenüberliegende Sprachwahl, anschließend sofort gesprächsbereit.
- Bei fehlender Mikrofonfreigabe bleibt der erste Dialog geöffnet. Refresh
  und spätere Sprachänderungen erfordern weiterhin keine erneute Freigabe.

## v1.4 — 09.11.2026

- Zuerst Sprachauswahl auf der gegenüberliegenden Hälfte: gedrehte, scrollbare
  Fahnen mit Sprachname, immer vier nebeneinander. Alle 96 Sprachen bleiben
  verfügbar, häufige Sprachen zuerst.
- Das linke Sprachmenü öffnet dieselbe Auswahl für Änderungen im Gespräch.
- Refresh-Knopf auf der eigenen Seite startet die gegenüberliegende Sprachwahl
  erneut; eigene Sprache und Einstellungen bleiben erhalten.

## v1.3 — 09.11.2026

- Neutrale Bezeichnung „Ihre Sprache“ statt „Arzt-Sprache“ in allen
  18 Oberflächensprachen, Sprachmenüs und der aktuellen Dokumentation.
- Fahnenwahl, Sprachzuordnung und Audioverarbeitung unverändert.

## v1.2 — 09.11.2026

- Fahnenauswahl für alle 18 häufigen Oberflächensprachen; ein Tipp setzt zugleich
  die Arzt-Sprache unten. Die obere Gesprächssprache bleibt erhalten.
- Kompakter Startdialog mit kurzer Push-to-Talk-Erklärung, Fahnen und
  Mikrofonfreigabe. Vorlauf bleibt in den Einstellungen.
- Fahnenpiktogramme auch in den nativen Sprachmenüs; Layout für iPhone/iPad
  angepasst, Schreibrichtung arabischer, persischer und kurdischer Dialoge beachtet.
- README einschließlich Bildunterschriften zweispaltig: Englisch links,
  Deutsch rechts. Bilder bleiben über die volle Breite.
- Versionsfolge künftig in Schritten von 0,1.

## v1.1 — 09.11.2026

- Passwortschutz optional und bei Neuinstallation standardmäßig ausgeschaltet.
  Auf der bestehenden Installation ebenfalls ausgeschaltet. Getrennte Sitzungen,
  HTTPS und die Lizenzbestätigungen bleiben erhalten.
- Oberfläche zwischen Deutsch und Englisch umschaltbar, Auswahl lokal gespeichert
  und unabhängig von den Übersetzungssprachen.
- Zwei alphabetische Sprachgruppen: häufig in Deutschland verwendete Sprachen
  zuerst, übrige Sprachen darunter. Die erste Gruppe ist eine praktische Auswahl,
  keine behauptete statistische Rangfolge. Orientierung für die großen
  Haushaltssprachen: [Destatis, 17.02.2026](https://www.destatis.de/DE/Presse/Pressemitteilungen/Zahl-der-Woche/2026/PD26_08_p002.html),
  ergänzt um verbreitete Fremd- und Gesprächssprachen.
- Schriftgröße passt sich anhand der verfügbaren Fläche an, sodass der gesamte
  Original- und Übersetzungstext sichtbar bleibt, auch bei der 45/55-Aufteilung.

## Erste Version — 08.11.2026

PHP-PWA, lokale SeamlessM4T-v2-Pipeline, Push-to-Talk mit einstellbarem Vorlauf,
native Installation/Updates, lokale CA und iPad-Einrichtung.
