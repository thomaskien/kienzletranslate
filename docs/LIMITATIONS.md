# Grenzen der ersten Version

- Kein medizinisch validiertes Produkt; keine Zusage klinisch ausreichender
  Übersetzungsqualität. Ausschließlich nichtkommerzieller technischer Prototyp.
- Zwei manuell ausgewählte Sprachen. Automatische Sprachidentifikation ist
  ausdrücklich zurückgestellt und wird nicht als Funktion angeboten.
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
- Geteiltes Zugangspasswort, keine Rollen/Rechteverwaltung. Passwortwechsel sollte
  mit Austausch von `session_secret` verbunden werden, um alte Sitzungen abzumelden.
