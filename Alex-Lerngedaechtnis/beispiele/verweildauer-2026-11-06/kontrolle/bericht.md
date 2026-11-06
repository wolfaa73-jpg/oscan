# Verweildauer und Richtung: synthetischer Vergleich

Taktwertung ist maßgeblich. Alle Ergebnisse beschreiben künstliche Spuren, keine Geräteprüfung.
Satz: kontrolle. Freeze-Commit: 4df7cf9101d9587b39c9a0072ebccbfb7798c76c.

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
| Feste Regel | 41.77 % | 76.12 % | 70.99 % | 0/3298 | 3385.61 | 84.03 |
| Festes Erbe | 80.86 % | 68.95 % | 70.99 % | 0/3298 | 1495.07 | 211.47 |
| Startwert | 63.01 % | 70.82 % | 70.99 % | 148/3298 | 2375.97 | 167.31 |
| Ohne Erbe | 50.02 % | 72.11 % | 70.99 % | 317/3298 | 3059.32 | 144.16 |
| Letzter Durchgang | 25.44 % | 81.14 % | 70.99 % | 487/3298 | 4281.78 | 81.34 |
| Immer warnen | 100.00 % | 70.99 % | 70.99 % | 0/3298 | 244.37 | 244.37 |
| Nie warnen | 0.00 % | — | 70.99 % | 3298/3298 | 5980.43 | 277.05 |
| Verweildauer und Richtung | 43.92 % | 75.62 % | 70.99 % | 220/3298 | 3272.66 | 108.68 |

## grob, temperatur

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 36.59 % | 28.11 % | 23.38 % | 0/858 | 1512.92 | 253.01 |
| Festes Erbe | 70.81 % | 22.25 % | 23.38 % | 0/858 | 1262.68 | 529.56 |
| Startwert | 55.18 % | 23.19 % | 23.38 % | 42/858 | 1426.05 | 411.27 |
| Ohne Erbe | 43.81 % | 23.19 % | 23.38 % | 99/858 | 1595.43 | 331.99 |
| Letzter Durchgang | 22.28 % | 29.09 % | 23.38 % | 167/858 | 1777.40 | 166.01 |
| Immer warnen | 87.58 % | 23.30 % | 23.38 % | 0/858 | 931.88 | 646.09 |
| Nie warnen | 0.00 % | — | 23.38 % | 858/858 | 2248.99 | 72.08 |
| Verweildauer und Richtung | 38.46 % | 24.50 % | 23.38 % | 56/858 | 1621.93 | 284.06 |

## grob, speicher

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 37.67 % | 44.83 % | 41.68 % | 0/1485 | 2510.09 | 194.14 |
| Festes Erbe | 72.92 % | 38.59 % | 41.68 % | 0/1485 | 1683.05 | 418.26 |
| Startwert | 56.82 % | 40.15 % | 41.68 % | 67/1485 | 2080.39 | 323.34 |
| Ohne Erbe | 45.11 % | 41.32 % | 41.68 % | 136/1485 | 2399.75 | 258.70 |
| Letzter Durchgang | 22.95 % | 50.36 % | 41.68 % | 200/1485 | 2920.67 | 123.20 |
| Immer warnen | 90.18 % | 41.39 % | 41.68 % | 0/1485 | 900.48 | 493.72 |
| Nie warnen | 0.00 % | — | 41.68 % | 1485/1485 | 3893.65 | 124.75 |
| Verweildauer und Richtung | 39.61 % | 44.36 % | 41.68 % | 94/1485 | 2458.31 | 213.77 |

## grob, schleife

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 37.62 % | 44.18 % | 41.08 % | 0/1470 | 2484.93 | 196.45 |
| Festes Erbe | 72.81 % | 38.35 % | 41.08 % | 0/1470 | 1650.59 | 419.91 |
| Startwert | 56.74 % | 40.40 % | 41.08 % | 56/1470 | 2015.22 | 321.09 |
| Ohne Erbe | 45.04 % | 42.30 % | 41.08 % | 118/1470 | 2303.90 | 253.07 |
| Letzter Durchgang | 22.91 % | 50.96 % | 41.08 % | 181/1470 | 2855.86 | 120.31 |
| Immer warnen | 90.05 % | 40.79 % | 41.08 % | 0/1470 | 905.63 | 498.79 |
| Nie warnen | 0.00 % | — | 41.08 % | 1470/1470 | 3843.08 | 123.49 |
| Verweildauer und Richtung | 39.55 % | 44.99 % | 41.08 % | 99/1470 | 2381.96 | 211.84 |

## je_signal, gesamt

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 41.77 % | 76.12 % | 70.99 % | 0/3298 | 3385.61 | 84.03 |
| Festes Erbe | 73.73 % | 68.48 % | 70.99 % | 0/3298 | 1922.49 | 195.76 |
| Startwert | 64.37 % | 69.54 % | 70.99 % | 6/3298 | 2374.87 | 165.70 |
| Ohne Erbe | 44.16 % | 70.39 % | 70.99 % | 119/3298 | 3472.39 | 120.15 |
| Letzter Durchgang | 21.69 % | 83.38 % | 70.99 % | 472/3298 | 4487.27 | 70.02 |
| Immer warnen | 100.00 % | 70.99 % | 70.99 % | 0/3298 | 244.37 | 244.37 |
| Nie warnen | 0.00 % | — | 70.99 % | 3298/3298 | 5980.43 | 277.05 |
| Verweildauer und Richtung | 38.79 % | 80.76 % | 70.99 % | 664/3298 | 3404.35 | 118.65 |

## je_signal, temperatur

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 20.82 % | 35.76 % | 23.38 % | 0/858 | 1661.34 | 128.66 |
| Festes Erbe | 38.91 % | 19.79 % | 23.38 % | 0/858 | 1808.59 | 300.19 |
| Startwert | 30.68 % | 23.62 % | 23.38 % | 55/858 | 1777.49 | 230.02 |
| Ohne Erbe | 11.92 % | 21.67 % | 23.38 % | 441/858 | 2090.33 | 126.87 |
| Letzter Durchgang | 7.17 % | 37.82 % | 23.38 % | 533/858 | 2031.03 | 87.65 |
| Immer warnen | 100.00 % | 23.38 % | 23.38 % | 0/858 | 737.00 | 737.00 |
| Nie warnen | 0.00 % | — | 23.38 % | 858/858 | 2248.99 | 72.08 |
| Verweildauer und Richtung | 5.71 % | 35.02 % | 23.38 % | 626/858 | 2092.32 | 88.29 |

## je_signal, speicher

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 15.26 % | 60.39 % | 41.68 % | 0/1485 | 3089.54 | 56.44 |
| Festes Erbe | 36.80 % | 27.67 % | 41.68 % | 0/1485 | 3190.93 | 248.64 |
| Startwert | 31.08 % | 31.20 % | 41.68 % | 44/1485 | 3187.79 | 203.42 |
| Ohne Erbe | 22.09 % | 34.57 % | 41.68 % | 249/1485 | 3315.46 | 155.93 |
| Letzter Durchgang | 8.82 % | 77.22 % | 41.68 % | 327/1485 | 3276.49 | 46.23 |
| Immer warnen | 100.00 % | 41.68 % | 41.68 % | 0/1485 | 544.74 | 544.74 |
| Nie warnen | 0.00 % | — | 41.68 % | 1485/1485 | 3893.65 | 124.75 |
| Verweildauer und Richtung | 22.62 % | 69.51 % | 41.68 % | 485/1485 | 2489.56 | 105.15 |

## je_signal, schleife

| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 15.10 % | 58.65 % | 41.08 % | 0/1470 | 3073.18 | 58.39 |
| Festes Erbe | 36.63 % | 26.78 % | 41.08 % | 0/1470 | 3176.47 | 250.90 |
| Startwert | 30.72 % | 30.34 % | 41.08 % | 45/1470 | 3171.34 | 203.93 |
| Ohne Erbe | 21.49 % | 34.14 % | 41.08 % | 244/1470 | 3289.07 | 152.90 |
| Letzter Durchgang | 8.36 % | 78.00 % | 41.08 % | 331/1470 | 3250.48 | 45.00 |
| Immer warnen | 100.00 % | 41.08 % | 41.08 % | 0/1470 | 551.19 | 551.19 |
| Nie warnen | 0.00 % | — | 41.08 % | 1470/1470 | 3843.08 | 123.49 |
| Verweildauer und Richtung | 22.09 % | 70.47 % | 41.08 % | 498/1470 | 2447.62 | 102.86 |

## Aussagegrenzen

Die Mischung gewichtet Familien durch gleich viele gleich lange Spuren. Einzelne Familien
können anders ausfallen; kein globaler Gewinner wird aus dem Gesamtwert abgeleitet.
Dauer und Richtung sind im Kandidaten bedingt unabhängig. Das Ein-Takt-Dauerprior ist
eine zusätzliche Annahme. Fehlende Dauerabdeckung unterdrückt eine Warnung, beweist aber
keine Sicherheit. Erste linkszensierte Läufe werden nicht als vollständige Dauern gelernt.
Kein Beleg für Echtzeit, RAM, Energie oder Nutzen an echten 6-/24-Stunden-Aufnahmen.
