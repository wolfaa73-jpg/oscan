# Nachtrag zu vorab-zufall-2h-2026-11-07.md

Geschrieben am 7. November 2026 nach Laufende um 15:28:57. Die Vorab-Datei bleibt unverändert, SHA-256 `59c2fe527dcd40fa3904fd3d911e64c118639778ef8d499a91b7778a75eedef1`.

## Ergebnis gegen die Hypothesen

- **Z0 erfüllt.** `koerper.py pruefen`: Alle 7.200 Einstufungen und Entscheidungen des Geräts stimmen mit Python überein.
- **Z1 bis Z4 nicht prüfbar.** Kein tiefes Leck erreichte den Ausfall, deshalb gab es keine einzige Speicherphase.
  - Alle 17 geplant tiefen Durchgänge blieben bei 17.804 B stehen. Die Ausfallgrenze liegt bei 16.384 B.
  - Die 18 flachen Durchgänge endeten bei 34.252 B.
  - Das liegt nicht an der Auswertung, sondern am Reiz, siehe unten.

## Fehler im Aufbau: falsche Grenzen

Die Vorab-Datei sagt „Die Grenzen sind dieselben wie im 24-h-Lauf“. Das stimmt nicht.

- Die Aufnahme lief ohne `--grenzen`, also mit der Vorgabe `ERKUNDUNG` aus koerper.py: Temperatur 50,0/60,0 °C statt 38,0/39,0 °C. Speicher- und Lückengrenzen waren gleich.
- Folge: keine einzige Wärmephase. Im Vergleich V waren es 233.
- Dasselbe gilt für den 15-min-MQTT-Test am Vormittag. Der war nur ein Melder-Test und keine Auswertung.
- Für Z1 bis Z4 ändert der Fehler nichts, denn das Leck hätte auch mit richtigen Grenzen den Ausfall nicht erreicht.
- Künftig gehören die Grenzen ausdrücklich in jeden Aufnahmebefehl, und vor dem Start wird die JSON mit der Vergleichsaufnahme abgeglichen.

## Befund: Das tiefe Leck erreicht den Ausfall nicht zuverlässig

Das zeigt sich erkundend auch im 24-h-Lauf, dessen Prüfung abgeschlossen ist.

| Aufnahme | tiefe Durchgänge | davon Ausfall erreicht | Tiefstwerte |
| --- | --- | --- | --- |
| 6 h, 05.11. (frisch geflasht) | 56 | 56 | 13.844 B |
| 24 h, 06.11., erste 2 h (V) | 19 | 19 | 13.692 B |
| 24 h, 06.11., ganz | 209 | 128 | 13.548–13.836 oder 17.660–17.948 B |
| 2 h, 07.11. (dieser Lauf) | 17 | 0 | 17.804 B |

Im 24-h-Lauf kommt das stundenweise. Die Angabe zählt je Laufstunde, wie viele tiefe Durchgänge den Ausfall erreichten (erreicht/tief):

| Stunde | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| erreicht/tief | 10/10 | 9/9 | 9/9 | 10/10 | 2/9 | 0/9 | 0/8 | 3/8 | 8/8 | 8/8 | 8/8 | 9/9 |

| Stunde | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| erreicht/tief | 9/9 | 9/9 | 10/10 | 9/9 | 7/10 | 0/8 | 0/8 | 8/8 | 0/8 | 0/8 | 0/8 | 0/9 |

**Wie es dazu kommt.** Ein Block belegt 4.112 B, das sind 4.096 B und 16 B Verwaltung.

- Die Firmware belegt weiter, solange `frei − boden ≥ block` gilt.
- Bei 17.804 B frei ist das erfüllt, denn 17.804 − 12.288 = 5.516 ≥ 4.096. Der 85. Block hätte also kommen müssen.
- Weil er nicht kam, muss `heap_caps_malloc` gescheitert sein.
- Wahrscheinlich ist der Speicher zerstückelt, und der größte freie Block ist kleiner als 4 KB. **Gemessen ist das nicht.** Prüfen ließe es sich, indem die Firmware bei `voll()` den größten freien Block mitschreibt.
- Die Lastaufgabe läuft durchgehend und wird nicht je Durchgang neu angelegt. Sie scheidet als einfache Ursache aus.

**Folge für den 24-h-Prüfbericht.** Die Zahlen bleiben, wie gemessen. Die Speicherwelt war aber nicht das geplante 8/8-Muster.

- Darüber lag ein zweites, ungeplantes Muster. In stundenlangen Blöcken lief auch kein tiefes Leck voll.
- H1 ist erfüllt, mit 81 % Präzision beim knappen Speicher. Ein Teil davon ist das Lernen dieser langen Blöcke, und darin ist „letzter Durchgang“ stark.
- Sauber im Sinne des Plans ist nur der 6-h-Lauf.

## Was der Lauf trotzdem zeigt, erkundend

- **Bremse, 46 Ausfälle:**
  - Je Signal hat jedes Verfahren außer „nie warnen“ alle 46 vorgewarnt.
  - Die feste Regel warnte bei 30 und 60 Takten vor allen 46, auch grob.
  - Das Gerät rechnet grob mit Startwert h6/.6 und Blick 60. Es warnte innerhalb von 60 Takten vor 40 von 46, im Vergleich V vor 42 von 46. Innerhalb von 30 Takten waren es 33 von 46, in V 38 von 46, direkt aus den Gerätezeilen gezählt.
  - Vergleichbar ist das nicht sauber, weil die Wärme fehlte und kein Leck volllief.
- **Melder, 2 h:** Er hat ohne Störung gesendet. Am Ende stand `aktiv:false` am Broker, kein Kindprozess blieb hängen, das Dashboard lief ohne Neustart und ohne Fehlerzeile.

## Für eine Wiederholung

- Grenzen ausdrücklich angeben: `--grenzen 380 390 65536 16384 20000 200000`.
- Den S3 vorher neu starten. Nach dem Flashen und in den ersten vier Stunden des 24-h-Laufs liefen alle tiefen Lecks voll.
- Eine Vorprüfung einbauen: Erreicht der erste tiefe Durchgang 16.384 B nicht, wird abgebrochen.
- Besser noch: den größten freien Block mitschreiben, damit sich die Ursache messen lässt.
