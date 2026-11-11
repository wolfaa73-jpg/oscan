# Schritt 3: Funk als Wärmeversuch und ein Gesicht auf dem C3

**Review-Nachtrag:** Empfinden verwendet jetzt v2. Die Korrektur für Sendefehler und das versionierte Fahrtformat sind in [FAHRT-FUNK-v2.md](FAHRT-FUNK-v2.md) beschrieben. Neue Prüfwerte folgen im Nachtrag am Ende; der ursprüngliche Prüflauf bleibt als historischer Nachweis erhalten.

Baut auf Schritt 1 (PR #10) und Schritt 2 (PR #11) auf. Hauptzweig und Alex’ Geräte
wurden nicht verändert. Bitte in dieser Reihenfolge prüfen und übernehmen. Bei noch
offenen Vorgänger-PRs zeigt dieser PR nur den zusätzlichen dritten Schritt.

## Was fertig ist

- `EmpfindenFunk.h`: zuschaltbarer ESP-NOW-Sender, keine Routerverbindung, Broadcast auf
  Kanal 6. `FUNK 0` aus, `FUNK 1` Bereitschaft, `FUNK 2` ein Paket je Körpertakt.
  Vorher `EMPFINDEN 1`; Änderungen nur außerhalb laufender Körperaufnahme.
- `FUNKPLAN 1` fährt die feste Wärmeprobe. Aufnahme mit `--funkversuch`, Auswertung
  `python3 funkversuch.py funk.csv`. Ablauf und Auswertung vorab in [FUNK-VORAB.md](FUNK-VORAB.md).
- `EmpfindenPaket.h` und `empfinden_paket.py`: 12-Byte-Format, explizit little endian,
  CRC-8, Validierung der Flags und Werte. Keine gerätespezifischen Kennungen.
- Eigenes PlatformIO-Projekt `esp32/Gesicht`: Guition ESP32-2424S012N ohne Touch.
  Gemeinsame reine Zeichenfunktion `esp32/Gemeinsam/GesichtFormen.h`, Displaytreiber separat.
- 56 Hauptbilder: vier Zustände × zwei Richtungen × Stufen 0 bis 6, einschließlich
  identischer Nullstufen. Dazu sechs Sonderansichten (Anlauf, kein Signal, fehlende Messung,
  woanders in beide Richtungen, Ausfall). Insgesamt 62 Einzelbilder und eine Übersicht.
  [Bildübersicht](beispiele/empfinden-gesicht-v1/uebersicht.png), Eingaben, Formen und
  Datei-Prüfsummen in `beispiele/empfinden-gesicht-v1/manifest.json`.
  Die vollständige Testmatrix enthält auch Kombinationen, die der Knoten heute nicht
  sendet, etwa ruhig mit Stufe 6; sie prüft die getrennten Eingänge der Zeichenfunktion.

## Geprüft und gebaut

345 Labortests erfolgreich (53,195 s) mit `python3 -m unittest discover`; der Lauf ist in
`beispiele/empfinden-gesicht-v1/PRUEFNACHWEIS.json` festgehalten.
10.000 Pakete stimmen bytegleich zwischen C++ und Python überein. Der C++-Decoder
weist für jedes Paket alle 96 einzelnen Bitänderungen zurück: 960.000 Defekte.
Zusätzlich: falsche Länge, ungültige Flags mit neu berechneter CRC in Python,
Paketduplikate auch nach Ablauf der Frist, alte Takte, Neustart und 32-Bit-Zeitumlauf.
156 Kombinationen prüfen die reine Gesichtszeichnung; die PNGs stammen aus genau diesem
C++-Code. Nur Schrift-Rasterung und Rundmaske kommen aus Pillow, deshalb kein Nachweis
einer pixelgleichen LCD-Darstellung. Die Übersicht wurde visuell kontrolliert.

| Projekt | Umgebung | statisches RAM | Flash |
| --- | --- | ---: | ---: |
| Knoten mit Funk | esp32s3-startwert | 56.668 Byte | 776.693 Byte |
| Gesicht | guition-c3 | 39.180 Byte | 794.488 Byte |

Beide Builds erfolgreich, espressif32@6.12.0, Arduino-ESP32 2.0.17;
LovyanGFX 1.2.29 wird über lib_deps geladen. Kein manuell befülltes lib/ nötig.
RAM-Werte sind Linkerwerte, kein Laufzeit-Höchstverbrauch von WiFi und Displaybibliothek.
Das eigene Gesicht verwendet keinen Vollbildpuffer: nur maximal 20 Zeichenbefehle und
einen einzelnen Paket-Queueeintrag. Nach der letzten Eingabevalidierung bleiben die
S3-Funktionen numerisch unverändert; das Übersetzerflag -ffp-contract=off bleibt gesetzt.

## Aufbauen bei Alex

```sh
cd Alex-Lerngedaechtnis
python3 -m pip install numpy Pillow pyserial
python3 -m unittest discover
pio run -d esp32 -e esp32s3-startwert
pio run -d esp32/Gesicht -e guition-c3
```

Das Aufspielen übernimmt Alex. Für unterwegs danach:

```sh
python3 fahrt.py an --port PORT --empfinden --funk
```

Das merkt beide Zusatzfunktionen für den Fahrtmodus und startet den Knoten neu.
`fahrt.py aus` stoppt ihn wie bisher; `STOP` beendet auch den Funk. Zum nächsten
Fahrtstart ohne Funk: zuerst `STOP`, dann `FUNK 0` und danach `FAHRT 1`; ohne Empfinden zusätzlich
`EMPFINDEN 0`. Der alte 16-Byte-Bestand bleibt erhalten. Neue Fahrtzeilen verwenden das gekennzeichnete 20-Byte-Format mit eigenem Reizfeld; Funkreize einschließlich Bit 32 werden jetzt auch im Fahrtprotokoll gespeichert. Siehe `FAHRT-FUNK-v2.md`; zum Abholen die aktualisierte `fahrt.py` verwenden.

Displaykonfiguration entsprechend Auftrag: SPI2, SCLK 6, MOSI 7, DC 2, CS 10,
MISO −1, Reset **−1**, Hintergrundlicht 3 aktiv hoch, `invert=true`, `rgb_order=false`.
40 MHz Schreibfrequenz statt der angegebenen maximalen 80 MHz: konservativ gesetzt,
am Gerät noch nicht verglichen. Helligkeit 48/255, PWM 5 kHz und 40-ms-Knopfentprellung
sind gesetzt. GPIO 9 schaltet die zweite Ansicht mit Temperatur, beiden Stufen und Takt.
USB-CDC eingeschaltet, 4 MB Flash, kein PSRAM vorausgesetzt.

## Paketvertrag v1

| Byte | Bedeutung |
| ---: | --- |
| 0 | 0x4F |
| 1 | Version 1 |
| 2–5 | Körpertakt uint32, little endian |
| 6–7 | Temperatur int16 in Zehntelgrad, −32768 heißt fehlend |
| 8 | gerade, int8 in Zweierkomplement |
| 9 | woanders, int8 in Zweierkomplement |
| 10 | Bits 0 Anlauf, 1 überrascht, 2 SCHWACH, 3 AUSFALL, 4 Log voll, 5 Suchen, 6 erklärt |
| 11 | CRC-8/ATM: Polynom 0x07, Start 0, keine Reflexion/XOR, über Byte 0..10 |

Bit 7 bleibt reserviert. SCHWACH und AUSFALL gleichzeitig sowie Suchen/erklärt oder
Suchen/erklärt zusammen mit überrascht werden abgewiesen. Stufenbereich ±30 entspricht
der Rechenreferenz; Temperaturbereich −100..200 °C ist eine gesetzte Plausibilitätsgrenze.
Die Augen sättigen aus Platzgründen ab Stufe 6, die Zahlenansicht zeigt den vollständigen Wert.
Überrascht im Paket heißt |gerade|≥2; das alte Vorhersage-Bit bleibt in seiner bisherigen
Zeile unverändert. Suchen und erklärt existieren nur als Paketplätze und Bildproben;
der Knoten setzt beide Bits nirgends.

Nach fünf Sekunden ohne neueren gültigen Takt zeigt das Display KEIN SIGNAL. Beschädigte
Pakete und Duplikate halten es nicht frisch. Nach einer Empfangspause darf auch ein
kleinerer Takt eines neu gestarteten Knotens beginnen. Mehrere Sender sind nicht vorgesehen;
ein Broadcast hat hier keine Authentisierung. CRC erkennt Beschädigung, keinen Absender.
Die WiFi-Rückruffunktion kopiert nur ein geprüftes Paket in eine Queue; LCD und Knopf
laufen in loop. Das folgt den [ESP-NOW-Hinweisen von Espressif](https://docs.espressif.com/projects/esp-idf/en/v4.4.8/esp32/api-reference/network/esp_now.html).
Der Treiber nutzt [LovyanGFX](https://github.com/lovyan03/LovyanGFX), fest auf 1.2.29 gesetzt.

## Was die künstliche Wärmeprobe sagt

Vier deterministische Fälle (Nullwirkung, bekannte 2/0,5 °C Zusatzwärme, beide mit und
 ohne linearer Drift) treffen die bekannten Kontraste innerhalb 0,02 °C. Eine vollständige
künstliche CSV mitsamt JSON und beiden Nebendateien besteht denselben Prüfer wie später
Alex’ Aufnahme. Defekte und fremde Reize werden vor Ausgabe von Kontrasten abgewiesen.

Mit der in kunstkoerper.GEMESSEN hinterlegten Umgebungsstreuung, acht Saaten je Fall:

| bekannte Wirkung | Bereitschaft minus Aus, Spannweite | Senden minus Bereitschaft, Spannweite |
| --- | ---: | ---: |
| keine Zusatzwärme | −0,491 bis +0,308 °C | −0,300 bis +0,359 °C |
| 2 °C Bereitschaft, weitere 0,5 °C Senden | 1,509 bis 2,308 °C | 0,200 bis 0,859 °C |

Kein Konfidenzintervall, sondern acht künstliche Läufe je Zeile. In keinem dieser Läufe
meldet die schnelle Schicht binnen 60 Takten ab Einschalten Stufe ≥2, auch nicht bei
2 °C Zusatzwärme: Eine langsame Erwärmung kann von der Vorhersage mitverfolgt werden.
Das Werkzeug kann eine Verschiebung messen, es garantiert kein Überraschungswort.
Alle Werte: `beispiele/empfinden-gesicht-v1/funk-kunstprobe.json`. Noch keine echten
Funkmesswerte. Das Sendebit wurde ausdrücklich **nicht** Eingang der Vorhersage.

## Antwort auf die Frage zur Verständlichkeit des Gesichts

Vorschlag für einen günstigen getrennten Versuch, noch nicht durchgeführt:

1. Zehn Menschen ohne Projektkenntnis. Vorab dieselbe kurze Erklärung für Zahlen und
   Gesicht: gerade = Abweichung von der eigenen Vorhersage, woanders = langsamer
   Temperaturkontrast. Kein Wort über Gefühle, Absichten oder Bewusstsein.
2. 24 vorab erzeugte Pakete mit normalen, warmen/kalten, schwachen/starken, fehlenden und
   widersprüchlich wirkenden Kombinationen (z.B. gerade wärmer, woanders kälter).
   Hälfte beginnt mit Zahlen, Hälfte mit Bildern; Reihenfolge fest ausgelost.
3. Abfragen: Richtung gerade, relative Stärke, Richtung woanders, Anlauf/Signalverlust.
   Zusätzlich „Kannst du daraus Freude/Angst oder die absolute Temperatur ablesen?“;
   richtige Gesichtsantwort: nein. Bilder auch einmal in Graustufen zeigen.
4. Vorab gesetzte Entwurfsziele: mindestens 90 % richtige Richtungen, 80 % richtige
   Stärkevergleiche und mindestens 90 % korrekte Antworten auf „nicht ableitbar“.
   Rohzahlen pro Person und Verwechslungsmatrix veröffentlichen, keine repräsentative
   Bevölkerungsbehauptung aus zehn Personen. Bei Verfehlung die Darstellung ändern,
   dann mit anderen Personen prüfen. Kein Nachstimmen der Rechenmodelle für das Gesicht.

Die vier Zustände werden statisch gezeichnet. Kein spontanes Blinzeln, kein Suchen ohne
entsprechendes Bit, keine erfundene Emotion zwischen Paketen. Kälter/wärmer unterscheiden
sich zusätzlich zur Farbe durch ein abwärts/aufwärts gerichtetes Dreieck.

## Noch niemand hat hier am Gerät geprüft

- Tatsächlicher ESP-NOW-Empfang, Reichweite, Störungen, Senden ohne Empfänger und Wärmeeffekt.
- Farben, Bildlage, Hintergrundlicht, USB-Verhalten und Boot-Knopf am konkreten C3-Board.
- Sichtbarkeit der langsamen LED-Impulse und ihre Eigenwärme.
- Laufzeit-RAM, echte Stromunterbrechung und Kombination aus Funk, Fahrtlog und Speichern.
- Verständlichkeit des Gesichts für Außenstehende.

Alex’ Abnahme: beide Projekte bauen/aufspielen, Paketempfang im Sekundentakt ansehen,
Knoten ausschalten (nach fünf Sekunden KEIN SIGNAL), neu starten (Anlauf), Knopf testen;
danach separat die dreistündige Funk-Wärmeprobe durchführen. Die offene Watchdog-Ursache
und die bisherige nicht atomare Kombination aus Logdatei und Fahrtstand bleiben dokumentierte
Grenzen aus Schritt 1; hier wurden sie nicht umgebaut.

## Abschließende Review-Prüfung mit v2

357 Tests bestanden (62,553 s), einschließlich 42.600 echter Fahrttakte C++/Python, 12.000 künstlicher Takte, alter CSV-Version, LED-Tabelle und der fünf neuen Fehler-/Formatprüfungen. Der alte Abbruchausdruck wird im Mutationstest erkannt. S3-Bau: 56.788 B RAM, 777.205 B Flash; C3: unverändert 39.180 B RAM, 794.488 B Flash. Im S3-Abbild keine `madd.s`/`msub.s`.

Aktuelle Quellenprüfsummen und Ergebnisse: `beispiele/empfinden-review-v2/pruefung.json`. Der frühere Nachweis mit 345 Tests bleibt als historischer v1-Stand erhalten. Kern, Vokabular, Knoten.h, Vorhersage.h und selbstvorhersage.py sind gegenüber der Basis unverändert. Die Display-Bildproben bleiben ebenfalls unverändert.

Die v2-Änderungen an der Wahrnehmung stehen in `EMPFINDEN-v2-ERGEBNISSE.md`. Für die Fahrt den aktualisierten Leser verwenden: Er erhält den alten Bestand und wertet das neue Reizfeld aus. Hardwareprüfungen werden durch diese Rechen- und Buildprüfungen nicht ersetzt.
