# OSCan: Verbund und Arbeitsvergabe anschließen

Stand 5. November 2026. Diese Etappe baut auf Alex’ Hauptstand `c4ec40bec14516a1666566f619eb82c1ef35d930` auf. Darin ist unser erster Systemversuch `07793f1662fb36a9a0c09b5449773155594d7c4b` bereits übernommen und nachgeprüft. Der Anschluss wird separat unter `codex/verbund-disposition` zur Übernahme vorgeschlagen.

## Ergebnis

Der bisher getrennte Verbundversuch und der Disponent sind verbunden. Zwei sendende Knoten lernen lokal und liefern OC-Statuspakete. Die Zentrale prüft deren Sitzung, Runde und Alter. Der feste Disponent verwendet die bestätigten Zustände und die Vorwarnung des Primärknotens. Das Auftragsregister verhindert eine zweite Ausführung derselben freigegebenen Arbeit innerhalb seiner Lebensdauer. Echte lokale Arbeiter führen die freigegebenen Testaufträge aus.

```text
Lernknoten → OC-Statuspaket → Empfangsprüfung → feste Disposition
                                                ↓
                                   Auftrag mit Sitzung und Takt
                                                ↓
                                     begrenztes Auftragsregister
                                                ↓
                                      lokaler Arbeiter → Quittung
```

Der Kanal zwischen Lernknoten und Zentrale ist in diesem gemeinsamen Versuch deterministisch im Speicher simuliert. Die OC-Pakete werden vollständig kodiert und geprüft. Die zwei Arbeiter sind echte lokale Prozesse mit Pipe-Verbindungen. Das ist noch kein physischer ESP32-Pi-Verbund und noch kein Netzprotokoll für Arbeitsaufträge.

## Start und Dateien

Im Laborordner:

```bash
python3 -B -m unittest -v
python3 -B verbundsystem.py
python3 -B verbundsystem.py --json beispiele/verbund-system.json
```

| Datei | Aufgabe |
|---|---|
| `systemkern.py` | Gemeinsame feste Disposition; lokale Lernregel und externer Status nutzen denselben Ablauf |
| `auftraege.py` | Unveränderliche Aufträge, Quittungen und begrenztes Register |
| `verbundsystem.py` | Rundengenaue Verbindung zwischen `Zentrale`, Disponent und Register; gemeinsamer Versuch |
| `test_verbundsystem.py` | 24 neue Prüfungen für Anschluss und Auftragslebensdauer |
| `beispiele/verbund-system.json` | Reproduzierbarer Ablauf mit Verlust, Neustart, Duplikaten und ablaufender Freigabe |

Die vorhandene API `Systemkern.schritt()` und die erste Prozessprobe bleiben nutzbar. `Arbeitsprozesse.ausfuehren()` akzeptiert zusätzlich eine Auftragssitzung, die bis zum Arbeiter mitgeführt und bei dessen Antwort geprüft wird. Die Lernregeln und das OC-Paketformat werden nicht geändert.

## Feste Regeln für die Verbindung

1. Knoten 1 ist Primär, Knoten 2 Reserve. Die Zuordnung ist eine explizite Versuchskonfiguration.
2. Nur die beiden sendenden `Messknoten` besitzen lernende Kerne. Die Zentrale verarbeitet Vorwarnungen als Daten. Wiederholte Statuspakete und wiederholte Planabrufe erzeugen keine neue Erfahrung.
3. Jeder Dispositionszyklus stellt beiden Knoten genau eine neue Frage. Zur Arbeitsvergabe genügt keine noch sichtbare Meldung aus der vorigen Runde. Eine neue Antwort aus der aktuellen Runde ist erforderlich.
4. Der Disponent plant einen logischen Takt voraus. Eine früher reservierte Reserve darf nur bei unmittelbar folgendem Dispositionstakt und unmittelbar folgenden lokalen Messtakten beider Knoten verwendet werden. Die lokalen Zähler dürfen unterschiedliche Startwerte haben. Beide Sitzungen müssen unverändert sein.
5. Die Reserve muss in der aktuellen Runde selbst `OK` oder `SCHWACH` melden. Bei unbekanntem oder ausgefallenem Reserveknoten wird sie weder eingesetzt noch für den nächsten Takt reserviert.
6. Ein neuer Sitzungseintrag beendet einen schon begonnenen Zyklus und verwirft seine Vorsorge. Der Lernstand des sendenden Knotens darf dabei erhalten bleiben.
7. Vor der ersten Arbeitsausführung werden die benötigten Meldungen erneut geprüft. Ein inzwischen abgelaufener Plan wird `VERFALLEN`. Eine bereits abgeschlossene Arbeit liefert bei Wiederholung nur ihre gespeicherte Quittung.

Die Quelle muss wie im bestehenden `Messknoten` eine neue Beobachtung bei einer neuen Frage liefern. Für unabhängig erfasste und später übertragene Messwerte fehlt weiterhin ein eigener Vertrag über deren Erfassungsalter. Eine Meldung ist zudem nur bis zur Freigabe geprüft; ein danach tatsächlich ausfallender Arbeiter ist ein Ausführungsfehler, keine rückwirkend sichere Freigabe.

## Auftragslebensdauer

Die Identität eines Auftrags besteht aus einer frischen 128-Bit-Sitzung der Laufzeit und dem Dispositionstakt. Der vollständige Plan ist unveränderlich. Die Quittung trägt dieselbe Sitzung und denselben Takt. Ein anderer Plan unter derselben Kennung ist ein Konflikt. Ein Auftrag einer fremden Sitzung wird abgewiesen.

| Status | Bedeutung |
|---|---|
| `IN_ARBEIT` | Vor dem Arbeiteraufruf eingetragen; erneuter Eintritt führt nicht nochmals aus |
| `ERLEDIGT` | Auftragskennung und SHA-256 des festen Testauftrags stimmen |
| `AUSGESETZT` | Der feste Disponent hat keinen Arbeiter freigegeben |
| `VERFALLEN` | Die Freigabe ist vor dem Arbeitsbeginn abgelaufen |
| `UNGEKLAERT` | Wirkung oder Rückmeldung ist unklar; keine automatische Wiederholung |

Eine verlorene Antwort ist kein Beweis dafür, dass der Auftrag nicht ausgeführt wurde. Deshalb führt ein Timeout, ein falsches Arbeitsergebnis oder eine Ausnahme nach Arbeitsbeginn zu `UNGEKLAERT`. Auch eine Unterbrechung per Strg-C hinterlässt diesen Zustand, bevor sie weitergereicht wird. Ein spätes Ergebnis aus einer anderen Auftragssitzung wird nicht als aktueller Erfolg akzeptiert.

Das Register hält höchstens 1.024 Einträge, konfigurierbar beim Aufbau. Es entfernt keine alten Kennungen automatisch: Sonst könnte ein sehr später Wiederholungsversuch erneut wirken. Bei vollem Register wird neue Arbeit vor ihrem Beginn abgewiesen; vorhandene Quittungen bleiben abrufbar.

**Grenze:** Das Register ist flüchtig und gehört in einen einzigen seriellen Ereignisablauf. Es sichert höchstens eine Ausführung pro Kennung während dieser Registerlebensdauer. Es liefert keine dauerhafte Exactly-once-Garantie über Prozessabstürze. Ein Neustart braucht eine neue Sitzung. Frühere Wirkungen sind danach gegebenenfalls ungeklärt. Eine alte Arbeit unter einer neuen Kennung erneut anzulegen wäre eine neue Ausführung und wird nicht durch dieses Register verhindert. Die Demonstration verwendet feste UUIDs ausschließlich für reproduzierbare Ergebnisse; normale Instanzen erzeugen frische UUIDs.

## Nachweise

Die vollständige Suite umfasst 101 erfolgreiche Tests: die bisherigen 77 und 24 neue. Dazu gehören der Ablauf mit echten Arbeitern, Duplikate während und nach einer Ausführung, Ergebnisverlust, Strg-C, Registergrenze, widersprüchliche Aufträge, alte Sitzungen, Mess- und Dispositionslücken sowie eine vor Arbeitsbeginn ablaufende Freigabe.

Der gemeinsame Acht-Takt-Versuch führt fünf Arbeiten aus, setzt zwei aus und lässt eine geplante Reservenutzung vor Beginn verfallen. Jede Quittung wird nochmals angefordert und bleibt identisch. Die Reserve arbeitet in Takt 2; in Takt 4 fehlt ihre neue Meldung; in Takt 6 verhindert die neue Knotensitzung die alte Vorsorge; in Takt 8 greift die erneute Altersprüfung. Alte Statuspakete und doppelte Meldungen werden separat abgewiesen.

Der Kontrollvergleich aus Systemversuch 1 mit 300 Spuren wurde nach dem Herauslösen der festen Disposition erneut erzeugt. JSON, CSV und HTML bleiben bytegenau gleich. Die neue Verbindung ändert damit keine der zuvor berichteten Vergleichszahlen.

## Nächste Entscheidungen für Alex und Claude

- Das Register für einen echten Aktor dauerhaft machen: Auftrag, Wirkung und Abschluss brauchen eine passende Transaktions- oder Wiederherstellungsstrategie. Bis dahin dürfen ungeklärte Wirkungen nicht automatisch wiederholt werden.
- Für entfernte Arbeiter einen eigenen Auftrags- und Quittungsvertrag definieren. Die jetzige Prozessantwort enthält bereits Sitzung und Takt; sie ist jedoch kein authentifiziertes Netzwerkformat.
- Eine tatsächliche Bereitschaftsbestätigung der Reserve ergänzen. Der Versuch modelliert Reservierung als Nutzungserlaubnis eines schon laufenden Prozesses; Startzeit, Energie und echte Kapazität sind noch nicht gemessen.
- Alex’ Wortgedächtnis gezielt anbinden: bestätigte Wörter über `grob()` übersetzen und den Vorhersagehorizont explizit in eine Reservierungszeit überführen. Ein Alarm „binnen 30 Takten“ ist keine Zusage für genau den nächsten Takt.

Die Übergabe erfolgt auf dem eigenen Arbeitszweig `codex/verbund-disposition` und als Pull Request gegen `main`. Alex kann dort den Anschluss getrennt von seinem bereits übernommenen ersten Systemversuch prüfen. Die Hauptentwicklung wird für die Übergabe nicht automatisch zusammengeführt.
