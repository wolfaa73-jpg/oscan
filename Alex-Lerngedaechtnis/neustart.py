"""Einen abschnittsweisen Knotenlauf mit prüfbarem, versioniertem Lernstand fortsetzen."""
import argparse
import csv
import hashlib
import hmac
import json
import math
import os
import sys
import tempfile
from pathlib import Path

from kern import Knoten, MAX_TAKT, REGELN, Startwertgedaechtnis, ZUSTAENDE
from versuch import lies_spur, messpunkte


def kodiert(daten):
    return json.dumps(daten, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def als_matrix(tabelle):
    return [[tabelle[z][f] for f in ZUSTAENDE] for z in ZUSTAENDE]


def sichern(pfad, quelle, knoten):
    g = knoten.gedaechtnis
    # Genau die benannten Regeln. Abweichende Einstellungen fallen beim Laden auf.
    regel = next((name for name, typ in REGELN.items() if type(g) is typ), None)
    if regel is None:
        raise ValueError("Für diese Lernregel gibt es kein Sicherungsformat.")
    daten = dict(regel=regel, format="alex-knoten-v1", quelle=quelle, takt=knoten.takt,
                 zustand=knoten.zustand, halbwertszeit=g.halbwertszeit,
                 vokabular=list(ZUSTAENDE), erbe=als_matrix(g.erbe),
                 gewichte=als_matrix(g.gewichte))
    umschlag = dict(daten=daten, sha256=hashlib.sha256(kodiert(daten)).hexdigest())
    # Eine neue Datei im selben Dateisystem veröffentlichen. link() scheitert
    # atomar, wenn ein anderer Schreiber den Namen schon veröffentlicht hat.
    with tempfile.NamedTemporaryFile(dir=pfad.parent, delete=False) as datei:
        tmp = Path(datei.name)
        try:
            datei.write(kodiert(umschlag) + b"\n")
            datei.flush()
            os.fsync(datei.fileno())
        except BaseException:
            tmp.unlink()
            raise
    try:
        os.link(tmp, pfad)
    finally:
        tmp.unlink()


def laden(pfad, quelle):
    try:
        umschlag = json.loads(pfad.read_bytes())
        d = umschlag["daten"]
        if not hmac.compare_digest(umschlag["sha256"], hashlib.sha256(kodiert(d)).hexdigest()):
            raise ValueError("Prüfsumme stimmt nicht.")
        if d["format"] != "alex-knoten-v1" or d["vokabular"] != list(ZUSTAENDE):
            raise ValueError("Format oder Tokenreihenfolge unbekannt.")
        if d["quelle"] != quelle:
            raise ValueError("Der Stand gehört zu einer anderen Messreihe.")
        if type(d["takt"]) is not int or not 1 <= d["takt"] <= MAX_TAKT or d["zustand"] not in ZUSTAENDE:
            raise ValueError("Ungültiger letzter Messpunkt.")
        if d["regel"] not in REGELN:
            raise ValueError("Unbekannte Lernregel.")
        g = REGELN[d["regel"]]()
        if d["halbwertszeit"] != g.halbwertszeit:
            raise ValueError("Halbwertszeit passt nicht zur Regelversion.")
        # Stände aus Version 0.2 tragen kein Erbe. Ihre Regeln hatten auch keines.
        erbe, anfang = d.get("erbe", [[0] * 3] * 3), als_matrix(g.erbe)
        if isinstance(g, Startwertgedaechtnis):
            # Der Startwert verblasst mit eigenen Ausgängen. Er liegt zwischen null und seinem Anfang.
            if not isinstance(erbe, list) or len(erbe) != 3 or any(not isinstance(z, list) or len(z) != 3 for z in erbe):
                raise ValueError("Ungültiges Erbe.")
            for z, zeile, start in zip(ZUSTAENDE, erbe, anfang):
                for f, wert, hoechstens in zip(ZUSTAENDE, zeile, start):
                    if type(wert) not in (int, float) or not math.isfinite(wert) or not 0 <= wert <= hoechstens:
                        raise ValueError("Erbe passt nicht zur Regelversion.")
                    g.erbe[z][f] = wert
        elif erbe != anfang:
            raise ValueError("Erbe passt nicht zur Regelversion.")
        matrix = d["gewichte"]
        if not isinstance(matrix, list) or len(matrix) != 3:
            raise ValueError("Ungültige Gedächtnismatrix.")
        for z, zeile in zip(ZUSTAENDE, matrix):
            if not isinstance(zeile, list) or len(zeile) != 3:
                raise ValueError("Ungültige Gedächtniszeile.")
            for f, wert in zip(ZUSTAENDE, zeile):
                if type(wert) not in (int, float) or not math.isfinite(wert) or not 0 <= wert <= d["takt"]:
                    raise ValueError("Ungültiges Gewicht.")
                g.gewichte[z][f] = wert
        if sum(sum(row.values()) for row in g.gewichte.values()) > d["takt"]:
            raise ValueError("Mehr Belege als beobachtbare Übergänge.")
        knoten = Knoten(g)
        knoten.takt, knoten.zustand = d["takt"], d["zustand"]
        return knoten
    except (KeyError, TypeError, OverflowError, ValueError) as fehler:
        raise ValueError(f"Ungültiger Lernstand: {fehler}") from fehler


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("spur", type=Path)
    p.add_argument("--quelle", required=True, help="Kennung einer durchgehend nummerierten Messreihe")
    p.add_argument("--laden", type=Path)
    p.add_argument("--sichern", type=Path, help="Neuer Dateiname, bestehende Stände bleiben erhalten")
    p.add_argument("--regel", choices=tuple(REGELN), help="Regel für einen neuen Lernstand")
    a = p.parse_args()
    try:
        spur = lies_spur(a.spur, minimum=1)
        if a.laden and isinstance(spur[0], str):
            raise ValueError("Fortsetzen benötigt eine CSV mit absoluten Takten.")
        if a.laden and a.regel:
            raise ValueError("Bei Fortsetzung gilt die Regel im Lernstand.")
        if a.laden:
            k = laden(a.laden, a.quelle)
        else:
            k = Knoten(REGELN[a.regel or "zeit"]())
        log = csv.writer(sys.stdout, lineterminator="\n")
        log.writerow(("takt", "zustand", "sofort", "vorwarnung"))
        for t, z in messpunkte(spur):
            s = k.schritt(t, z)
            log.writerow((t, z, int(s.sofort), int(s.vorwarnung)))
        if a.sichern:
            sichern(a.sichern, a.quelle, k)
    except (ValueError, OSError, csv.Error) as fehler:
        p.exit(2, f"Knotenlauf abgebrochen: {fehler}\n")


if __name__ == "__main__":
    main()
