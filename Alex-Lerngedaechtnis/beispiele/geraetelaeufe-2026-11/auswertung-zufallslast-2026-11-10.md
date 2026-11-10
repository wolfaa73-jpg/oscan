# Auswertung: Temperaturvorhersage bei zufälligen Lastdauern

Gerechnet am 10. November 2026 nach dem Ende des Laufs, nach `vorab-zufallslast-2026-11-10.md` (SHA fc9bcf06…,
unverändert) mit `vorhersage.py` (SHA 401e9566…, unverändert seit dem Einfrieren). Die Tabellen stehen in
`vorhersage-tabellen-zufallslast-2026-11-10.md`.

## Ergebnis

**Die Frage ist nicht bejaht.** „Körper“ kommt bei 60 Takten auf 89,1 % des besseren Maßstabs, verlangt waren
höchstens 80 %.

| Verfahren | H 30 °C | H 60 °C | Anteil des besseren Maßstabs bei H 60 |
| --- | ---: | ---: | ---: |
| bleibt | 0,434 | 0,666 | 100,0 % |
| Mittel | 0,713 | 0,714 | 107,2 % |
| ohne Lastgeschichte | 0,440 | 0,641 | 96,4 % |
| Körper | 0,437 | 0,593 | 89,1 % |
| Körper, lernt mit | 0,566 | 0,920 | 138,2 % |
| mit Takten seit dem Lastwechsel | 0,415 | 0,553 | 83,1 % |

Bei 30 Takten schlägt kein Modell ohne die Fächer den Maßstab „bleibt“ (Körper 100,5 %).

## Aufnahme und Reiz

- 28.800 Takte, rc 0, keine Abbruchdatei. `koerper.py pruefen`: alle 28.800 Einstufungen und Entscheidungen
  stimmen mit Python überein.
- Vor der Rechnung habe ich nur die Lastspalte angesehen (für R1), keine Temperaturwerte.
- **R1 erfüllt:** 184 Phasen, 182 von 183 vollständigen genau wie `koerper.lastdauern`, eine um 1 Takt kürzer
  (die erste). Kein anderer Reiz war gesetzt.
- **R2 erfüllt:** 35,0 bis 40,0 °C.

## Erwartungen von vorher

- **„Körper“ bei 60 bis 75 %:** nicht eingetroffen, 89,1 %.
- **„ohne Lastgeschichte“ über 85 %:** eingetroffen, 96,4 %.
- **Fächer seit dem Lastwechsel bringen unter 5 Punkte:** nicht eingetroffen, 6,0 Punkte.
- **„lernt mit“ schlechter als „Körper“, aber besser als beide Maßstäbe:** nur der erste Teil, 138,2 %.

## Einordnung

- Mit festem Takt lag „Körper“ bei 49 % von „bleibt“. Mit Zufallslast bleiben 89 %. Der größte Teil des
  Vorsprungs vom Morgen war also Wissen über den Fahrplan, nicht über den Körper.
- Die Probe am künstlichen Körper (nach dem Einfrieren gerechnet) hatte zwei der vier verfehlten Punkte
  angekündigt: die Fächer und „lernt mit“. Für einen idealen Körper mit 30 s Zeitkonstante sagte sie aber
  72 bis 92 % voraus, im Median 75 %. Der echte Lauf liegt am schlechten Rand dieser Spanne. Die strenge
  Grenze allein erklärt das Verfehlen also nicht.
- Der Betragsfehler begünstigt bei ganzen Grad den Maßstab „bleibt“, weil er oft genau null ist. Beim
  Wurzelfehler steht „Körper“ bei 0,715 gegen 0,873 („Mittel“, dort der bessere Maßstab), also 82 %. Das war
  nicht das festgelegte Maß und ändert das Ergebnis nicht.

## Nachträglich beobachtet, ohne Hypothesenstatus

- **Zeitkonstante:** Mit Zufallslast ist sie erstmals bestimmbar. Der einfache Körper passt in beiden Hälften
  am besten mit 30 s, Hub 1,9 °C. Der Restfehler bleibt auch dann bei 0,37 °C.
- **Drift:** Die Prüfhälfte war im Mittel 0,28 °C wärmer (38,24 gegen 37,96 °C). Die Stundenmittel stiegen von
  37,7 auf 38,5 °C und fielen wieder auf 38,2 °C.
- **Hub klein gegen die Auflösung:** 1,9 °C Hub bei 1 °C Stufen. Die Anzeige wechselt 167-mal je 1.000 Takte.

## Was daraus folgt, nicht entschieden

- Für die Selbstvorhersage ist der Chipsensor mit ganzen Grad und 1,9 °C Hub ein schwacher Körper. Ein
  größerer Hub (Lüfter, stärkere Last) oder ein feinerer Fühler (der LM35) würde mehr zeigen.
- Ein nächster Lastlauf braucht Dauern ohne Gedächtnis und eine Erfolgsgrenze, die vorher an künstlichen Daten
  geprobt ist.
