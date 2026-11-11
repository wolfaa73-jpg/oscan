# Empfinden v2: Festlegung vor der erneuten Nachrechnung

Anlass: Alex’ Entscheidung in PR #10 vom 11.11.2026, Kommentar 6807417888.
V1 bleibt erhalten: EMPFINDEN-PLAN.md, die v1-Ergebnisdatei sowie bytegleiche Referenzen
in referenzen/empfinden_v1.py und referenzen/Empfinden-v1.h (Stand e45c8e2).
Die vier Aufnahmen und v1-Ergebnisse sind bekannt. Dies ist ein vorab festgelegter
Versionsvergleich an bekannten Daten, keine unabhängige oder blinde Leistungsprüfung.

## Festgelegte Änderungen

- L: 3600 gültige Takte Halbwertszeit, von Alex entschieden. M bleibt bei 600.
- Geladener Neustart: keine Wort-Sperre. Der kalte Anlauf bleibt bei insgesamt 1800
  gültigen Takten. Ein noch nicht ausgereifter gespeicherter Stand bleibt im Kaltanlauf.
- Beide Maßbänder lernen weiterhin nicht in den ersten 600 gültigen Takten nach jedem
  Start. Die Filter M/L und die Selbstvorhersage laufen dabei weiter.
- Maßband woanders: eigene Halbwertszeit HW=7200 Lerntakte (gesetzt). Es reagiert damit
  langsamer als der 1-h-Bezug, aber innerhalb des ersten Tages. HW ist ausdrücklich von
  HL getrennt. Die alte anfängliche 1/n-Gewichtung kommt nicht zurück.
- Startmaß woanders bleibt 0,5 °C als **Prior**, Mindestmaß sinkt auf 0,1 °C (gesetzt).
  So kann eine ruhige Umgebung auch ein kleineres eigenes Maß hinterlassen. Die lange
  Mittelung von M/L glättet die 1-°C-Quantisierung; 0,1 °C ist ein technischer Boden,
  keine Behauptung über die Genauigkeit des Sensors. Startvarianz 0,25, Bodenvarianz 0,01.
- Schutz vor Selbstnormalisierung bleibt: kein RMS-Update bei Betrag ≥4×vorheriges Maß.
  2 h gelten daher in angenommenen Lerntakten, nicht zwangsläufig in Wanduhrzeit.
  Bei 8 h durchgehend freigegebenem Lernen bleibt 1/16 der Startvarianz; bei ständig
  gesperrtem Lernen gibt es diese Zusage ausdrücklich nicht. Zähler nw wird berichtet.
- Schnelles Maßband, Hysterese, Stufen und Vorhersage bleiben rechnerisch unverändert.
- Konstantenmeldung und gespeicherter Empfindenstand bekommen Version 2. V1-Stände
  dürfen explizit übernommen werden: Filter und RMS werden erhalten, erst die folgenden
  Takte rechnen nach v2. Das ist kein rückwirkend aus der Vergangenheit berechneter v2-Stand.
  Alte CSVs werden anhand ihrer Konstantenversion mit der eingefrorenen v1-Referenz geprüft.

## Vorprobe an künstlichen Daten, bevor echte Daten neu gerechnet werden

1. Host/Python mindestens 12.000 Takte, Einbruch, Fehlwerte/Bereichsfehler, Sichern/Laden:
   vollständige Zeilen und portable Zustandsbytes identisch.
2. Reifer Stand, Neustart, sofort stark negatives Fehlermittel ergibt kälter mindestens Stufe 2
   schon im ersten Takt; qg und qw während 600 gültiger Takte unverändert.
3. Kalter Start: bis Takt 1800 keine Wörter. Fehlende Werte verbrauchen keinen Lernschutz.
4. Konstante 37 °C über 8 h sowie eine bekannte sinusförmige Umgebung (Amplitude 2 °C,
   Periode 3600 Takte): das woanders-Maß darf kleiner bzw. größer als sein 0,5-°C-Prior werden.
   Das prüft Anpassbarkeit, keine reale Güte. Keine Parametersuche an den vier Aufnahmen.
5. Import alter Zustände und Nachrechnung einer alten CSV prüfen.

## Erneute Nachrechnung, eingefrorene Auswertungsregeln

Dieselben vier Rohdateien und derselbe 8-h-Vorlauf vor dem Kälteversuch. Fahrt: dieselben
Neustarts und gespeicherten Vorhersagestände wie v1. Zusätzlich vollständige Stufenfolgen,
Maßband-Verlauf je 1800 Takte, gültige Takte, Kaltanlauf und ausgeschlossene Neustarttakte.

Jede Häufigkeit bekommt Zähler und Nenner. Nebeneinander:
1. jeweilige betriebsfähige Takte (Version entscheidet über Wortfreigabe),
2. die Schnittmenge dieser Takte, damit Anlaufänderungen den Vergleich nicht verfälschen,
3. alle gültigen Takte nach dem ersten kalten Anlauf, mit unterdrückten v1-Wörtern als solchen.
Die Regel „nie auffällig“ (0/N) und das bisherige Überraschungsbit stehen daneben.
Insbesondere werden die ursprünglichen 31076/35850 aus v1 wiederhergestellt; Alex’ 95 %
werden ohne seine genaue Zählweise nicht mit einem erfundenen Nenner erklärt.

Für jeden der zwölf Starts: erste 60 Takte, erster schneller Ausschlag ab Stufe 2, Richtung,
Maximum und Maßband vor/nach dem 600-Takt-Lernschutz. Die erste Pressluft (Fenster
12500–13000) wird gesondert berichtet, ebenso die bereits verwendeten Ereignisfenster.
Alex’ Erwartung: woanders deutlich seltener, Einschalt-Momente und erste Pressluft sichtbar.
Das sind zu prüfende Erwartungen, keine Bedingungen für nachträgliches Nachstimmen.

Für #11: LED-Werte nicht ändern. Anteil der Takte mit woanders≠0 und die tatsächlichen
Vier-Takt-Impulse im Fahrtmodus zählen; Stufe 1 zählt für die LED ebenfalls. Helligkeit
für gerade bleibt ausschließlich in hell[] einschließlich Stufe 0 festgelegt.

Vorprobe: Eine Sinus-Amplitude von 1,5 °C war für den Test „Maß größer als Prior“
zu klein: Nach beiden Filtern lag das Maß bei 0,495 °C. Deshalb prüft die bekannte
Testfolge jetzt mit 2 °C Amplitude beide Anpassungsrichtungen. Keine Modellkonstante
wurde dafür verändert und noch keine der vier echten Aufnahmen mit v2 nachgerechnet.
