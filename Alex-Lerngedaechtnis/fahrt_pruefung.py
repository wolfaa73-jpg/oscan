"""Gespeicherte Fahrtdateien prüfen, ohne Gerät, Änderung oder Reparatur.

python fahrt_pruefung.py aufnahme.bin --format v2 --json pruefung.json
Exit: 0 = geprüfte Regeln unauffällig, 1 = Auffälligkeiten/leer, 2 = Format-/Dateifehler.
Der Prüfer belegt keine physische Vollständigkeit und prüft keinen gespeicherten Lernstand.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import fahrt

GRENZEN = [
    "Kein Nachweis gegen beliebige Bitfehler: Das Dateiformat enthält keine eigene vollständige Prüfsumme.",
    "SHA-256 identifiziert die geprüften Bytes; ohne vorab bekannten Sollwert ist das keine Integritätsbestätigung.",
    "Nicht gesicherte Takte vor Stromausfall und stromlose Zeit sind im Protokoll nicht rekonstruierbar.",
    "Ein lückenloser Taktzähler belegt weder einen Sekundentakt noch die Übereinstimmung mit dem gespeicherten Lernstand.",
    "V1 hat keine Kennung; bei bekanntem V2-Export --format v2 wählen, damit ein beschädigter Kopf nicht als V1 gelesen wird.",
]


def pruefe(daten, format_erwartet="auto", max_beispiele=20):
    """Vollständige Zähler und begrenzte Beispiele liefern; Daten bleiben unverändert.

    Satznummern beginnen bei 1, Byteoffsets bei 0 in der Eingabedatei.
    Die Formatprüfung verwendet denselben Decoder wie fahrt.py.
    """
    if (format_erwartet not in ("auto", "v1", "v2")
            or not isinstance(max_beispiele, int) or max_beispiele < 0):
        raise ValueError("Ungültige Prüfeinstellung")
    zahlen = Counter()
    beispiele = []
    strukturfehler = 0
    out = dict(
        version=1,
        eingabe=dict(bytes=len(daten), sha256=hashlib.sha256(daten).hexdigest(),
                     format="unbestimmt", erwartet=format_erwartet),
        saetze=0, dekodiert=0, neustarts=0, neustarts_bei_null=0, empfinden_saetze=0,
        taktuebergaenge_geprueft=0, erster_takt=None, letzter_takt=None,
        fehlende_taktnummern=0, befunde={}, beispiele=beispiele, grenzen=GRENZEN[:],
    )

    def befund(art, **details):
        zahlen[art] += 1
        if len(beispiele) < max_beispiele:
            beispiele.append(dict(art=art, **details))

    def ende():
        out["befunde"] = dict(sorted(zahlen.items()))
        out["beispiele_ausgelassen"] = sum(zahlen.values()) - len(beispiele)
        if strukturfehler:
            out["status"] = "formatfehler"
        elif not out["saetze"]:
            out["status"] = "leer"
        elif zahlen:
            out["status"] = "auffaellig"
        else:
            out["status"] = "unauffaellig"
        return out

    # Auch der V2-Sender liefert bei noch leerem Log einen Export ohne Kopf.
    if not daten:
        return ende()
    v2 = daten.startswith(fahrt.V2_KENNUNG)
    if (format_erwartet == "v2" and not v2) or (format_erwartet == "v1" and v2):
        strukturfehler += 1
        befund("format_passt_nicht")
        return ende()
    if v2:
        out["eingabe"]["format"] = "v2"
        kopf, breite = len(fahrt.V2_KOPF), fahrt.V2_BYTES
        if daten[:kopf] != fahrt.V2_KOPF:
            strukturfehler += 1
            befund("ungueltiger_v2_kopf")
            return ende()
    else:
        out["eingabe"]["format"] = "v1"
        kopf, breite = 0, fahrt.SATZ.size

    rest = (len(daten) - kopf) % breite
    if rest:
        strukturfehler += 1
        befund("unvollstaendiger_satz", byteoffset=len(daten) - rest, restbytes=rest)
    out["saetze"] = (len(daten) - kopf) // breite
    vorher = None
    for i in range(out["saetze"]):
        pos = kopf + i * breite
        raw = daten[pos:pos + breite]
        try:
            s = next(fahrt.saetze((fahrt.V2_KOPF if v2 else b"") + raw))
        except ValueError:
            strukturfehler += 1
            befund("satz_nicht_dekodierbar", satz=i + 1, byteoffset=pos)
            # Keine scheinbare Taktlücke über einen nicht lesbaren Satz hinweg erfinden.
            vorher = None
            continue

        out["dekodiert"] += 1
        out["neustarts"] += s["neustart"]
        out["neustarts_bei_null"] += s["bei_null"]
        out["empfinden_saetze"] += int("gerade" in s)
        basis = dict(satz=i + 1, byteoffset=pos, takt=s["takt"], neustart=bool(s["neustart"]))
        if s["zustand"] == "?":
            strukturfehler += 1
            befund("ungueltiger_zustand", **basis)
        if s["grenze_cg"] is not None and s["grenze_cg"] < 0:
            strukturfehler += 1
            befund("negative_vorhersagegrenze", **basis)
        reiz = s.get("reiz")
        if reiz is not None:
            if bool(reiz & 1) != bool(s["last"]):
                strukturfehler += 1
                befund("widerspruechliche_lastbits", **basis)
            # Bit 8 = Sendung versucht; 16 = Funk bereit; 32 = Sende-API meldet Fehler.
            if (reiz & 8 and not reiz & 16) or (reiz & 32 and (reiz & 24) != 24):
                strukturfehler += 1
                befund("widerspruechliche_funkbits", **basis)
            if reiz & 32:
                befund("funk_sendefehler", **basis)
        if s["temp_dc"] is None:
            befund("temperatur_fehlt", **basis)
        elif not -1000 <= s["temp_dc"] <= 2000:
            befund("temperatur_unplausibel", **basis)

        if out["erster_takt"] is None:
            out["erster_takt"] = s["takt"]
        out["letzter_takt"] = s["takt"]
        if vorher is not None:
            out["taktuebergaenge_geprueft"] += 1
            delta = (s["takt"] - vorher) & 0xffffffff
            if delta != 1:
                if delta == 0:
                    art = "doppelter_takt"
                elif delta < 0x80000000:
                    art = "taktluecke"
                    out["fehlende_taktnummern"] += delta - 1
                else:
                    art = "taktruecksprung"
                befund(art, vorher=vorher, erwartet=(vorher + 1) & 0xffffffff, **basis)
        vorher = s["takt"]
    return ende()


def exitcode(ergebnis):
    if ergebnis["status"] == "formatfehler":
        return 2
    return 0 if ergebnis["status"] == "unauffaellig" else 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("datei", type=Path)
    p.add_argument("--format", choices=("auto", "v1", "v2"), default="auto", dest="format_erwartet")
    p.add_argument("--json", type=Path, dest="ausgabe",
                   help="neue JSON-Datei; bestehende Dateien werden nie überschrieben")
    a = p.parse_args(argv)
    try:
        daten = a.datei.read_bytes()
    except OSError:
        print("Eingabe konnte nicht gelesen werden.", file=sys.stderr)
        return 2
    r = pruefe(daten, a.format_erwartet)
    if a.ausgabe:
        try:
            with a.ausgabe.open("x", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False, indent=2)
                f.write("\n")
        except FileExistsError:
            print("Ausgabedatei existiert bereits und bleibt unverändert.", file=sys.stderr)
            return 2
        except OSError:
            print("Prüfbericht konnte nicht geschrieben werden.", file=sys.stderr)
            return 2
    else:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    return exitcode(r)


if __name__ == "__main__":
    sys.exit(main())
