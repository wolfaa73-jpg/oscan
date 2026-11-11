# Probe am Rechner: Kälteeinbruch als Vorhersagefehler, 10. November 2026

Gerechnet vor dem Kälteversuch am Gerät, mit `kaelteprobe.py`. Explorativ. Frage: Wie schnell und wie sicher
fällt ein Kälteeinbruch auf, wenn die Grenze aus dem eigenen Vorhersagefehler der ersten Laufhälfte kommt?

- Formen des Einbruchs (geschätzt, nicht gemessen): „schnell“ = 10 s Kühlen mit Zeitkonstante 5 s, Erholung
  30 s; „träge“ = 20 s mit 15 s, Erholung 60 s. Tiefen 1, 2 und 3 °C. Je Lauf 11 Einbrüche in der zweiten Hälfte.
- Verfahren: „Körper“ oder „bleibt“ (Mittel der letzten fünf), h Takte voraus, Fehler über n Takte gemittelt,
  Grenze = q-Wert des Betrags in der ersten Hälfte. Ein Alarm zählt neu nach 60 ruhigen Takten.
- Am echten Lauf wird der Einbruch auf die ganzen Grad aufaddiert, mit einem festen Zufallsversatz je Einbruch.
- Die Variante „Körper h10 n20“ wurde vorher an den Saaten 1–12 ausgesucht. Die Fehlalarmraten der Varianten
  sind nicht gleichgezogen.

Ergebnis in Kürze: 2 bis 3 °C fallen sicher auf, aber erst nach etwa 8 bis 16 Takten. Binnen zwei Takten
schafft es nur der Sprungmelder („bleibt h1 n1“) bei 3 °C schnell. 1 °C ist Glückssache. „Ruhe nach“ misst den
Erkenner, nicht den Körper. Der Versuch am Gerät zeigte danach: Pusten bringt etwa 4 °C, die Erholung dauert
Minuten statt 30 bis 60 s (`auswertung-kaelte-2026-11-10.md`).

## Simulator, Saaten 13–24

| Verfahren, Form, Tiefe | Grenze °C | Fehlalarme/h | ≤ 2 Takte | ≤ 10 | ≤ 30 | ≤ 120 | Verzug Median | Ruhe nach (Median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Körper h10 n20 q0.999, schnell, 1 °C | 0.71 | 1.43 | 2 % | 11 % | 50 % | 51 % | 13 | 15 |
| Körper h10 n20 q0.999, schnell, 2 °C | 0.71 | 1.43 | 2 % | 74 % | 100 % | 100 % | 9 | 27 |
| Körper h10 n20 q0.999, schnell, 3 °C | 0.71 | 1.43 | 2 % | 100 % | 100 % | 100 % | 7 | 29 |
| Körper h10 n20 q0.999, träge, 1 °C | 0.71 | 1.43 | 2 % | 3 % | 47 % | 48 % | 19 | 20 |
| Körper h10 n20 q0.999, träge, 2 °C | 0.71 | 1.43 | 2 % | 20 % | 100 % | 100 % | 13 | 35 |
| Körper h10 n20 q0.999, träge, 3 °C | 0.71 | 1.43 | 2 % | 56 % | 100 % | 100 % | 10 | 38 |
| Körper h1 n1 q0.999, schnell, 1 °C | 1.06 | 4.68 | 4 % | 43 % | 46 % | 54 % | 6 | 6 |
| Körper h1 n1 q0.999, schnell, 2 °C | 1.06 | 4.68 | 42 % | 99 % | 99 % | 100 % | 3 | 8 |
| Körper h1 n1 q0.999, schnell, 3 °C | 1.06 | 4.68 | 93 % | 100 % | 100 % | 100 % | 1 | 10 |
| Körper h1 n1 q0.999, träge, 1 °C | 1.06 | 4.68 | 2 % | 20 % | 36 % | 44 % | 14 | 6 |
| Körper h1 n1 q0.999, träge, 2 °C | 1.06 | 4.68 | 4 % | 68 % | 91 % | 93 % | 8 | 21 |
| Körper h1 n1 q0.999, träge, 3 °C | 1.06 | 4.68 | 19 % | 98 % | 100 % | 100 % | 5 | 27 |
| bleibt h1 n1 q0.999, schnell, 1 °C | 1.00 | 1.24 | 2 % | 18 % | 18 % | 21 % | 4 | 0 |
| bleibt h1 n1 q0.999, schnell, 2 °C | 1.00 | 1.24 | 31 % | 82 % | 82 % | 82 % | 3 | 5 |
| bleibt h1 n1 q0.999, schnell, 3 °C | 1.00 | 1.24 | 82 % | 100 % | 100 % | 100 % | 2 | 7 |
| bleibt h1 n1 q0.999, träge, 1 °C | 1.00 | 1.24 | 1 % | 1 % | 2 % | 7 % | 59 | 0 |
| bleibt h1 n1 q0.999, träge, 2 °C | 1.00 | 1.24 | 2 % | 19 % | 25 % | 28 % | 6 | 0 |
| bleibt h1 n1 q0.999, träge, 3 °C | 1.00 | 1.24 | 11 % | 60 % | 66 % | 66 % | 5 | 6 |
| bleibt h1 n10 q0.999, schnell, 1 °C | 0.33 | 1.81 | 2 % | 35 % | 35 % | 38 % | 7 | 0 |
| bleibt h1 n10 q0.999, schnell, 2 °C | 0.33 | 1.81 | 12 % | 97 % | 98 % | 98 % | 4 | 13 |
| bleibt h1 n10 q0.999, schnell, 3 °C | 0.33 | 1.81 | 47 % | 100 % | 100 % | 100 % | 3 | 15 |
| bleibt h1 n10 q0.999, träge, 1 °C | 0.33 | 1.81 | 1 % | 10 % | 12 % | 16 % | 9 | 0 |
| bleibt h1 n10 q0.999, träge, 2 °C | 0.33 | 1.81 | 2 % | 59 % | 78 % | 79 % | 8 | 16 |
| bleibt h1 n10 q0.999, träge, 3 °C | 0.33 | 1.81 | 5 % | 95 % | 99 % | 99 % | 6 | 21 |

## Echter 8-h-Lauf, Einbruch aufaddiert, 12 Lagen

| Verfahren, Form, Tiefe | Grenze °C | Fehlalarme/h | ≤ 2 Takte | ≤ 10 | ≤ 30 | ≤ 120 | Verzug Median | Ruhe nach (Median) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Körper h10 n20 q0.999, schnell, 1 °C | 0.88 | 0.50 | 1 % | 2 % | 21 % | 25 % | 16 | 0 |
| Körper h10 n20 q0.999, schnell, 2 °C | 0.88 | 0.50 | 0 % | 35 % | 95 % | 95 % | 11 | 27 |
| Körper h10 n20 q0.999, schnell, 3 °C | 0.88 | 0.50 | 0 % | 90 % | 100 % | 100 % | 8 | 31 |
| Körper h10 n20 q0.999, träge, 1 °C | 0.88 | 0.50 | 1 % | 2 % | 22 % | 28 % | 20 | 0 |
| Körper h10 n20 q0.999, träge, 2 °C | 0.88 | 0.50 | 1 % | 5 % | 95 % | 96 % | 16 | 37 |
| Körper h10 n20 q0.999, träge, 3 °C | 0.88 | 0.50 | 0 % | 21 % | 100 % | 100 % | 13 | 43 |
| Körper h1 n1 q0.999, schnell, 1 °C | 1.13 | 2.52 | 17 % | 47 % | 57 % | 68 % | 5 | 24 |
| Körper h1 n1 q0.999, schnell, 2 °C | 1.13 | 2.52 | 35 % | 98 % | 98 % | 99 % | 3 | 43 |
| Körper h1 n1 q0.999, schnell, 3 °C | 1.13 | 2.52 | 80 % | 100 % | 100 % | 100 % | 2 | 46 |
| Körper h1 n1 q0.999, träge, 1 °C | 1.13 | 2.52 | 10 % | 34 % | 54 % | 71 % | 12 | 44 |
| Körper h1 n1 q0.999, träge, 2 °C | 1.13 | 2.52 | 17 % | 62 % | 92 % | 94 % | 7 | 73 |
| Körper h1 n1 q0.999, träge, 3 °C | 1.13 | 2.52 | 23 % | 93 % | 100 % | 100 % | 5 | 98 |
| bleibt h1 n1 q0.999, schnell, 1 °C | 1.20 | 0.76 | 11 % | 30 % | 39 % | 49 % | 5 | 1 |
| bleibt h1 n1 q0.999, schnell, 2 °C | 1.20 | 0.76 | 32 % | 81 % | 86 % | 89 % | 3 | 16 |
| bleibt h1 n1 q0.999, schnell, 3 °C | 1.20 | 0.76 | 77 % | 100 % | 100 % | 100 % | 2 | 28 |
| bleibt h1 n1 q0.999, träge, 1 °C | 1.20 | 0.76 | 6 % | 24 % | 36 % | 49 % | 11 | 4 |
| bleibt h1 n1 q0.999, träge, 2 °C | 1.20 | 0.76 | 11 % | 40 % | 60 % | 73 % | 10 | 18 |
| bleibt h1 n1 q0.999, träge, 3 °C | 1.20 | 0.76 | 16 % | 54 % | 73 % | 85 % | 5 | 57 |
| bleibt h1 n10 q0.999, schnell, 1 °C | 0.54 | 0.50 | 0 % | 10 % | 13 % | 20 % | 10 | 0 |
| bleibt h1 n10 q0.999, schnell, 2 °C | 0.54 | 0.50 | 2 % | 75 % | 78 % | 79 % | 6 | 11 |
| bleibt h1 n10 q0.999, schnell, 3 °C | 0.54 | 0.50 | 5 % | 100 % | 100 % | 100 % | 5 | 13 |
| bleibt h1 n10 q0.999, träge, 1 °C | 0.54 | 0.50 | 0 % | 5 % | 11 % | 19 % | 19 | 0 |
| bleibt h1 n10 q0.999, träge, 2 °C | 0.54 | 0.50 | 0 % | 20 % | 33 % | 44 % | 12 | 0 |
| bleibt h1 n10 q0.999, träge, 3 °C | 0.54 | 0.50 | 0 % | 66 % | 86 % | 89 % | 8 | 15 |
