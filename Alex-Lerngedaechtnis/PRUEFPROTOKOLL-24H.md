# Vorabprotokoll: unabhängige 24-Stunden-Prüfung

Fassung `24h-v1`, 6. November 2026. Auftrag 1 aus
[NAECHSTE-RUNDE-DANIEL.md](NAECHSTE-RUNDE-DANIEL.md).
Dieses Protokoll wurde mit künstlichen Gerätezeilen entwickelt. Die reale
24-Stunden-Aufnahme wurde dabei nicht geöffnet. Kern, Vokabular und Firmware
bleiben unverändert. Dies ist eine Prüfung bestehender Warnverfahren, keine
Freigabe einer neuen Geräteeinstellung.

## Zeitpunkt und Durchführung bei Alex

Die Aufnahme endet laut Auftrag am **7. November 2026 gegen 10:40 Uhr**.
Für diesen Plan wird die Zeitzone **Europe/Berlin (CET; 09:40 UTC)** festgehalten.
Maßgeblich ist, dass die endgültige Version von Protokoll, Skript und Abhängigkeiten
vor der ersten Datensicht öffentlich auf GitHub festliegt. Der GitHub-PR mit seinem
Serverzeitpunkt belegt die Bereitstellung. Ein bloß rückdatierter lokaler Commit
reicht nicht. Die tatsächliche erste Datensicht muss Alex/Claude separat bestätigen;
das Skript kann sie nicht nachweisen. Nachträgliche Änderungen werden als neue,
explorative Fassung behandelt; sie ersetzen keinen missliebigen Erstbefund.

Claude führt **nach dem Aufnahmeende und vor dem Betrachten von Kurven oder Zahlen**
im Laborordner die unverändert veröffentlichte Fassung aus:

```sh
cd Alex-Lerngedaechtnis
python3 -B -m unittest test_pruefung24h
python3 -B pruefung24h.py messungen/koerper-startwert-24h-2026-11-06.csv > pruefbericht-24h.md
```

Der zweite Befehl erhält nur den CSV-Pfad. Die gleichnamige JSON-Begleitdatei muss
neben der CSV liegen. Es gibt keine Schalter zum Nachjustieren, keinen Portzugriff
und kein Ändern der Eingaben. Der Bericht gehört zunächst lokal zu Alex. Weitergabe
nur nach inhaltlicher Kontrolle. Das Skript gibt keine lokalen Dateipfade,
JSON-Freitexte oder Kontaktdaten aus. Es druckt Hashes, fest benannte Einstellungen,
Messzahlen und Tabellen.

Rückgabe `0`: vollständiger Bericht. Rückgabe `2`: Abbruch, **keine Güteauswertung**.
Den Rückgabestatus und Bericht unverändert zurückmelden; dazu den verwendeten
Git-Commit, den tatsächlichen Ausführungszeitpunkt und die Bestätigung, ob vorher
jemand die Aufnahme angesehen hatte. Ein negativer Hypothesenbefund ist ein gültiges
Ergebnis und deshalb kein technischer Programmfehler.

## Harte Vorbedingungen

1. Aktueller neunspaltiger CSV-Kopf und lesbare JSON-Datei. Eine vorhandene
   `.abbruch.txt` sperrt diesen Prüfweg, auch wenn davor viele Zeilen aufgezeichnet wurden.
2. Metadaten genau `regel=startwert`, `blick=60`, `intervall_ms=1000`,
   `sichern_alle=600`, `fortsetzung=null`. Erwartet wird ein frischer Lauf.
   Abweichungen werden nicht automatisch „passend“ gemacht.
3. Mindestens 86.400 Zeilen, Takte lückenlos **1, 2, …, N**. Eventuelle zusätzliche
   STOP-Nachlaufzeilen gehören vollständig dazu. Es wird kein günstiger Abschnitt
   ausgeschnitten. Doppelte, fehlende, vertauschte oder bei einem Speichervorgang
   übersprungene Takte führen zum Abbruch. Nach `LADEN` gibt es anderswo eine
   dokumentierte Lücke; dieser Lauf beginnt ausdrücklich ohne `--fortsetzen`.
4. Geordnete Ganzzahlgrenzen, zulässige Rohwerte und Bits, nicht rückläufige
   Empfangszeiten. Zeitangaben dienen der Dokumentation; Horizont und Nenner zählen
   logische Takte, nicht nachträglich geglättete Wanduhrsekunden. Gleichzeitiger
   Empfang mehrerer Zeilen ist zulässig. Fehlende Temperaturwerte werden genau wie
   im Gerät eingestuft (kein Temperaturreiz) und ihre Anzahl wird ausgewiesen.
5. **`koerper.pruefen` muss bestehen.** Zusätzlich wird die gesamte Aufnahme erneut
   mit einem frischen `kern.Knoten(startwert, blick=60)` geprüft. Jede Abweichung
   von Stufe, Sofortmeldung oder Vorwarnung wird mit Taktnummer und beiden Werten
   aufgelistet. Die erlaubte Anzahl ist **null**. Keine Mehrheitsregel, Toleranz
   bei Warnbits oder Reparatur. Strukturfehler können diese Nachrechnung verhindern;
   dann bedeutet eine leere Abweichungsliste ausdrücklich keine bestätigte Parität.
6. SHA-256 von CSV und JSON vor und nach der Rechnung muss gleich sein. Keine
   Auswertung einer noch wachsenden Datei. Der Bericht enthält außerdem Hashes
   des Skripts, Protokolls und aller unmittelbar verwendeten Modellquellen.

Die Aufnahmegrenzen werden unverändert aus der Begleitdatei übernommen und im
Bericht gedruckt. Sie werden nicht anhand der Messreihe gewählt. Unterschiedliche
Grenzen oder Reizbedingungen gegenüber dem alten 6h-Lauf begrenzen die Übertragbarkeit;
ein Datensatz mit solcher Abweichung darf nicht als identische Wiederholung gelten.
Das Skript zertifiziert weder Sensorqualität noch Vollständigkeit der ursprünglichen
Aufzeichnung außerhalb der gelieferten Dateien.

## Vorab festgelegte Verfahren und Horizonte

Alle folgenden Methoden werden bei **30 und 60 Takten** bewertet, jeweils grob und
je Signal. 30 entspricht der eingefrorenen Kostenrechnung #4; 60 entspricht dem
Gerät. Beide Tabellen werden vollständig berichtet. Keine Auswahl des besseren Horizonts.

| Verfahren | Festlegung |
| --- | --- |
| Feste Regel | Warnung genau bei SCHWACH bzw. eigenem hohem Signalwort |
| Festes Erbe | unveränderliches Erbe 3, eigene Kontext-Halbwertszeit 6, Schwelle 0,6 |
| Startwert h6/.6 | Erbe 3; Erb-Halbwertszeit 6 eigene Zustandsausgänge; Schwelle 0,6 |
| Startwert #4 | Erb-Halbwertszeit 1/15/17 für Temperatur/Speicher/Schleife; Schwelle 0,95 |
| Letzter Durchgang | bei hohem Signal warnen, falls der letzte abgeschlossene Nicht-OK-Lauf kritisch war; anfangs nein |
| Immer warnen | in jedem nichtkritischen eigenen Takt warnen, einschließlich OK |
| Nie warnen | keine Vorwarnung |

Die Halbwertszeit **eigener Erfahrung bleibt immer 6**. Mindestbeleg ist 3.
Aktuelle Beobachtung einarbeiten, dann die Zukunft vorhersagen. Nur vergangene und
aktuelle Stufen gehen in die Modelle ein; Reizbits, künftige Zustände und die spätere
Bewertung sind keine Modelleingänge. Modelle starten einmal bei Takt 1 und lernen
über die ganze Aufnahme; keine stündlichen Neustarts.

**Grob:** Ein Dreizustandsmodell sieht die schlechteste Stufe des Geräts. Seine
Warnung wird für Gesamt und für jedes Einzelsignal bewertet. Damit bleibt sichtbar,
wie ein grober Alarm einem bestimmten Signal fälschlich zugeschrieben werden kann.
Beim Spezialfall `Startwert #4` existiert keine einzelne grobe h=1/15/17-Regel:
Daher werden **drei getrennte grobe Modelle** mit h=1,15,17 gerechnet. Für die
jeweilige Signalbewertung gilt dessen h; Gesamt ist deren ODER, bei globalem
AUSFALL unterdrückt. Diese explizite grobe Erweiterung ist **explorativ**, nicht
die in #4 ausgewählte Geräteinstellung. Die anderen sechs Methoden verwenden
dieselbe grobe Warnfolge für alle Signale. Auch „Immer warnen“ respektiert in
der groben Sicht den global kritischen Zustand. Deshalb kann sein Warnanteil
bei einem einzeln noch nichtkritischen Signal unter 100 % liegen; je Signal
erreicht diese Baseline im eigenen nichtkritischen Nenner exakt 100 %.

**Je Signal:** Drei getrennte Dreizustandsmodelle sehen ihre eigenen Signalwörter.
Gesamt ist ODER der drei Warnungen, bei globalem AUSFALL unterdrückt. Eigene
Signalbewertungen werden durch gleichzeitige andere Ausfälle nicht gelöscht.
Es gibt keine Addition der drei Signalkosten zu angeblichen Gerätekosten.

Die schnelle Wahrscheinlichkeitsrechnung aus `kostenlabor` wird nur zur
Auswertung verwendet und fällt nahe den Schwellen auf die Referenz zurück.
Die Geräteparität verwendet ausschließlich den unveränderten `kern.Knoten`.
Synthetische Tests vergleichen beide Warnberechnungen zusätzlich.

## Zähler und Kosten: feste Nenner

L bezeichnet die Zahl aller Aufnahmetakte, Indizes 0 bis L−1. Für Horizont H zählen Bewertungstakte 0 bis L−H−1;
die letzten H Takte liefern bekannte Zukunft und werden nicht zu falschen
Negativbeispielen. Kritische aktuelle Takte zählen nicht als Warngelegenheiten.
**Alle übrigen eigenen Takte einschließlich OK** zählen. Trefferziel: mindestens
ein eigener kritischer Zustand in den folgenden 1 bis H Takten.

- N: auswertbare nichtkritische Takte; W: gewarnte davon.
- Warnanteil W/N, Präzision Treffer/W, Grundrate Zieltakte/N.
- Fehlwarnungen W−Treffer; verpasste Zieltakte Zieltakte−Treffer.
- Eine Phase ist ein ununterbrochener kritischer Lauf, keine nachträgliche
  Zusammenlegung kurzer Unterbrechungen. Nur Beginne H bis L−H−1 zählen.
  Vorgewarnt ist die Phase, wenn in ihren H vorangehenden Takten mindestens eine
  Warnung während eines eigenen nichtkritischen Zustands liegt.
- `Kphase = 10 × unangekündigte Phasen + falsche Warntakte`.
- `Ktakt = 10 × verpasste Zieltakte + falsche Warntakte`.

Beide Kosten werden absolut und je 1.000 **Instrumenttakte L−H** gedruckt, wie #4.
Die Zählung ist im neuen Skript unabhängig implementiert und wird auf zufälligen
Testfolgen mit den bestehenden #4-Zählern verglichen. Ein Nullnenner ergibt `NA`,
keinen erfundenen Wert 0 oder 100 Prozent. Rohzähler bleiben sichtbar.

Zusätzliche Tabellen `nur_hoch` beschränken Warnanteil, Präzision und Grundrate auf
eigene hohe Signalwörter. Sie dienen dem alten Speicherbefund, **nicht** den
#4-Kosten; deshalb enthalten sie keine Kostenspalten. Die Phasenzähler bleiben
unverändert alle auswertbaren Phasen samt nichtkritischen Vorfenstern. Jede
Gütevergleichstabelle enthält auch „Immer warnen“ und „Nie warnen“.

## Numerische Hypothesen vor Datensicht

Die Grenzen sind Übertragungsziele, keine nachträglich berechneten Konfidenzgrenzen.
Alle fünf Teilbefunde werden einzeln ausgegeben, auch bei Widerspruch. Ohne
nötigen Nenner bzw. Phase lautet der Befund `NICHT_PRUEFBAR`. Es gibt weder eine
zusammenfassende Erfolgsnote noch eine Behauptung statistischer Signifikanz.

**H1, Speicherlernen:** Je Signal, Startwert h6/.6, H=30, `nur_hoch`: Präzision
mindestens **65 %**, Warnanteil höchstens **80 % des festen Erbes**, und mindestens
**80 %** der auswertbaren Speicherphasen vorgewarnt. Grundlage: der frühere 6h-Lauf
berichtete 79 statt 52 % Präzision, 90 % Warnungen in tiefen und 26 % in flachen
Blöcken sowie 51/56 vorgewarnte Phasen. Die konservativeren Schwellen verlangen
weiterhin Präzisionsgewinn, nennenswertes Schweigen und begrenzten Verlust von
Phasen. Es wird absichtlich **kein** 40-%-Warnziel aus einem anderen Nenner übernommen.

**H2, Gesamtnutzen:** Je Signal, Startwert h6/.6, H=60, alle eigenen nichtkritischen
Gesamttakte: Warnanteil höchstens **45 %**, Präzision mindestens **65 %**, mindestens
**90 %** der Phasen vorgewarnt. Ausgangspunkt sind 40 %, 70 % und 243/252 im alten
6h-Lauf. Die drei Grenzen müssen gemeinsam erfüllt sein; mehr Schweigen allein reicht nicht.

**H3a/b/c, Kostenübertragung aus #4:** Je Signal und H=30: die eingefrorene
h=1/15/17-Kombination hat für **jedes** der drei Signale `Kphase(r10)` höchstens so
hoch wie h6/.6. Grundlage sind die synthetischen Werte 80,251/59,413/59,313 gegenüber
230,959/203,195/203,271 je 1.000 Takte. Das ist eine bewusst falsifizierbare
Übertragung auf ein Gerät. Für `Ktakt` wird kein Vorteil behauptet: dessen
Optimierung wählte in #4 andere Einstellungen (h24/.05), die hier nicht nachträglich
ergänzt werden. Feste Regel, letzter Durchgang und nie warnen können weiterhin
besser sein; ihre Zahlen bleiben daneben stehen.

Quellen: [UEBERGABE.md](UEBERGABE.md), Abschnitte zum 6h-Startwert und 30min-Gerät;
[KOSTEN-PLAN.md](KOSTEN-PLAN.md) und [KOSTEN-UEBERGABE.md](KOSTEN-UEBERGABE.md).
Die dortige starke Verringerung der Temperaturkosten ging mit viel mehr
unangekündigten Phasen einher. Ein erfülltes H3 ist deshalb kein Sicherheitsnachweis.

## Flashtermine: dokumentieren, nicht ausfiltern

Für **jeden Takt mit Nummer mod 600 = 0** erscheinen Schleifenlücke in µs,
grobe Stufe, Schleifenstufe, Gerätewarnung und Sofortmeldung. Zusätzlich werden
vorab festgelegt die jeweiligen **Folgetakte mod 600 = 1, ab Takt 601** ausgegeben,
weil die Messung eines Takts vor seinem anschließenden Speichervorgang liegen kann.
Eine zweite Tabelle zeigt alle sieben Methoden, beide Horizonte und beide Sichten
mit Gesamt- und Einzelwarnungen an diesen Takten. Der normale Randfensterausschluss
wird angezeigt; ansonsten bleiben diese Takte vollständig in allen Tabellen.

Ein auffälliger Wert beweist ohne unspeichernden Vergleichslauf keine Verursachung
durch Flash. Es werden weder Schwellwerte erhöht noch Lücken gelöscht. Ein
Taktverlust ist ein technischer Abbruch und kein reparierbarer Messpunkt.

## Künstliche Gegenproben und Grenzen

`test_pruefung24h.py` benutzt ausschließlich `test_labor.KoerperTests.geraetezeilen`.
Gezielt beschädigte Spuren enthalten falsche Warnbits, falsche Stufen/Sofortmeldungen,
fehlende Takte einschließlich 600, eine simulierte LADEN-Lücke, unpassende Metadaten
und eine Abbruchdatei. Sie müssen scheitern. Dazu kommen Handzähler, 100 zufällige
Zählervergleiche, Präfixkausalität, langsame Modellreferenz und Nullnenner.
Diese Tests belegen technische Konsistenz, keinen Nutzen auf der echten Aufnahme.

Eine Aufnahme desselben Geräts mit denselben programmierten Reizen ist eine
zeitlich neue Prüfung, aber keine breite Feldstudie. Keine Hardwaremessung wird
hier vorgetäuscht. Den vollständigen Erstbericht bewahren; weitere interessante
Auswertungen erst danach ausdrücklich als explorativ kennzeichnen.

## Prüfung dieser Lieferung vor Veröffentlichung

17 neue Tests und die vollständige Laborsuite mit insgesamt 245 Tests bestanden.
Ein zusätzlicher synthetischer Durchlauf mit 86.400 Gerätezeilen erzeugte alle
28 vorgegebenen Gütevergleichstabellen und fand null Geräteabweichungen. Die
Speichertakt-Tabellen kamen vollständig dazu. Keine reale Aufnahme wurde benutzt.
Ein unabhängiger Review kontrollierte die Onlinefolge, Gerätegleichheit und Nenner.
