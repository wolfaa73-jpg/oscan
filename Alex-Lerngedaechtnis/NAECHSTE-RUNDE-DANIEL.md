# Nächste Runde für Daniel

6. November 2026, abends. Nach den Kostenrechnungen (#4) und dem Ideenpapier (#5). Daniel hat noch Codex-Kontingent. Hier sind vier Aufträge, nach Dringlichkeit sortiert. Jeder Auftrag kommt auf einen eigenen Zweig und in einen eigenen Pull Request, damit Alex sie einzeln übernehmen kann.

Es gelten die Regeln aus [RECHEN-UEBERGABE.md](RECHEN-UEBERGABE.md):

- Jede Tabelle hat eine Zeile „Immer warnen“ und zählt je Takt.
- Was gemessen wird, steht vorher fest.
- Die Regel `erbe` bleibt unverändert.
- Tests startest du im Laborordner.
- Commits nur mit der noreply-Adresse.

Neu kommt dazu: **`kern.py`, `vokabular.py`, `Knoten.h` und die Firmware nicht ändern.** Wenn du dort einen Fehler findest, beschreib ihn mit einem Test, der fehlschlägt, und repariere ihn nicht. Den Fehler behebt Alex mit Claude, weil auf dem S3 gerade ein Lauf mit genau diesem Stand läuft.

## 1. Eilig: Prüfprotokoll für die 24-Stunden-Aufnahme

Die Aufnahme `koerper-startwert-24h-2026-11-06.csv` endet am **7. November gegen 10:40**. Bis dahin hat niemand hineingesehen, auch Claude nicht. Wenn das Protokoll vorher im Repo liegt, ist die Prüfung echt unabhängig. Ein Commit nach 10:40 ist nur noch eine Auswertung.

Liefere `PRUEFPROTOKOLL-24H.md` und ein Skript `pruefung24h.py`, das nur einen CSV-Pfad bekommt und die festgelegten Tabellen ausgibt. Claude führt das Skript bei Alex aus und berichtet die Zahlen unverändert.

- **Vorbedingung:** `koerper.py pruefen` muss bestehen. Sonst bricht das Skript ab und wertet nichts aus.
- **Verfahren:** Alle Einstellungen stehen im Protokoll und dürfen danach nicht mehr geändert werden.
  - Feste Regel.
  - Festes Erbe.
  - Startwert wie auf dem Gerät: h=6 und Schwelle 0,6.
  - Startwert mit der in #4 eingefrorenen Kombination: h=1/15/17 und Schwelle 0,95.
  - Letzter Durchgang.
  - Immer warnen.
  - Nie warnen.
  - Jedes Verfahren grob wie im Gerät und je Signal.
- **Maße je Takt:**
  - Warnanteil, Trefferquote und Grundrate.
  - Unangekündigte Phasen.
  - Beide Kostenbegriffe aus #4 mit dem Verhältnis 10, also eine verpasste Phase kostet 10 und ein verpasster Zieltakt kostet 10.
- **Gleichheit mit dem Gerät:** Die Warnungen, die das Gerät geschrieben hat, sollen mit der Python-Nachrechnung desselben Startwerts übereinstimmen, Takt für Takt. Abweichungen zählst du und zeigst sie, du glättest sie nicht.
- **Hypothesen vorab, als Sätze mit Zahlengrenze.** Beispiel: „Je Signal mit Startwert erreicht beim Speicher mindestens 65 % Treffer bei höchstens 40 % Warnanteil.“ Die Grenzen leitest du aus den 6 Stunden und aus #4 ab, nicht aus Wunsch.
- **Testen ohne die echten Daten:**
  - Das CSV-Format kennst du aus `koerper.py` und `test_labor.geraetezeilen`.
  - Prüfe das Skript an künstlichen Gerätezeilen.
  - Dazu kommt ein absichtlich verdorbener Lauf mit fehlenden Takten, einer Lücke beim Sichern und einer falschen Warnung. Daran muss die Vorbedingung oder der Gleichheitsvergleich anschlagen.
- **Besonderheit:** Das Gerät sicherte jeden 600. Takt still in den Flash. Die Aufnahme beginnt ohne `--fortsetzen`, deshalb gibt es keinen übersprungenen Takt nach `LADEN`, siehe UEBERGABE.md unter „Weiterlernen über Läufe“. Ob das Schreiben die Schleifenlücke an diesen Takten anhebt, ist nicht gemessen. Das Skript soll deshalb die Takte, deren Nummer ein Vielfaches von 600 ist, getrennt ausweisen: Lücke, Stufe und daraus entstandene Warnungen. Sie werden aber nicht aus der Wertung genommen.

## 2. Plan A, B und C aus deinem Ideenpapier durchführen

Die Pläne stehen in [IDEEN-DANIEL.md](IDEEN-DANIEL.md) (#5). Fang in deiner eigenen Reihenfolge an: zuerst A, dann B, dann C.

- Neue Dateien, etwa `ideenlabor.py` und `test_ideenlabor.py`, ohne Abhängigkeit vom laufenden Kern, außer zum Lesen.
- **Zuerst der Prüfer mit den absichtlichen Defekten aus deinem Plan.** Belegt wird das durch einen Test je Defekt, der rot wird, wenn der Prüfer ihn übersieht.
- Danach die Kandidaten auf dem Entwicklungssatz.
- **Einfrieren:** Verfahren und Einstellungen committen, bevor du den Prüfsatz erzeugst. Der Commit-Hash steht im Bericht.
- Bericht als `IDEEN-ERGEBNISSE.md`, auch wenn alles negativ ausgeht. Ein sauberes Nein ist hier ein Ergebnis.

## 3. Firmware und Python unter Last (Aufgabe 6 der Rechenübergabe)

Das ist der Auftrag, der am meisten Rechenzeit schluckt, ohne dass Ideen nötig sind.

- **Zufallsspuren gegen `esp32/host.cpp`:** alle vier Regeln, Blick 1 bis 600, dazu Lücken, Fehlzeilen und `SICHERN`/`LADEN` an zufälligen Stellen.
  - Neu seit dem 6. November und deshalb besonders wichtig:
    - `SICHERN_ALLE`, der um eins erhöhte Takt nach `LADEN`.
    - `NEUER_LAUF` mitten im Lauf.
    - Ein AG01-Stand, der in eine Startwert-Firmware geladen wird.
  - Jede Antwort muss mit `kern.Knoten` übereinstimmen.
- **Mutationstests** über `kern.py`, `vokabular.py`, `neustart.py` und `Knoten.h`: Welche absichtlichen Fehler bemerkt `test_labor.py` nicht? Lieferst du als Liste mit je einem neuen Test, der den Fehler fängt.
- Gefundene echte Abweichungen beschreibst du nur, siehe oben. Du reparierst sie nicht.

## 4. Sicherheitsabstände und zweiter Weg (Aufgaben 5 und 4)

Das ist für den Fall, dass danach noch Kontingent übrig ist.

- **Aufgabe 5, Bootstrap über ganze Einheiten:** Leckdurchgänge, Hitzephasen und Bremsrampen, für die in RECHEN-UEBERGABE genannten Zahlen. Die 6-Stunden-Aufnahme bekommst du von Alex auf Anfrage. Die 24-Stunden-Aufnahme gehört nicht dazu.
- **Aufgabe 4, Verweildauer und Richtung getrennt:** als Python-Prototyp mit der Schnittstelle von `Wortgedaechtnis`, gemessen auf den künstlichen Spuren aus #4.

## Was bei Alex läuft

Der S3 nimmt bis 7. November gegen 10:40 mit `esp32s3-startwert` auf und sichert jeden 600. Takt. Danach führt Claude zuerst das Prüfprotokoll aus, falls es dann im Repo liegt, und erst danach jede weitere Auswertung.
