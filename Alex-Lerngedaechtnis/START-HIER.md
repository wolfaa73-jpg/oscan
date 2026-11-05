# Alex’ Lernlabor

**Stand 0.4 · 5. November 2026 · Arbeitsprojekt für Alex und Claude**

Wann sollte ein kleiner Knoten eine Erfahrung vergessen? Dieses Labor setzt drei Gedanken aus Alex’ Entwurf zusammen. Ein fester Reflex meldet einen beobachteten Ausfall. Neun veränderliche Gewichte lernen, welcher Zustand auf welchen folgt. Ein zweiter Knoten kann über kurze Zustandsmeldungen erfahren, was der erste beobachtet hat. Seit Version 0.3 bringt ein siebtes Verfahren ein kleines festes Erbe mit, das eigene Erfahrung überstimmen kann.

Das Konzept steht in Alex’ Ideensammlung eine Ordnerebene höher (`../Ideensammlung Lernendes Betriebssystem mit verblassendem Gedächtnis.md`). Sie ist die maßgebliche Fassung. Ihr Abschnitt „Versuchsstand“ hält fest, was dieses Labor gezeigt hat.

## In zwei Minuten ausprobieren

1. **Bericht.html** per Doppelklick öffnen. Die Grafik zeigt den Moment, in dem der Knoten anfängt zu warnen, und den Moment, in dem er seine Meinung ändert. Darunter stehen die Ergebnisse für sechs unterschiedliche Bedingungen.
2. Im Terminal im entpackten Ordner die ursprüngliche Demo starten. Python 3.9 oder neuer genügt.

```bash
python3 versuch.py
python3 transport.py
python3 -B -m unittest -v
```

Der erste Lauf zeigt, was der Knoten vorhersagt. Der zweite zeigt, was ein anderer Knoten tatsächlich erfahren würde, wenn eine Nachricht verloren geht. Die vollständigen Tests brauchen zusätzlich einen C++11-Compiler. Ohne ihn werden die Sketch-Tests als übersprungen gekennzeichnet.

## Was wir gelernt haben

**Seltenes Wissen braucht eine eigene Uhr.** Das erste Gedächtnis halbiert Belege alle 24 Takte. Im neuen Verfahren halbieren sie sich erst nach sechs weiteren beobachteten Folgen desselben Ausgangszustands. Eine lange Zeit ohne schwaches Signal löscht damit die Erfahrung über schwache Signale nicht. Eine neue Beobachtung kann sie aber korrigieren. Andere Halbwertszeiten ändern das Bild kaum. Die Zeitregel holt bei seltenem Vorzeichen erst bei sehr langen Halbwertszeiten auf, die Kontextregel hängt kaum davon ab (`python3 labor.py --halbwertszeiten`).

Im Kontrollversuch bestand jedes Szenario aus 20 eigenständigen Spuren mit je 480 Takten. Jede Zelle zeigt **richtige Vorwarnungen / Fehlwarnungen**. Die vollständigen Zahlen einschließlich verpasster Ausfälle und Datenmenge stehen im Bericht.

| Bedingung | Feste Regel | Lernen ohne Verblassen | Verblassen nach Zeit | Verblassen je Kontext | Erbe und Kontext |
|---|---:|---:|---:|---:|---:|
| Stabiles Vorzeichen | 1779 / 321 | 1720 / 312 | 1682 / 302 | 1693 / 308 | 1779 / 321 |
| Seltenes, meist verlässliches Vorzeichen | 170 / 38 | 113 / 29 | 0 / 0 | 94 / 24 | 169 / 38 |
| Vorzeichen verliert seine Bedeutung | 952 / 1371 | 853 / 615 | 809 / 194 | 819 / 210 | 900 / 269 |
| Alte Bedeutung kehrt zurück | 1237 / 998 | 574 / 417 | 930 / 230 | 928 / 242 | 1088 / 319 |
| Bedeutung ändert sich nach langer Stille | 641 / 932 | 553 / 415 | 513 / 87 | 523 / 159 | 603 / 216 |
| Kein Vorzeichen | 219 / 2119 | 0 / 0 | 0 / 0 | 0 / 0 | 10 / 64 |

Die Schwierigkeit beim Vergessen ist die Wahl des richtigen Maßstabs. Eine lange Pause liefert keine neuen Hinweise darauf, ob ein Zusammenhang noch gilt. Wer das frühere Wissen bewahrt, kann beim seltenen Wiedersehen sofort reagieren. Hat sich während der Pause etwas geändert, warnt derselbe Knoten zunächst zu oft. Für dauerhaft wichtige Ereignisse bleibt die Sofortmeldung deshalb eine feste Regel.

**Ein kleines Erbe ersetzt den Anlauf, ein großes wird zum Vorurteil.** „Erbe und Kontext“ beginnt mit drei festen Beobachtungen „SCHWACH → AUSFALL“. Drei ist der Mindestbeleg einer Warnung, das Erbe trägt also ab dem ersten schwachen Signal. Es verblasst nie, eigene Erfahrung kann es aber überstimmen. Auf leerem Gedächtnis genügen dafür drei beobachtete Folgen „SCHWACH → OK“. Wo das Erbe stimmt, warnt der Knoten so oft richtig wie die feste Regel. Verliert das Vorzeichen seine Bedeutung, behält er 95 % ihrer richtigen Vorwarnungen bei einem Fünftel ihrer Fehlwarnungen. Ohne Vorzeichen kostet das Erbe 64 Fehlwarnungen, die feste Regel 2119. Mit zwölf festen Beobachtungen wären es 1325 (`python3 labor.py --erbe-reihe`). Der Entwicklungssatz zeigt dasselbe Bild.

**Der eigene Körper kann das Erbe widerlegen.** Unter Last wärmt sich der S3 langsam von 36 auf 38 bis 39 °C. Auf „warm“ folgt im nächsten Takt fast nie „heiß“. Der Knoten mit Erbe warnt deshalb dreimal wie mitgegeben, dann haben ihn drei eigene Folgen „SCHWACH → SCHWACH“ überstimmt. Die feste Regel warnt weiter bei jedem warmen Takt. Für träge Signale ist ein Takt Vorhersage zu kurz.

**Eine gesendete Meldung ist noch keine empfangene Meldung.** Im zweiten Versuch dauert der Ausfall 20 Takte. Geht genau die erste Ausfallmeldung verloren, übersieht das reine Melden von Zustandswechseln den gesamten Ausfall. Mit einer zusätzlichen Zustandsmeldung spätestens alle fünf Takte erfährt die Gegenstelle in Takt 11 vom Ausfall in Takt 6. Dafür sendet der Knoten im 36-Takt-Versuch 40 statt 15 Nutzbytes. Beim Senden in jedem Takt wären es 180. Bei vollständiger Funkstille kann die Gegenstelle nur kenntlich machen, ab wann ihr letztes Wissen zu alt ist.

## Was jetzt benutzbar ist

- **Eine eigene Messung.** Ein Python-Werkzeug prüft die TCP-Erreichbarkeit eines eigenen Dienstes und speichert Zeit, Verbindungsdauer und Ergebnis. Die beigefügte lokale Aufzeichnung enthält sechs erfolgreiche und sechs abgelehnte Verbindungen nach einem absichtlichen Stopp.
- **Ein Gedächtnis mit Neustart.** Alle drei Lernregeln (Zeit, Kontext, Erbe) können ihren Zustand auf dem Rechner sichern und mit absoluten Takten fortsetzen. Messlücken erzeugen keine erfundenen Übergänge. Der ESP32-Sketch hat eigene Befehle zum Sichern und Laden. Das Erbe gehört zur Regel. Ein Stand mit abweichendem Erbe wird beim Laden abgewiesen.
- **Drei übersetzte Firmwarevarianten.** Zeit, Kontext und Erbe wurden für den klassischen ESP32 (`esp32dev`) und für Alex’ ESP32-S3-N16R8 (`esp32s3`) gebaut. Der identische Sketchcode wurde im Hosttest pro Variante über 57.840 Beobachtungen mit Python verglichen. Für einen physischen Lauf liegt ein serieller Prüfer bei. Seit 0.3 übersteht er einen langsamen Start, bei dem das Board wiederholte Neustartbefehle alle beantwortet. Auf Alex’ ESP32-S3 bestanden alle drei Varianten am 5. November die Demo mit 240 von 240 Antworten. Die Erbe-Variante behielt ihren Lernstand über eine Stromtrennung.
- **Körpersignale.** Seit 0.4 misst der S3 im Körpermodus in eigenem Takt Chiptemperatur, freien Speicher und Schleifenlücke, stuft sie ein und lernt damit. `koerper.py` zeichnet auf und rechnet jede Entscheidung nach. Mit `--last` arbeitet Kern 0 in einem Rhythmus und wärmt den Chip, die eingebaute LED zeigt den Zustand.
- **Ein reproduzierbarer Übergabestand.** 42 automatisierte Tests waren erfolgreich. Der Versuchsbericht läuft offline. Quellcode, Messdateien und eine eingefrorene Kopie der Originalnotizen liegen im Ordner, die Lieferungen 0.1 und 0.2 unter `../archiv`.

## Womit Alex und Claude weitermachen sollten

**Zuerst einen realen Fall wählen, in dem ein Takt Vorwarnzeit eine Handlung ermöglicht.** Ein Beispiel wäre der Wechsel auf einen zweiten Meldeweg, bevor ein Dienst unerreichbar wird. Alex legt fest, wie teuer eine unnötige Umschaltung und wie teuer ein verpasster Ausfall ist. Claude kann dann alle sieben Verfahren auf derselben echten Spur vergleichen. Die Demo, die der Rechner bereits ausgewertet hat, besteht das Gerät inzwischen, auch über eine Stromtrennung hinweg (`wiederanlauf.py`).

**Offen ist eine Grundsatzfrage.** Laut Ideensammlung steigt die Stärke einer Erinnerung bei jedem Abruf. Im Labor verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel. Ein möglicher Ausgleich wären zwei Werte pro Eintrag: ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf. Die Entscheidung liegt bei Alex.

Die Befehle, Dateiformate, Abnahmekriterien und ein Einstiegsprompt stehen in **UEBERGABE.md**. **Ideensammlung-original.md** ist die eingefrorene Fassung vom 4. November, auf der Version 0.2 aufbaut.
