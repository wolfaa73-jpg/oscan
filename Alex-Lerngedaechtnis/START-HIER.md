# Alex’ Lernlabor

**Stand 0.5 · 5. November 2026 · Arbeitsprojekt für Alex und Claude**

Wann sollte ein kleiner Knoten eine Erfahrung vergessen? Dieses Labor setzt drei Gedanken aus Alex’ Entwurf zusammen. Ein fester Reflex meldet einen beobachteten Ausfall. Neun veränderliche Gewichte lernen, welcher Zustand auf welchen folgt. Ein zweiter Knoten kann über kurze Zustandsmeldungen erfahren, was der erste beobachtet hat. Seit Version 0.3 bringt ein siebtes Verfahren ein kleines festes Erbe mit, das eigene Erfahrung überstimmen kann.

Das Konzept steht in Alex’ Ideensammlung eine Ordnerebene höher (`../Ideensammlung Lernendes Betriebssystem mit verblassendem Gedächtnis.md`). Sie ist die maßgebliche Fassung. Ihr Abschnitt „Versuchsstand“ hält fest, was dieses Labor gezeigt hat.

## In zwei Minuten ausprobieren

1. **Bericht.html** per Doppelklick öffnen. Die Grafik zeigt den Moment, in dem der Knoten anfängt zu warnen, und den Moment, in dem er seine Meinung ändert. Darunter stehen die Ergebnisse für sechs unterschiedliche Bedingungen.
2. Im Terminal im entpackten Ordner die ursprüngliche Demo starten. Python 3.9 oder neuer genügt.

```bash
python3 versuch.py
python3 transport.py
python3 -B -m unittest -v
```

Der erste Lauf zeigt, was der Knoten vorhersagt. Der zweite zeigt, was ein anderer Knoten tatsächlich erfahren würde, wenn eine Nachricht verloren geht. Die vollständigen Tests brauchen zusätzlich einen C++11-Compiler. Ohne ihn werden die Sketch-Tests als übersprungen gekennzeichnet.

## Was wir gelernt haben

**Seltenes Wissen braucht eine eigene Uhr.** Das erste Gedächtnis halbiert Belege alle 24 Takte. Im neuen Verfahren halbieren sie sich erst nach sechs weiteren beobachteten Folgen desselben Ausgangszustands. Eine lange Zeit ohne schwaches Signal löscht damit die Erfahrung über schwache Signale nicht. Eine neue Beobachtung kann sie aber korrigieren. Andere Halbwertszeiten ändern das Bild kaum. Die Zeitregel holt bei seltenem Vorzeichen erst bei sehr langen Halbwertszeiten auf, die Kontextregel hängt kaum davon ab (`python3 labor.py --halbwertszeiten`).

Im Kontrollversuch bestand jedes Szenario aus 20 eigenständigen Spuren mit je 480 Takten. Jede Zelle zeigt **richtige Vorwarnungen / Fehlwarnungen**. Die vollständigen Zahlen einschließlich verpasster Ausfälle und Datenmenge stehen im Bericht.

| Bedingung | Feste Regel | Lernen ohne Verblassen | Verblassen nach Zeit | Verblassen je Kontext | Erbe und Kontext |
|---|---:|---:|---:|---:|---:|
| Stabiles Vorzeichen | 1779 / 321 | 1720 / 312 | 1682 / 302 | 1693 / 308 | 1779 / 321 |
| Seltenes, meist verlässliches Vorzeichen | 170 / 38 | 113 / 29 | 0 / 0 | 94 / 24 | 169 / 38 |
| Vorzeichen verliert seine Bedeutung | 952 / 1371 | 853 / 615 | 809 / 194 | 819 / 210 | 900 / 269 |
| Alte Bedeutung kehrt zurück | 1237 / 998 | 574 / 417 | 930 / 230 | 928 / 242 | 1088 / 319 |
| Bedeutung ändert sich nach langer Stille | 641 / 932 | 553 / 415 | 513 / 87 | 523 / 159 | 603 / 216 |
| Kein Vorzeichen | 219 / 2119 | 0 / 0 | 0 / 0 | 0 / 0 | 10 / 64 |

Die Schwierigkeit beim Vergessen ist die Wahl des richtigen Maßstabs. Eine lange Pause liefert keine neuen Hinweise darauf, ob ein Zusammenhang noch gilt. Wer das frühere Wissen bewahrt, kann beim seltenen Wiedersehen sofort reagieren. Hat sich während der Pause etwas geändert, warnt derselbe Knoten zunächst zu oft. Für dauerhaft wichtige Ereignisse bleibt die Sofortmeldung deshalb eine feste Regel.

**Ein kleines Erbe ersetzt den Anlauf, ein großes wird zum Vorurteil.** „Erbe und Kontext“ beginnt mit drei festen Beobachtungen „SCHWACH → AUSFALL“. Drei ist der Mindestbeleg einer Warnung, das Erbe trägt also ab dem ersten schwachen Signal. Es verblasst nie, eigene Erfahrung kann es aber überstimmen. Auf leerem Gedächtnis genügen dafür drei beobachtete Folgen „SCHWACH → OK“. Wo das Erbe stimmt, warnt der Knoten so oft richtig wie die feste Regel. Verliert das Vorzeichen seine Bedeutung, behält er 95 % ihrer richtigen Vorwarnungen bei einem Fünftel ihrer Fehlwarnungen. Ohne Vorzeichen kostet das Erbe 64 Fehlwarnungen, die feste Regel 2119. Mit zwölf festen Beobachtungen wären es 1325 (`python3 labor.py --erbe-reihe`). Der Entwicklungssatz zeigt dasselbe Bild.

**Der eigene Körper kann das Erbe widerlegen.** Unter Last wärmt sich der S3 langsam von 36 auf 38 bis 39 °C. Auf „warm“ folgt im nächsten Takt fast nie „heiß“. Der Knoten mit Erbe warnt deshalb dreimal wie mitgegeben, dann haben ihn drei eigene Folgen „SCHWACH → SCHWACH“ überstimmt. Die feste Regel warnt weiter bei jedem warmen Takt. Für träge Signale ist ein Takt Vorhersage zu kurz.

**Mit weiterem Blick bestätigt dieselbe Erfahrung das Erbe, schlägt die feste Regel aber nicht.** `vokabular.py` gibt dem Knoten zehn feste Wörter mit Nummer, Oberbegriff und Bedeutung. Für eine Vorwarnung denkt es seine gelernte Tabelle bis zu 30 oder 60 Takte weiter. Im sechsstündigen Mitschnitt unter Last kündigt es so jede Hitzephase an. Es warnt bei jedem warmen Takt wie die feste Regel und dazu in vielen OK-Takten. Nach Warnläufen gezählt sah das zuerst besser aus als die feste Regel, doch so gezählt hätte auch „immer warnen“ nur einen Fehlalarm. Je Takt gezählt bleibt die feste Regel vorn. Gemessen auf den 114 Phasen nach den ersten 41 Minuten, an denen die Blickweite gewählt wurde: Bei 60 s Horizont folgt auf 60 % ihrer Warntakte Hitze, beim gelernten Blick auf 48 % und bei immer warnen auf 50 % (UEBERGABE.md). Drei Zustände verraten nicht, ob nach einem OK die nächste Hitze nah ist.

**Ein Wort je Takt verdeckt das zweite Signal.** In einer Stunde mit Last, Leck und Bremse kündigen sich Speicher und Schleife immer an, die Wärme nur zu 61 %. Feste Regel und Gedächtnis warnen bei allen dreien gleich, und das feine Vokabular entscheidet wie das grobe. Fällt eine Bremse in eine Hitzephase, zählt das schwerere Wort, und ihr Vorzeichen geht unter. Wer wissen will, was als Nächstes ausfällt, braucht einen Zustand je Signal. Ein eigenes Gedächtnis je Signal warnt deshalb bei jedem eigenen Vorzeichen, auch unter Hitze, und sah die verdeckte Bremsphase vorher. Nach 54 Minuten setzte ihn ein anderes Programm zurück, das am selben USB nach einem anderen Gerät suchte, seitdem belegt der Rekorder den Port exklusiv.

**Das Erbe verblasst nie, und so lernt das Gedächtnis keine Ausnahme.** In sechs Stunden wurde knapper Speicher acht Durchgänge lang voll, die nächsten acht nicht, im Wechsel. Kein Verfahren lernt das. Alle warnen im flachen Block wie im tiefen und treffen nur die Grundrate von 51 %. Das Erbe „auf knapp folgt voll“ zählt immer drei Beobachtungen. Die eigene Erfahrung „auf knapp folgt frei“ kommt nicht über 1,3, denn jeder Takt, in dem der Speicher knapp bleibt, lässt sie altern. In einer Gegenprobe ohne Erbe, an derselben Aufnahme nachgerechnet, folgt das Gedächtnis dem letzten Durchgang und trifft zu 88 %. Dann bleibt aber der erste Ausfall jedes Blocks ohne Vorwarnung, und vor genau diesem ersten Mal soll das Erbe schützen. Seit dem 6. November gibt es deshalb eine vierte Regel, in der das Erbe als Startwert verblasst (siehe unten).

**Eine gesendete Meldung ist noch keine empfangene Meldung.** Im zweiten Versuch dauert der Ausfall 20 Takte. Geht genau die erste Ausfallmeldung verloren, übersieht das reine Melden von Zustandswechseln den gesamten Ausfall. Mit einer zusätzlichen Zustandsmeldung spätestens alle fünf Takte erfährt die Gegenstelle in Takt 11 vom Ausfall in Takt 6. Dafür sendet der Knoten im 36-Takt-Versuch 40 statt 15 Nutzbytes. Beim Senden in jedem Takt wären es 180. Bei vollständiger Funkstille kann die Gegenstelle nur kenntlich machen, ab wann ihr letztes Wissen zu alt ist.

## Was jetzt benutzbar ist

- **Eine eigene Messung.** Ein Python-Werkzeug prüft die TCP-Erreichbarkeit eines eigenen Dienstes und speichert Zeit, Verbindungsdauer und Ergebnis. Die beigefügte lokale Aufzeichnung enthält sechs erfolgreiche und sechs abgelehnte Verbindungen nach einem absichtlichen Stopp.
- **Ein Gedächtnis mit Neustart.** Alle vier Lernregeln (Zeit, Kontext, Erbe, Startwert) können ihren Zustand auf dem Rechner sichern und mit absoluten Takten fortsetzen. Messlücken erzeugen keine erfundenen Übergänge. Der ESP32-Sketch hat eigene Befehle zum Sichern und Laden. Das Erbe gehört zur Regel. Ein Stand mit abweichendem Erbe wird beim Laden abgewiesen, beim Startwert darf es verblasst, aber nicht gewachsen sein. Seit dem 6. November lernt der S3 auch über Körperaufnahmen hinweg weiter: `--sichern-alle` lässt ihn regelmäßig sichern, `--fortsetzen` mit dem Stand der vorigen Aufnahme beginnen, und `pruefen` rechnet die ganze Kette nach.
- **Vier übersetzte Firmwarevarianten.** Zeit, Kontext, Erbe und seit dem 6. November Startwert wurden für den klassischen ESP32 (`esp32dev`) und für Alex’ ESP32-S3-N16R8 (`esp32s3`) gebaut. Der identische Sketchcode wurde im Hosttest pro Variante über 57.840 Beobachtungen mit Python verglichen. Für einen physischen Lauf liegt ein serieller Prüfer bei. Seit 0.3 übersteht er einen langsamen Start, bei dem das Board wiederholte Neustartbefehle alle beantwortet. Auf Alex’ ESP32-S3 bestanden die ersten drei Varianten am 5. November die Demo mit 240 von 240 Antworten. Die Erbe-Variante behielt ihren Lernstand über eine Stromtrennung. Der Startwert bestand die Demo am 6. November, lief 30 Minuten im Körpermodus und behielt sein verblasstes Erbe über eine Stromtrennung.
- **Körpersignale.** Seit 0.4 misst der S3 im Körpermodus in eigenem Takt Chiptemperatur, freien Speicher und Schleifenlücke, stuft sie ein und lernt damit. `koerper.py` zeichnet auf und rechnet jede Entscheidung nach. Mit `--last` arbeitet Kern 0 in einem Rhythmus und wärmt den Chip, die eingebaute LED zeigt den Zustand. Seit 0.5 machen `--leck` und `--bremse` dem Knoten auch Speicher und Hauptschleife knapp, und `--blick` lässt ihn seine Vorwarnung bis zu 600 Takte vorausdenken. Auf dem S3 entscheidet er dabei in jeder Probe wie Python, auch mit nur 13.860 Byte freiem Speicher. 600 Takte Vorausschau kosten ihn 2,6 ms je Takt.
- **Ein Vokabular.** `vokabular.py` legt zehn Wörter fest und wertet Körperaufnahmen mit weiterem Blick aus. Die Wörter gibt es bisher nur auf dem Rechner, das Gerät spricht weiter OK, SCHWACH und AUSFALL. Den weiten Blick über diese drei rechnet es seit 0.5 selbst.
- **Zwei Teilversuche von Daniel.** `verbund.py` gibt jeder Meldung Knotennummer, Sitzung und Abfragerunde, `Verbund.html` zeigt einen gestörten Lauf. `systemkern.py` lässt einen festen Disponenten Aufträge an zwei echte Arbeiterprozesse verteilen, `Systembericht.html` vergleicht die Regeln mit Kosten. Einstieg in `SYSTEM-UEBERGABE.md` und `VERBUND-UEBERGABE.md`. Seit dem 6. November sind auch Anschluss, Auftragsjournal und Arbeiter-Wiederanlauf übernommen (`ANSCHLUSS-`, `JOURNAL-` und `WIEDERANLAUF-UEBERGABE.md`). Rechenaufgaben, bei denen Daniel weiterhelfen kann, stehen in `RECHEN-UEBERGABE.md`.
- **Ein reproduzierbarer Übergabestand.** 174 automatisierte Tests waren erfolgreich, 107 davon aus Daniels Teilversuchen, gestartet im Laborordner. Von außerhalb findet ein Kindprozess in `test_auftragsjournal.py` sein Modul nicht. Der Versuchsbericht läuft offline. Quellcode, Messdateien und eine eingefrorene Kopie der Originalnotizen liegen im Ordner, die Lieferungen 0.1 und 0.2 unter `../archiv`.

## Womit Alex und Claude weitermachen sollten

**Zuerst einen realen Fall wählen, in dem ein Takt Vorwarnzeit eine Handlung ermöglicht.** Ein Beispiel wäre der Wechsel auf einen zweiten Meldeweg, bevor ein Dienst unerreichbar wird. Alex legt fest, wie teuer eine unnötige Umschaltung und wie teuer ein verpasster Ausfall ist. Claude kann dann alle sieben Verfahren auf derselben echten Spur vergleichen. Die Demo, die der Rechner bereits ausgewertet hat, besteht das Gerät inzwischen, auch über eine Stromtrennung hinweg (`wiederanlauf.py`).

**Offen ist eine Grundsatzfrage.** Laut Ideensammlung steigt die Stärke einer Erinnerung bei jedem Abruf. Im Labor verändert ein Abruf nichts, und ein eigener Alarm zählt nie als Lernbeispiel. Ein möglicher Ausgleich wären zwei Werte pro Eintrag: ein Beleg, der nur durch Beobachtung wächst, und ein Behalten, das durch Nutzung wachsen darf. Die Entscheidung liegt bei Alex.

**Entschieden: Das Erbe wird ein verblassender Startwert.** Alex wählte am 6. November den ersten von zwei Wegen. In der neuen Regel `startwert` verblasst das Erbe mit jedem eigenen Ausgang aus seinem Zustand. Rechner und Firmware rechnen sie bitgleich. Auf dem S3 entschied sie 30 Minuten lang wie Python und warnte seltener als mit festem Erbe, bei fast gleicher Trefferquote. Am 6-h-Lauf nachgerechnet lernt das Gedächtnis je Signal damit die Ausnahme beim Speicher und trifft zu 79 statt 52 %. Die meisten Hitzewarnungen fallen dafür weg, weil auf warm nur selten heiß folgt. Im groben Blick des Geräts kostet der Startwert Vorwarnungen, er zahlt sich erst mit einem Gedächtnis je Signal aus. Wie es mit dem Gerät weitergeht, steht in UEBERGABE.md unter „Wechselnde Bedeutung“. Auch hier entscheidet Alex.

Die Befehle, Dateiformate, Abnahmekriterien und ein Einstiegsprompt stehen in **UEBERGABE.md**. **Ideensammlung-original.md** ist die eingefrorene Fassung vom 4. November, auf der Version 0.2 aufbaut.
