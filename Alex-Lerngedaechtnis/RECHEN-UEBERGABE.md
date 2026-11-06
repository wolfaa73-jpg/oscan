# Rechenaufgaben für Daniel

Stand 6. November 2026, nach dem Startwert (0f8f9fc, 68e4bcb) und der Übernahme von #1 bis #3. Daniel hat gefragt, wie er helfen kann. Hier sind Aufgaben, die viel Rechenzeit, aber keinen S3 brauchen, außer der letzten. Jede steht für sich. Welche er nimmt, entscheiden Alex und Daniel.

Hintergrund steht in UEBERGABE.md unter „Wechselnde Bedeutung, sechs Stunden“ und „Entschieden am 6. November“. Kurz gesagt: Ein festes Erbe überstimmt eigene Erfahrung, deshalb lernt kein Gedächtnis eine Ausnahme. Als verblassender Startwert lernt das Gedächtnis je Signal die Ausnahme beim Speicher (79 statt 52 % Treffer). Dafür verliert es die meisten Hitzewarnungen, weil auf warm nur zu 38 % heiß folgt. Alles das ist an derselben Aufnahme nachgerechnet, die das Problem gezeigt hat. Eine unabhängige Bestätigung fehlt.

## Regeln für alle Aufgaben

- **Nichts an der 6-Stunden-Aufnahme einstellen.** Schwellen, Halbwertszeiten und Muster werden auf künstlichen Spuren gewählt. Die echten Aufnahmen dienen erst danach als Prüfung.
- **Jede Vergleichstabelle hat eine Zeile „Immer warnen“** und zählt je Takt: Warnanteil, Trefferquote, Grundrate. Nach Phasen gezählt sieht „immer warnen“ fast perfekt aus. Das war am 5. November schon einmal ein Zählartefakt. `vokabular.bewerte` und `bewerte_je_signal` zählen so.
- **Vorher festlegen, was gemessen wird**, und im Bericht sagen, was erst danach dazukam.
- **Die Regel `erbe` bleibt unverändert.** Neues kommt als eigene Regel oder als Parameter dazu, wie `startwert`.
- **Tests im Laborordner starten:** `python3 -B -m unittest`. Von außerhalb findet ein Kindprozess in `test_auftragsjournal.py` sein Modul nicht.
- **Commits nur mit der noreply-Adresse** (`281549317+Daniel-GER@users.noreply.github.com`), das Repo ist öffentlich.

## 1. Schwelle je Signal aus Kosten

Heute warnt jedes Gedächtnis ab 60 % Ausfallwahrscheinlichkeit, gleich welches Signal. Bei der Wärme entscheidet allein diese Schwelle, ob überhaupt gewarnt wird.

- Für jedes Signal Schwellen von 0,05 bis 0,95 und Kostenverhältnisse „verpasster Ausfall zu Fehlalarm“ von 1 bis 100 durchrechnen. Grundlage sind `warnungen(..., schwelle=…)` und `warnungen_je_signal`, je mit festem Erbe und mit `startwert=True`.
- Ergebnis je Signal: Ab welchem Kostenverhältnis lohnt sich welche Schwelle, und wie viele Phasen bleiben dann ohne Vorwarnung.
- Auf künstlichen Spuren wählen (Aufgabe 2), an den Aufnahmen nur prüfen.

## 2. Viele künstliche Spuren mit wechselnder Bedeutung

Bisher gibt es ein einziges Muster, acht Leckdurchgänge tief, acht flach. Gebraucht wird ein Erzeuger für Stufen je Signal, ähnlich `labor.generiere`, aber für Wärme, Speicher und Schleife getrennt:

- Blocklängen, Zufallsmasken und seltene Ausnahmen, etwa einer von zwanzig Durchgängen anders.
- Wärme mit einstellbarer Folgewahrscheinlichkeit warm → heiß, sie liegt am Gerät bei 38 % binnen 30 s.
- Überlagerungen wie im echten Lauf, damit ein Signal das Vorzeichen eines anderen verdeckt.

Darauf laufen gegeneinander: feste Regel, festes Erbe, Startwert, ohne Erbe, „wie der letzte Durchgang“ und „immer warnen“, grob wie im Gerät und je Signal. Tausende Startwerte je Familie, Ergebnisse als CSV. Mit einem getrennten Entwicklungs- und Kontrollsatz wie in `labor.py`.

## 3. Halbwertszeit des Startwerts

Der Startwert verblasst je eigenem Ausgang um den Faktor der Kontextregel, also mit einer Halbwertszeit von sechs Ausgängen. Die Sechs ist übernommen, nicht gewählt. Am 6-Stunden-Lauf wichen drei Ausgänge schneller, dafür blieb ein Ausfall mehr unangekündigt.

- Raster 1 bis 24 Ausgänge auf den Spuren aus Aufgabe 2. Dafür einen Parameter neben `startwert=True` einführen, ohne `kern.Startwertgedaechtnis` zu ändern, solange nichts entschieden ist.
- Frage: Gibt es einen Bereich, der über viele Muster trägt, oder hängt die gute Wahl am Muster?

## 4. Zweiter Weg: Verweildauer und Richtung getrennt

Heute altert eigene Erfahrung mit jedem Takt im selben Zustand. Ein Ausgang aus KNAPP kommt deshalb nie über 1,3 Beobachtungen, und der Blick überschätzt den Rückweg OK → KNAPP. Der zweite Weg lernt getrennt, wie lange ein Zustand bleibt und wohin er danach geht.

- Als Prototyp in Python, neben `Wortgedaechtnis`, mit derselben Schnittstelle (`beobachte`, `beleg`, `kritisch_binnen`). So passt er in `warnungen` und `verfahren`.
- Gemessen mit der Maschine aus Aufgabe 2, dazu an den echten Aufnahmen.
- Erst wenn das trägt, lohnt sich ein Gedanke an `Knoten.h`.

## 5. Sicherheitsabstände der bisherigen Ergebnisse

Wie fest sind die Zahlen? Bootstrap über ganze Einheiten, nicht über Takte: Leckdurchgänge, Hitzephasen, Bremsrampen. Mindestens:

- Speicher je Signal mit Startwert gegen festes Erbe: 79 gegen 52 % Treffer.
- Gerät 30 Minuten: 59 gegen 73 % Warnanteil bei 77 gegen 79 % Treffern.
- Feste Regel gegen Je Signal mit Startwert über sechs Stunden.

## 6. Gleichheit von Firmware und Python unter Last

Der Hostprüfstand (`esp32/host.cpp`, `SketchTests` in `test_labor.py`) vergleicht heute die Demo, 120 Kontrollspuren und wenige Neustarts.

- Millionen zufälliger Spuren für alle vier Regeln, Blick 1 bis 600, mit Lücken, Fehlzeilen und `SICHERN`/`LADEN` an zufälligen Stellen. Jede Antwort muss mit `kern.Knoten` übereinstimmen.
- Mutationstests über `kern.py`, `vokabular.py` und `Knoten.h`: Welche absichtlichen Fehler bemerkt die Testreihe nicht? Daraus werden neue Tests.

## 7. Wiederholung auf einem zweiten Gerät (nur mit ESP32-S3)

Falls Daniel einen ESP32-S3 hat: Den 6-Stunden-Lauf auf seinem Chip wiederholen, einmal mit `esp32s3-erbe`, einmal mit `esp32s3-startwert`, gleiche Reize:

```bash
python3 koerper.py aufnahme messungen/koerper-muster-6h-<datum>.csv --port /dev/PORT --regel startwert --takte 21600 --last 120 120 --leck 4096 12288 5 120 32768 4278255360 --bremse 10 10 300 5 120 --blick 60 --grenzen 380 390 65536 16384 20000 200000
python3 koerper.py pruefen messungen/koerper-muster-6h-<datum>.csv
```

Seine Grenzen für die Temperatur müssen zu seinem Chip passen. Die Werte oben passen zu Alex’ UICPAL bei etwa 37 °C. Laufen beide Varianten gleichzeitig auf zwei Geräten, sehen sie dieselbe Umgebung.

## Was bei Alex parallel weiterläuft

- **Weiterlernen über Läufe.** Bisher beginnt jede Körperaufnahme mit `NEUER_LAUF`, das Gerät vergisst also alles zwischen zwei Läufen. Als Nächstes lädt eine Aufnahme auf Wunsch den gesicherten Stand und sichert regelmäßig. Dann behält das Gerät Erfahrung und verblasstes Erbe über Pausen und Stromtrennungen. Die Nachrechnung in Python startet dafür vom selben Stand. Wie, steht nach dem Einbau in UEBERGABE.md.
- **Danach ein langer Lauf mit Startwert** und denselben Reizen wie der 6-Stunden-Lauf. An dieser Aufnahme ist nichts eingestellt. Sie ist die unabhängige Prüfung für die Aufgaben 1 bis 5, also bitte erst prüfen, wenn Schwellen, Halbwertszeiten und Muster auf künstlichen Spuren gewählt sind.

## Daten

Die Messaufnahmen liegen nur bei Alex in `messungen/` und sind nicht im Repo. Durchsucht am 6. November: keine MAC, keine Seriennummer, kein Portname. Die JSON-Dateien enthalten nur Regel, Grenzen, Reize und Startzeit. Alex gibt sie auf Anfrage weiter. Für die Aufgaben 1 bis 4 und 6 genügen künstliche Spuren.
