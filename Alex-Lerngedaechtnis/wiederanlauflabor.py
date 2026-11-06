"""Misst reale lokale Arbeiterabbrüche, Reservebereitschaft und Wiederanlauf."""
import argparse
import hashlib
import json
import platform
import statistics
import tempfile
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from arbeitsspeicher import Hashauftrag
from arbeiterlaufzeit import STOERUNGEN, Wiederanlauf
from systemkern import Systemkern


def durchlauf(stoerung, vorbereitung, nummer=0):
    if stoerung not in STOERUNGEN or type(vorbereitung) is not bool:
        raise ValueError("Unbekannter Versuch.")
    daten = hashlib.sha256(b"OSCan-Wiederanlauf-Last-v1").digest() * 8192  # 256 KiB
    job = Hashauftrag(f"auftrag-{nummer}", daten)
    with tempfile.TemporaryDirectory(prefix="oscan-arbeiter-") as tmp:
        pfad = Path(tmp) / "arbeit.sqlite3"
        with Wiederanlauf(pfad, antwortfrist=.25) as laufzeit:
            primaer_start_ms = laufzeit.primaer.start_ms
            primaer_alt = laufzeit.primaer.instanz
            # Beide Varianten erhalten dieselbe Last und dieselbe künstliche Warnung.
            laufzeit.ausfuehren(Hashauftrag("warmlauf", daten))
            plan = Systemkern("erbe").schritt(1, "SCHWACH")
            vorbereitung_ms = 0.0
            ab_vorwarnung = time.perf_counter_ns()
            if vorbereitung and plan.reserve_fuer == 2:
                vorbereitung_ms = laufzeit.vorbereiten()
            ergebnis, bericht = laufzeit.ausfuehren(job, stoerung)
            mit_vorbereitung_ms = (time.perf_counter_ns() - ab_vorwarnung) / 1e6
            identisch, doppelt = laufzeit.ausfuehren(job)
            if identisch != ergebnis or doppelt["versuche"]:
                raise AssertionError("Wiederholung hat erneut einen Arbeiter beauftragt.")
            neustart_ms = 0.0
            if stoerung != "keine":
                neustart_ms = laufzeit.primaer_neustarten()
                if laufzeit.primaer.instanz == primaer_alt:
                    raise AssertionError("Neustart ohne neue Arbeiterinstanz.")
            folge, folgebericht = laufzeit.ausfuehren(Hashauftrag("folgeauftrag", b"OSCan lebt weiter"))
            if folgebericht["versuche"][0]["rolle"] != "PRIMAER":
                raise AssertionError("Folgeauftrag nicht auf dem bereiten Primär-Arbeiter.")
            standby_ms = ((time.perf_counter_ns() - laufzeit.reserve_bereit_ns) / 1e6
                          if laufzeit.reserve_bereit_ns is not None else 0.0)
            reserve_start_ms = laufzeit.reserve_start_ms
            if laufzeit.speicher.offene():
                raise AssertionError("Offene Arbeit nach erfolgreichem Versuch.")
        # Fachliche Kennung und Ergebnis überleben auch die Supervisor-Sitzung.
        with Wiederanlauf(pfad) as neu:
            wiederhergestellt, nach_neustart = neu.ausfuehren(job)
            if wiederhergestellt != ergebnis or nach_neustart["versuche"]:
                raise AssertionError("Supervisor-Neustart hat abgeschlossene Arbeit wiederholt.")
        return dict(nummer=nummer, stoerung=stoerung, reserve="vorbereitet" if vorbereitung else "kalt",
                    last_bytes=len(daten), vorwarnplan=asdict(plan), ergebnis=asdict(ergebnis),
                    primaer_start_ms=primaer_start_ms, vorbereitung_ms=vorbereitung_ms,
                    inklusive_vorbereitung_ms=mit_vorbereitung_ms,
                    reserve_start_ms=reserve_start_ms, reserve_bereit_gesamt_ms=standby_ms,
                    primaer_neustart_ms=neustart_ms, auftrag=bericht,
                    folgeauftrag_ms=folgebericht["gesamt_ms"],
                    wiederholung_ohne_arbeit=True, supervisor_neustart_ohne_doppelarbeit=True)


def zusammenfassung(laeufe):
    gruppen = []
    for stoerung in STOERUNGEN:
        for reserve in ("kalt", "vorbereitet"):
            zeilen = [z for z in laeufe if z["stoerung"] == stoerung and z["reserve"] == reserve]
            if not zeilen:
                continue
            werte = {}
            for name in ("gesamt_ms", "wiederanlauf_ms"):
                zahlen = [z["auftrag"][name] for z in zeilen]
                werte[name] = dict(min=min(zahlen), median=statistics.median(zahlen), max=max(zahlen))
            for name in ("primaer_start_ms", "vorbereitung_ms", "inklusive_vorbereitung_ms", "reserve_bereit_gesamt_ms", "primaer_neustart_ms"):
                zahlen = [z[name] for z in zeilen]
                werte[name] = dict(min=min(zahlen), median=statistics.median(zahlen), max=max(zahlen))
            gruppen.append(dict(stoerung=stoerung, reserve=reserve, anzahl=len(zeilen), werte=werte))
    return gruppen


def versuch(wiederholungen=10):
    if type(wiederholungen) is not int or not 1 <= wiederholungen <= 100:
        raise ValueError("1 bis 100 Wiederholungen erforderlich.")
    laeufe = []
    # Reihenfolge innerhalb jedes Paars alterniert gegen einen einfachen Reihenfolgeeffekt.
    for nr in range(wiederholungen):
        for stoerung in STOERUNGEN:
            for vorbereitet in ((False, True) if nr % 2 == 0 else (True, False)):
                laeufe.append(durchlauf(stoerung, vorbereitet, nr))
    ordner = Path(__file__).parent
    return dict(art="Lokaler Hashdienst, reale Arbeiterprozesse, kontrollierte Fehler",
                erstellt_utc=datetime.now(timezone.utc).isoformat(),
                umgebung=dict(system=platform.system(), version=platform.release(),
                              architektur=platform.machine(), python=platform.python_version()),
                methodik=dict(wiederholungen=wiederholungen, last_bytes=262144, antwortfrist_s=.25,
                              startfrist_s=5, uhr="perf_counter_ns, nur im Supervisor",
                              hinweis="Künstliche Vorwarnung, keine Messung der Prognosegüte; keine Echtzeitgarantie"),
                quell_sha256={name: hashlib.sha256((ordner / name).read_bytes()).hexdigest()
                               for name in ("arbeitsspeicher.py", "arbeiterlaufzeit.py", "wiederanlauflabor.py",
                                            "systemkern.py", "kern.py")},
                zusammenfassung=zusammenfassung(laeufe), laeufe=laeufe)


def markdown(daten):
    zeilen = ["# OSCan: gemessener Arbeiter-Wiederanlauf", "", f'Messzeit: {daten["erstellt_utc"]}.', "",
              "Alle Werte sind Millisekunden; angegeben ist der Median. Minima, Maxima und einzelne Läufe stehen in der JSON-Datei.", "",
              "| Störung | Reserve | n | Auftrag gesamt | Inklusive Vorbereitung | Ab Fehlererkennung bis Ergebnis | Primär-Neustart |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for z in daten["zusammenfassung"]:
        w = z["werte"]
        zeilen.append(f'| {z["stoerung"]} | {z["reserve"]} | {z["anzahl"]} | '
                      f'{w["gesamt_ms"]["median"]:.3f} | {w["inklusive_vorbereitung_ms"]["median"]:.3f} | '
                      f'{w["wiederanlauf_ms"]["median"]:.3f} | {w["primaer_neustart_ms"]["median"]:.3f} |')
    zeilen += ["", "Die Auftragszeit beginnt vor dem dauerhaften Registrieren und endet beim geprüften Ergebnis. "
               "Der vorgezogene Reservestart liegt außerhalb dieses Intervalls; die zusätzliche Spalte inklusive Vorbereitung misst ihn mit. "
               "Die Wiederanlaufzeit beginnt bei der Fehlererkennung, umfasst bestätigtes Beenden, Speicherprüfung und gegebenenfalls Reservestart/-arbeit. "
               "Bei einem Hänger liegt die Antwortfrist davor und ist in der gesamten Auftragszeit enthalten.", "",
               "`vor_commit` beendet den Arbeiter nach einem unbestätigten Datenbank-Update; "
               "`nach_commit` beendet ihn nach dem gespeicherten Ergebnis und vor der Antwort; "
               "`haengt` hält ihn in einer offenen Schreibtransaktion fest. "
               "Bei `nach_commit` genügt die Ergebnisabfrage, ohne Ersatzarbeit.", "",
               "Die Last umfasst 256 KiB synthetischer Daten pro Auftrag. Jeder Lauf enthält Warmlauf, "
               "Prüfung einer Wiederholungsanfrage, gegebenenfalls Primär-Neustart, Folgeauftrag und Wiederöffnung des Supervisors. "
               "Nur die bezeichneten Intervalle stehen in der Tabelle. Die JSON-Datei enthält außerdem die Bereitschaftsdauer der Reserve; "
               "diese ist keine CPU-Zeit- oder Energiemessung.", "",
               "Die Vorwarnung ist künstlich und aktiviert hier bereits das feste Erbe der vorhandenen Lernregel. "
               "Eine feste SCHWACH-Regel könnte dieselbe Vorbereitung auslösen. Der Versuch misst die Wirkung tatsächlicher Reservebereitschaft, "
               "keinen Vorteil lernender Prognosen. Einzelrechner-Messung ohne zugesicherte Latenz oder Übertragbarkeit auf ESP32/Pi.", ""]
    return "\n".join(zeilen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiederholungen", type=int, default=10)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--bericht", type=Path)
    args = parser.parse_args()
    daten = versuch(args.wiederholungen)
    if args.json:
        args.json.write_text(json.dumps(daten, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    text = markdown(daten)
    if args.bericht:
        args.bericht.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
