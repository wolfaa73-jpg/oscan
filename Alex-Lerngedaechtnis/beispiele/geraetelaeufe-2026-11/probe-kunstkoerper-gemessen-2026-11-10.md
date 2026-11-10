# Künstlicher Körper mit gemessener Umgebung (10.11.2026, nach der Auswertung)

Explorativ. Anlass: Die erste Probe (`probe-kunstkoerper-2026-11-10.md`) traf die Fehler der Modelle, machte
aber den Maßstab „bleibt“ zu schlecht und sagte deshalb 75 % statt der echten 89 % voraus. Drift und Rauschen
waren dort angenommen.

## Was geändert ist

`umgebung.py` gleicht die Umgebung an die **erste Hälfte** des Zufallslast-Laufs an (Autokovarianz des Rests
bei 11 Abständen, Wechselrate der Anzeige, Hub). Ergebnis, jetzt Vorgabe in `kunstkoerper.GEMESSEN`:

| Größe | Wert |
| --- | ---: |
| Zeitkonstante, Hub, Ruhetemperatur | 30 s, 2,0 °C, 36,95 °C |
| schneller Anteil der Umgebung | Streuung 0,33 °C, Zeit 37 s |
| langsamer Anteil | Streuung 0,47 °C, Zeit 85 min |
| Messrauschen vor dem Runden | 0,15 °C |

Ein einzelner Anteil reicht nicht (Verlust 0,82 gegen 0,03 mit zweien). Der schnelle Anteil hat fast die
Zeitkonstante des Körpers: Es sieht aus wie Wärme, die nicht von unserer Last kommt und durch denselben Körper
läuft.

## Lesart der Gegenprobe

- **Lastlauf vom 5.11. (unabhängig, anderer Tag, fester Takt):** 11 von 12 echten Werten liegen im Band der
  24 Simulationen, der zwölfte („bleibt“ bei H 60) um 0,003 °C daneben. „Körper“ bei H 60: echt 47 %,
  simuliert im Median 55 %.
- **Zufallslast-Lauf, ganze Auswertung:** Alle Modelle liegen im Band. Die Maßstäbe „bleibt“ und „Mittel“
  sind in echt weiter besser als simuliert (0,666 gegen 0,761 bis 0,845 °C).
- **Die Erfolgsgrenze:** 17 von 24 Simulationen bestehen die 80 %, mit der alten Annahme waren es 22 von 24.
  Die echten 89 % liegen jetzt im simulierten Bereich, aber am Rand.
- **Warum „bleibt“ noch abweicht:** Der echte Körper war über die 8 Stunden nicht gleich. Viertelweise:

  | Viertel | Hub °C | Rest-Varianz | „bleibt“ bei 60 s °C | Wechsel je 1.000 | Mittel °C |
  | ---: | ---: | ---: | ---: | ---: | ---: |
  | 1 | 2,11 | 0,34 | 0,82 | 194 | 37,77 |
  | 2 | 1,91 | 0,21 | 0,73 | 162 | 38,15 |
  | 3 | 1,66 | 0,19 | 0,64 | 143 | 38,38 |
  | 4 | 1,77 | 0,21 | 0,69 | 168 | 38,09 |

  Mit steigender Temperatur schrumpften Hub und Unruhe. Geschätzt wurde an den unruhigeren Vierteln 1 und 2,
  geprüft wird an 3 und 4. Der Simulator kennt nur eine gleichbleibende Umgebung.

## Was das nicht zeigt

Die Umgebung stammt aus einem halben Lauf an einem Tag. Warum der Hub mit der Temperatur schrumpft, ist offen
und nicht eingebaut. Der Lüfter ist weiter nicht simuliert.

# Tabellen

## 8-h-Zufallslast vom 10.11. (erste Hälfte diente der Schätzung)

28800 Takte, echte Lastreihe, 24 Saaten. Betragsfehler in °C; „im Band“ = echter Wert zwischen kleinstem und größtem simulierten.

| H | Verfahren | echt | Simulation Mittel (kleinster–größter) | im Band | echt: Anteil | Simulation: Anteil Median |
| ---: | --- | ---: | ---: | :---: | ---: | ---: |
| 30 | bleibt | 0.434 | 0.523 (0.494–0.549) | nein | 100 % | 100 % |
| 30 | Mittel | 0.713 | 0.886 (0.778–1.216) | nein | 164 % | 163 % |
| 30 | ohne Lastgeschichte | 0.440 | 0.526 (0.455–0.766) | nein | 101 % | 97 % |
| 30 | Körper | 0.437 | 0.475 (0.432–0.581) | ja | 100 % | 89 % |
| 30 | Körper, lernt mit | 0.566 | 0.597 (0.518–0.677) | ja | 130 % | 112 % |
| 30 | mit Takten seit dem Lastwechsel | 0.415 | 0.463 (0.415–0.563) | ja | 96 % | 87 % |
| 60 | bleibt | 0.666 | 0.816 (0.761–0.845) | nein | 100 % | 100 % |
| 60 | Mittel | 0.714 | 0.886 (0.778–1.217) | nein | 107 % | 105 % |
| 60 | ohne Lastgeschichte | 0.641 | 0.765 (0.602–1.122) | ja | 96 % | 92 % |
| 60 | Körper | 0.593 | 0.644 (0.582–0.756) | ja | 89 % | 78 % |
| 60 | Körper, lernt mit | 0.920 | 1.008 (0.859–1.158) | ja | 138 % | 123 % |
| 60 | mit Takten seit dem Lastwechsel | 0.553 | 0.613 (0.550–0.726) | ja | 83 % | 75 % |

„Körper“ bei H 60 höchstens 80 %: 17 von 24 Simulationen, echt 89.1 %.
Zum Vergleich die alte Annahme (Zufallsweg 1 °C je Tag, Rauschen 0,3 °C): 22 von 24, Median 75 %.

## Lastlauf vom 5.11., fester Takt 120/120, 6 h (nicht für die Schätzung benutzt)

21610 Takte, echte Lastreihe, 24 Saaten. Betragsfehler in °C; „im Band“ = echter Wert zwischen kleinstem und größtem simulierten.

| H | Verfahren | echt | Simulation Mittel (kleinster–größter) | im Band | echt: Anteil | Simulation: Anteil Median |
| ---: | --- | ---: | ---: | :---: | ---: | ---: |
| 30 | bleibt | 0.596 | 0.579 (0.553–0.602) | ja | 100 % | 100 % |
| 30 | Mittel | 0.888 | 0.790 (0.685–0.897) | ja | 149 % | 135 % |
| 30 | ohne Lastgeschichte | 0.579 | 0.533 (0.455–0.685) | ja | 97 % | 91 % |
| 30 | Körper | 0.464 | 0.421 (0.393–0.493) | ja | 78 % | 72 % |
| 30 | Körper, lernt mit | 0.598 | 0.530 (0.467–0.613) | ja | 100 % | 90 % |
| 30 | mit Takten seit dem Lastwechsel | 0.439 | 0.411 (0.381–0.477) | ja | 74 % | 70 % |
| 60 | bleibt | 0.989 | 0.942 (0.891–0.986) | nein | 111 % | 121 % |
| 60 | Mittel | 0.889 | 0.790 (0.686–0.897) | ja | 100 % | 100 % |
| 60 | ohne Lastgeschichte | 0.817 | 0.738 (0.613–1.036) | ja | 92 % | 93 % |
| 60 | Körper | 0.414 | 0.440 (0.381–0.556) | ja | 47 % | 55 % |
| 60 | Körper, lernt mit | 0.729 | 0.679 (0.587–0.890) | ja | 82 % | 84 % |
| 60 | mit Takten seit dem Lastwechsel | 0.423 | 0.437 (0.371–0.559) | ja | 48 % | 55 % |

„Körper“ bei H 60 höchstens 80 %: 24 von 24 Simulationen, echt 46.6 %.
