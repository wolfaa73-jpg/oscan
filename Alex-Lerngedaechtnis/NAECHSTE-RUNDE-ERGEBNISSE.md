# Für Alex und Claude: Ergebnisse der nächsten Runde

6. November 2026. Vier getrennte Arbeitszweige und Pull Requests, ausgehend von
bereinigter Basis `3f227a98bb5d36aa5f2c85d09c45bbded34b7966`.
Die bestehenden Kern-, Vokabular- und Firmwaredateien wurden in keinem Paket
verändert. Die PRs wurden bereitgestellt; eine Übernahme in main bleibt der Reviewentscheidung vorbehalten.

## Zuerst: unabhängige 24-Stunden-Prüfung

[PR #6](https://github.com/wolfaa73-jpg/oscan/pull/6) enthält
`PRUEFPROTOKOLL-24H.md`, `pruefung24h.py` und synthetische Gegenproben.
Veröffentlichung: **6. November 2026, 15:12:34 UTC / 16:12:34 CET**;
Freeze `8e8ad1984b59c729d7bc5293ca3a0cbdf84cb72a`.
Die reale Aufnahme wurde hier nicht geöffnet. Nach ihrem Ende führt Claude
zuerst diesen Stand aus, vor Kurven, Auswahl oder weiteren Auswertungen.

Im Laborordner des zugehörigen Stands:

```sh
python3 -B pruefung24h.py messungen/koerper-startwert-24h-2026-11-06.csv > pruefbericht-24h.md
```

CSV und gleichnamige JSON-Datei müssen zusammenliegen. Rückgabestatus und Bericht
unverändert aufbewahren. Alex/Claude bestätigen den tatsächlichen Zeitpunkt der
ersten Datensicht; ein Commit allein kann diesen nicht beweisen. Abbruch bedeutet
keine Güteauswertung. Negative Hypothesen sind gültige Ergebnisse.

Zur Flashdiagnostik: Der Sketch sichert nach der Messung und klammert eigene
Arbeit aus der fremden Schleifenlücke aus. Eine direkte Lückenerhöhung in Takt 601
wird deshalb nicht behauptet. 600er-Takte und ihre Folgetakte bleiben wie vorab
festgelegt in der Wertung und werden zusätzlich dokumentiert.

## Weitere Pakete

| Auftrag | Pull Request und Einstieg | Wichtig für die Übernahme |
| --- | --- | --- |
| Ideen A–C | [PR #9](https://github.com/wolfaa73-jpg/oscan/pull/9), `IDEEN-ERGEBNISSE.md` | Erst Defektprüfer, dann Entwicklung, dann Freeze, dann neuer Prüfsatz; negative Befunde gehören zur Lieferung. |
| Firmware/Python | [PR #7](https://github.com/wolfaa73-jpg/oscan/pull/7), `FIRMWARE-ERGEBNISSE.md` und `FIRMWARE-LANGLAUF-ERGEBNISSE.md` | 232.103 Raster-/Sonderbeobachtungen plus eine Million Langlaufbeobachtungen ohne Antwortabweichung. Sieben von der alten test_labor-Suite übersehene Mutanten durch neue Regressionen abgedeckt. |
| Verweildauer und Bootstrap | [PR #8](https://github.com/wolfaa73-jpg/oscan/pull/8), `VERWEILDAUER-ERGEBNISSE.md` | Mechanisch geprüfter Prototyp, aber kein allgemeiner Ersatz: in neuer Kontrolle 664/3298 Phasen verpasst. Echte Bootstrapintervalle bleiben ohne ältere Aufnahmen offen. |

Die Hostprüfungen ersetzen keine ESP32-Hardware-, Stromausfall- oder Echtzeitprüfung.
Die synthetischen Miniwelten ersetzen keine Feldmessung. Aus günstigen Kosten allein
folgt keine sichere Warnstrategie; beide Kostenbegriffe und einfache Gegner stehen
in den Berichten daneben.

## Noch benötigte Daten

Nur für die historischen Bootstrapintervalle fehlen die freigegebenen älteren
6h- und 30min-CSVs samt Sidecars. Das Werkzeug und seine Gegenproben sind vorhanden.
Die gerundeten alten Prozentwerte reichen zur Berechnung nicht aus. Die neue
24h-Aufnahme ist für diese Aufgabe ausgeschlossen und wird nicht ersatzweise benutzt.

## Datenschutz und Weiterarbeit

Neue Commits benutzen die öffentliche GitHub-No-Reply-Identität. Neue Dateien,
Berichte, Rohartefakte und PR-Texte wurden vor Veröffentlichung auf private
Kontaktdaten geprüft. Die lokale Datenschutz-Regeldatei gehört nicht zur Übergabe.
Beim Weiterarbeiten die aktuellen bereinigten Zweige verwenden; keine entfernte
alte Historie zurückführen. Die bestehende lokale Schutzprüfung wurde nicht umgangen.

## Gemeinsame Abschlussprüfung

Alle vier Pakete zusammen bestanden **363 Tests**, ohne Fehler, Fehlschläge oder
übersprungene Tests. Die frische gemeinsame Exportkopie enthielt 95 unveränderte
Basisdateien und 29 zusätzliche Python-/Test-/Plandateien, ohne Überlagerungskonflikte.
Die Hashes wurden danach erneut gegen die vier endgültigen Arbeitszweige geprüft.
[Integrationsnachweis](beispiele/naechste-runde-integration/INTEGRATION-ERGEBNIS.md),
[Manifest](beispiele/naechste-runde-integration/integration-manifest.json) und
[Rohresultat](beispiele/naechste-runde-integration/integration-result.json) liegen bei.
Nach Übernahme der vier Pakete startet die übliche Prüfung im Laborordner mit
`python3 -B -m unittest`. Die dokumentierte Testzahl gilt für genau die geprüften
Quellen; spätere Änderungen benötigen ihre eigene Prüfung.

A/B/C wurden mit Freeze `278ebad39ab3850ef8c7b4349e4a6e30b8a4b27d` vor der
Kontrollerzeugung festgelegt. Der ursprüngliche B-Speicherprüfer besaß eine erst
nach dem Lauf erkannte Grenze gegenüber gekürzten Serialisierungen. Die separate
nachträgliche Prüfung ist offen dokumentiert: unveränderte Modelle, sieben
zusätzliche Tests, 73.728 Zustandsprüfungen und Kontrolle aller 9.600 B-Rohzeilen.
Diese Ergänzung wird nicht als ursprüngliche Blindprüfung ausgegeben.

Der Verweildauer-Freeze `4df7cf9101d9587b39c9a0072ebccbfb7798c76c` liegt ebenfalls
vor seiner neuen Kontrolle. Eine spätere Korrektur historischer Phasenzähler im
separaten Bootstrapwerkzeug änderte weder Prototyp noch Kontrollzahlen.
