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

**Erbe und Kontext.** Das siebte Verfahren nutzt die Kontextregel und rechnet zusätzlich mit drei festen Beobachtungen „SCHWACH → AUSFALL“. Sie liegen in einer eigenen Tabelle, verblassen nie und werden durch Beobachtung nicht verändert. Weil Erbe und Erfahrung getrennt liegen, ist die Herkunft jedes Belegs bekannt. Das Erbe steht für Wissen von außen, etwa von Alex oder einem Sprachmodell. Die Zahl drei ist der Mindestbeleg der Warnregel und wurde nicht an Messwerte angepasst. Die erste Gegenprobe am 5. November lief allerdings auf dem Kontrollsatz. Der Entwicklungssatz zeigt dasselbe Bild: bei seltenem Vorzeichen 202 richtige Vorwarnungen wie bei der festen Regel, bei stabilem 1844 statt 1845. `--erbe-reihe` vergleicht null bis zwölf feste Beobachtungen auf dem gewählten Satz. Sketch, serieller Prüfer und Neustart kennen alle Lernregeln. Ihre Namen stehen an einer Stelle, `REGELN` in kern.py. Der Sketch bildet die Summen in derselben Reihenfolge wie Python und entscheidet deshalb bitgleich. Als Gegenprobe wurde das Erbe im Sketch probehalber auf zwei gesetzt. Der Paritätstest schlug daraufhin beim ersten schwachen Signal an.

**Erbe als Startwert (seit 6. November).** Die vierte Regel `startwert` beginnt mit demselben Erbe, lässt es aber mit jedem eigenen Ausgang aus seinem Zustand verblassen, mit dem Faktor der Kontextregel. Bleiben im selben Zustand zählt nicht. So trägt das Erbe die erste Warnung und weicht, wenn der Zustand anders endet. Warum und mit welchem Ergebnis, steht unter „Wechselnde Bedeutung, sechs Stunden“.

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

Der versionierte JSON-Stand enthält Messreihenkennung, letzten Takt und Zustand, Regel, Halbwertszeit, Erbe, Vokabular und neun Gewichte. Halbwertszeit und Erbe müssen beim Laden zur Regelversion passen. Beim Startwert liegt das Erbe dafür zwischen null und seinem Anfang. Stände aus 0.2 tragen kein Erbe und bleiben ladbar. Mit `--regel erbe` beginnt ein neuer Lauf mit Erbe. Eine SHA-256-Prüfsumme erkennt Veränderungen. Beim Laden werden Format, Quelle, Wertebereiche und Version geprüft. Gesichert wird zunächst in einer temporären Datei im Zielverzeichnis. Nach dem Schreiben wird sie unter dem neuen Namen veröffentlicht. Das lokale Dateisystem muss Hardlinks unterstützen. Ein vorhandener Stand wird nicht überschrieben. Die Tests vergleichen jede Entscheidung nach dem Neustart mit dem ungeteilten Lauf. Für reale Auszeiten muss die Taktnummer die verstrichene Zeit abbilden. Autorisierung, Verschlüsselung und ein Schutz gegen absichtlich zurückgespielte ältere Stände gehören zu einem späteren Produkt für persönliche Daten.

## Gerätestand und Prüfweg

Der Sketch akzeptiert über die serielle Schnittstelle Zeilen wie `34,SCHWACH`. Die Antwort enthält Takt, Zustand, Sofortmeldung und Vorwarnung. Jede Zeile endet mit LF oder CRLF. Ein Wiederholungstakt, ein unbekanntes Token oder eine überlange Zeile ergibt `FEHLER` und verändert das Gedächtnis nicht. Das lesbare Replay-Protokoll ist vom modellierten Fünf-Byte-Statuspaket getrennt. Es dient der Prüfung auf dem Tisch. [Espressif-Dokumentation zur seriellen Schnittstelle](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/serial.html)

Mit PlatformIO 6.1.18, Plattform espressif32 6.12.0 und dem Profil für den klassischen ESP32 Dev Module wurden alle Firmwareabbilder übersetzt. Das Profil ist eine Referenzwahl. Für Alex’ konkretes Board zuerst die genaue Chipfamilie, Flashgröße, Boardkennung und den seriellen Port bestimmen. [Boardprofil des Referenzgeräts](https://docs.platformio.org/en/latest/boards/espressif32/esp32dev.html)

Seit 0.3 gibt es dieselben drei Varianten für Alex’ ESP32-S3-N16R8 (UICPAL, DevKitC-1-Klon): `esp32s3`, `esp32s3-kontext` und `esp32s3-erbe`. Die Speicherwerte stammen aus Alex’ Projekt `esp32-s3-audio`: Oktal-PSRAM (`qio_opi`), 16 MB Flash und die Tabelle `default_16MB.csv`. `Serial` ist UART0 am COM-Anschluss mit der CH343-Brücke, deshalb gilt `ARDUINO_USB_CDC_ON_BOOT=0`. Dort kann das Öffnen des Ports das Board zurücksetzen wie beim klassischen ESP32, muss es aber nicht. Am Abend des 5. November tat es das nicht. Der Prüfer kommt mit beidem zurecht. Am nativen USB-Anschluss müsste `ARDUINO_USB_CDC_ON_BOOT=1` gesetzt werden. Das ist nicht geprüft. Seit dem 6. November hat jedes Board eine vierte Variante, `esp32dev-startwert` und `esp32s3-startwert`.

```bash
pio run -d esp32
```

| Gebaute Variante | Vom Linker gemeldete RAM-Belegung | Vom Build gemeldeter Flashbedarf |
|---|---:|---:|
| esp32dev · Zeit | 23.972 Byte | 289.257 Byte |
| esp32dev-kontext · Kontext | 23.972 Byte | 289.273 Byte |
| esp32dev-erbe · Erbe und Kontext | 23.972 Byte | 289.253 Byte |
| esp32dev-startwert · Startwert | 23.972 Byte | 289.273 Byte |
| esp32s3 · Zeit | 21.600 Byte | 301.873 Byte |
| esp32s3-kontext · Kontext | 21.600 Byte | 301.873 Byte |
| esp32s3-erbe · Erbe und Kontext | 21.600 Byte | 301.873 Byte |
| esp32s3-startwert · Startwert | 21.600 Byte | 301.873 Byte |

Gebaut am 6. November mit Leckmuster, Startwert und `isKey` auf Alex’ Mac. Die Zahlen umfassen das Arduino-Programm samt Framework. Die neun Gewichte und die Erbtabelle belegen je 72 Byte, die Tabelle für die Blöcke des Lecks 2.048 Byte. In 0.3, vor Körpermodus und Reizen, lag die RAM-Belegung beim S3 bei 18.872 Byte. Die Rechenzeit des weiten Blicks ist am Gerät gemessen (siehe „Weiter Blick im Gerät“), Stromaufnahme und tatsächlich beanspruchte Flashzyklen noch nicht. Der Hosttest führt je Variante den identischen Sketch auf der Demo und allen 120 Kontrollspuren aus. Alle 57.840 Antworten pro Variante stimmen bei Takt, Zustand, Sofortmeldung und Vorwarnung mit Python überein.

**Erster Boardlauf.** Nach dem Aufspielen der zum Gerät passenden Variante den seriellen Monitor schließen und mit einem Python-Interpreter mit `pyserial` den Prüfer starten. Den Beispielport durch den tatsächlichen Port ersetzen. Der Prüfer startet bewusst einen leeren RAM-Lauf, sendet eine Zeile, wartet auf die Antwort und vergleicht jede Entscheidung. Erwartet werden 240 von 240 passende Antworten. Startet das Board langsam, sendet der Prüfer `NEUER_LAUF` mehrmals, und jede Wiederholung wird beantwortet. Seit 0.3 überspringt er diese späten Bereitmeldungen vor der ersten Antwort. Vorher schlug der Hosttest gelegentlich beim ersten Start frisch übersetzter Programme fehl.

```bash
python3 boardprobe.py --port /dev/PORT --regel zeit
```

**Erster Boardlauf auf dem S3.** Geprüft wurde ein UICPAL-S3, ein ESP32-S3-N16R8 auf einem DevKitC-1-Klon mit zwei USB-C-Anschlüssen. Das Kabel gehört an den COM-Anschluss. Dort trägt der Port die Seriennummer der CH343-Brücke im Namen (`/dev/cu.usbmodem…`) und bleibt beim Umstecken gleich. Am nativen Anschluss erscheint dasselbe Board mit wechselnder Nummer und meldet die MAC als Seriennummer. In den Befehlen steht `/dev/PORT` für den COM-Port. Vor dem ersten Aufspielen bestätigt `esptool.py … flash_id` Chip, Flashgröße und PSRAM, ohne etwas zu schreiben. Danach je Variante aufspielen und prüfen:

```bash
pio run -d esp32 -e esp32s3-erbe -t upload --upload-port /dev/PORT
python3 boardprobe.py --port /dev/PORT --regel erbe
```

**Ergebnis am 5. November.** esptool bestätigte einen ESP32-S3 (QFN56) Revision v0.2 mit 16 MB Flash, 8 MB eingebettetem PSRAM und der erwarteten MAC. Aufgespielt wurde mit 230400 Baud, Bootloader, Partitionstabelle, otadata und App jeweils mit bestätigtem Hash. Zeit, Kontext und Erbe bestanden die Demo mit je 240 von 240 Antworten. Die Gegenprobe mit falscher `--regel` brach wie vorgesehen mit „Falsche Variante“ ab. Auf dem Board lief danach `esp32s3-erbe`, seit dem 6. November läuft `esp32s3-startwert`. Geprüft ist damit die Demo, die 120 Kontrollspuren liefen nur im Hosttest. Auch der Wiederanlauf nach Stromtrennung bestand. Die Erbe-Variante sicherte nach 99 Takten, war 5 s ohne Strom und lud danach ihren Stand. Takt 99 wurde abgewiesen, Takt 100 angenommen, und die übrigen 141 Antworten entsprachen dem durchgehenden Lauf. Ein erster Versuch war beim Sichern abgebrochen, ohne dass sichtbar wurde, was statt `GESICHERT` ankam. Vermutlich brauchte der erste Flashzugriff nach dem Aufspielen länger als die 0,6 s Lesefrist. Belegt ist das nicht. Seitdem wartet `wiederanlauf.py` bis zu 3 s und nennt im Fehlerfall die erhaltene Zeile. Am 6. November nannte es die Zeile. Gibt es den Schlüssel im NVS noch nicht, schreibt der Arduino-Kern beim ersten Sichern vor `GESICHERT` eine eigene Fehlerzeile auf die serielle Leitung: `[E][Preferences.cpp:503] getBytesLength(): nvs_get_blob len fail: startwert NOT_FOUND`. Das zweite Sichern lief sauber, weil der Schlüssel dann existierte. Wahrscheinlich war das auch am 5. November die Ursache, nicht die Lesefrist. Seitdem prüft der Sketch den Schlüssel zuerst mit `Preferences::isKey`, das nichts meldet. Die Ersatz-Preferences im Hosttest schreiben dieselbe Fehlerzeile wie der Kern. Ohne `isKey` schlägt der Test deshalb an. Am Gerät lief danach das erste Sichern unter `kontext` sauber durch, ein Schlüssel, der auf diesem Board vorher nie gesichert worden war.

**Neustart auf dem Board.** `SICHERN` legt den aktuellen Stand im NVS-Namensraum `alex-lernlabor` ab. Jede Regel hat ihren eigenen Schlüssel: `zeit`, `kontext`, `erbe` und `startwert`. Nur dieser explizite Befehl schreibt den Lernstand. Bereits identische Nutzdaten werden erkannt. `NEUER_LAUF` setzt das RAM zurück. `LADEN` übernimmt einen gültigen Stand in einen leeren Knoten. Das binäre Format hat genau 86 Byte. Es enthält die Kennung `AG01`, Regel (1 Zeit, 2 Kontext, 3 Erbe) und Zustand als je ein Byte, den Takt als uint32, neun binary64-Gewichte in Zeilenfolge OK/SCHWACH/AUSFALL und eine CRC32 über die ersten 82 Byte. Mehrbyte-Werte werden in Little Endian gespeichert. Die Prüfung erkennt Beschädigungen und verweigert ungültige Werte. Sie authentifiziert keinen Absender. Bei Zeit, Kontext und Erbe steht das Erbe nicht im Stand, es gehört zur Firmware. Der Startwert (Regel 4) verblasst, sein Stand heißt deshalb `AG02` und hat 158 Byte. Hinter den Gewichten folgen die neun Werte des Erbes in derselben Zeilenfolge, die CRC32 deckt die ersten 154 Byte. Ein geladenes Erbe darf nicht über seinen Anfang wachsen und nicht dort entstehen, wo die Regel keines hat. Einen Stand einer anderen Regel weist `LADEN` ab. [Espressif-Dokumentation zu Preferences und NVS](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/preferences.html)

Für den physischen Wiederanlauftest gibt es seit 0.3 `wiederanlauf.py`. `sichern` spielt einen zufällig langen Anfang der Demo ein, vergleicht jede Antwort und lässt den Stand sichern. Danach das Board vom Strom trennen und wieder einschalten. `laden` lädt den Stand und sendet den Grenztakt noch einmal. Das Gerät muss ihn abweisen und den nächsten Takt annehmen, erst dann endet der Stand genau an der Grenze. Den Rest vergleicht es mit dem durchgehenden Lauf. Der zufällige Grenztakt sorgt dafür, dass ein älterer Stand im NVS nicht als Erfolg durchgeht.

```bash
python3 wiederanlauf.py sichern --port /dev/PORT --regel erbe
python3 wiederanlauf.py laden --port /dev/PORT --regel erbe --grenze N
```

Der Hosttest spielt beide Teile in zwei getrennten Prozessen mit Dateibackend durch, auch mit falscher Grenze. Der Zustand nach einem Abbruch **während** des Schreibens steht noch aus.

## Körpersignale

Seit 0.4 misst sich der Knoten auf Wunsch selbst. Im Körpermodus liest er in eigenem Takt die Chiptemperatur, den freien internen Speicher und die größte Lücke zwischen zwei Durchläufen von `loop()` seit dem letzten Takt. Durchläufe mit eigener Arbeit, also Messung, Ausgabe und LED, zählen dabei nicht mit, gemessen wird nur fremde Wartezeit. Daraus stuft er den Takt als OK, SCHWACH oder AUSFALL ein, der schlechteste der drei Werte zählt. Mit dieser Einstufung lernt er wie im Replay. Eine nicht lesbare Temperatur steht als „-“ in der Ausgabe und zählt nicht mit.

Die Firmware hat keine eigenen Grenzwerte. `GRENZEN` übergibt sie in Zehntelgrad, Byte und Mikrosekunden, `KOERPER <ms>` startet den Modus, `STOP` beendet ihn. Jeder Takt antwortet mit `K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us,reiz`. Das letzte Feld hält in Bits fest, welche Reize gerade wirken: 1 Last, 2 Leck, 4 Bremse. Bis 0.4 hieß es `last` und kannte nur die Last, solche Aufnahmen bleiben lesbar. `MESSWERT` speist Rohwerte von außen ein und nimmt denselben Weg durch Einstufung und Lernen. Darüber vergleicht der Hosttest beides mit Python.

**Neustarts sichtbar machen.** Beim Start meldet die Firmware `NEUSTART,<nummer>,<grund>`, mit dem Grund aus `esp_reset_reason()`, etwa `PANIK`, `TASK_WACHHUND` oder `UNTERSPANNUNG`. Ein Puls auf der EN-Leitung, wie ihn die USB-Brücke gibt, sieht für den Chip aus wie echtes Einschalten: Das ROM schreibt `rst:0x1 (POWERON)`, die Firmware `NEUSTART,1,EINSCHALTEN`. Kommt während einer Aufnahme statt einer Körperzeile etwas anderes, hebt `aufnahme` diese Zeile und alles danach in `<name>.abbruch.txt` auf. Die Fehlermeldung nennt die Zeilen `rst:` und `NEUSTART,`. Geprüft ist das am S3 mit einem EN-Puls aus einem zweiten Prozess mitten in einer Aufnahme. Ein fremder Prozess am Port kann das Board also während einer Aufnahme zurücksetzen. Deshalb belegt `aufnahme` den Port seitdem exklusiv (TIOCEXCL). Am S3 scheitert ein zweites Öffnen dann mit EBUSY.

**Eine Veränderung mitgeben.** `LAST <an_s> <aus_s>` lässt Kern 0 im vorgegebenen Rhythmus arbeiten und ruhen, die Hauptschleife läuft auf Kern 1. Die Arbeit gibt alle 10 ms kurz ab, damit der Task-Wachhund nicht anschlägt und keine Meldung ins Protokoll schreibt. `LAST 0 0`, `STOP` und `NEUER_LAUF` beenden die Last. Die Einstufung kennt die Phase nicht, der Knoten spürt die Last allein über seine Messwerte.

**Speicher und Schleife reizen (seit 0.5).** Damit auch die Wörter für Speicher und Schleife Erfahrungen bekommen, gibt es zwei weitere Reize. Beide wirken im Takt des Körpers, ihr Ablauf steht in `Reize.h` und wird am Rechner geprüft:
- `LECK <byte> <boden> <halten> <pause> [<flach> <muster>]` belegt je Takt einen Block internen Speichers, bis kein Block mehr über den Boden passt. Dann bleibt es `halten` Takte am Boden, gibt alles frei und wächst nach `pause` Takten wieder. Blöcke von 1 bis 64 KiB. Der Boden liegt bei mindestens 8 KiB, das ist eine gewählte Reserve für Ausgabe, LED und Lastaufgabe, noch keine gemessene. Mit `flach` und `muster` hält nicht jeder Durchgang erst am Boden: Bit n des Musters gilt für Durchgang n, nach 32 Durchgängen von vorn, und ein gesetztes Bit hält schon bei `flach` Byte an. Liegt `flach` zwischen den Grenzen für voll und knapp, folgt auf knappen Speicher mal voller und mal nicht. Das Vorzeichen wechselt so seine Bedeutung, wie in den synthetischen Szenarien. Am S3 geprüft mit `--leck 4096 12288 2 5 32768 2`: Der erste Durchgang ging bis 13.180 Byte, der zweite hielt bei 33.740 Byte, der dritte ging wieder tief.
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

Den Neustart hat ein anderes Programm ausgelöst. Eine zweite Claude-Sitzung auf demselben Mac suchte zur selben Zeit am USB nach einem anderen Gerät und öffnete dabei diesen Port. Sie las die Startzeile des S3 und das `KOERPER,aus`, mit dem er auf das `STOP` des Rekorders antwortete. Das passt zu allem, was die Aufnahme zeigte: Vor dem Startbanner kam keine Zeile, also weder Panik noch Wachhund noch Brownout, und das Leck stand in diesem Moment weit über dem Boden. Firmware und Versorgung sind damit entlastet. Seitdem meldet die Firmware den Grund ihres Neustarts, und der Rekorder hebt die Zeilen danach auf (siehe „Neustarts sichtbar machen“). Die Wiederholung mit denselben Einstellungen ab 21:49 lief die volle Stunde durch: 3.600 Takte, alle wie Python, 17 Lecks je zurück auf 363.380 Byte, 24 Bremsrampen je 299,7 ms, kein Neustart. Je Signal bestätigt sie die erste Stunde (siehe „Drei Reize, je Signal gezählt“ unter Vokabular).

**Sechs Stunden mit wechselnder Bedeutung.** Am 5. November ab 23:17, mit Last 120/120, Leck `4096 12288 5 120 32768 4278255360`, Bremse `10 10 300 5 120` und Blick 60. Das Muster ist 0xFF00FF00: Acht Durchgänge gehen bis zum Boden, acht halten bei 32 KiB, im Wechsel, ein Block dauert knapp eine halbe Stunde. Die Frage: Lernt ein Gedächtnis, wann knapper Speicher voll wird, und schlägt es dort die feste Regel? Der Port war exklusiv belegt, der Lauf ging ohne Neustart bis 05:17 durch:
- Alle 21.600 Einstufungen und Entscheidungen stimmen mit Python überein, kein Takt fehlt.
- 104 Lecks, genau nach Muster: 56 gingen bis 13.844 Byte, 48 hielten bei 34.404 Byte. Knapp war der Speicher im tiefen Durchgang 12 Takte, dann voll, im flachen 13 Takte, dann wieder frei. Nach jeder Freigabe standen 363.364 Byte zur Verfügung, mit der Firmware fürs Muster 16 Byte weniger als zuvor.
- 141 Bremsrampen erreichten je 299,7 bis 300,4 ms. Ohne Bremse lag die Lücke ab Takt 2 bei höchstens 19 µs.
- Der Chip lag zwischen 35 und 39 °C. OK waren 10.489 Takte, SCHWACH 8.219, AUSFALL 2.892.

Was die Verfahren daraus lernen, steht unter Vokabular („Wechselnde Bedeutung“).

**Weiter Blick im Gerät (seit 0.5).** `BLICK <takte>` lässt die Vorwarnung bis zu 600 Takte vorausdenken, wie `blick_voraus` in kern.py. Blick 1 entscheidet wie bisher, ein neuer Lauf beginnt wieder damit. Während des Körpermodus nimmt das Gerät keinen neuen Blick an, sonst passte die Aufnahme nicht mehr zu ihrer Nachrechnung. Gerät und Python summieren in derselben Reihenfolge. Der Hosttest vergleicht beide bei Blick 2 und 60 für alle Lernregeln, absichtlich falsche Varianten fallen dabei auf (ein Schritt zu wenig: 7, ein vergessenes Erbe: 129 von 6.026 Antworten abweichend). Am Rechner verbietet eine Pragma-Zeile dem Compiler, Multiplikation und Addition zu verschmelzen. Auf den geprüften Spuren hätte das keine Entscheidung verändert, die Zeile ist Vorsorge.

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

Wirken mehrere Reize, zählt eine zweite Tabelle **je Signal**. Dafür wird jedes Signal für sich eingestuft, ohne den Vorrang der Wörter, ein Leck bleibt also auch bei heißem Chip sichtbar. Jedes Signal hat seine eigenen kritischen Phasen. Eine Warnung, während das Signal selbst auf seiner hohen Stufe steht (TEMP_HOCH, SPEICHER_KNAPP, SCHLEIFE_ZAEH), trifft nur, wenn binnen H Takten seine eigene kritische Stufe folgt. Gezählt wird nach der Stufe des Signals, nicht nach dem Wort des Takts. Ein von Hitze verdecktes Vorzeichen zählt deshalb als nicht gewarnt. Ein warmer Takt bekommt so keinen Treffer für ein Leck, das zufällig danach kommt. Bei Warnungen im Zustand OK zählt jedes kritische Wort. Diese Zählung stand fest, bevor die erste Aufnahme mit allen drei Reizen ausgewertet wurde. Nach dem Befund zur Verdeckung kam am selben Abend die Zuordnung nach der eigenen Stufe hinzu, dazu ein Verfahren **Je Signal**: ein eigenes Gedächtnis je Signal über dessen eigene Stufen, jedes mit seinem Erbe hoch → kritisch. In der Gesamttabelle warnt es, wenn eines seiner Signale warnt und kein Wort kritisch ist.

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

Feste Regel, grober und feiner Blick kommen auf dieselben Zahlen, das feine Vokabular entscheidet auch hier genau wie das grobe. Nach der Stufe des Signals selbst gezählt warnen sie aber nur in 90 % der warmen, 66 % der knappen und 76 % der zähen Takte. Im Rest verdeckt ein anderes Signal das Vorzeichen. Das eigene Gedächtnis je Signal warnt in allen diesen Takten und sieht auch die verdeckte Bremsphase vorher (21 von 21). Es trifft zu 62, 97 und 100 %. Im Zustand OK rät es wie die anderen, 75 % gegen eine Grundrate von 77 %.
- **Leck und Bremse kündigen sich verlässlich an, die Wärme nicht.** Auf knapp folgt immer voll, auf zäh immer steht, auf warm nur zu 61 % binnen einer Minute heiß. Bei verlässlichen Vorzeichen ist die feste Regel ideal, und das Gedächtnis lernt dasselbe.
- **Ein Wort je Takt verdeckt ein zweites Signal.** Die eine Bremsphase ohne Vorwarnung hatte 18 zähe Takte vor sich, doch der Chip war zugleich heiß. Dann zählt das schwerere Wort TEMP_KRITISCH, und im Ausfall warnt der Knoten nicht. Bei 30 s Blick traf das zwei Lecks und drei Bremsphasen. Wer wissen will, was als Nächstes ausfällt, braucht einen Zustand je Signal.
- **Im OK-Zustand trifft der Blick nur die Grundrate.** Er warnt in 74 % der OK-Takte und trifft zu 77 %, genau wie immer warnen. Insgesamt trifft die feste Regel zu 88 % bei 59 % Warnanteil, der Blick zu 84 % bei 89 %. Weil 39 % der Takte AUSFALL waren, liegt die Grundrate schon bei 83 %.

**Die Wiederholung bestätigt das.** Die volle Stunde ab 21:49, wieder bei 60 s:
- **Je Signal:** Temperatur 20 von 20 Phasen vorgewarnt, Treffer bei TEMP_HOCH 58 %. Speicher 17 von 17 und Schleife 24 von 24, beide mit 100 % Treffern. Bei 30 s blieben je zwei Lecks und Bremsphasen ohne Vorwarnung.
- **Im OK-Zustand:** Der Blick warnt in 72 % der Takte und trifft zu 69 %, immer warnen träfe 72 %.
- **Insgesamt:** Die feste Regel trifft zu 90 % bei 55 % Warnanteil, der Blick zu 82 % bei 87 %, die Grundrate liegt bei 82 %. Das feine Vokabular weicht nur in einem Alarm vom groben ab.
- **Je Signal:** Die feste Regel warnt in 88, 59 und 65 % der warmen, knappen und zähen Takte, das eigene Gedächtnis je Signal in allen. Es trifft zu 59, 100 und 100 %, im Zustand OK zu 70 % bei einer Grundrate von 72 %.

```bash
python3 vokabular.py auswertung messungen/koerper-reize-2026-11-05.csv --horizont 30 60
python3 vokabular.py auswertung messungen/koerper-reize-wdh-2026-11-05.csv --horizont 30 60
```

**Wechselnde Bedeutung, sechs Stunden.** Die Aufnahme mit dem Leckmuster, 21.600 Takte, an ihr wurde nichts gewählt. Alle Verfahren außer dem mit einem Takt Blick warnen jede der 252 Phasen vor, der Vorschlag Richtung bei 30 s eine weniger.

| Verfahren | Fehlalarme / Alarme, 30 s | Warnanteil | Trefferquote | Fehlalarme / Alarme, 60 s | Warnanteil | Trefferquote |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 102 / 358 | 44 % | 66 % | 61 / 358 | 44 % | 83 % |
| Grob, ein Takt (1 bzw. 3 von 252 vorgewarnt) | 2 / 3 | 0 % | 57 % | 0 / 3 | 0 % | 100 % |
| Grob, weiter Blick | 131 / 387 | 65 % | 50 % | 81 / 372 | 71 % | 68 % |
| Vokabular, weiter Blick | 130 / 387 | 65 % | 50 % | 82 / 371 | 71 % | 68 % |
| Vorschlag Richtung, weiter Blick | 153 / 415 | 68 % | 46 % | 55 / 351 | 83 % | 64 % |
| Je Signal | 134 / 393 | 63 % | 52 % | 85 / 375 | 69 % | 69 % |
| Immer warnen | 1 / 253 | 100 % | 38 % | 1 / 253 | 100 % | 64 % |

Je Signal bei 30 s: Die feste Regel warnt in 91, 89 und 95 % der warmen, knappen und zähen Takte, das eigene Gedächtnis je Signal in allen. Die feste Regel trifft dabei zu 38, 51 und 100 %, das Gedächtnis je Signal zu 38, 52 und 100 %. Im Zustand OK warnt das Gedächtnis je Signal in 34 % der Takte und trifft zu 18 %, bei einer Grundrate von 17 %.

Der Speicher ist das Signal mit wechselnder Bedeutung. Für ihn zählen nur die knappen Takte, getrennt nach tiefen und flachen Blöcken, Horizont 30 s. Richtig wäre, im tiefen Block zu warnen und im flachen nicht:

| Verfahren | warnt bei KNAPP, tiefer Block | flacher Block | Trefferquote | VOLL vorgewarnt |
|---|---:|---:|---:|---:|
| Feste Regel | 88 % | 90 % | 51 % | 56 / 56 |
| Je Signal, Erbe 3 wie bisher | 100 % | 100 % | 52 % | 56 / 56 |
| Je Signal, Erbe 2 oder 1 | 100 % | 100 % | 52 % | 56 / 56 |
| Je Signal ohne Erbe | 87 % | 12 % | 88 % | 49 / 56 |
| Zum Vergleich: wie der letzte Durchgang | 88 % | 12 % | 88 % | 49 / 56 |

Bei 60 s ändert sich nur die Zeile ohne Erbe, auf 88 %, 14 % und 87 %. Die Gegenproben mit kleinerem Erbe kamen erst nach dem Ergebnis dazu, an derselben Aufnahme. Sie zeigen die Ursache, eine unabhängige Bestätigung sind sie nicht.
- **Das Erbe überstimmt die Erfahrung.** Mit Erbe lernt kein Verfahren den Wechsel. Alle warnen im flachen Block so oft wie im tiefen und treffen zur Grundrate von 51 %. Die geschätzte Wahrscheinlichkeit für VOLL binnen 30 s fällt auch im flachen Block nie unter 0,95. Nachgerechnet am zwölften Durchgang, mitten im ersten flachen Block:
  - Das Erbe KNAPP → VOLL zählt immer drei Beobachtungen, es verblasst nie. Die eigene Erfahrung KNAPP → OK kommt nicht über 1,3, hier sind es 1,27. Denn die Halbwertszeit von 6 zählt jeden Takt, in dem KNAPP erlebt wird, auch die zwölf, in denen der Speicher knapp bleibt. Bis zum nächsten Ausgang ist ein Beleg auf ein Viertel gealtert, im letzten knappen Takt stehen noch 0,32. Schon das ergibt 3 zu 1,27, also 0,70 für VOLL.
  - Der Blick geht außerdem über OK zurück zu KNAPP. Die OK-Zeile trägt frisch den Eintritt in genau dieses Leck, OK → KNAPP 1,00 gegen OK → OK 8,17. Auch diese Wege enden über das Erbe in VOLL, aus 0,70 werden 0,95.
  - Auch ein Erbe von 1 überstimmt noch, im letzten knappen Takt steht es 1 zu 0,32.
- **Ohne Erbe folgt das Gedächtnis dem letzten Durchgang.** Es warnt in 87 % der knappen Takte tiefer Blöcke und in 12 % der flachen und trifft zu 88 statt 51 %. Je Durchgang entscheidet es genau wie die Regel „wie der letzte Durchgang“. Den ersten Durchgang jedes Blocks rät es deshalb falsch. Sieben von 56 VOLL-Phasen bleiben ohne Vorwarnung, die jeweils erste eines tiefen Blocks, darunter die allererste. Vor genau diesem ersten Mal soll das Erbe schützen.
- **Insgesamt bleibt die feste Regel vorn.** Ohne Erbe warnt das Gedächtnis je Signal nur in 27 % der ruhigen Takte und trifft zu 63 %, die feste Regel warnt in 44 % und trifft zu 66 %. Dafür bleiben 39 von 252 Phasen ohne Vorwarnung. Je Signal gezählt ist es vor allem Hitze: Von 98 Temperaturphasen sieht es 28 vorher, von 56 Lecks 49, von 141 Bremsphasen 140. Auf warm folgt hier nur zu 38 % binnen 30 s heiß, ohne Erbe bleibt die gelernte Wahrscheinlichkeit meist unter der Schwelle. Bei 60 s sind es 39 % Warnanteil und 70 % Treffer gegen 44 und 83 %, mit 242 von 252 Phasen vorgewarnt.

**Entschieden am 6. November: Das Erbe wird ein verblassender Startwert.** Offen standen zwei Wege: das Erbe als Startwert, der mit eigenen Ausgängen schwindet, oder Verweildauer und Richtung getrennt lernen. Alex wählte den ersten, der zweite ist nicht verworfen, nur nicht gewählt. Die neue Regel `startwert` beginnt mit demselben Erbe von drei Beobachtungen. Mit jedem eigenen Ausgang aus seinem Zustand verblasst es um den Faktor der Kontextregel, also mit einer Halbwertszeit von sechs Ausgängen. Bleiben zählt nicht, es sagt nichts darüber, wohin der Zustand führt. Auch ein Ausgang in den Ausfall zählt, dann trägt eigene Erfahrung die Warnung. Die Sechs ist von der Kontextregel übernommen und nicht an diese Aufnahme angepasst. Die Regel `erbe` bleibt, wie sie war. Daniels Verbund und Systemversuch rechnen weiter mit ihr.

- **Umgesetzt** in kern.py als `Startwertgedaechtnis` (Regel 4), im Sketch als Variante `esp32s3-startwert` mit dem Gerätestand `AG02` und in vokabular.py als `Wortgedaechtnis(..., startwert=True)`. Die Auswertung zeigt dafür die Zeilen „Grob, Startwert“ und „Je Signal, Startwert“. Der Hosttest rechnet alle vier Regeln bitgleich mit Python, auch über einen Neustart. Als Gegenprobe übersprang eine Firmware probehalber das gesicherte Erbe beim Laden, der Vergleich mit dem durchgehenden Lauf schlug an. 94 Tests grün. Auf dem S3 läuft die Variante seit dem 6. November, Ergebnis unten unter „Am Gerät, 30 Minuten“.
- **Nachgerechnet an derselben Aufnahme**, eine unabhängige Bestätigung ist das nicht:

| Verfahren, 30 s | vorgewarnt | Warnanteil | Trefferquote | Wärme | Speicher | Schleife |
|---|---:|---:|---:|---:|---:|---:|
| Feste Regel | 252 / 252 | 44 % | 66 % | 98 / 98 | 56 / 56 | 141 / 141 |
| Grob, Erbe fest (so rechnet das Gerät heute) | 252 / 252 | 65 % | 50 % | 98 / 98 | 56 / 56 | 141 / 141 |
| Grob, Startwert | 157 / 252 | 28 % | 45 % | 73 / 98 | 40 / 56 | 81 / 141 |
| Je Signal, Erbe fest | 252 / 252 | 63 % | 52 % | 98 / 98 | 56 / 56 | 141 / 141 |
| Je Signal, Startwert | 218 / 252 | 29 % | 64 % | 32 / 98 | 51 / 56 | 141 / 141 |
| Immer warnen | 252 / 252 | 100 % | 38 % | 98 / 98 | 56 / 56 | 141 / 141 |

Bei 60 s warnt die feste Regel in 44 % der Takte und trifft zu 83 %. Je Signal mit Startwert sind es 40 und 70 % bei 243 von 252 Phasen, die Wärme 49 von 98. Grob mit Startwert sind es 42 und 63 % bei 212 von 252.
- **Der Speicher lernt die Ausnahme.** Je Signal warnt der Startwert in den knappen Takten der tiefen Blöcke zu 90 %, in den flachen zu 26 % statt 100 %, und trifft zu 79 statt 52 %. Durch den ersten flachen Block trägt ihn das Erbe noch, ab dem zweiten folgt er dem letzten Durchgang. Den ersten Ausfall der fünf späteren tiefen Blöcke sieht er nicht kommen, 51 von 56 VOLL-Phasen sind vorgewarnt. Mit einer Halbwertszeit von drei Ausgängen wiche das Erbe schon im ersten flachen Block, dann wären 15 % der flachen Takte gewarnt und 87 % Treffer, dafür bliebe ein Ausfall mehr unangekündigt.
- **Die Wärme verliert ihre Warnung.** Auf warm folgt binnen 30 s nur zu 38 % heiß. Das lernt der Startwert und bleibt meist unter der Schwelle von 60 %. Bisher hielt das feste Erbe diese Warnungen. Ob 38 % eine Warnung wert sind, entscheidet die Schwelle, nicht das Gedächtnis.
- **Im groben Blick des Geräts kostet der Startwert.** SCHWACH steht dort für warm, knapp und zäh zugleich. Ohne festes Erbe mischt die Zeile die meist harmlose Wärme mit der Bremse, die immer bis zum Stillstand geht. So sind nur 81 von 141 Bremsphasen vorgewarnt. Der Startwert zahlt sich erst mit einem Gedächtnis je Signal aus, und das rechnet bisher nur der Rechner.
- **Die Wiederholung der Reizstunde** (3.600 Takte, jedes Leck tief) zeigt dasselbe. Je Signal mit Startwert sind bei 30 s Speicher und Schleife vollständig vorgewarnt, die Wärme in 7 von 20 Phasen, insgesamt 30 von 36 bei 52 % Warnanteil und 69 % Treffern. Die feste Regel warnt 36 von 36 vor, bei 55 % und 73 %.

**Am Gerät, 30 Minuten.** Am 6. November von 07:59 bis 08:29 lief `esp32s3-startwert` auf dem S3 mit den Reizen des 6-Stunden-Laufs, nur 1.800 statt 21.600 Takte. Vorher bestand er die Demo mit 240 von 240 Antworten. Alle 1.800 Einstufungen und Entscheidungen stimmen mit Python überein, einen Neustart gab es nicht. Die neun Lecks liefen nach Muster, acht tief und eines flach, danach waren je 363.364 Byte frei. Die zwölf Bremsrampen erreichten je 299,8 ms, der Chip lag bei 35 bis 39 °C. Gezählt bei 60 s, dem Blick des Geräts:

| Verfahren, 60 s | vorgewarnt | Fehlalarme / Alarme | Warnanteil | Trefferquote |
|---|---:|---:|---:|---:|
| Gerät mit Startwert | 24 / 24 | 7 / 35 | 59 % | 77 % |
| Festes Erbe, an derselben Aufnahme nachgerechnet | 24 / 24 | 7 / 34 | 73 % | 79 % |
| Feste Regel | 24 / 24 | 5 / 32 | 50 % | 91 % |
| Immer warnen | 24 / 24 | 1 / 25 | 100 % | 74 % |

Das Gerät warnte 886-mal. In den ersten 30 Minuten des 6-Stunden-Laufs mit festem Erbe waren es 1.160 Warnungen. Die Nachrechnung hatte dieselbe Richtung vorhergesagt: an jener halben Stunde 66 statt 79 % Warnanteil bei 81 statt 84 % Treffern. In einer halben Stunde ist das Erbe erst wenig verblasst, und der Speicher hatte nur einen flachen Durchgang. Was der Startwert über Stunden bringt und kostet, zeigt erst ein längerer Lauf.

**Wiederanlauf mit `AG02`.** Danach sicherte das Gerät nach 111 Takten der Demo. Dort steht das Erbe bei 0,375, und ein beim Laden auf 3 hängengebliebenes Erbe würde eine spätere Entscheidung ändern. Das trifft auf 102 der 161 möglichen Grenzen zu, ein auf null gefallenes Erbe auf keine. Nach einer Stromtrennung lud es den Stand und wies Takt 111 ab. Die übrigen 129 Antworten entsprachen dem durchgehenden Lauf.

```bash
python3 koerper.py pruefen messungen/koerper-startwert-30min-2026-11-06.csv
python3 vokabular.py auswertung messungen/koerper-startwert-30min-2026-11-06.csv --horizont 30 60
python3 wiederanlauf.py sichern --port /dev/PORT --regel startwert --grenze 111
python3 wiederanlauf.py laden --port /dev/PORT --regel startwert --grenze 111
```

**Offen: Wie geht es mit dem Gerät weiter?** Drei Möglichkeiten, noch nicht gewählt:
- Den Startwert länger laufen lassen, wie er ist. Das prüft die Nachrechnung unabhängig. Laut Nachrechnung warnt das Gerät damit über Stunden schlechter als heute.
- Erst ein Gedächtnis je Signal ins Gerät bringen, jedes mit Startwert. Das ist ein größerer Umbau des Sketchs.
- Die Wärme gesondert ansehen. Bei 38 % Folgewahrscheinlichkeit entscheidet allein die Schwelle von 60 %, ob gewarnt wird.

```bash
python3 vokabular.py auswertung messungen/koerper-muster-6h-2026-11-05.csv --horizont 30 60
```

Die Trennung nach Blöcken und die Gegenproben sind nicht Teil von `vokabular.py`. Sie liefen mit dessen Funktionen: `warnungen` über die Speicherstufen aus `stufen_je_signal`, mit `Wortgedaechtnis(..., erbe=…)`, beim Startwert mit `startwert=True`. Die Halbwertszeit von drei Ausgängen lief nur zum Vergleich, als Unterklasse außerhalb des Labors. Tief ist ein Leckdurchgang, wenn der Speicher dabei VOLL erreicht.

## Kommunikationsversuch und nächste Entscheidung

`transport.py` spielt einem Sender und einem Empfänger dieselbe logische Uhr vor. Ein Statuspaket besteht aus vier Byte Takt in Big Endian und einem Byte Zustand. OK, SCHWACH und AUSFALL haben die IDs 1–3, Vorwarnung die ID 4. Der Zustandskanal akzeptiert nur die ersten drei. Doppelte, verspätete oder zukünftige Pakete verändern den Empfängerstand nicht. Der Versuch verwendet eine bekannte Sitzung mit genau einem Sender. Bei realen Neustarts und mehreren Knoten muss die Gegenstelle Sender und Sitzungen unterscheiden, bevor sie Sequenznummern vergleichen kann.

Der Herzschlag trägt den aktuellen Zustand. Nach zehn Takten ohne gültige Meldung wird er beim Empfänger unbekannt. Protokolliert werden gesendete Nutzbytes, empfangene Pakete, falsche und unbekannte Takte sowie der erste tatsächlich sichtbare Ausfall. Vorwarnungen werden in diesem Teilversuch nicht übertragen. Bei Totalausfall der Leitung kann ein Empfänger die Ursache der Stille nicht feststellen. Ein zweiter Meldeweg oder ein später auslesbares lokales Ereignisprotokoll wäre dafür ein eigener, messbarer Versuch.

**Abnahme der nächsten Etappe.** Ein physischer Knoten soll die Referenzspur und den Wiederanlauftest bestehen. Die Referenzspur hat Alex’ ESP32-S3 am 5. November in allen drei Varianten bestanden, den Wiederanlauf nach Stromtrennung in der Erbe-Variante. Auf einer getrennten Feldaufzeichnung sollen Alex und Claude danach die Zahl nützlicher Vorwarnungen, Fehlwarnungen, verpasster Ausfälle, offene Warnungen und die tatsächlich verfügbare Reaktionszeit berichten. Erst mit dieser Messung lässt sich entscheiden, welche Gedächtnisregel und welcher Meldetakt in Alex’ Alltag sinnvoll sind.

**Offene Grundsatzfrage.** Laut Ideensammlung steigt die Stärke einer Erinnerung bei jedem Abruf. Hier verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel. `test_abrufen_verstaerkt_keine_vermutung` sichert das ab. Ein möglicher Ausgleich wären zwei Werte pro Eintrag: ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf. Die Entscheidung liegt bei Alex. Vor einem zweiten echten Knoten braucht das Fünf-Byte-Paket außerdem eine Sender- und Sitzungskennung.
