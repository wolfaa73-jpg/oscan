# Vorab: zwei Stunden mit unregelmäßigem Leck, zweiter Anlauf

Festgelegt am 7. November 2026 vor dem Start der Aufnahme. Der erste Anlauf war nicht prüfbar, siehe `vorab-zufall-2h-2026-11-07.md` und den Nachtrag dazu: falsche Temperaturgrenzen, und kein tiefes Leck lief voll.

## Was sich geändert hat

- **Firmware:** `esp32s3-startwert` mit dem reparierten Leck. Passt ein ganzer Block in kein freies Stück mehr, über dem Boden ist aber noch genug frei, nimmt es halb so große Blöcke, bis 1 KiB. Dazu kommen die `SPEICHER`-Zeilen in `<name>.speicher.csv`. Die Entscheidungen des Knotens sind unverändert, Demo 240/240.
- **Einstellungen** wie der 24-h-Lauf vom 6. November, ausdrücklich übergeben, auch `--grenzen 380 390 65536 16384 20000 200000` und `--sichern-alle 600`. Einziger Unterschied ist das Leckmuster **2347385558 = 0x8BEA42D6**, gezogen wie im ersten Anlauf. Nach dem Start wird die JSON Feld für Feld mit der des 24-h-Laufs verglichen.
- Durchgang 0 bis 33: `TFFTFTFFTFTTTTFTTFTFTFFFFFTFTTTFTF` (T = tief, F = flach). Zehnmal kommt ein tiefes Leck direkt nach einem flachen.

## Reizkontrolle

- **R1:** Jeder geplant tiefe Durchgang erreicht weniger als 16.384 B frei.
- Ich prüfe das nur in der Speicherdatei, nie in den Körperzeilen. Scheitert schon der erste tiefe Durchgang, breche ich ab. Scheitert ein späterer, ist der Lauf für Z1 bis Z4 nur eingeschränkt prüfbar, und das steht dann im Bericht.

## Rechnung

Unverändert aus dem ersten Anlauf:

- `pruefung24h.auswertung` im eingefrorenen Stand 8e8ad19, H=30 und H=60, grob und je Signal.
- **Vergleich V:** dieselbe Rechnung auf den ersten 7.200 Takten des 24-h-Laufs. Dort liefen alle 19 tiefen Durchgänge voll.
- **Leckdurchgang:** ein Block mit Reizbit 2, tief bei weniger als 16.384 B frei, „tief nach flach“, wenn der vorige flach war.

## Hypothesen, je Signal, H=30

Die Grenzen sind unverändert aus dem ersten Anlauf übernommen. **Die Zahlen von V kenne ich inzwischen** aus dessen Auswertung:

| Verfahren in V | Speicherphasen verpasst |
| --- | --- |
| Feste Regel | 0 von 19 |
| Startwert h6/.6 | 1 von 19 |
| Letzter Durchgang | 3 von 19 |

Bei h6/.6, Speicher nur_hoch, lag die Präzision bei 65,1 % gegen 52,3 % Grundrate. Angepasst habe ich keine Grenze.

- **Z0 Gerät:** `koerper.py pruefen` besteht, 0 Abweichungen.
- **Z1 Feste Regel:** 0 unangekündigte Speicherphasen.
- **Z2 Startwert h6/.6:** Er verpasst mindestens doppelt so viele Speicherphasen wie in V und mindestens 3 mehr, also mindestens 4. Mindestens die Hälfte davon sind tiefe Lecks nach einem flachen.
- **Z3 Startwert h6/.6, Speicher nur_hoch:** Präzision höchstens Grundrate + 15 Prozentpunkte. V erfüllt das schon, mit +12,8 Punkten, Z3 trennt die beiden Welten also nicht.
- **Z3b, neu und vor den Daten ergänzt, weil Z3 nicht trennt:** Die Präzision liegt unter der von V, also unter 65,1 %.
- **Z4 Letzter Durchgang:** mindestens 6 unangekündigte Speicherphasen.

Nur berichtet, ohne Hypothese:

- grob, wie es das Gerät rechnet,
- H=60, Wärme und Schleife,
- die Ampel, bei der die feste Regel entscheidet und der Lerner die Stufe setzt,
- wie oft das Leck kleinere Blöcke brauchte (Ereignis `KLEIN`).
