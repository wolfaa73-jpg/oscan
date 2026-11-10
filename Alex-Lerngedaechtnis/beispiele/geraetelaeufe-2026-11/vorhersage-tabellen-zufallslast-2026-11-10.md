# Temperaturvorhersage, zwei Hälften

koerper-zufallslast-8h-2026-11-10.csv: 28800 Takte, anpassen bis Takt 14400, prüfen ab Takt 14521. Temperatur 35.0 bis 40.0 °C, 183 Lastwechsel.

## H = 30

14250 Prüftakte, davon 5520 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil des besseren Maßstabs |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 0.434 | 0.709 | 0.463 | 0.417 | 100.0 % |
| Mittel | 0.713 | 0.872 | 0.565 | 0.806 | 164.1 % |
| ohne Lastgeschichte | 0.440 | 0.567 | 0.426 | 0.449 | 101.2 % |
| Körper | 0.437 | 0.560 | 0.399 | 0.460 | 100.5 % |
| Körper, lernt mit | 0.566 | 0.781 | 0.667 | 0.502 | 130.4 % |
| mit Takten seit dem Lastwechsel | 0.415 | 0.550 | 0.379 | 0.438 | 95.5 % |

## H = 60

14220 Prüftakte, davon 5520 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil des besseren Maßstabs |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 0.666 | 0.934 | 0.615 | 0.698 | 100.0 % |
| Mittel | 0.714 | 0.873 | 0.683 | 0.734 | 107.2 % |
| ohne Lastgeschichte | 0.641 | 0.740 | 0.558 | 0.694 | 96.4 % |
| Körper | 0.593 | 0.715 | 0.466 | 0.675 | 89.1 % |
| Körper, lernt mit | 0.920 | 1.193 | 0.940 | 0.907 | 138.2 % |
| mit Takten seit dem Lastwechsel | 0.553 | 0.690 | 0.448 | 0.619 | 83.1 % |
