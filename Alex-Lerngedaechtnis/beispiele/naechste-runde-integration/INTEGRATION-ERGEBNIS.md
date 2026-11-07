# Gemeinsame Integration der vier Erweiterungen

Bereinigte Basis: `3f227a98bb5d36aa5f2c85d09c45bbded34b7966`.
Die Exportkopie enthaelt 95 unveraenderte getrackte Basisdateien und 29
zusaetzliche Python-, Test- und Plan-Dateien: 24h-Pruefer 3, Ideenlabor samt
separatem Speicheraudit 11, Firmwarepruefung inklusive Langlauf 7,
Verweildauer/Bootstrap 8. Keine Basisdatei wurde ersetzt. Keine
Ueberlagerungskonflikte oder unterschiedlichen Doppelbelegungen.

## Abschliessender gemeinsamer Durchgang

**363 Tests bestanden**, keine Fehler, keine Fehlschlaege, keine uebersprungenen
Tests. Gemeinsame unittest-Discovery lief aus dem temporaeren Laborordner mit
Python 3.9.6. Laufzeit dieses Durchgangs: 39.971 Sekunden (kein Benchmark).

Die historische Bootstrap-Phasenzaehlerkorrektur und ihre Regression sind
enthalten. Gegenueber der anschliessend bereits gruenen 356-Test-Fassung wurden
nur `ideenlabor_speicherpruefung.py` und
`test_ideenlabor_speicherpruefung.py` hinzugefuegt. Die sieben weiteren Tests
pruefen die separate Speicherabsicherung. Keine der 27 zuvor uebernommenen
Quellen wurde dafuer aktualisiert; ihre Hashgleichheit wurde vor der Aufnahme
der beiden neuen Dateien und erneut nach dem gemeinsamen Testlauf bestaetigt.
Die eingefrorenen Verfahren und Kontrollwerte wurden durch diese Integration
nicht geaendert oder neu ausgewaehlt.

Alle Basis-/Overlaydateien blieben waehrend der Tests unveraendert. Die
Overlayhashes stimmen nach dem Lauf weiterhin mit den vier Quellworktrees
ueberein. SHA-256 fuer jede Datei, die vorangegangene Bootstrapkorrektur und
die beiden Speicherpruefer-Ergaenzungen stehen in `integration-manifest.json`.
Zaehler und Bindung an Runner/Manifest stehen in `integration-result.json`.
Die vorigen Integrationen bleiben mit den Suffixen `.before-bootstrap-review`
und `.before-memory-audit` separat erhalten. Vor dem Zusammenfuehren sind die
finalen Zweighashes gegen das aktuelle Manifest abzugleichen.

Es wurden weder Commits erstellt noch Zweige zusammengefuehrt. Nur getrackte
Basis-Testfixtures wurden exportiert; keine Koerper- oder 24h-Aufnahmen und
keine zusaetzlichen Nutzerdaten wurden kopiert. Ein frueher technischer Vorlauf
mit fehlendem Spawn-Guard im temporaeren Runner wurde verworfen; alle hier
als gruen genannten Integrationsdurchgaenge verwenden den korrigierten Runner.
