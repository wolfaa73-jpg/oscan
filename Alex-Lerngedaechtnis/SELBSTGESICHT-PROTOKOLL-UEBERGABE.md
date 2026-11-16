# Selbstgesicht: drei Protokollfehler behoben

Basis ist der aktuelle bereinigte Hauptzweig `9d2e103d112dc87591c87505e6ed15797d06663a`.
Anlass ist Alex’ Bitte um Prüfung des Flash- und Protokollteils im Kommentar zu PR #12.
Die Änderung betrifft ausschließlich `esp32/Selbstgesicht/src/main.cpp`, ergänzt um
Regressionstests und diesen Nachweis. Selbst.h, Vorhersage, Empfinden, Lichtplan,
Displayzeichnung, andere Firmwareprojekte und das V2-Dateiformat bleiben unverändert.

## Verhalten

| Auslöser | Vorher | Jetzt |
|---|---|---|
| Vorhandene Logdatei lässt sich nicht zum Lesen öffnen | Länge 0; Download und Status melden ein leeres Protokoll | `FEHLER`; kein erfolgreicher leerer Download |
| Löschen einer der drei Dateien schlägt fehl oder die Datei ist danach noch vorhanden | `FAHRT,leer`, gegebenenfalls mit erneut geladenem alten Lernstand | `FEHLER`; kein Neustart bei null und keine Erfolgsmeldung |
| Bei `ZEILEN 1` fällt ein Messtakt in den Download | Diagnosezeilen mischen sich in die Hexdaten; Leser bricht ab | Nur Diagnoseausgabe pausiert während des Exports; Messung, Lernen und Schreiben laufen weiter |

Eine fehlende oder tatsächlich leere Logdatei bleibt ein gültiges leeres Protokoll.
Ein begonnener Export liefert wie bisher einen festen Ausschnitt bis zu seiner Startlänge;
später angehängte Sätze gehören erst zum nächsten Download. Die Diagnoseeinstellung bleibt
erhalten und wird nach Abschluss oder Abbruch des Exports wieder wirksam.

## Schutz nach Speicherfehlern

Ein erkannter Log-Lesefehler oder Löschfehler sperrt weitere Flash-Schreibvorgänge.
Das schützt sowohl den verbliebenen Logbestand als auch den gespeicherten Lernstand.
Messung und Lernen im RAM laufen weiter. Die vorhandene Voll-/Störungsanzeige wird gesetzt;
bei einem schon beim Start erkannten Fehler erscheint zusätzlich `SELBST,speicherfehler`.
Status oder Download dürfen einen Lesefehler nicht in eine gültige Null-Länge umdeuten.

Beim Löschen sind drei Dateien beteiligt. Der Vorgang ist **nicht atomar**: Wenn eine spätere
Löschung scheitert, können frühere Dateien bereits gelöscht sein. Der Code hält dann an,
behält den RAM-Stand und überschreibt den Rest nicht durch neue Sicherungen. Erst wenn ein
erneuter, bewusst angeforderter `FAHRTLEER` alle Dateien entfernt hat, beginnt das Gerät
bei null und gibt das Schreiben wieder frei. Ein Neustart mit wieder lesbarem Bestand gibt
das Schreiben ebenfalls frei und folgt dabei der bisherigen Lade-/Neuanlaufregel.

`FAHRTLEER` bleibt ein ausdrücklich angeforderter Löschbefehl; diese Lieferung führt ihn
nicht aus. Sie aktualisiert und flasht auch kein Gerät. Die bestehende Grenze, dass Log und
Lernstand keine gemeinsame atomare Flash-Transaktion bilden, wird hier nicht verändert.

## Prüfungen

Die neuen Tests kompilieren die **vollständige tatsächliche main.cpp**, einschließlich
`setup`, `loop`, Befehlsparser und Flashfunktionen. Nur Arduino, LCD, Serial und LittleFS
werden durch ein kontrollierbares Modell ersetzt. Es gibt keine nachgebaute Kopie des
Produktionsablaufs in den Tests.

- Vor der Korrektur: neun neue Tests ausgeführt. Acht fehlgeschlagene Assertions
  (einschließlich Teilfälle) und ein Downloadfehler reproduzieren die bisherigen Mängel;
  die normalen Kontrollfälle bestehen bereits am Original.
- Nach der Korrektur: alle neun neuen Tests bestehen, zusammen mit den vier vorhandenen
  Selbstgesicht-Tests. Letztere prüfen 7.500 künstliche Takte, Fehlwerte, Neustarts und
  exakte Gleichheit mit Python.
- Vollständige Laborsuite: **370 Tests bestanden**, keine Fehler oder übersprungenen Tests,
  Laufzeit 81,872 Sekunden auf dem Prüfrechner.
- C3-Bau `esp32/Selbstgesicht`, Umgebung `guition-c3`: erfolgreich.
  RAM **24.508 Byte**, Flash **389.818 Byte**.
- Festgelegte Abhängigkeiten: espressif32 6.12.0, LovyanGFX 1.2.29, NumPy 2.0.2;
  Bauwerkzeug PlatformIO Core 6.1.18.

Die neuen Fälle umfassen vorhandene leere und fehlende Dateien, Öffnungsfehler bei Export,
Status, Sichern und Neustart sowie Löschfehler an jeder der drei Dateien. Ein fehlerhaftes
`remove`, das Erfolg behauptet, die Datei aber stehen lässt, wird ebenfalls erkannt.
Nach fehlgeschlagenem Löschen werden weitere Schreibvorgänge und ein erfolgreicher
erneuter Löschversuch mit anschließendem Neuanfang geprüft.

Der Downloadtest beginnt mit 630 gesicherten Sätzen und 29 noch gepufferten Takten.
Während der Übertragung kommt ein weiterer Flashblock hinzu. Zurückgegeben werden exakt
die ursprünglichen 630 Sätze, mit gültiger Länge und Prüfsumme, auch bei `ZEILEN 1`.
Die Taktzahl steigt währenddessen weiter; Diagnoseausgabe kehrt anschließend zurück.
Auch ein abgebrochener Export lässt die Diagnose wieder zu.

Reproduktion im Laborordner:

```sh
python -B -m unittest test_selbstgesicht_flash test_selbstgesicht -v
python -B -m unittest -v
pio run -d esp32/Selbstgesicht -e guition-c3
```

Maschinenlesbarer Nachweis und Quellenprüfsummen:
`beispiele/selbstgesicht-protokoll-2026-11-16/pruefung.json`.
Die Fehler wurden im Dateisystemmodell geprüft, nicht durch physische Flashfehler oder
Stromunterbrechungen am Board. Eine Geräteprobe mit Alex’ Aufzeichnung bleibt sein nächster
Schritt; die erfolgreiche Hostprüfung ersetzt diese nicht.
