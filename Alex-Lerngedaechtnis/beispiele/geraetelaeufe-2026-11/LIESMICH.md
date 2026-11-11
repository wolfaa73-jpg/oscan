# Berichte zu den Geräteläufen, 6. bis 10. November 2026

Festlegungen (`vorab-…`), Prüfberichte, Auswertungen und Tabellen, so wie sie entstanden sind. Die Rohaufnahmen
liegen seit dem 10. November in `roh/` (CSV mit Begleit-JSON, vom 5. bis 10. November), damit jede Auswertung
nachgerechnet werden kann, etwa mit `koerper.py pruefen roh/NAME.csv`. Nicht dabei sind die Sicherungen des
Einstellungsspeichers. Sätze wie „nicht committet“ beschreiben den Tag, an dem der Bericht
geschrieben wurde. Die Zusammenfassung steht in `../../STAND-2026-11-10.md`.

Eine Änderung gegenüber den lokalen Dateien: In `vorab-zufall-2h-2026-11-07.md` steht `PANEL` statt einer
Adresse im Heimnetz. Ein dort oder anderswo genannter Hash dieser Datei gilt für das lokale Original.

Zum Lauf mit zufälligen Lastdauern vom 10. November liegen hier die Festlegung
(`vorab-zufallslast-2026-11-10.md`), die Probe am künstlichen Körper und die Auswertung
(`auswertung-zufallslast-2026-11-10.md`). Die Festlegung wurde vor dem Ende des Laufs veröffentlicht.

Zum Kälteversuch von Hand am 10. November abends liegen hier die Probe am Rechner
(`probe-kaelte-2026-11-10.md`), die Festlegung (`vorab-kaelte-2026-11-10.md`) und die Auswertung
(`auswertung-kaelte-2026-11-10.md`), nachzurechnen mit
`kaelteversuch.py roh/koerper-zufallslast-8h-2026-11-10.csv roh/koerper-kaelte-2026-11-10.csv`.

Zum 11. November: `selbstvorhersage-2026-11-11.md` (Lernverfahren, Referenz, Firmware) und `fahrt-2026-11-11.md`
(der Knoten einen Tag unterwegs). Das Protokoll der Fahrt liegt als `roh/fahrt-2026-11-11.bin`, die Kontrolle
vor der Abfahrt als `roh/kontrolle-vorhersage-2026-11-11.*`.
