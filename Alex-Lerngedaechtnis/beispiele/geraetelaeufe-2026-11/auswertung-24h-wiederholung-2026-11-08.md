# Auswertung: 24-h-Wiederholung mit repariertem Leck

Gerechnet am 8. November 2026 ab 19:06 nach `vorab-24h-wiederholung-2026-11-07.md` (SHA aea09585…), ohne Änderung.

## Aufnahme

- **Datei:** `koerper-startwert-24h-2026-11-07.csv`, vom 07.11. 19:04:28 bis 08.11. 19:04:28.
- 86.400 Takte, rc 0, keine Abbruchdatei.
- Die JSON stimmt mit der vom 6. November überein, nur `beginn` weicht ab.
- Vor dem Protokoll habe ich nur in die Speicherdatei gesehen, für R1 und KLEIN. Die Körperzeilen habe ich vorher nicht angesehen.

## Protokoll 24h-v1

- **Umgebung:** Worktree 8e8ad19, unverändert (`git status` leer), Interpreter `/usr/bin/python3` 3.9.6. Das Protokoll schreibt `python3`, aber das zeigt auf diesem Rechner auf PlatformIO.
- **Lauf:**
  - Beginn 19:06:00.
  - `-m unittest test_pruefung24h`: 17 Tests OK.
  - `pruefung24h.py`: rc 0.
  - Ende 19:06:29.
- **Bericht:** `pruefbericht-24h-v1-wiederholung-2026-11-08.md`. Die Quell-Hashes sind dieselben wie im ersten Bericht. csv_sha256 0b92ee58…, json_sha256 d88e1608….
- **`koerper.py pruefen`:** BESTANDEN, 0 Geräteabweichungen.

| Hypothese | 24 h vom 6./7.11. | Wiederholung |
| --- | --- | --- |
| H1 Speicher (H=30) | ERFÜLLT | ERFÜLLT |
| H2 Gesamt (H=60) | ERFÜLLT | **NICHT ERFÜLLT** |
| H3 Wärme, Speicher, Schleife | ERFÜLLT | ERFÜLLT |

- **H1**, je Signal, Speicher, h6/.6:
  - Präzision 83,7 %, vorher 81,2 %.
  - Warnanteil 50,1 % gegen 100 % beim Erbe.
  - Phasenquote 184 von 208 = 88,5 %, vorher 113 von 128 = 88,3 %.
- **H2**, je Signal, gesamt, h6/.6, scheitert allein am Warnanteil:
  - Warnanteil 48,7 %, erlaubt sind höchstens 45 %. Vorher waren es 42,4 %.
  - Präzision 75,6 %, vorher 71,7 %.
  - Phasenquote 2.769 von 2.829 = 97,9 %, vorher 2.130 von 2.176 = 97,9 %.
- **Nur beobachtet, ohne Hypothesenstatus:** Die Welt hatte mehr Wärmephasen, nämlich 2.438 statt 1.674. Der Ruhe-Median lag beide Male bei 37,0 °C.
  - Die Grundrate stieg von 64,6 auf 71,3 %.
  - Die feste Regel warnt in 52,4 statt 45,8 % der Takte.
  - Der Warnanteil von h6/.6 im Verhältnis zur festen Regel liegt beide Male bei 0,93.

## Reiz

- **R1 erfüllt:** 208 von 208 tiefen Durchgängen unter 16.384 B, 208 von 208 flachen darüber.
  - Grundlage ist die Speicherdatei mit 416 `BODEN`-Zeilen.
  - Der 417. Durchgang war flach und endete mit der Aufnahme.
- **KLEIN** gab es in 123 von 208 tiefen Durchgängen und in keinem flachen. Auch der kleinste Block scheiterte nie.
  - Ohne Reparatur wären diese 123 Durchgänge stehen geblieben. Am 6. November waren es 81.
- **Verlauf über den Tag:**

  | Zeit | Fall | Durchgänge |
  | --- | --- | --- |
  | 19:05–05:39 | KLEIN | 96 |
  | 06:09–08:14 | normal | 21 |
  | 08:18–11:11 | KLEIN | 27 |
  | 11:41–18:33 | normal | 64 |
- **Folge:** Die Speicherwelt ist diesmal das reine 8/8-Muster. Daher gibt es 208 Speicherphasen statt 128.

## Speicherphasen je Durchgang (je Signal, H=30)

- **Feste Regel:** 0 von 208 verpasst.
- **Startwert h6/.6:** 24 verpasst. Es sind genau die ersten tiefen Lecks nach jedem flachen Block, außer beim ersten Wechsel in Durchgang 16. Das sind 24 von 25 Wechseln und sonst keine Phase.
- **Startwert #4:** 48 verpasst. Das ist jeder Wechsel (25), dazu jeweils das zweite tiefe Leck danach (23).
- **Letzter Durchgang:** 26 verpasst, nämlich Durchgang 0 und alle 25 Wechsel.
- **Erwartung aus dem Vorab**, ohne Hypothesenstatus:
  - etwa 209 Phasen,
  - feste Regel 0,
  - der Startwert verpasst vor allem die Wechsel, etwa 26.

  Eingetroffen sind 208 Phasen, 0 bei der festen Regel und 24 beim Startwert, alle an Wechseln.
- **Mit dem 2-h-Lauf b zusammen**, als Deutung:
  - **Lauf b:** h6/.6 verpasste 3 von 10 Wechseln. Die flachen Strecken waren dort meist nur einen Durchgang lang. Die drei verpassten lagen nach der einzigen langen Strecke von 5 Durchgängen und kurz danach.
  - **Hier:** Nach jeweils 8 flachen Durchgängen, rund 28 Minuten, verpasst er 24 von 25.
  - **Schluss:** Der Lerner verlernt die Warnung, solange es ruhig ist. Je länger die Ruhe dauert, desto sicherer fehlt sie beim nächsten Leck.

## Sonst

- **Unangekündigte Phasen**, gesamt, je Signal, H=30:
  - feste Regel 0, h6/.6 155 und #4 487 von 2.829.
  - Vorher waren es 0, 144 und 391 von 2.176.
- **Eine Wärmephase ließ die feste Regel unangekündigt**, bei Takt 64.570, das war am 08.11. gegen 13:00.
  - Der Sensor sprang in einem Takt von 37,0 auf 39,0 °C, ohne die Stufe dazwischen.
  - Eine Regel, die auf die Stufe HOCH wartet, kann einen solchen Sprung nicht vorwarnen.
  - In der Gesamtwertung bleibt die feste Regel trotzdem bei 0 unangekündigten Phasen.
- **Schleife:** unverändert 560 Phasen. Kein Verfahren verpasst eine.
