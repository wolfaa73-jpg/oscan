# Warnschwellen und Erb-Halbwertszeit: Kontrollbericht

Die folgenden Einstellungen wurden ausschließlich auf Entwicklung gewählt und vor der
Kontrolle eingefroren. Dieser Bericht wählt keine Konfiguration anhand der Kontrollwerte.

Entwicklung: 1000 Spuren; unabhängige Kontrolle: 2000 Spuren.
Je Spur 960 Instrumenttakte, davon die letzten 30 nur als bekannte Zukunft.
Alle Warnkosten und Warnanteile zählen **sämtliche eigenen nichtkritischen Takte, auch OK**.
Trefferquote = richtige Warntakte / Warntakte; Grundrate = Zieltakte / nichtkritische Takte.
Kritische Phasen haben ein vollständiges Vorfenster; angrenzende kritische Takte bilden eine Phase.

`takt`: r × verpasste Zieltakte + falsche Warntakte. `phase`: r × unangekündigte Phasen + falsche Warntakte.
r bezeichnet jeweils den Preis des genannten Verlusts in Einheiten eines falschen Warntakts.
Die Modelle sind nicht austauschbar. Kosten sind je 1.000 ausgewertete Instrumenttakte normiert,
nicht je 1.000 nichtkritische Takte. Signalweise Kosten sind keine addierbaren Kosten einer gemeinsamen Geräteaktion.

## Unsicherheit

[intervalle.csv](intervalle.csv) enthält die 72 vorgeplanten Kostendifferenzen zur jeweiligen
Defaultkonfiguration für r=1,10,100. Negative Werte bedeuten geringere gemessene Kosten.
Je Vergleich 500 gepaarte Bootstrap-Ziehungen ganzer Spuren, getrennt innerhalb der vier Familien;
die ursprüngliche Familiengröße bleibt erhalten. 2,5-/97,5-%-Quantile werden linear interpoliert.
Das sind punktweise 95-%-Intervalle, kein gemeinsamer Signifikanztest über alle Vergleiche.
Die Unsicherheit bezieht sich auf diesen synthetischen Generator; sie erfasst keine unbekannten realen Fehlerursachen.

## Vorab festgelegte Kontrollvergleiche

### Temperatur · takt · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 284,577 | 19,87 % | 36,99 % | 24,45 % | 1065 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 261,001 | 10,21 % | 36,70 % | 24,45 % | 7715 / 13965 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 321,582 | 16,95 % | 23,38 % | 24,45 % | 6131 / 13965 |
| Startwert: gemeinsames Raster | 1 | 0,95 | 243,904 | 3,38 % | 36,16 % | 24,45 % | 11067 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 454,548 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 387,150 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 283,240 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 234,909 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 252,832 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -143,246
je 1.000 Takte, punktweises Bootstrap-Intervall [-145,205; -141,624].

### Temperatur · takt · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 971,880 | 91,46 % | 23,34 % | 24,45 % | 0 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 1145,075 | 85,30 % | 22,45 % | 24,45 % | 0 / 13965 |
| Startwert: Halbwertszeit gewählt | 8 | 0,6 | 1821,674 | 33,44 % | 24,02 % | 24,45 % | 144 / 13965 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 1008,053 | 90,20 % | 23,16 % | 24,45 % | 0 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 1858,964 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 1831,190 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 1709,387 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 2349,091 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 2124,697 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -823,138
je 1.000 Takte, punktweises Bootstrap-Intervall [-841,925; -802,948].

### Temperatur · takt · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 3657,703 | 91,46 % | 23,34 % | 24,45 % | 0 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 5732,123 | 85,30 % | 22,45 % | 24,45 % | 0 / 13965 |
| Startwert: Halbwertszeit gewählt | 24 | 0,6 | 15937,508 | 37,56 % | 21,72 % | 24,45 % | 0 / 13965 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 4088,375 | 90,20 % | 23,16 % | 24,45 % | 0 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 15903,125 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 16271,594 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 15970,855 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 23490,914 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 20843,342 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -12183,218
je 1.000 Takte, punktweises Bootstrap-Intervall [-12348,351; -12004,370].

### Temperatur · phase · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 120,846 | 19,87 % | 36,99 % | 24,45 % | 1065 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 66,234 | 10,21 % | 36,70 % | 24,45 % | 7715 / 13965 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 128,020 | 16,95 % | 23,38 % | 24,45 % | 6131 / 13965 |
| Startwert: gemeinsames Raster | 1 | 0,95 | 26,701 | 3,38 % | 36,16 % | 24,45 % | 11067 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 298,502 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 227,127 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 124,780 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 7,508 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 49,592 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -200,426
je 1.000 Takte, punktweises Bootstrap-Intervall [-201,505; -199,480].

### Temperatur · phase · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 125,999 | 19,87 % | 36,99 % | 24,45 % | 1065 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 103,565 | 10,21 % | 36,70 % | 24,45 % | 7715 / 13965 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 157,686 | 16,95 % | 23,38 % | 24,45 % | 6131 / 13965 |
| Startwert: gemeinsames Raster | 1 | 0,95 | 80,251 | 3,38 % | 36,16 % | 24,45 % | 11067 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 298,502 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 230,959 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 124,780 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 75,081 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 92,299 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -150,708
je 1.000 Takte, punktweises Bootstrap-Intervall [-152,022; -149,591].

### Temperatur · phase · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,9 | 146,954 | 23,02 % | 34,47 % | 24,45 % | 38 / 13965 |
| Startwert: Schwelle gewählt | 6 | 0,65 | 266,835 | 28,84 % | 26,15 % | 24,45 % | 1158 / 13965 |
| Startwert: Halbwertszeit gewählt | 8 | 0,6 | 251,771 | 33,44 % | 24,02 % | 24,45 % | 144 / 13965 |
| Startwert: gemeinsames Raster | 24 | 0,85 | 163,710 | 24,37 % | 32,42 % | 24,45 % | 102 / 13965 |
| Festes Erbe, Default | fest | 0,6 | 298,502 | 39,29 % | 20,90 % | 24,45 % | 0 / 13965 |
| Startwert, Default | 6 | 0,6 | 269,282 | 31,35 % | 24,72 % | 24,45 % | 792 / 13965 |
| Feste Regel | – | – | 124,780 | 20,95 % | 37,99 % | 24,45 % | 0 / 13965 |
| Immer warnen | – | – | 725,672 | 100,00 % | 24,45 % | 24,45 % | 0 / 13965 |
| Nie warnen | – | – | 750,806 | 0,00 % | – | 24,45 % | 13965 / 13965 |
| Letzter Durchgang | – | – | 519,363 | 7,47 % | 37,51 % | 24,45 % | 8826 / 13965 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -105,572
je 1.000 Takte, punktweises Bootstrap-Intervall [-107,689; -103,265].

### Speicher · takt · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 369,188 | 14,99 % | 57,85 % | 41,87 % | 802 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 358,349 | 9,99 % | 67,59 % | 41,87 % | 5836 / 23322 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 461,918 | 24,33 % | 34,44 % | 41,87 % | 3302 / 23322 |
| Startwert: gemeinsames Raster | 7 | 0,95 | 358,251 | 10,40 % | 66,95 % | 41,87 % | 5394 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 545,242 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 500,867 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 361,697 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 391,185 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 345,995 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -142,616
je 1.000 Takte, punktweises Bootstrap-Intervall [-143,344; -141,865].

### Speicher · takt · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 895,366 | 92,27 % | 40,90 % | 41,87 % | 0 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 1045,718 | 87,77 % | 40,87 % | 41,87 % | 0 / 23322 |
| Startwert: Halbwertszeit gewählt | 9 | 0,6 | 3196,752 | 33,06 % | 30,13 % | 41,87 % | 30 / 23322 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 926,401 | 91,33 % | 40,90 % | 41,87 % | 0 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 3211,957 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 3208,948 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 3112,688 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 3911,849 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 3297,066 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -2282,547
je 1.000 Takte, punktweises Bootstrap-Intervall [-2305,247; -2261,401].

### Speicher · takt · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 4368,011 | 92,27 % | 40,90 % | 41,87 % | 0 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 6092,976 | 87,77 % | 40,87 % | 41,87 % | 0 / 23322 |
| Startwert: Halbwertszeit gewählt | 24 | 0,6 | 29928,652 | 35,54 % | 28,39 % | 41,87 % | 0 / 23322 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 4724,788 | 91,33 % | 40,90 % | 41,87 % | 0 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 29879,102 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 30289,754 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 30622,591 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 39118,495 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 32807,775 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -25564,967
je 1.000 Takte, punktweises Bootstrap-Intervall [-25768,624; -25377,139].

### Speicher · phase · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 59,446 | 14,99 % | 57,85 % | 41,87 % | 802 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 33,397 | 9,99 % | 67,59 % | 41,87 % | 5836 / 23322 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 150,799 | 24,33 % | 34,44 % | 41,87 % | 3302 / 23322 |
| Startwert: gemeinsames Raster | 1 | 0,95 | 21,187 | 6,58 % | 73,06 % | 41,87 % | 8591 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 248,941 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 200,292 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 56,032 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 12,539 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 20,842 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -179,105
je 1.000 Takte, punktweises Bootstrap-Intervall [-179,637; -178,490].

### Speicher · phase · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 63,326 | 14,99 % | 57,85 % | 41,87 % | 802 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 61,636 | 9,99 % | 67,59 % | 41,87 % | 5836 / 23322 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 166,776 | 24,33 % | 34,44 % | 41,87 % | 3302 / 23322 |
| Startwert: gemeinsames Raster | 15 | 0,95 | 59,413 | 12,27 % | 63,26 % | 41,87 % | 3218 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 248,941 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 203,195 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 56,032 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 125,387 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 45,539 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -143,782
je 1.000 Takte, punktweises Bootstrap-Intervall [-144,488; -143,067].

### Speicher · phase · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,9 | 95,960 | 19,18 % | 47,60 % | 41,87 % | 38 / 23322 |
| Startwert: Schwelle gewählt | 6 | 0,75 | 214,803 | 22,97 % | 37,78 % | 41,87 % | 1512 / 23322 |
| Startwert: Halbwertszeit gewählt | 9 | 0,6 | 217,440 | 33,06 % | 30,13 % | 41,87 % | 30 / 23322 |
| Startwert: gemeinsames Raster | 24 | 0,9 | 114,139 | 18,10 % | 48,94 % | 41,87 % | 517 / 23322 |
| Festes Erbe, Default | fest | 0,6 | 248,941 | 36,80 % | 27,60 % | 41,87 % | 0 / 23322 |
| Startwert, Default | 6 | 0,6 | 232,227 | 31,07 % | 31,11 % | 41,87 % | 600 / 23322 |
| Feste Regel | – | – | 56,032 | 15,15 % | 60,42 % | 41,87 % | 0 / 23322 |
| Immer warnen | – | – | 543,118 | 100,00 % | 41,87 % | 41,87 % | 0 / 23322 |
| Nie warnen | – | – | 1253,871 | 0,00 % | – | 41,87 % | 23322 / 23322 |
| Letzter Durchgang | – | – | 292,506 | 8,71 % | 77,76 % | 41,87 % | 5104 / 23322 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -118,089
je 1.000 Takte, punktweises Bootstrap-Intervall [-120,468; -116,054].

### Schleife · takt · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 368,756 | 15,09 % | 58,13 % | 41,93 % | 802 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 358,241 | 10,07 % | 67,76 % | 41,93 % | 5849 / 23342 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 462,173 | 24,47 % | 34,58 % | 41,93 % | 3261 / 23342 |
| Startwert: gemeinsames Raster | 7 | 0,95 | 358,134 | 10,50 % | 67,10 % | 41,93 % | 5402 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 545,218 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 501,049 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 361,350 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 391,663 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 345,240 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -142,915
je 1.000 Takte, punktweises Bootstrap-Intervall [-143,664; -142,185].

### Schleife · takt · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 892,181 | 92,27 % | 41,00 % | 41,93 % | 0 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 1041,011 | 87,82 % | 40,96 % | 41,93 % | 0 / 23342 |
| Startwert: Halbwertszeit gewählt | 9 | 0,6 | 3196,020 | 33,17 % | 30,23 % | 41,93 % | 30 / 23342 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 922,776 | 91,34 % | 40,99 % | 41,93 % | 0 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 3212,029 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 3207,373 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 3110,676 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 3916,629 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 3291,912 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -2284,597
je 1.000 Takte, punktweises Bootstrap-Intervall [-2307,307; -2261,308].

### Schleife · takt · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,05 | 4345,472 | 92,27 % | 41,00 % | 41,93 % | 0 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,05 | 6051,688 | 87,82 % | 40,96 % | 41,93 % | 0 / 23342 |
| Startwert: Halbwertszeit gewählt | 24 | 0,6 | 29929,559 | 35,62 % | 28,48 % | 41,93 % | 0 / 23342 |
| Startwert: gemeinsames Raster | 24 | 0,05 | 4696,873 | 91,34 % | 40,99 % | 41,93 % | 0 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 29880,142 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 30270,615 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 30603,934 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 39166,290 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 32758,638 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -25573,742
je 1.000 Takte, punktweises Bootstrap-Intervall [-25775,852; -25368,244].

### Schleife · phase · r=1

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 59,432 | 15,09 % | 58,13 % | 41,93 % | 802 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 33,484 | 10,07 % | 67,76 % | 41,93 % | 5849 / 23342 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 151,290 | 24,47 % | 34,58 % | 41,93 % | 3261 / 23342 |
| Startwert: gemeinsames Raster | 1 | 0,95 | 21,075 | 6,58 % | 73,26 % | 41,93 % | 8645 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 248,905 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 200,639 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 55,869 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 12,549 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 20,569 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -179,564
je 1.000 Takte, punktweises Bootstrap-Intervall [-180,108; -179,024].

### Schleife · phase · r=10

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,95 | 63,312 | 15,09 % | 58,13 % | 41,93 % | 802 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,95 | 61,785 | 10,07 % | 67,76 % | 41,93 % | 5849 / 23342 |
| Startwert: Halbwertszeit gewählt | 1 | 0,6 | 167,069 | 24,47 % | 34,58 % | 41,93 % | 3261 / 23342 |
| Startwert: gemeinsames Raster | 17 | 0,95 | 59,313 | 12,65 % | 62,81 % | 41,93 % | 2862 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 248,905 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 203,271 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 55,869 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 125,495 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 45,208 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -143,958
je 1.000 Takte, punktweises Bootstrap-Intervall [-144,694; -143,238].

### Schleife · phase · r=100

| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|---:|---:|---:|
| Erbe: Schwelle gewählt | fest | 0,9 | 96,039 | 19,25 % | 47,82 % | 41,93 % | 41 / 23342 |
| Startwert: Schwelle gewählt | 6 | 0,75 | 212,045 | 23,09 % | 37,96 % | 41,93 % | 1455 / 23342 |
| Startwert: Halbwertszeit gewählt | 8 | 0,6 | 217,372 | 32,68 % | 30,52 % | 41,93 % | 98 / 23342 |
| Startwert: gemeinsames Raster | 24 | 0,9 | 113,101 | 18,19 % | 49,17 % | 41,93 % | 497 / 23342 |
| Festes Erbe, Default | fest | 0,6 | 248,905 | 36,86 % | 27,70 % | 41,93 % | 0 / 23342 |
| Startwert, Default | 6 | 0,6 | 229,594 | 31,19 % | 31,22 % | 41,93 % | 544 / 23342 |
| Feste Regel | – | – | 55,869 | 15,21 % | 60,67 % | 41,93 % | 0 / 23342 |
| Immer warnen | – | – | 542,340 | 100,00 % | 41,93 % | 41,93 % | 0 / 23342 |
| Nie warnen | – | – | 1254,946 | 0,00 % | – | 41,93 % | 23342 / 23342 |
| Letzter Durchgang | – | – | 291,595 | 8,79 % | 78,28 % | 41,93 % | 5092 / 23342 |

Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz -116,493
je 1.000 Takte, punktweises Bootstrap-Intervall [-118,731; -114,396].

## Entwicklungsprofil und Grenzen

[halbwertsprofil.csv](halbwertsprofil.csv) zeigt das gesamte Halbwertszeitraster 1–24 bei Schwelle 0,6,
je Familie und gepoolt, einschließlich der Baselines. Dieses Profil ist Entwicklungsdiagnostik,
keine weitere unabhängige Kontrollbestätigung. Ein Optimum hängt vom Signal, der Musterfamilie und
vom gewählten Kostenbegriff ab; aus einer einzelnen besten Rasterzelle folgt kein allgemeiner Gewinner.
Die vollständig eingefrorenen Entscheidungen für r=1…100 stehen im Entwicklungsordner in `auswahl.json`;
[schwellenwechsel.csv](schwellenwechsel.csv) fasst aufeinanderfolgende Preisverhältnisse mit gleicher Wahl zusammen:
je Signal, Kostenmodell und Suchraum stehen dort r_von, r_bis, Konfiguration, Erb-Halbwertszeit und Schwelle.
Diese Bereiche stellen ausschließlich die bereits eingefrorene Auswahl dar; es wird nichts neu optimiert.
Die zugehörigen Kontrollkosten stehen in `auswahl-pruefung.csv`. Preisgrenzen sind diskrete Entwicklungswechsel,
keine universellen ökonomischen Grenzen. Kleinste Kostenunterschiede sind keine belastbare Geräteempfehlung.

Alle künstlichen Ausfälle besitzen ein hohes Vorzeichen innerhalb des Horizonts. Das begünstigt die feste Regel.
Es wurden keine Geräteaufnahmen zum Einstellen oder Prüfen verwendet. Physikalische Erwärmung, unbekannte Ausfälle
ohne Vorzeichen und reale Energie-/RAM-/Aktionskosten sind nicht modelliert. Aufgaben 4–7 und die unabhängige
Prüfung an echten Aufnahmen bleiben offen. Nach Betrachtung dieser Kontrolle ist sie für nachträgliche Anpassungen
kein unberührter Kontrollsatz mehr.

## Nachprüfung

Vor Berichtserstellung wurden sämtliche Ergebnisprüfsummen, Splitdefinitionen und die unveränderte Auswahl geprüft.
Optimum und Tiebreak jeder eingefrorenen Wahl wurden ausschließlich aus dem Entwicklungsraster bestätigt.
Alle Kontrollsummen wurden aus den Einzelspuren neu addiert; jede erwartete Kombination aus Familie, Signal,
Konfiguration und Seed kommt genau einmal vor. Taktzahl, nichtkritische Takte, Zieltakte und Phasen müssen
für alle Konfigurationen desselben Seeds übereinstimmen. Die Bootstrap-Paarung verwendet dieselbe Spur beider Verfahren.
Der Berichtsmanifest enthält nur neutrale Dateinamen, Hashes und Verfahrensparameter.
