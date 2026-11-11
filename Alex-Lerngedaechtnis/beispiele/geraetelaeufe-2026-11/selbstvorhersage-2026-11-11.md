# Selbstvorhersage: Referenz für das Gerät, 11. November 2026

Stufe 1 bis 3 des Plans „das Gerechnete aufs Gerät“. Explorativ am Rechner, nichts davon lief bisher auf dem
Gerät. Die Referenz ist `selbstvorhersage.py`, die Tests stehen in `test_labor.py` (SelbstvorhersageTests).

## Stufe 1: ein Lernverfahren, das mitlaufend funktioniert

Das mitlernende Verfahren vom 10.11. (normalisiertes LMS, Schrittweite 0,05) lag bei 138 % des besseren
Maßstabs. Verglichen wurden kleinere Schrittweiten, skalierte Eingänge und rekursive kleinste Quadrate (RLS)
mit Vergessen 1 bis 0,999. Betragsfehler 60 Takte voraus, zweite Laufhälfte, Anteil des besseren Maßstabs:

| Verfahren | 8-h-Lauf 10.11. | Lastlauf 5.11. | Simulator (8 Läufe) |
| --- | ---: | ---: | ---: |
| bleibt | 100 % | 118 % | 100 % |
| Mittel bisher | 106 % | 100 % | 102 % |
| fest an der ersten Hälfte angepasst | 89 % | 49 % | 79 % |
| LMS 0,05 (10.11.) | 138 % | 87 % | 126 % |
| LMS 0,002, skaliert | 87 % | 61 % | 79 % |
| RLS, Vergessen 0,9995 | 87 % | 39 % | 77 % |

- RLS mit Vergessen 0,999 entgleiste in einem von acht Simulatorläufen. Ursache: Ohne Lastwechsel wächst die
  Kovarianz. Nach 24 h Ruhe erreichte ihre Spur 1,7 Millionen (Start 600).
- Mit einem Deckel auf die Spur (600) blieben alle Varianten stabil, auch nach 24 h Ruhe mit anschließender
  Last (78 %). Einfache Genauigkeit liefert dieselben Anteile wie doppelte.
- 10 Takte voraus schlägt beim Betragsfehler kein Verfahren „bleibt“ (103 bis 104 %), beim Wurzelfehler
  deutlich (76 bis 77 %). Grund sind die ganzen Grad: „bleibt“ liegt oft exakt richtig. Für den kurzen Horizont
  ist der Wurzelfehler das passende Maß; das gehört vor einem Gerätelauf festgelegt.

## Stufe 2: die Referenz

Konstanten und ihre Herkunft:

| Konstante | Wert | Herkunft |
| --- | --- | --- |
| Horizonte | 10 und 60 Takte | 10 aus der Kälteprobe, 60 wie am 10.11. |
| Vergessen | 0,9995 je Takt | Stufe 1; zwischen 0,9995 und 0,9999 kaum Unterschied |
| Deckel | Spur 600 | gleich dem Startwert; nur im Simulator bei langer Ruhe geprüft |
| Mittelung des Fehlers | 20 Takte | Kälteprobe |
| Normalmaß | verblassendes Mittel des Quadrats, Halbwertszeit 3.600 Takte | gesetzt, nicht verglichen |
| Anlauf | Normalmaß ab dem 600., Überraschung ab dem 1.800. Fehler | gesetzt, nicht verglichen |
| Faktor | 4,0 | an den Aufnahmen unten ausgesucht, siehe Tabelle |

Wahl des Faktors (Strecken mit Überraschung je Stunde ohne Störung, Beginn des Alarms beim Pusten):

| Faktor | 8-h-Lauf | Lastlauf 5.11. | Simulator (4 Läufe) | Alarm beim Pusten (Beginn Takt 146) |
| ---: | ---: | ---: | ---: | ---: |
| 3,0 | 5,07 | 2,18 | 2,63 | Takt 158 |
| 3,5 | 0,80 | 0,36 | 0,60 | Takt 160 |
| 4,0 | 0,00 | 0,18 | 0,07 | Takt 161 |
| 4,5 | 0,00 | 0,00 | 0,03 | Takt 163 |

Solange er überrascht ist, lernt das Normalmaß nicht weiter, die Gewichte schon.

## Ergebnisse der Referenz

Ausgabe von `selbstvorhersage.py`, beim Kälteversuch mit dem 8-h-Lauf als Vorlauf (als hätte er den Stand vom
Morgen behalten).

## koerper-zufallslast-8h-2026-11-10.csv

28800 Takte, Temperatur 35 bis 40 °C, gewertet ab Takt 1801.

| Horizont | Verfahren | Betragsfehler °C | Wurzelfehler °C | Anteil „bleibt“ (Betrag / Wurzel) |
| ---: | --- | ---: | ---: | ---: |
| 10 | bleibt | 0.310 | 0.566 | 100 % / 100 % |
| 10 | Mittel bisher | 0.760 | 0.904 | 245 % / 160 % |
| 10 | Selbstvorhersage | 0.320 | 0.432 | 103 % / 76 % |
| 60 | bleibt | 0.705 | 0.978 | 100 % / 100 % |
| 60 | Mittel bisher | 0.763 | 0.907 | 108 % / 93 % |
| 60 | Selbstvorhersage | 0.608 | 0.740 | 86 % / 76 % |

Überrascht in 0 von 27000 Takten, 0 Strecken, das sind 0.00 je Stunde.
Strecken (Beginn, Länge): keine.
## koerper-last-2026-11-05.csv

21610 Takte, Temperatur 35 bis 40 °C, gewertet ab Takt 1801.

| Horizont | Verfahren | Betragsfehler °C | Wurzelfehler °C | Anteil „bleibt“ (Betrag / Wurzel) |
| ---: | --- | ---: | ---: | ---: |
| 10 | bleibt | 0.372 | 0.629 | 100 % / 100 % |
| 10 | Mittel bisher | 0.844 | 0.959 | 227 % / 153 % |
| 10 | Selbstvorhersage | 0.344 | 0.454 | 92 % / 72 % |
| 60 | bleibt | 1.030 | 1.290 | 100 % / 100 % |
| 60 | Mittel bisher | 0.846 | 0.963 | 82 % / 75 % |
| 60 | Selbstvorhersage | 0.377 | 0.487 | 37 % / 38 % |

Überrascht in 1 von 19810 Takten, 1 Strecken, das sind 0.18 je Stunde.
Strecken (Beginn, Länge): 15559 (1).
## koerper-kaelte-2026-11-10.csv nach Vorlauf

900 Takte, Temperatur 28 bis 39 °C, gewertet ab Takt 1.

| Horizont | Verfahren | Betragsfehler °C | Wurzelfehler °C | Anteil „bleibt“ (Betrag / Wurzel) |
| ---: | --- | ---: | ---: | ---: |
| 10 | bleibt | 0.557 | 0.860 | 100 % / 100 % |
| 10 | Mittel bisher | 2.280 | 3.105 | 409 % / 361 % |
| 10 | Selbstvorhersage | 0.732 | 1.038 | 131 % / 121 % |
| 60 | bleibt | 2.131 | 2.770 | 100 % / 100 % |
| 60 | Mittel bisher | 2.693 | 3.596 | 126 % / 130 % |
| 60 | Selbstvorhersage | 2.620 | 3.726 | 123 % / 135 % |

Überrascht in 196 von 900 Takten, 6 Strecken, das sind 24.00 je Stunde.
Strecken (Beginn, Länge): 161 (34), 229 (49), 285 (29), 322 (14), 503 (36), 553 (34).

Zum Kälteversuch: Das Pusten (Beginn etwa Takt 146) fällt bei Takt 161 auf, nach 15 Takten. Beide
Kühlpack-Einbrüche geben je zwei Strecken, eine beim Abkühlen und eine bei der Umkehr. Dazwischen und danach
ist er ruhig, anders als bei der Auswertung mit festen Gewichten vom 10.11., in der der Alarm 630 Takte stand:
Die mitlernenden Gewichte folgen der Erholung. Die Vorhersage selbst ist während der Störung schlechter als
„bleibt“.

## Stufe 3: die Firmware (übersetzt, noch nicht aufgespielt)

- `esp32/Lernknoten/Vorhersage.h` rechnet dasselbe wie `selbstvorhersage.py`, in derselben Reihenfolge und in
  einfacher Genauigkeit. Der Sketch bindet sie ein: `VORHERSAGE 1` beginnt bei null und meldet die Konstanten,
  `VORHERSAGE 0` beendet. Je Körpertakt kommt vor der Körperzeile eine Zeile
  `VORHERSAGE,takt,v10_mg,v60_mg,fehler_mg,mittel_mg,grenze_mg,ueberrascht` (Tausendstelgrad). Eine nicht lesbare
  Temperatur zählt wie die letzte lesbare. Der Stand überlebt `STOP`, nicht `NEUER_LAUF` und keinen Neustart.
- `koerper.py aufnahme --vorhersage` schaltet sie ein, schreibt die Zeilen nach `<name>.vorhersage.csv` und die
  gemeldeten Konstanten in die JSON. `koerper.py pruefen` rechnet jede Zeile mit `selbstvorhersage.py` nach;
  erlaubt sind 2 mg Abweichung, die Überraschung muss stimmen. Ohne `--vorhersage` bleibt alles wie bisher.
- Am Rechner gebaut gibt die Firmware-Datei über 12.000 Takte mit Einbruch und fehlenden Messwerten Zeile für
  Zeile dasselbe aus wie die Referenz (Test in `test_labor.py`).
- Für den S3 übersetzt (`esp32s3-startwert`, 27 KB RAM, 315 KB Flash). `-ffp-contract=off` in `platformio.ini`
  verhindert verschmolzene Multiplikation und Addition; im Maschinencode steht keine. Ob das Gerät dieselben
  Zahlen liefert, zeigt erst ein Lauf.

## Grenzen

- Faktor und Vergessen sind an denselben Aufnahmen ausgesucht, an denen sie hier berichtet werden.
- Der Kälteversuch ist ein einzelner Lauf; der Vorlauf vom Morgen ist eine Annahme, am Gerät hätte er nach dem
  Neustart nichts gewusst.
- Ob er sich an eine dauerhaft veränderte Lage gewöhnt oder überrascht bleibt, ist nicht untersucht.
- Die Firmware wird nicht bitgleich rechnen (andere Reihenfolge, verschmolzene Multiplikation). Der Abgleich
  am Gerät braucht eine Toleranz.
