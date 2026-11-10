# Vorab: Sagt der Knoten seine eigene Temperatur besser voraus als „bleibt, wie es ist“?

Festgelegt am 10. November 2026, bevor irgendeine Vorhersage gerechnet wird.

**Einschränkung.** Beide Aufnahmen sind bekannt, auch ihre Stufenzahlen (1.674 und 2.438 Wärmephasen). Eine Temperaturvorhersage wurde auf keiner von beiden je gerechnet. Der Lauf ist damit halb blind und ersetzt keinen neuen Gerätelauf.

## Frage

Kann ein kleines lineares Modell die Chiptemperatur in 30 und in 60 Takten besser vorhersagen als der einfachste Maßstab, wenn es die eigene Last als Eingang bekommt?

## Daten

- **Anpassen:** `koerper-startwert-24h-2026-11-06.csv`.
- **Prüfen:** `koerper-startwert-24h-2026-11-07.csv`. Kein Wert daraus fließt in Gewichte oder Einstellungen.
- Ziel ist `temp_dc` in H Takten, H = 30 und 60. Last ist Bit 1 von `reiz`.
- Gewertet werden alle Takte ab 121 bis Ende minus H.

## Verfahren, alle werden berichtet

- **Maßstab „bleibt“:** Vorhersage ist die jetzige Temperatur.
- **Maßstab „Mittel“:** der Mittelwert der Anpass-Aufnahme, fest.
- **Körper, fest:** kleinste Quadrate auf der Anpass-Aufnahme, danach eingefroren. Eingänge: Konstante, Mittel der letzten 5 Takte, Steigung (Mittel der letzten 5 minus Mittel der 5 davor), Last jetzt, Lastanteil der letzten 60 Takte, Lastanteil der letzten 120 Takte.
- **Körper, lernt mit:** dieselben Eingänge, beginnt bei null und lernt auf der Prüf-Aufnahme laufend (normalisiertes LMS, Schrittweite 0,05, Temperatur als Abstand zu 37,0 °C). Jede Vorhersage zählt, bevor ihr Ziel bekannt ist. Die Schrittweite wird nicht nachgestellt.
- **Mit Rhythmus, fest:** wie „Körper, fest“, dazu die Takte seit dem letzten Lastwechsel (höchstens 240) in 8 Fächern zu je 30, getrennt nach Last an und aus. Dieses Modell kann den 120/120-Reizplan auswendig lernen. Es steht daneben, um Körperwissen von Planwissen zu trennen, und zählt nicht als Erfolg.

## Zählung

- Mittlerer Betragsfehler in °C, dazu die Wurzel des mittleren Quadratfehlers.
- Getrennt nach „bis 60 Takte nach einem Lastwechsel“ und „Rest“.
- Dieselben Zahlen auch auf der Anpass-Aufnahme, als Kontrolle auf Überanpassung.

## Erfolg, vorher festgelegt

„Körper, fest“ gilt als besser, wenn sein mittlerer Betragsfehler auf der Prüf-Aufnahme bei H = 60 höchstens 80 % des Fehlers von „bleibt“ beträgt. Sonst gilt die Frage als nicht bejaht.

## Erwartung, vorher notiert

- „bleibt“ liegt bei 0,6 bis 0,9 °C.
- „Körper, fest“ gewinnt vor allem nach Lastwechseln, im Rest kaum.
- „Körper, lernt mit“ ist nach wenigen Minuten nahe an „Körper, fest“.
- „Mit Rhythmus“ ist deutlich besser als „Körper“, weil der Plan fest ist.
- Unsicher: Da die Prüf-Aufnahme wärmer war, kann die feste Konstante danebenliegen.
