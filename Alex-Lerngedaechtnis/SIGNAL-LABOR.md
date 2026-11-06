# Signallabor: vorab festgelegter Versuchsplan

Rechenaufgabe 2 aus RECHEN-UEBERGABE.md, Fassung 1 vom 6. November 2026.
Die Definitionen stehen vor der ersten großen Ergebnisreihe fest. Keine echte
Messaufnahme wird eingelesen. Keine Schwelle oder Halbwertszeit wird hier gewählt.
Die bestehenden Lernregeln und die Firmware bleiben unverändert.

## Generierte Beobachtungen

Pro Spur 960 Takte, drei getrennte Stufenfolgen (Temperatur, Speicher, Schleife).
Ein Takt ist eine synthetische Zeiteinheit; es gibt keine Hardwarekalibrierung.
Jedes Signal beginnt mit 1–12 OK-Takten, danach wiederholen sich hohe Stufe
(1–12 Takte), optional kritische Stufe (2–8), OK-Pause (Horizont + 2–12).
Diese Pause verhindert, dass ein späterer Durchgang einem harmlosen Durchgang
versehentlich als dessen unmittelbarer Ausgang zugerechnet wird.

Vier Familien:

- `bloecke`: Speicher und Schleife wechseln nach jeweils 3–8 Durchgängen zwischen
  tiefem und flachem Ausgang; 5 % der Ausgänge widersprechen dem aktuellen Block.
- `zufallsmaske`: Speicher und Schleife ziehen ihren Ausgang unabhängig mit 50 %.
  Hier kann der letzte Durchgang prinzipiell keine zuverlässige Vorschau liefern.
- `seltene_ausnahme`: Speicher und Schleife werden in 95 % der Durchgänge kritisch;
  der Rest bleibt hoch. Ausnahmen sind Bernoulli-Ziehungen, nicht exakt jeder 20.
- `ueberlagerung`: wie Blöcke, Temperatur bleibt aber 15–30 Takte hoch. Der Vorrang
  der Temperatur verdeckt so häufiger Speicher- und Schleifensignale.

In jeder Familie wird ein warmer Durchgang mit Wahrscheinlichkeit 0,38 kritisch,
einstellbar über `--waerme-p`. Das ist eine Wahrscheinlichkeit pro Durchgang,
keine Garantie einer gemessenen 38-%-Trefferquote je warmem Takt. Abweichende
Beobachtungsfenster, abgeschnittene Randdurchgänge und Überlagerung ändern die
gezählte Grundrate. Alle Signale laufen unabhängig und können sich überlagern.
Es werden Stufen erzeugt, keine physikalisch simulierten Sensorwerte.

## Trennung und Vergleiche

Entwicklung und Kontrolle bekommen getrennte, durch SHA-256 abgeleitete
Zufallsströme, ebenso Familie, Seed und Signal. Plan: je Satz 1.000 Seeds je
Familie (0–999), insgesamt 8.000 Spuren bzw. 2.000 pro Familie. Nach Ansicht der
Kontrollwerte darf dieser Kontrollsatz keine unabhängige Bestätigung für eine
daran angepasste Regel mehr heißen. Dafür ist ein neuer, vorab reservierter Satz
nötig. Alle Verfahren sehen je Vergleich dieselbe Spur und beginnen frisch.

Sechs Verfahren, jeweils grob und je Signal: feste Regel (bei hoher Stufe warnen),
festes Erbe, verblassender Startwert, ohne Erbe, letzter Durchgang, immer warnen.
Gedächtnisse verwenden unverändert Halbwertszeit 6, Erbgewicht 3, Mindestbeleg 3,
Schwelle 0,6 und Horizont 30. „Ohne Erbe“ heißt Kontextregel mit Erbgewicht 0.
„Letzter Durchgang“ merkt nur, ob der letzte vollständig beobachtete Nicht-OK-Lauf
kritisch wurde; bei aktueller hoher Stufe warnt es entsprechend. Vor dem ersten
Abschluss warnt es nicht. Es erhält keine zukünftigen Daten oder Zyklusmarken.

Grob wird der schwerste Zustand mit Vorrang Temperatur > Speicher > Schleife
verwendet. Je Signal lernt jedes seinen eigenen Verlauf. Gesamtwarnung ist das
ODER dieser Warnungen, unterdrückt während eines beliebigen aktuellen Ausfalls.
Ein einzelnes Signal darf vor seinem eigenen Ausfall warnen, auch wenn ein anderes
schon ausgefallen ist. In der groben Sicht gilt die Gesamtwarnung für jedes Signal.

Der schnelle Dreierblick potenziert dieselbe absorbierende Übergangsmatrix.
Beobachtung, Alterung und Belegzählung stammen aus Wortgedaechtnis. Bei höchstens
1e-10 Abstand zur Warnschwelle wird die Originalrechnung benutzt. `--referenz`
deaktiviert die Beschleunigung; Tests prüfen Wahrscheinlichkeiten und Warnfolgen.
Das ist eine Beschleunigung der Laborrechnung, keine Firmwareänderung.

## Zählung vor der Auswertung festgelegt

- Pro Takt: Warnanteil = Warntakte / auswertbare Takte; Trefferquote = Warntakte
  mit eigenem Ausfall in den folgenden 1–30 Takten / Warntakte; Grundrate =
  entsprechende Zieltakte / auswertbare Takte. Leere Nenner bleiben leer.
- Gesamt sind alle aktuell nichtkritischen Takte auswertbar. Je Signal sind es
  dessen hohe Takte, auch wenn sie durch ein anderes Signal verdeckt werden.
  Ein fremder Ausfall zählt nie als Treffer für dieses Signal.
- Die letzten 30 Takte dienen nur als bekannte Zukunft, nicht als angeblich
  negative Beispiele. Gelernt wird von Takt 0 an, ohne Burn-in auszublenden.
- Ausfallphasen sind zusammenhängende kritische Takte ohne Glättung (`zusammen=1`,
  anders als der Standard `zusammen=10` von vokabular). Gezählt werden nur Beginne ab Takt 30
  und vor Takt 930: voller Vorlauf und dieselbe abgeschlossene Bewertungsperiode.
  Eine Warnung im eigenen nichtkritischen Vorfenster genügt als Vorwarnung.
- CSV enthält die Rohzähler einschließlich verpasster Phasen. Summenquoten sind
  Quotienten der aufsummierten Zähler, keine Mittelwerte von Prozentwerten.
- `verdeckt` zählt hohe Signaltakte, deren Wort nicht als schwerstes Wort erscheint.
  Dieselben Zähler stehen je Verfahren wiederholt; nicht über Verfahren addieren.
- Jede Vergleichsgruppe enthält „Immer warnen“. Je Signal erreicht diese Baseline
  in der eigenen Sicht Warnanteil 1 und Trefferquote = Grundrate. In der groben
  Sicht können fremde aktuelle Ausfälle Warnungen unterdrücken; das ist Teil der
  Informationsgrenze der groben Sicht, keine vollständige Signal-Baseline.

Die Ergebnisse sind ein kontrollierter synthetischer Belastungstest. Sie belegen
keine Einsparung oder Zuverlässigkeit auf einem echten Gerät. Unsicherheitsintervalle,
Kostenoptimierung, Halbwertszeitraster, neue Gedächtnisregeln und Firmware-Dauertests
gehören zu den anderen Aufgaben und werden hier nicht als erledigt ausgegeben.

Vor Freigabe wurde ein Implementierungsfehler korrigiert: `zusammen=0` hätte
benachbarte Ausfalltakte getrennt, entgegen der oben festgelegten Phasendefinition.
Die Zählung verwendet deshalb `zusammen=1`; beide großen Sätze wurden vollständig
neu gerechnet. Warnverfahren, Generator und Parameter wurden dabei nicht geändert.

## Ausführen und weiterarbeiten

Im Laborordner `Alex-Lerngedaechtnis` mit Python 3.9 oder neuer:

```sh
python3 -B -m unittest
python3 -B signallabor.py --satz entwicklung --anzahl 1000 --prozesse 4 --ausgabe rechen-ergebnisse/entwicklung
python3 -B signallabor.py --satz kontrolle --anzahl 1000 --prozesse 4 --ausgabe rechen-ergebnisse/kontrolle
```

Jeder neue Ausgabeordner enthält `einzel.csv`, `summen.csv` und `manifest.json`.
Vorhandene Ordner werden nicht überschrieben. Ein abgebrochener Lauf bleibt als
`unvollstaendig` markiert. Das Manifest speichert Einstellungen, Quellhashes und
Ergebnisprüfsummen, keine Benutzernamen, Kontaktangaben oder absoluten Quellpfade.
Die Reihenfolge und CSV-Inhalte sind auch mit mehreren Prozessen deterministisch.

Kleiner Prüflauf: `--anzahl 2 --takte 120`; Referenzvergleich zusätzlich mit
`--referenz` und einem anderen Ausgabeordner. Andere Wärmechance beispielsweise
mit `--waerme-p 0.8`. Aufgaben 1 und 3 sollten eigene neue Pläne und unangesehene
Kontrollsätze verwenden; diese Reihe wählt keine optimale Einstellung aus.
