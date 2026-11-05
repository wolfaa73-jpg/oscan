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

**Stand 0.4 vom 5. November 2026.** Die Firmware entscheidet auf einem ESP32-S3 in allen drei Lernregeln genauso wie Python und behält ihren Lernstand über eine Stromtrennung. Im Körpermodus misst sie ihre eigene Chiptemperatur, ihren freien Speicher und ihre Schleifenzeit. Alle Aussagen zur Güte der Regeln stammen aus synthetischen Spuren, nicht aus Messungen im Alltag.

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

## Verbund und Arbeitsvergabe gemeinsam ausführen

[Anschluss und Auftragslebensdauer](Alex-Lerngedaechtnis/ANSCHLUSS-UEBERGABE.md) beschreibt die Verbindung: neue Statusmeldungen steuern den festen Disponenten; ein begrenztes Register verhindert doppelte Arbeit unter derselben Kennung. Der gemeinsame Versuch läuft mit `python3 -B verbundsystem.py` im Laborordner und verwendet zwei echte lokale Arbeiter. Er prüft insbesondere Verlust, Sitzungswechsel und ablaufende Arbeitsfreigaben.

## Aufträge nach einem Absturz wiederfinden

Das optionale [dauerhafte Auftragsjournal](Alex-Lerngedaechtnis/JOURNAL-UEBERGABE.md) erhält Quittungen über Prozessneustarts. Angefangene Arbeit ohne bestätigten Abschluss bleibt ungeklärt und wird unter derselben Kennung nicht erneut ausgeführt. `python3 -B neustartlabor.py` prüft drei harte Abbrüche eigener Prozesse und wiederholte Anfragen. Die Erweiterung benötigt macOS oder Linux; ihre Testwirkung ist eine Dateizeile. Eine atomare Wirkung auf einem echten Gerät oder ein Schutz über gelöschte bzw. zurückgesetzte Journale hinweg ist damit nicht belegt.

## Echten Arbeiter-Ausfall und Wiederanlauf messen

Die [Wiederanlauf-Übergabe](Alex-Lerngedaechtnis/WIEDERANLAUF-UEBERGABE.md) ergänzt einen lokalen Hashdienst mit dauerhaften fachlichen Kennungen, bestätigter Reservebereitschaft und kontrolliertem Prozessneustart. `python3 -B wiederanlauflabor.py --wiederholungen 1` prüft Abbruch vor/nach dem Speichern und einen hängenden Arbeiter. Der [Messbericht](Alex-Lerngedaechtnis/Wiederanlaufbericht.md) enthält 80 Durchläufe und weist die vorgezogene Startzeit einer vorbereiteten Reserve gesondert aus. Die sichere Wiederholung gilt für den transaktionalen Ergebnisdatensatz dieses Backends; für externe Gerätewirkungen braucht es einen eigenen Vertrag.
