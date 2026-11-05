# Übergabe an Alex und Claude

**Version 0.5 · Stand 5. November 2026**

Alex’ Fernziel ist ein lokales System, dessen Gedächtnis die Arbeit vorhandener Geräte mitsteuert. Im Labor kann man den ersten Mechanismus isoliert untersuchen. Eine erlernte Vorhersage verändert die ausgehenden Meldungen. Der feste Ausfallreflex bleibt von jeder Lernregel unabhängig. Programmcode, ein Prüfsummenvergleich und das Erkennen des eigenen Gerätezustands sind drei unterschiedliche Dinge. Eine beglaubigte Startkette und ein integriertes Betriebssystem sind Forschungsarbeit für spätere Stufen.

## Einstieg für Claude

> Lies START-HIER.md, diese Übergabe und den Abschnitt „Versuchsstand“ in Alex’ Ideensammlung eine Ebene höher, für Daniels Teilversuche zusätzlich SYSTEM-UEBERGABE.md und VERBUND-UEBERGABE.md. Führe die Tests aus und gleiche die Kontrollwerte mit der beigefügten CSV ab. Kläre mit Alex einen eigenen Messendpunkt, eine mögliche Handlung innerhalb eines Takts und das Verhältnis der Kosten einer Fehlwarnung zu einem verpassten Ausfall. Halte Abtastintervall, Timeout und Schwach-Schwelle vor der Messung fest. Nimm zwei zeitlich getrennte Spuren auf. Verwende die erste zur Erkundung und die zweite für die Entscheidung mit eingefrorenen Einstellungen. Vergleiche alle sieben Verfahren, benenne konkrete Fehlentscheidungen mit Takt und vergleiche mit der einfachen festen Warnregel. Dokumentiere reale Ergebnisse getrennt von den synthetischen Kontrollen.

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
| Welche Wörter kennt er, und wie weit blickt er voraus? | vokabular.py |
| Wie erkennt eine Zentrale Absender, Sitzung und veraltete Meldungen? | verbund.py, verbundlabor.py, VERBUND-UEBERGABE.md (Daniel) |
| Wie wird aus einer Vorwarnung eine Handlung? | systemkern.py, systemlabor.py, SYSTEM-UEBERGABE.md (Daniel) |
| Welche Nachweise sind automatisiert? | test_versuch.py, test_labor.py, test_verbund.py, test_system.py |

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

Seit 0.3 gibt es dieselben drei Varianten für Alex’ ESP32-S3-N16R8 (UICPAL, DevKitC-1-Klon): `esp32s3`, `esp32s3-kontext` und `esp32s3-erbe`. Die Speicherwerte stammen aus Alex’ Projekt `esp32-s3-audio`: Oktal-PSRAM (`qio_opi`), 16 MB Flash und die Tabelle `default_16MB.csv`. `Serial` ist UART0 am COM-Anschluss mit der CH343-Brücke, deshalb gilt `ARDUINO_USB_CDC_ON_BOOT=0`. Dort kann das Öffnen des Ports das Board zurücksetzen wie beim klassischen ESP32, muss es aber nicht. Am Abend des 5. November tat es das nicht. Der Prüfer kommt mit beidem zurecht. Am nativen USB-Anschluss müsste `ARDUINO_USB_CDC_ON_BOOT=1` gesetzt werden. Das ist nicht geprüft.

```bash
pio run -d esp32
```

| Gebaute Variante | Vom Linker gemeldete RAM-Belegung | Vom Build gemeldeter Flashbedarf |
|---|---:|---:|
| esp32dev · Zeit | 23.956 Byte | 287.677 Byte |
| esp32dev-kontext · Kontext | 23.956 Byte | 287.677 Byte |
| esp32dev-erbe · Erbe und Kontext | 23.956 Byte | 287.689 Byte |
| esp32s3 · Zeit | 21.584 Byte | 300.277 Byte |
| esp32s3-kontext · Kontext | 21.584 Byte | 300.277 Byte |
| esp32s3-erbe · Erbe und Kontext | 21.584 Byte | 300.285 Byte |

Gebaut am 5. November mit Stand 0.5 auf Alex’ Mac. Die Zahlen umfassen das Arduino-Programm samt Framework. Die neun Gewichte und die Erbtabelle belegen je 72 Byte, die Tabelle für die Blöcke des Lecks 2.048 Byte. In 0.3, vor Körpermodus und Reizen, lag die RAM-Belegung beim S3 bei 18.872 Byte. Die Rechenzeit des weiten Blicks ist am Gerät gemessen (siehe „Weiter Blick im Gerät“), Stromaufnahme und tatsächlich beanspruchte Flashzyklen noch nicht. Der Hosttest führt je Variante den identischen Sketch auf der Demo und allen 120 Kontrollspuren aus. Alle 57.840 Antworten pro Variante stimmen bei Takt, Zustand, Sofortmeldung und Vorwarnung mit Python überein.

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

Seit 0.4 misst sich der Knoten auf Wunsch selbst. Im Körpermodus liest er in eigenem Takt die Chiptemperatur, den freien internen Speicher und die größte Lücke zwischen zwei Durchläufen von `loop()` seit dem letzten Takt. Durchläufe mit eigener Arbeit, also Messung, Ausgabe und LED, zählen dabei nicht mit, gemessen wird nur fremde Wartezeit. Daraus stuft er den Takt als OK, SCHWACH oder AUSFALL ein, der schlechteste der drei Werte zählt. Mit dieser Einstufung lernt er wie im Replay. Eine nicht lesbare Temperatur steht als „-“ in der Ausgabe und zählt nicht mit.

Die Firmware hat keine eigenen Grenzwerte. `GRENZEN` übergibt sie in Zehntelgrad, Byte und Mikrosekunden, `KOERPER <ms>` startet den Modus, `STOP` beendet ihn. Jeder Takt antwortet mit `K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us,reiz`. Das letzte Feld hält in Bits fest, welche Reize gerade wirken: 1 Last, 2 Leck, 4 Bremse. Bis 0.4 hieß es `last` und kannte nur die Last, solche Aufnahmen bleiben lesbar. `MESSWERT` speist Rohwerte von außen ein und nimmt denselben Weg durch Einstufung und Lernen. Darüber vergleicht der Hosttest beides mit Python.

**Neustarts sichtbar machen.** Beim Start meldet die Firmware `NEUSTART,<nummer>,<grund>`, mit dem Grund aus `esp_reset_reason()`, etwa `PANIK`, `TASK_WACHHUND` oder `UNTERSPANNUNG`. Ein Puls auf der EN-Leitung, wie ihn die USB-Brücke gibt, sieht für den Chip aus wie echtes Einschalten: Das ROM schreibt `rst:0x1 (POWERON)`, die Firmware `NEUSTART,1,EINSCHALTEN`. Kommt während einer Aufnahme statt einer Körperzeile etwas anderes, hebt `aufnahme` diese Zeile und alles danach in `<name>.abbruch.txt` auf. Die Fehlermeldung nennt die Zeilen `rst:` und `NEUSTART,`. Geprüft ist das am S3 mit einem EN-Puls aus einem zweiten Prozess mitten in einer Aufnahme. Ein fremder Prozess am Port kann das Board also während einer Aufnahme zurücksetzen.

**Eine Veränderung mitgeben.** `LAST <an_s> <aus_s>` lässt Kern 0 im vorgegebenen Rhythmus arbeiten und ruhen, die Hauptschleife läuft auf Kern 1. Die Arbeit gibt alle 10 ms kurz ab, damit der Task-Wachhund nicht anschlägt und keine Meldung ins Protokoll schreibt. `LAST 0 0`, `STOP` und `NEUER_LAUF` beenden die Last. Die Einstufung kennt die Phase nicht, der Knoten spürt die Last allein über seine Messwerte.

**Speicher und Schleife reizen (seit 0.5).** Damit auch die Wörter für Speicher und Schleife Erfahrungen bekommen, gibt es zwei weitere Reize. Beide wirken im Takt des Körpers, ihr Ablauf steht in `Reize.h` und wird am Rechner geprüft:
- `LECK <byte> <boden> <halten> <pause>` belegt je Takt einen Block internen Speichers, bis kein Block mehr über den Boden passt. Dann bleibt es `halten` Takte am Boden, gibt alles frei und wächst nach `pause` Takten wieder. Blöcke von 1 bis 64 KiB. Der Boden liegt bei mindestens 8 KiB, das ist eine gewählte Reserve für Ausgabe, LED und Lastaufgabe, noch keine gemessene.
- `BREMSE <start> <schritt> <bis> <halten> <pause>` hält die Hauptschleife je Takt einmal an: `start`, `start + schritt` und so weiter bis `bis` Millisekunden, dann `halten` Takte bei `bis` und `pause` Takte gar nicht. Höchstens 900 ms, damit bei 1 s Takt kein Takt ausfällt. Der Stillstand zählt als fremde Wartezeit und erscheint im nächsten Takt als Lücke.

`LECK 0 0 0 0` und `BREMSE 0 0 0 0 0` beenden einen Reiz, `STOP` und `NEUER_LAUF` beenden alle und geben den Speicher frei.

**Auf dem S3 am 5. November.** Jede Probe lief mit Blick 60, und alle Einstufungen und Entscheidungen stimmten mit Python überein:
- **Leck mit hohem Boden** (`--leck 4096 200000 3 10`, 90 Takte): Je Takt sinkt der freie Speicher um 4.112 Byte, also 4 KiB und 16 Byte Verwaltung. Bei 203.012 Byte hält er drei Takte, nach der Freigabe stehen wieder 363.380 Byte zur Verfügung.
- **Leck bis knapp über den Boden** (`--leck 4096 12288 5 30`, 150 Takte): Ab Takt 73 ist der Speicher knapp (SCHWACH), ab Takt 85 voll (AUSFALL, unter 16 KiB). Mit 13.860 Byte frei lief der S3 sechs Takte lang weiter, der Takt blieb auf die Millisekunde pünktlich. Danach gab er alles frei. Die Untergrenze von 8 KiB ist damit noch nicht geprüft.
- **Bremse** (`--bremse 10 10 300 5 30`, 80 Takte): Die Lücke folgt der Rampe auf weniger als 1 ms genau, 9,6 ms, 19,6 ms und so weiter bis 299,6 ms. Die Abweichung kommt vom 1-ms-Raster von FreeRTOS. Ab 20 ms ist der Takt SCHWACH, ab 200 ms AUSFALL. Nach fünf Takten bei 300 ms und 30 Takten Pause beginnt die Rampe wieder.

Gegenüber 0.4 stehen 2.120 Byte weniger frei, davon 2.048 für die Blocktabelle. Mit Lastaufgabe sind es 363.380 Byte. Die Aufgabe bleibt nach ihrem ersten Start bestehen, auch über `NEUER_LAUF` hinweg.

**Eine Stunde mit allen drei Reizen.** Am 5. November ab 20:45, mit Last 120/120, Leck `4096 12288 5 120`, Bremse `10 10 300 5 120` und Blick 60. Nach 53 min 48 s (Takt 3.228) startete der S3 neu, und der Rekorder brach am Startbanner des ROM ab. Bis dahin:
- Alle 3.228 Einstufungen und Entscheidungen stimmen mit Python überein, kein Takt fehlt.
- 15 Lecks liefen bis 13.860 Byte frei. Nach jeder Freigabe standen wieder genau 363.380 Byte zur Verfügung, der Speicher verliert also nichts.
- 21 Bremsrampen erreichten je 299,6 ms. Ohne Bremse lag die Lücke ab Takt 2 bei höchstens 18 µs.
- 39 % der Takte waren AUSFALL, wie vor dem Start geschätzt.

Den Neustart hat ein anderes Programm ausgelöst. Eine zweite Claude-Sitzung auf demselben Mac suchte zur selben Zeit am USB nach einem anderen Gerät und öffnete dabei diesen Port. Sie las die Startzeile des S3 und das `KOERPER,aus`, mit dem er auf das `STOP` des Rekorders antwortete. Das passt zu allem, was die Aufnahme zeigte: Vor dem Startbanner kam keine Zeile, also weder Panik noch Wachhund noch Brownout, und das Leck stand in diesem Moment weit über dem Boden. Firmware und Versorgung sind damit entlastet. Seitdem meldet die Firmware den Grund ihres Neustarts, und der Rekorder hebt die Zeilen danach auf (siehe „Neustarts sichtbar machen“). Die Wiederholung mit denselben Einstellungen ab 21:49 lief die volle Stunde durch: 3.600 Takte, alle wie Python, 17 Lecks je zurück auf 363.380 Byte, 24 Bremsrampen je 299,7 ms, kein Neustart. Die Auswertung je Signal steht für diese Aufnahme noch aus.

**Weiter Blick im Gerät (seit 0.5).** `BLICK <takte>` lässt die Vorwarnung bis zu 600 Takte vorausdenken, wie `blick_voraus` in kern.py. Blick 1 entscheidet wie bisher, ein neuer Lauf beginnt wieder damit. Während des Körpermodus nimmt das Gerät keinen neuen Blick an, sonst passte die Aufnahme nicht mehr zu ihrer Nachrechnung. Gerät und Python summieren in derselben Reihenfolge. Der Hosttest vergleicht beide bei Blick 2 und 60 für alle drei Lernregeln, absichtlich falsche Varianten fallen dabei auf (ein Schritt zu wenig: 7, ein vergessenes Erbe: 129 von 6.026 Antworten abweichend). Am Rechner verbietet eine Pragma-Zeile dem Compiler, Multiplikation und Addition zu verschmelzen. Auf den geprüften Spuren hätte das keine Entscheidung verändert, die Zeile ist Vorsorge.

Auf dem S3 bestand 0.5 am 5. November die Demo bei Blick 1 wieder mit 240 von 240 Antworten. Bei Blick 60 stimmten sechs Minuten unter Last alle 360 Körpertakte mit Python überein, dazu die drei Reizproben. Im Replay mit einem Muster, das alle neun Übergänge belegt, passten bei Blick 1, 60, 300 und 600 jeweils 240 von 240 Antworten. Die Antwortzeit über die serielle Leitung stieg dabei im Median von 2,50 ms bei Blick 1 auf 2,75, 3,79 und 5,06 ms. Der Blick kostet also etwa 4,3 µs je Takt Vorausschau, bei 600 Takten 2,6 ms, ein Viertelprozent eines Sekundentakts. Gemessen ist das ohne Last auf Kern 0.

**LED.** Ist `ALEX_RGB_PIN` gesetzt (S3-Profile: GPIO48 wie in der Core-Variante DevKitC-1 v1.0, am UICPAL-Board bestätigt), zeigt die eingebaute RGB-LED den Zustand: grün OK, gelb SCHWACH, rot AUSFALL, schwach weiß bereit und kurz blau bei einer Vorwarnung. Die LED-Arbeit zählt nicht zur Lücke. Ihr Treiber belegt 2.872 Byte Speicher.

```bash
python3 koerper.py aufnahme messungen/koerper.csv --port /dev/PORT --regel erbe --takte 3600 --last 120 120 --blick 60
python3 koerper.py pruefen messungen/koerper.csv
python3 koerper.py spur messungen/koerper.csv --grenzen 450 550 65536 16384 20000 200000 > spur.csv
```

Leck und Bremse kommen genauso dazu, zum Beispiel `--leck 4096 12288 5 120 --bremse 10 10 300 5 120`. `aufnahme` schreibt neben die CSV eine JSON mit Regel, Intervall, Grenzen, Blick und Reizen. `pruefen` rechnet jede Einstufung und jede Entscheidung des Geräts nach und fasst die Werte zusammen. `spur` stuft die Rohwerte wahlweise mit anderen Grenzen neu ein, als Eingabe für `versuch.py`. Die Grenzen der ersten Aufnahme (`ERKUNDUNG` in koerper.py: 50 und 60 °C, 64 und 16 KiB frei, 20 und 200 ms Lücke) sind vorläufige Erkundungswerte ohne Datenblattbezug. Eigene Aufnahmen liegen in `messungen/`, das nicht ins Repo geht.

**Erster Lauf am 5. November.** 30 Takte à 1 s auf dem ESP32-S3:
- Chiptemperatur 35 bis 38 °C in ganzen Grad, direkt nach dem Aufspielen fallend
- freier Speicher konstant 371.820 Byte
- Schleifenlücke meist 209 µs, höchstens 655 µs

Alle Takte waren OK, keine Vorwarnung, und alle Einstufungen und Entscheidungen stimmten mit Python überein. Wie erwartet lernt der Knoten auf dem Tisch nur, dass auf OK wieder OK folgt.

**Mitschnitt über drei Stunden, und was er zeigte.** 11.159 Takte ab 10:11:
- Der Median der Temperatur sank von 36 auf 35 °C.
- Der Speicher änderte sich um kein Byte.
- Alle 11.159 Entscheidungen stimmten mit Python überein.
- Ab Takt 41 war die Zeile „nach OK“ gesättigt (Gewicht 9,166). Danach lernte der Knoten nichts mehr, das Erbe blieb unberührt.

Die Lücke lag in 96 % der Takte bei genau 209 µs. Das war ein Fehler im Entwurf: Jedes Fenster enthielt den Durchlauf mit der vorigen Messung, gemessen wurde also der eigene Aufwand. Seit der Korrektur liegt die Lücke in Ruhe bei 16 µs.

**Erkundung mit Last, 5. November 13:23.** 540 Takte, Kern 0 im Rhythmus 120 s Arbeit und 120 s Ruhe:

| | Ruhe | Last |
|---|---:|---:|
| Temperatur, Median | 36 °C | 38 °C |
| Temperatur, Spitze | – | 39 °C |
| Lücke, Median | 16 µs | 17 µs |

Unter Last steigt der Chip binnen etwa einer Minute auf 38 °C, an der Spitze auf 39 °C. In der Ruhe kühlt er in rund zwei Minuten auf 35 bis 36 °C zurück. Die Hauptschleife auf Kern 1 merkt von der Last fast nichts. Der Speicher sank beim Start der Last einmalig um 3.448 Byte, das sind Stapel und Verwaltung der Lastaufgabe.

Probeweise neu eingestuft (SCHWACH ab 37, AUSFALL ab 39 °C) zeigte die Erkundung: Auf ein warmes Signal folgte im nächsten Takt nur in 6 von 351 Fällen ein heißes. Die feste Regel hätte 345 Fehlwarnungen gegeben. „Erbe und Kontext“ warnte dreimal, dann hatte die eigene Erfahrung das Erbe überstimmt. Für ein so träges Signal ist ein Takt Vorhersage zu kurz.

Für den Mitschnitt gelten die auf der Erkundung gewählten Grenzen, danach eingefroren: SCHWACH ab 38 °C, AUSFALL ab 39 °C, Speicher und Lücke wie in `ERKUNDUNG`. Auf der Erkundung ergab das 67 % OK, 27 % SCHWACH und 6 % AUSFALL. Der Mitschnitt mit demselben Lastrhythmus begann um 13:34. Für das Aufspielen von 0.5 endete er um 19:34, nach 21.610 statt der geplanten 43.200 Takte.

**Mitschnitt unter Last, sechs Stunden.** Alle 21.610 Einstufungen und Entscheidungen stimmen mit Python überein, auch mit dem Rechenweg von 0.5 bei Blick 1. Der Speicher blieb bei 365.500 Byte, die Lücke lag im Median bei 16 µs. Die größte Lücke, 306 µs, fällt in den ersten Takt, dessen Fenster die Verarbeitung von `KOERPER` enthält. Danach waren es höchstens 18 µs. Mit einem Takt Blick warnte das Gerät 33-mal. In Ruhe lag der Median jede Stunde bei 37 °C, doch insgesamt wurde der Chip über den Nachmittag wärmer. Die Grenzen blieben fest, der Anteil heißer Takte stieg deshalb:

| Stunde | Ruhe, tiefster Wert | Last, Median | Last, Spitze | Anteil AUSFALL |
|---|---:|---:|---:|---:|
| 1 | 35 °C | 38 °C | 39 °C | 16 % |
| 3 | 36 °C | 39 °C | 39 °C | 32 % |
| 6 | 36 °C | 39 °C | 40 °C | 43 % |

## Vokabular

`vokabular.py` legt die Wörter fest, in denen der Knoten über seinen Körper spricht, bisher nur auf dem Rechner. Es folgt den Regeln aus Alex’ Vokabularentwurf:
- **Feste Nummern:** Nummern ändern sich nie und werden nie neu vergeben, neue Wörter kommen nur hinten dazu.
- **Alte Token:** 1 bis 4 sind die bisherigen Token des Fünf-Byte-Pakets.
- **Oberbegriff:** Jedes Körperwort hat einen. Ein Knoten, der nur OK, SCHWACH und AUSFALL kennt, versteht damit weiter alles.
- **Prüfung:** Ein Test hält Fassung 1 fest und schlägt an, sobald jemand eine bestehende Nummer ändert.

| Nr. | Wort | Oberbegriff | Bedeutung |
|---:|---|---|---|
| 1 | OK | OK | nichts Auffälliges |
| 2 | SCHWACH | SCHWACH | Oberbegriff: eingeschränkt, aber arbeitsfähig |
| 3 | AUSFALL | AUSFALL | Oberbegriff: nicht arbeitsfähig |
| 4 | VORWARNUNG | – | Meldung: ein Ausfall wird erwartet |
| 5 | TEMP_HOCH | SCHWACH | Chiptemperatur ab der Grenze für hoch |
| 6 | TEMP_KRITISCH | AUSFALL | Chiptemperatur ab der Grenze für kritisch |
| 7 | SPEICHER_KNAPP | SCHWACH | freier Speicher bis zur Grenze für knapp |
| 8 | SPEICHER_VOLL | AUSFALL | freier Speicher bis zur Grenze für voll |
| 9 | SCHLEIFE_ZAEH | SCHWACH | fremde Wartezeit der Hauptschleife ab der Grenze für zäh |
| 10 | SCHLEIFE_STEHT | AUSFALL | fremde Wartezeit der Hauptschleife ab der Grenze für steht |

Jeder Körpertakt bekommt das schwerste zutreffende Wort. Bei gleicher Schwere geht Temperatur vor Speicher vor Schleife. Der Oberbegriff dieses Worts ist genau die Einstufung, die das Gerät heute schon vornimmt, ein Test prüft das an allen Grenzfällen. Das Erbe gilt je Signal: Auf hoch folgt kritisch, mit drei festen Beobachtungen.

**Weiter Blick.** Das Wortgedächtnis lernt wie die Kontextregel, welches Wort auf welches folgt. Für eine Vorwarnung denkt es diese Tabelle Schritt für Schritt weiter und schätzt so, wie wahrscheinlich binnen H Takten ein kritisches Wort kommt. Bei H = 1 entscheidet es Takt für Takt genau wie der bisherige Knoten, auch das prüft ein Test. Seit 0.5 teilen sich Auswertung und Knoten dafür eine Funktion, `kern.blick_voraus`. Über OK, SCHWACH und AUSFALL rechnet das Gerät mit `BLICK` dasselbe.

**Wie gezählt wird.** Kritische Läufe mit höchstens 10 Takten Abstand gelten als eine kritische Phase. Sonst zählte jedes Flackern zwischen zwei Gradstufen als neuer Ausfall. Ein Alarm ist ein zusammenhängender Warnlauf außerhalb einer Phase, über eine Phase hinweg verschmelzen zwei Läufe nicht. Er ist richtig, wenn während des Laufs oder binnen H Takten danach eine Phase beginnt. So gezählt gewinnt, wer durchgehend warnt, denn ein langer Lauf reicht bis in die nächste Phase. Seit 0.5 zählt die Auswertung deshalb auch je Takt. Der **Warnanteil** ist der Teil der nicht kritischen Takte mit Warnung, die **Trefferquote** der Teil der Warntakte, auf die binnen H Takten ein kritischer Takt folgt. „Immer warnen“ steht als Maßstab in jeder Tabelle, seine Trefferquote ist die Grundrate. `--bis N` wertet nur die ersten N Takte aus, wie eine kürzere Aufnahme. `--nach N` zählt erst danach, gelernt wird über die ganze Aufnahme.

Wirken mehrere Reize, zählt eine zweite Tabelle **je Signal**. Dafür wird jedes Signal für sich eingestuft, ohne den Vorrang der Wörter, ein Leck bleibt also auch bei heißem Chip sichtbar. Jedes Signal hat seine eigenen kritischen Phasen. Eine Warnung bei seinem hohen Wort (TEMP_HOCH, SPEICHER_KNAPP, SCHLEIFE_ZAEH) trifft nur, wenn binnen H Takten sein eigenes kritisches Wort folgt. Ein warmer Takt bekommt so keinen Treffer für ein Leck, das zufällig danach kommt. Bei Warnungen im Zustand OK zählt jedes kritische Wort. Diese Zählung stand fest, bevor die erste Aufnahme mit allen drei Reizen ausgewertet wurde.

```bash
python3 vokabular.py liste
python3 vokabular.py auswertung messungen/koerper-last-2026-11-05.csv --horizont 30 60 --bis 2460
python3 vokabular.py auswertung messungen/koerper-last-2026-11-05.csv --horizont 30 60 --nach 2460
```

**Am Mitschnitt unter Last, 41 Minuten mit 20 Hitzephasen:**

| Verfahren | vorgewarnt, Horizont 30 s | Fehlalarme / Alarme | Vorwarnzeit | vorgewarnt, Horizont 60 s | Fehlalarme / Alarme | Vorwarnzeit |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 20 / 20 | 14 / 34 | 30 s | 20 / 20 | 13 / 34 | 56 s |
| Grob, ein Takt (heute im Gerät) | 1 / 20 | 0 / 1 | 28 s | 2 / 20 | 0 / 1 | 44 s |
| Grob, weiter Blick | 20 / 20 | 14 / 34 | 30 s | 20 / 20 | 13 / 34 | 56 s |
| Vokabular, weiter Blick | 20 / 20 | 14 / 34 | 30 s | 20 / 20 | 13 / 34 | 56 s |
| Vorschlag Richtung, weiter Blick | 20 / 20 | 24 / 44 | 30 s | 20 / 20 | 14 / 36 | 60 s |
| Immer warnen | 20 / 20 | 1 / 21 | 30 s | 20 / 20 | 1 / 21 | 60 s |

Je Takt gezählt, bei 30 und 60 s Horizont: Die feste Regel warnt in 38 % der nicht kritischen Takte und trifft zu 68 bzw. 78 %. Der weite Blick warnt in 51 bzw. 55 % und trifft zu 54 bzw. 60 %. Immer warnen träfe zu 30 bzw. 44 %.

Drei Befunde:
- **Der Blick entscheidet über das Erbe.** Bei einem Takt widerlegt die Erfahrung das Erbe. Mit 30 bis 60 s Blick bestätigt sie es aus eigenen Beobachtungen: Auf warm folgt binnen einer Minute heiß, und der Knoten warnt bei jedem warmen Takt wie die feste Regel. Er warnt aber auch in einem Teil der OK-Takte. Nach Läufen gezählt fällt das nicht auf, denn diese Warnungen verlängern nur Läufe, die ohnehin zählen. Je Takt trifft die feste Regel öfter.
- **Mehr Wörter allein ändern noch nichts.** Auf dem Tisch schwankt nur die Temperatur, TEMP_HOCH ist dann SCHWACH und TEMP_KRITISCH ist AUSFALL. Die Wörter für Speicher und Schleife warten auf Erfahrungen.
- **Die Fehlalarme sind Nachwärme.** 12 der 14 beginnen außerhalb der Last, 10 davon höchstens 15 s nach dem Ende einer Hitzephase, wenn der Chip beim Abkühlen noch auf 38 °C steht.

Ein erster Vorschlag für den wachsenden Rand teilt OK und TEMP_HOCH nach der Richtung der Temperatur auf: Median der letzten fünf Takte gegen fünf Takte 20 Takte zuvor. Das Fenster ist eine Wahl vorab, die Erkundung hatte für eine Wahl aus den Daten nur zwei Hitzephasen. Der Vorschlag verschiebt die Warnungen nach vorn, beseitigt die Nachwärme aber nicht. In dieser Form ist er deshalb nicht bestätigt und hat keine Nummer bekommen. Gegen Nachwärme spricht mehr für einen längeren Zusammenhang, etwa das vorige Wort oder die Dauer in einem Zustand, als für weitere Wörter.

**Endauswertung nach sechs Stunden.** Die Blickweiten 30 und 60 wurden an den ersten 41 Minuten gewählt, das ist die Tabelle oben. Danach folgten 114 Phasen, an denen nichts mehr gewählt wurde. Gelernt hat jedes Verfahren über die ganze Aufnahme, gezählt wird nur danach (`--nach 2460`). Alle Verfahren außer dem mit einem Takt Blick warnen jede der 114 Phasen vor.

| Verfahren | Fehlalarme / Alarme, 30 s | Warnanteil | Trefferquote | Fehlalarme / Alarme, 60 s | Warnanteil | Trefferquote |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 158 / 279 | 44 % | 53 % | 130 / 279 | 44 % | 60 % |
| Grob, ein Takt (bis 0.4 im Gerät, 1 von 114 vorgewarnt) | 9 / 9 | 0 % | 50 % | 9 / 9 | 0 % | 50 % |
| Grob oder Vokabular, weiter Blick | 99 / 218 | 65 % | 38 % | 50 / 206 | 72 % | 48 % |
| Vorschlag Richtung, weiter Blick | 123 / 246 | 64 % | 38 % | 46 / 200 | 80 % | 48 % |
| Immer warnen | 1 / 115 | 100 % | 31 % | 1 / 115 | 100 % | 50 % |

- **Nach Läufen gezählt gewinnt, wer immer warnt.** Ein durchgehender Lauf reicht von Phase zu Phase und gibt nur einen Fehlalarm. Der Zwischenstand nach knapp vier Stunden, der gelernte Blick schlage die feste Regel (55 gegen 96 Fehlalarme bei 60 s), beruhte auf dieser Zählung und hält nicht.
- **Je Takt bleibt die feste Regel vorn.** Von den Verfahren, die jede Phase vorwarnen, warnt sie am seltensten und trifft am besten. Der gelernte Blick warnt bei jedem warmen Takt und dazu in vielen OK-Takten. Bei 60 s trifft er nicht besser als immer warnen. Drei Zustände verraten nicht, ob nach einem OK die nächste Hitze nah ist. Mit dem wärmer werdenden Chip warnte er auch in OK öfter: Sein Warnanteil stieg bei 60 s von 55 auf 72 %, der der festen Regel nur von 38 auf 44 %.
- **Ein Takt bleibt zu kurz.** Er warnt eine von 114 Phasen vor, alle neun Alarme sind falsch.

Für eine Entscheidung zählt, was jeder Warntakt kostet. So rechnet Daniels Systemversuch mit Reservetakten. Gegen die Warnungen in OK hilft eher mehr Zusammenhang, etwa das vorige Wort oder die Dauer im Zustand, als ein weiterer Blick.

**Drei Reize, je Signal gezählt.** Die Stunde mit Last, Leck und Bremse (3.228 Takte, an ihr wurde nichts gewählt), Horizont 60 s:

| Signal und hohes Wort | Phasen | vorgewarnt | Trefferquote beim hohen Wort |
|---|---:|---:|---:|
| Temperatur, TEMP_HOCH | 27 | 27 | 61 % |
| Speicher, SPEICHER_KNAPP | 15 | 15 | 100 % |
| Schleife, SCHLEIFE_ZAEH | 21 | 20 | 100 % |

Feste Regel, grober und feiner Blick warnen bei jedem hohen Wort und kommen deshalb auf dieselben Zahlen. Das feine Vokabular entscheidet auch hier genau wie das grobe.
- **Leck und Bremse kündigen sich verlässlich an, die Wärme nicht.** Auf knapp folgt immer voll, auf zäh immer steht, auf warm nur zu 61 % binnen einer Minute heiß. Bei verlässlichen Vorzeichen ist die feste Regel ideal, und das Gedächtnis lernt dasselbe.
- **Ein Wort je Takt verdeckt ein zweites Signal.** Die eine Bremsphase ohne Vorwarnung hatte 18 zähe Takte vor sich, doch der Chip war zugleich heiß. Dann zählt das schwerere Wort TEMP_KRITISCH, und im Ausfall warnt der Knoten nicht. Bei 30 s Blick traf das zwei Lecks und drei Bremsphasen. Wer wissen will, was als Nächstes ausfällt, braucht einen Zustand je Signal.
- **Im OK-Zustand trifft der Blick nur die Grundrate.** Er warnt in 74 % der OK-Takte und trifft zu 77 %, genau wie immer warnen. Insgesamt trifft die feste Regel zu 88 % bei 59 % Warnanteil, der Blick zu 84 % bei 89 %. Weil 39 % der Takte AUSFALL waren, liegt die Grundrate schon bei 83 %.

```bash
python3 vokabular.py auswertung messungen/koerper-reize-2026-11-05.csv --horizont 30 60
```

## Kommunikationsversuch und nächste Entscheidung

`transport.py` spielt einem Sender und einem Empfänger dieselbe logische Uhr vor. Ein Statuspaket besteht aus vier Byte Takt in Big Endian und einem Byte Zustand. OK, SCHWACH und AUSFALL haben die IDs 1–3, Vorwarnung die ID 4. Der Zustandskanal akzeptiert nur die ersten drei. Doppelte, verspätete oder zukünftige Pakete verändern den Empfängerstand nicht. Der Versuch verwendet eine bekannte Sitzung mit genau einem Sender. Bei realen Neustarts und mehreren Knoten muss die Gegenstelle Sender und Sitzungen unterscheiden, bevor sie Sequenznummern vergleichen kann.

Der Herzschlag trägt den aktuellen Zustand. Nach zehn Takten ohne gültige Meldung wird er beim Empfänger unbekannt. Protokolliert werden gesendete Nutzbytes, empfangene Pakete, falsche und unbekannte Takte sowie der erste tatsächlich sichtbare Ausfall. Vorwarnungen werden in diesem Teilversuch nicht übertragen. Bei Totalausfall der Leitung kann ein Empfänger die Ursache der Stille nicht feststellen. Ein zweiter Meldeweg oder ein später auslesbares lokales Ereignisprotokoll wäre dafür ein eigener, messbarer Versuch.

**Abnahme der nächsten Etappe.** Ein physischer Knoten soll die Referenzspur und den Wiederanlauftest bestehen. Die Referenzspur hat Alex’ ESP32-S3 am 5. November in allen drei Varianten bestanden, den Wiederanlauf nach Stromtrennung in der Erbe-Variante. Auf einer getrennten Feldaufzeichnung sollen Alex und Claude danach die Zahl nützlicher Vorwarnungen, Fehlwarnungen, verpasster Ausfälle, offene Warnungen und die tatsächlich verfügbare Reaktionszeit berichten. Erst mit dieser Messung lässt sich entscheiden, welche Gedächtnisregel und welcher Meldetakt in Alex’ Alltag sinnvoll sind.

**Offene Grundsatzfrage.** Laut Ideensammlung steigt die Stärke einer Erinnerung bei jedem Abruf. Hier verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel. `test_abrufen_verstaerkt_keine_vermutung` sichert das ab. Ein möglicher Ausgleich wären zwei Werte pro Eintrag: ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf. Die Entscheidung liegt bei Alex. Vor einem zweiten echten Knoten braucht das Fünf-Byte-Paket außerdem eine Sender- und Sitzungskennung.
