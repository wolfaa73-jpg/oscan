# Schritt 2: LED-Zuordnung

Dieser Zweig baut auf Schritt 1 auf. Nur Fahrtmodus **mit aktiviertem Empfinden** verwendet
EmpfindenLed.h. Außerhalb der Fahrt und bei Fahrt ohne Empfinden bleibt die alte Anzeige.

| Priorität / Eingang | RGB / Muster |
| --- | --- |
| Protokoll voll | (4,0,4), dauerhaft, höchste Priorität |
| Anlauf oder Messung fehlt | (2,2,2), dauerhaft |
| gerade = 0 | (0,2,0) |
| gerade wärmer | (H, H/4 abgerundet, 0) |
| gerade kälter | (0, H/4 abgerundet, H) |
| woanders ≠0 | jeder vierte Takt ein eigener Farbimpuls in dessen Richtung, H=min(4,Stufe+1) |

| Stufe gerade | 0 | 1 | 2 | 3 | 4 | 5 | ≥6 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H | 2 | 3 | 4 | 6 | 8 | 12 | 16 |

Der vierte Takt ist `fahrtTakt % 4 == 3`; die anderen drei zeigen „gerade“.
Kein zusätzlicher Timer, kein schnelleres LED-Schreiben als vorher, kein voller Atemzyklus:
der gesonderte langsame Impuls lässt sich bei einem Update je Sekunde klar testen.
Maximaler Kanalwert 16/255 statt bisher 40/255. Das ist eine gesetzte Dämpfung, kein
Nachweis vernachlässigbarer Eigenwärme. Der Farbimpuls kann bei gleichzeitig gleicher
Richtung wie gerade subtil sein; am echten Board prüfen, bevor die Zuordnung feststeht.

Die reine Funktion liefert Muster und Farbe ohne GPIO. Der Hosttest prüft alle 59.536
Kombinationen aus −30..30 in beiden Schichten, Anlauf, vollem Log und vier Phasen.
Die bestehende Hostprüfung kontrolliert außerdem unveränderte Ausgaben ohne Schalter.

Alex: normal, kälter/wärmer je Stufe, langsamer Hinweis bei gerade=0, Anlauf und volles
Protokoll am Gerät ansehen. LED-Helligkeit und Einfluss auf die Chiptemperatur sind noch
nicht gemessen. Die Anzeige ist eine Zuordnung von Zahlen, kein weiterer Lernzustand.
