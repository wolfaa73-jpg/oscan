# OSCan: Erfahrungen dürfen verblassen, Arbeitsverpflichtungen nicht

Stand 5. November 2026. Anschluss an `7893ba2` und [Pull Request #1](https://github.com/wolfaa73-jpg/oscan/pull/1). Diese Etappe ergänzt den dort beschriebenen Verbund um ein optionales dauerhaftes Auftragsjournal. Sie ist als eigener Vorschlag auf `codex/auftragsjournal` vorbereitet; die erste Anschluss-Etappe bleibt getrennt prüfbar.

## Ergebnis für die OS-Architektur

OSCan unterscheidet zwei Arten von Gedächtnis: Das lernende Gedächtnis darf alte Hinweise abschwächen und daraus andere Vorschläge ableiten. Das Auftragsjournal speichert dagegen verbindliche Tatsachen über bereits begonnene Arbeit. Weder Verblassen noch eine neue Prognose dürfen eine ungeklärte Wirkung nachträglich zu „noch nicht ausgeführt“ erklären.

`auftragsjournal.py` hält Auftragskennung, vollständigen Plan und Quittung in SQLite. Eine Transaktion schreibt `IN_ARBEIT` fest, bevor der Arbeiter aufgerufen wird. Eine zweite Transaktion bestätigt den Abschluss. Beim erneuten Öffnen werden unbestätigte Anfänge zu `UNGEKLAERT`. Bekannte Kennungen liefern dann ausschließlich ihre gespeicherte Quittung. Ein anderer Plan unter derselben Kennung bleibt ein Fehler.

Das erweitert einen ausführbaren Baustein für ein lernendes Betriebssystem. Es ersetzt noch keinen Bootpfad, Speicherschutz oder Gerätetreiber.

## Start in einer Minute

Auf macOS oder Linux, Python ab 3.9 mit `sqlite3`, im Laborordner:

```bash
python3 -B neustartlabor.py
python3 -B -m unittest -v
python3 -B neustartlabor.py --json beispiele/journal-neustart.json
```

Die Probe legt eigene temporäre Verzeichnisse an und beendet nur ihre eigenen kurzlebigen Kindprozesse. Keine zusätzliche Python-Bibliothek oder Hardware erforderlich. Für die vollständige vorhandene Testsuite wird weiterhin ein C++11-Compiler gebraucht. Die neue Besitzsperre verwendet POSIX `flock`; Windows ist für diese Erweiterung noch nicht unterstützt.

| Abrissstelle des eigenen Prozesses | Wirkung vor Neustart | Quittung nach Neustart | Wirkung nach 11 Wiederholungen |
|---|---:|---|---:|
| Nach gespeichertem Anfang, vor der Wirkung | 0 | `UNGEKLAERT` | 0 |
| Nach der Wirkung, vor gespeichertem Abschluss | 1 | `UNGEKLAERT` | 1 |
| Nach dauerhaft gespeichertem Abschluss | 1 | `ERLEDIGT` | 1 |

Die Testwirkung ist eine synchronisierte Dateizeile außerhalb der Datenbank. `os._exit(73)` beendet den Prozess ohne Kontextmanager, Abschlussroutine oder reguläres Schließen. Das prüft reale lokale Prozessabbrüche, keinen physischen Stromausfall und keinen echten Aktor. Die Ergebnisse stehen in `beispiele/journal-neustart.json`.

## Anschluss an den Verbund

```python
from pathlib import Path
from auftragsjournal import Auftragsjournal
from verbundsystem import Verbundsystem

# Dieses lokale Verzeichnis bleibt über Laufzeitneustarts erhalten.
pfad = Path("messungen/auftraege.sqlite3")
pfad.parent.mkdir(parents=True, exist_ok=True)
with Auftragsjournal(pfad) as journal:
    system = Verbundsystem(register=journal)
    # Neue Knotensitzungen anmelden, aktuelle Meldungen abfragen,
    # dann system.entscheide(...) / system.ausfuehren(...) wie bisher.
    for auftrag, quittung in journal.uebersicht():
        print(auftrag.sitzung.hex(), quittung.takt, quittung.status)
```

Das Journal erzeugt bei jedem Öffnen eine neue Auftragssitzung. Alte gespeicherte Kennungen bleiben zur Quittungsabfrage bekannt, unbekannte alte Freigaben werden abgewiesen. `uebersicht()` findet auch Kennungen wieder, die vorher nur im abgestürzten Prozess bekannt waren; sie startet nichts. Das neu aufgebaute `Verbundsystem` übernimmt keine alten Knotenmeldungen, Reservierungen oder Ausführungsfreigaben. Neue Arbeit braucht wieder aktuelle Meldungen. Ohne übergebenes Register bleibt der bisherige flüchtige Ablauf erhalten.

Kapazität und Sitzung werden vom übergebenen Register verwaltet. Das Journal gehört dem Aufrufer, der es mit dem Kontextmanager schließt. Änderungen der Lernregeln, des OC-Paketformats und der Firmware sind für diese Etappe nicht erforderlich.

## Welche Fehler abgefangen werden

- Ein zweiter Journalbesitzer wird über eine Betriebssystem-Dateisperre abgewiesen. Er darf die gerade laufende Arbeit des ersten Prozesses nicht irrtümlich als abgestürzt markieren. Die Sperre wird beim Prozessende freigegeben.
- Das Journal ist an seinen erzeugenden Prozess und Thread gebunden. Derselbe Auftrag kann aus seinem Callback den Status abfragen; eine verschachtelte neue Arbeitsausführung wird abgewiesen.
- Ein Schreibfehler vor dem Anfang lässt keine Wirkung zu. Scheitert das Speichern des Abschlusses, wird kein Erfolg gemeldet. Die betroffene Instanz sperrt sich bis zum erneuten Öffnen. Dabei entscheidet der tatsächlich gespeicherte Stand über `ERLEDIGT` oder `UNGEKLAERT`.
- Ergebnisverlust, falsche Ergebnisse und Unterbrechungen hinterlassen `UNGEKLAERT`. Der Verbund verwirft bei einer Ausführungsausnahme seine vorgemerkte Reserve.
- Die Kapazität gilt über alle Neustarts hinweg, standardmäßig 1.024 Einträge. Neue Arbeit wird bei voller Kapazität vor ihrem Beginn abgewiesen. Alte Quittungen bleiben abrufbar; kein automatisches Löschen alter Kennungen.
- Unbekannte Formate, beschädigte Dateien, unpassende Kapazität und widersprüchliche gespeicherte Ergebnisse führen zum Fehler. Es gibt kein stilles Zurücksetzen auf ein leeres Journal.

## Nachweise

127 Tests erfolgreich: 101 bestehende und 26 neue Journalprüfungen. Die neuen Prüfungen umfassen echte Prozessabbrüche an drei Grenzen, Bestätigung von Schreibvorgängen verloren, SQLite-Schreibfehler vor und nach Wirkung, Neustarts, volle Kapazität, konkurrierende Besitzer, falsche Threads, beschädigte Daten und die Verbindung zum festen Disponenten. Die Besitzkonkurrenz wird auch mit einem separaten Prozess geprüft.

Der Acht-Takt-Verbundversuch ohne dauerhaftes Register erzeugt weiterhin bytegenau dieselbe JSON-Ausgabe wie vor dieser Erweiterung. Seine fünf ausgeführten, zwei ausgesetzten und eine verfallene Arbeit bleiben unverändert. Die Lernregeln und die Dispositionsfunktion wurden nicht geändert.

Die Datenbank nutzt `journal_mode=DELETE`, `synchronous=EXTRA` und `fullfsync=ON`. `EXTRA` synchronisiert beim Rollback-Journal auch den Verzeichniseintrag nach dem Löschen des Journals; `fullfsync` nutzt auf macOS den zusätzlichen Flush. Grundlage sind die [SQLite-PRAGMA-Dokumentation](https://www.sqlite.org/pragma.html#pragma_synchronous) und die [Beschreibung atomarer SQLite-Commits](https://www.sqlite.org/atomiccommit.html). Das ersetzt keine Prüfung der konkreten Hardware und ihres Verhaltens bei Stromverlust.

## Grenzen und nächster sinnvoller Versuch

**Die externe Wirkung und die Datenbankbestätigung bilden keine gemeinsame Transaktion.** Eine angefangene, unbestätigte Arbeit kann noch laufen, bereits gewirkt haben oder nie zur Wirkung gekommen sein. `UNGEKLAERT` beschreibt genau dieses fehlende Wissen. Das Journal garantiert weder erfolgreiche Ausführung noch einen automatisch ermittelbaren Endzustand. Es gibt bewusst keinen automatischen Wiederholungs- oder „als erledigt markieren“-Knopf.

Die Deduplizierung bezieht sich auf dieselbe gespeicherte Kennung. Wer denselben fachlichen Auftrag mit neuer Sitzung oder neuem Takt erneut anlegt, erzeugt neue Arbeit. Auch das Zurückspielen einer älteren Datenbank, das Löschen des Journals oder eine automatische Rotation kann schon bekannte Kennungen vergessen. Für einen echten Anwendungsfall braucht es daher eine dauerhafte fachliche Auftrags-ID beim Auftraggeber und möglichst einen idempotenten oder abfragbaren Aktor.

Die Datenbank gehört auf eine vertrauenswürdige lokale Platte. Datenbank, SQLite-Nebendateien und `.lock`-Datei dürfen während der Nutzung nicht verschoben, ersetzt oder gelöscht werden; keine parallelen Zugriffe über Hardlinks oder mehrere Kopien. Ein Betriebssystembenutzer mit Schreibzugriff kann die Dateien verändern. Das ist kein authentifiziertes Netzprotokoll und keine Schutzgrenze gegen bösartige Prozesse. `quick_check` erkennt nicht jede denkbare inhaltliche Verfälschung.

Bei vollem Journal hält neue Arbeit an. Eine sichere Aufbewahrungs-/Archivierungsregel und ein Wiederherstellungsverfahren für echten Plattenverlust bleiben offen. Ein beim allerersten Anlegen unterbrochenes, unvollständiges Journal wird konservativ abgewiesen und muss untersucht werden.

Der nächste sinnvolle OS-Versuch ist eine konkrete, wiederanlaufbare Hintergrundarbeit auf zwei lokalen Arbeitern: fachliche Auftrags-ID, abfragbarer Ausführungsstand und bestätigte Reservebereitschaft. Erst dann sollten ein wirklich ausfallender Arbeiter, reale Durchlaufzeit und Reservekosten verglichen werden. Die Netzwerkübertragung von Arbeitsaufträgen und Alex’ Mehrtaktprognosen sind davon getrennte weitere Schritte.

Für die Übernahme zuerst PR #1 prüfen. Dieser Folge-PR ist gegen `codex/verbund-disposition` gerichtet, damit nur die Journal-Erweiterung sichtbar ist. Nach Übernahme der Grundlage kann Alex ihn auf `main` umstellen. Es wird nichts automatisch zusammengeführt.
