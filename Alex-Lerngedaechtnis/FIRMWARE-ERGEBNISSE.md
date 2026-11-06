# Firmware und Python unter Last: Ergebnis

6. November 2026. Auftrag 3 aus `NAECHSTE-RUNDE-DANIEL.md`, Aufgabe 6 der Rechenuebergabe.

**Ergebnis:** 4800 Rasterfaelle plus 103 Sonderfaelle vergleichen 232103 synthetische Beobachtungen und 314137 Protokollzeilen einschliesslich Header. Keine Ausgabeabweichung, keine Abweichung der geprueften NVS-Matrizen. Die vorhandene `test_labor`-Suite laesst sieben der 16 festgelegten Mutanten unbemerkt durch; neue gezielte Regressionstests erkennen alle 16.

Es wurde kein Originalfehler gefunden. Die geschuetzten Quellen wurden nicht repariert oder veraendert. Der Hostpruefstand ersetzt keinen Test auf einem ESP32, echte Flash-/Stromausfaelle oder einen allgemeinen Beweis fuer beliebige Spuren.

## Umfang und Reproduktion

- Regeln: zeit, kontext, erbe, startwert; je Regel jeder Blick 1 bis 600.
- Seeds: 730001 und 730002; Generatornamen `OSCAN-FIRMWARE-v1` und `OSCAN-FIRMWARE-BODY-v1` mit Regel/Blick/Seed als deterministischem Textstartwert.
- Raster: 4800 Faelle mit je 48 Beobachtungen, insgesamt 230400.
- Sonderfaelle: 32 Koerperlaeufe vor Prozesswechsel, 32 Fortsetzungen, 32 Resets direkt nach LADEN, drei AG01-Abweisungen und vier uint32-Grenzfaelle. Zusammen 1703 weitere Beobachtungen.
- Alle Protokollzeilen werden exakt verglichen. Gespeicherte Header und CRC ebenfalls; Matrixwerte separat mit absoluter Toleranz 2e-12 und Ablehnung nichtendlicher Zahlen. Warnentscheidungen bekommen keine Toleranz.
- 38408 absichtlich ungueltige Befehlszeilen plus drei abgewiesene AG01-Staende; 36117 Luecken; 4800 explizite Sicherungen; 4864 erfolgreiche LADEN; 14432 Resets; 326 automatische Sicherungen.
- 1696 synthetische Koerpermessungen pruefen SICHERN_ALLE, Fortsetzung und Reset. Nach LADEN ist der erste Koerpertakt `Standtakt+2`: ein zusaetzlicher ausgelassener Takt. Eine direkte Replay-Zeile behaelt ihren angegebenen Takt.
- AG01-Staende von zeit/kontext/erbe werden in Startwert-Firmware als FEHLER abgewiesen. Der anschliessende erste Schritt entspricht einem frischen Startwertknoten; es erfolgt keine stille Konvertierung.

Im Laborordner:

```bash
python3 -B -m unittest -v test_firmwarepruefung
python3 -B firmwarepruefung.py --output /tmp/oscan-firmware-paritaet.json
python3 -B firmwaremutationen.py --output /tmp/oscan-firmware-mutationen.json
```

Der schnelle Vorlauf benutzt `--smoke`. Der volle Lauf umfasst bewusst keine Millionen Spuren: Horizonte, Neustarts und Vertragsgrenzen sind systematisch abgedeckt; pro Kombination gibt es nur zwei Zufallsspuren. Weitere Seeds koennen bisher unentdeckte Faelle finden.

## Mutationen: getrennt von Originalfehlern

Die unveraenderte Quellkopie besteht 59 Tests aus `test_labor` und 19 neue Tests. Pro Mutant laeuft dieselbe vollstaendige bestehende Suite, danach sein zugeordneter Regressionstest. Alle Mutationen finden ausschliesslich in temporaeren Kopien statt. Quellhashes jeder Kopie werden vor ihrer Mutation mit dem Original verglichen.

Die alte Suite besteht sieben Mutanten weiterhin. Sechs weitere verursachen Assertions, drei weitere Laufzeitfehler (teilweise zusaetzlich Assertions). Laufzeitfehler werden separat ausgewiesen und nicht als erfolgreiche fachliche Assertion-Detektion ausgegeben. Jeder der 16 gezielten neuen Regressionstests endet am jeweiligen Mutanten mit einer Assertion und besteht am Original.

**Von der alten Suite uebersehene Mutanten und der neue gezielte Test:**

- `kern_threshold` in `kern.py`: `test_firmwarepruefung.PythonRegressionen.test_kern_schwelle_inklusive`.
- `kern_gap` in `kern.py`: `test_firmwarepruefung.PythonRegressionen.test_kern_luecke_keine_transition`.
- `vok_threshold` in `vokabular.py`: `test_firmwarepruefung.PythonRegressionen.test_vokabular_schwelle_inklusive`.
- `vok_initial_phase` in `vokabular.py`: `test_firmwarepruefung.PythonRegressionen.test_vokabular_anfangsphase`.
- `restart_total` in `neustart.py`: `test_firmwarepruefung.PythonRegressionen.test_neustart_gesamtmasse`.
- `cpp_threshold` in `esp32/Lernknoten/Knoten.h`: `test_firmwarepruefung.FirmwareRegressionen.test_cpp_schwelle_inklusive`.
- `cpp_total` in `esp32/Lernknoten/Knoten.h`: `test_firmwarepruefung.FirmwareRegressionen.test_cpp_gesamtmasse`.

Die vollstaendigen Ersetzungen, Rohresultate, Fehlerklassen und Testnamen aller 16 Mutanten stehen im JSON. Die sieben Luecken betreffen die inklusive Schwelle 0,6 in Python/Wortmodell/C++, eine Zweitaktluecke, eine bereits anfangs kritische Phase und die Gesamtmasse importierter Python-/C++-Staende.

## Artefakte und Integritaet

- [Vorabplan](FIRMWARE-PRUEFPLAN.md)
- [Rohzaehler aller Raster- und Sonderfaelle](beispiele/firmware-paritaet.json)
- [Mutationsergebnisse und konkrete Ersetzungen](beispiele/firmware-mutationen.json)

Compiler: `Apple clang version 21.0.0 (clang-2100.3.34.2)`.
Gemeinsame Compilerargumente: `-std=c++11 -Wall -Wextra -Werror -pedantic -ffp-contract=off`.
Je Variante kommen keine Definition (zeit), `-DALEX_KONTEXT`, `-DALEX_ERBE` oder `-DALEX_STARTWERT` hinzu; Quelle ist `esp32/host.cpp`. Die Ausgabebinaerdateien existieren nur temporaer.

Die JSONs enthalten SHA-256 der geschuetzten Kern-/Firmwarequellen, der Pruefskripte und des Plans. Vorher-/Nachherpruefung: Quellen und Messskripte unveraendert. Ergebnisse enthalten keine lokalen Benutzernamen, absoluten Projektpfade oder Kontaktdaten.

**Entwicklungskorrektur:** Der erste isolierte Mutationslauf scheiterte an einer fehlenden Loopback-Testfixture und ist verworfen, nicht als Mutationsergebnis gewertet. Im verbindlichen Lauf erzeugt der Runner den benoetigten 12-Zeilen-Testeingang synthetisch (sechs VERBUNDEN, sechs ABGELEHNT); die unveraenderte Kopie wird mit derselben Fixture vorab geprueft. Eine fruehe Original-Suite benutzte ihre vorhandene kleine Loopback-Testfixture; keine Koerperaufnahme und insbesondere keine reservierte 24h-Aufnahme wurde eingelesen. Nach Schaerfung der Nichtendlichkeitspruefung und Skripthashes wurde das vollstaendige Paritaetsraster erneut mit denselben Seeds ausgefuehrt. Nur die abschliessenden Laeufe liegen bei.

Es entstehen hier keine Warnleistungs-Vergleichstabellen. Die Vorgabe „Immer warnen“ ist fuer Warnleistungsvergleiche notwendig; als Oracle fuer die exakte Antwort einer benannten Firmware-Lernregel waere sie falsch.

## Unabhaengige Abschlusskontrolle

Die vollstaendige Laborsuite besteht mit 247 Tests (228 vorhandene und 19 neue).
Separater Review von Runner, NVS-Vergleich und Mutationsklassifikation; die Hashes
der veroeffentlichten Rohresultate stimmen mit den tatsaechlichen Quellstaenden
ueberein. Alle zuvor vorhandenen Dateien sind gegenueber der bereinigten Basis unveraendert.
