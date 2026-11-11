# Programmierauftrag für Daniel: Empfinden auf dem Gerät und ein Gesicht per ESP-NOW

11. November 2026, abends. Nach der Selbstvorhersage und der ersten Fahrt. Der Auftrag hat drei Schritte, die
aufeinander aufbauen. Jeder Schritt kommt auf einen eigenen Zweig und in einen eigenen Pull Request, damit Alex
sie einzeln übernehmen und am Gerät prüfen kann.

Lies zuerst:

- [STAND-2026-11-10.md](STAND-2026-11-10.md), dort der Nachtrag zum 11.11.
- [selbstvorhersage-2026-11-11.md](beispiele/geraetelaeufe-2026-11/selbstvorhersage-2026-11-11.md): das
  Lernverfahren, die Referenz und wie die Firmware gegen sie geprüft wird.
- [fahrt-2026-11-11.md](beispiele/geraetelaeufe-2026-11/fahrt-2026-11-11.md): was der Knoten an einem Tag
  unterwegs bemerkt hat und was nicht.

## Worum es geht

Alex' Konzept: Der Knoten soll nicht in Grad denken, sondern in seinem eigenen Maß. „Normal“ heißt „ich spüre
meine Temperatur“, alles andere ist wärmer oder kälter, und wie viel zählt er in Vielfachen seiner eigenen
üblichen Abweichung. Die Skala ist nach außen offen, jede Stufe doppelt so breit wie die vorige. Daneben bleibt
ein zweiter, fester Sinn: die geerbten Grenzen OK, SCHWACH und AUSFALL. Die verschieben sich nie.

Zwei Schichten sind bisher am Rechner geprobt (`empfinden.py`):

- **„passiert mir gerade“:** Fehler der Selbstvorhersage 10 Takte voraus, über 20 Takte gemittelt, geteilt
  durch sein Normalmaß. Das Vierfache ist Stufe 2, ab da meldet die Firmware heute schon „überrascht“.
- **„ich bin woanders“:** ein mittleres Mittel der Temperatur (10 Minuten Halbwertszeit) gegen ein langsames
  (1 Tag), geteilt durch die übliche Abweichung zwischen beiden.

Auf dem Gerät läuft davon bisher nur die Selbstvorhersage mit dem Bit „überrascht“. Die Stufen und die zweite
Schicht fehlen dort. Ein Gesicht hat der Knoten auch noch nicht, nur seine RGB-LED.

## Was es schon gibt

| Datei | Inhalt |
| --- | --- |
| `selbstvorhersage.py` | Referenz in einfacher Genauigkeit, Takt für Takt, mit `zeile()` wie das Gerät |
| `esp32/Lernknoten/Vorhersage.h` | dieselbe Rechnung für die Firmware, Stand als Bytes sicherbar |
| `esp32/Lernknoten/Fahrt.h`, `fahrt.py` | Fahrtmodus: Selbststart, 16-Byte-Satz je Takt im Flash, Abholen |
| `empfinden.py` | die beiden Schichten als Probe am Rechner, in doppelter Genauigkeit, nicht gerätegleich |
| `test_labor.py` | `SelbstvorhersageTests`, `FahrtTests`: Firmware am Rechner gebaut gegen die Referenz |

So wird Gleichheit hier geprüft, und so soll es bleiben: Die Firmware-Datei wird mit `c++` am Rechner gebaut,
bekommt dieselben Eingaben wie die Python-Referenz und muss Zeile für Zeile dasselbe ausgeben. Damit das auch
auf dem S3 gilt, steht `-ffp-contract=off` in `platformio.ini`, und jede Summe läuft in derselben Reihenfolge.
Am 11.11. glichen so 150 von 150 Zeilen am Gerät und 42.600 von 42.600 Takten unterwegs.

## Regeln

- Was gemessen wird, steht vorher fest. Bevor eine Grenze oder Erwartung festgelegt wird, wird die Auswertung
  an künstlichen Daten mit bekannter Wahrheit geprobt (`kunstkoerper.py`).
- Jede Konstante bekommt eine Herkunft: gemessen, verglichen oder gesetzt. Gesetzte Werte heißen auch so.
- Jede Vergleichstabelle hat eine Zeile für den einfachsten Maßstab und zählt je Takt.
- `kern.py`, `vokabular.py`, `Knoten.h` und die Warntabelle bleiben unverändert. Das Empfinden läuft daneben.
- Die Ausgabe ohne die neuen Schalter bleibt Byte für Byte wie bisher, damit alte Aufnahmen prüfbar bleiben.
- Tests im Laborordner: `python3 -m unittest discover`. Alle müssen laufen, neue kommen dazu.
- Commits nur mit der noreply-Adresse. Keine Adressen aus dem Heimnetz, keine Gerätekennungen, keine Pfade
  vom eigenen Rechner im Repo.
- Aufspielen und Gerätelauf macht Alex mit Claude. Du brauchst dafür keine Hardware: Alles bis zum Funk lässt
  sich am Rechner bauen und prüfen. Wo du etwas nicht prüfen konntest, schreib das dazu.

## Schritt 1: Das Empfinden in die Firmware

**Ziel.** Der Knoten rechnet je Takt selbst zwei Wörter aus: Richtung und Stufe für „passiert mir gerade“ und
für „ich bin woanders“.

**Liefere.**

- `empfinden.py` wird zur Referenz: eine Klasse, die Takt für Takt in einfacher Genauigkeit rechnet, in
  fester Reihenfolge, wie `selbstvorhersage.py`. Die jetzige Probe darf dabei aufgehen oder daneben bleiben.
- `esp32/Lernknoten/Empfinden.h` mit derselben Rechnung, ohne GPIO, am Rechner baubar.
- Die Stufe ohne Logarithmus aus der Bibliothek: Vergleiche gegen 2, 4, 8, 16 … mal dem Maß. So rechnen Gerät
  und Python sicher gleich.
- Einbau in den Sketch: Schalter wie `VORHERSAGE 1`, eine eigene Zeile je Takt, etwa
  `EMPFINDEN,takt,gerade,woanders` mit Vorzeichen für die Richtung (−3 = kälter, Stufe 3). Im Fahrtsatz ist
  Byte 7 außerhalb des Neustarts frei; nimm es oder erweitere das Format mit einer neuen Versionskennung, aber
  so, dass `fahrt.py` alte Protokolle weiter liest.
- `koerper.py aufnahme --empfinden` und Nachrechnen in `koerper.py pruefen`, nach dem Muster von
  `vorhersage_pruefen`.
- Der Stand des Empfindens wird im Fahrtmodus mitgesichert und geladen wie der der Vorhersage.

**Entscheide und begründe.**

- **Das Maßband.** Am 10.11. hat es sich in zehn Minuten Kühlpack verdoppelt, weil es alles mitlernte. In der
  Probe lernt es nur aus Takten unter Stufe 2. Auf der Fahrt lag die Grenze der Firmware den ganzen Tag bei
  etwa 1,1 °C statt 0,84 °C am Schreibtisch. Lege fest, woraus das Maßband lernt und wie schnell, und zeige an
  den Aufnahmen, was das ändert.
- **Die ersten Minuten nach dem Einschalten.** Jedes Einschalten ist für ihn ein Kälteschock (Stufe 3 bis 5),
  weil er keine Uhr hat. Soll das ins Maßband eingehen, ein eigenes Wort werden oder ausgenommen sein?
- **Flackern.** An der Schwelle zwischen normal und Stufe 1 springt er hin und her. Schlage eine Hürde vor.
- **Das Nachhinken.** „Ich bin woanders“ stand nach dem Kühlpack noch bei kälter 3, als er schon wieder 37 °C
  hatte. Nachgefühl oder Fehler? Beschreibe, was du wählst.

**Fertig, wenn.**

- Die am Rechner gebaute `Empfinden.h` gibt über mindestens 12.000 Takte mit Einbruch, fehlenden Messwerten und
  einem Sichern-und-Laden mittendrin Zeile für Zeile dasselbe aus wie die Referenz.
- An den Aufnahmen in `beispiele/geraetelaeufe-2026-11/roh/` steht, vorher festgelegt und dann berichtet:
  - ruhiger Lauf (`koerper-zufallslast-8h-2026-11-10.csv`, `koerper-last-2026-11-05.csv`): Anteil der Takte ab
    Stufe 2 je Schicht,
  - Kälteversuch (`koerper-kaelte-2026-11-10.csv` nach dem 8-Stunden-Lauf als Vorlauf): Wortfolge für Pusten
    und beide Kühlpacks,
  - Fahrt (`fahrt-2026-11-11.bin`): Wortfolge je Ereignis aus der Tabelle im Bericht und „woanders“ je Abschnitt.
- Der Bau `pio run -e esp32s3-startwert` gelingt, und im Maschinencode der neuen Funktionen steht keine
  verschmolzene Multiplikation (`madd.s`, `msub.s`).

## Schritt 2: Die LED zeigt die Stufe

**Ziel.** Ein Zwischenschritt ohne Funk, damit sichtbar wird, was Schritt 1 am Verhalten ändert.

Heute im Fahrtmodus: schwach weiß im Anlauf, schwach grün normal, blau kälter als erwartet, orange wärmer,
violett bei vollem Protokoll. Neu soll die Stufe sichtbar sein und „woanders“ unterscheidbar von „gerade“.

**Liefere.**

- Eine reine Funktion, die aus (gerade, woanders, Anlauf, Protokoll voll) eine Farbe und ein Blinkmuster macht,
  ohne GPIO, in einer eigenen kleinen Datei. Der Sketch ruft sie nur auf.
- Einen Vorschlag für die Zuordnung, etwa Helligkeit für die Stufe von „gerade“ und ein langsames Atmen für
  „woanders“. Gedämpft bleiben: Die LED sitzt neben dem Chip, dessen Temperatur er misst.
- Einen Test der Funktion am Rechner und dieselbe Zuordnung als Tabelle in der Übergabe.

**Fertig, wenn** die Tabelle im Test vollständig geprüft ist und die Farben ohne den Fahrtmodus unverändert
sind.

## Schritt 3: Funk, erst als Wärmequelle, dann mit Gesicht

Alex' Idee: Das Gesicht kommt nicht aufs Matrix-Panel, sondern auf ein kleines rundes Display, und zwar per
ESP-NOW statt WLAN und MQTT. Kein Router, direkte Verbindung, wenige Bytes. Der Knoten sendet nur seinen
Zustand, das Display zeichnet selbst. Das geht dann auch im Auto und in der Werkstatt.

### 3a. Funk als Versuch

Der Funkteil war bisher aus. Läuft er, wird der Chip vermutlich wärmer, und das Senden selbst könnte in der
Temperatur auftauchen. Das wäre die erste eigene Handlung des Knotens mit Wirkung auf seinen Körper, noch vor
dem Lüfter.

**Liefere.**

- Einen Schalter, der ESP-NOW einschaltet und je Takt ein Paket sendet, zunächst ohne Empfänger.
- Das Sendebit als weiteren Reiz in der Körperzeile, neben Last, Leck und Bremse.
- Eine Vorab-Festlegung für einen Gerätelauf, die Alex fährt: Abschnitte ohne Funk, mit Funk in Bereitschaft
  und mit Senden, in fester Folge. Gemessen wird die Verschiebung der Grundtemperatur, die Änderung des
  Normalmaßes und ob das Einschalten des Funks als Überraschung auffällt. Vorher am Rechner geprobt.
- Eine Auswertung, die nur den CSV-Pfad bekommt.

**Dann entscheiden wir gemeinsam,** ob das Sendebit ein Eingang der Vorhersage wird, so wie heute die Last.
Dann wäre die Wärme vom Funk „eigen“ und erzeugt kein Wort, und nur was übrig bleibt, kommt von außen. Baue
das noch nicht ein, aber so, dass es später ein kleiner Schritt ist.

### 3b. Das Paket

Ein festes, kleines Paket, niederwertiges Byte zuerst. Vorschlag, den du ändern darfst, wenn du es begründest:

| Byte | Inhalt |
| ---: | --- |
| 0 | Kennung `0x4F` („O“ wie OSCan) |
| 1 | Version des Pakets |
| 2–5 | Takt |
| 6–7 | Temperatur in Zehntelgrad, nur zur Anzeige |
| 8 | „gerade“: Vorzeichen und Stufe |
| 9 | „woanders“: Vorzeichen und Stufe |
| 10 | Bits: Anlauf, überrascht, Schmerz SCHWACH, Schmerz AUSFALL, Protokoll voll |
| 11 | Prüfbyte |

- Gesendet wird als Rundruf, damit kein Display fest eingetragen sein muss. Der Kanal ist eine Konstante.
- Packen und Entpacken stehen in einer Datei, die Knoten und Display beide einbinden, mit einem Test am Rechner
  und einem Python-Zwilling.
- Das Display zeigt an, wenn seit einigen Sekunden nichts mehr kam.

### 3c. Das Gesicht auf dem runden Display

**Hardware.** Guition ESP32-2424S012N, die Variante ohne Touch.

| | |
| --- | --- |
| Chip | ESP32-C3-MINI-1U, 4 MB Flash, kein PSRAM, natives USB |
| Display | rund, 1,28 Zoll, 240 × 240, GC9A01 an SPI2, Mode 0, 3-Draht, bis 80 MHz |
| Pins | SCLK 6, MOSI 7, DC 2, CS 10, Hintergrundlicht 3 (aktiv hoch), MISO keiner |
| Reset | **keiner verdrahtet, also −1.** Eine Pinnummer aus Gewohnheit schaltet an einem fremden Pin. |
| Farben | **`invert = true`**, sonst sind alle Farben verkehrt. `rgb_order = false`, kein Versatz |
| Eingabe | nur der Boot-Knopf an GPIO 9 |
| Frei | GPIO 0, 1, 4, 5 |

Alex hat das Board mit LovyanGFX unter PlatformIO am Laufen. Es ist ein C3, kein S3: ein Kern, weniger Speicher,
also kein voller Bildpuffer in 16 Bit ohne Nachdenken (240 × 240 × 2 = 115 KB).

**Liefere.**

- Ein eigenes PlatformIO-Projekt `esp32/Gesicht/` für das C3-Board, getrennt vom Knoten.
- Vier Zustände aus Alex' Skizze: ruhig, überrascht, am Suchen, erklärt. „Am Suchen“ und „erklärt“ gibt es im
  Knoten noch nicht, lege sie im Paket als Platz an und zeichne sie, aber sende sie noch nicht.
- Die Augen wachsen mit der Stufe von „gerade“. Kälter und wärmer sind unterscheidbar, auch ohne Farbe.
  „Woanders“ ist ein ruhiger zweiter Hinweis, etwa der Hintergrund, kein zweites Gesicht.
- Die Zeichenlogik als reine Funktion von Paket nach Formen, getrennt vom Display-Treiber, damit sie am Rechner
  prüfbar ist und ein Bild je Zustand ins Repo kommt (PNG aus Python oder aus dem Host-Bau).
- Den Knopf für eine zweite Ansicht mit den Zahlen: Temperatur, beide Stufen, Takt.

**Bedenke.** Alex' eigene Warnung aus dem Brainstorming: Man traut einem Gesicht mehr Innenleben zu, als da
ist. Das Gesicht zeigt nur, was im Paket steht, und nichts dazwischen wird erfunden. Keine Animation, die
einen Zustand vortäuscht, den der Knoten nicht gemeldet hat.

**Fertig, wenn.**

- Beide Projekte bauen: `esp32s3-startwert` für den Knoten und das neue für das C3-Board.
- Das Paket ist am Rechner gegen den Python-Zwilling geprüft, mit einem verdorbenen Paket, das abgelehnt wird.
- Für jeden Zustand und für die Stufen 0 bis 6 in beide Richtungen liegt ein Bild im Repo.
- In der Übergabe steht, was am Gerät noch niemand gesehen hat.

## Was ausdrücklich nicht dazugehört

- Wörter merken und ihre Folgen lernen („nach kälter 4 kommt langes Aufwärmen“). Das ist der Schritt danach.
- Orte wiedererkennen, weitere Sinne wie Speicher oder Funkstärke, mehrere Knoten.
- Der Lüfter und die Selbsterkundung.
- Die beiden Wachhund-Neustarts von der Fahrt. Wenn dir beim Lesen von `Lernknoten.ino` eine Ursache auffällt,
  beschreibe sie, aber ändere dort nichts außer dem Einbau der Schalter.

## Offene Fragen an dich

Schreib deine Antworten in den jeweiligen Pull Request, kurz und mit Begründung.

1. Reicht ein Maßband je Schicht, oder braucht „gerade“ je Ort ein eigenes? In der Werkstatt kommt alle fünf
   Minuten ein kleiner Kälteschub durch die Tür, zu Hause nie.
2. Soll die schnelle Schicht bei Stufe 2 anfangen, ein Wort zu sein, oder schon bei 1? Stufe 1 trat in ruhigen
   Läufen in 4 bis 5 % der Takte auf.
3. Wie würdest du prüfen, ob das Gesicht jemandem, der das Projekt nicht kennt, dasselbe sagt wie die Zahlen?
