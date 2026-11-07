# Ideenlabor A, B und C – Ergebnisse

Durchgeführt mit neuen künstlichen Miniwelten; ohne laufenden Kern, Firmware oder Geräteaufnahmen.

**Entwicklungsstand – noch keine unabhängige Prüfung.**

Namensraum: `OSCAN-IDEEN-v2`. Planfassung 0.3. 58 Defekt-/Funktionsprüfungen bestanden.
Freeze-Commit: `noch nicht gesetzt; Prüfziehungen gesperrt`.
Rohzähler, einzelne Seeds, Fragearten, Fristenfenster und Ressourcen: [JSON](IDEEN-ENTWICKLUNG.json).

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
| kandidat | 0.2344 / 0.0984 | 0.4956 / 0.4953 | 0.2686 / 0.1497 | 207 | 102 |
| Immer warnen | 0.4997 / 0.5009 | 0.4966 / 0.4972 | 0.4987 / 0.4993 | 32 | 32 |
| Nie warnen | 0.5003 / 0.4991 | 0.5034 / 0.5028 | 0.5013 / 0.5007 | 32 | 32 |
| Letzter Ausgang | 0.5020 / 0.5082 | 0.5029 / 0.4993 | 0.5023 / 0.5086 | 32 | 32 |
| ungeteilt | 0.5045 / 0.5035 | 0.4956 / 0.4953 | 0.5072 / 0.5075 | 67 | 67 |
| x | 0.2394 / 0.2369 | 0.4998 / 0.4978 | 0.2605 / 0.2687 | 102 | 102 |
| z | 0.3649 / 0.3633 | 0.4980 / 0.5004 | 0.3746 / 0.3778 | 102 | 102 |
| xz | 0.1020 / 0.0984 | 0.4939 / 0.4935 | 0.1701 / 0.2006 | 172 | 172 |

Bewertungsfenster 257–768, Welt S: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5077 | 487 | 521 | 0.4958 | 0.9041 | 0.4991 |
| Immer warnen | 10240 | 10240 | 5129 | 0 | 1.0000 | 0.4991 | 0.4991 |
| Nie warnen | 10240 | 0 | 0 | 5111 | 0.0000 | NA | 0.4991 |
| Letzter Ausgang | 10240 | 5115 | 2604 | 2600 | 0.4995 | 0.4909 | 0.4991 |
| ungeteilt | 10240 | 5965 | 3005 | 2151 | 0.5825 | 0.4962 | 0.4991 |
| x | 10240 | 5575 | 1445 | 981 | 0.5444 | 0.7408 | 0.4991 |
| z | 10240 | 5305 | 1957 | 1763 | 0.5181 | 0.6311 | 0.4991 |
| xz | 10240 | 5077 | 487 | 521 | 0.4958 | 0.9041 | 0.4991 |

Bewertungsfenster 257–768, Welt N: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5947 | 2935 | 2137 | 0.5808 | 0.5065 | 0.5028 |
| Immer warnen | 10240 | 10240 | 5091 | 0 | 1.0000 | 0.5028 | 0.5028 |
| Nie warnen | 10240 | 0 | 0 | 5149 | 0.0000 | NA | 0.5028 |
| Letzter Ausgang | 10240 | 5154 | 2559 | 2554 | 0.5033 | 0.5035 | 0.5028 |
| ungeteilt | 10240 | 5947 | 2935 | 2137 | 0.5808 | 0.5065 | 0.5028 |
| x | 10240 | 5874 | 2911 | 2186 | 0.5736 | 0.5044 | 0.5028 |
| z | 10240 | 6057 | 3016 | 2108 | 0.5915 | 0.5021 | 0.5028 |
| xz | 10240 | 5878 | 2891 | 2162 | 0.5740 | 0.5082 | 0.5028 |

Bewertungsfenster 257–768, Welt R: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5114 | 760 | 773 | 0.4994 | 0.8514 | 0.5007 |
| Immer warnen | 10240 | 10240 | 5113 | 0 | 1.0000 | 0.5007 | 0.5007 |
| Nie warnen | 10240 | 0 | 0 | 5127 | 0.0000 | NA | 0.5007 |
| Letzter Ausgang | 10240 | 5129 | 2605 | 2603 | 0.5009 | 0.4921 | 0.5007 |
| ungeteilt | 10240 | 5920 | 2995 | 2202 | 0.5781 | 0.4941 | 0.5007 |
| x | 10240 | 5366 | 1495 | 1256 | 0.5240 | 0.7214 | 0.5007 |
| z | 10240 | 5674 | 2208 | 1661 | 0.5541 | 0.6109 | 0.5007 |
| xz | 10240 | 5141 | 1034 | 1020 | 0.5021 | 0.7989 | 0.5007 |

S: relevante Teilung 20/20; Verlustdifferenz gegen ungeteilt -0.405078. N: 0/20 Teilungen. R: mittlere Restdifferenz gegen Vierertabelle -0.031576.
Die 200-Folgen-Abnahme wird auf diesem Entwicklungssatz nicht vorgenommen.

### global128

| Verfahren | S: alle / Bewertung | N: alle / Bewertung | R: alle / Bewertung | Spitze Bytes | Nach Auswahl Bytes |
|---|---:|---:|---:|---:|---:|
| kandidat | 0.2333 / 0.0984 | 0.4985 / 0.5000 | 0.2993 / 0.1976 | 161 | 161 |
| Immer warnen | 0.4997 / 0.5009 | 0.4966 / 0.4972 | 0.4987 / 0.4993 | 32 | 32 |
| Nie warnen | 0.5003 / 0.4991 | 0.5034 / 0.5028 | 0.5013 / 0.5007 | 32 | 32 |
| Letzter Ausgang | 0.5020 / 0.5082 | 0.5029 / 0.4993 | 0.5023 / 0.5086 | 32 | 32 |
| ungeteilt | 0.5021 / 0.5017 | 0.4985 / 0.5000 | 0.5035 / 0.5037 | 161 | 161 |
| x | 0.2389 / 0.2373 | 0.4980 / 0.4961 | 0.2829 / 0.3034 | 161 | 161 |
| z | 0.3652 / 0.3646 | 0.4963 / 0.4997 | 0.3883 / 0.3991 | 161 | 161 |
| xz | 0.1020 / 0.0984 | 0.4969 / 0.4985 | 0.1688 / 0.1986 | 161 | 161 |

Bewertungsfenster 257–768, Welt S: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5077 | 487 | 521 | 0.4958 | 0.9041 | 0.4991 |
| Immer warnen | 10240 | 10240 | 5129 | 0 | 1.0000 | 0.4991 | 0.4991 |
| Nie warnen | 10240 | 0 | 0 | 5111 | 0.0000 | NA | 0.4991 |
| Letzter Ausgang | 10240 | 5115 | 2604 | 2600 | 0.4995 | 0.4909 | 0.4991 |
| ungeteilt | 10240 | 5624 | 2825 | 2312 | 0.5492 | 0.4977 | 0.4991 |
| x | 10240 | 5441 | 1380 | 1050 | 0.5313 | 0.7464 | 0.4991 |
| z | 10240 | 5108 | 1865 | 1868 | 0.4988 | 0.6349 | 0.4991 |
| xz | 10240 | 5077 | 487 | 521 | 0.4958 | 0.9041 | 0.4991 |

Bewertungsfenster 257–768, Welt N: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5553 | 2762 | 2358 | 0.5423 | 0.5026 | 0.5028 |
| Immer warnen | 10240 | 10240 | 5091 | 0 | 1.0000 | 0.5028 | 0.5028 |
| Nie warnen | 10240 | 0 | 0 | 5149 | 0.0000 | NA | 0.5028 |
| Letzter Ausgang | 10240 | 5154 | 2559 | 2554 | 0.5033 | 0.5035 | 0.5028 |
| ungeteilt | 10240 | 5553 | 2762 | 2358 | 0.5423 | 0.5026 | 0.5028 |
| x | 10240 | 5479 | 2705 | 2375 | 0.5351 | 0.5063 | 0.5028 |
| z | 10240 | 5644 | 2806 | 2311 | 0.5512 | 0.5028 | 0.5028 |
| xz | 10240 | 5568 | 2762 | 2343 | 0.5437 | 0.5040 | 0.5028 |

Bewertungsfenster 257–768, Welt R: 512 Takte je Spur; Quotienten aus summierten Rohzählern.

| Verfahren | Takte | Warnungen | Fehlalarme | Verpasst | Warnanteil | Trefferquote | Grundrate |
|---|---:|---:|---:|---:|---:|---:|---:|
| kandidat | 10240 | 5092 | 994 | 1029 | 0.4973 | 0.8048 | 0.5007 |
| Immer warnen | 10240 | 10240 | 5113 | 0 | 1.0000 | 0.5007 | 0.5007 |
| Nie warnen | 10240 | 0 | 0 | 5127 | 0.0000 | NA | 0.5007 |
| Letzter Ausgang | 10240 | 5129 | 2605 | 2603 | 0.5009 | 0.4921 | 0.5007 |
| ungeteilt | 10240 | 5367 | 2699 | 2459 | 0.5241 | 0.4971 | 0.5007 |
| x | 10240 | 5070 | 1525 | 1582 | 0.4951 | 0.6992 | 0.5007 |
| z | 10240 | 5274 | 2117 | 1970 | 0.5150 | 0.5986 | 0.5007 |
| xz | 10240 | 5103 | 1005 | 1029 | 0.4983 | 0.8031 | 0.5007 |

S: relevante Teilung 20/20; Verlustdifferenz gegen ungeteilt -0.403223. N: 0/20 Teilungen. R: mittlere Restdifferenz gegen Vierertabelle -0.009115.
Die 200-Folgen-Abnahme wird auf diesem Entwicklungssatz nicht vorgenommen.

Die Zustandsbytes enthalten auch Suchmodelle, Auswahlfehler, laufende Rundenzähler und die ausgewiesenen Arbeitszähler. Blattfenster werden nach Auswahl freigegeben. Arbeitszähler im JSON unterscheiden Ergebnislesungen, Fensterupdates und Haupt-/Nebenprognosen. Geringerer laufender Zustand ist kein Nachweis geringerer Spitze oder Energie.

## C: Darstellung, Herkunft und Widerruf

Verlust: richtig 0, falsch 4, unbekannt 1. Nenner sind die tatsächlich gestellten Fragen, nicht die 256 Beobachtungstakte; diese Tabellen sind keine Warnquoten je Gerätetakt. Zuerst Fragen innerhalb einer Kategorie, dann Prüfpunkte und Kategorien, danach Seeds und Familien gleich gewichtet. Der Widerruf ist eine eigene Kategorie. Nutzenentscheidungen verwenden exakte Brüche.

Die Tabelle wird für jedes Budget getrennt ausgewertet.

### Budget 32 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 32 | regel | 0.241720 | 0.434676 | 1.088294 | 0.588230 | 32 |
| 32 | ring | 0.602297 | 0.606036 | 1.088294 | 0.765542 | 32 |
| 32 | zaehler | 0.755609 | 1.152663 | 1.226190 | 1.044821 | 28 |
| 32 | halbiert | 0.755609 | 1.048497 | 1.257440 | 1.020515 | 28 |
| 32 | unbekannt | 0.974359 | 0.975580 | 0.976190 | 0.975376 | 12 |
| 32 | konstant_0 | 1.307692 | 1.308913 | 1.274802 | 1.297136 | 12 |
| 32 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.308913 | 1.344246 | 1.320284 | 12 |

Budget 32: kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Entwicklungssatz; kein unabhängiger Nutzennachweis.


### Budget 64 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 64 | regel | 0.031250 | 0.487752 | 0.952381 | 0.490461 | 64 |
| 64 | ring | 0.278045 | 0.470314 | 0.952381 | 0.566913 | 64 |
| 64 | zaehler | 0.755609 | 1.152663 | 1.226190 | 1.044821 | 28 |
| 64 | halbiert | 0.755609 | 1.048497 | 1.257440 | 1.020515 | 28 |
| 64 | unbekannt | 0.974359 | 0.975580 | 0.976190 | 0.975376 | 12 |
| 64 | konstant_0 | 1.307692 | 1.308913 | 1.274802 | 1.297136 | 12 |
| 64 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.308913 | 1.344246 | 1.320284 | 12 |

Budget 64: kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Entwicklungssatz; kein unabhängiger Nutzennachweis.


### Budget 128 Byte

| Budget | Verfahren | Wiederholung | Wechsel | Unregelmäßig | Gleichgewichteter Verlust | Bildspitze Bytes |
|---:|---|---:|---:|---:|---:|---:|
| 128 | regel | 0.031250 | 0.565972 | 0.689484 | 0.428902 | 128 |
| 128 | ring | 0.055288 | 0.483936 | 0.689484 | 0.409570 | 128 |
| 128 | zaehler | 0.755609 | 1.152663 | 1.226190 | 1.044821 | 28 |
| 128 | halbiert | 0.755609 | 1.048497 | 1.257440 | 1.020515 | 28 |
| 128 | unbekannt | 0.974359 | 0.975580 | 0.976190 | 0.975376 | 12 |
| 128 | konstant_0 | 1.307692 | 1.308913 | 1.274802 | 1.297136 | 12 |
| 128 | Immer warnen (zusätzliche Referenz) | 1.307692 | 1.308913 | 1.344246 | 1.320284 | 12 |

Budget 128: kein strikt kleinerer Gesamtverlust als alle fünf vorab benannten Pflichtgegner im Entwicklungssatz; kein unabhängiger Nutzennachweis.

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
