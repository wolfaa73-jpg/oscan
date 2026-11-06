# Vorabplan: Warnschwellen und Erb-Halbwertszeit

6. November 2026, Aufgaben 1 und 3. Der Plan wird vor der Rasterrechnung festgelegt;
die Auswahl wird nach der Entwicklung als JSON eingefroren und vor dem Kontrolllauf
lokal committet. Echte Messaufnahmen werden weder gelesen noch zum Einstellen benutzt.

## Datensätze und Kandidaten

Generator aus `signallabor.py`, unveränderte vier Familien, je 960 Takte und Horizont 30.
Entwicklung: 250 Seeds/Familie (0–249, Entwicklungsnamensraum). Diese Entwicklungs-
spuren waren bereits im ersten Signallabor enthalten; sie dürfen zum Einstellen dienen.
Kontrolle: 500 Seeds/Familie (10.000–10.499, Kontrollnamensraum), vorher nicht angesehen.
Tests/Probeläufe verwenden andere Seeds ab 900.000. Die Auswahl verwendet die Summe
über gleich viele Spuren aller vier Familien je Signal; Familienwissen ist kein
zusätzlicher Eingang des Warnverfahrens. Pro Spur beginnt das Gedächtnis neu.

Schwellen: 0,05 bis 0,95 in Schritten von 0,05. Startwert-Halbwertszeiten: 1–24
eigene Zustandsausgänge. **Nur das Erbe bekommt den neuen Ausgangsfaktor.** Eigene
Erfahrung altert weiterhin mit Halbwertszeit 6 Beobachtungen; Selbstübergänge lassen
das Erbe unverändert. Festes Erbe bleibt fest. `kern.Startwertgedaechtnis`, `vokabular`
und die Firmware werden nicht verändert. Bei h=6 entspricht das neue Modell dem
bisherigen Startwert. Die schnelle Rechnung fällt an jeder Rastergrenze auf die
Originalrechnung zurück, wenn der Abstand kleiner als 1e-10 ist.

Vier getrennte Suchräume je Signal: festes Erbe/Schwelle; Startwert h=6/Schwelle;
Startwert Schwelle 0,6/Halbwertszeit; gemeinsames Startwert-Raster. Baselines sind
feste Regel, immer warnen, nie warnen und letzter Durchgang. Die Defaultmodelle
(festes Erbe 0,6 und Startwert h 6/0,6) werden immer mit auf Kontrolle geprüft.

## Zwei ausdrücklich verschiedene Kostenbegriffe

Alle eigenen **nichtkritischen Takte**, auch OK, zählen. Eine Warnung während OK
kann daher einen Fehlalarm verursachen. Ein Treffer bedeutet eigener kritischer
Zustand in den folgenden 1–30 Takten. Die letzten 30 Takte dienen nur als Zukunft.
Ein hoher Signalzustand ist kein Filter für die Kosten. Phasen sind zusammenhängende
kritische Takte; volle Vorfenster wie im Signallabor, Beginne zwischen 30 und 929.

Für jedes ganzzahlige r=1…100 werden zwei Größen getrennt ausgewertet:

- `takt`: r × verpasste Zieltakte + falsche Warntakte. r ist der Preis eines
  nicht gewarnten positiven Takts in Einheiten eines falschen Warntakts.
- `phase`: r × verpasste Phasen + falsche Warntakte. r ist der Preis eines
  ganzen unangekündigten Ausfalls in Einheiten eines falschen Warntakts.

Eine Phase gilt als vorgewarnt, wenn im eigenen nichtkritischen Vorfenster eine
Warnung liegt. Die zwei Kostenarten sind nicht austauschbar. Es gibt keine
Behauptung, diese Preise seien für das Gerät bekannt. Signalweise Kosten dürfen
nicht ohne Weiteres addiert werden, wenn mehrere Signale dieselbe Aktion auslösen.

Minimiert werden exakte ganzzahlige Entwicklungskosten. Nur bei echtem Gleichstand:
weniger verpasste Phasen, weniger Warntakte, kleinerer Abstand des Schwellenindex
zu 12 (=0,6), kleinerer Abstand h zu 6, kleineres h, kleinerer Schwellenindex.
Festes Erbe wird in einem eigenen Suchraum behandelt (h=0 nur als Tabellenkennung).
Auch beim Taktkostenmodell sind Phasen damit ausdrücklich ein sekundäres Kriterium.

## Einfrieren und unabhängige Prüfung

`auswahl.json` enthält alle 2.400 Entscheidungen (3 Signale ×2 Kostenmodelle ×100
Verhältnisse ×4 Suchräume), genaue Splitbereiche, Quell-/Generator-/Planhashes,
Konfigurations-IDs und Tiebreakversion. Danach prüft die Kontrolle ausschließlich
die Vereinigungsmenge dieser Konfigurationen, Defaults und Baselines. Sie führt
keine neue Auswahl aus. Die unberührte Auswahldatei wird per Hash nachgewiesen.

Das vollständige Halbwertszeit-/Schwellenraster und familienweise Optima werden
nur auf Entwicklung gezeigt. Sie beschreiben Musterabhängigkeit, keine unabhängig
bestätigten Gewinner. Kontrollkosten werden für jede eingefrorene Auswahl und
Familie ausgegeben. Die diskreten Wechsel der gewählten Einstellung über r gelten
für dieses Raster und diese synthetische Mischung, nicht als allgemeine Preisgrenzen.

Berichtet werden Rohzähler, Warnanteil, Trefferquote, Grundrate, verpasste Phasen,
Kosten und Verbesserung gegenüber unveränderten Defaultmodellen. Alle Vergleichs-
tabellen führen „Immer warnen“. Kostendarstellung je 1.000 ausgewertete Instrument-
takte (930 pro Spur), kein Mittelwert gerundeter Prozentwerte.

Für r=1,10,100: gepaarte Bootstrap-Intervalle der Kostendifferenz zum entsprechenden
Default (festes Erbe oder Startwert h 6/0,6). Je 500 Wiederholungen, Ziehung ganzer
Spuren mit Zurücklegen innerhalb jeder Familie, gleicher Seedindex für beide
Verfahren. Bootstrap-Seed 20261106. Quantile durch lineare Interpolation an Position (n−1)×p. 2,5-/97,5-%-Quantile als punktweise 95-%-
Intervalle; kein gemeinsamer Signifikanztest über alle Vergleiche. Keine Unsicherheit
aus einzelnen Takten konstruieren. Auch ein schmales Intervall beschreibt nur den
synthetischen Generator, nicht unbekannte reale Ausfallursachen.

## Reproduktion

Im Laborordner:

```sh
python3 -B -m unittest
python3 -B kostenlabor.py entwicklung --ausgabe rechen-ergebnisse/kostenentwicklung
# Auswahl prüfen und festhalten, bevor Kontrolle gestartet wird.
python3 -B kostenlabor.py kontrolle --auswahl rechen-ergebnisse/kostenentwicklung/auswahl.json --ausgabe rechen-ergebnisse/kostenkontrolle
```

Die abschließende Auswertung ist verbindlicher Teil der Pipeline:
`python3 -B kostenbericht.py --entwicklung rechen-ergebnisse/kostenentwicklung --kontrolle rechen-ergebnisse/kostenkontrolle --ausgabe rechen-ergebnisse/kostenbericht`.
Sie prüft die Auswahl- und Ergebnisprüfsummen und erstellt die vorgeplanten
Bootstrap-Intervalle und normalisierten Kostentabellen.

Ergebnisordner werden nie überschrieben. Manifeststatus bleibt bei Abbruch
`unvollstaendig`. Entwicklung speichert das gesamte aggregierte Raster und die
gefrorene Auswahl; Kontrolle zusätzlich jede Spur/Konfiguration als CSV. Dateien
enthalten keine Kontaktangaben, Benutzernamen oder absoluten lokalen Pfade.
Aufgaben 4–7 und die Prüfung an unabhängigen echten Aufnahmen bleiben offen.
