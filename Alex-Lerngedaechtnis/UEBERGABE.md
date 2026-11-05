# Übergabe an Alex und Claude

**Version 0.2 · Stand 4. November 2026**

Alex’ Fernziel ist ein lokales System, dessen Gedächtnis die Arbeit vorhandener Geräte mitsteuert. Im Labor kann man den ersten Mechanismus isoliert untersuchen. Eine erlernte Vorhersage verändert die ausgehenden Meldungen. Der feste Ausfallreflex bleibt von jeder Lernregel unabhängig. Programmcode, ein Prüfsummenvergleich und das Erkennen des eigenen Gerätezustands sind drei unterschiedliche Dinge. Eine beglaubigte Startkette und ein integriertes Betriebssystem sind Forschungsarbeit für spätere Stufen.

## Einstieg für Claude

> Lies START-HIER.md und diese Übergabe. Führe die Tests aus und gleiche die Kontrollwerte mit der beigefügten CSV ab. Kläre mit Alex einen eigenen Messendpunkt, eine mögliche Handlung innerhalb eines Takts und das Verhältnis der Kosten einer Fehlwarnung zu einem verpassten Ausfall. Halte Abtastintervall, Timeout und Schwach-Schwelle vor der Messung fest. Nimm zwei zeitlich getrennte Spuren auf. Verwende die erste zur Erkundung und die zweite für die Entscheidung mit eingefrorenen Einstellungen. Vergleiche alle sechs Verfahren, benenne konkrete Fehlentscheidungen mit Takt und vergleiche mit der einfachen festen Warnregel. Dokumentiere reale Ergebnisse getrennt von den synthetischen Kontrollen.

| Frage | Zuständige Dateien |
|---|---|
| Welche Erfahrung altert wann? | kern.py |
| Wie werden beobachtete Übergänge, Warnungen und Bytes gezählt? | versuch.py |
| Woher stammen Prüfbedingungen und Bericht? | labor.py, Bericht.html, beispiele/kontrollwerte.csv |
| Wie entstehen echte Messwerte? | messen.py, beispiele/loopback-roh.csv |
| Wie funktioniert die Gegenstelle bei Paketverlust? | transport.py |
| Wie bleibt ein Lernstand über zwei Läufe erhalten? | neustart.py, esp32/Lernknoten/Knoten.h |
| Wo liegen Gerätesketch und serieller Referenzvergleich? | esp32/Lernknoten/Lernknoten.ino, esp32/platformio.ini, boardprobe.py |
| Welche Nachweise sind automatisiert? | test_versuch.py, test_labor.py |

## Referenzlauf und Aussagegrenzen

```bash
python3 -B -m unittest -v
python3 versuch.py --spur beispiele/demo.csv --details
python3 labor.py --satz kontrolle --csv erneut.csv --bericht erneut.html
python3 transport.py
```

Der Kontrollsatz umfasst 120 Spuren mit insgesamt 57.600 Beobachtungen. Jede Spur wird jedem der sechs Verfahren in zeitlicher Reihenfolge vorgespielt. Vorhersagehorizont ist ein Takt. Bei einer Warnung ist der Folgezustand noch unbekannt. Der Entwicklungssatz nutzt Startwerte 0–19, der Kontrollsatz 1000–1019. Die Familien und Generatorannahmen sind gleich. Der zweite Satz prüft die Ergebnisse auf neuen Zufallsverläufen innerhalb dieser Annahmen. Er ersetzt die Feldmessung nicht. Jede Zeile der Ergebnis-CSV identifiziert Familie, Startwert und Verfahren. Für jedes Verfahren pro Familie sind die Zahlen im Bericht Summen über 20 Spuren.

Ein Warnsignal verlangt mindestens drei gewichtete Übergänge und mindestens 60 % Ausfallanteil. Die feste Vergleichsregel warnt bei jedem schwachen Signal. Das vergleichbare Lernen ohne Verblassen zählt alle Übergänge gleich. Die zeitbasierte Regel halbiert die Belege nach 24 logischen Takten, die Kontextregel nach sechs neuen Folgen desselben Ausgangszustands. Beide Zahlen sind Entwurfsentscheidungen. Für allgemeine Aussagen über Zeit- und Kontextalterung müssen auch andere Halbwertszeiten untersucht werden. Der aktuelle Kontext besteht aus genau einem Zustand. Ursachen, längere Muster und semantische Ähnlichkeit sind damit offen.

**Wie Alex eine Regel auswählen kann.** Bei einem Bedeutungswechsel kostet das zeitliche Verblassen im Kontrollsatz 44 zusätzliche verpasste Vorwarnungen gegenüber Lernen ohne Verblassen. Es spart 421 Fehlwarnungen. Wer ausschließlich diese beiden Kosten bewertet, erhält den Gleichstand bei rund 9,6 Fehlwarnungen pro verpasstem Ausfall. Liegt der tatsächliche Schaden einer verpassten Warnung höher, kippt die Wahl. Für die Praxis zählen zusätzlich die nutzbare Vorwarnzeit und die Kosten der Aktion.

## Eigene Daten gewinnen

Für eine lokale Funktionsprobe in einem ersten Terminal einen eigenen Testdienst starten. In einem zweiten Terminal die Aufnahme beginnen. Den Dienst während der Aufnahme beenden, um einen nachvollziehbaren Ausfall zu erzeugen.

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

```bash
python3 messen.py aufnahme roh-lauf1.csv --ip 127.0.0.1 --port 8765 --takte 60 --intervall-ms 1000 --timeout-ms 400
python3 messen.py spur roh-lauf1.csv --schwach-ms 100 > spur-lauf1.csv
python3 versuch.py --spur spur-lauf1.csv --details
```

Für einen Feldversuch die Adresse und den Port eines eigenen Testdienstes einsetzen. Pro geplantem Takt wird eine neue TCP-Verbindung aufgebaut und geschlossen. Beobachtet wird die Verbindungsannahme des Dienstes. Der fachliche Zustand eines Sensors oder die Dauer einer HTTP-Anfrage erfordern eine eigene Messdefinition. Bei Erfolg dient die gemessene Verbindungsdauer als Frühindikator. Ein Fehler oder Timeout im **nächsten** Takt liefert das spätere Zielereignis. Vor der Messung Schwelle kleiner als Timeout, Timeout kleiner als Intervall wählen. Beides in Millisekunden dokumentieren. Zusätzlich helfen ein unabhängiges Protokoll des abgeschalteten Dienstes und Zeitmarken für geplante Störungen.

Die Rohdatei erhält Takt, Startzeit seit Aufnahmebeginn, Verbindungsdauer und Ergebnis. Ein bestehender Dateiname wird abgelehnt. Lokale Berechtigungsfehler brechen die Aufnahme ab. Verpasste Zeitfenster bleiben Lücken. Der Import akzeptiert die bisherige einspaltige CSV für lückenlose Aufzeichnungen und das neue Format `takt,zustand`. Doppelte, rückläufige und übergroße Taktnummern werden abgewiesen. Nach einer Lücke wird der erste sichtbare Zustand erneut gemeldet. Eine davor offene Vorhersage erhält weder einen Treffer noch eine Fehlwarnung. Ein nach der Lücke erstmals beobachteter Ausfall zählt als Sofortmeldung mit unbekanntem Beginn.

**Beigefügter Gerätedatenersatz für den Messpfad.** In der realen Loopback-Probe wurde ein TCP-Listener nach sechs angenommenen Verbindungen geschlossen. Sechs weitere Verbindungen wurden abgelehnt. Abtastung 100 ms, Timeout 40 ms, Auswerteschwelle 20 ms. Beim Einlesen der Rohdatei entstehen sechs `OK` und sechs `AUSFALL`. Das prüft die Erfassung eines anhaltenden Ausfalls. Für die Güte der Vorhersage enthält diese kurze Spur zu wenige Ereignisse.

## Lernstand auf dem Rechner fortsetzen

Die folgenden Befehle teilen die mitgelieferte Demo nach Takt 120. In einem frischen Arbeitsordner mit den Projektdateien ausführen. `stand120.json` bleibt als eigener Wiederanlaufpunkt erhalten.

```bash
head -n 121 beispiele/demo.csv > teil1.csv
{ head -n 1 beispiele/demo.csv; tail -n +122 beispiele/demo.csv; } > teil2.csv
python3 neustart.py teil1.csv --quelle demo-v1 --regel kontext --sichern stand120.json > vorher.csv
python3 neustart.py teil2.csv --quelle demo-v1 --laden stand120.json > nachher.csv
```

Der versionierte JSON-Stand enthält Messreihenkennung, letzten Takt und Zustand, Regel, Halbwertszeit, Vokabular und neun Gewichte. Eine SHA-256-Prüfsumme erkennt Veränderungen. Beim Laden werden Format, Quelle, Wertebereiche und Version geprüft. Gesichert wird zunächst in einer temporären Datei im Zielverzeichnis. Nach dem Schreiben wird sie unter dem neuen Namen veröffentlicht. Das lokale Dateisystem muss Hardlinks unterstützen. Ein vorhandener Stand wird nicht überschrieben. Die Tests vergleichen jede Entscheidung nach dem Neustart mit dem ungeteilten Lauf. Für reale Auszeiten muss die Taktnummer die verstrichene Zeit abbilden. Autorisierung, Verschlüsselung und ein Schutz gegen absichtlich zurückgespielte ältere Stände gehören zu einem späteren Produkt für persönliche Daten.

## Gerätestand und Prüfweg

Der Sketch akzeptiert über die serielle Schnittstelle Zeilen wie `34,SCHWACH`. Die Antwort enthält Takt, Zustand, Sofortmeldung und Vorwarnung. Jede Zeile endet mit LF oder CRLF. Ein Wiederholungstakt, ein unbekanntes Token oder eine überlange Zeile ergibt `FEHLER` und verändert das Gedächtnis nicht. Das lesbare Replay-Protokoll ist vom modellierten Fünf-Byte-Statuspaket getrennt. Es dient der Prüfung auf dem Tisch. [Espressif-Dokumentation zur seriellen Schnittstelle](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html)

Mit PlatformIO 6.1.18, Plattform espressif32 6.12.0 und dem Profil für den klassischen ESP32 Dev Module wurden beide Firmwareabbilder übersetzt. Das Profil ist eine Referenzwahl. Für Alex’ konkretes Board zuerst die genaue Chipfamilie, Flashgröße, Boardkennung und den seriellen Port bestimmen. [Boardprofil des Referenzgeräts](https://docs.platformio.org/en/latest/boards/espressif32/esp32dev.html)

```bash
pio run -d esp32
```

| Gebaute Variante | Vom Linker gemeldete RAM-Belegung | Vom Build gemeldeter Flashbedarf |
|---|---:|---:|
| esp32dev · Zeit | 21.668 Byte | 282.505 Byte |
| esp32dev-kontext · Kontext | 21.668 Byte | 282.521 Byte |

Die Zahlen umfassen das Arduino-Programm samt Framework. Die neun Gewichte allein belegen 72 Byte. Die Laufzeit pro Takt, Stromaufnahme und tatsächlich beanspruchte Flashzyklen sind am Gerät zu messen. Der Hosttest führt je Variante den identischen Sketch auf der Demo und allen 120 Kontrollspuren aus. Alle 57.840 Antworten pro Variante stimmen bei Takt, Zustand, Sofortmeldung und Vorwarnung mit Python überein.

**Erster Boardlauf.** Nach dem Aufspielen der zum Gerät passenden Variante den seriellen Monitor schließen und mit einem Python-Interpreter mit `pyserial` den Prüfer starten. Den Beispielport durch den tatsächlichen Port ersetzen. Der Prüfer startet bewusst einen leeren RAM-Lauf, sendet eine Zeile, wartet auf die Antwort und vergleicht jede Entscheidung. Erwartet werden 240 von 240 passende Antworten.

```bash
python3 boardprobe.py --port /dev/PORT --regel zeit
```

**Neustart auf dem Board.** `SICHERN` legt den aktuellen Stand im NVS-Namensraum `alex-lernlabor` ab. Zeit- und Kontextregel nutzen getrennte Schlüssel. Nur dieser explizite Befehl schreibt den Lernstand. Bereits identische Nutzdaten werden erkannt. `NEUER_LAUF` setzt das RAM zurück. `LADEN` übernimmt einen gültigen Stand in einen leeren Knoten. Das binäre Format hat genau 86 Byte. Es enthält die Kennung `AG01`, Regel und Zustand als je ein Byte, den Takt als uint32, neun binary64-Gewichte in Zeilenfolge OK/SCHWACH/AUSFALL und eine CRC32 über die ersten 82 Byte. Mehrbyte-Werte werden in Little Endian gespeichert. Die Prüfung erkennt Beschädigungen und verweigert ungültige Werte. Sie authentifiziert keinen Absender. [Espressif-Dokumentation zu Preferences und NVS](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/preferences.html)

Für den physischen Wiederanlauftest die erste Hälfte der Demo über den seriellen Monitor oder eine Aufnahmesoftware senden, `SICHERN` bestätigen lassen, trennen und wieder einschalten. Dann `LADEN` senden und mit Takt 121 fortfahren. Die Antworten müssen denen des durchgängigen Laufs entsprechen. Der automatische Komplettprüfer beginnt immer mit einem frischen RAM-Zustand. Im Hosttest wurde der Neustart über zwei getrennte Prozesse und ein Dateibackend geprüft. Stromtrennung am echten ESP32 und der Zustand nach einem Abbruch **während** des Schreibens stehen noch aus.

## Kommunikationsversuch und nächste Entscheidung

`transport.py` spielt einem Sender und einem Empfänger dieselbe logische Uhr vor. Ein Statuspaket besteht aus vier Byte Takt in Big Endian und einem Byte Zustand. OK, SCHWACH und AUSFALL haben die IDs 1–3, Vorwarnung die ID 4. Der Zustandskanal akzeptiert nur die ersten drei. Doppelte, verspätete oder zukünftige Pakete verändern den Empfängerstand nicht. Der Versuch verwendet eine bekannte Sitzung mit genau einem Sender. Bei realen Neustarts und mehreren Knoten muss die Gegenstelle Sender und Sitzungen unterscheiden, bevor sie Sequenznummern vergleichen kann.

Der Herzschlag trägt den aktuellen Zustand. Nach zehn Takten ohne gültige Meldung wird er beim Empfänger unbekannt. Protokolliert werden gesendete Nutzbytes, empfangene Pakete, falsche und unbekannte Takte sowie der erste tatsächlich sichtbare Ausfall. Vorwarnungen werden in diesem Teilversuch nicht übertragen. Bei Totalausfall der Leitung kann ein Empfänger die Ursache der Stille nicht feststellen. Ein zweiter Meldeweg oder ein später auslesbares lokales Ereignisprotokoll wäre dafür ein eigener, messbarer Versuch.

**Abnahme der nächsten Etappe.** Ein physischer Knoten soll die Referenzspur und den Wiederanlauftest bestehen. Auf einer getrennten Feldaufzeichnung sollen Alex und Claude danach die Zahl nützlicher Vorwarnungen, Fehlwarnungen, verpasster Ausfälle, offene Warnungen und die tatsächlich verfügbare Reaktionszeit berichten. Erst mit dieser Messung lässt sich entscheiden, welche Gedächtnisregel und welcher Meldetakt in Alex’ Alltag sinnvoll sind.
