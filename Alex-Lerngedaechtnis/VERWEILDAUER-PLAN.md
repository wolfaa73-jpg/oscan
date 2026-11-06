# Verweildauer und Richtung: Plan vor der ersten Auswertung

Neuer Python-Prototyp, keine Änderung von kern.py, vokabular.py oder Firmware.
Keine echten Aufnahmen werden für Wahl oder Anpassung benutzt. Alte Kontrollen
aus #4 sind bereits bekannt und werden nicht als unabhängiger Nachweis verwendet.

## Modell und feste Entscheidungen

`Verweildauergedaechtnis` hat beobachte(vorher, jetzt), beleg(wort) und
kritisch_binnen(wort, horizont). Richtung bedeutet hier Ziel eines tatsächlichen
Zustandsausgangs, nicht Temperatursteigung. Pro Ausgangswort werden abgeschlossene
Lauflängen und Ausgangsrichtungen getrennt gelernt. Eine Folge von 50 gleichen
Wörtern ist keine Folge von 49 Richtungsbelegen. Nur beim beobachteten Ausgang
altern eigene Dauern und Richtungen mit Halbwertszeit sechs abgeschlossenen Läufen.

Dauer und Richtung werden bedingt auf das Wort als unabhängig behandelt. Das ist
eine starke, widerlegbare Vereinfachung. Lange Läufe mit anderem Ausgang als kurze
können deshalb falsch vorhergesagt werden. Der erste linkszensierte Lauf liefert
keine vollständige Dauer; sein beobachteter Ausgang darf die Richtung lehren.
Der letzte noch laufende Zustand liefert keine erfundene Abschlussbeobachtung.
Sein bereits beobachtetes Alter bedingt die Restdauer auf bisheriges Überleben.

Erbegewicht drei je vorhandener Kante; ausdrücklich zusätzlich angenommene
Erbdauer ein Takt. Dieses Dauerprior ist keine Gerätebeobachtung. Erbe verblasst
mit Halbwertszeit sechs eigenen Zustandsausgängen. Mindestbeleg drei, Schwelle
0,6, Horizont 30; keine Rasterwahl. beleg ist das kleinere Gewicht aus Richtung
und zur aktuellen Dauer passenden Läufen. Fehlende Dauerabdeckung liefert Beleg
null und keine Warnung, ausdrücklich keinen belegten gesunden Zustand.

Der Blick summiert Erneuerungspfade bis zum ersten kritischen Zustand. Er hält
die aktuellen Parameterschätzungen im Blickfenster fest. Der Prototyp besitzt
keine Firmware-Zeit-, Energie- oder Speicherzusage; die Zahl unterschiedlicher
Dauern kann wachsen. Kontrollierte Handfolgen prüfen Dauergrenzen, Rückwege,
Zensierung, Kausalität, Abfragen ohne Lernen und die Unabhängigkeitsgrenze.

## Vergleich und Einfrieren

Unveränderter Erzeuger aus signallabor.py, alle vier Familien, je 960 Takte.
Entwicklung: Satz entwicklung, Seeds 300000–300015. Vorgeschlagene neue Prüfung:
Satz kontrolle, Seeds 300100–300131, **erst nach festgehaltenem Commit**, ohne
nachträgliche Auswahl. Kein neuer Prüfsatz vor Freigabe des Hauptagenten.
Generator, Prototyp, Runner, Tests und Plan werden vor der Prüfung eingefroren.
Auswertung erzeugt nur neue Ergebnisordner und neutrale Dateinamen.

Gegenüber stehen Feste Regel, Festes Erbe, Startwert, Ohne Erbe, Letzter Durchgang,
Immer warnen, Nie warnen und der neue Prototyp. Jeweils grobe gemeinsame Sicht
und ein eigenes Modell je Signal. Ergebnisse pro Familie bleiben erhalten.
Die grobe Immer-warnen-Referenz bleibt die vorhandene globale Warnfolge: Ein
kritisches fremdes Signal unterdrückt den Alarm und kann im eigenen Signalnenner
einen Warnanteil unter 100 Prozent ergeben. Das ist Gerätesemantik, keine
signalweise ideale Referenz. Je Signal warnt Immer warnen an jedem geeigneten
eigenen Takt. Diese Unterscheidung darf beim Lesen der Tabellen nicht verschwinden.
Maßgeblich sind Taktraten: Warnanteil, Trefferquote und Grundrate; keine durch
zusammengefasste Warnläufe begünstigte Genauigkeit. Primär alle eigenen nicht
kritischen Takte, zusätzlich hohe Signaltakte für Anschluss an die dokumentierte
Speicherfrage. Die letzten 30 Takte sind ausschließlich Zukunft. Phasen zählen
nur mit vollem Vorfenster, unmittelbar benachbarte kritische Takte bilden eine Phase.
Verpasste Zieltakte und falsche Warntakte sowie unangekündigte Phasen werden
zusätzlich berichtet. Beide Kostenbegriffe bei r=10 bleiben getrennt und werden
je 1000 Instrumenttakte angegeben. Keine Summierung signalweiser Aktionskosten.

Es gibt keine vorab behauptete Überlegenheit. Der Bericht nennt Verluste gegen
die einfachen Gegner und Einschränkungen. Nur mechanische Korrektheit wird durch
Tests abgenommen; Nutzen bleibt ein Vergleich in diesen künstlichen Familien.
