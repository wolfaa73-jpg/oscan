# Empfinden v1: Festlegung vor der Nachrechnung echter Aufnahmen

Ausgang: main 847de18. Die bereits veröffentlichten Berichte sind bekannt. Die folgenden
Zahlen und Auswertungen sind eine technische Festlegung, keine neue Blindprüfung dieser Aufnahmen.
Vor der Nachrechnung läuft test_empfinden.py mit kunstkoerper.py, Saat 81: 12.000 Takte,
Temperatursprung −8 °C ab 9001 mit Erholung 300 Takte, fehlende Werte und Laden vor 6500.
Gemessen werden zeilenweise Gleichheit, bytegleicher portabler Zustand, Erkennen innerhalb
40 Takten, langsame Schicht an einer zusätzlichen konstanten Folge (2000 Takte 37 °C, 1200 Takte 29 °C). Kein Nachstimmen an echten Aufnahmen.

## Rechnung und Herkunft der Konstanten

| Größe | Wert | Herkunft |
| --- | --- | --- |
| Schneller Eingang | Fehler der 10-Takt-Vorhersage, Mittel 20 | vorhandene Selbstvorhersage, unverändert |
| Temperaturmittel M / L | Halbwert 600 / 86400 gültige Takte | aus Alex’ Konzept übernommen, gesetzt |
| Maßband schnell / langsam | RMS, Halbwert 3600 / 86400 Lerntakte | schnell wie Vorhersage, langsam wie alte Probe, gesetzt |
| Unteres Normalmaß | 0,2 / 0,5 °C | gesetzt gegen Nullteilung und Überempfindlichkeit bei quantisiertem Sensor |
| Neue Wörter | Betrag ≥ 2, 4, 8 … × Normalmaß | Konzept; Stufe ≥2 heißt auffällig |
| Lernen des Maßbands | nur bei Betrag < 4 × vorheriges Maß | schützt vor Selbstnormalisierung starker Störungen |
| Anlauf kalt / geladen | 1800 / 600 gültige Takte | gesetzt; kalt wie bisher, geladen zehn Minuten Beruhigung |
| Lernbeginn nach Start | nach 600 gültigen Takten | gesetzt wie bisher; auch nach Wiederanlauf |
| Hysterese 1→0 | unter 1,5 × Maß, Aufstieg weiterhin bei 2 | gesetzt; nur Anzeige, nicht Lernfreigabe |
| Maximale Stufe | 30 | technischer int-Bereich, weit über Sensorbereich |

RMS lernt von Anfang an nur mit dem festen Halbwert-Anteil.
M/L lernen auch im Anlauf, RMS nicht während der ersten 600 gültigen Messungen.
Ein Maß je Schicht bleibt zunächst ausreichend: Orte sind nicht bekannt; ortsspezifische
Maße würden ohne unabhängige Ortskennung unterschiedliche Empfindlichkeiten nur verdecken.
Stufe 1 ist sichtbar, ein Ereigniswort zählt erst ab 2. Das verhindert nicht jeden Fehlalarm.
Fehlende Messung: keine neue Aussage, beide Wörter 0 plus gueltig=0, kein Filter-/RMS-Update.
Die Selbstvorhersage behält ihr bisheriges Verhalten bei fehlenden Werten.

„Woanders“ bezeichnet ausdrücklich M minus L, nicht die momentane Temperatur. Nachhinken
ist daher ein Nachgefühl im rechnerischen Sinn. Kein Bewusstseins- oder Ortsnachweis.

## Vorab festgelegte Nachrechnung

1. Beide ruhigen CSVs: je Schicht Zahl ≥2 / gültige Takte außerhalb Anlauf, zusätzlich Anlauf-
   und Fehlwertzahl, Anfangs-/Endmaß. Einfachster Maßstab: nie auffällig (0/N), ferner altes
   Überraschungsbit mit identischem Nenner. Keine nachträgliche Erfolgsgrenze.
2. Kälte-CSV: 8-h-CSV als Vorlauf, kein künstlicher Neustart; vollständige Lauflängenfolge
   beider Wörter und Maßänderung. Zuordnung Pusten/Kühlpacks anhand vorhandener Berichte,
   keine nachträglich erfundenen Zeitmarken.
3. Fahrt: chronologisch, bei Neustart geladene Filter weiter, 600-Takt-Anlauf; bei bei_null
   frische Modelle. Vorhersage aus demselben gespeicherten 30-Takt-Stand wie zuvor. Wörter
   pro zusammenhängender Strecke, Abschnitte durch Neustart getrennt. Ereignisnamen ohne
   exakte Zeitmarken bleiben unsicher. Alte Bits und „nie auffällig“ als Maßstäbe.
4. Abweichung zu alter Regel: je Takt altes Überraschungsbit gegen neues |gerade|≥2;
   außerdem beide Normalmaße. Keine Behauptung besserer Alltagsleistung daraus.

## Kompatibilität und Gerät

Ohne EMPFINDEN 1 bleibt die bisherige serielle Ausgabe unverändert. Warntabelle, kern.py,
vokabular.py und Knoten.h bleiben unverändert. Fahrtstand wird versioniert und alte Stände
bleiben ladbar. Byte 7 des bestehenden 16-Byte-Satzes trägt außerhalb Neustarts zwei
Nibbles: 1..15 bedeutet −7..+7, 8 heißt normal, 0 heißt keine Angabe. Werte über 7 werden
nur im Fahrtsatz gesättigt (7 heißt dort mindestens 7); CSV und Funk bleiben genauer.
Am ersten Neustart-Takt ist Byte 7 weiterhin ausschließlich der Neustartgrund.
Alte Protokolle haben dort 0 und liefern daher unbekannte Empfindungswörter, keine normalen.

Ein Aufspielen, Stromausfallversuch, LED- oder Funkversuch ist kein Bestandteil des Hostnachweises.

## Ergebnis der ersten künstlichen Probe (noch keine echten Aufnahmen nachgerechnet)

12.000 Zeilen und der Zustand waren exakt gleich. Der kurze Kältesprung wurde schnell erkannt.
Die zusätzliche Erwartung eines negativen langsamen **Wortes** in dieser kurzen Erholung war
nicht erfüllt: Auch M−L kann wegen der vorangegangenen Umgebung noch positiv sein. Das wird
als Grenze übernommen. Ein isolierter permanenter Wechsel mit bekannter Vorgeschichte prüft
den langsamen Sinn separat. Dabei zeigte 1/n ein weiteres Problem: Das langsame Maß
wuchs während 20 Minuten Kälte von 0,5 auf 2,745 °C, obwohl die nominelle Halbwertszeit
ein Tag war. Deshalb entfällt 1/n **vor der Auswertung echter Daten** für beide Maßbänder.
Die angegebenen Halbwertszeiten gelten nun von Anfang an.
Der Schwellentest verwendet den unmittelbar kleineren float32-Wert; ein Dezimalabstand von
0,01 ist bei großen Stufen kleiner als ein darstellbarer Schritt.
Im Fahrtsatz bleibt Byte 7 auch bei Anlauf/Fehlmessung leer (keine gesicherte Aussage).
