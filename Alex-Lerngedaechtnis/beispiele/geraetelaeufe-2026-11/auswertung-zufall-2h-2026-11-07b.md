# Auswertung: zwei Stunden mit unregelmäßigem Leck, zweiter Anlauf

Gerechnet am 7. November 2026 ab 19:05, nach `vorab-zufall-2h-2026-11-07b.md` (SHA 34e6b396…), unverändert.

- **Aufnahme:** `koerper-startwert-zufall-2h-2026-11-07b.csv`, 17:04:05 bis 19:04:05, 7.200 Takte, rc 0.
- **Werkzeuge:** `koerper.py pruefen` im Arbeitsstand. `pruefung24h.auswertung` aus dem eingefrorenen Stand 8e8ad19, aufgerufen über `zufall2h_auswertung.py` und `zufall2h_phasen.py` im Scratchpad. Die Phasenzählung ist gegen `pruefung24h.zaehlen` abgeglichen.

## Reiz

- **R1 erfüllt:** Geprüft in der Speicherdatei, 35 `BODEN`-Zeilen.
  - 17 geplant tiefe Durchgänge, alle unter 16.384 B. Der höchste Boden liegt bei 15.836.
  - 18 geplant flache, alle darüber. Der tiefste Boden liegt bei 34.204.
  - Die Folge entspricht dem Vorab-Muster: Durchgang 0 bis 33 wie geplant, Durchgang 34 flach.
- **KLEIN:** 5 Ereignisse in 5 Durchgängen, nämlich 26, 28, 29, 30 und 32.
  - Jedes Ereignis liegt im 84. Leckblock. 17.900 B sind dann frei, das größte Stück hat 4.084 B, insgesamt gibt es 10 freie Stücke.
  - Ein 2-KiB-Block geht noch hinein, der Boden liegt dann bei 15.836.
  - In Durchgang 0 bis 25 gab es kein KLEIN, der Boden lag dort immer bei 13.644.
- **Damit lief das reparierte Leck zum ersten Mal auf dem Gerät.** Mit der alten Firmware wären diese fünf Durchgänge bei 17.900 B stehen geblieben, ohne Ausfall. Das ist dasselbe Bild wie in den Stunden am 6. November, in denen das Leck nicht volllief.
- **Ablauf in allen 17 tiefen Durchgängen gleich:**
  - SCHWACH ab Takt 72 des Durchgangs, AUSFALL ab Takt 84, dann 6 Takte AUSFALL.
  - Nur der Tiefstwert unterscheidet sich, 13.644 oder 15.836. Beide liegen unter `heap_ausfall`. Die Stufenfolge, aus der die Verfahren lernen, ist also in KLEIN-Durchgängen dieselbe.

## Hypothesen, je Signal, H=30, Speicher

| | Vorab | Gemessen | Ergebnis |
| --- | --- | --- | --- |
| Z0 Gerät | 0 Abweichungen | 7.200 von 7.200 gleich | erfüllt |
| Z1 Feste Regel | 0 verpasst | 0 von 17 | erfüllt |
| Z2 Startwert h6/.6 | mindestens 4 verpasst (doppelt und plus 3 gegen V mit 1), mindestens die Hälfte tief nach flach | 3 von 17, alle 3 tief nach flach | **nicht erfüllt**, 3 statt mindestens 4 |
| Z3 Präzision nur_hoch | höchstens Grundrate + 15 Punkte | 48,9 % bei 46,6 %, also + 2,3 | erfüllt, trennt aber nicht |
| Z3b Präzision nur_hoch | unter 65,1 % aus V | 48,9 % | erfüllt |
| Z4 Letzter Durchgang | mindestens 6 verpasst | 11 von 17 | erfüllt |

## Nur berichtet, ohne Hypothese

- **Verpasste Durchgänge, je Signal, H=30:**
  - **h6/.6:** Durchgang 26, 28 und 32.
  - **Startwert #4:** 18, 20, 26, 28 und 32.
  - **Letzter Durchgang:** Durchgang 0 und alle 10 Lecks, die tief nach einem flachen kommen.
  - In jedem Verfahren ist jeder verpasste Durchgang ein „tief nach flach“, außer Durchgang 0.
- **h6/.6 verpasst nur die letzten drei der zehn Übergänge „tief nach flach“.**
  - Sie liegen alle nach der längsten Flachstrecke (Durchgang 21 bis 25) und zugleich in der KLEIN-Zeit.
  - Als Ursache scheidet KLEIN aus, denn die Stufenfolge ist identisch.
  - Ob es an der langen Flachstrecke liegt oder daran, dass der Startwert verblasst, kann dieser Lauf nicht trennen.
  - Je Übergang gerechnet verpasst h6/.6 hier 3 von 10. In V war es 1 von 2.
- **grob, H=30, Speicher, wie das Gerät rechnet:**
  - Feste Regel 0, h6/.6 2, #4 3 und Letzter Durchgang 11 von 17 verpasst.
  - Zum Vergleich V: 0, 3, 5 und 10 von 19.
- **je Signal, H=60, Speicher:** h6/.6 verpasst 1, #4 0 von 17. In V waren es 1 und 1 von 18.
- **Gesamt, je Signal, H=30:** h6/.6 verpasst 9 von 301, in V 15 von 279.
- **Wärme, je Signal, H=30:** Diesmal gab es Wärmephasen, weil die richtigen Grenzen galten.
  - Feste Regel 0, h6/.6 28, #4 45 und Letzter Durchgang 282 von 282 verpasst.
  - V: 0, 26, 54 und 213 von 233.
- **Schleife, H=30:** In NEU und V gleich, 46 Phasen. Kein Verfahren verpasst eine.
- **Ampel:** nicht gerechnet. Vor den Daten habe ich sie nicht genau genug festgelegt, um sie jetzt ohne Nachjustieren zu rechnen.

## Nachtwiederholung, Stand beim Schreiben

- **Start und Einstellungen:** Die Aufnahme `koerper-startwert-24h-2026-11-07.csv` begann um 19:04:28. Ihre JSON stimmt mit der vom 6. November überein, nur `beginn` weicht ab. Verglichen wurden 15 Felder.
- **Erster tiefer Durchgang:** KLEIN bei Takt 85 (17.900 frei, größtes Stück 4.084), Boden 15.836 bei Takt 86. R1 ist für den ersten Durchgang erfüllt.
- Die Nacht beginnt also in dem Zustand, in dem das Leck am 6. November stehen blieb.
- Die Körperzeilen sind bis zum Protokoll ungesehen.
