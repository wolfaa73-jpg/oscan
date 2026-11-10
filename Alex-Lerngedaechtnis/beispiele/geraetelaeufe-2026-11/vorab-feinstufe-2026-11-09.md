# Vorab: Feinere Speicherstufen für den Lerner (explorativ)

Festgelegt am 9. November 2026 um 21:11, bevor der Feinstufen-Lerner zum ersten Mal rechnet.

**Explorativ.** Die Aufnahmen sind bekannt, auch ihre Leckböden: Flache Durchgänge halten bei 34.060 bis 34.396 B, tiefe fallen von unter 32 KiB in genau 4 Takten in den Ausfall. Kein Befund hieraus ersetzt einen vorab festgelegten Gerätelauf.

## Frage

Lernt der Lerner „Startwert h6/.6“ die Grenze zwischen tiefem und flachem Leck selbst, wenn er den freien Speicher feiner sieht als OK, KNAPP und VOLL? Was kostet das an Vorlauf?

## Verfahren

Alle werden berichtet, keines wird ausgewählt.

- Nur das Speichersignal, je Signal wie im Prüfprotokoll 24h-v1.
- Wörter: OK über der Grenze für knapp, K1 bis KN für KNAPP in N gleich breiten Stufen zwischen den Grenzen für knapp und voll (K1 oben), VOLL bis zur Grenze für voll. Die Grenzen stammen aus der JSON der Aufnahme, verglichen wird mit `<=` wie in vokabular.stufen_je_signal.
- N = 1, 2, 4, 8 und 16. N = 1 ist der bisherige Lerner. Er muss Takt für Takt dieselben Warnungen geben wie „Startwert h6/.6“ aus pruefung24h.py (kostenlabor.wahrscheinlichkeiten, Erb-Halbwertszeit 6, Schwelle 0,6), sonst gilt keine Zahl.
- Erbe: Jede Stufe Ki erbt „Ki → VOLL“ mit 3 Beobachtungen, die alte Bedeutung „knapp führt zu voll“ für jede Teilstufe. Es verblasst mit jedem eigenen Ausgang aus der Stufe, Halbwertszeit 6. Erfahrung nach der Kontextregel mit Halbwertszeit 6. Warnung bei Mindestbeleg 3 und Schwelle 0,6, der Blick über kern.blick_voraus.
- Maßstäbe: Feste Regel (warnt in jeder Stufe Ki), Immer warnen, Nie warnen.
- Horizonte 30 und 60.
- Aufnahmen: alle mit Leckmuster und vollem Takt, also muster-6h vom 5.11., startwert-24h vom 6. und 7.11., zufall-2h vom 7.11. und 7.11.b.

## Zählung

- pruefung24h.zaehlen unverändert, über die groben Speicherwörter: Warnanteil, Präzision, Phasen ohne Warnung, Kphase und Ktakt mit r = 10.
- Dazu je Leckdurchgang, also je Lauf außerhalb von OK: tief, wenn er VOLL erreicht, sonst flach. Ein Wechsel ist ein tiefer Durchgang direkt nach einem flachen.
- Berichtet werden vorgewarnte Wechsel, flache Durchgänge mit Warnung, Warnungen in OK und der Vorlauf als Median und kleinster Wert. Vorlauf heißt: Takte vom ersten Warntakt im Fenster bis zum Beginn von VOLL.

## Erwartung, vorher notiert

- N = 2 trennt nicht: Die Grenze bei 40 KiB liegt über dem flachen Halt, also sollte sich N = 2 verhalten wie N = 1.
- Ab N = 4 liegt eine Stufengrenze unter dem flachen Halt. Erwartet in den sauberen Aufnahmen: kein verpasster Wechsel, kaum Warnungen in flachen Durchgängen, nach Ruhe 3 bis 4 Takte Vorlauf.
- In Aufnahmen mit hängendem Leck (24 h vom 6.11., 2 h vom 7.11.) ist die unterste Stufe selbst mehrdeutig. Dort kann der Vorteil schrumpfen.
