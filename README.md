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

**Stand 0.3 vom 5. November 2026.** Die Firmware entscheidet auf einem ESP32-S3 in allen drei Lernregeln genauso wie Python. Alle Aussagen zur Güte der Regeln stammen aus synthetischen Spuren, nicht aus Messungen im Alltag.
