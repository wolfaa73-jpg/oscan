# Funk-Wärmeprobe v1, vor jedem Gerätelauf

Gesetzte Reihenfolge und Auswertung. Zuerst wird `test_funkversuch.py` an bekanntem
künstlichem Körper ausgeführt. Kein echter Funk-Wärmelauf ist hier bekannt oder ausgewertet.
Keine neue Eingangsvariable der Selbstvorhersage: Last bleibt deren einziger Handlungsreiz.

## Durchführung bei Alex

Knoten allein, kein Display nötig, feste Stromversorgung und Lage. Kein Anfassen, Pusten,
Lüfter oder anderer Reiz während der drei Stunden; Änderungen daneben mit Takt notieren.
Fahrtmodus für diese Aufnahme aus. Firmware des dritten PR verwenden.

```sh
cd Alex-Lerngedaechtnis
python3 koerper.py aufnahme funk.csv --port PORT --regel startwert --blick 60 \
  --grenzen 380 390 65536 16384 20000 200000 --intervall-ms 1000 --takte 10800 --funkversuch
python3 funkversuch.py funk.csv
```

PORT ist ein lokaler Platzhalter; Portkennung nicht veröffentlichen. Begleitdateien bleiben
neben funk.csv. Die Auswertung braucht nur diesen CSV-Pfad und überschreibt nichts.

| Takte | Zustand | ausgewertete Takte |
| --- | --- | --- |
| 1–1800 | Anlauf, Funk aus | 901–1800 nur beschreibend |
| 1801–3600 | Funk aus | 2701–3600 |
| 3601–5400 | Funk bereit, keine Pakete | 4501–5400 |
| 5401–7200 | ein Broadcast je Takt | 6301–7200 |
| 7201–9000 | Funk bereit, keine Pakete | 8101–9000 |
| 9001–10800 | Funk aus | 9901–10800 |

Phasenlänge 1800 und Beruhigung 900 sind **gesetzt**, nicht am Funk gemessen. Auswertung
zählt je Takt; jede Phase hat als einfachsten Ereignismaßstab „nie auffällig“, 0/N.
Temperaturmaßstab ist das Mittel beider Aus-Phasen, Bereitschaft das Mittel beider
Bereit-Phasen. Symmetrische Zeitpunkte heben eine lineare Drift auf, nicht beliebige Drift.
Berichtet werden Bereitschaft minus Aus, Senden minus Bereitschaft, Aus nachher minus
vorher; dazu dieselben Kontraste beider Normalmaße. Keine nachträglich gewählte Erfolgsgrenze.
Bei jedem Phasenbeginn zusätzlich erste 60 Takte: Zahl schneller Stufen ≥2 und erster Takt.
Das Überraschungsmaß kommt aus Empfinden v1, ohne weitere Anpassung.

Reizbits: 1 Last, 2 Leck, 4 Bremse bleiben unverändert; 8 ist der Aufruf zum Senden im
aktuellen Takt, 16 bedeutet Funk bereit, 32 API-Sendefehler. Temperatur wird davor gemessen:
eine Wirkung des gesendeten Pakets kann frühestens in späteren Takten auftauchen.
Ein erfolgreicher API-Aufruf beweist keinen Empfang. Der Broadcast braucht keinen Empfänger.
Bei Sendefehler bricht die Aufnahme sichtbar ab. Kein Router, keine SSID, keine feste
Geräteadresse, Kanal 6 gesetzt. WiFi-Stromsparmodus aus, damit Bereitschaft definiert ist.

Strenge Prüfung: alle 10800 Takte lückenlos, passende Reizfolge, keine fehlende Temperatur,
keine Abbruchdatei, unveränderte Vorhersage und beide Empfindungsschichten nachgerechnet.
Bei Abweichung keine Wärme-Kontraste ausgeben. Der Lauf ist dann technisch ungültig.

## Künstliche Vorprobe und Grenzen

Kunstkörper mit Zeitkonstante 30 s und deterministischer Umgebung: bekanntes Plus 2 °C
bei Bereitschaft, zusätzlich 0,5 °C beim Senden, außerdem Nullwirkung und lineare Drift.
Die Auswertung muss die bekannten Kontraste bis 0,02 °C wiederfinden. Diese Toleranz
prüft das Werkzeug an künstlichen Daten; sie ist keine Gerätegrenze und kein Effektbeleg.
Danach mit gemessener Umgebungsstreuung aus kunstkoerper.GEMESSEN: Streuung der Schätzwerte
berichten statt einen sicheren Erfolg zu fordern. Derselbe Fehler kann aus Umgebung oder
Funk entstehen. Ein einziger Lauf liefert keinen kausalen Beweis; bei interessantem Befund
wiederholen und die Abschnittsfolge in einem neuen vorab festgelegten Versuch umkehren.
Erst anschließend gemeinsam entscheiden, ob das Sendebit Eingang der Vorhersage wird.
