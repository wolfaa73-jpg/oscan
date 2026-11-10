# Auswertung: Temperaturvorhersage

10. November 2026. Festlegung: `vorab-vorhersage-2026-11-10.md` (08:21, SHA 6994b592…), unverändert. Tabellen: `vorhersage-tabellen-2026-11-10.md`, Skript `vorhersage.py` (nicht committet).

## Ergebnis nach Festlegung

Prüf-Aufnahme 7./8.11., mittlerer Betragsfehler in °C:

| Verfahren | H = 30 | H = 60 | Anteil von „bleibt“ bei H = 60 |
| --- | ---: | ---: | ---: |
| bleibt | 0,630 | 0,955 | 100 % |
| Mittel | 0,871 | 0,871 | 91 % |
| Körper, fest | 0,480 | 0,472 | 49 % |
| Körper, lernt mit | 0,544 | 0,615 | 64 % |
| Mit Rhythmus, fest | 0,462 | 0,466 | 49 % |

Das Erfolgskriterium (höchstens 80 % von „bleibt“ bei H = 60) ist erfüllt. Auf der Anpass-Aufnahme liegt „Körper, fest“ bei 0,475, also keine Überanpassung.

## Erwartungen

- „bleibt“ bei 0,6 bis 0,9: bei H = 30 ja, bei H = 60 knapp darüber.
- Gewinn vor allem nach Lastwechseln: **nicht** eingetroffen, der Gewinn ist im Rest größer.
- „lernt mit“ nahe an „fest“: **nicht** eingetroffen (64 gegen 49 %).
- „Mit Rhythmus“ deutlich besser: **nicht** eingetroffen (49 gegen 49 %).

## Schwäche der Festlegung (nach der Rechnung erkannt)

Die Eingänge „Lastanteil der letzten 60 und 120 Takte“ verraten bei festem 120/120-Plan, wo im Zyklus der Knoten steht. Darum bringt „Mit Rhythmus“ nichts mehr dazu: „Körper“ kennt den Plan schon. Nachträglich gerechnet, ohne Hypothesenstatus:

| Eingänge | H = 30 | H = 60 |
| --- | ---: | ---: |
| nur Temperatur und Steigung | 0,660 | 0,832 |
| dazu Last jetzt | 0,601 | 0,813 |
| dazu Lastgeschichte (= Körper, fest) | 0,480 | 0,472 |

Ohne Lastgeschichte bleibt bei H = 60 ein Fehler von 85 % von „bleibt“ und kaum weniger als beim Mittel. Der Gewinn stammt also überwiegend aus der Lastgeschichte, und die lässt sich in diesen Aufnahmen nicht vom Reizplan trennen.

## Sonst

- Der Fühler zählt ganze Grad. Rund 0,25 °C Betragsfehler sind damit ohnehin die Untergrenze.
- numpy meldet auf diesem Rechner Warnungen bei der Matrixmultiplikation. Gegenrechnung ohne sie: gleiche Zahlen, alle Werte endlich.

## Was eine saubere Prüfung braucht

Eine Aufnahme mit zufälligen Lastdauern. Dort hilft kein Plan, nur das Wissen, wie der Chip auf Last antwortet.
