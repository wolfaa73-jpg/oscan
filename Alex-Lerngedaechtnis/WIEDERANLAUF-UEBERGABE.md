# OSCan: echter Arbeiter-Ausfall und kontrollierter Wiederanlauf

Stand 5. November 2026. Grundlage ist `eba051e` aus [Pull Request #2](https://github.com/wolfaa73-jpg/oscan/pull/2). Diese Etappe ist auf `codex/arbeiter-wiederanlauf` separat prüfbar.

## Ergebnis

Ein lokaler Supervisor betreibt einen Primär-Arbeiter und bei Bedarf einen Reserve-Arbeiter als echte, getrennte Prozesse. Ein Arbeiter gilt erst nach seiner Bereitschaftsbestätigung als nutzbar. Fällt der Primär-Arbeiter während eines Auftrags aus oder hängt er, bestätigt die Steuerung zunächst sein Prozessende. Danach prüft sie das dauerhaft gespeicherte Ergebnis. Nur eine noch offene Arbeit wird an die Reserve übergeben. Ein neu gestarteter Primär-Arbeiter erhält eine neue Instanzkennung und kann den nächsten Auftrag übernehmen.

Die konkrete Hintergrundarbeit ist ein benannter SHA-256-Auftrag mit bis zu 1 MiB Daten. Ihre fachliche Wirkung besteht im gespeicherten Ergebnisdatensatz. Auftrag, Inhalt und Ergebnis sind über Supervisor-Neustarts hinweg auffindbar. Wiederholte Anfragen mit derselben Kennung liefern das vorhandene Ergebnis; eine gleiche Kennung mit anderem Inhalt wird abgewiesen.

Das beantwortet für diesen Backend-Typ eine bisher offene Frage aus dem Auftragsjournal: Nach einem Arbeiterausfall lässt sich unterscheiden, ob das Ergebnis schon gespeichert ist oder die Arbeit noch offen ist. Für beliebige Geräteaktionen bleibt `UNGEKLAERT` dagegen richtig. Das bestehende `Auftragsjournal` wird nicht nachträglich umgeschrieben oder automatisch auf „erledigt“ gesetzt.

## Ausprobieren

Im Laborordner, macOS oder Linux, Python ab 3.9 mit SQLite:

```bash
python3 -B -m unittest -v
python3 -B wiederanlauflabor.py --wiederholungen 1
python3 -B wiederanlauflabor.py --wiederholungen 10 --json beispiele/arbeiter-wiederanlauf.json --bericht Wiederanlaufbericht.md
```

Die vollständige Testsuite braucht wie bisher einen C++11-Compiler. Die Messreihe erzeugt ausschließlich eigene temporäre Datenbanken und Prozesse; sie beendet keine fremden Prozesse. Alle Arbeiter werden nach dem jeweiligen Versuch beendet. `--wiederholungen 10` bedeutet 80 Durchläufe: vier Störfälle, zwei Reservevarianten, jeweils zehn Wiederholungen. Die Reihenfolge kalt/vorbereitet wechselt innerhalb der Paare. Messzahlen variieren mit dem Rechnerzustand.

| Datei | Aufgabe |
|---|---|
| `arbeitsspeicher.py` | Dauerhafte fachliche Kennungen, unveränderliche Eingaben, Ergebnisabfrage und begrenzte Kapazität |
| `arbeiterlaufzeit.py` | Prozessbesitz, Bereitschaft, Antwortfrist, bestätigtes Beenden, Übernahme und Neustart |
| `wiederanlauflabor.py` | Reproduzierbare Störungen und Messintervalle |
| `test_wiederanlauf.py` | 28 zusätzliche Prüfungen einschließlich echter Prozessausfälle |
| `Wiederanlaufbericht.md` | Lesbare Zusammenfassung der Messreihe |
| `beispiele/arbeiter-wiederanlauf.json` | Alle 80 Läufe, Minima/Mediane/Maxima, Umgebung und Quellenprüfsummen |

## Ablauf und feste Grenzen

1. Der Supervisor registriert Kennung und Daten dauerhaft. Standardmäßig sind höchstens 128 Aufträge erlaubt; die Grenze bleibt über Neustarts erhalten. Es gibt kein automatisches Vergessen alter Kennungen. Die Grenze zählt Aufträge, nicht verbrauchte Bytes.
2. Der eigene Arbeiter wird mit `spawn` gestartet. Seine Bestätigung enthält Supervisor-Epoche, zufällige Arbeiterinstanz und PID. Jede weitere Antwort muss zur Instanz, Anfragenummer und Auftragskennung passen. Die lokalen Nachrichten sind begrenzte JSON-Daten über private Pipes, keine Shellbefehle.
3. Der Arbeiter prüft innerhalb einer SQLite-Schreibtransaktion die aktuelle Supervisor-Epoche. Er berechnet den Hash und speichert das Ergebnis in derselben Transaktion. Ein bereits vorhandenes Ergebnis behält seinen ursprünglichen Arbeiter als Herkunft.
4. Bei fehlender oder falscher Antwort wird der alte Prozess beendet und mit `join` auf sein Ende geprüft. Falls erforderlich folgen `terminate` und `kill`, jeweils nur für das eigene Prozessobjekt. Der alte Kanal wird danach verworfen. Ohne bestätigtes Ende bleiben Ersatzarbeit und weitere Aufträge dieser Laufzeit gesperrt.
5. Nach bestätigtem Ende wird der Speicher abgefragt. Ein bestätigtes Ergebnis wird zurückgegeben. Ein offener Auftrag darf hier auf der Reserve erneut berechnet werden, weil die vollständige fachliche Wirkung innerhalb derselben Datenbank liegt.
6. Pro Aufruf sind höchstens zwei Arbeitsversuche erlaubt. Fällt auch die Reserve ohne Abschluss aus, bleibt der fachliche Auftrag offen und die Laufzeit meldet einen Fehler. `speicher.offene()` findet solche Aufträge wieder. Ein weiterer Versuch braucht eine explizite Entscheidung des Aufrufers.
7. `primaer_neustarten()` beendet gegebenenfalls den alten Primär-Arbeiter und wartet auf eine neue Bereitschaftsbestätigung. Alte Instanzmeldungen werden nicht als Meldungen des neuen Arbeiters akzeptiert.

Eine Dateisperre begrenzt den Speicher auf einen Supervisor. Bei Wiederöffnung erhält er eine neue Epoche. Ein alter, noch lebender Arbeiter darf unter seiner alten Epoche keinen neuen Ergebnisdatensatz schreiben. Epochenprüfung und Ergebnisänderung liegen in derselben Schreibtransaktion: Ein Neustart kann einen bereits aktiven alten Schreiber erst ablösen, nachdem dessen Transaktion abgeschlossen oder zurückgerollt wurde. Bleibt die Datenbank gesperrt, schlägt die Öffnung fehl; fehlender Zugriff gilt nicht als „noch nicht ausgeführt“.

Die Zeitgrenzen sind Prüffristen des Versuchs: fünf Sekunden für den Start, in der Messreihe 250 ms für eine Antwort. Prozessbeendigung und Speicherung benötigen zusätzliche Zeit. Es gibt keine harte Ende-zu-Ende-Echtzeitgarantie.

## Verbindung mit dem lernenden Teil

Der Versuch verwendet den vorhandenen `Systemkern`: Bei einem künstlichen `SCHWACH`-Signal liefert dessen Regel `erbe` einen Vorwarnplan. In der vorbereiteten Variante wird daraufhin tatsächlich der Reserveprozess gestartet und seine Bereitschaft abgewartet. Die kalte Vergleichsvariante nutzt dieselbe Eingabe, verschiebt den Start aber bis nach dem Ausfall.

Die Vorwarnung stammt hier schon aus dem festen Erbe. Eine feste SCHWACH-Regel würde dieselbe Vorbereitung auslösen. Dies ist ein Versuch zum realen Aktions-Backend, kein neuer Nachweis über die Güte des Lernverfahrens. Vorwarnung und Ausfallzeitpunkt sind kontrollierte Eingaben.

```python
from pathlib import Path
from arbeitsspeicher import Hashauftrag
from arbeiterlaufzeit import Wiederanlauf
from systemkern import Systemkern

pfad = Path("messungen/arbeit.sqlite3")
pfad.parent.mkdir(parents=True, exist_ok=True)
with Wiederanlauf(pfad) as laufzeit:
    plan = Systemkern("erbe").schritt(1, "SCHWACH")
    if plan.reserve_fuer == 2:
        laufzeit.vorbereiten()
    auftrag = Hashauftrag("hintergrund:1", b"OSCan-Testinhalt")
    ergebnis, zeiten = laufzeit.ausfuehren(auftrag, stoerung="vor_commit")
    laufzeit.primaer_neustarten()
    print(ergebnis.sha256, zeiten["wiederanlauf_ms"])
```

`stoerung` ist ein Testschalter; ohne ihn läuft der Arbeiter regulär. Bei erneutem Start desselben Beispiels ist der Auftrag bereits erledigt und wird ohne neue Arbeiteranfrage beantwortet. Für einen neuen Inhalt muss der Auftraggeber eine neue fachliche Kennung vergeben.

Dieser Backend-Vertrag verwendet fachliche Kennungen und beliebige begrenzte Hashdaten. Das ältere Auftragsjournal speichert dagegen den festen Taktauftrag aus dem ersten Systemversuch. Beide Formate bleiben getrennt; der OC-Verbund ist noch nicht an diesen neuen Backend-Vertrag angeschlossen. Sein bisheriger Acht-Takt-Ablauf und die bestehenden Firmware-/Lernregeln bleiben unverändert.

## Prüfung und gemessene Ergebnisse

155 Tests erfolgreich: die bisherigen 127 und 28 neue. Geprüft sind unter anderem:

- echte Abbrüche vor und nach dem Commit sowie ein Arbeiter, der in einer offenen Schreibtransaktion hängt;
- Bereitschaft, Primär-Neustart und erfolgreich bearbeiteter Folgeauftrag;
- keine Übernahme ohne bestätigtes Prozessende, tote Reserve und zwei aufeinanderfolgende Arbeiterausfälle;
- Wiederholung unter derselben fachlichen Kennung auch nach Supervisor-Neustart;
- alte Antwortinstanz und alter noch lebender Arbeiter nach Epochenwechsel;
- unveränderlicher Inhalt, volle Kapazität, Schreib-/Lesefehler, beschädigte Daten und vollständiges Beenden eigener Prozesse.

Alle 80 Messläufe lieferten das geprüfte Ergebnis, beantworteten eine Wiederholung ohne neue Arbeiteranfrage und behielten das Ergebnis nach Wiederöffnung des Supervisors. Es waren 20 Kontrollläufe ohne Störung und 60 Läufe mit einem absichtlich ausfallenden oder hängenden Primär-Arbeiter. Die Störung `vor_commit` erfolgt nach dem Datenbank-Update, während dessen Transaktion noch offen ist; der anschließende Zugriff prüft damit auch die Wiederherstellung des Rollback-Journals.

Auf dem verwendeten Mac lag die Zeit von der Fehlererkennung bis zum Ergebnis bei `vor_commit` im Median bei **74,909 ms mit kalter Reserve** und **5,656 ms mit vorbereiteter Reserve**. Die gesamte Auftragszeit lag bei 79,869 beziehungsweise 11,391 ms. Einschließlich der vorgezogenen Vorbereitung waren es jedoch **79,873 beziehungsweise 79,011 ms**. Der Reservestart wird zeitlich verlagert; er verschwindet nicht. Bei einem Abbruch nach dem Commit war keine Ersatzarbeit nötig.

Diese Einzelrechner-Messung beschreibt diesen Lauf mit synthetischen 256-KiB-Aufträgen. Sie ist keine Zusicherung von Latenzen, kein Energienachweis und kein Vorteil eines vollständigen Betriebssystems. Alle Einzeldaten und Bereiche stehen im [Messbericht](Wiederanlaufbericht.md) und der JSON-Datei. Der Bericht weist die gesamte Auftragszeit, die Zeit inklusive Vorbereitung und die Zeit ab Fehlererkennung getrennt aus.

## Übergabe und nächste Grenzen

Die sichere Wiederholung gilt hier ausschließlich, weil der Ergebnisdatensatz die gesamte fachliche Wirkung des Backends ist. Ein Hash kann nach einem Abbruch erneut berechnet werden, ohne eine externe Wirkung zu verdoppeln. Für einen Motor, einen Dateiversand oder eine beliebige externe API muss ein anderer, ausdrücklicher Wiederherstellungsvertrag geschaffen werden. Ein fachlich gleicher Auftrag unter neuer Kennung bleibt neue Arbeit.

Vorausgesetzt wird eine vertrauenswürdige lokale Platte. Datenbank, SQLite-Nebendateien und Besitzsperre dürfen nicht während des Betriebs ersetzt, gelöscht oder über alternative Hardlinks geöffnet werden. Ein älteres Backup oder eine neue leere Datenbank kann frühere Kennungen vergessen. Stromausfall, Plattenverlust, bösartige Prozesse, Windows und ein entfernter ESP32-/Pi-Verbund sind nicht geprüft.

Für Alex und Claude ist der nächste Anschluss klar begrenzt: den neuen fachlichen Auftrag und seine Bereitschafts-/Ergebnisabfrage in den OC-Verbund einbinden, mit derselben Kennung über Sitzungswechsel. Dabei dürfen Statusfrische, Auftragssitzung und fachliche Identität nicht verwechselt werden. Erst danach bietet sich ein Versuch auf getrennten Geräten an.

Dieser Vorschlag baut auf PR #2 auf und wird zunächst gegen `codex/auftragsjournal` eröffnet. Zuerst die Grundlagen aus PR #1 und #2 prüfen; nach deren Übernahme die Basis dieses Vorschlags auf `main` umstellen. Es wird nichts automatisch zusammengeführt.

Technische Grundlagen: [Python-Prozesse, Sentinel und Prozessbeendigung](https://docs.python.org/3/library/multiprocessing.html) sowie [SQLite-Transaktionen](https://www.sqlite.org/lang_transaction.html). Nach einer erzwungenen Prozessbeendigung werden dessen Kommunikationskanäle nicht weiterverwendet. Die Datenbank verwendet wie das frühere Journal `synchronous=EXTRA` und auf macOS zusätzlich `fullfsync`.
