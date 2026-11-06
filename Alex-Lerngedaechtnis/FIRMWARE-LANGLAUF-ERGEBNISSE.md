# Firmware/Python: Ergänzung durch lange Lerngeschichten

Ausschließlich künstliche Daten. Vier kontinuierlich fortgelernte Geschichten, keine Million verschiedener Spuren.
Genau 1000000 Beobachtungen, 1000080 exakt verglichene Protokollzeilen.
Abweichende Zeilen: 0; NVS-Prüffehler: 0.
Blick 1: 997952 Beobachtungen; Blick 600: 2048.
952 Lücken; 16 Sicherungen, 12 LADEN und 16 NEUER_LAUF.

## Zähler pro Regel

| Regel | Seed | Beobachtungen | Lücken | Ausgänge aus SCHWACH | Ausgabeabweichungen | NVS-Fehler |
|---|---:|---:|---:|---:|---:|---:|
| zeit | 730101 | 250000 | 238 | 57305 | 0 | 0 |
| kontext | 730102 | 250000 | 238 | 57102 | 0 | 0 |
| erbe | 730103 | 250000 | 238 | 57124 | 0 | 0 |
| startwert | 730104 | 250000 | 238 | 57375 | 0 | 0 |

Die Tabelle zählt Paritätsprüfungen, keine Warnleistung; Immer warnen wäre hier kein Oracle für die vier Firmware-Regeln.

## Unterlauf und Wiederanlauf

Erster beobachteter subnormaler Python-Startwert: Beobachtung 27142.
Letzter Rest: Python `0x0.0000000000004p-1022`, Firmware `0x0.0000000000004p-1022`.
Klassifikation: Python subnormal, Firmware subnormal.
Ein positiver subnormaler Rundungsrest ist nicht automatisch ein Fehler und wird nicht als exakt null ausgegeben.
Nach 62.500, 125.000 und 187.500 Beobachtungen wurde gesichert, der eigene Hostprozess beendet und mit
NEUER_LAUF→BLICK1→LADEN aus demselben NVS fortgesetzt. Der absolute Takt lief weiter.
Vier NVS-Stände je Regel wurden geprüft; die zusätzliche Schluss-Sicherung enthält den langen Blickabschnitt.

## Integrität und Grenzen

Geschützte Quellen unverändert: True; bisherige Prüfer unverändert: True; neue Prüfquellen unverändert: True.
Vollständig bytegleiche NVS-Stände: 16/16. Maßgeblich bleibt die vorhandene Matrixregel:
Header/CRC prüfen, endliche Matrixwerte mit absoluter Toleranz 2e-12; Protokoll und Warnentscheidungen immer exakt.
Quellhashes, Compilerkennung/-flags und sämtliche Abschnittszähler stehen in [firmware-langlauf.json](beispiele/firmware-langlauf/firmware-langlauf.json).
Dies ergänzt die vorherigen 48-Beobachtungs-Fälle um lange Lerngeschichten. Es ersetzt keinen ESP32-
Flash-/Stromausfall-, Echtzeit- oder Sicherheitsnachweis. Kein Originalcode wurde verändert.

Reproduktion im Laborordner:

```sh
python3 -B -m unittest -v test_firmwarelanglauf
python3 -B firmwarelanglauf.py --ausgabe rechen-ergebnisse/neuer-langlauf
```

Vier neue gezielte Tests prüfen Fortlernen über LADEN, Horizontwechsel, erzwungene Ausgänge und die Trennung von subnormal und null. Alle vier bestanden.

Vorabdefinition: [FIRMWARE-LANGLAUF-PLAN.md](FIRMWARE-LANGLAUF-PLAN.md). Ausführung: [firmwarelanglauf.py](firmwarelanglauf.py). Die ursprünglichen Kurzspuren- und Mutationsartefakte bleiben unverändert und ihre bisherigen Quellhashes gültig.
