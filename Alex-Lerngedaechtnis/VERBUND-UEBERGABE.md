# OSCan · Verbundversuch 1

Stand 5. November 2026. Ausgangspunkt dieses Teilversuchs war Alex’ OSCan 0.3, Git-Commit `8f823824aede3134677a449a2a55bb639976e4e7`.

Dieser Teilversuch ist auf [OSCan 0.4, Commit `91b2435`](https://github.com/wolfaa73-jpg/oscan/commit/91b24356d1011667f76cfe664effaf7fe2688c0b) geprüft und Bestandteil der gemeinsamen Systemübergabe. Einstieg in den aktuellen Gesamtstand: [SYSTEM-UEBERGABE.md](SYSTEM-UEBERGABE.md). Das ältere lokale Archiv `uebergabe-verbund-1` bleibt als eigenständiger Stand auf Basis 0.3 erhalten.

Dieser Versuch setzt bei der offenen Absenderfrage aus der Ideensammlung an. Zwei Knoten können denselben lokalen Messtakt verwenden oder ihre Zähler nach einem Neustart neu beginnen. Die Gegenstelle braucht deshalb eine eindeutige Zuordnung und einen Maßstab dafür, wie frisch ihr Wissen ist.

## Zuerst ansehen

`Verbund.html` per Doppelklick öffnen. Die Zeitleiste lässt sich mit Maus oder Tastatur bedienen. Takt 16 zeigt einen unerreichbaren Knoten neben einem weiterhin erreichbaren. In Takt 22 kommt eine Nachricht aus einer alten Sitzung an. In Takt 30 wird die Zentrale neu zugeordnet. Die Gedächtnistabellen stammen aus dem lokalen Prüfprotokoll der Simulation. Das Datenpaket überträgt Messtakt, Zustand und Warnflags.

Im Laborordner ausführen.

```bash
python3 verbundlabor.py
python3 verbundlabor.py --bericht Verbund-neu.html --json verlauf.json
python3 verbundlabor.py --udp
python3 -B -m unittest -v
```

Python 3.9 oder neuer genügt für den neuen Versuch. Die bestehenden Sketch-Prüfungen benötigen einen C++11-Compiler. Die UDP-Probe startet zwei eigene Prozesse und öffnet nur lokale Ports auf 127.0.0.1. Beide Prozesse beenden sich nach dem Versuch. Die Anzeige selbst benötigt weder einen Server noch Internetzugang.

## Was gebaut wurde

| Datei | Aufgabe |
|---|---|
| verbund.py | Binärformat, Knotenadapter und Zentrale mit Sitzungen und Fristen |
| verbundlabor.py | Aufgezeichneter Fehlerlauf, lokaler UDP-Lauf und Berichtserzeugung |
| verbund-vorlage.html | Darstellung und Zeitleiste des Berichts |
| Verbund.html | Bereits erzeugte, allein lesbare Aufzeichnung |
| test_verbund.py | Regressionen für Zuordnung, Zeit, Wiederholung und Paketfehler |
| beispiele/verbund-pakete.json | Drei vollständige Hex-Beispiele für die Portierung auf andere Sprachen |
| beispiele/verbund-udp.json | Ergebnis des tatsächlich ausgeführten lokalen Prozessversuchs |

Der Knotenadapter benutzt `Knoten` und `REGELN` aus Alex’ vorhandenem `kern.py`. Die Quelle ist eine Funktion, die bei einer neuen Abfrage einen absoluten lokalen Messtakt und einen Zustand liefert. Eine Wiederholung derselben Frage bekommt dieselbe gespeicherte Antwort. So erzeugt ein Übertragungsretry keine zusätzliche Erfahrung. Jede neue Frage sammelt genau eine neue Beobachtung. Die neue Erfassung ist daher abfragegetrieben. Ein unabhängig laufender Sensor braucht bei der späteren Integration einen eigenen Zeit- und Puffervertrag.

## Entscheidungen im Entwurf

Die Zentrale kennt die zugelassenen Knotennummern. Der Betreiber beziehungsweise die lokale Versuchsteuerung ordnet einer Verbindung mit `anmelden()` eine frische Sitzung zu. In normalen Läufen wird sie zufällig mit UUID4 erzeugt. In der deterministischen Simulation werden festgelegte, pro Anmeldung neue Werte verwendet. Eine empfangene Datenmeldung kann diese Zuordnung nicht verändern. Eine über das Netz ausgehandelte Aufnahme neuer Geräte bleibt ein eigener Schritt.

Jede Abfrage erhält eine aufsteigende Rundennummer. Eine Meldung ist nur gültig, wenn Nummer des Knotens, Sitzung und Runde zur offenen Abfrage passen. Ein neu gestarteter Knoten erhält eine neue Sitzung. Auch nach einem Neustart der Zentrale werden für beide Seiten neue Sitzungen eingerichtet. Bereits verwendete Kennungen dürfen nicht aus einem alten Stand übernommen werden. Ein alter Datensatz darf das Wissen einer neuen Verbindung dadurch nicht überschreiben.

Die Fristen werden ausschließlich mit der monotonen Uhr des Empfängers gemessen. Der Zustand altert ab Versand der Abfrage. Eine um 0,6 Einheiten verspätete Antwort ist deshalb bereits 0,6 Einheiten alt. Der lokale Messtakt des Knotens dient der Reihenfolge seiner Beobachtungen. In der Simulation beginnt Knoten 2 absichtlich mit einem um 10.000 höheren Messtakt.

Ein vollständig abgelaufener Zustand wird als unbekannt dargestellt. Das unterscheidet die fehlende Kommunikation von einem ausdrücklich beobachteten Ausfall des Sensors. Die letzten Warnflags werden mit dem Zustand ungültig. Eine Vorwarnung bezieht sich auf den nächsten **lokalen Messtakt** des sendenden Knotens. Vor einer echten automatischen Reaktion muss feststehen, wann dieser Messtakt stattfindet und ob noch genügend Zeit zur Reaktion bleibt.

Die Knotennummer und die UUID ordnen Daten zu. Die CRC erkennt Übertragungsfehler. Ein absichtlicher Angreifer kann beides nachbilden. Für offene oder fremde Netze braucht es einen authentifizierten Transport und eine geregelte Aufnahme der Geräte. Die lokale Probe setzt bekannte Prozesse voraus.

## Datenformat OC, Version 1

Alle Mehrbyte-Ganzzahlen werden in Netzwerkreihenfolge, Big Endian, übertragen. Ein vollständiges Datagramm hat 36 Byte.

| Byteposition | Länge | Inhalt |
|---|---:|---|
| 0–1 | 2 | Kennung OC |
| 2 | 1 | Formatversion 1 |
| 3 | 1 | Art, 0 Abfrage oder 1 Meldung |
| 4–5 | 2 | Knotennummer, 1 bis 65535 |
| 6–21 | 16 | Frische Sitzungskennung, 128 Bit |
| 22–25 | 4 | Abfragerunde, 1 bis 2³²−1 |
| 26–29 | 4 | Lokaler Messtakt, bei einer Abfrage 0 |
| 30 | 1 | Zustand, 1 OK, 2 SCHWACH, 3 AUSFALL, bei Abfrage 0 |
| 31 | 1 | Bit 0 Vorwarnung, Bit 1 Sofortmeldung, sonst 0 |
| 32–35 | 4 | CRC32 über Byte 0 bis 31 |

Die Datei `beispiele/verbund-pakete.json` enthält vollständige Bytefolgen für eine Abfrage, eine Vorwarnung und eine Ausfallmeldung. Damit kann eine zweite Implementierung ihre Ausgabe bytegenau vergleichen.

Abfragen tragen keine Messdaten. Eine Meldung braucht einen positiven Messtakt. Ein beobachteter Ausfall kann keine Vorwarnung für seinen eigenen Beginn tragen. Der Rundenzähler läuft nicht über. Bei Erreichen seiner Grenze muss eine neue Sitzung eingerichtet werden. Pro Knoten hält die Zentrale eine offene Runde und den zuletzt bestätigten Zustand. Alle Methoden der Zentrale gehören in einen gemeinsamen Ereignisablauf. Mehrere Threads müssten ihre Zugriffe extern synchronisieren.

Eine reguläre Runde überträgt 36 Byte Frage und 36 Byte Antwort. Netz- und Funkrahmen kommen hinzu. Die Fristen und die 128-Bit-Kennung sind explizite Entwurfsentscheidungen. Das Labor misst damit zuerst die korrekte Zuordnung. Eine spätere Verkleinerung sollte gegen dieselben Fehlerproben geprüft werden.

## Durchgeführte Prüfungen

Am 5. November wurden alle 52 Tests erfolgreich ausgeführt. Darin enthalten sind die 37 Prüfungen des GitHub-Ausgangsstands und 15 neue Tests. Die neuen Tests verändern unter anderem jedes der 288 Bits eines Statuspakets einzeln. Jede solche Beschädigung wird erkannt. Vierzig reproduzierbare Zufallsfolgen mit je zwei Knoten und vierzig Runden prüfen Verspätung, Wiederholung und Verlust. Eine alte Nachricht darf einen veralteten Zustand nicht wiederbeleben.

Die Anzeige wurde in Chrome bei 390 und 1150 Pixel Breite geprüft. Tastaturbedienung, Rücksetzen, Abspielen und Pause funktionieren. Beide Breiten bleiben ohne horizontalen Seitenüberlauf.

Der deterministische Fehlerlauf ergibt 120 Fragen, 114 erzeugte Antworten und vier zusätzlich eingespielte Paketkopien. 112 Antworten werden angenommen. Sechs Meldungen werden wegen Duplikat, Beschädigung, alter Sitzung, alter Runde oder abgelaufener Antwortfrist verworfen. Sechs Fragen gehen im simulierten Kanal verloren. Die modellierte Protokolldatenmenge beträgt 8.568 Byte. Knoten 1 ist in Takt 15 bis 18 für die Zentrale unbekannt. Knoten 2 bleibt in dieser Phase erreichbar.

Die separate UDP-Probe verwendet zwei echte Knotenprozesse auf demselben Rechner. Alle 480 Antworten stimmen in Messtakt, Zustand, Vorwarnung und Sofortmeldung mit der Python-Referenz überein. Über die lokalen Sockets wurden 34.560 Byte dieses Protokolls versendet. Die Ergebnisse stehen in `beispiele/verbund-udp.json`. Ein physischer ESP32-zu-Pi-Verbund ist noch zu prüfen. Die dokumentierten Boardergebnisse in Alex’ Übergabe betreffen seinen Stand 0.3.

Mit Alex’ zusätzlichem Stand 0.4 bestehen alle 56 Tests, einschließlich seiner neuen Körperprüfungen und der 15 Verbundtests. Die dafür geladenen GitHub-Dateien wurden anhand ihrer Git-Objekt-Hashes geprüft. Der Python-Lernkern ist zwischen den beiden Basisrevisionen unverändert. Die Prüfung belegt die gemeinsame Ausführbarkeit; der Körperdatenstrom ist noch nicht an den Verbund angeschlossen. Für diesen Anschluss muss der Transport die bereits auf dem Gerät erlernte Entscheidung weitergeben. Er darf dieselbe Beobachtung nicht erneut in einem zweiten Lernkern zählen. Außerdem muss das tatsächliche Alter der selbstständig erfassten Messung begrenzt werden; der Versandzeitpunkt einer späteren Abfrage allein genügt hierfür nicht.

## Nächster Auftrag für Claude

> Lies diese Übergabe und prüfe die Basisrevision. Nutze für Alex’ Stand 0.4 den Patch. Führe die vollständige Testsuite, die Simulation und die lokale UDP-Probe aus. Prüfe mit Alex als ersten Geräteweg einen Python-Knoten auf dem Pi und eine Python-Zentrale auf dem Mac. Lege fest, wie beide ihre frischen Sitzungskennungen über einen vertrauenswürdigen Anmeldeweg erhalten. Kläre Sensor, Abtastintervall und maximal toleriertes Alter einer Meldung. Plane anschließend den Anschluss von 0.4-Körpersignalen mit eigener Erfassung, ohne doppelte Lernschritte und mit nachprüfbarem Messalter. Übertrage danach den kleinen Paketvertrag auf die passende Geräteschnittstelle. Bei jedem Neustart von Sender oder Empfänger muss die alte Sitzung verworfen werden. Halte reale Verlustzeiten und Paketmengen neben den Simulationsergebnissen fest.

Für die gemeinsame Übernahme von Verbund und Systemversuch gilt die aktuelle Systemübergabe. Alex entscheidet nach der Prüfung, wie die Erweiterungen in seine Hauptentwicklung einfließen.
