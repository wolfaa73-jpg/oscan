# Vorab: 24-h-Wiederholung mit repariertem Leck

Festgelegt am 7. November 2026 gegen 17:10, vor dem Start der Aufnahme. Alex hat sie für die Nacht freigegeben, sie beginnt direkt nach dem 2-h-Zufallstest.

## Frage

Hält der Befund vom 6. November, wenn die Welt so ist wie geplant? Damals lief das tiefe Leck nur in 128 von 209 Durchgängen voll. Darüber lag ein ungeplantes, stundenlanges Muster, siehe `vorab-zufall-2h-2026-11-07-nachtrag.md`. Mit dem reparierten Leck sollte jeder tiefe Durchgang volllaufen, und die Speicherwelt ist dann das 8/8-Blockmuster.

## Aufbau

- **Firmware:** `esp32s3-startwert` mit repariertem Leck und `SPEICHER`-Zeilen, dieselbe wie im 2-h-Lauf `…-07b`.
- **Einstellungen** wie am 6. November, alle ausdrücklich übergeben:

  ```
  --regel startwert --intervall-ms 1000 --takte 86400 --blick 60
  --grenzen 380 390 65536 16384 20000 200000 --last 120 120
  --leck 4096 12288 5 120 32768 4278255360
  --bremse 10 10 300 5 120 --sichern-alle 600
  ```

  Nach dem Start wird die JSON Feld für Feld mit der vom 6. November verglichen. Abweichen darf nur `beginn`.
- Die Aufnahme heißt `koerper-startwert-24h-2026-11-07.csv`, ohne `--mqtt`, weil sie nachts läuft.
- Das Gerät wird vorher nicht neu gestartet. Es läuft seit dem Flashen kurz vor 17:04 durch, wie am 6. November.

## Prüfung

- Daniels Protokoll **24h-v1**, unverändert, im Worktree des Stands 8e8ad19:
  - `python3 -B -m unittest test_pruefung24h`
  - `python3 -B pruefung24h.py <aufnahme> > <bericht>`
- Berichtet werden Rückgabe, Bericht, Commit und Laufzeit unverändert, wie beim ersten Mal.
- Die Hypothesen H1, H2 und H3a/b/c gelten wie im Protokoll. Ich ändere an ihnen nichts.
- **Vor dem Protokoll sieht niemand in die Körperzeilen.** Erlaubt ist nur die Speicherdatei, denn sie zeigt den Reiz, nicht die Entscheidungen.

## Reizkontrolle

- **R1:** Jeder geplant tiefe Durchgang erreicht weniger als 16.384 B frei. Jeder flache bleibt darüber.
- Geprüft wird das in der Speicherdatei: `BODEN`-Zeilen der Durchgänge nach Muster.
- Wie oft das Leck kleinere Blöcke brauchte (`KLEIN`), wird mitgezählt. Am 6. November lag dieser Fall bei 81 von 209.
- Scheitert R1, sind die Protokollzahlen trotzdem gültig gemessen, nur ist die Welt dann nicht die geplante. Das steht dann im Bericht.

## Meine Erwartung, ohne Hypothesenstatus

- Speicherphasen: etwa 209 statt 128.
- Die feste Regel verpasst weiter keine Phase.
- Der Startwert verpasst vor allem das erste tiefe Leck nach einem flachen Block. Das sind zwei Wechsel je 32 Durchgänge, in 24 h etwa 26.
