# Vorab: Kälteversuch von Hand

Festgelegt am 10. November 2026 um 19:32, vor dem Start der Aufnahme. Explorativer Erstversuch, kein Urteil über das Projekt.

## Lauf

- 15 Minuten, 900 Takte, dieselben Einstellungen wie der 8-Stunden-Lauf vom Morgen (Regel startwert, Blick 60, Grenzen 380 390 65536 16384 20000 200000, Last 240 240 20261110). Firmware unverändert.
- Alex kühlt den Chip von Hand, wann und wie er will. Zeitpunkte und Mittel nennt er danach; sie sind nicht vorgegeben.

## Auswertung

- Gewichte der Körper-Vorhersage (10 Takte voraus) und die Grenze kommen allein aus dem 8-Stunden-Lauf vom Morgen (ganzer Lauf), nichts wird an der neuen Aufnahme angepasst.
- Überraschung: Fehler der Vorhersage, über 20 Takte gemittelt, Betrag über dem 99,9-%-Wert aus dem 8-Stunden-Lauf.
- Daneben der Sprungmelder ohne Modell (Wert gegen Mittel der letzten fünf, 99,9-%-Grenze) als Vergleich.
- Berichtet werden: Alarme mit Takt, Tiefe des Einbruchs gegenüber der Vorhersage, Verzug ab dem ersten Takt unter der Vorhersage, Alarme außerhalb der von Alex genannten Zeiten.

## Erwartung (aus der Probe am Mac)

- Ein Einbruch ab 2 °C löst binnen 30 Takten Alarm aus, typisch nach 8 bis 16 Takten.
- Unter 2 °C ist es Glückssache.
- Außerhalb der Kühlzeiten höchstens ein Alarm in 15 Minuten.

## Vorbehalte

- Die Aufnahme beginnt mit einem Neustart; die ersten 120 Takte werden nicht gewertet.
- Abends ist die Umgebung anders als morgens, die Grenze kann deshalb zu scharf oder zu lasch sein.
