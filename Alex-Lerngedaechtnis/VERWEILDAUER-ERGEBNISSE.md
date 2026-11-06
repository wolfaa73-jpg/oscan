# Verweildauer und Richtung: Ergebnis und Übergabe

6. November 2026. Getrennter Python-Prototyp; keine Änderung am laufenden Kern, am Vokabular oder an der Firmware.

**Ergebnis:** Die getrennte Dauer-/Richtungsrechnung funktioniert in den geprüften Mechanikfällen. Als allgemeiner Ersatz trägt dieser Kandidat in der neuen künstlichen Kontrolle nicht: Er gibt weniger und teilweise präzisere Warnungen aus, lässt jedoch erheblich mehr Phasen unangekündigt. Eine Übernahme in den Gerätekern ist daraus nicht begründet.

## Was ausgeführt wurde

- Vorabplan: [VERWEILDAUER-PLAN.md](VERWEILDAUER-PLAN.md). Keine Rasterwahl und keine nachträgliche Parameteranpassung.
- Entwicklung: 16 Seeds je vier Familien, insgesamt 64 Spuren zu 960 Takten; Seeds 300000–300015 im Entwicklungsnamensraum.
- Freeze vor der neuen Kontrolle: `4df7cf9101d9587b39c9a0072ebccbfb7798c76c`.
- Neue Kontrolle: 32 Seeds je vier Familien, insgesamt 128 Spuren; Seeds 300100–300131 im Kontrollnamensraum. Die alten Kontrollen aus #4 wurden dafür nicht wiederverwendet.
- Quellenhashes blieben während der Kontrolle unverändert. Ergebnisdateien und kandidatenunabhängige Aufgaben-/Ziel-/Phasennenner wurden nachgerechnet.
- 29 zusätzliche gezielte Tests grün; gesamte Laborsuite 257 Tests grün. Nach der letzten reinen Darstellungsergänzung zur Bootstrapabdeckung wurden die 13 Bootstraptests erneut erfolgreich ausgeführt.

Die Prüfung war vor Ausführung dieser neuen Kontrollspuren eingefroren. Der Generator und seine Familien waren bereits bekannt; das ist keine unabhängige Prüfung an echten Geräten.

## Maßgebliche Taktwertung der neuen Kontrolle

Nachfolgend die Sicht **je Signal**, insgesamt als ODER der eigenen Warnungen außerhalb global kritischer Takte. Eigene Signaltabellen zählen alle eigenen nichtkritischen Takte, einschließlich OK. Warnanteil und Trefferquote besitzen verschiedene Nenner; die Grundrate ist die Trefferquote der Immer-warnen-Referenz. Die letzten 30 Takte jeder Spur dienen nur als Zukunft. Kosten werden bei r=10 je 1000 Instrumenttakte angegeben, Takt- und Phasenfehler ausdrücklich getrennt.

| Bereich | Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |
|---|---|---:|---:|---:|---:|---:|---:|
| gesamt | Feste Regel | 41.77 % | 76.12 % | 70.99 % | 0/3298 | 3385.61 | 84.03 |
| gesamt | Startwert | 64.37 % | 69.54 % | 70.99 % | 6/3298 | 2374.87 | 165.70 |
| gesamt | Immer warnen | 100.00 % | 70.99 % | 70.99 % | 0/3298 | 244.37 | 244.37 |
| gesamt | Verweildauer und Richtung | 38.79 % | 80.76 % | 70.99 % | 664/3298 | 3404.35 | 118.65 |
| temperatur | Feste Regel | 20.82 % | 35.76 % | 23.38 % | 0/858 | 1661.34 | 128.66 |
| temperatur | Startwert | 30.68 % | 23.62 % | 23.38 % | 55/858 | 1777.49 | 230.02 |
| temperatur | Immer warnen | 100.00 % | 23.38 % | 23.38 % | 0/858 | 737.00 | 737.00 |
| temperatur | Verweildauer und Richtung | 5.71 % | 35.02 % | 23.38 % | 626/858 | 2092.32 | 88.29 |
| speicher | Feste Regel | 15.26 % | 60.39 % | 41.68 % | 0/1485 | 3089.54 | 56.44 |
| speicher | Startwert | 31.08 % | 31.20 % | 41.68 % | 44/1485 | 3187.79 | 203.42 |
| speicher | Immer warnen | 100.00 % | 41.68 % | 41.68 % | 0/1485 | 544.74 | 544.74 |
| speicher | Verweildauer und Richtung | 22.62 % | 69.51 % | 41.68 % | 485/1485 | 2489.56 | 105.15 |
| schleife | Feste Regel | 15.10 % | 58.65 % | 41.08 % | 0/1470 | 3073.18 | 58.39 |
| schleife | Startwert | 30.72 % | 30.34 % | 41.08 % | 45/1470 | 3171.34 | 203.93 |
| schleife | Immer warnen | 100.00 % | 41.08 % | 41.08 % | 0/1470 | 551.19 | 551.19 |
| schleife | Verweildauer und Richtung | 22.09 % | 70.47 % | 41.08 % | 498/1470 | 2447.62 | 102.86 |

Alle acht Verfahren, die grobe Sicht und die eigenen Signale stehen im [vollständigen Kontrollbericht](beispiele/verweildauer-2026-11-06/kontrolle/bericht.md). Die grobe Immer-warnen-Zeile behält dort die Gerätesemantik: Ein fremdes kritisches Signal unterdrückt einen globalen Alarm, weshalb der Warnanteil im eigenen Signalnenner unter 100 Prozent liegen kann. Diese Sicht ist von der eigenen Signalreferenz zu unterscheiden.

## Was daraus folgt

Die hohe Trefferquote des Kandidaten ist kein hinreichender Erfolg: Insgesamt bleiben 664 von 3298 Phasen ohne Warnung, bei der festen Regel keine. Gegen diese feste Regel sind in der Mischung sowohl Taktkosten als auch Phasenkosten höher. Die geringe Temperaturwarnung lässt 626 von 858 Phasen unangekündigt. Diese Ausfälle werden nicht durch eine günstige Präzisionszahl verdeckt.

Beim Speicher und bei der Schleife sinken die Taktkosten gegenüber Startwert und fester Regel; gleichzeitig bleiben viele Phasen ohne Vorwarnung. Bei den gewählten hohen Grundraten und r=10 erreicht Immer warnen sehr niedrige Taktkosten. Das ist im vorgegebenen Kostenmodell mitzuberichten und keine Empfehlung, reale Geräte dauerhaft zu warnen. Eine Änderung des Kostenbegriffs kann die Bewertung umkehren.

Der Ansatz löst einen konkreten Mechanismus: Verweilen erzeugt keine zusätzlichen Richtungsbelege, und ein beobachteter längerer Rückweg braucht auch im Blick seine Zeit. Er nimmt jedoch an, dass Dauer und Ausgangsrichtung bedingt auf das Wort unabhängig sind. Ein analytischer Gegenfall zeigt genau diese Grenze. Das Dauerprior von einem Takt ist ebenfalls eine zusätzliche Annahme, keine Gerätebeobachtung. Fehlende Dauerabdeckung ist unbekannt und kann Warnungen unterdrücken. Weder ein neuer Parameter noch eine weitere Auswahl wurde nach der Kontrolle ausprobiert.

Ein weiterer Versuch müsste eine neue Hypothese und einen neuen vorab festgelegten Prüfsatz erhalten, beispielsweise gemeinsame Dauer-/Zielinformation oder einen ausdrücklichen Rückfall bei fehlender Dauerabdeckung. Der vorliegende Kontrollsatz wäre dafür Entwicklungswissen, kein erneut unabhängiger Nachweis.

## Bootstrap: Werkzeug vorhanden, echte Zahlen weiterhin offen

[einheitenbootstrap.py](einheitenbootstrap.py) und [EINHEITEN-BOOTSTRAP-PLAN.md](EINHEITEN-BOOTSTRAP-PLAN.md) liefern die vorab festgelegte Auswertung ganzer Leckdurchgänge, Hitzephasen und Bremsrampen. Die Warnungen werden einmal chronologisch gelernt, danach werden ganze Einheiten gepaart wiedergezogen. Verhältniswerte entstehen aus Rohzählersummen; es werden keine künstlichen Übergänge durch neu zusammengeklebte Rohdaten erzeugt.

Geprüft sind identische Paare mit exakt null Differenz, konstante bekannte Differenzen, ungleiche Einheitenlängen, undefinierte Trefferquoten, falsche Paarung, Randzensierung, Block8-Mindestgröße und die Geräteprüfung an künstlichen Zeilen. Ein vollständiger künstlicher Lauf mit 2000 Wiederziehungen erzeugte gültige Manifest-/Dateihashes ohne lokale Pfade in den Artefakten. Der Bericht weist je Einheitenart L-H, übernommene Takte und Prozentabdeckung ausdrücklich aus.

**Es liegen hier keine echten 6-Stunden-/30-Minuten-CSVs samt Sidecars vor.** Deshalb gibt es keine neuen Intervalle für 79 gegen 52 Prozent oder für die dokumentierten 59/73 und 77/79 Prozent. Die gerundeten Angaben reichen zur Rekonstruktion nicht aus. Die 24-Stunden-Prüfaufnahme wurde weder gesucht noch gelesen und ist ausdrücklich kein Ersatz.

Das gewöhnliche Einheitenbootstrap setzt Austauschbarkeit voraus; Lernstand, Erwärmung und Reizblöcke können sie verletzen. Block8 ist eine zusätzliche Sensitivität, keine Garantie. Die Intervalle beschreiben eine einzelne beobachtete Lerngeschichte und ersetzen keine unabhängigen Aufnahme- oder Gerätewiederholungen.

## Dateien und Reproduktion

- [Entwicklung: Manifest](beispiele/verweildauer-2026-11-06/entwicklung/manifest.json), [Rohzähler](beispiele/verweildauer-2026-11-06/entwicklung/spuren.csv), [Familienvergleich](beispiele/verweildauer-2026-11-06/entwicklung/vergleich.csv).
- [Kontrolle: Manifest](beispiele/verweildauer-2026-11-06/kontrolle/manifest.json), [Rohzähler](beispiele/verweildauer-2026-11-06/kontrolle/spuren.csv), [Familienvergleich](beispiele/verweildauer-2026-11-06/kontrolle/vergleich.csv).
- [Prototyp](verweildauer.py), [Vergleichslabor](verweildauerlabor.py), [Modelltests](test_verweildauer.py), [Vergleichstests](test_verweildauerlabor.py), [Bootstraptests](test_einheitenbootstrap.py).

Der Kontrollrunner verlangt **HEAD gleich Freeze-Commit**. Für eine Wiederholung deshalb eine getrennte Arbeitskopie am Freeze auschecken; den späteren Ergebniskopf nicht als Freeze angeben. Im Laborordner dieser Kopie:

```sh
python3 -B -m unittest
python3 -B verweildauerlabor.py entwicklung --ausgabe rechen-ergebnisse/neue-entwicklung
python3 -B verweildauerlabor.py kontrolle --freeze 4df7cf9101d9587b39c9a0072ebccbfb7798c76c --ausgabe rechen-ergebnisse/neue-kontrolle
```

Wenn Alex die ausdrücklich freigegebenen älteren Aufnahmen samt gleichnamiger JSON-Datei bereitstellt, im aktuellen Laborordner, beispielsweise:

```sh
python3 -B einheitenbootstrap.py messungen/koerper-muster-6h-2026-11-05.csv --profil 6h --ausgabe rechen-ergebnisse/bootstrap-6h
python3 -B einheitenbootstrap.py messungen/aufnahme-30min.csv --profil 30min --ausgabe rechen-ergebnisse/bootstrap-30min
```

Der zweite Dateiname ist ein neutraler Platzhalter, kein behaupteter vorhandener Mitschnitt. Die Quelle wird nicht verändert. Alte Ergebnisordner werden nicht überschrieben. Die Verarbeitung setzt koerper.pruefen voraus, weist Fortsetzungsketten zurück und liest keine als 24h benannte Aufnahme. Ein fehlendes oder undefiniertes Intervall bleibt sichtbar; es wird nicht durch null ersetzt.

Geschützte Quellen und Firmware sind unverändert. Alex kann den Prototyp und das Bootstrapwerkzeug getrennt beurteilen; echte Bootstrapresultate bleiben bis zum Eingang der freigegebenen Daten offen.

## Ergänzende unabhängige Randprüfung

Ein zusätzlicher Review fand eine Abweichung allein in den ergänzenden historischen
Phasenzählern: Frühe Phasen vor H fehlten dort, obwohl die historische Referenz
sie mit verkürztem Vorfenster zählt. Die historische Ausgabe folgt jetzt dieser
Referenz; die Bootstrapzählung verlangt weiterhin vollständige Vorfenster. Der
Handfall Phase 5 / Warnung 4 / H=30 ergibt historisch 1/1, im Bootstrap 0/0.
Alle 14 Bootstraptests bestehen. Die drei Taktquoten und die Bootstrapintervalle
ändern sich durch diese Korrektur nicht. Der eingefrorene Verweildauer-Prototyp,
sein Vergleichslabor und sämtliche Entwicklungs-/Kontrollzahlen blieben unverändert.
