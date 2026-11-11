# Empfinden v2: Nachrechnung und Review-Antwort

Festlegung: Commit `0852f98`, vor dieser erneuten Rechnung. Regeln in [EMPFINDEN-PLAN-v2.md](EMPFINDEN-PLAN-v2.md). V1-Plan, Referenz und Ergebnisse bleiben erhalten. Alle vier v1-Zusammenfassungen wurden exakt reproduziert. Bekannte Aufnahmen, keine neue Blindprüfung.

## Vier identische Eingänge

Betriebsfähige, gültige Takte als jeweiliger Nenner. „Auffällig“ bedeutet Betrag ≥2. Ohne Auffälligkeit wäre die triviale Vergleichsregel überall 0/N; sie könnte auch alle Eingriffe übersehen.

| Aufnahme | v1 gerade | v2 gerade | v1 woanders | v2 woanders | Schlussmaß woanders v1 → v2 |
|---|---:|---:|---:|---:|---:|
| koerper-zufallslast-8h-2026-11-10.csv | 0/27000 (0.00 %) | 0/27000 (0.00 %) | 0/27000 (0.00 %) | 0/27000 (0.00 %) | 500 → 210 mg |
| koerper-last-2026-11-05.csv | 2/19810 (0.01 %) | 2/19810 (0.01 %) | 0/19810 (0.00 %) | 0/19810 (0.00 %) | 500 → 232 mg |
| koerper-kaelte-2026-11-10.csv | 194/900 (21.56 %) | 194/900 (21.56 %) | 322/900 (35.78 %) | 557/900 (61.89 %) | 504 → 214 mg |
| fahrt-2026-11-11.bin | 482/35850 (1.34 %) | 705/40800 (1.73 %) | 31076/35850 (86.68 %) | 4681/40800 (11.47 %) | 545 → 1906 mg |

## Fahrt: Nenner, Lernen und LED

Auf denselben 35850 freigegebenen Takten: woanders 31076/35850 (86.68 %) → 3033/35850 (8.46 %). Gerade 482/35850 (1.34 %) → 482/35850 (1.34 %). Der Vergleich mit gemeinsamem Nenner trennt die Änderung am langsamen Sinn von der aufgehobenen Neustartsperre.

Nach dem ersten Kaltanlauf liegen 40.800 gültige Takte vor. V1 sperrt davon weitere 4.950 wegen Neustarts; v2 keine. Insgesamt bleibt v1 in 6.750, v2 in 1.800 Takten im Anlauf. Das alte Überraschungsbit ist in diesen 40.800 Takten 676-mal gesetzt; v2 erreicht 705 schnelle Ausschläge. Das ist keine eigenständige Erfolgsquote.

| LED: Betrag woanders ≥1 | v1 | v2 |
|---|---:|---:|
| aktiv / betriebsfähig | 34036/35850 (94.94 %) | 13460/40800 (32.99 %) |
| vierter Takt / betriebsfähig | 8509/35850 (23.74 %) | 3366/40800 (8.25 %) |

LED-Zählung ohne Überlagerung durch volles Protokoll, die in der alten Aufnahme nicht verzeichnet ist. Die 95 % aus dem Review passen numerisch zur Zählung ab Stufe 1 (34.036/35.850); ohne Alex’ Zählcode ist das eine mögliche Erklärung, keine bestätigte Rekonstruktion.

V2 nimmt auf der Fahrt 33.687 Updates des langsamen Maßes an, v1 5.644. L endet bei 31,049 statt 37,887 °C; M liegt in beiden Fassungen bei 29,235 °C. Das Schlussmaß woanders ist 1,906 statt 0,545 °C. In den ruhigen Aufnahmen fällt es auf 0,210 bzw. 0,232 °C: Es ist nicht mehr am anfänglichen 0,5-°C-Wert festgehalten. Ein kleineres Maß erhöht beim folgenden Kälteversuch die Empfindlichkeit; dort wird woanders häufiger, nicht seltener.

## Alle Neustarts

Jeweils höchstens die ersten 60 Sätze, begrenzt am nächsten Neustart. Vorzeichen minus bedeutet kälter. Die erste Zeile ist der Kaltstart. Noch unreife geladene Stände behalten den Kaltanlauf.

| Starttakt | Grund | erster schneller Ausschlag v1 | erster schneller Ausschlag v2 | gültige Takte Lernschutz in Segment | Maßbänder im Schutz verändert? |
|---:|---:|---|---|---:|---|
| 1 | 3 | keiner | keiner | 300 | nein |
| 301 | 1 | keiner | keiner | 30 | nein |
| 331 | 1 | keiner | keiner | 600 | nein |
| 4021 | 1 | keiner | [4022, -2] | 600 | nein |
| 6241 | 1 | keiner | [6242, -2] | 600 | nein |
| 7771 | 1 | keiner | keiner | 600 | nein |
| 11251 | 6 | keiner | keiner | 600 | nein |
| 12481 | 6 | keiner | [12511, -2] | 600 | nein |
| 36061 | 1 | keiner | [36062, -2] | 600 | nein |
| 38221 | 1 | keiner | [38224, -2] | 600 | nein |
| 41551 | 1 | keiner | [41552, -2] | 600 | nein |
| 42451 | 1 | keiner | [42457, -2] | 150 | nein |

Die fünf hervorgehobenen Einschaltmomente 4.021, 6.241, 36.061, 38.221 und 41.551 liefern innerhalb von 1–3 Folgetakten gewöhnliches „kälter“. Kein künstliches Einschaltwort. Ein zusätzlicher Kälteausschlag folgt auf Start 42.451. Die zwei sehr frühen Neustarts bleiben wegen des unreifen Gedächtnisses stumm.

## Bekannte Ereignisfenster

Diese Fenster stammen aus der vorhandenen Ereigniszuordnung, sind ungefähr und keine unabhängig erfassten Wahrheitsetiketten. Gezählt wird gerade ab Stufe 2.

| Fenster | Takte | v1 | v2 | erstes v2-Wort |
|---|---|---:|---:|---|
| Pressluft 1 | 12500–13000 | 0 | 42 | [12511, -2] |
| Fön kurz 1 | 13400–14100 | 58 | 58 | [13453, 2] |
| Fön kurz 2 | 15200–15900 | 37 | 37 | [15251, 2] |
| Reiniger und Pressluft | 18450–18780 | 35 | 35 | [18473, -2] |
| Fön lang 1 | 18781–19400 | 113 | 113 | [18791, 2] |
| Fön lang 2 | 24120–24500 | 86 | 86 | [24160, 2] |
| Isopropanol und Pressluft | 27800–28400 | 35 | 35 | [27830, -2] |
| Fön lang 3 | 34100–34600 | 101 | 101 | [34143, 2] |

Die erste Pressluft ist ab Takt 12.511 sichtbar, mit 42 schnellen Ausschlägen im Fenster gegenüber 0 in v1 und 38 alten Überraschungsbits.

## Reproduktion und Grenzen

```sh
python empfinden_vergleich.py --ausgabe vergleich-neu.json
python -m unittest test_empfinden test_empfinden_vergleich -v
```

Rohdatei- und Verfahrensprüfsummen, vollständige Wortfolgen, Maßverläufe alle 1.800 Takte, Schnittmengen und Ereignisse stehen in `beispiele/geraetelaeufe-2026-11/empfinden-v2-vergleich.json`. Ausgaben werden nicht überschrieben.

Ein geladener v1-Stand wird ab dem nächsten Takt nach v2 fortgeführt. Er enthält weiterhin seine alte Lerngeschichte; die Vergleichsergebnisse hier starten beide Fassungen mit denselben Originaleingängen. Beide Situationen sind ausdrücklich verschieden.

Nicht bewiesen sind Alltagstauglichkeit, richtiges menschliches Empfinden oder Unterscheidbarkeit der LED-Helligkeiten. Keine neue Aufnahme und kein Flashen. Konstanten wurden nach der Nachrechnung nicht angepasst.

## Technische Prüfung

343 Tests der vollständigen Suite bestanden; anschließend zusätzlicher Test über alle 42.600 Fahrttakte mit C++/Python, zwölf Neustarts und gleichem Endzustand bestanden. 12.000 künstliche Takte prüfen auch Fehlwerte und Bereichsfehler. S3-Bau: RAM 32.096 B, Flash 362.421 B. Im gesamten Abbild kein `madd.s`/`msub.s`. Quellenprüfsummen in `empfinden-v2-pruefung.json`.
