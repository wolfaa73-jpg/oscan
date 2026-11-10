# Auswertung: Feinere Speicherstufen (explorativ)

9. November 2026, abends. Die Festlegung steht in `vorab-feinstufe-2026-11-09.md` (21:11, vor der ersten Rechnung). Alle Tabellen stehen in `feinstufe-tabellen-2026-11-09.md`, das Skript ist `feinstufe.py` (nicht committet). Der Lauf ist explorativ, denn die Leckböden waren vorher bekannt.

## Gegenprobe

N = 1 gleicht „Startwert h6/.6“ aus pruefung24h in allen Takten aller fünf Aufnahmen, bei 30 und bei 60 Takten Horizont. Die Zahlen unten stehen also auf demselben Lerner und derselben Zählung wie das Prüfprotokoll.

## Kernzahlen: 24-h-Wiederholung (7./8.11., repariertes Leck, 208 tief, 209 flach, 25 Wechsel)

| Verfahren | H | Warnanteil | Präzision | Phasen ohne Warnung | Wechsel vorgewarnt | flache mit Warnung | Warnung in OK | Vorlauf nach Wechsel | Kphase |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Feste Regel | 30 | 6,11 % | 48,0 % | 0 | 25/25 | 209/209 | 0 | 12 | 2.704 |
| Startwert h6/.6 | 30 | 5,17 % | 49,5 % | 24 | 1/25 | 33/209 | 1.800 | 7 | 2.465 |
| Fein N = 4 | 30 | 4,76 % | 54,4 % | 0 | 25/25 | 58/209 | 1.096 | 3 | 1.847 |
| Fein N = 8 | 30 | 4,34 % | 55,9 % | 0 | 25/25 | 60/209 | 862 | 3 | 1.629 |
| Fein N = 16 | 30 | 4,48 % | 55,3 % | 0 | 25/25 | 83/209 | 720 | 4 | 1.706 |
| Feste Regel | 60 | 6,11 % | 48,0 % | 0 | 25/25 | 209/209 | 0 | 12 | 2.704 |
| Startwert h6/.6 | 60 | 7,12 % | 36,5 % | 24 | 1/25 | 58/209 | 3.355 | 12 | 4.087 |
| Fein N = 4 | 60 | 7,63 % | 35,1 % | 0 | 25/25 | 84/209 | 3.117 | 3 | 4.209 |
| Fein N = 8 | 60 | 7,55 % | 35,5 % | 0 | 25/25 | 84/209 | 3.055 | 3 | 4.147 |
| Fein N = 16 | 60 | 7,74 % | 35,0 % | 0 | 25/25 | 109/209 | 2.940 | 4 | 4.283 |

Zum Maßstab: Immer warnen kostet 78.882 (H 30) und 72.612 (H 60), nie warnen 2.080.

## Die anderen Aufnahmen in Kürze (Fein N = 4 / 8 / 16)

- **6-h-Muster (5.11., 56 tief, 6 Wechsel):** kein Wechsel verpasst bei beiden Horizonten, h6/.6 verpasst 5. Kphase bei H 30: 586 / 558 / 568, feste Regel 624. Bei H 60: 1.234 / 1.224 / 1.253, feste Regel 624.
- **2-h-Zufall b (7.11., 17 tief, 10 Wechsel):** kein Wechsel verpasst, h6/.6 verpasst 3 (H 30) und 1 (H 60). Warnungen in 14 bis 17 von 18 flachen Durchgängen. Kphase bei H 30: 335 / 351 / 349, feste Regel 234.
- **24 h vom 6.11. (hängendes Leck: 128 tief, 81 hängen unter 32 KiB ohne VOLL):** 3 / 4 / 4 Phasen ohne Warnung bei H 30 und 2 / 2 / 3 bei H 60, die feste Regel verpasst keine. Kphase bei H 30: 1.252 / 1.145 / 1.170, feste Regel 4.081.
- **2-h-Zufall (7.11., kein Durchgang erreichte VOLL):** nur Fehlwarnungen. Bei H 30: 390 / 427 / 444, feste Regel 523.

## Erwartungen von vorher

- **N = 2 wie N = 1:** eingetroffen. 24 verpasst in der Wiederholung wie bei N = 1.
- **Ab N = 4 kein verpasster Wechsel in sauberen Aufnahmen:** eingetroffen, in allen drei bei beiden Horizonten.
- **Kaum Warnungen in flachen Durchgängen:** **nicht** eingetroffen. 58 bis 109 von 209 in der Wiederholung, 14 bis 17 von 18 im Zufallslauf.
- **3 bis 4 Takte Vorlauf nach Ruhe:** eingetroffen. N = 4 und 8 haben 3, N = 16 hat 4.
- **Bei hängendem Leck schrumpft der Vorteil:** eingetroffen, und zwar bis zu verpassten Phasen, 2 bis 4 von 128.

## Woher die Fehlwarnungen kommen (Befund nach der Rechnung)

1. **Warnungen in OK direkt nach jedem Ausfall:** Die Kontextregel lässt eine Zeile nur altern, wenn ihr Zustand selbst beobachtet wird. Während eines Durchgangs ruht die OK-Zeile. Bei der Freigabe gilt der Ausgang von vorhin deshalb noch als frisch, rund 1 zu 9 je Takt statt rund 1 zu 200. Bis das verblasst, warnt der Lerner in den ersten 10 bis 15 OK-Takten nach jedem Ausfall. Beim Speicher sind das alles Fehlwarnungen, denn der nächste Durchgang beginnt frühestens 99 Takte später. Das gilt schon für h6/.6 (1.800 Takte bei H 30, 3.355 bei H 60). Auch das Gerät mit seinem groben Zustand warnt so: 9.894 seiner 31.349 Warntakte liegen in OK, fast alle binnen 60 Takten nach einem Ausfallende. Dort folgt aber bei 44 % binnen einer Minute ein weiterer Ausfall, weil die Temperatur an der Grenze flackert.
2. **Warnungen in flachen Durchgängen:** Die Haltestufe des flachen Lecks erlebt beide Ausgänge, weiter nach unten (tief) oder zurück nach OK (flach). Ihr Gedächtnis mit Halbwertszeit 6 zählt auch das Verweilen. So spiegelt es fast nur die letzten ein bis zwei Durchgänge. War der letzte tief, warnt der Lerner im nächsten flachen schon in der obersten Stufe.

Beides kommt aus der Kontextregel, nicht aus den Stufen. Daniels Idee, Verweildauer und Richtung getrennt zu lernen (VERWEILDAUER-ERGEBNISSE.md), zielt genau auf diesen Mechanismus. Mit feinen Stufen ist sie noch nicht geprüft.

## Folgen für den Schiedsrichter

- Mit Alex' Rückfallregel bestünde „Fein“ ab N = 4 in den drei sauberen Aufnahmen: Es verpasst nichts, was die feste Regel erkennt. Im hängenden Leck vom 6.11. fiele es zurück, nach 2 bis 4 verpassten Phasen.
- Der heutige Lerner h6/.6 verpasst den ersten Wechsel nach 1,87 h (Takt 6724, zweiter Wechsel). Den ersten Wechsel in Durchgang 16 erkennt er noch. Im Zufallslauf b sind es 1,52 h.
- **Kostenverhältnis:** Mit r = 10 ist nie warnen (2.080) in der Wiederholung billiger als die feste Regel (2.704). Soll die feste Regel dort vor „nie warnen“ liegen, muss r über 13 liegen. Für das einzufrierende Verhältnis ist das ein Anhaltspunkt, keine Empfehlung.

## Nächste Schritte, nicht entschieden

- Verweildauer und Richtung getrennt, auf den feinen Stufen, vorab festgelegt.
- Die Warnung in OK nach Ausfällen gezielt prüfen, auch für das Gerät.
- Alles Konfirmatorische nur mit vorab festgelegtem Gerätelauf.
