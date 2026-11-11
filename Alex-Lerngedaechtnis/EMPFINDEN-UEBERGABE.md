# Empfinden v1: Übergabe an Alex und Claude

Schritt 1, auf main 847de18. Verfahren vor echter Nachrechnung eingefroren in f3a50d0.
Keine Geräteprüfung durchgeführt; aufspielen und Stromausfallprobe bleiben bei Alex.

## Start und Nachweis

```sh
cd Alex-Lerngedaechtnis
python3 -m unittest discover
python3 koerper.py aufnahme --help
python3 fahrt.py an --port PORT --empfinden
cd esp32
pio run -e esp32s3-startwert
```

Für eine Rechneraufnahme den vorhandenen Aufnahmebefehl um `--empfinden` ergänzen;
1000 ms und frischer Lauf sind Pflicht. Die JSON nennt die Konstanten, `.empfinden.csv`
enthält beide Stufen, Anlauf, Gültigkeit, beide Maße und Temperaturmittel in Tausendstelgrad.
`koerper.py pruefen DATEI.csv` prüft sämtliche Zeilen exakt. Ohne neue Schalter bleiben
Ausgaben gleich. Ein Hostvergleich mit dem Ausgangssketch prüft 2000 Takte bytegleich.

336 Tests erfolgreich. Neue Hostprobe: 12.000 Takte, Einbruch, fehlende Werte und Sichern/
Laden mitten im Lauf; alle Zeilen und der portable 60-Byte-Empfindenstand stimmen exakt.
Der S3-Bau braucht 32.096 Byte RAM und 362.429 Byte Flash. Im Maschinencode der neuen
Empfinden-Funktionen und koerperTakt stehen weder madd.s noch msub.s; maschinenlesbarer
Nachweis: `beispiele/geraetelaeufe-2026-11/empfinden-maschinencode.json`.

## Taktweise Ergebnisse

Nenner: gültige Takte außerhalb Anlauf. Bereits bekannte Aufnahmen, keine unabhängige
Leistungsprüfung. „Nie auffällig“ ist die einfachste Vergleichsregel, keine brauchbare
Ereigniserkennung. Alle vollständigen Stufenfolgen und Eingabe-/Methodenprüfsummen stehen
in `beispiele/geraetelaeufe-2026-11/empfinden-v1-ergebnisse.json`.

| Aufnahme | Nenner | nie auffällig | altes Überraschungsbit | gerade ≥2 | woanders ≥2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| koerper-zufallslast-8h-2026-11-10.csv | 27000 | 0 | 0 (0.000 %) | 0 (0.000 %) | 0 (0.000 %) |
| koerper-kaelte-2026-11-10.csv | 900 | 0 | 196 (21.778 %) | 194 (21.556 %) | 322 (35.778 %) |
| koerper-last-2026-11-05.csv | 19810 | 0 | 1 (0.005 %) | 2 (0.010 %) | 0 (0.000 %) |
| fahrt-2026-11-11.bin | 35850 | 0 | 468 (1.305 %) | 482 (1.344 %) | 31076 (86.683 %) |

Die schnelle Skala endet bei 0,213 °C (8 h), 0,217 °C (5.11.) und 0,258 °C (Fahrt).
Nach dem Kühlversuch steigt sie von 0,213 auf 0,227 °C, die langsame von 0,500 auf
0,504 °C. Die alte schnelle Vierfachgrenze am Fahrtende liegt bei 1,100 °C; die neue
bei ungefähr 1,032 °C. 14 gewertete Fahrt-Takte unterscheiden sich in der schnellen
Auffälligkeit vom alten Bit. Die unveränderte Vorhersage wurde separat gegen alle
42.600 aufgezeichneten Überraschungsbits nachgerechnet: null Abweichungen.

## Wortfolgen

Stufe ≥2 zählt als Ereigniswort. Tabelle fasst auf Richtung zusammen; genaue Stufen
und Lauflängen sind im JSON. Zeitfenster der Fahrt nachträglich aus den vorhandenen
Ausschlägen zugeordnet, keine unabhängigen Ereigniszeitstempel.

| Ereignis / Fenster (Takte) | gerade | woanders |
| --- | --- | --- |
| Pusten, 146–229 | normal → kälter → normal → kälter | normal |
| Kühlpack 1, 230–484 | kälter → normal → wärmer → normal → wärmer → normal | normal |
| Kühlpack 2, 485–900 | normal → kälter → normal → wärmer → normal | normal → kälter |
| Pressluft (Zuordnung aus Reihenfolge), 12500–13000 | Anlauf/fehlend | Anlauf/fehlend |
| Fön kurz 1, 13400–14100 | normal → wärmer → normal → kälter → normal → kälter → normal → wärmer → normal | kälter |
| Fön kurz 2, 15200–15900 | normal → wärmer → normal → kälter → normal | kälter → normal → kälter |
| Bremsenreiniger + Pressluft, 18450–18780 | normal → kälter → normal | kälter |
| Fön lang 1, 18781–19400 | normal → wärmer → normal → kälter → normal → wärmer → normal → wärmer → normal → kälter → normal | kälter → normal |
| Fön lang 2, 24120–24500 | normal → wärmer → normal → kälter → normal → wärmer → normal → wärmer → normal → wärmer → normal | kälter → normal |
| Isopropanol + Pressluft, 27800–28400 | normal → kälter → normal | kälter |
| Fön lang 3, 34100–34600 | normal → wärmer → normal → kälter → normal → wärmer → normal → wärmer → normal → wärmer → normal | kälter → normal |
| Auto, Ursache unbekannt, 7100–7250 | normal → kälter → normal | kälter |

Einschalten nach Pause: Wörter während des Wiederanlaufs unterdrückt, eigenes Anlaufbit.
**Das betrifft auch die Pressluft kurz nach dem Wachhund-Neustart bei 12481.** Diese
Wahl verhindert einen falschen normalen Betriebszustand nach Boot, kostet aber echte
Beobachtungen: 6750 von 42600 Fahrt-Takten liegen im Anlauf. Keine Uhr, kein Nachweis
einer konkreten Pausendauer. Anlauf ist keine Aussage, dass nichts geschieht.

## Langsame Schicht je Startabschnitt

| Takte | gewertet | woanders ≥2 | häufigstes Wort |
| --- | ---: | ---: | --- |
| 1–300 | 0 | 0 | Anlauf |
| 301–330 | 0 | 0 | Anlauf |
| 331–4020 | 2220 | 0 | Anlauf |
| 4021–6240 | 1620 | 1620 | kälter 4 |
| 6241–7770 | 930 | 930 | kälter 4 |
| 7771–11250 | 2880 | 2880 | kälter 3 |
| 11251–12480 | 630 | 630 | kälter 3 |
| 12481–36060 | 22980 | 20426 | kälter 3 |
| 36061–38220 | 1560 | 1560 | kälter 4 |
| 38221–41550 | 2730 | 2730 | kälter 3 |
| 41551–42450 | 300 | 300 | Anlauf |
| 42451–42600 | 0 | 0 | Anlauf |

Die neue langsame Schicht bleibt wesentlich länger „woanders“ als die alte explorative
Probe. Ursache der gewählten Definition: Ein-Tages-Bezug ab der ersten Temperatur und
ein gegen Störungen geschütztes Maß. 86,68 % der gewerteten Fahrt-Takte sind auffällig.
Das ist ein anhaltender Temperatur-Kontrast, kein Ortswechselzähler. Für das Gesicht
deshalb nur ein ruhiger Hintergrundhinweis; diese Definition vor einem neuen Gerätelauf
mit Alex besprechen. Die Parameter wurden nach diesem Ergebnis nicht verändert.

## Entscheidungen und Grenzen

- Ein Maßband je Schicht; keine Ortsmodelle ohne unabhängige Ortsinformation.
- Stufe 1 sichtbar, Ereigniswort ab 2; Hysterese 2/1,5 nur an der Normalgrenze.
- Fehlende Temperatur lernt nichts und wird ausdrücklich ungültig gemeldet.
- Fahrt: Byte 7 trägt zwei Stufen bis ±7, höhere Werte gesättigt. Anlauf/Fehlmessung/
  Neustart liefern dort keine Stufen. Alte Leser bleiben 16-Byte-kompatibel; der neue
  Leser exportiert zusätzliche Spalten nur, wenn neue Stufen enthalten sind.
- Gesicherter Fahrtstand v2 enthält Vorhersage plus Empfinden; alte v1-Stände laden die
  Vorhersage weiter. Das Empfinden beginnt dann neu. Warntabelle unverändert.
- Watchdog-Ursache nicht belegt. Die Lastschleife enthält bereits vTaskDelay(1);
  aus dem Quelltext allein ergibt sich keine eindeutige Reparatur. Nicht geändert.
- Bestehende Fahrt-Speicherung schreibt Log und Stand nacheinander. Atomizität beider
  Dateien bei Stromverlust ist damit nicht bewiesen; die Erweiterung behauptet das nicht.

## Am Gerät prüfen

1. Aufnahme mit --empfinden, danach `koerper.py pruefen`: keine Differenzen.
2. Fahrt mit --empfinden starten, mindestens einen vollständigen 30-Takt-Block abwarten.
3. Strom trennen, starten, Log holen: Vorhersagestand geladen, Anlaufbit zunächst gesetzt,
   Maßband nicht durch den Einschaltvorgang gelernt. CSV und Flash-Ausgabe vergleichen.
4. Bei Upgrade alten Stand/Log vorher abholen. Keine automatische Löschung nötig.
5. Neue Hardwarebeobachtungen mit Firmware-Commit und Prüfergebnis berichten; keine
   privaten Rechnerpfade oder Gerätekennungen in die öffentliche Übergabe aufnehmen.
