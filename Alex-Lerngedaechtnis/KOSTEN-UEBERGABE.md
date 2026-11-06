# Für Alex und Claude: Kosten und Vergessensgeschwindigkeit

6. November 2026. Aufgaben 1 und 3 sind als synthetische Untersuchung umgesetzt
und geprüft; zusammen mit dem Signallabor liegt damit die Grundlage für Aufgaben
1–3 vor. Ein Nachweis am echten Gerät steht weiter aus. Die vollständige Testsuite besteht
mit 228 Tests, einschließlich der vorhandenen C++-Hostvergleiche.

## Das wichtigste Ergebnis

Die passenden Warnschwellen und Erb-Halbwertszeiten hängen stark vom Kostenbegriff
ab. Die gewählten Einstellungen verbessern die bisherigen Standardwerte auf neuen
Kontrollspuren überwiegend, teilweise deutlich. Einzelne eingefrorene Einstellungen
haben auf der Kontrolle höhere Kosten als der jeweilige Default. Trotzdem sind einfache Vergleichsregeln in mehreren
Szenarien günstiger. Eine universell bessere Lernregel ist damit nicht nachgewiesen.

Beispiel aus einem vorab festgelegten Vergleich: **Eine verpasste Phase kostet
10 falsche Warntakte**. Werte sind Kosten je 1.000 ausgewertete Instrumenttakte,
je Signal getrennt; die Spalten sind keine addierbaren Gerätekosten.

| Verfahren | Temperatur | Speicher | Schleife |
|---|---:|---:|---:|
| Startwert, bisher h=6 / Schwelle 0,6 | 230,959 | 203,195 | 203,271 |
| Startwert, vorher gewählte Kombination | 80,251 | 59,413 | 59,313 |
| Feste Regel | 124,780 | 56,032 | 55,869 |
| Immer warnen | 725,672 | 543,118 | 542,340 |
| Nie warnen | 75,081 | 125,387 | 125,495 |
| Letzter Durchgang | 92,299 | 45,539 | 45,208 |

Für die gewählte Kombination gelten hier h=1/15/17 für Temperatur/Speicher/Schleife,
jeweils Schwelle 0,95. Wird hingegen **jeder verpasste Zieltakt** mit 10 berechnet,
wählt dieselbe Entwicklung für alle drei Signale h=24 und Schwelle 0,05. Die zwei
Kostenarten beschreiben verschiedene Handlungsziele, obwohl beide die Zahl 10 tragen.
Dass bei günstigen verpassten Phasen sogar „nie warnen“ günstiger sein kann,
zeigt, wie entscheidend die Definition dieses Handlungsziels ist.

Die Reduktion der Kosten bedeutet nicht, dass mehr Ausfälle angekündigt werden:
Im obigen Temperaturvergleich bleiben mit der gewählten Kombination 11.067 von
13.965 Phasen unangekündigt, gegenüber 792 mit dem bisherigen Startwert. Der
Kostenbegriff nimmt dieses Verhältnis ausdrücklich in Kauf. Diese Werte sind
deshalb keine Empfehlung, die Firmware auf diese Einstellung umzuschalten.

Die genaue Kostendifferenz zum bisherigen Startwert beträgt in diesem Vergleich
−150,708 je 1.000 Takte; das punktweise Bootstrap-Intervall ist [−152,022; −149,591].
Es beschreibt die Stichprobenunsicherheit dieses künstlichen Generators, keine
Zuverlässigkeitsgarantie für echte Geräte. Alle übrigen vorher festgelegten
Vergleiche stehen im vollständigen Bericht, einschließlich der Baselines.

## Was geliefert wird

- [KOSTEN-PLAN.md](KOSTEN-PLAN.md): vor der Rechnung festgelegte Datensätze,
  Kostenbegriffe, Auswahlregeln und Auswertung.
- `kostenlabor.py`: 19 Schwellen und 24 Erb-Halbwertszeiten; die Halbwertszeit
  eigener Erfahrung bleibt 6. Festes Erbe bleibt fest. Bestehende Kernregeln,
  Körperaufnahme und Firmware wurden nicht verändert.
- `kostenbericht.py`: prüft Hashes, Auswahlregeln, alle Kontrollrohzeilen und deren
  Paarung; erzeugt 72 gepaarte Bootstrap-Intervalle mit je 500 Wiederholungen.
- [Bericht](beispiele/kostenlabor-2026-11-06/bericht/KOSTEN-ERGEBNISSE.md): 18
  Kostentabellen für r=1,10,100 mit allen Baselines und den passenden Nennern.
- [Schwellenwechsel](beispiele/kostenlabor-2026-11-06/bericht/schwellenwechsel.csv):
  direkt ablesbar, für welche r-Bereiche von 1 bis 100 die Entwicklung dieselbe
  Einstellung wählt. Das sind diskrete Bereiche dieses Rasters, keine universellen Preise.
- [Halbwertsprofil](beispiele/kostenlabor-2026-11-06/bericht/halbwertsprofil.csv):
  alle h=1…24 bei Schwelle 0,6, je Familie und gepoolt, samt Baselines. Familienweise
  Entwicklungsoptima stehen zusätzlich in `entwicklung/familien-auswahl.csv`.
- [Ergebnisordner](beispiele/kostenlabor-2026-11-06): vollständige Entwicklung,
  eingefrorene Auswahl, Kontrollsummen, 206.000 Kontrollrohzeilen im ZIP und Manifeste.

## Wie die neue Kontrolle getrennt blieb

1. Entwicklung: 250 bereits verfügbare Entwicklungsseeds je Familie, insgesamt
   1.000 Spuren. Alle Kandidaten verwenden dieselben Beobachtungen.
2. Die 2.400 Entscheidungen wurden zusammen mit Plan und Kostenkern in Commit
   `17b9391f9ff8a68c8baaac8bcd084bdf50b9fdf1` festgehalten, **vor** dem Kontrolllauf.
3. Kontrolle: 500 neue Seeds je Familie, 10000–10499 im getrennten Kontrollnamensraum,
   insgesamt 2.000 vorher unbetrachtete Spuren. Geprüft wurden nur die ausgewählten
   Konfigurationen und vorher festgelegten Defaults/Baselines, keine neue Auswahl.
4. Die Auswahl blieb byteidentisch. SHA-256:
   `1ff54ae27c1f11244c9290835e4f1109291d485ce7f519c3facbcf70001740f2`.

Der Bericht bestätigt die Entwicklungsoptima einschließlich Tiebreak nochmals
auf der Entwicklung. Er stellt außerdem sicher, dass je Familie/Signal/Seed alle
verglichenen Konfigurationen dieselben auswertbaren Takte, Ziele und Phasen besitzen.
Bootstrap resampelt ganze gepaarte Spuren innerhalb der jeweiligen Familie.

## Nachprüfen und fortsetzen

Im Laborordner `Alex-Lerngedaechtnis`:

```sh
python3 -B -m unittest
python3 -m zipfile -e beispiele/kostenlabor-2026-11-06/kontrolle/einzelwerte.zip beispiele/kostenlabor-2026-11-06/kontrolle
python3 -B kostenbericht.py --entwicklung beispiele/kostenlabor-2026-11-06/entwicklung --kontrolle beispiele/kostenlabor-2026-11-06/kontrolle --ausgabe rechen-ergebnisse/nachpruefung
```

Das ZIP enthält ausschließlich `einzel.csv`; entpackt ist sie rund 20 MB groß und
wird lokal ignoriert. Der Bericht prüft ihren Hash gegen das unveränderte Manifest.
Ein neuer Ausgabeordner ist nötig. Die vollständige Entwicklungs-/Kontrollrechnung
lässt sich mit den Befehlen im Plan wiederholen.

Zwei Randfälle des ersten Signallabors sind abgesichert: ungültige Horizonte
werden abgewiesen; Testverläufe müssen länger als der doppelte Horizont sein.
Die ersten 8.000 Standardspuren bleiben unverändert. Deren historische Quellhashes
beziehen sich auf den veröffentlichten Stand
`92f7013b9656f48de80ec858050218033df602e1`, nicht auf die zusätzlich abgesicherte Datei.

## Was weiterhin entschieden und geprüft werden muss

Alex muss festlegen, welche konkrete Handlung eine Warnung auslöst und was dabei
ein Fehlalarm bzw. ein verpasster Ausfall kostet. Erst dann ist eine Einstellung
aus diesem Raster sinnvoll interpretierbar. Viele Rasteroptima liegen am Rand
(zum Beispiel h=24); damit ist kein Optimum außerhalb des geprüften Bereichs ausgeschlossen.

Alle künstlichen Ausfälle haben ein hohes Vorzeichen. Die feste Regel wird dadurch
begünstigt. Echte Aufnahmen, unbekannte Ausfälle ohne Vorzeichen, korrelierte
Sensorfehler und Energie-/Aktionskosten fehlen weiterhin. Nach Sichtung dieser
Kontrolle dürfen neue Einstellungen nicht mit denselben Daten als unabhängig
bestätigt bezeichnet werden. Nächste Schritte sind eine vorab festgelegte Prüfung
an Alex' unabhängiger Aufnahme und gegebenenfalls der getrennte Verweildauer-/
Richtungsansatz aus Aufgabe 4. Aufgaben 4–7 sind nicht als abgeschlossen ausgewiesen.
