# Übergabe an Alex und Claude

**Version 0.4 · Stand 5. November 2026**

Alex’ Fernziel ist ein lokales System, dessen Gedächtnis die Arbeit vorhandener Geräte mitsteuert. Im Labor kann man den ersten Mechanismus isoliert untersuchen. Eine erlernte Vorhersage verändert die ausgehenden Meldungen. Der feste Ausfallreflex bleibt von jeder Lernregel unabhängig. Programmcode, ein Prüfsummenvergleich und das Erkennen des eigenen Gerätezustands sind drei unterschiedliche Dinge. Eine beglaubigte Startkette und ein integriertes Betriebssystem sind Forschungsarbeit für spätere Stufen.

## Einstieg für Claude

> Lies START-HIER.md, diese Übergabe und den Abschnitt „Versuchsstand“ in Alex’ Ideensammlung eine Ebene höher. Führe die Tests aus und gleiche die Kontrollwerte mit der beigefügten CSV ab. Kläre mit Alex einen eigenen Messendpunkt, eine mögliche Handlung innerhalb eines Takts und das Verhältnis der Kosten einer Fehlwarnung zu einem verpassten Ausfall. Halte Abtastintervall, Timeout und Schwach-Schwelle vor der Messung fest. Nimm zwei zeitlich getrennte Spuren auf. Verwende die erste zur Erkundung und die zweite für die Entscheidung mit eingefrorenen Einstellungen. Vergleiche alle sieben Verfahren, benenne konkrete Fehlentscheidungen mit Takt und vergleiche mit der einfachen festen Warnregel. Dokumentiere reale Ergebnisse getrennt von den synthetischen Kontrollen.

| Frage | Zuständige Dateien |
|---|---|
| Wo steht das Konzept, und was ist davon geprüft? | ../Ideensammlung Lernendes Betriebssystem mit verblassendem Gedächtnis.md |
| Welche Erfahrung altert wann? | kern.py |
| Wie wirkt festes Vorwissen (Erbe)? | kern.py, labor.py --erbe-reihe |
| Wie werden beobachtete Übergänge, Warnungen und Bytes gezählt? | versuch.py |
| Woher stammen Prüfbedingungen und Bericht? | labor.py, Bericht.html, beispiele/kontrollwerte.csv |
| Wie entstehen echte Messwerte? | messen.py, beispiele/loopback-roh.csv |
| Wie funktioniert die Gegenstelle bei Paketverlust? | transport.py |
| Wie bleibt ein Lernstand über zwei Läufe erhalten? | neustart.py, esp32/Lernknoten/Knoten.h |
| Wo liegen Gerätesketch und serieller Referenzvergleich? | esp32/Lernknoten/Lernknoten.ino, esp32/platformio.ini, boardprobe.py, wiederanlauf.py |
| Wie nimmt der Knoten seinen eigenen Zustand wahr? | esp32/Lernknoten/Koerper.h, koerper.py |
| Welche Nachweise sind automatisiert? | test_versuch.py, test_labor.py |

## Referenzlauf und Aussagegrenzen

```bash
python3 -B -m unittest -v
python3 versuch.py --spur beispiele/demo.csv --details
python3 labor.py --satz kontrolle --csv erneut.csv --bericht erneut.html
python3 labor.py --satz entwicklung --erbe-reihe --halbwertszeiten
python3 transport.py
```

Der Kontrollsatz umfasst 120 Spuren mit insgesamt 57.600 Beobachtungen. Jede Spur wird jedem der sieben Verfahren in zeitlicher Reihenfolge vorgespielt. Vorhersagehorizont ist ein Takt. Bei einer Warnung ist der Folgezustand noch unbekannt. Der Entwicklungssatz nutzt Startwerte 0–19, der Kontrollsatz 1000–1019. Die Familien und Generatorannahmen sind gleich. Der zweite Satz prüft die Ergebnisse auf neuen Zufallsverläufen innerhalb dieser Annahmen. Er ersetzt die Feldmessung nicht. Jede Zeile der Ergebnis-CSV identifiziert Familie, Startwert und Verfahren. Für jedes Verfahren pro Familie sind die Zahlen im Bericht Summen über 20 Spuren.

Ein Warnsignal verlangt mindestens drei gewichtete Übergänge und mindestens 60 % Ausfallanteil. Die feste Vergleichsregel warnt bei jedem schwachen Signal. Das vergleichbare Lernen ohne Verblassen zählt alle Übergänge gleich. Die zeitbasierte Regel halbiert die Belege nach 24 logischen Takten, die Kontextregel nach sechs neuen Folgen desselben Ausgangszustands. Beide Zahlen sind Entwurfsentscheidungen. Für allgemeine Aussagen über Zeit- und Kontextalterung müssen auch andere Halbwertszeiten untersucht werden. Seit 0.3 vergleicht `python3 labor.py --halbwertszeiten` Zeitregeln mit 12 bis 192 Takten und Kontextregeln mit 3 bis 24 Folgen. Bei seltenem Vorzeichen holt die Zeitregel erst bei sehr langen Halbwertszeiten auf (Kontrollsatz: keine richtige Vorwarnung bis 24 Takte, 83 bei 192). Die Kontextregel liegt durchweg bei 82 bis 95. Der aktuelle Kontext besteht aus genau einem Zustand. Ursachen, längere Muster und semantische Ähnlichkeit sind damit offen.

**Erbe und Kontext.** Das siebte Verfahren nutzt die Kontextregel und rechnet zusätzlich mit drei festen Beobachtungen „SCHWACH → AUSFALL“. Sie liegen in einer eigenen Tabelle, verblassen nie und werden durch Beobachtung nicht verändert. Weil Erbe und Erfahrung getrennt liegen, ist die Herkunft jedes Belegs bekannt. Das Erbe steht für Wissen von außen, etwa von Alex oder einem Sprachmodell. Die Zahl drei ist der Mindestbeleg der Warnregel und wurde nicht an Messwerte angepasst. Die erste Gegenprobe am 5. November lief allerdings auf dem Kontrollsatz. Der Entwicklungssatz zeigt dasselbe Bild: bei seltenem Vorzeichen 202 richtige Vorwarnungen wie bei der festen Regel, bei stabilem 1844 statt 1845. `--erbe-reihe` vergleicht null bis zwölf feste Beobachtungen auf dem gewählten Satz. Sketch, serieller Prüfer und Neustart kennen alle drei Lernregeln. Ihre Namen stehen an einer Stelle, `REGELN` in kern.py. Der Sketch bildet die Summen in derselben Reihenfolge wie Python und entscheidet deshalb bitgleich. Als Gegenprobe wurde das Erbe im Sketch probehalber auf zwei gesetzt. Der Paritätstest schlug daraufhin beim ersten schwachen Signal an.

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

Der versionierte JSON-Stand enthält Messreihenkennung, letzten Takt und Zustand, Regel, Halbwertszeit, Erbe, Vokabular und neun Gewichte. Halbwertszeit und Erbe müssen beim Laden zur Regelversion passen. Stände aus 0.2 tragen kein Erbe und bleiben ladbar. Mit `--regel erbe` beginnt ein neuer Lauf mit Erbe. Eine SHA-256-Prüfsumme erkennt Veränderungen. Beim Laden werden Format, Quelle, Wertebereiche und Version geprüft. Gesichert wird zunächst in einer temporären Datei im Zielverzeichnis. Nach dem Schreiben wird sie unter dem neuen Namen veröffentlicht. Das lokale Dateisystem muss Hardlinks unterstützen. Ein vorhandener Stand wird nicht überschrieben. Die Tests vergleichen jede Entscheidung nach dem Neustart mit dem ungeteilten Lauf. Für reale Auszeiten muss die Taktnummer die verstrichene Zeit abbilden. Autorisierung, Verschlüsselung und ein Schutz gegen absichtlich zurückgespielte ältere Stände gehören zu einem späteren Produkt für persönliche Daten.

## Gerätestand und Prüfweg

Der Sketch akzeptiert über die serielle Schnittstelle Zeilen wie `34,SCHWACH`. Die Antwort enthält Takt, Zustand, Sofortmeldung und Vorwarnung. Jede Zeile endet mit LF oder CRLF. Ein Wiederholungstakt, ein unbekanntes Token oder eine überlange Zeile ergibt `FEHLER` und verändert das Gedächtnis nicht. Das lesbare Replay-Protokoll ist vom modellierten Fünf-Byte-Statuspaket getrennt. Es dient der Prüfung auf dem Tisch. [Espressif-Dokumentation zur seriellen Schnittstelle](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html)

Mit PlatformIO 6.1.18, Plattform espressif32 6.12.0 und dem Profil für den klassischen ESP32 Dev Module wurden alle drei Firmwareabbilder übersetzt. Das Profil ist eine Referenzwahl. Für Alex’ konkretes Board zuerst die genaue Chipfamilie, Flashgröße, Boardkennung und den seriellen Port bestimmen. [Boardprofil des Referenzgeräts](https://docs.platformio.org/en/latest/boards/espressif32/esp32dev.html)

Seit 0.3 gibt es dieselben drei Varianten für Alex’ ESP32-S3-N16R8 (UICPAL, DevKitC-1-Klon): `esp32s3`, `esp32s3-kontext` und `esp32s3-erbe`. Die Speicherwerte stammen aus Alex’ Projekt `esp32-s3-audio`: Oktal-PSRAM (`qio_opi`), 16 MB Flash und die Tabelle `default_16MB.csv`. `Serial` ist UART0 am COM-Anschluss mit der CH343-Brücke, deshalb gilt `ARDUINO_USB_CDC_ON_BOOT=0`. Dort setzt das Öffnen des Ports das Board zurück wie beim klassischen ESP32, und der Prüfer rechnet damit. Am nativen USB-Anschluss müsste `ARDUINO_USB_CDC_ON_BOOT=1` gesetzt werden. Das ist nicht geprüft.

```bash
pio run -d esp32
```

| Gebaute Variante | Vom Linker gemeldete RAM-Belegung | Vom Build gemeldeter Flashbedarf |
|---|---:|---:|
| esp32dev · Zeit | 21.740 Byte | 282.625 Byte |
| esp32dev-kontext · Kontext | 21.740 Byte | 282.625 Byte |
| esp32dev-erbe · Erbe und Kontext | 21.740 Byte | 282.633 Byte |
| esp32s3 · Zeit | 18.872 Byte | 282.337 Byte |
| esp32s3-kontext · Kontext | 18.872 Byte | 282.337 Byte |
| esp32s3-erbe · Erbe und Kontext | 18.872 Byte | 282.345 Byte |

Gemessen am 5. November auf Alex’ Mac. Die Zahlen umfassen das Arduino-Programm samt Framework. Die neun Gewichte und die Erbtabelle belegen je 72 Byte. In 0.2 lag die RAM-Belegung ohne Erbtabelle bei 21.668 Byte. Die Laufzeit pro Takt, Stromaufnahme und tatsächlich beanspruchte Flashzyklen sind am Gerät zu messen. Der Hosttest führt je Variante den identischen Sketch auf der Demo und allen 120 Kontrollspuren aus. Alle 57.840 Antworten pro Variante stimmen bei Takt, Zustand, Sofortmeldung und Vorwarnung mit Python überein.

**Erster Boardlauf.** Nach dem Aufspielen der zum Gerät passenden Variante den seriellen Monitor schließen und mit einem Python-Interpreter mit `pyserial` den Prüfer starten. Den Beispielport durch den tatsächlichen Port ersetzen. Der Prüfer startet bewusst einen leeren RAM-Lauf, sendet eine Zeile, wartet auf die Antwort und vergleicht jede Entscheidung. Erwartet werden 240 von 240 passende Antworten. Startet das Board langsam, sendet der Prüfer `NEUER_LAUF` mehrmals, und jede Wiederholung wird beantwortet. Seit 0.3 überspringt er diese späten Bereitmeldungen vor der ersten Antwort. Vorher schlug der Hosttest gelegentlich beim ersten Start frisch übersetzter Programme fehl.

```bash
python3 boardprobe.py --port /dev/PORT --regel zeit
```

**Erster Boardlauf auf dem S3.** Geprüft wurde ein UICPAL-S3, ein ESP32-S3-N16R8 auf einem DevKitC-1-Klon mit zwei USB-C-Anschlüssen. Das Kabel gehört an den COM-Anschluss. Dort trägt der Port die Seriennummer der CH343-Brücke im Namen (`/dev/cu.usbmodem…`) und bleibt beim Umstecken gleich. Am nativen Anschluss erscheint dasselbe Board mit wechselnder Nummer und meldet die MAC als Seriennummer. In den Befehlen steht `/dev/PORT` für den COM-Port. Vor dem ersten Aufspielen bestätigt `esptool.py … flash_id` Chip, Flashgröße und PSRAM, ohne etwas zu schreiben. Danach je Variante aufspielen und prüfen:

```bash
pio run -d esp32 -e esp32s3-erbe -t upload --upload-port /dev/PORT
python3 boardprobe.py --port /dev/PORT --regel erbe
```

**Ergebnis am 5. November.** esptool bestätigte einen ESP32-S3 (QFN56) Revision v0.2 mit 16 MB Flash, 8 MB eingebettetem PSRAM und der erwarteten MAC. Aufgespielt wurde mit 230400 Baud, Bootloader, Partitionstabelle, otadata und App jeweils mit bestätigtem Hash. Zeit, Kontext und Erbe bestanden die Demo mit je 240 von 240 Antworten. Die Gegenprobe mit falscher `--regel` brach wie vorgesehen mit „Falsche Variante“ ab. Auf dem Board läuft seitdem `esp32s3-erbe`. Geprüft ist damit die Demo, die 120 Kontrollspuren liefen nur im Hosttest. Auch der Wiederanlauf nach Stromtrennung bestand. Die Erbe-Variante sicherte nach 99 Takten, war 5 s ohne Strom und lud danach ihren Stand. Takt 99 wurde abgewiesen, Takt 100 angenommen, und die übrigen 141 Antworten entsprachen dem durchgehenden Lauf. Ein erster Versuch war beim Sichern abgebrochen, ohne dass sichtbar wurde, was statt `GESICHERT` ankam. Vermutlich brauchte der erste Flashzugriff nach dem Aufspielen länger als die 0,6 s Lesefrist. Belegt ist das nicht. Seitdem wartet `wiederanlauf.py` bis zu 3 s und nennt im Fehlerfall die erhaltene Zeile.

**Neustart auf dem Board.** `SICHERN` legt den aktuellen Stand im NVS-Namensraum `alex-lernlabor` ab. Jede Regel hat ihren eigenen Schlüssel: `zeit`, `kontext` und `erbe`. Nur dieser explizite Befehl schreibt den Lernstand. Bereits identische Nutzdaten werden erkannt. `NEUER_LAUF` setzt das RAM zurück. `LADEN` übernimmt einen gültigen Stand in einen leeren Knoten. Das binäre Format hat genau 86 Byte. Es enthält die Kennung `AG01`, Regel (1 Zeit, 2 Kontext, 3 Erbe) und Zustand als je ein Byte, den Takt als uint32, neun binary64-Gewichte in Zeilenfolge OK/SCHWACH/AUSFALL und eine CRC32 über die ersten 82 Byte. Mehrbyte-Werte werden in Little Endian gespeichert. Die Prüfung erkennt Beschädigungen und verweigert ungültige Werte. Sie authentifiziert keinen Absender. Das Erbe steht nicht im Stand, es gehört zur Firmware. Einen Stand einer anderen Regel weist `LADEN` ab. [Espressif-Dokumentation zu Preferences und NVS](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/preferences.html)

Für den physischen Wiederanlauftest gibt es seit 0.3 `wiederanlauf.py`. `sichern` spielt einen zufällig langen Anfang der Demo ein, vergleicht jede Antwort und lässt den Stand sichern. Danach das Board vom Strom trennen und wieder einschalten. `laden` lädt den Stand und sendet den Grenztakt noch einmal. Das Gerät muss ihn abweisen und den nächsten Takt annehmen, erst dann endet der Stand genau an der Grenze. Den Rest vergleicht es mit dem durchgehenden Lauf. Der zufällige Grenztakt sorgt dafür, dass ein älterer Stand im NVS nicht als Erfolg durchgeht.

```bash
python3 wiederanlauf.py sichern --port /dev/PORT --regel erbe
python3 wiederanlauf.py laden --port /dev/PORT --regel erbe --grenze N
```

Der Hosttest spielt beide Teile in zwei getrennten Prozessen mit Dateibackend durch, auch mit falscher Grenze. Der Zustand nach einem Abbruch **während** des Schreibens steht noch aus.

## Körpersignale

Seit 0.4 misst sich der Knoten auf Wunsch selbst. Im Körpermodus liest er in eigenem Takt die Chiptemperatur, den freien internen Speicher und die größte Lücke zwischen zwei Durchläufen von `loop()` seit dem letzten Takt. Die eigene Messung und Ausgabe zählen dabei mit. Daraus stuft er den Takt als OK, SCHWACH oder AUSFALL ein, der schlechteste der drei Werte zählt. Mit dieser Einstufung lernt er wie im Replay. Eine nicht lesbare Temperatur steht als „-“ in der Ausgabe und zählt nicht mit.

Die Firmware hat keine eigenen Grenzwerte. `GRENZEN` übergibt sie in Zehntelgrad, Byte und Mikrosekunden, `KOERPER <ms>` startet den Modus, `STOP` beendet ihn. Jeder Takt antwortet mit `K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us`. `MESSWERT` speist Rohwerte von außen ein und nimmt denselben Weg durch Einstufung und Lernen. Darüber vergleicht der Hosttest beides mit Python.

```bash
python3 koerper.py aufnahme messungen/koerper.csv --port /dev/PORT --regel erbe --takte 3600
python3 koerper.py pruefen messungen/koerper.csv
python3 koerper.py spur messungen/koerper.csv --grenzen 450 550 65536 16384 20000 200000 > spur.csv
```

`aufnahme` schreibt neben die CSV eine JSON mit Regel, Intervall und Grenzen. `pruefen` rechnet jede Einstufung und jede Entscheidung des Geräts nach und fasst die Werte zusammen. `spur` stuft die Rohwerte wahlweise mit anderen Grenzen neu ein, als Eingabe für `versuch.py`. Die Grenzen der ersten Aufnahme (`ERKUNDUNG` in koerper.py: 50 und 60 °C, 64 und 16 KiB frei, 20 und 200 ms Lücke) sind vorläufige Erkundungswerte ohne Datenblattbezug. Eigene Aufnahmen liegen in `messungen/`, das nicht ins Repo geht.

**Erster Lauf am 5. November.** 30 Takte à 1 s auf dem ESP32-S3:
- Chiptemperatur 35 bis 38 °C in ganzen Grad, direkt nach dem Aufspielen fallend
- freier Speicher konstant 371.820 Byte
- Schleifenlücke meist 209 µs, höchstens 655 µs

Alle Takte waren OK, keine Vorwarnung, und alle Einstufungen und Entscheidungen stimmten mit Python überein. Wie erwartet lernt der Knoten auf dem Tisch nur, dass auf OK wieder OK folgt. Am selben Tag begann ein Mitschnitt über 12 Stunden.

## Kommunikationsversuch und nächste Entscheidung

`transport.py` spielt einem Sender und einem Empfänger dieselbe logische Uhr vor. Ein Statuspaket besteht aus vier Byte Takt in Big Endian und einem Byte Zustand. OK, SCHWACH und AUSFALL haben die IDs 1–3, Vorwarnung die ID 4. Der Zustandskanal akzeptiert nur die ersten drei. Doppelte, verspätete oder zukünftige Pakete verändern den Empfängerstand nicht. Der Versuch verwendet eine bekannte Sitzung mit genau einem Sender. Bei realen Neustarts und mehreren Knoten muss die Gegenstelle Sender und Sitzungen unterscheiden, bevor sie Sequenznummern vergleichen kann.

Der Herzschlag trägt den aktuellen Zustand. Nach zehn Takten ohne gültige Meldung wird er beim Empfänger unbekannt. Protokolliert werden gesendete Nutzbytes, empfangene Pakete, falsche und unbekannte Takte sowie der erste tatsächlich sichtbare Ausfall. Vorwarnungen werden in diesem Teilversuch nicht übertragen. Bei Totalausfall der Leitung kann ein Empfänger die Ursache der Stille nicht feststellen. Ein zweiter Meldeweg oder ein später auslesbares lokales Ereignisprotokoll wäre dafür ein eigener, messbarer Versuch.

**Abnahme der nächsten Etappe.** Ein physischer Knoten soll die Referenzspur und den Wiederanlauftest bestehen. Die Referenzspur hat Alex’ ESP32-S3 am 5. November in allen drei Varianten bestanden, den Wiederanlauf nach Stromtrennung in der Erbe-Variante. Auf einer getrennten Feldaufzeichnung sollen Alex und Claude danach die Zahl nützlicher Vorwarnungen, Fehlwarnungen, verpasster Ausfälle, offene Warnungen und die tatsächlich verfügbare Reaktionszeit berichten. Erst mit dieser Messung lässt sich entscheiden, welche Gedächtnisregel und welcher Meldetakt in Alex’ Alltag sinnvoll sind.

**Offene Grundsatzfrage.** Laut Ideensammlung steigt die Stärke einer Erinnerung bei jedem Abruf. Hier verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel. `test_abrufen_verstaerkt_keine_vermutung` sichert das ab. Ein möglicher Ausgleich wären zwei Werte pro Eintrag: ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf. Die Entscheidung liegt bei Alex. Vor einem zweiten echten Knoten braucht das Fünf-Byte-Paket außerdem eine Sender- und Sitzungskennung.
