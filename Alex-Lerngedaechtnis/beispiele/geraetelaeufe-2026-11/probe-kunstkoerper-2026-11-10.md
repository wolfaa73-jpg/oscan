# Probe der Auswertung am künstlichen Körper (10.11.2026)

Explorativ, gerechnet nach dem Einfrieren von vorab-zufallslast-2026-11-10.md und während der 8-h-Lauf lief.
Die Festlegung bleibt unverändert, in die laufende Aufnahme wurde nicht gesehen. Die Probe hätte vor das
Einfrieren gehört.

Körper: `kunstkoerper.py`, eine Zeitkonstante, Last heizt um einen festen Hub, Umgebung als Zufallsweg,
Rauschen, Ausgabe in ganzen Grad. Lastplan wie im Lauf (240 240 20261110, 183 Wechsel in 8 h). Ausgewertet mit
`vorhersage.py`, unverändert. Zeitkonstante und Hub grob aus den beiden 24-h-Läufen: der Fit ist zwischen
15 und 90 s flach (Restfehler 0,58 bis 0,66 °C), bester Wert bei 30 s. Drift und Rauschen sind angenommen.

## Lesart

1. Auch ein vollkommen einfacher Körper kommt bei H = 60 nur auf 66 bis 79 % des Maßstabs. Die Erfolgsgrenze
   von 80 % liegt beim schnellen Körper an der Decke: mit 1 °C Drift je Tag bestehen 7 von 24 Rauschsaaten.
   Beim mittleren und trägen Körper bestehen 20 bis 24 von 24.
2. Die Streuung kommt fast ganz aus der Drift zwischen Anpass- und Prüfhälfte. Ohne Drift liegen alle
   24 Saaten innerhalb eines Punkts.
3. „Ohne Lastgeschichte“ gegen „Körper“ misst kein Körperwissen. Beim trägen Körper ist der Abstand 0 Punkte,
   beim schnellen 7 bis 22. Die Lastgeschichte hilft dort, wo die gerundete Temperatur den Zustand schlecht
   wiedergibt, und gegen die Drift.
4. Die Takte seit dem Lastwechsel bringen auch bei Zufallslast 2 bis 6 Punkte. Gleichverteilte Dauern von
   einem Viertel bis zum vollen Wert sind nicht gedächtnislos: je länger eine Phase läuft, desto eher endet sie.
5. „Körper, lernt mit“ liegt bei H = 60 fast immer über 100 %, auch am bekannten Körper. Das liegt an
   Schrittweite und verzögertem Ziel, nicht am Körper.
6. Die Rundung auf ganze Grad kostet bei H = 60 etwa 0,04 bis 0,06 °C.
7. R2 (mindestens 3 ganze Grad Spanne) war in jeder Probe erfüllt.

# Tabellen 1: je 8 Rauschsaaten, Drift 1 °C je Tag, Rauschen 0,3 °C

## Zufallslast, ganze Grad


### H = 30

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.537 (100–100 %) | 0.786 (135–162 %) | 0.558 (85–158 %) | 0.508 (84–130 %) | 0.615 (106–129 %) | 0.483 (82–124 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.517 (100–100 %) | 0.803 (145–174 %) | 0.473 (79–127 %) | 0.445 (80–110 %) | 0.529 (95–111 %) | 0.430 (77–111 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.513 (100–100 %) | 0.866 (155–193 %) | 0.408 (75–92 %) | 0.421 (75–104 %) | 0.466 (87–93 %) | 0.411 (75–99 %) |

### H = 60

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.789 (100–105 %) | 0.786 (100–111 %) | 0.752 (84–137 %) | 0.650 (79–104 %) | 0.991 (120–144 %) | 0.611 (73–100 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.790 (100–103 %) | 0.803 (100–116 %) | 0.691 (76–129 %) | 0.599 (73–92 %) | 0.950 (101–141 %) | 0.567 (68–88 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.797 (100–100 %) | 0.866 (100–125 %) | 0.575 (67–95 %) | 0.574 (67–95 %) | 0.827 (95–109 %) | 0.527 (63–78 %) |

## Zufallslast, ohne Rundung


### H = 30

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.537 (100–100 %) | 0.780 (140–168 %) | 0.487 (76–146 %) | 0.437 (74–113 %) | 0.576 (100–117 %) | 0.412 (70–109 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.528 (100–100 %) | 0.795 (145–176 %) | 0.410 (67–120 %) | 0.377 (66–97 %) | 0.480 (80–100 %) | 0.362 (63–96 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.511 (100–100 %) | 0.835 (156–195 %) | 0.324 (59–79 %) | 0.332 (60–88 %) | 0.405 (72–84 %) | 0.315 (58–77 %) |

### H = 60

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.789 (100–105 %) | 0.780 (100–114 %) | 0.709 (84–132 %) | 0.607 (76–97 %) | 0.992 (113–149 %) | 0.557 (69–90 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.796 (100–104 %) | 0.795 (100–116 %) | 0.644 (74–121 %) | 0.556 (68–85 %) | 0.947 (98–135 %) | 0.510 (63–79 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.793 (100–100 %) | 0.835 (100–125 %) | 0.524 (61–89 %) | 0.517 (60–89 %) | 0.843 (92–113 %) | 0.455 (55–69 %) |

## fester Takt 240/240, ganze Grad


### H = 30

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.464 (100–100 %) | 0.813 (161–190 %) | 0.502 (90–165 %) | 0.478 (89–151 %) | 0.535 (106–127 %) | 0.393 (67–131 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.445 (100–100 %) | 0.869 (175–211 %) | 0.416 (82–137 %) | 0.406 (80–135 %) | 0.459 (95–112 %) | 0.352 (61–131 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.490 (100–100 %) | 1.003 (189–223 %) | 0.386 (76–91 %) | 0.422 (74–134 %) | 0.448 (84–96 %) | 0.396 (72–122 %) |

### H = 60

Betragsfehler in °C, Mittel über 8 Rauschsaaten; in Klammern Anteil am besseren Maßstab, kleinster bis größter Wert.

| Körper | Spanne °C | bleibt | Mittel | ohne Lastgeschichte | Körper | Körper, lernt mit | mit Takten seit dem Lastwechsel |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell (τ 15 s, Hub 1.7 °C) | 4–5 | 0.633 (100–100 %) | 0.813 (122–136 %) | 0.678 (83–155 %) | 0.601 (87–127 %) | 0.940 (133–169 %) | 0.395 (48–97 %) |
| mittel (τ 30 s, Hub 2.0 °C) | 4–5 | 0.644 (100–100 %) | 0.869 (125–142 %) | 0.612 (83–143 %) | 0.556 (79–119 %) | 0.908 (117–158 %) | 0.359 (42–95 %) |
| träge (τ 90 s, Hub 3.5 °C) | 5–6 | 0.774 (100–100 %) | 1.002 (123–141 %) | 0.521 (58–84 %) | 0.616 (53–163 %) | 0.875 (92–128 %) | 0.411 (46–86 %) |

# Tabellen 2: Erfolgsgrenze, je 24 Rauschsaaten

H = 60, ganze Grad, Zufallslast, 24 Rauschsaaten. Anteil am besseren Maßstab: Median (kleinster–größter); bestanden = Körper ≤ 80 %.

| Körper | Drift °C/Tag | Rauschen °C | Körper | bestanden | ohne Lastgeschichte | Abstand Punkte | seit Wechsel bringt | lernt mit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| schnell | 1 | 0.3 | 82 % (78–104) | 7/24 | 94 % (84–137) | 12 | 4 | 123 % (0/24 unter 100) |
| schnell | 0 | 0.3 | 79 % (78–79) | 24/24 | 86 % (86–86) | 7 | 4 | 133 % (0/24 unter 100) |
| schnell | 2 | 0.3 | 82 % (79–133) | 7/24 | 106 % (87–226) | 22 | 5 | 118 % (0/24 unter 100) |
| schnell | 1 | 0.15 | 84 % (78–114) | 3/24 | 96 % (86–152) | 15 | 6 | 145 % (0/24 unter 100) |
| mittel | 1 | 0.3 | 75 % (72–92) | 23/24 | 83 % (76–129) | 8 | 4 | 122 % (0/24 unter 100) |
| mittel | 0 | 0.3 | 73 % (72–73) | 24/24 | 78 % (77–79) | 5 | 3 | 142 % (0/24 unter 100) |
| mittel | 2 | 0.3 | 75 % (72–104) | 20/24 | 95 % (78–211) | 19 | 4 | 113 % (1/24 unter 100) |
| mittel | 1 | 0.15 | 75 % (69–93) | 21/24 | 83 % (77–144) | 9 | 4 | 138 % (0/24 unter 100) |
| träge | 1 | 0.3 | 69 % (66–95) | 23/24 | 70 % (66–95) | 0 | 5 | 106 % (5/24 unter 100) |
| träge | 0 | 0.3 | 66 % (65–67) | 24/24 | 66 % (65–67) | 0 | 2 | 102 % (3/24 unter 100) |
| träge | 2 | 0.3 | 71 % (67–124) | 20/24 | 79 % (70–147) | 5 | 6 | 104 % (7/24 unter 100) |
| träge | 1 | 0.15 | 68 % (64–101) | 23/24 | 69 % (64–98) | -0 | 6 | 107 % (4/24 unter 100) |
