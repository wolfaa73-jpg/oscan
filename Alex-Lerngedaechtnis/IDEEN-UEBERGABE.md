# Ideenlabor A/B/C – Übergabe an Alex und Claude

Das Labor führt ausschließlich Auftrag 2 aus NAECHSTE-RUNDE-DANIEL.md aus. Kern, Vokabular, Knoten.h und Firmware bleiben unverändert. Es benutzt neue künstliche Miniwelten; keine Geräteaufnahme und insbesondere nicht die reservierte 24-Stunden-Aufnahme.

Startpunkt ist [IDEEN-ERGEBNISSE.md](IDEEN-ERGEBNISSE.md). Darin stehen vollständige Vergleichstabellen, die unveränderten Abnahmekriterien und die nachträglich ergänzte Prüfergrenze. Die [Entwicklung](IDEEN-ENTWICKLUNG.md) bleibt separat erhalten. Einzelne Seeds, Zähler und Ressourcen stehen in IDEEN-ENTWICKLUNG.json und IDEEN-PRUEFUNG.json.

**Freeze:** `278ebad39ab3850ef8c7b4349e4a6e30b8a4b27d`. Die Verfahren, Parameter und 58 ursprünglichen Tests wurden vor Erzeugung des Prüfsatzes committet. B verwendet im Satz `pruefung` die Seeds 0–199; C 0–3 je Familie; Namensraum `OSCAN-IDEEN-v2`. Der Lauf umfasst 9.600 B-Verfahrensauswertungen auf 200 Grundfolgen und 252 C-Verfahrensauswertungen auf zwölf Folgen. Das sind keine entsprechend vielen unabhängigen Geräteversuche.

A liefert die Sollkosten und einen klaren negativen Vergleich für die vierfache Kalibrierung. B besteht die vorab festgelegten Hürden, schlägt die feste Vierertabelle aber nicht über alle Runden. C gewinnt im festgelegten Gemisch, verliert jedoch teilweise in der Wechselfamilie. Der kleine 128-Byte-Vorsprung in der Prüfung kehrt den Entwicklungsvergleich um; deshalb keine allgemeine Überlegenheitsbehauptung.

**Ehrliche Prüfergrenze:** Erst nach dem Kontrolllauf wurde erkannt, dass der ursprüngliche B-Speicherprüfer einen verkürzten Serializer nicht selbstständig entlarvte. Die eingefrorenen Serializer waren nachweislich vollständig; eine zusätzliche unabhängige Prüfung bestätigt das anhand realer Modellfelder und sämtlicher veröffentlichter B-Speicherzeilen. Sieben nachträgliche Tests sowie 73.728 Zustandsprüfungen sind in [IDEEN-SPEICHERPRUEFUNG.json](IDEEN-SPEICHERPRUEFUNG.json) dokumentiert. Diese zusätzliche Absicherung wird nicht als vor dem Prüfsatz erledigt ausgegeben. Kandidaten und Kontrollrohwerte wurden dafür nicht geändert.

Im Laborordner prüfen:

```sh
python3 -B -m unittest -v test_ideenlabor_pruefer test_ideenlabor test_ideenlabor_c test_ideenlabor_speicherpruefung
python3 -B ideenlabor_speicherpruefung.py IDEEN-PRUEFUNG.json --ausgabe IDEEN-SPEICHERPRUEFUNG-WIEDERHOLUNG.json
```

Exakte Wiederholung, mit neuen Zielnamen, weil vorhandene Ausgaben geschützt sind:

```sh
python3 -B ideenlabor.py --satz entwicklung --ausgabe IDEEN-ENTWICKLUNG-WIEDERHOLUNG.json --bericht IDEEN-ENTWICKLUNG-WIEDERHOLUNG.md
python3 -B ideenlabor.py --satz pruefung --freeze 278ebad39ab3850ef8c7b4349e4a6e30b8a4b27d --ausgabe IDEEN-PRUEFUNG-WIEDERHOLUNG.json --bericht IDEEN-PRUEFUNG-WIEDERHOLUNG.md
```

Die Wiederholung ist eine Reproduktion desselben Prüfsatzes, keine neue unabhängige Bestätigung. Bei einer an diesen Ergebnissen angepassten Methode müssen Generatornamespace, Verfahren, Gegner und Kriterien vorher neu festgelegt und eingefroren werden. Die nachträglichen Einordnungsabschnitte im Ergebnisbericht werden vom ursprünglichen eingefrorenen Generator nicht erzeugt.

Die Byteangaben sind offen ausgewiesene logische Zustands- und Pufferbilanzen. Sie sind keine gemessenen Python-, ESP32-, Energie- oder Laufzeitvorteile. Eine Übernahme in das Betriebssystem bleibt ein eigener, konkret begründeter nächster Schritt.
