# Vorab: zwei Stunden mit unregelmäßigem Leck

Festgelegt am 7. November 2026 um 13:30, gut eine Minute nach Start der Aufnahme. Bis zur Auswertung sieht niemand in die Werte. Geprüft wurde vorher nur, dass die Datei wächst und die JSON die richtigen Einstellungen trägt.

## Frage

Ist der Startwert-Lerner noch sicher, wenn die Fehler nicht im Takt kommen? Im 24-h-Lauf kamen die Lecks in Blöcken, acht tiefe und dann acht flache (Muster 0xFF00FF00). Ein Gedächtnis mit Halbwertszeit 6 kann daraus lernen, dass auf flach wieder flach folgt. Echte Fehler kommen nicht in Achterblöcken. Der ungünstigste Fall für den Lerner ist ein tiefes Leck direkt nach einem flachen.

## Aufbau

- Aufnahme `koerper-startwert-zufall-2h-2026-11-07.csv`, Beginn 13:28:57, 7.200 Takte.
- Firmware `esp32s3-startwert`, Regel startwert, Blick 60, Intervall 1000 ms. Die Grenzen sind dieselben wie im 24-h-Lauf, ebenso Last 120/120 und Bremse 10 10 300 5 120.
- Leck 4096 12288 5 120 32768, Muster **2347385558 = 0x8BEA42D6**: 16 von 32 Durchgängen flach wie bisher, gezogen mit `random.Random(20261107).sample(range(32), 16)`.
  - Durchgang 0 bis 33: `TFFTFTFFTFTTTTFTTFTFTFFFFFTFTTTFTF` (T = tief, F = flach).
  - Darin kommt zehnmal ein tiefes Leck direkt nach einem flachen vor. Im alten Muster sind es in denselben Durchgängen zwei.
- Die Aufnahme beginnt ohne `--fortsetzen` und ohne `--sichern-alle`. Damit bleibt der Endstand des 24-h-Laufs im NVS erhalten. Die Entscheidungen des Geräts hängen davon nicht ab.
- `--mqtt PANEL` meldet die Warnungen nebenbei ans Panel. Das ist ein Dauertest des Melders und ist nicht Teil der Wertung.

## Rechnung

- Gerechnet wird mit `pruefung24h.auswertung` im eingefrorenen Stand 8e8ad19, unverändert, H=30 und H=60, grob und je Signal.
- **Vergleich V:** dieselbe Rechnung auf den ersten 7.200 Takten des 24-h-Laufs. Diese Takte sind ein frischer Zweistundenlauf mit Blockmuster, alles andere ist gleich.
- **Leckdurchgang:** ein zusammenhängender Block mit Reizbit 2. Er gilt als tief, wenn sein kleinster freier Speicher unter 16.384 B liegt (heap_ausfall). „Tief nach flach“ heißt, dass der vorige Durchgang flach war.

## Hypothesen, je Signal, H=30, soweit nicht anders genannt

- **Z0 Gerät:** `koerper.py pruefen` besteht, 0 Abweichungen vom Gerät.
- **Z1 Feste Regel:** 0 unangekündigte Speicherphasen, wie im 24-h-Lauf.
- **Z2 Startwert h6/.6:** Er verpasst mindestens doppelt so viele Speicherphasen wie in V und mindestens 3 mehr als in V. Mindestens die Hälfte der verpassten sind tiefe Lecks nach einem flachen.
- **Z3 Startwert h6/.6, Speicher nur_hoch:** Präzision höchstens Grundrate + 15 Prozentpunkte. Im 24-h-Lauf waren es 81 % bei 27 % Grundrate.
- **Z4 Letzter Durchgang:** mindestens 6 unangekündigte Speicherphasen. Er sagt nach einem flachen Durchgang flach voraus und muss deshalb die tiefen nach flachen verpassen. Bleibt Z4 aus, ist mein Bild vom Mechanismus falsch.

Nur berichtet, ohne Hypothese: grob, wie es das Gerät rechnet, H=60, Wärme und Schleife. Außerdem erkundend die Ampel, bei der die feste Regel entscheidet und der Lerner die Stufe setzt.
