# OSCan: gemessener Arbeiter-Wiederanlauf

Messzeit: 2026-11-05T17:29:12.757230+00:00.

Alle Werte sind Millisekunden; angegeben ist der Median. Minima, Maxima und einzelne Läufe stehen in der JSON-Datei.

| Störung | Reserve | n | Auftrag gesamt | Inklusive Vorbereitung | Ab Fehlererkennung bis Ergebnis | Primär-Neustart |
|---|---|---:|---:|---:|---:|---:|
| keine | kalt | 10 | 8.912 | 8.915 | 0.000 | 0.000 |
| keine | vorbereitet | 10 | 9.949 | 79.512 | 0.000 | 0.000 |
| vor_commit | kalt | 10 | 79.869 | 79.873 | 74.909 | 67.860 |
| vor_commit | vorbereitet | 10 | 11.391 | 79.011 | 5.656 | 67.372 |
| nach_commit | kalt | 10 | 9.325 | 9.350 | 0.272 | 67.585 |
| nach_commit | vorbereitet | 10 | 10.654 | 79.128 | 0.303 | 67.600 |
| haengt | kalt | 10 | 406.915 | 406.920 | 152.347 | 67.238 |
| haengt | vorbereitet | 10 | 320.448 | 387.744 | 64.806 | 88.930 |

Die Auftragszeit beginnt vor dem dauerhaften Registrieren und endet beim geprüften Ergebnis. Der vorgezogene Reservestart liegt außerhalb dieses Intervalls; die zusätzliche Spalte inklusive Vorbereitung misst ihn mit. Die Wiederanlaufzeit beginnt bei der Fehlererkennung, umfasst bestätigtes Beenden, Speicherprüfung und gegebenenfalls Reservestart/-arbeit. Bei einem Hänger liegt die Antwortfrist davor und ist in der gesamten Auftragszeit enthalten.

`vor_commit` beendet den Arbeiter nach einem unbestätigten Datenbank-Update; `nach_commit` beendet ihn nach dem gespeicherten Ergebnis und vor der Antwort; `haengt` hält ihn in einer offenen Schreibtransaktion fest. Bei `nach_commit` genügt die Ergebnisabfrage, ohne Ersatzarbeit.

Die Last umfasst 256 KiB synthetischer Daten pro Auftrag. Jeder Lauf enthält Warmlauf, Prüfung einer Wiederholungsanfrage, gegebenenfalls Primär-Neustart, Folgeauftrag und Wiederöffnung des Supervisors. Nur die bezeichneten Intervalle stehen in der Tabelle. Die JSON-Datei enthält außerdem die Bereitschaftsdauer der Reserve; diese ist keine CPU-Zeit- oder Energiemessung.

Die Vorwarnung ist künstlich und aktiviert hier bereits das feste Erbe der vorhandenen Lernregel. Eine feste SCHWACH-Regel könnte dieselbe Vorbereitung auslösen. Der Versuch misst die Wirkung tatsächlicher Reservebereitschaft, keinen Vorteil lernender Prognosen. Einzelrechner-Messung ohne zugesicherte Latenz oder Übertragbarkeit auf ESP32/Pi.
