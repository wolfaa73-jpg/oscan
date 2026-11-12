# Fahrt trotz Sendefehler: Review-Ergänzung zu PR #12

Ein abgelehntes `esp_now_send` setzt Reizbit 32. Im Fahrtmodus wird der Satz geschrieben
und der Körper läuft weiter. Im kontrollierten `FUNKPLAN 1` bleibt der Fehler ein sichtbarer
Abbruch. Auch außerhalb der Fahrt und bei fehlgeschlagenem expliziten Sichern bleibt der
bisherige Abbruch erhalten. Das Bit beschreibt nur die Annahme durch die Sende-API,
keinen Empfangsnachweis. An der Funkstrecke und am Displaytreiber wird nichts geändert.

## Weshalb ein eigenes Feld nötig ist

Im alten 16-Byte-Satz sind die Bits 16 und 32 in Byte 6 bereits der Kernzustand. Byte 7
trägt den Neustartgrund oder zwei Empfinden-Stufen. Dort das Reizbit hineinzuschreiben
würde vorhandene Angaben verfälschen. Deshalb bekommt jede neue Fahrtzeile ein eigenes
Reizfeld, auch bei ausgeschaltetem Funk.

- `/fahrt.log`: vorhandener 16-Byte-Bestand, nur noch gelesen, nicht umgeschrieben.
- `/fahrt-v2.log`: neue 20-Byte-Sätze, weiterhin alle 30 Takte gespeichert.
- `FAHRTLOG` liefert einen gekennzeichneten V2-Strom: zuerst alte Sätze mit ausdrücklich
  unbekanntem Reizfeld, dann neue Sätze. Die Prüfsumme erfasst Kopf und sämtliche Sätze.
- `fahrt.py` liest sowohl unveränderte alte Dateien als auch den neuen Export. Beim neuen
  Export entstehen zusätzlich CSV-Spalten `reiz` und `funk_sendefehler`. Ein unbekanntes
  Reizfeld aus dem Altbestand wird als `-` ausgegeben, nicht als „kein Fehler“.
- `FAHRTSTAND` ergänzt Satzgröße und Exportkopfgröße am Ende der bisherigen Antwort.
  Das aktualisierte Werkzeug berechnet Satzanzahl und Restlaufzeit damit richtig.
- Nicht lesbare Bestände und unvollständige Dateiränder werden nicht durch weitere Sätze verdeckt. Der Fahrtkörper
  läuft dann mit „Protokoll voll/gestört“ weiter; der Export lehnt den beschädigten Strom ab.
  Automatische Reparatur oder Abschneiden ist nicht Teil dieser Änderung.

## Format

Exportkopf, 16 Byte: ASCII `OSCFAHRT`, uint32 Version `2`, uint32 Satzgröße `20`, jeweils
little endian. Danach je 20 Byte:

| Bytes | Bedeutung |
|---|---|
| 0–15 | unveränderter bisheriger Fahrtsatz |
| 16 | Reizbits 1/2/4/8/16/32, einschließlich Sende-API-Fehler |
| 17–18 | reserviert, müssen null sein |
| 19 | 1 = Reizfeld bekannt; 0 = unbekannt und Byte 16 muss null sein |

Neue Daten belegen 25 % mehr Protokollspeicher: 72.000 statt 57.600 Byte pro Stunde.
Der Puffer wächst um 120 Byte. Es gibt keine zweite Schreiboperation pro Satz, und die
Sicherungshäufigkeit bleibt gleich. Wie bisher können bei Stromausfall bis zu 29 im RAM gepufferte, aber noch nicht in Flash gesicherte Takte fehlen. Log und Vorhersagestand sind weiterhin keine gemeinsame atomare Transaktion.

**Zum Abholen die aktualisierte `fahrt.py` verwenden.** Ältere Werkzeuge kennen das neue
Format nicht. Vor einer Rückkehr auf alte Firmware alle Daten abholen und den Fahrtbestand
bewusst leeren; sonst könnte alte Firmware wieder an die alte Datei anhängen, und die
Reihenfolge beider Bestände wäre nicht mehr chronologisch. Diese Änderung führt weder
Flashen noch Löschen aus. Die bisherige Speicherlogik für den Vorhersagestand bleibt erhalten.

## Prüfung

`python -m unittest test_fahrt_funk -v`

- Tatsächliche `koerperTakt`-Funktion mit erzwungenem Sende-API-Fehler: 90 Fahrt-Takte
  laufen weiter und erhalten das Reizbit. Funkplan und normaler Versuch brechen ab.
  Ein Rückbau auf den alten Fehlerausdruck wird vom selben Test erkannt (Mutation).
- Tatsächliche Fahrtfunktionen mit Dateisystemmodell: alter Satz bleibt bytegleich,
  60 neue Sätze werden in zwei Blöcken geschrieben, zwei Neustartmarkierungen erhalten,
  Status und Reizfeld getrennt zurückgelesen; Exportlänge und Prüfsumme stimmen.
- Abgeschnittene Datensätze, falsche Versionen, Satzgrößen und reservierte Bits abgewiesen.
- Fehlender NVS-Schlüssel `funk` ruft `getUChar` nicht auf; Setzen/Lesen beider Werte geprüft.
- Alte und neue Statusantwort korrekt ausgewertet.

Das Modell prüft Code und Dateiformat. Reale Funkfehler, Flash-Ausfälle und das Verhalten
am Board sind damit nicht als gemessen ausgegeben.
