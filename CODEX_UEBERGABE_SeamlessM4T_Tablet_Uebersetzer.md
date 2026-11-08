# Codex-Übergabe: Lokaler SeamlessM4T-Gesprächsübersetzer für ein iPad

**Stand:** 08.11.2026  
**Auftrag an Codex:** Dieses Projekt **implementieren**, nicht nur erneut konzipieren. Die folgenden Entscheidungen wurden mit dem Auftraggeber bereits abgestimmt und sollen als verbindliche Anforderungen gelten. Ungeklärte technische Voraussetzungen zuerst mit einem kleinen Funktionstest prüfen; anschließend die lauffähige Anwendung einschließlich Tests, Einrichtung und Betriebsdokumentation umsetzen. Keine alternativen Oberflächen- oder Bedienkonzepte einführen.

## 0. Dateien und Priorität der Anforderungen

- `CODEX_UEBERGABE_SeamlessM4T_Tablet_Uebersetzer.md` — diese Spezifikation.
- `a_clean_modern_high_contrast_user_interface_desi.png` — **letzter freigegebener visueller Entwurf**; als **optische Referenz**, nicht als exakter Funktions-Screenshot zu behandeln.

**Bei Abweichungen ist diese Markdown-Datei maßgeblich.** Das Bild zeigt beispielsweise eine grüne Fläche mit Text, während die finale Funktionsvorgabe vorsieht, dass die gesamte KI-Verarbeitung und die endgültige Textausgabe **erst nach dem Loslassen** stattfinden. Auch Sprachbezeichnungen und deren Anordnung müssen den nachstehenden Regeln entsprechen. Das Bild ist unverändert, weil es ausdrücklich als letzte Originalbilddatei mitgeliefert werden soll.

## 1. Produktziel

Ein **vollständig lokaler** Gesprächsübersetzer für zwei sich am Tisch gegenübersitzende Menschen; typischer Anwendungsfall ist ein Arzt und ein fremdsprachiger Gesprächspartner. Ein iPad mini liegt **im Hochformat** zwischen beiden. Jede Person schaut auf ihre Hälfte des Displays. Beide Hälften sind großflächige **Push-to-Talk-Tasten**, keine dauerhaft aktivierten Sprecher-Modi.

- **Obere Displayhälfte:** für die gegenüber sitzende Person; eigentlicher Text um **180° gedreht**.
- **Untere Displayhälfte:** Arztseite; eigentlicher Text aus Sicht des Arztes normal lesbar.
- Der Sprecher **hält** seine Hälfte gedrückt, spricht und **lässt los**. Erst dann wird die Äußerung final verarbeitet.
- Die eigene Seite zeigt das **Originaltranskript**; die Gegenseite zeigt die **Übersetzung**. Beide Texte bleiben bis zur nächsten abgeschlossenen Äußerung sichtbar.
- Optional spricht das Modell den **übersetzten Text** in der Zielsprache aus.
- Nur **eine KI-Modellinstanz**: **Meta SeamlessM4T v2 Large**. Kein Whisper, NLLB, Piper, eigenständiges TTS, externes Sprachmodell, Cloud-API oder weiteres trainiertes KI-Modell. Nicht-KI-Komponenten wie Audioumwandlung sind zulässig.
- Modell und KI-Rechenarbeit laufen auf **einem zentralen Linux-Server**; auf dem iPad läuft lediglich eine PWA im Browser.

## 2. Zielhardware und Betrieb

| Teil | Vorgabe |
|---|---|
| Client | **iPad mini (Testgerät von 2023)**, iPadOS Safari/PWA, Hochformat |
| Installation Client | Über **„Zum Home-Bildschirm“ / Add to Home Screen**, Start im `standalone`-Modus möglichst ohne Browserleisten |
| Server | Native Installation unter Ubuntu/Debian 64 Bit, **ohne Docker-/Containerpflicht** |
| GPU | NVIDIA **RTX 3090 24 GB**, CUDA |
| RAM | 64 GB vorhanden |
| Modell | `facebook/seamless-m4t-v2-large` (vollständiger Checkpoint für ASR, Speech→Text, Speech→Speech) |
| Berechnung | Primär FP16 auf der GPU; Versions- und Kompatibilitätsprüfungen durchführen |
| Netzwerk | Lokales LAN, **HTTPS** mit auf dem iPad vertrauenswürdigem Zertifikat |
| Externer Dienst | **Nicht erforderlich** nach einmaligem, vom Nutzer autorisiertem Modell-Download |

Ein einzelner zentraler Dienst mit mehreren unabhängigen Clients/Sitzungen ist architektonisch vorzusehen, auch wenn zunächst nur ein iPad getestet wird. Die Modellgewichte dürfen **nicht pro Browser-Client erneut geladen** werden. Serielle GPU-Inferenz/Warteschlange ist für v1 ausreichend.

## 3. Unveränderliche Bedienregeln

### 3.1 Push-to-Talk, KEIN Tap-to-Toggle

1. **`pointerdown`** auf einer Sprechfläche: diese Fläche sofort **grün**; das zugehörige Mikrofon pulsiert; ein neuer Aufnahmeblock beginnt, einschließlich des konfigurierten Audiovorlaufs.
2. Solange derselbe Finger auf der Fläche **gehalten** wird: neue Mikrofon-Samples werden dem Aufnahmeblock angehängt. Kein automatisches Sprecher-Umschalten.
3. **`pointerup`**: die Fläche wird **sofort schwarz**; der Aufnahmeblock endet samplegenau; erst jetzt wird er zur KI-Verarbeitung freigegeben.
4. Die **KI-Verarbeitung** (Original-ASR, Übersetzung und gegebenenfalls TTS) läuft **erst nach dem Loslassen** für genau den abgeschlossenen Block. Keine VAD-Satzendeerkennung, keine KI-Berechnung auf laufenden Teilstücken, keine fortlaufende automatische Transkription.
5. Ein **neuer** Aufnahme-/Verarbeitungsblock entsteht **nur durch erneutes Drücken**, egal auf welcher Hälfte.
6. **`pointercancel`**, App-Verlust des Vordergrunds, Touch-Unterbrechung und ähnliche Fehlerfälle sollen die aktuelle Aufnahme **abbrechen/verwerfen**, nicht unbemerkt weiterlaufen lassen. Multi-Touch auf zwei Sprechflächen ist abzuweisen; nur ein Touch ist zurzeit der aktive Aufnahme-Touch.
7. Zwischen den Aufnahmen sind **beide Hälften schwarz**. Alte Resultate können sichtbar bleiben; grün bedeutet ausschließlich **Finger wird gerade gehalten/Aufnahme läuft**.

**Ausdrücklich keine** automatische Sprechererkennung, Sprecherumschaltung per Sprache, Sprachpausen-Erkennung als Aufnahmestopp oder automatische Wiederaufnahme.

### 3.2 Kontinuierlich geöffneter Mikrofonstream + Vorlauf

Der zuvor diskutierte Ansatz „Mikrofon-Track nach jedem Loslassen wirklich schließen“ wurde **verworfen**.

- Das Mikrofon wird nach der ersten Berechtigungsfreigabe **einmal** geöffnet und bleibt **technisch geöffnet**, während die PWA aktiv ist.
- Audiodaten laufen kontinuierlich in einen **lokalen Ringbuffer im Arbeitsspeicher des iPads**. Dieser hält stets die **letzten maximal 3 Sekunden** vor.
- Im Leerlauf: **keine Übertragung** dieser Audiodaten zum Server, keine Modellinferenz, keine dauerhafte Speicherung, kein Transkript.
- Beim Drücken: Der finale Aufnahmeblock enthält die letzten **`pre_roll_ms`** aus dem Ringbuffer **plus** sämtliche Samples von `pointerdown` bis `pointerup`.
- Der Vorlauf ist **standardmäßig 1000 ms**, einstellbar von **0 bis 3000 ms** in **250-ms-Schritten**. Genau die gewählte Dauer wird übernommen; der Ringbuffer selbst darf weiterhin 3 Sekunden halten.
- So sollen Wortanfänge unmittelbar vor dem Tastendruck nicht verloren gehen. Die technische Bedeutung von „keine Verarbeitung im Leerlauf“ lautet hier: **keine serverseitige Verarbeitung/Übertragung/semantische Auswertung**; die rein lokale Aufnahme in den Vorlaufbuffer ist ausdrücklich erlaubt und gewollt.
- `AudioWorklet` mit kontinuierlichen PCM-Samples wird gegenüber wiederholtem Öffnen/Schließen und gegenüber `MediaRecorder` bevorzugt, damit Vorlauf und Release samplegenau geschnitten werden können.
- Die Audiokette muss den tatsächlichen Gerätesamplerate berücksichtigen (z. B. 48 kHz); erst serverseitig oder in einer kontrollierten Pipeline auf das für Seamless benötigte Format umwandeln. Audiolängen und Sample-Zählung nicht durch bloßes Runden von Millisekunden schätzen.
- Eine normale Bedienung darf keinerlei Audio von vor oder nach dem ausgewählten Vorlauf-/Haltefenster an den Server übertragen.
- Bei App-Hintergrund, Berechtigungsverlust, fehlerhaftem AudioContext oder Netzfehler: sichere Zustände und verständliche Fehlermeldung.

### 3.3 Wiedergabe und neue Aufnahmen

- Mittiger **Lautsprecherknopf** schaltet **automatische Ausgabe der Übersetzung als Audio** EIN/AUS.
- **AUS:** Originaltranskript und übersetzter Text, **keine** Audioausgabe.
- **EIN:** Originaltranskript, übersetzter Text, **übersetzte Sprachausgabe** durch SeamlessM4T.
- Diese Einstellung ist unabhängig von der gedrückten Sprecherseite.
- Sobald eine neue Sprechfläche gedrückt wird, laufende Audioausgabe unmittelbar stoppen/unterbrechen. Während eigener Audiowiedergabe Mikrofon-Echo und Kontamination des Vorlaufbuffers vermeiden; Browser-`echoCancellation` aktivieren, zusätzlich während Playback aufgenommene Echo-Samples nicht als sauberen Vorlauf behandeln bzw. den Ringbuffer für ein neues PTT passend zurücksetzen. Keine falsche Sicherheit hinsichtlich vollständiger Echo-Unterdrückung behaupten.
- iPadOS kann für Audiowiedergabe eine vorherige Nutzerinteraktion/`AudioContext.resume()` verlangen. Das über eine echte Touchinteraktion vorbereiten.
- Neue PTT-Aufnahme darf auch starten, während eine frühere KI-Anfrage noch bearbeitet wird. Alte Antworten über **`utterance_id`/Generation Counter** vor falscher Anzeige schützen; Warteschlange/Abbruchkonzept definieren, veraltete Antwort nicht als neue ausgeben. Ein erneuter Tastendruck übernimmt nicht den alten Sprecherstatus.

## 4. UI – **final freigegebener Entwurf**

### 4.1 Layout

- Hochformat, vollflächig, schwarzer Hintergrund mit großflächigen weißen Texten.
- Zwei riesige Touchbereiche, die den Bildschirm einschließlich der Textdarstellung ausfüllen; kleine Steuerelemente sind hiervon explizit ausgenommen.
- **Bei aktivem PTT:** gedrückte Hälfte **sattes Grün**, nimmt etwa **45 %** der nutzbaren Fläche ein; ungedrückte Hälfte **Schwarz**, etwa **55 %**. Also **grüne Seite kleiner als schwarze**. Bei keinem gedrückten Finger sind beide schwarz; für diesen Fall kann das Layout neutral 50/50 sein, solange es beim Start der Aufnahme eindeutig reagiert und sich nicht störend verschiebt.
- Auf der aktiven grünen Seite erscheint ein **großes pulsierendes Mikrofonsymbol**. Es pulsiert nur während tatsächlicher PTT-Aufnahme.
- Bei fertigem Ergebnis: Originaltranskript auf der gerade sprechenden Seite; übersetzter Text auf der Gegenseite. Texte groß, kontrastreich, dynamisch umgebrochen; nicht abgeschnitten, bei langen Sätzen erforderlichenfalls innerhalb der jeweiligen Hälfte scrollbar.
- **Obere Hälfte:** Text für den gegenüber Sitzenden stets `rotate(180deg)` / entsprechende CSS-Transformation. **Untere Hälfte:** Text normal.
- **Sprachlabels, Sprachauswahl, Vorlaufknopf, mittiger Lautsprecherknopf und Übersetzer-Symbol ausdrücklich NICHT drehen**; sie sollen aus Sicht des Arztes lesbar/bedienbar bleiben.
- Keine „Arzt“- oder „Patient“-Pills, **kein Footer** und keine störenden Zeilen unter den Textbereichen.
- Das **Übersetzer-Symbol mit den zwei Pfeilen/Sprechblasen** aus dem Mockup bleibt erhalten.
- Zentraler Lautsprecherknopf sitzt auf der Trennzone; sein Status ist klar erkennbar (aktiv/stumm).

### 4.2 Sprachanzeigen

- Genau **eine reguläre Sprachauswahl**, an der **Arztseite (unten)**; Standard **Deutsch** (`deu`). Diese Auswahl bestimmt die eine feste Sprache des Gesprächs.
- Die **Patientensprache** wird automatisch erkannt und gespeichert. Sie wird ebenfalls **für den Arzt sichtbar** mit einem ungedrehten Sprachlabel, z. B. `↑ Ukrainisch`. Kein zweites standardmäßiges Sprach-Dropdown auf der Hauptansicht.
- In der mittigen Kontrollzone aus **Arztsicht**: links ein Pfeil nach oben mit automatisch ermitteltem Patientensprachlabel, rechts das **Dropdown für die feste Arztsprache**. Mittiger Lautsprecherknopf und Übersetzer-Symbol bleiben, in einer kompakten, vom Bild inspirierten Anordnung; keine zusätzliche Footerzeile.
- Wenn eine Sprachidentifikation unklar/nicht möglich ist, **nicht** eine erkannte Sprache vortäuschen. Verständliche Zustandsanzeige und eine bewusst zugängliche Korrektur-/Diagnosefunktion in den **Arzt-Einstellungen**, ohne die Vorgabe der einen regulären Sprachauswahl zu unterlaufen. Details siehe Abschnitt 6.

### 4.3 NEU: Vorlaufknopf auf der Arztseite

- **Kleiner, unaufdringlicher Knopf auf der unteren Displayhälfte**, z. B. `↺ 1,0 s`, aus Arztsicht lesbar.
- Durch Tippen öffnet er ein kleines Overlay mit Slider **0–3 s**, **250-ms-Schritte**, Standard **1,0 s**. Anzeige des aktuellen Werts; Aktion „Übernehmen/Schließen“.
- Einstellung lokal auf dem iPad speichern (z. B. `localStorage`), beim nächsten Start wiederherstellen. **Nur Konfiguration**, keine Audiodaten persistent speichern.
- Während Overlay geöffnet: Push-to-Talk-Flächen deaktivieren, damit die Sliderbedienung **niemals** als PTT-Touch interpretiert wird.
- Das Bedienelement ist vom großflächigen PTT-Hit-Target ausgenommen und löst selbst keine Aufnahme aus.

### 4.4 Referenzgrafik

Die mitgelieferte PNG ist ein **Moodboard/Designziel** für Typografie, großzügige Flächen, Farben und den gedrehten Lesebereich. Sie ist **kein 1:1 verbindliches Pixel-Layout** und bildet den neu beschlossenen PTT-Idle/Release-Zustand nicht exakt ab. Nicht noch einmal mit einem Bildgenerator entwerfen; die Oberfläche als echte responsive HTML/CSS-Komponenten bauen.

## 5. Audio- und KI-Pipeline (Seamless-only)

### 5.1 Pro Äußerung

1. PTT-Blöcke kommen als **abgeschlossene Audioaufnahme** (Vorlauf + Haltezeit) zum Server.
2. Zuordnung: `speaker_side` = `top` oder `bottom`, zugehörige Quellsprache (sofern bekannt), Zielsprachcode, Audio-ein/aus und eindeutige Äußerungs-ID.
3. **Originaltranskript** mit SeamlessM4T-ASR, soweit die erforderliche Quellsprache bekannt und vom Modell unterstützt wird.
4. **Übersetzter Text** möglichst **direkt aus dem Sprach-Audio** mittels Speech-to-Text Translation (**S2TT**), statt die ASR-Zwischenübersetzung erzwingen zu müssen.
5. Ist Audioausgabe aktiviert, statt reinem S2TT **Speech-to-Speech (**S2ST**)** des **selben Checkpoints** verwenden und den erzeugten **übersetzten Text** aus der passenden Zwischenrepräsentation/Tokenausgabe extrahieren. Exakte Transformers-Version und Rückgabeobjekte im Code verifizieren.
6. Ergebnis clientseitig nur der zugehörigen Äußerung/Seite zuordnen; Originaltext auf Sprecherseite, Zieltext auf Gegenseite; optional Sprachausgabe.
7. Sprachausgabe kann nur für **vom Modell unterstützte Audio-Zielsprachen** erfolgen; für Text-aber-nicht-Audio-Sprachen transparenten **Text-only-Fallback** anbieten und anzeigen, nicht abstürzen.

**Ein Modell geladen** heißt nicht zwangsläufig **nur ein einzelner Inferenz-Aufruf**. Original-ASR plus übersetzter Text (plus gegebenenfalls generiertes Audio) dürfen zwei Teilaufrufe derselben residenten Modellinstanz sein. **Kein zusätzlicher KI-Checkpoint.**

### 5.2 Wichtige offene Voraussetzung: **automatische Patientenspracherkennung**

Diese Anforderung ist fachlich verbindlich, aber technisch **nicht als gelöst vorauszusetzen**:

- SeamlessM4T v2 kann eingehendes Audio auch bei **unbekannter Quellsprache direkt in eine bekannte Zielsprache übersetzen**.
- Daraus folgt **nicht automatisch**, dass die öffentlich dokumentierte API einen **zuverlässigen ISO-Sprachcode der Quellsprache** ausgibt.
- Für die **Rückübersetzung** Arzt → Patient und für das **Originaltranskript** des Patienten wird aber ein expliziter Patientensprachcode benötigt.

**Auftrag an Codex:** Zunächst per offizieller Modellimplementierung/Checkpoints prüfen, ob Seamless selbst einen verwertbaren Sprachidentifikationspfad bzw. ein Sprachlabel/-score aus **demselben** Modell zur Verfügung stellt. Falls nicht, einen innerhalb der Ein-Modell-Vorgabe bleibenden Ansatz prototypisch testen und seine Qualität/Latenz messen; keine erfundene Funktion behaupten und kein Whisper, fastText-LID oder sonstiges Modell heimlich hinzufügen. Falls keine belastbare automatische Erkennung möglich ist, im Projekt klar als **offenen Blocker** dokumentieren. Für die Entwicklung darf ein Testmodus die Patientensprache vorübergehend explizit im **Arzt-Setup/Debugbereich** vorgeben (nicht als zweite reguläre Sprachauswahl auf der Hauptansicht), damit das übrige System vollständig implementiert werden kann. Die App darf bei ungeklärter Sprache keine falsche Zielsprache vorgaukeln. Eine einmal erkannte Sprache soll für die Sitzung gespeichert werden; nur ein bewusstes Zurücksetzen startet erneute Identifikation.

### 5.3 Schnittstellen und Timing

Vorschlag: Browser hält den PCM-Ringbuffer lokal und sendet nach `pointerup` den vollständigen Block als WAV/PCM in einem **HTTPS POST** an FastAPI. WebSocket ist bei dieser **abgeschlossenen Blockverarbeitung nicht zwingend erforderlich**.

Beispiel-Endpunkte (konkret implementierbar/anpassbar):

- `GET /api/health` — Server-/Modellstatus (keine personenbezogenen Daten)
- `POST /api/sessions` — Sitzung erzeugen
- `PATCH /api/sessions/{id}` — feste Sprache, TTS-Status, eventuell ermittelte Patientensprache
- `POST /api/sessions/{id}/utterances` — Multipart: WAV/PCM, `utterance_id`, `speaker_side`, `tts_enabled`; Response mit Originaltext, übersetztem Text, Sprachen, Status und optional kurzlebigem Audio-Token/-URL
- `GET /api/sessions/{id}/audio/{utterance_id}` — optional kurzlebiges Audio **ausschließlich aus RAM**, Token/Sitzung prüfen
- `DELETE /api/sessions/{id}` — RAM-Daten der Sitzung entfernen

Keine dauerhafte Speicherung von Audio oder Transkripten im Standardbetrieb; niemals Audiobinärdaten als Base64 in Serverlogs ablegen. Eine Anfrage-Warteschlange führt die GPU-Inferenz grundsätzlich seriell aus. Im Frontend bei neuem Touch die Audioausgabe stoppen und veraltete Serverantworten anhand der IDs ignorieren.

**Metriken separat, ohne Nutzdaten:** Aufnahmelänge, Übertragungsdauer, Warteschlange, ASR-Zeit, Übersetzungszeit, TTS-Zeit, Zeit bis Ergebnis, Spitzen-VRAM, Fehlercode. Optionale Benchmarks nur mit künstlichen/nicht personenbezogenen Testsätzen.

## 6. Beispiel für den konkreten Gesprächsablauf

**Ausgangslage:** Arztseite unten = Deutsch, Patientensprache nach Erkennung = Türkisch.

**Patient spricht (oben drücken und halten):**
- Oben wird während des Gedrückthaltens grün; nur sein Audio (plus 1 s Vorlauf) wird dem lokalen Äußerungsblock hinzugefügt.
- Loslassen → oben wieder schwarz → Verarbeitung startet.
- **Oben um 180° gedreht:** türkisches Originaltranskript.
- **Unten normal:** deutsche Übersetzung.
- Lautsprecher EIN: deutschsprachige Ausgabe; AUS: nur die beiden Texte.

**Arzt spricht (unten drücken und halten):**
- Unten grün, oben schwarz; bei `pointerup` wieder beide schwarz und danach Übersetzung.
- **Unten:** deutsches Originaltranskript.
- **Oben um 180° gedreht:** türkische Übersetzung.
- Lautsprecher EIN: türkischsprachige Ausgabe.

Für jeden neu abgeschlossenen Block bleiben die letzten angezeigten Texte bestehen, bis neue Ergebnisse eintreffen. Während einer Aufnahme können die vorherigen Texte sichtbar bleiben; sie dürfen nicht fälschlich als **Live-Transkript der aktuellen** Äußerung gekennzeichnet werden.

## 7. Browser-/iPad-Technik

- **PWA:** `manifest.webmanifest`, App-Icons, `display: standalone`, optional Service Worker für Frontend-Assets (nicht für Audio-/Gesprächsdaten), iOS Meta-Tags/Safe Areas.
- **Portrait first:** `100dvh`, `env(safe-area-inset-*)`, responsiv für iPad-mini-Hochformat; bei Querformat verständlicher Hinweis oder sinnvolle Anpassung.
- **Touch:** Pointer Events (`pointerdown`, `pointerup`, `pointercancel`) und `setPointerCapture()`, `touch-action: none` für Sprechflächen; **Steuerknöpfe/Slider dürfen keinen PTT-Handler auslösen**; iOS-Touch-Sonderfälle testen.
- **Mikrofon:** `getUserMedia`, Web Audio API, `AudioWorklet` für langlebigen PCM-Stream und lokalen Ringbuffer; Permission- und AudioContext-Reaktivierung nach iOS-Unterbrechung berücksichtigen.
- **Playback:** nur nach Browser-Audiofreigabe; geräteseitig testbarer WAV/PCM-/geeigneter Codec. Kein Echo im neuen Vorlauf. Laufende Wiedergabe beim nächsten PTT abbrechen.
- **Sicherheit:** HTTPS auch im LAN (außer zu reinen lokalen Entwicklungszwecken), autorisierte Sitzungen/Clients und keine offenen produktiven Endpunkte ohne Zugriffsregelung.
- **Privacy by default:** Mikrofon bleibt im Vordergrund für den lokalen Vorlauf aktiv, obwohl keine Serverübertragung stattfindet; eine klare Datenschutzhinweis-Information gehört ins Setup, nicht als dauerhafter Footer ins Gesprächsinterface.

## 8. Backend-Design

Empfohlene Komponenten: Python 3.x, FastAPI/Uvicorn, PyTorch CUDA, Hugging Face Transformers, geeignete Audiobibliothek für WAV/PCM/Sampling (keine zusätzlichen trainierten Modelle). Versionsstände **installierbar und zueinander kompatibel pinnen**, insbesondere bei SeamlessM4T-v2-Support in Transformers. Inferenz nur auf einer einzigen Modellinstanz, `eval()` und `torch.inference_mode()`, FP16 wo unterstützt.

Nicht die vollständigen Modelle mehrmals pro Funktion laden. ASR/S2TT/S2ST über die vom Framework unterstützte Variante **einer** Modellinstanz abbilden; falls dedizierte Modellklassen Checkpoints unterschiedlich initialisieren, das so implementieren, dass dennoch nur **ein Checkpoint resident** ist bzw. transparent dokumentieren, wenn sich eine harte Einschränkung ergibt. Das Ziel ist ein einzelnes SeamlessM4T-Modell auf der RTX 3090, keine separaten Modellgewichte/ASR-KIs.

Empfohlene Projektstruktur (nicht zwingend):

```text
seamless-tablet-translator/
├── README.md
├── LICENSE
├── backend/
│   ├── app/              # FastAPI, Sitzungen, API, Warteschlange
│   ├── model/            # ausschließlich SeamlessM4T v2 Adapter
│   ├── audio/            # WAV, Resampling, Ausgabeformat
│   ├── tests/
│   └── requirements.txt (oder pyproject.toml + Lock)
├── frontend/
│   ├── src/              # PWA-UI, Pointer Events, Ringbuffer
│   ├── public/           # Manifest, Icons, statische Assets
│   └── tests/
├── deploy/
│   ├── *.service         # systemd
│   └── ...               # Beispiel: lokales HTTPS via Reverse Proxy
└── docs/
    ├── INSTALLATION.md
    ├── TESTPLAN.md
    └── LIMITATIONS.md
```

Native Einrichtung mit einer klaren Startanleitung, Modellablagepfad konfigurierbar, kein stillschweigender Download zusätzlicher KI-Gewichte. Healthcheck, modellbedingte Fehler und GPU-/RAM-Mangel sauber behandeln.

## 9. Lizenz-/Nutzungsrahmen

**Wichtig:** Der zugrunde liegende Seamless-Quellcode ist MIT-lizenziert; die von Meta veröffentlichten SeamlessM4T-Modellgewichte stehen unter **CC BY-NC 4.0**. Die eigenständige Anwendung kann offen entwickelt werden; die Modellgewichte **nicht** in das Repository/Archiv/Release aufnehmen. Installation der Gewichte separat und mit gut sichtbarem Lizenzhinweis. **Kommerzielle Nutzung der Gewichte nicht als freigegeben darstellen.**

Das Projekt soll zunächst als **nichtkommerzieller technischer Prototyp mit Testdaten** entstehen. Keine Behauptung medizinischer Validierung, keine Behandlung realer Patientendaten ohne gesonderte datenschutzrechtliche und lizenzrechtliche Prüfung. Eine noch so klare README-Beschränkung ist nicht automatisch eine Haftungsfreistellung für jede eigene Nutzung.

## 10. Akzeptanztests (Definition of Done)

1. PWA lässt sich auf dem iPad mini zum Home-Bildschirm hinzufügen und im Hochformat als weitgehend bildschirmfüllende App starten.
2. Ohne Touch: beide Hälften schwarz, Mikrofonstream darf geöffnet sein, **keine Audioübertragung** und **keine KI-Verarbeitung**.
3. Unten gedrückt: **nur unten** grün + pulsierendes Mikrofon; oben gedrückt: **nur oben** grün. Beide Seiten sind große Touchziele.
4. Bei `pointerup` wird die grüne Seite sofort schwarz und exakt ein Audioblock inklusive konfiguriertem Vorlauf abgesendet.
5. Bei kurzem Drücken mit vor dem Touch gesprochenem Wort ist dessen Anfang durch 1 s Vorlauf im Roh-Audioblock nachweisbar (Testaufnahme und Waveform-Vergleich).
6. 0/250/1000/3000 ms Vorlauf werden korrekt angewendet; **kleiner Vorlaufknopf unten** öffnet Slider, gespeicherter Wert bleibt nach App-Neustart erhalten.
7. Im geöffneten Slider-Overlay lösen Touch/Schiebegesten keine PTT-Aufnahmen aus.
8. `pointercancel`, Wegwischen/App-Unterbrechung oder zweiter Finger verursachen keine hängende aktive Aufnahme.
9. Originaltranskript steht auf der tatsächlich sprechenden Seite und die Übersetzung gegenüber; oberer **Text** ist 180° gedreht, Sprachanzeigen und Knöpfe **nicht**.
10. Sprachausgabe AUS: nur Original- und Zieltext, **kein Audio**. Sprachausgabe EIN: zusätzlich **Seamless-eigene** synthetisierte Zielsprachenausgabe.
11. Neue Aufnahme während Wiedergabe stoppt die Wiedergabe, startet sofort Aufzeichnung und verwirft/verarbeitet veraltete Ergebnisse korrekt.
12. Sprachausgabe von einer nicht unterstützten Zielsprache führt zu nachvollziehbarem **Text-only-Fallback**.
13. Modellgewichte werden auf dem Server nur **einmal** geladen; wechselnde Sprachrichtungen/Clients führen nicht zum Nachladen einer zweiten KI.
14. Keine Cloudaufrufe im laufenden Betrieb, keine dauerhaft gespeicherten Gesprächsaufnahmen, keine medizinischen Gesprächsinhalte in Serverlogs.
15. **Sprachidentifikation:** Entweder nachweislich funktionierende automatische Erkennung mit demselben Seamless-Checkpoint und Anzeige der Sprache, **oder** ausdrücklich als noch nicht erfüllte Anforderung dokumentiert, mit klarem Debug-/Test-Fallback und ohne irreführende Behauptung. Die übrigen Punkte müssen trotzdem lauffähig sein.
16. Installationsanleitung, Start/Stop via systemd, Testplan, Konfigurationshinweise, Lizenzhinweis und kurze Benchmark-/Limitations-Dokumentation liegen bei.

## 11. Konkrete Reihenfolge für Codex

1. **Spike:** Installation CUDA + SeamlessM4T v2, Sprach→Text, Original-ASR und optional Sprach→Sprach auf RTX 3090 funktionsfähig messen. **Sofort** Sprachidentifikations-API/Interna prüfen und dokumentieren, statt spätere Implementierung auf eine nicht nachgewiesene Funktion zu stützen.
2. **Frontend/PWA** aus Referenz-PNG umsetzen (echte Oberfläche, keine Bilddatei als UI). Für Entwicklung Mock-Inferenz-Responses vorsehen.
3. **AudioWorklet + 3-s-Ringbuffer + PTT** inkl. Vorlauf, Race-Handling und lokalem Persistieren der Schiebereglereinstellung implementieren.
4. **Backend und Inferenz-Pipeline** integrieren, API mit korrekter Zuordnung von Sprecher/Quelle/Ziel/Ausgabe.
5. **Echte iPad-Tests:** Touch, Audio-Berechtigung, Hintergrundwechsel, Audio-Ausgabe/-Abbruch, zuverlässiger Vorlauf, Home-Screen-Modus.
6. Tests, Fehlermeldungen, Benchmarks, systemd/HTTPS-Dokumentation und Freigabe-Checkliste fertigstellen.

**Nicht zur Debatte stellen:** Manuelles Push-to-Talk statt Sprecherumschaltung, dauerhaft bereitstehendes Mikrofon, nur ausgewählter Block ans Backend, 1 s Standard-Vorlauf/Slider 0–3 s, ein SeamlessM4T-Modell, zentraler Server, hochformatige Zwei-Personen-PWA und zuletzt festgelegtes minimalistisches Interface.

---

**Quellen für die technische Implementierung (öffentlich):**
- Meta Seamless Communication: https://github.com/facebookresearch/seamless_communication
- Modell: https://huggingface.co/facebook/seamless-m4t-v2-large
- Transformers-Modell-API: https://huggingface.co/docs/transformers/model_doc/seamless_m4t_v2
- Web Audio / AudioWorklet: https://developer.mozilla.org/en-US/docs/Web/API/AudioWorklet
- Pointer Events: https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events
- getUserMedia / Secure Context: https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
- CC BY-NC 4.0: https://creativecommons.org/licenses/by-nc/4.0/deed.de
