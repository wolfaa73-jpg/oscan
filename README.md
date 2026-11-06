# OSCan: lernendes Betriebssystem mit verblassendem Gedächtnis

Eine Gedankensammlung und ein erstes Versuchslabor zu der Frage, wie ein System aussehen könnte, dessen Gedächtnis verblasst, sich verdichtet und die Arbeit vorhandener Geräte mitsteuert. Vieles ist Spekulation und als solche gekennzeichnet.

- **[Ideensammlung](Ideensammlung%20Lernendes%20Betriebssystem%20mit%20verblassendem%20Ged%C3%A4chtnis.md)** ist das Konzept. Am Ende hält der Abschnitt „Versuchsstand“ fest, was davon geprüft ist und woher jeder Befund stammt.
- **[Alex-Lerngedaechtnis](Alex-Lerngedaechtnis/START-HIER.md)** ist das Lernlabor: ein fester Reflex und eine kleine lernende Übergangstabelle, in Python und als ESP32-Sketch, mit Vergleichsbericht, Messwerkzeug, Neustart und seriellem Prüfer.

```bash
cd Alex-Lerngedaechtnis
python3 versuch.py
python3 -B -m unittest -v
```

Gebraucht werden Python 3.9 oder neuer, für die Sketch-Tests ein C++11-Compiler und für das Gerät PlatformIO.

**Stand 0.5 vom 5. November 2026.** Die Firmware entscheidet auf einem ESP32-S3 in allen drei Lernregeln genauso wie Python und behält ihren Lernstand über eine Stromtrennung. Im Körpermodus misst sie ihre eigene Chiptemperatur, ihren freien Speicher und ihre Schleifenzeit. Seit 0.5 kann sie ihre Vorwarnung bis zu 600 Takte vorausdenken und sich selbst Speicher und Hauptschleife knapp machen, beides auf dem S3 geprüft. Eine vierte Regel lässt das Erbe als Startwert verblassen. Sie rechnet im Hosttest bitgleich mit Python, auf dem S3 ist sie noch nicht geprüft. Alle Aussagen zur Güte der Regeln stammen aus synthetischen Spuren, nicht aus Messungen im Alltag.

Lizenz: MIT, siehe [LICENSE](LICENSE).

## Systementscheidungen und Verbund prüfen

Der [Systemversuch](Alex-Lerngedaechtnis/SYSTEM-UEBERGABE.md) verbindet das Gedächtnis mit der Vergabe von Arbeitsaufträgen an Primär- und Reserve-Arbeiter. Er vergleicht feste und lernende Regeln auf wechselnden Systemzuständen und führt eine zusätzliche Probe mit zwei echten lokalen Prozessen aus.

Den erzeugten [Systembericht](Alex-Lerngedaechtnis/Systembericht.html) herunterladen und lokal im Browser öffnen. Der [Verbundbericht](Alex-Lerngedaechtnis/Verbund.html) zeigt Knotenidentitäten, Sitzungen und veraltete Meldungen. Die [Verbund-Übergabe](Alex-Lerngedaechtnis/VERBUND-UEBERGABE.md) beschreibt dessen Protokoll und Grenzen.

```bash
cd Alex-Lerngedaechtnis
python3 -B -m unittest -v
python3 -B systemlabor.py prozesse
python3 -B systemlabor.py kontrolle
```

Das sind Laufzeitexperimente auf dem vorhandenen Betriebssystem. Die Vergleichszahlen beruhen auf modellierten Arbeitsbedingungen; sie belegen noch keinen Vorteil eines vollständigen Betriebssystems im Alltag.
