# Verweildauer und Richtung: synthetischer Vergleich

Taktwertung ist maßgeblich. Alle Ergebnisse beschreiben künstliche Spuren, keine Geräteprüfung.
Satz: entwicklung. Freeze-Commit: noch keine unabhängige Prüfung.

Keine Parameterwahl anhand dieser Ergebnisse. Alle eigenen nichtkritischen Takte zählen;
die letzten 30 Takte liefern nur Zukunft. Hohe Signaltakte und einzelne Familien stehen in den CSVs.
Trefferquote bedeutet Anteil richtiger Warntakte, nicht Anteil vorhergesagter Phasen.
Immer warnen behält die vorhandene Sicht: grob wird bei einem fremden kritischen Signal
kein globaler Alarm ausgegeben. Deshalb kann sein Warnanteil im eigenen Signalnenner
unter 100 % liegen. In der Sicht je_signal warnt die Referenz an jedem geeigneten eigenen Takt.
Kosten r=10 sind Modellannahmen; Takt- und Phasenkosten besitzen verschiedene Fehlereinheiten.
Signalweise Kosten nicht addieren, wenn Signale dieselbe Aktion auslösen.

## grob, gesamt

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 42.17 % | 77.12 % | 71.07 % | 0/1654 | 3317.41 | 81.01 |
| Festes Erbe | 80.60 % | 69.31 % | 71.07 % | 0/1654 | 1484.22 | 207.68 |
| Startwert | 63.77 % | 72.01 % | 71.07 % | 61/1654 | 2261.42 | 160.11 |
| Ohne Erbe | 51.24 % | 73.21 % | 71.07 % | 140/1654 | 2933.00 | 138.81 |
| Letzter Durchgang | 25.58 % | 83.23 % | 71.07 % | 215/1654 | 4215.62 | 72.14 |
| Immer warnen | 100.00 % | 71.07 % | 71.07 % | 0/1654 | 242.94 | 242.94 |
| Nie warnen | 0.00 % | — | 71.07 % | 1654/1654 | 5967.74 | 277.89 |
| Verweildauer und Richtung | 46.19 % | 76.10 % | 71.07 % | 103/1654 | 3108.84 | 110.01 |

## grob, temperatur

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 36.88 % | 28.68 % | 24.18 % | 0/441 | 1558.52 | 252.57 |
| Festes Erbe | 70.49 % | 23.62 % | 24.18 % | 0/441 | 1240.24 | 516.95 |
| Startwert | 55.77 % | 24.79 % | 24.18 % | 26/441 | 1397.03 | 407.11 |
| Ohne Erbe | 44.81 % | 24.55 % | 24.18 % | 53/441 | 1589.94 | 333.55 |
| Letzter Durchgang | 22.37 % | 29.43 % | 24.18 % | 87/441 | 1841.13 | 166.23 |
| Immer warnen | 87.46 % | 24.41 % | 24.18 % | 0/441 | 906.94 | 634.76 |
| Nie warnen | 0.00 % | — | 24.18 % | 441/441 | 2321.74 | 74.09 |
| Verweildauer und Richtung | 40.40 % | 26.72 % | 24.18 % | 26/441 | 1569.69 | 288.61 |

## grob, speicher

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 37.82 % | 44.70 % | 40.73 % | 0/721 | 2426.53 | 195.85 |
| Festes Erbe | 72.29 % | 38.32 % | 40.73 % | 0/721 | 1637.53 | 417.44 |
| Startwert | 57.19 % | 40.50 % | 40.73 % | 21/721 | 1963.42 | 322.13 |
| Ohne Erbe | 45.96 % | 41.80 % | 40.73 % | 55/721 | 2265.37 | 259.66 |
| Letzter Durchgang | 22.95 % | 50.19 % | 40.73 % | 79/721 | 2842.39 | 120.28 |
| Immer warnen | 89.69 % | 40.19 % | 40.73 % | 0/721 | 940.89 | 502.22 |
| Nie warnen | 0.00 % | — | 40.73 % | 721/721 | 3813.68 | 121.14 |
| Verweildauer und Richtung | 41.43 % | 43.05 % | 40.73 % | 51/721 | 2364.70 | 229.45 |

## grob, schleife

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 37.99 % | 47.15 % | 42.66 % | 0/759 | 2494.47 | 187.18 |
| Festes Erbe | 72.60 % | 39.39 % | 42.66 % | 0/759 | 1721.37 | 410.22 |
| Startwert | 57.44 % | 42.16 % | 42.66 % | 22/759 | 2029.15 | 313.42 |
| Ohne Erbe | 46.16 % | 43.05 % | 42.66 % | 53/759 | 2369.54 | 253.95 |
| Letzter Durchgang | 23.05 % | 54.70 % | 42.66 % | 88/759 | 2899.24 | 112.11 |
| Immer warnen | 90.08 % | 42.28 % | 42.66 % | 0/759 | 911.44 | 484.69 |
| Nie warnen | 0.00 % | — | 42.66 % | 759/759 | 3976.98 | 127.52 |
| Verweildauer und Richtung | 41.61 % | 44.68 % | 42.66 % | 50/759 | 2458.70 | 222.98 |

## je_signal, gesamt

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 42.17 % | 77.12 % | 71.07 % | 0/1654 | 3317.41 | 81.01 |
| Festes Erbe | 74.01 % | 69.13 % | 71.07 % | 0/1654 | 1863.04 | 191.83 |
| Startwert | 65.17 % | 70.29 % | 71.07 % | 1/1654 | 2284.06 | 162.75 |
| Ohne Erbe | 44.91 % | 71.38 % | 71.07 % | 62/1654 | 3383.62 | 118.33 |
| Letzter Durchgang | 21.79 % | 84.47 % | 71.07 % | 230/1654 | 4450.30 | 67.07 |
| Immer warnen | 100.00 % | 71.07 % | 71.07 % | 0/1654 | 242.94 | 242.94 |
| Nie warnen | 0.00 % | — | 71.07 % | 1654/1654 | 5967.74 | 277.89 |
| Verweildauer und Richtung | 40.24 % | 79.85 % | 71.07 % | 313/1654 | 3337.23 | 120.67 |

## je_signal, temperatur

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 21.17 % | 38.21 % | 24.18 % | 0/441 | 1670.78 | 125.59 |
| Festes Erbe | 39.57 % | 21.01 % | 24.18 % | 0/441 | 1823.49 | 300.13 |
| Startwert | 31.88 % | 24.88 % | 24.18 % | 14/441 | 1790.07 | 232.27 |
| Ohne Erbe | 12.62 % | 19.59 % | 24.18 % | 240/441 | 2181.77 | 137.75 |
| Letzter Durchgang | 7.44 % | 36.96 % | 24.18 % | 279/441 | 2102.67 | 91.92 |
| Immer warnen | 100.00 % | 24.18 % | 24.18 % | 0/441 | 727.99 | 727.99 |
| Nie warnen | 0.00 % | — | 24.18 % | 441/441 | 2321.74 | 74.09 |
| Verweildauer und Richtung | 4.90 % | 28.65 % | 24.18 % | 344/441 | 2220.55 | 91.35 |

## je_signal, speicher

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 15.06 % | 58.87 % | 40.73 % | 0/721 | 3041.70 | 58.00 |
| Festes Erbe | 36.47 % | 27.04 % | 40.73 % | 0/721 | 3139.26 | 249.14 |
| Startwert | 30.52 % | 30.80 % | 40.73 % | 24/721 | 3131.37 | 201.76 |
| Ohne Erbe | 21.46 % | 33.76 % | 40.73 % | 127/721 | 3268.51 | 154.44 |
| Letzter Durchgang | 8.43 % | 76.02 % | 40.73 % | 168/721 | 3232.80 | 47.14 |
| Immer warnen | 100.00 % | 40.73 % | 40.73 % | 0/721 | 554.92 | 554.92 |
| Nie warnen | 0.00 % | — | 40.73 % | 721/721 | 3813.68 | 121.14 |
| Verweildauer und Richtung | 22.94 % | 67.34 % | 40.73 % | 235/721 | 2437.43 | 109.64 |

## je_signal, schleife

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 14.99 % | 61.85 % | 42.66 % | 0/759 | 3165.89 | 53.33 |
| Festes Erbe | 36.70 % | 27.89 % | 42.66 % | 0/759 | 3269.71 | 246.69 |
| Startwert | 31.19 % | 31.54 % | 42.66 % | 18/759 | 3259.02 | 202.07 |
| Ohne Erbe | 22.88 % | 34.55 % | 42.66 % | 115/759 | 3379.70 | 158.94 |
| Letzter Durchgang | 8.89 % | 78.80 % | 42.66 % | 160/759 | 3341.50 | 44.46 |
| Immer warnen | 100.00 % | 42.66 % | 42.66 % | 0/759 | 534.51 | 534.51 |
| Nie warnen | 0.00 % | — | 42.66 % | 759/759 | 3976.98 | 127.52 |
| Verweildauer und Richtung | 23.64 % | 66.30 % | 42.66 % | 239/759 | 2590.24 | 114.43 |

## Aussagegrenzen

Die Mischung gewichtet Familien durch gleich viele gleich lange Spuren. Einzelne Familien
können anders ausfallen; kein globaler Gewinner wird aus dem Gesamtwert abgeleitet.
Dauer und Richtung sind im Kandidaten bedingt unabhängig. Das Ein-Takt-Dauerprior ist
eine zusätzliche Annahme. Fehlende Dauerabdeckung unterdrückt eine Warnung, beweist aber
keine Sicherheit. Erste linkszensierte Läufe werden nicht als vollständige Dauern gelernt.
Kein Beleg für Echtzeit, RAM, Energie oder Nutzen an echten 6-/24-Stunden-Aufnahmen.
