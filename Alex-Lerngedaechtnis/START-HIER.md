# Alex’ Lernlabor

**Stand 0.2 · 4. November 2026 · Arbeitsprojekt für Alex und Claude**

Wann sollte ein kleiner Knoten eine Erfahrung vergessen? Dieses Labor setzt drei Gedanken aus Alex’ Entwurf zusammen. Ein fester Reflex meldet einen beobachteten Ausfall. Neun veränderliche Gewichte lernen, welcher Zustand auf welchen folgt. Ein zweiter Knoten kann über kurze Zustandsmeldungen erfahren, was der erste beobachtet hat.

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

**Seltenes Wissen braucht eine eigene Uhr.** Das erste Gedächtnis halbiert Belege alle 24 Takte. Im neuen Verfahren halbieren sie sich erst nach sechs weiteren beobachteten Folgen desselben Ausgangszustands. Eine lange Zeit ohne schwaches Signal löscht damit die Erfahrung über schwache Signale nicht. Eine neue Beobachtung kann sie aber korrigieren.

Im Kontrollversuch bestand jedes Szenario aus 20 eigenständigen Spuren mit je 480 Takten. Jede Zelle zeigt **richtige Vorwarnungen / Fehlwarnungen**. Die vollständigen Zahlen einschließlich verpasster Ausfälle, Datenmenge und fester Vergleichsregeln stehen im Bericht.

| Bedingung | Lernen ohne Verblassen | Verblassen nach Zeit | Verblassen je Kontext |
|---|---:|---:|---:|
| Seltenes, meist verlässliches Vorzeichen | 113 / 29 | 0 / 0 | 94 / 24 |
| Vorzeichen verliert seine Bedeutung | 853 / 615 | 809 / 194 | 819 / 210 |
| Alte Bedeutung kehrt zurück | 574 / 417 | 930 / 230 | 928 / 242 |
| Bedeutung ändert sich nach langer Stille | 553 / 415 | 513 / 87 | 523 / 159 |

Die Schwierigkeit beim Vergessen ist die Wahl des richtigen Maßstabs. Eine lange Pause liefert keine neuen Hinweise darauf, ob ein Zusammenhang noch gilt. Wer das frühere Wissen bewahrt, kann beim seltenen Wiedersehen sofort reagieren. Hat sich während der Pause etwas geändert, warnt derselbe Knoten zunächst zu oft. Für dauerhaft wichtige Ereignisse bleibt die Sofortmeldung deshalb eine feste Regel.

**Eine gesendete Meldung ist noch keine empfangene Meldung.** Im zweiten Versuch dauert der Ausfall 20 Takte. Geht genau die erste Ausfallmeldung verloren, übersieht das reine Melden von Zustandswechseln den gesamten Ausfall. Mit einer zusätzlichen Zustandsmeldung spätestens alle fünf Takte erfährt die Gegenstelle in Takt 11 vom Ausfall in Takt 6. Dafür sendet der Knoten im 36-Takt-Versuch 40 statt 15 Nutzbytes. Beim Senden in jedem Takt wären es 180. Bei vollständiger Funkstille kann die Gegenstelle nur kenntlich machen, ab wann ihr letztes Wissen zu alt ist.

## Was jetzt benutzbar ist

- **Eine eigene Messung.** Ein Python-Werkzeug prüft die TCP-Erreichbarkeit eines eigenen Dienstes und speichert Zeit, Verbindungsdauer und Ergebnis. Die beigefügte lokale Aufzeichnung enthält sechs erfolgreiche und sechs abgelehnte Verbindungen nach einem absichtlichen Stopp.
- **Ein Gedächtnis mit Neustart.** Beide Lernregeln können ihren Zustand auf dem Rechner sichern und mit absoluten Takten fortsetzen. Messlücken erzeugen keine erfundenen Übergänge. Der ESP32-Sketch hat eigene Befehle zum Sichern und Laden.
- **Zwei übersetzte Firmwarevarianten.** Beide wurden für das Referenzboard `esp32dev` gebaut. Der identische Sketchcode wurde im Hosttest pro Variante über 57.840 Beobachtungen mit Python verglichen. Für einen physischen Lauf liegt ein serieller Prüfer bei.
- **Ein reproduzierbarer Übergabestand.** 26 automatisierte Tests waren erfolgreich. Der Versuchsbericht läuft offline. Die Originalnotizen, der Quellcode, die Messdateien und das Prüfprotokoll sind im Paket.

## Womit Alex und Claude weitermachen sollten

**Zuerst einen realen Fall wählen, in dem ein Takt Vorwarnzeit eine Handlung ermöglicht.** Ein Beispiel wäre der Wechsel auf einen zweiten Meldeweg, bevor ein Dienst unerreichbar wird. Alex legt fest, wie teuer eine unnötige Umschaltung und wie teuer ein verpasster Ausfall ist. Claude kann dann alle sechs Verfahren auf derselben echten Spur vergleichen. Als erstes Geräteexperiment lässt sich der Sketch mit derselben Demo prüfen, die der Rechner bereits ausgewertet hat.

Die Befehle, Dateiformate, Abnahmekriterien und ein Einstiegsprompt stehen in **UEBERGABE.md**. **Ideensammlung-original.md** enthält Alex’ vollständige ursprüngliche Notizen.
