# Ideenlabor A, B und C – Ergebnisse

Durchgeführt mit neuen künstlichen Miniwelten; ohne laufenden Kern, Firmware oder Geräteaufnahmen.

**Prüfsatz nach Freeze.**

Namensraum: `OSCAN-IDEEN-v2`. Planfassung 0.3. 58 Defekt-/Funktionsprüfungen bestanden.
Freeze-Commit: `278ebad39ab3850ef8c7b4349e4a6e30b8a4b27d`.
Rohzähler, einzelne Seeds, Fragearten, Fristenfenster und Ressourcen: [JSON](IDEEN-PRUEFUNG.json).

## A: getrennte Handlungsfolgen

Die Sollrechnung wurde ausgeführt. A=1 bezeichnet Entlasten, nicht die nachgewiesene Rettung eines Auftrags.
Die gemeinsame Beobachtung A=1/Y=0 wird neutral als Handlung ohne anschließenden Ausfall gezählt. Weil die Handlung den Ausgang verändert, belegt dieser Quotient weder Warnpräzision noch Rettung.

| Verfahren | 32 Bewertung: Kosten | 16+32 Aufgaben: Kosten | 16+8 Aufgaben: Kosten |
|---|---:|---:|---:|
| Vier Beobachtungen je Zelle | 96 | 208 | 136 |
| Eine Beobachtung je Zelle | 96 | 160 | 88 |
| Nie entlasten | 160 | 240 | 120 |
| Immer entlasten (Immer warnen) | 288 | 432 | 216 |
| Bei Vorzeichen | 224 | 336 | 168 |

Summen über die vier vorab gleich gewichteten Welten, jeweils dieselbe Aufgabenanzahl pro Verfahren. Der einfachere adaptive Gegner ist günstiger; der Vierfach-Kandidat verdient gegenüber ihm seine Zusatzkosten nicht.
A1 bestätigt identische Zustände bei identischer sichtbarer Geschichte; A2 und die getrennte Störfolge sind vollständig im JSON enthalten.

## B: einmalige Wortwahl

Alle Fehler zählen. Die Tabellen zeigen mittlere Verluste je Takt; 257–768 ist das vorab festgelegte Bewertungsfenster. Beide Fensterarten werden vollständig ausgewiesen.

### blatt32

| Verfahren | S: alle / Bewertung | N: alle / Bewertung | R: alle / Bewertung | Spitze Bytes | Nach Auswahl Bytes |
|---|---:|---:|---:|---:|---:|
| kandidat | 0.2328 / 0.1001 | 0.5004 / 0.4988 | 0.2670 / 0.1514 | 207 | 102 |
| Immer warnen | 0.5004 / 0.5013 | 0.5018 / 0.5007 | 0.4997 / 0.5003 | 32 | 32 |
| Nie warnen | 0.4996 / 0.4987 | 0.4982 / 0.4993 | 0.5003 / 0.4997 | 32 | 32 |
| Letzter Ausgang | 0.4987 / 0.4985 | 0.4998 / 0.4981 | 0.4988 / 0.4986 | 32 | 32 |
| ungeteilt | 0.4988 / 0.4991 | 0.5005 / 0.4990 | 0.4988 / 0.4992 | 67 | 67 |
| x | 0.3194 / 0.3181 | 0.4999 / 0.4980 | 0.3345 / 0.3408 | 102 | 102 |
| z | 0.2826 / 0.2804 | 0.5010 / 0.4993 | 0.3010 / 0.3079 | 102 | 102 |
| xz | 0.1037 / 0.1001 | 0.5019 / 0.5011 | 0.1725 / 0.2034 | 172 | 172 |

Bewertungsfenster 257–768, Welt S: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 51177 | 5184 | 5069 | 0.4998 | 0.8987 | 0.4987 |
| Immer warnen | 102400 | 102400 | 51338 | 0 | 1.0000 | 0.4987 | 0.4987 |
| Nie warnen | 102400 | 0 | 0 | 51062 | 0.0000 | NA | 0.4987 |
| Letzter Ausgang | 102400 | 51059 | 25520 | 25523 | 0.4986 | 0.5002 | 0.4987 |
| ungeteilt | 102400 | 57793 | 28921 | 22190 | 0.5644 | 0.4996 | 0.4987 |
| x | 102400 | 54776 | 18143 | 14429 | 0.5349 | 0.6688 | 0.4987 |
| z | 102400 | 54046 | 15848 | 12864 | 0.5278 | 0.7068 | 0.4987 |
| xz | 102400 | 51177 | 5184 | 5069 | 0.4998 | 0.8987 | 0.4987 |

Bewertungsfenster 257–768, Welt N: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 57407 | 28679 | 22399 | 0.5606 | 0.5004 | 0.4993 |
| Immer warnen | 102400 | 102400 | 51273 | 0 | 1.0000 | 0.4993 | 0.4993 |
| Nie warnen | 102400 | 0 | 0 | 51127 | 0.0000 | NA | 0.4993 |
| Letzter Ausgang | 102400 | 51108 | 25494 | 25513 | 0.4991 | 0.5012 | 0.4993 |
| ungeteilt | 102400 | 57401 | 28687 | 22413 | 0.5606 | 0.5002 | 0.4993 |
| x | 102400 | 57552 | 28711 | 22286 | 0.5620 | 0.5011 | 0.4993 |
| z | 102400 | 57707 | 28852 | 22272 | 0.5635 | 0.5000 | 0.4993 |
| xz | 102400 | 57942 | 29062 | 22247 | 0.5658 | 0.4984 | 0.4993 |

Bewertungsfenster 257–768, Welt R: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 51240 | 7788 | 7720 | 0.5004 | 0.8480 | 0.4997 |
| Immer warnen | 102400 | 102400 | 51228 | 0 | 1.0000 | 0.4997 | 0.4997 |
| Nie warnen | 102400 | 0 | 0 | 51172 | 0.0000 | NA | 0.4997 |
| Letzter Ausgang | 102400 | 51157 | 25520 | 25535 | 0.4996 | 0.5011 | 0.4997 |
| ungeteilt | 102400 | 58348 | 29145 | 21969 | 0.5698 | 0.5005 | 0.4997 |
| x | 102400 | 55744 | 19735 | 15163 | 0.5444 | 0.6460 | 0.4997 |
| z | 102400 | 53586 | 16973 | 14559 | 0.5233 | 0.6833 | 0.4997 |
| xz | 102400 | 51559 | 10608 | 10221 | 0.5035 | 0.7943 | 0.4997 |

S: relevante Teilung 200/200; Verlustdifferenz gegen ungeteilt -0.399004. N: 4/200 Teilungen. R: mittlere Restdifferenz gegen Vierertabelle -0.033796.
Vorab-Hürden: S bestanden, N bestanden, R bestanden.

### global128

| Verfahren | S: alle / Bewertung | N: alle / Bewertung | R: alle / Bewertung | Spitze Bytes | Nach Auswahl Bytes |
|---|---:|---:|---:|---:|---:|
| kandidat | 0.2335 / 0.1001 | 0.5001 / 0.4995 | 0.3010 / 0.2013 | 161 | 161 |
| Immer warnen | 0.5004 / 0.5013 | 0.5018 / 0.5007 | 0.4997 / 0.5003 | 32 | 32 |
| Nie warnen | 0.4996 / 0.4987 | 0.4982 / 0.4993 | 0.5003 / 0.4997 | 32 | 32 |
| Letzter Ausgang | 0.4987 / 0.4985 | 0.4998 / 0.4981 | 0.4988 / 0.4986 | 32 | 32 |
| ungeteilt | 0.4997 / 0.4994 | 0.5000 / 0.4993 | 0.5005 / 0.5006 | 161 | 161 |
| x | 0.3199 / 0.3177 | 0.5000 / 0.4986 | 0.3512 / 0.3645 | 161 | 161 |
| z | 0.2826 / 0.2806 | 0.5012 / 0.5004 | 0.3196 / 0.3361 | 161 | 161 |
| xz | 0.1037 / 0.1001 | 0.5009 / 0.4995 | 0.1712 / 0.2013 | 161 | 161 |

Bewertungsfenster 257–768, Welt S: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 51177 | 5184 | 5069 | 0.4998 | 0.8987 | 0.4987 |
| Immer warnen | 102400 | 102400 | 51338 | 0 | 1.0000 | 0.4987 | 0.4987 |
| Nie warnen | 102400 | 0 | 0 | 51062 | 0.0000 | NA | 0.4987 |
| Letzter Ausgang | 102400 | 51059 | 25520 | 25523 | 0.4986 | 0.5002 | 0.4987 |
| ungeteilt | 102400 | 53932 | 27005 | 24135 | 0.5267 | 0.4993 | 0.4987 |
| x | 102400 | 52501 | 16984 | 15545 | 0.5127 | 0.6765 | 0.4987 |
| z | 102400 | 52021 | 14845 | 13886 | 0.5080 | 0.7146 | 0.4987 |
| xz | 102400 | 51177 | 5184 | 5069 | 0.4998 | 0.8987 | 0.4987 |

Bewertungsfenster 257–768, Welt N: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 52547 | 26284 | 24864 | 0.5132 | 0.4998 | 0.4993 |
| Immer warnen | 102400 | 102400 | 51273 | 0 | 1.0000 | 0.4993 | 0.4993 |
| Nie warnen | 102400 | 0 | 0 | 51127 | 0.0000 | NA | 0.4993 |
| Letzter Ausgang | 102400 | 51108 | 25494 | 25513 | 0.4991 | 0.5012 | 0.4993 |
| ungeteilt | 102400 | 52640 | 26323 | 24810 | 0.5141 | 0.4999 | 0.4993 |
| x | 102400 | 52819 | 26372 | 24680 | 0.5158 | 0.5007 | 0.4993 |
| z | 102400 | 53111 | 26610 | 24626 | 0.5187 | 0.4990 | 0.4993 |
| xz | 102400 | 54211 | 27115 | 24031 | 0.5294 | 0.4998 | 0.4993 |

Bewertungsfenster 257–768, Welt R: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 102400 | 51142 | 10290 | 10320 | 0.4994 | 0.7988 | 0.4997 |
| Immer warnen | 102400 | 102400 | 51228 | 0 | 1.0000 | 0.4997 | 0.4997 |
| Nie warnen | 102400 | 0 | 0 | 51172 | 0.0000 | NA | 0.4997 |
| Letzter Ausgang | 102400 | 51157 | 25520 | 25535 | 0.4996 | 0.5011 | 0.4997 |
| ungeteilt | 102400 | 54771 | 27429 | 23830 | 0.5349 | 0.4992 | 0.4997 |
| x | 102400 | 53603 | 19878 | 17447 | 0.5235 | 0.6292 | 0.4997 |
| z | 102400 | 51216 | 17231 | 17187 | 0.5002 | 0.6636 | 0.4997 |
| xz | 102400 | 51287 | 10366 | 10251 | 0.5008 | 0.7979 | 0.4997 |

S: relevante Teilung 200/200; Verlustdifferenz gegen ungeteilt -0.399287. N: 1/200 Teilungen. R: mittlere Restdifferenz gegen Vierertabelle -0.008073.
Vorab-Hürden: S bestanden, N bestanden, R bestanden.

Die Zustandsbytes enthalten auch Suchmodelle, Auswahlfehler, laufende Rundenzähler und die ausgewiesenen Arbeitszähler. Blattfenster werden nach Auswahl freigegeben. Arbeitszähler im JSON unterscheiden Ergebnislesungen, Fensterupdates und Haupt-/Nebenprognosen. Geringerer laufender Zustand ist kein Nachweis geringerer Spitze oder Energie.

## C: Darstellung, Herkunft und Widerruf

Verlust: richtig 0, falsch 4, unbekannt 1. Nenner sind die tatsächlich gestellten Fragen, nicht die 256 Beobachtungstakte; diese Tabellen sind keine Warnquoten je Gerätetakt. Zuerst Fragen innerhalb einer Kategorie, dann Prüfpunkte und Kategorien, danach Seeds und Familien gleich gewichtet. Der Widerruf ist eine eigene Kategorie. Nutzenentscheidungen verwenden exakte Brüche.

Die Tabelle wird für jedes Budget getrennt ausgewertet.

### Budget 32 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 32 | regel | 0.176282 | 0.409598 | 1.100539 | 0.562140 | 32 |
| 32 | ring | 0.575721 | 0.591146 | 1.100539 | 0.755802 | 32 |
| 32 | zaehler | 0.755609 | 1.132440 | 1.234003 | 1.040684 | 28 |
| 32 | halbiert | 0.755609 | 1.069940 | 1.234003 | 1.019851 | 28 |
| 32 | unbekannt | 0.974359 | 0.976190 | 0.976190 | 0.975580 | 12 |
| 32 | konstant_0 | 1.307692 | 1.309524 | 1.226190 | 1.281136 | 12 |
| 32 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.309524 | 1.392857 | 1.336691 | 12 |

Budget 32: kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Prüfsatz.


### Budget 64 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 64 | regel | 0.031250 | 0.588542 | 0.906994 | 0.508929 | 64 |
| 64 | ring | 0.226162 | 0.500744 | 0.906994 | 0.544633 | 64 |
| 64 | zaehler | 0.755609 | 1.132440 | 1.234003 | 1.040684 | 28 |
| 64 | halbiert | 0.755609 | 1.069940 | 1.234003 | 1.019851 | 28 |
| 64 | unbekannt | 0.974359 | 0.976190 | 0.976190 | 0.975580 | 12 |
| 64 | konstant_0 | 1.307692 | 1.309524 | 1.226190 | 1.281136 | 12 |
| 64 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.309524 | 1.392857 | 1.336691 | 12 |

Budget 64: kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Prüfsatz.


### Budget 128 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 128 | regel | 0.031250 | 0.635417 | 0.675967 | 0.447545 | 128 |
| 128 | ring | 0.057692 | 0.622024 | 0.675967 | 0.451894 | 128 |
| 128 | zaehler | 0.755609 | 1.132440 | 1.234003 | 1.040684 | 28 |
| 128 | halbiert | 0.755609 | 1.069940 | 1.234003 | 1.019851 | 28 |
| 128 | unbekannt | 0.974359 | 0.976190 | 0.976190 | 0.975580 | 12 |
| 128 | konstant_0 | 1.307692 | 1.309524 | 1.226190 | 1.281136 | 12 |
| 128 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.309524 | 1.392857 | 1.336691 | 12 |

Budget 128: kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Prüfsatz.

Die zusätzliche Immer-warnen-Referenz ändert die fünf ursprünglichen Pflichtgegner nicht. Ausnahmeabnahme bei 64/128 Byte und Widerruf werden als harte Bedingungen geprüft. Ein korrekt beantworteter, aber im Bild nicht mehr belegbarer historischer Wert gilt als verbotener Cache-Zugriff.

Die logischen C-Arbeitsraumgrenzen sind konservative Pufferbilanzen: Regelkandidat 480 Byte, Ring 448 Byte, andere Verfahren 144 Byte. Sie umfassen Eingabeblock, gepacktes Suffix, Kodierausgabe, Suchtemporäre und eine ausdrücklich angenommene 32-Byte-Verwaltung. Konservativer Regel-Join: 32 Eingabe + 128 gepacktes Suffix + höchstens 120 Abschnittsbytes + 128 neues Bild + 12 Header + 32 Verwaltung = 452 Byte. Die Regelsuche hält nur Parameter/Fehlerzahl und materialisiert erst den Gewinner. Ein entfernter Abschnitt wird sofort freigegeben. Beim Zählerausgabeaufbau fallen höchstens 32 + 16 + 8 + 16 + 24 + 32 = 128 Byte an; die angegebene Grenze 144 enthält Reserve. Für Abfragen liegen die konservativen Zusatzgrenzen bei 120 Bytes Ringslice + 32 Verwaltung = 152 beziehungsweise 32 Rohabschnitt + 26 Ausnahmekopie + 32 Verwaltung = 90 beim Regeldecoder; der alte persistente Zustand zählt separat zum Abbildbudget. Sie sind **keine Messung des Python-RAMs**; Python-Objektoverhead und Interpreter werden nicht als Geräte-RAM ausgegeben. Kodiervergleiche, Zählerupdates und tatsächlich dekodierte Ereignisse bei Abfragen stehen getrennt im JSON.

## Grenzen und Reproduktion

Der Katalog in C ist von Hand passend zur Modellfrage vorgegeben. B untersucht Merkmalsauswahl und festgelegte Fenster, kein frei wachsendes Wörterbuch. A besitzt weder Messrauschen noch lang wirkende Aktionen. Ein bestandenes Ergebnis belegt keinen Nutzen am Gerät.
Die Prüfer testen Daten- und Zustandsverträge, keine Sicherheitsisolation beliebigen Python-Codes. Historische Antworten werden sowohl gegen die Wahrheit als auch gegen die im Bild tatsächlich vorhandenen Belege geprüft.

```sh
python3 -B -m unittest -v test_ideenlabor_pruefer test_ideenlabor test_ideenlabor_c
python3 -B ideenlabor.py --satz entwicklung --ausgabe IDEEN-ENTWICKLUNG.json
# Erst nach identischem, committetem Quellstand:
python3 -B ideenlabor.py --satz pruefung --freeze COMMIT_HASH --ausgabe IDEEN-PRUEFUNG.json
```

Vorhandene Rohwerte und Berichte werden vor Beginn abgewiesen und beim Schreiben exklusiv angelegt. Entwicklung verwendet standardmäßig IDEEN-ENTWICKLUNG.json und IDEEN-ENTWICKLUNG.md; die Prüfung IDEEN-PRUEFUNG.json und IDEEN-ERGEBNISSE.md. Für Wiederholungsläufe sind neue explizite Ausgabepfade erforderlich. Der vollständige 40-stellige Freeze-Hash muss alle Laborquellen, Tests und die Planfassung enthalten. Das Skript vergleicht jede Datei vor Kontrollziehungen und erneut nach dem Lauf. Die 24-Stunden-Aufnahme wird weder geöffnet noch benötigt.

## Zusätzliche Prüferabsicherung nach dem Kontrolllauf

Dieser Abschnitt wurde nach Abschluss ergänzt; die eingefrorenen Verfahren, Parameter, Quellhashes und Kontrollrohwerte wurden nicht geändert.

Der ursprüngliche B-Prüfer `b_speicher` verglich die gemeldete Länge mit der Länge desselben Serializer-Ergebnisses. Er erkannte eine widersprüchliche Meldelänge, aber **keinen tatsächlich gekürzten Serializer**, der wichtige Suchfenster ausließ. Der vorher vorhandene Defekttest belegte diesen stärkeren Fall daher nicht. Diese Grenze wird nicht rückwirkend als vorab erfüllte Prüfung ausgegeben.

Die getrennte [Speicherprüfung](ideenlabor_speicherpruefung.py) untersucht jetzt reale Modellfelder, Blattpuffer, Pending-Zustand und Arbeitszähler. Zusätzliche Cachefelder werden abgewiesen, und der erwartete vollständige Byteinhalt wird unabhängig aufgebaut. Ein absichtlich gekürzter Serializer passiert den ursprünglichen Prüfer und scheitert am neuen. Sieben zusätzliche Tests bestehen; sie gehören zur **nachträglichen Absicherung**, nicht zu den 58 Tests vor dem Kontrolllauf.

Die unveränderten echten Modelle bestanden 73.728 Zustandsprüfungen über drei Handfolgen, alle acht Methoden und beide Fensterarten. Alle 9.600 veröffentlichten B-Rohzeilen entsprechen den analytisch erwarteten Spitzen-, Auswahl- und Endgrößen. Es wurden keine neuen Kontrollziehungen erzeugt. [Audit-Rohwerte und Quellhashes](IDEEN-SPEICHERPRUEFUNG.json) halten diese getrennte Prüfung fest.

## Fachliche Einordnung für die Weiterarbeit

A bestätigt die Trennung von beobachtetem Ergebnis und unbeobachteter Alternative. Die vierfache Kalibrierung ist hier aber teurer als der Ein-Beobachtungs-Gegner: 208 gegenüber 160 Kosteneinheiten im vollständigen Vergleich.

B besteht beide vorab festgelegten S/N/R-Abnahmen. Das belegt die gewählte Informations- und Anpassungsmechanik innerhalb dieser Miniwelt. Über **alle 768 Runden** bleibt die feste Vierertabelle jedoch günstiger im Vorhersageverlust: in S etwa 0,104 gegenüber 0,233 beim Kandidaten. Bei `blatt32` benötigt der Kandidat nach Auswahl weniger gespeicherten Zustand, aber eine höhere Spitze; bei `global128` fällt dieser Zustandsvorteil weg. Daraus folgt kein allgemeiner praktischer Vorteil der zusätzlichen Wortauswahl.

C schlägt im gleichgewichteten Prüfgemisch alle fünf Pflichtgegner bei 32, 64 und 128 Byte. Das darf die Einzelwelten nicht verdecken: In der Wechselfamilie ist der Ringpuffer bei 64 und 128 Byte besser. Beim 128-Byte-Gesamtwert ist der Vorsprung zudem klein: 0,447545 gegenüber 0,451894; auf den Entwicklungsfolgen lag hier der Ringpuffer vorn. Zwölf künstliche Prüffolgen sind kein statistischer oder praktischer Nachweis allgemeiner Überlegenheit. Mehr erhaltene Vergangenheit kann eine heutige Prognose verschlechtern.

Die sinnvolle Fortsetzung wäre eine neue, vorab festgelegte Frage zu Entscheidungskosten beziehungsweise zeitlicher Geltung. Diese Ergebnisse autorisieren weder eine Änderung am laufenden Gerät noch eine nachträgliche Wahl günstiger Parameter oder die Verwendung der reservierten 24-Stunden-Aufnahme.
