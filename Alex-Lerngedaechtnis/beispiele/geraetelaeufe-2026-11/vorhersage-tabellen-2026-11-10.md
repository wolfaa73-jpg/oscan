# Temperaturvorhersage

Anpassen: koerper-startwert-24h-2026-11-06.csv, prüfen: koerper-startwert-24h-2026-11-07.csv. Mittel der Anpass-Aufnahme 37.19 °C, der Prüf-Aufnahme 37.56 °C.

## H = 30, Prüf-Aufnahme

86250 Takte, davon 43140 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil von „bleibt“ |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 0.630 | 0.890 | 0.600 | 0.660 | 100.0 % |
| Mittel | 0.871 | 1.062 | 0.850 | 0.892 | 138.2 % |
| Körper, fest | 0.480 | 0.595 | 0.474 | 0.485 | 76.2 % |
| Körper, lernt mit | 0.544 | 0.688 | 0.537 | 0.551 | 86.3 % |
| Mit Rhythmus, fest | 0.462 | 0.572 | 0.457 | 0.467 | 73.3 % |

## H = 30, Anpass-Aufnahme (Kontrolle)

86250 Takte, davon 43140 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil von „bleibt“ |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 0.683 | 0.954 | 0.618 | 0.747 | 100.0 % |
| Körper, fest | 0.491 | 0.607 | 0.476 | 0.507 | 72.0 % |
| Mit Rhythmus, fest | 0.466 | 0.578 | 0.451 | 0.480 | 68.2 % |

Gewichte „Körper, fest“ (Konstante, Mittel5, Steigung, Last, Last60, Last120): 9.410, 0.676, -0.298, -0.641, 13.990, -30.947

## H = 60, Prüf-Aufnahme

86220 Takte, davon 43140 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil von „bleibt“ |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 0.955 | 1.204 | 0.776 | 1.135 | 100.0 % |
| Mittel | 0.871 | 1.062 | 0.981 | 0.761 | 91.2 % |
| Körper, fest | 0.472 | 0.589 | 0.452 | 0.492 | 49.4 % |
| Körper, lernt mit | 0.615 | 0.795 | 0.641 | 0.590 | 64.4 % |
| Mit Rhythmus, fest | 0.466 | 0.582 | 0.444 | 0.487 | 48.7 % |

## H = 60, Anpass-Aufnahme (Kontrolle)

86220 Takte, davon 43140 bis 60 Takte nach einem Lastwechsel.

| Verfahren | Betragsfehler °C | Wurzelfehler °C | nach Lastwechsel | Rest | Anteil von „bleibt“ |
| --- | ---: | ---: | ---: | ---: | ---: |
| bleibt | 1.042 | 1.303 | 0.813 | 1.271 | 100.0 % |
| Körper, fest | 0.475 | 0.591 | 0.471 | 0.479 | 45.6 % |
| Mit Rhythmus, fest | 0.465 | 0.578 | 0.460 | 0.469 | 44.6 % |

Gewichte „Körper, fest“ (Konstante, Mittel5, Steigung, Last, Last60, Last120): 19.527, 0.700, -0.357, -4.373, 9.828, -43.371
