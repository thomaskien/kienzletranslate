# Grenzen und Betriebsbedingungen

- Kein medizinisch validiertes Produkt; keine Zusage klinisch ausreichender
  Übersetzungsqualität. Ausschließlich nichtkommerzieller technischer Prototyp.
- Zwei Gesprächssprachen; optional genau ein Erkennungsversuch für die Patientenseite.
  Eine sichere automatische Sprachzuordnung benötigt mindestens fünf Sekunden ab
  Sprachbeginn und ausreichend Sprache. Die Übersetzung zur bekannten eigenen Sprache
  erfolgt seit v1.7 auch ohne sichere Zuordnung. Manuelle Auswahl ist dann nur für die
  Antwortsprache nötig; das zusätzliche Originaltranskript entfällt. Stille/Geräusche
  können wie bei manueller Sprachwahl zu unzuverlässigen Modellausgaben führen.
  Modell-Scores garantieren keine korrekte Sprachzuordnung; eine erkannte Sprache
  kann über das linke Menü korrigiert werden. Nur Refresh gibt einen neuen Versuch frei.
- GPU-Inferenz seriell. Bis zu acht wartende Aufträge; neue Äußerung ersetzt
  ältere Ergebnisse derselben Sitzung. Bereits laufende GPU-Kernel werden zu Ende
  ausgeführt. Maximal 64 RAM-Ergebnisse, Löschung nach zehn Minuten oder Abmelden.
- Maximal 60 Sekunden inklusive Vorlauf; kurze Gesprächsbeiträge sind empfohlen.
  Textgenerierung auf 256 neue Tokens begrenzt. Sehr lange/komplexe Aussagen können
  entsprechend gekürzt werden; lange Aufnahmen werden bei Überschreitung verworfen.
- AudioWorklet-Blöcke werden anhand ihrer Samplepositionen geschnitten; die
  Zuordnung von Touchereignissen zur Audio-Uhr hängt von der Browserimplementierung
  ab. Tatsächliche iPad-Latenz und Aufnahmequalität müssen am Gerät geprüft werden.
- Browser-Echounterdrückung garantiert keine völlige Echofreiheit. Während
  Wiedergabe wird der Vorlauf verworfen; nach Unterbrechung fehlt dieser Vorlauf
  bewusst. Kopfhörer oder geringe Lautstärke können bei schwieriger Akustik helfen.
- Keine dauerhafte Gesprächsspeicherung, Exportfunktion oder Offline-Übersetzung
  auf dem iPad. Server und Netzwerk müssen erreichbar sein. Inferenz läuft nach
  der Einrichtung ohne externe Dienste; Installationen/Updates benötigen Internet.
- Die App vermeidet Gesprächsdaten auf Festplatte und in Logs. Betriebssystem-
  Swap, Crashdumps und administratives Debugging sind gesonderte Host-Themen.
- Kein automatischer Wechselbetrieb mit anderen GPU-Diensten. Das Modell startet
  nach einem Serverneustart ungeladen; konkurrierende Dienste können VRAM belegen.
- Standardmäßig direkter Zugang ohne Passwort; optional gemeinsames Zugangspasswort,
  keine Rollen/Rechteverwaltung. Passwortwechsel sollte
  mit Austausch von `session_secret` verbunden werden, um alte Sitzungen abzumelden.
