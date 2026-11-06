# Signallabor: geprüfte Übergabe für Alex und Claude

Stand 6. November 2026. Rechenaufgabe 2 ist implementiert und ausgeführt:
8.000 synthetische Spuren à 960 Takte, vier Familien, je 1.000 Entwicklungs-
und Kontrollspuren pro Familie. Das sind 7.680.000 generierte Takte,
96.000 Verfahrens-/Sichtdurchläufe und 384.000 CSV-Ergebniszeilen.
Es wurden keine echten Aufnahmen verwendet und keine Parameter optimiert.

## Einstieg

- `signallabor.py`: Generator, sechs Vergleichsverfahren, Bewertung und CSV-Export.
- [SIGNAL-LABOR.md](SIGNAL-LABOR.md): vor dem großen Lauf festgelegte Definitionen
  und Befehle. Die Manifeste bestätigen per Hash denselben Plan und Code für beide Sätze.
- [Ergebnisordner](beispiele/signallabor-2026-11-06): Summen je Familie/Sicht/Signal,
  Manifeste und vollständige Einzelwerte im ZIP (Entwicklung und Kontrolle getrennt).
- `test_signallabor.py`: 19 zusätzliche Tests. Gesamtsuite: 193 Tests erfolgreich,
  einschließlich der bestehenden C++-Hostvergleiche. Zusätzlich stimmten bei zwölf
  weiteren 960-Takt-Spuren alle Warnfolgen mit der unbeschleunigten Originalrechnung überein.

Der Ausgangsstand ist der bereinigte Commit
`e894424235ef779ec6cb4def26e91b335186f264` (Weiterlernen über Körperaufnahmen).
`kern.py`, `vokabular.py`, `koerper.py` und Firmware wurden nicht verändert.

## Kontrollsatz: Gesamtsicht

Summe über vier Familien, jeweils 4.000 Spuren pro Zeile. Die Größen sind
Quotienten der Rohzähler; Phasen verschiedener Signale werden hier zusammengefasst.
Warnanteil und Trefferquote beziehen sich auf alle aktuell nichtkritischen Takte.

| Sicht / Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|
| grob / Feste Regel | 42,25 % | 78,00 % | 72,47 % | 0 / 105588 |
| grob / Festes Erbe | 81,22 % | 70,45 % | 72,47 % | 0 / 105588 |
| grob / Startwert | 64,49 % | 72,11 % | 72,47 % | 4020 / 105588 |
| grob / Ohne Erbe | 51,74 % | 72,92 % | 72,47 % | 9156 / 105588 |
| grob / Letzter Durchgang | 26,10 % | 82,48 % | 72,47 % | 14747 / 105588 |
| grob / Immer warnen | 100,00 % | 72,47 % | 72,47 % | 0 / 105588 |
| je_signal / Feste Regel | 42,25 % | 78,00 % | 72,47 % | 0 / 105588 |
| je_signal / Festes Erbe | 74,21 % | 70,07 % | 72,47 % | 0 / 105588 |
| je_signal / Startwert | 65,46 % | 70,99 % | 72,47 % | 114 / 105588 |
| je_signal / Ohne Erbe | 45,59 % | 71,95 % | 72,47 % | 3323 / 105588 |
| je_signal / Letzter Durchgang | 22,56 % | 84,88 % | 72,47 % | 13619 / 105588 |
| je_signal / Immer warnen | 100,00 % | 72,47 % | 72,47 % | 0 / 105588 |

## Kontrollsatz: Speicher bei wechselnden Blöcken

1.000 Spuren der Familie `bloecke`, eigenes Gedächtnis je Signal. Warnanteil und
Trefferquote beziehen sich hier auf hohe Speicherstufen, nicht auf alle Takte.

| Sicht / Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|
| je_signal / Feste Regel | 100,00 % | 50,01 % | 50,01 % | 0 / 9747 |
| je_signal / Festes Erbe | 100,00 % | 50,01 % | 50,01 % | 0 / 9747 |
| je_signal / Startwert | 92,88 % | 51,31 % | 50,01 % | 398 / 9747 |
| je_signal / Ohne Erbe | 53,74 % | 68,94 % | 50,01 % | 1904 / 9747 |
| je_signal / Letzter Durchgang | 47,42 % | 77,02 % | 50,01 % | 2216 / 9747 |
| je_signal / Immer warnen | 100,00 % | 50,01 % | 50,01 % | 0 / 9747 |

## Kontrollsatz: Temperatur bei wechselnden Blöcken

Dieselben 1.000 Spuren, eigene Temperaturstufen. Die erzeugte Wärmefolge ist
zufällig; ein vergangener heißer Durchgang verrät nicht den nächsten Ausgang.

| Sicht / Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |
|---|---:|---:|---:|---:|
| je_signal / Feste Regel | 100,00 % | 37,92 % | 37,92 % | 0 / 7473 |
| je_signal / Festes Erbe | 100,00 % | 37,92 % | 37,92 % | 0 / 7473 |
| je_signal / Startwert | 92,19 % | 37,85 % | 37,92 % | 538 / 7473 |
| je_signal / Ohne Erbe | 43,40 % | 38,22 % | 37,92 % | 3712 / 7473 |
| je_signal / Letzter Durchgang | 35,81 % | 38,81 % | 37,92 % | 4624 / 7473 |
| je_signal / Immer warnen | 100,00 % | 37,92 % | 37,92 % | 0 / 7473 |

## Was sich daraus ableiten lässt

Der Startwert senkt die Warnlast gegenüber dem festen Erbe, verliert dabei aber
Vorwarnungen. In diesen relativ kurzen künstlichen Verläufen verbessert er die
Trefferquote des wechselnden Speichers nur wenig. Die einfache Vergleichsregel
„letzter Durchgang“ erkennt die Blockstruktur besser, übersieht aber Wechsel und
seltene Ausnahmen. Bei zufälligen Wärmeausgängen bringt selektives Warnen keine
entsprechende Verbesserung der Trefferquote. Eine bloß höhere Trefferquote reicht
deshalb nicht als Auswahlkriterium: Warnlast und verpasste Phasen müssen mit hinein.

Das ist keine Bestätigung oder Widerlegung der Zahlen aus Alex' sechs Stunden.
Die synthetischen Spuren bilden andere Dauern und Wechselhäufigkeiten ab.

Grenzen, bei der Ergebnisinterpretation ausdrücklich festgehalten: In diesem
Generator hat jeder Ausfall ein hohes Vorzeichen innerhalb des Horizonts. Damit
ist die vollständige Phasenabdeckung der festen Regel konstruktionsbedingt.
„Immer warnen“ ist ebenfalls kein Beleg für Vorhersagefähigkeit; dafür stehen
Trefferquote und Grundrate daneben. Unerwartete Ausfälle ohne Vorzeichen,
physikalische Erwärmung, zeitlich korrelierte Sensorfehler und echte Energie-
oder RAM-Kosten sind nicht modelliert. Ein Takt ist keine kalibrierte Sekunde.
Es wurden keine nachträglichen zusätzlichen Leistungskennzahlen eingeführt.
Bei der unabhängigen Durchsicht wurde ein Fehler in der Phasengruppierung entdeckt
und vor Freigabe korrigiert: angrenzende kritische Takte bilden genau eine Phase.
Ein Regressionstest deckt das ab. Beide Datensätze wurden vollständig neu gerechnet;
Warnverfahren, Generator und Parameter blieben dabei gleich.

## Weiterarbeiten ohne Datenleck

1. Für Aufgaben 1 und 3 Kostenverhältnisse und Halbwertszeitraster vorab festlegen.
   Den Entwicklungssatz zum Wählen benutzen. Die bereits angesehenen Kontrollwerte
   dieses Berichts sind danach keine unberührte Bestätigung mehr: neue Kontrollseeds
   (beispielsweise ab 10.000 über die Python-API) vor dem nächsten Versuch reservieren.
2. Die Bibliotheksfunktionen `generiere`, `verfahren`, `auswerten` können direkt
   verwendet werden. Modelle bekommen ausschließlich aktuelle/eigene Beobachtungen,
   keine Generator-Ausgänge oder zukünftigen Phasenmarkierungen.
3. Erst nach Einfrieren der Auswahl Alex' unabhängigen langen Lauf prüfen.
   Rechenaufgaben 1, 3–7 sind mit dieser Übergabe noch nicht erledigt.

Die unveränderte Einstellung dieses Versuchs ist nicht als Empfehlung ausgewählt.
Der Kontrollsatz wurde nach dem Entwicklungssatz ausgeführt, ohne dazwischen
Generator, Verfahren, Schwelle oder Halbwertszeit zu ändern.

## Rohdaten und Nachprüfung

`einzelwerte.zip` enthält acht CSV-Dateien (Satz/Familie), je 48.000 Zeilen plus
Kopfzeile. `index.json` enthält Größen und SHA-256-Prüfsummen der acht Dateien.
Die ursprünglichen Einzel-CSV-Prüfsummen der Manifeste lassen sich rekonstruieren:
Dateien pro Satz in Reihenfolge bloecke, zufallsmaske, seltene_ausnahme,
ueberlagerung zusammenfügen, nur die erste Kopfzeile behalten, CRLF beibehalten.
Die Summen wurden vor der Übergabe unabhängig aus allen Einzelzeilen nachgerechnet;
sämtliche Phasenzahlen zusätzlich direkt aus den generierten Zustandswechseln geprüft.
Quellhashes, Ergebnisprüfsummen, vollständige Zeilenzahlen und ZIP-Rücklesung stimmen.
Das ZIP enthält ausschließlich generierte Werte und neutrale Dateimetadaten.
Lokale Pfade, Kontaktangaben, Git-Konfiguration und Logs sind nicht Bestandteil.
