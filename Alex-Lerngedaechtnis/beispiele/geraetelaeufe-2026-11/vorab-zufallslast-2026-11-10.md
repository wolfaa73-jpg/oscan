# Vorab: Temperaturvorhersage bei zufälligen Lastdauern

Festgelegt am 10. November 2026 um 08:27, von Alex bestätigt („Ja, starten“), vor dem Aufspielen und vor dem Start. Ausgewertet wird mit `vorhersage.py <aufnahme>` (Modus zwei Hälften), Stand von jetzt.

## Frage

Sagt das kleine lineare Modell die Chiptemperatur auch dann besser voraus als die einfachen Maßstäbe, wenn die Last keinem festen Plan folgt?

## Lauf

- 8 Stunden, 28.800 Takte, Regel startwert, Blick 60, Grenzen ausdrücklich 380 390 65536 16384 20000 200000.
- Nur Last, kein Leck, keine Bremse, keine Erkundung, kein Sichern.
- `--last 240 240 20261110`: jede Arbeits- und Ruhephase dauert zufällig 60 bis 240 s.
- Vor dem Start: Speicher des Geräts sichern, MAC prüfen, `esp32s3-startwert` aufspielen, Demo 240/240.
- Nach dem Start die JSON Feld für Feld gegen diese Festlegung prüfen.

```bash
caffeinate -i ~/.platformio/penv/bin/python3 -B koerper.py aufnahme --port /dev/cu.usbmodem5C843185441 --regel startwert --intervall-ms 1000 --takte 28800 --blick 60 --grenzen 380 390 65536 16384 20000 200000 --last 240 240 20261110 messungen/koerper-zufallslast-8h-2026-11-10.csv
```

## Auswertung

- Anpassen an den Takten 1 bis 14.400, prüfen an 14.401 bis 28.800. Zwischen beiden bleiben 120 Takte ungewertet.
- Ziel: `temp_dc` in 30 und in 60 Takten. Mittlerer Betragsfehler in °C, dazu der Wurzelfehler.
- Verfahren, alle werden berichtet:
  - **bleibt:** die jetzige Temperatur.
  - **Mittel:** der Mittelwert der Anpass-Hälfte.
  - **ohne Lastgeschichte:** Konstante, Mittel der letzten 5 Takte, Steigung, Last jetzt.
  - **Körper:** dazu Lastanteil der letzten 60 und 120 Takte. Dieselben Eingänge wie am 10.11. morgens.
  - **Körper, lernt mit:** dieselben Eingänge, beginnt bei null, normalisiertes LMS mit Schrittweite 0,05, über den ganzen Lauf, gewertet nur in der Prüf-Hälfte.
  - **mit Takten seit dem Lastwechsel:** wie Körper, dazu 16 Fächer. Als Kontrolle: Bei Zufallsdauern darf das kaum etwas bringen.

## Erfolg

„Körper“ gilt als besser, wenn sein Betragsfehler in der Prüf-Hälfte bei 60 Takten höchstens 80 % des besseren der beiden Maßstäbe „bleibt“ und „Mittel“ beträgt. Sonst gilt die Frage als nicht bejaht.

## Erwartung

- „Körper“ landet bei 60 bis 75 % des besseren Maßstabs, also schlechter als die 49 % mit festem Plan.
- „ohne Lastgeschichte“ liegt über 85 %.
- Die Fächer seit dem Lastwechsel bringen weniger als 5 Prozentpunkte.
- „lernt mit“ ist schlechter als „Körper“, aber besser als beide Maßstäbe.

## Reizprüfung

- R1: Die Längen der Lastphasen in der Aufnahme passen zu `koerper.lastdauern(20261110, 240, 240, …)`, auf 2 Takte genau.
- R2: Die Temperatur überstreicht mindestens 3 ganze Grad.
