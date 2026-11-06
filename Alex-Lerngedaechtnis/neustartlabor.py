"""Drei harte Prozessabbrüche prüfen die dauerhafte Auftragslebensdauer.

Nur eigene kurzlebige Kindprozesse werden mit os._exit beendet. Die Wirkung
ist eine synchronisierte Zeile in einer eigenen temporären Datei, kein Aktor.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

from auftraege import Auftrag
from auftragsjournal import Auftragsjournal
from systemkern import Plan, disponiere


def _wirkung(pfad, auftrag):
    with pfad.open("a", encoding="ascii") as datei:
        datei.write("wirkung\n")
        datei.flush()
        os.fsync(datei.fileno())
    return hashlib.sha256(f"OSCan-Auftrag:{auftrag.plan.takt}".encode("ascii")).hexdigest()


def _kind(ordner, stelle):
    with Auftragsjournal(ordner / "auftraege.sqlite3") as journal:
        a = Auftrag(journal.sitzung, disponiere(1, "OK", False, False))
        print(json.dumps(dict(sitzung=a.sitzung.hex(), plan=asdict(a.plan))), flush=True)

        def arbeiter(auftrag):
            if stelle == "vor_wirkung":
                os._exit(73)
            ergebnis = _wirkung(ordner / "wirkung.txt", auftrag)
            if stelle == "nach_wirkung":
                os._exit(73)
            return ergebnis

        journal.ausfuehren(a, arbeiter)
        os._exit(73)  # Auch hier kein close(), __exit__() oder atexit.


def versuch():
    verlauf = []
    for stelle in ("vor_wirkung", "nach_wirkung", "nach_abschluss"):
        with tempfile.TemporaryDirectory(prefix="oscan-abbruch-") as tmp:
            ordner = Path(tmp)
            kind = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()),
                                   "--kind", stelle, "--ordner", tmp],
                                  capture_output=True, text=True, timeout=15)
            if kind.returncode != 73:
                raise RuntimeError(f"Abbruchprobe fehlgeschlagen: {kind.returncode}: {kind.stderr}")
            daten = json.loads(kind.stdout)
            a = Auftrag(bytes.fromhex(daten["sitzung"]), Plan(**daten["plan"]))
            wirkungsdatei = ordner / "wirkung.txt"
            def anzahl():
                return len(wirkungsdatei.read_text().splitlines()) if wirkungsdatei.exists() else 0
            vorher = anzahl()
            with Auftragsjournal(ordner / "auftraege.sqlite3") as journal:
                q = journal.ausfuehren(a, lambda auftrag: _wirkung(wirkungsdatei, auftrag))
                neue_sitzung = journal.sitzung != a.sitzung
                for _ in range(10):
                    if journal.ausfuehren(a, lambda auftrag: _wirkung(wirkungsdatei, auftrag)) != q:
                        raise AssertionError("Quittung bei Wiederholung verändert.")
            nachher = anzahl()
            erwartet = "ERLEDIGT" if stelle == "nach_abschluss" else "UNGEKLAERT"
            if q.status != erwartet or vorher != nachher or not neue_sitzung:
                raise AssertionError("Wiederherstellungsvertrag verletzt.")
            verlauf.append(dict(abbruch=stelle, prozess_exit=kind.returncode,
                                status_nach_neustart=q.status, neue_sitzung=neue_sitzung,
                                wirkungen_vorher=vorher, wirkungen_nachher=nachher,
                                wiederholungen=11))
    return dict(art="Harte lokale Prozessabbrüche; externe Testwirkung ist eine Dateizeile",
                grenze="Kein Stromausfalltest und keine atomare Transaktion mit einem realen Aktor",
                verlauf=verlauf)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--kind", choices=("vor_wirkung", "nach_wirkung", "nach_abschluss"),
                        help=argparse.SUPPRESS)
    parser.add_argument("--ordner", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.kind:
        if args.ordner is None:
            parser.error("Kindprozess braucht einen eigenen temporären Ordner.")
        _kind(args.ordner, args.kind)
    daten = versuch()
    if args.json:
        args.json.write_text(json.dumps(daten, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for z in daten["verlauf"]:
        print(f'{z["abbruch"]}: {z["status_nach_neustart"]}; '
              f'Wirkungen {z["wirkungen_vorher"]} → {z["wirkungen_nachher"]}; '
              f'{z["wiederholungen"]} Wiederholungen ohne neue Wirkung')


if __name__ == "__main__":
    main()
