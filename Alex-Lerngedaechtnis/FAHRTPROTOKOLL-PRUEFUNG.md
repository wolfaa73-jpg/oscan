# Fahrtprotokolle vor der Auswertung prüfen

`fahrt_pruefung.py` prüft eine bereits abgeholte Binärdatei am Rechner. Ein formal
lesbares Protokoll kann nach einem Neustart trotzdem doppelte oder rückläufige
Takte enthalten. Solche Stellen sollen vor einer Auswertung sichtbar werden.
Der Prüfer stellt keine Verbindung zum Gerät her, verändert die Eingabe nicht und
repariert nichts. Firmware, Lernverfahren und `fahrt.py` bleiben unverändert.

## Für Alex und Claude

Im Ordner `Alex-Lerngedaechtnis`, mit Python ab 3.9:

```sh
# Bereits abgeholter V2-Export, z. B. vom Selbstgesicht:
python3 -B fahrt_pruefung.py aufnahme.bin --format v2 --json pruefung.json

# Vorhandene ältere Aufnahme aus diesem Repository:
python3 -B fahrt_pruefung.py beispiele/geraetelaeufe-2026-11/roh/fahrt-2026-11-11.bin --format v1

# Prüfungen des neuen Werkzeugs / vollständige Testsuite:
python3 -B -m unittest test_fahrt_pruefung -v
python3 -B -m unittest -v
```

Das neue Werkzeug braucht nur die Python-Standardbibliothek und die bestehende
Datei `fahrt.py`. Für die vollständige Testsuite gelten die bisherigen
Projektabhängigkeiten, einschließlich C++-Compiler.

Die Eingabe muss ein **Export von `fahrt.py holen`** sein. Die geräteinterne Datei
`/selbst.log` hat keinen V2-Exportkopf und ist nicht unmittelbar als Eingabe geeignet.
`--format auto` ist möglich; bei bekanntem Format bitte `v1` oder `v2` angeben.
V1 hat keine Kennung, daher kann Auto-Erkennung einen beschädigten V2-Kopf nicht
zuverlässig von V1 unterscheiden.

| Rückgabecode | Bedeutung | Weiteres Vorgehen |
| --- | --- | --- |
| 0 | Alle implementierten Regeln unauffällig | Auswertung möglich; unten genannte Grenzen beachten. |
| 1 | Auffälligkeiten oder leere Aufnahme | Befunde prüfen und Aufnahme gezielt einordnen. |
| 2 | Formatfehler oder Datei konnte nicht gelesen/geschrieben werden | Ursache klären; diese Prüfung nicht als bestanden verwenden. |

Bei lesbarer Eingabe wird auch bei Befunden ein JSON-Bericht erstellt. Ohne
`--json` geht er an die Standardausgabe. Vorhandene Ausgabedateien werden nie
überschrieben, auch wenn als Ausgabe versehentlich die Eingabe angegeben wird.
Bei Schreibfehlern ist ein möglicherweise unvollständiger Bericht nicht verwendbar.
Der Bericht enthält weder Quelldateinamen noch lokale Verzeichnisse; SHA-256 und
Bytezahl identifizieren die geprüfte Eingabe.

## Welche Regeln geprüft werden

- V1/V2-Kopf, Satzlänge, reservierte V2-Bytes, bekannte Reizbits und gültige
  Empfinden-Nibbles; dafür wird der vorhandene Decoder wiederverwendet.
- Gültiger Zustandswert, nichtnegative verfügbare Vorhersagegrenze, übereinstimmende
  Lastbits und schlüssige Funkbits. Eine Sendung setzt „Funk bereit“ voraus;
  ein Sende-API-Fehler setzt zusätzlich einen Sendeversuch voraus.
- Benachbarte Takte: Wiederholung, Lücke oder Rücksprung. Eine Neustartmarkierung
  macht einen Rücksprung sichtbar, aber nicht unauffällig. Ein erwarteter Überlauf
  von `4294967295` auf `0` ist gültig. Der erste Takt darf beliebig sein.
- Fehlende Temperatur, Temperatur außerhalb −100 bis +200 °C und gemeldete
  Sende-API-Fehler. Dies sind Auffälligkeiten, nicht automatisch Formatfehler.
  Das Temperaturintervall ist eine grobe Plausibilitätsregel, keine Gerätespezifikation
  und kein Nachweis eines sicheren Betriebs. Ein Sende-API-Erfolg belegt keinen Empfang.

Alle Befunde werden gezählt. Die ersten 20 erhalten Beispiele mit Satznummer
(ab 1), Byteoffset (ab 0) und, soweit lesbar, Takt und Neustartmarkierung.
`beispiele_ausgelassen` zählt weitere **Befunde**, nicht weitere Datensätze.
`saetze` zählt vollständige Datensatzplätze, `dekodiert` erfolgreich dekodierte
Sätze. Nach einem nicht dekodierbaren Satz wird kein Taktübergang darüber hinweg
behauptet. `neustarts` und `neustarts_bei_null` zählen gespeicherte Markierungen;
`empfinden_saetze` zählt Sätze mit gespeicherten Empfinden-Werten.

Taktabstände werden modulo 2³² eingeordnet: Abstände 2 bis 2³¹−1 als Lücke,
Abstände ab 2³¹ als Rücksprung. Diese Einordnung ist bei extrem weit auseinander
liegenden Ausschnitten mehrdeutig. `fehlende_taktnummern` summiert Lücken in der
Zählfolge, nicht bewiesene verlorene Messungen oder Sekunden ohne Strom.

## Nachweis und Grenzen

Die im Repository vorhandene Aufnahme vom 11. November 2026 wurde erneut gelesen:
**42.600 Datensätze, 12 Neustartmarkierungen, 42.599 geprüfte Taktübergänge, keine
Befunde nach diesen Regeln.** Der reproduzierbare Bericht liegt in
[`beispiele/fahrtpruefung-2026-11-16.json`](beispiele/fahrtpruefung-2026-11-16.json).
Das ist eine Prüfung vorhandener Daten, kein neuer Gerätelauf.

Am 16. November 2026 bestanden alle **386 Tests** der vollständigen Testsuite,
darunter **16 neue Tests** für diesen Prüfer (Python 3.9, 70,673 Sekunden).
Es wurde kein Gerät geflasht und kein neuer Hardwarelauf durchgeführt.

Die neuen Tests bauen Binärsätze unabhängig vom Decoder auf und verändern gezielt
Kopfbytes, Satzlängen, Empfinden-Nibbles, Reizbits und Taktfolgen. Zusätzlich prüfen
sie Zählerüberlauf, leere Dateien, begrenzte Beispielausgabe, unveränderte Ein- und
Ausgabedateien sowie 1.000 deterministische Zufallsdateien. Ein Gegenbeispiel zeigt
bewusst auch die Grenze: Ein verändertes Temperaturbit kann plausibel bleiben und
wird dann nur bei Vergleich mit einem vorher bekannten SHA-256-Sollwert erkennbar.

Ein unauffälliger Bericht beweist deshalb weder Fehlerfreiheit noch Vollständigkeit.
Das gespeicherte Exportformat enthält keine eigene vollständige Prüfsumme. Der
Transportcheck in `fahrt.py holen` schützt die Übertragung, nicht nachträgliche
Dateiänderungen. Der neue SHA-256-Wert allein ist kein Integritätsnachweis.

Nicht gesicherte Takte vor einem Stromausfall, stromlose Dauer und Gleichstand von
Log und gespeichertem Lernstand lassen sich aus dem Export allein nicht beweisen.
Der Prüfer stellt auch keinen atomaren Speicherstand her. Eine auffällige Stelle
ist ein Anlass zur Prüfung, kein Beleg für eine bestimmte Fehlerursache.
