"""Körpersignale des Knotens aufzeichnen und prüfen: Chiptemperatur, freier Speicher, Schleifenlücke."""
import argparse
import csv
import json
import signal
import statistics
import sys
import time
from dataclasses import asdict, astuple, dataclass
from pathlib import Path

from boardprobe import antwort, bereit
from kern import Knoten, REGELN, ZUSTAENDE

KOPF = ("takt", "zeit_ms", "temp_dc", "heap", "luecke_us", "zustand", "sofort", "vorwarnung", "last")
KOPF_ALT = KOPF[:-1]  # erste Aufnahmen vom 5. November, noch ohne Lastphase
MAX_TEMP = 100000  # Zehntelgrad, wie maxTemp im Sketch


@dataclass(frozen=True)
class Grenzen:
    """Temperatur in Zehntelgrad, freier Speicher in Byte, Schleifenlücke in Mikrosekunden."""
    temp_schwach: int
    temp_ausfall: int
    heap_schwach: int
    heap_ausfall: int
    luecke_schwach: int
    luecke_ausfall: int

    def __post_init__(self):
        if not (all(type(w) is int and 0 <= w < 2**32 for w in astuple(self))
                and self.temp_schwach < self.temp_ausfall <= MAX_TEMP
                and self.heap_schwach > self.heap_ausfall
                and self.luecke_schwach < self.luecke_ausfall):
            raise ValueError("Grenzen müssen ganzzahlig und geordnet sein, SCHWACH vor AUSFALL.")

    def befehl(self):
        return ("GRENZEN " + " ".join(map(str, astuple(self)))).encode("ascii")


# Vorläufige Werte für eine erste Erkundung, nicht aus Datenblättern abgeleitet.
# Die Rohwerte bleiben erhalten, mit `spur --grenzen` lassen sie sich neu einstufen.
ERKUNDUNG = Grenzen(500, 600, 65536, 16384, 20000, 200000)


def einstufen(temp_dc, heap, luecke_us, g):
    """Wie einstufen in Koerper.h: der schlechteste Wert zählt, eine fehlende Temperatur nicht."""
    if (temp_dc is not None and temp_dc >= g.temp_ausfall) or heap <= g.heap_ausfall \
            or luecke_us >= g.luecke_ausfall:
        return "AUSFALL"
    if (temp_dc is not None and temp_dc >= g.temp_schwach) or heap <= g.heap_schwach \
            or luecke_us >= g.luecke_schwach:
        return "SCHWACH"
    return "OK"


def lies_koerperzeile(zeile):
    """K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us,last"""
    teile = zeile.decode("ascii", "replace").split(",")
    if len(teile) != 9 or teile[0] != "K" or teile[2] not in ZUSTAENDE:
        raise ValueError(f"Unerwartete Körperzeile {zeile!r}.")
    takt, sofort, warnung, heap, luecke, last = (int(teile[i]) for i in (1, 3, 4, 6, 7, 8))
    temp = None if teile[5] == "-" else int(teile[5])
    return dict(takt=takt, temp_dc=temp, heap=heap, luecke_us=luecke, zustand=teile[2],
                sofort=sofort, vorwarnung=warnung, last=last)


def aufnehmen(port, regel, grenzen, intervall_ms, takte, ziel, last=None):
    """Körpermodus starten und jede Zeile mitschreiben. Gibt die Zahl der Takte zurück.

    last=(an_s, aus_s) lässt Kern 0 in diesem Rhythmus arbeiten. Der Knoten spürt das
    nur über seine Messwerte."""
    if not 100 <= intervall_ms < 2**32:
        raise ValueError("Das Intervall muss mindestens 100 ms betragen.")
    if last is not None and not all(type(s) is int and 0 <= s <= 3600 for s in last):
        raise ValueError("Last und Pause in ganzen Sekunden bis 3600.")
    if ziel.exists() or ziel.with_suffix(".json").exists():
        raise ValueError(f"{ziel} oder die zugehörige .json gibt es schon.")
    bereit(port, regel)
    anzahl = 0
    stille = 3 * intervall_ms / 1000 + 1
    try:
        port.write(grenzen.befehl() + b"\n")
        if (erhalten := antwort(port, nach_handschlag=True, frist=3.0)) != b"GRENZEN,ok":
            raise ValueError(f"Grenzen nicht übernommen, erhalten {erhalten!r}.")
        # Die Last vor dem Körpermodus starten, damit keine Körperzeile vor der Bestätigung kommt.
        if last is not None:
            port.write(f"LAST {last[0]} {last[1]}\n".encode("ascii"))
            if (erhalten := antwort(port, frist=3.0)) != b"LAST,ok":
                raise ValueError(f"Last nicht gestartet, erhalten {erhalten!r}.")
        port.write(f"KOERPER {intervall_ms}\n".encode("ascii"))
        if (erhalten := antwort(port, frist=3.0)) != b"KOERPER,an":
            raise ValueError(f"Körpermodus nicht gestartet, erhalten {erhalten!r}.")
        meta = dict(regel=regel, intervall_ms=intervall_ms, grenzen=asdict(grenzen),
                    last=None if last is None else list(last), beginn=time.strftime("%Y-%m-%d %H:%M"))
        with ziel.with_suffix(".json").open("x", encoding="utf-8") as datei:
            json.dump(meta, datei, ensure_ascii=False, indent=1)
        with ziel.open("x", encoding="utf-8", newline="") as datei:
            schreiber = csv.writer(datei)
            schreiber.writerow(KOPF)
            beginn = letzte = time.monotonic()
            while takte is None or anzahl < takte:
                zeile = port.readline().strip()
                if not zeile:
                    if time.monotonic() - letzte > stille:
                        raise ValueError(f"Seit {stille:.0f} s keine Körperzeile mehr.")
                    continue
                k = lies_koerperzeile(zeile)
                letzte = time.monotonic()
                k["zeit_ms"] = round((letzte - beginn) * 1000)
                k["temp_dc"] = "-" if k["temp_dc"] is None else k["temp_dc"]
                schreiber.writerow([k[feld] for feld in KOPF])
                datei.flush()
                anzahl += 1
    except KeyboardInterrupt:
        pass
    finally:
        port.write(b"STOP\n")
    return anzahl


def lies_aufnahme(pfad):
    meta = json.loads(pfad.with_suffix(".json").read_text(encoding="utf-8"))
    with pfad.open(encoding="utf-8", newline="") as datei:
        zeilen = csv.reader(datei, strict=True)
        kopf = next(zeilen, None)
        if kopf not in (list(KOPF), list(KOPF_ALT)):
            raise ValueError("Kopf der Aufnahme ist ungültig.")
        werte = []
        for nummer, zeile in enumerate(zeilen, start=2):
            if len(zeile) != len(kopf):
                raise ValueError(f"Zeile {nummer} ist unvollständig.")
            z = {"last": "0", **dict(zip(kopf, zeile))}  # alte Aufnahmen ohne Lastphase
            w = {f: int(z[f]) for f in KOPF if f not in ("temp_dc", "zustand")}
            w["temp_dc"] = None if z["temp_dc"] == "-" else int(z["temp_dc"])
            w["zustand"] = z["zustand"]
            werte.append(w)
    return meta, werte


def neu_einstufen(werte, g):
    return [(w["takt"], einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g)) for w in werte]


def pruefen(pfad):
    """Jede Einstufung und jede Entscheidung des Geräts mit Python nachrechnen."""
    meta, werte = lies_aufnahme(pfad)
    g = Grenzen(**meta["grenzen"])
    knoten = Knoten(REGELN[meta["regel"]]())
    for nummer, w in enumerate(werte, start=2):
        if einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g) != w["zustand"]:
            raise ValueError(f"Zeile {nummer}: Einstufung {w['zustand']} passt nicht zu den Rohwerten.")
        s = knoten.schritt(w["takt"], w["zustand"])
        if (int(s.sofort), int(s.vorwarnung)) != (w["sofort"], w["vorwarnung"]):
            raise ValueError(f"Zeile {nummer}: Entscheidung weicht von Python ab.")
    return meta, werte


def tausender(zahl):
    return f"{zahl:,.0f}".replace(",", ".")


def grad(zehntel):
    return f"{zehntel / 10:.1f}".replace(".", ",")


def bericht(meta, werte):
    temps = [w["temp_dc"] for w in werte if w["temp_dc"] is not None]
    heaps = [w["heap"] for w in werte]
    luecken = [w["luecke_us"] for w in werte]
    zeilen = [f"{len(werte)} Takte à {meta['intervall_ms']} ms, Regel {meta['regel']}, Beginn {meta['beginn']}."]
    if temps:
        zeilen.append(f"Chiptemperatur {grad(min(temps))} bis {grad(max(temps))} °C, "
                      f"Median {grad(statistics.median(temps))} °C"
                      + (f", {len(werte) - len(temps)} Takte ohne Messwert." if len(temps) < len(werte) else "."))
    if heaps:
        zeilen.append(f"Freier Speicher {tausender(min(heaps))} bis {tausender(max(heaps))} Byte.")
        zeilen.append(f"Schleifenlücke Median {tausender(statistics.median(luecken))} µs, "
                      f"größte {tausender(max(luecken))} µs.")
    for name, phase in (("Unter Last", 1), ("In Ruhe", 0)):
        teil = [w for w in werte if w["last"] == phase]
        t = [w["temp_dc"] for w in teil if w["temp_dc"] is not None]
        if t and any(w["last"] for w in werte):
            zeilen.append(f"{name} ({len(teil)} Takte): Temperatur Median {grad(statistics.median(t))} °C, "
                          f"höchstens {grad(max(t))} °C, Lücke Median "
                          f"{tausender(statistics.median(w['luecke_us'] for w in teil))} µs.")
    zustaende = {z: sum(w["zustand"] == z for w in werte) for z in ZUSTAENDE}
    zeilen.append("Zustände: " + ", ".join(f"{z} {n}" for z, n in zustaende.items())
                  + f". Vorwarnungen: {sum(w['vorwarnung'] for w in werte)}.")
    return "\n".join(zeilen)


def abbrechen(signum, frame):
    # SIGTERM wie Strg-C behandeln, damit STOP gesendet und die Datei geschlossen wird.
    raise KeyboardInterrupt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    a = sub.add_parser("aufnahme", help="Körpermodus starten und mitschreiben, Strg-C oder SIGTERM beendet")
    a.add_argument("datei", type=Path)
    a.add_argument("--port", required=True)
    a.add_argument("--regel", choices=list(REGELN), default="erbe")
    a.add_argument("--intervall-ms", type=int, default=1000)
    a.add_argument("--takte", type=int, help="Ohne Angabe bis zum Abbruch")
    a.add_argument("--grenzen", type=int, nargs=6, metavar="N", help="Temperatur schwach ausfall (Zehntelgrad), "
                   "Speicher schwach ausfall (Byte), Lücke schwach ausfall (µs)")
    a.add_argument("--last", type=int, nargs=2, metavar=("AN", "AUS"), help="Kern 0 arbeitet AN s, ruht AUS s")
    k = sub.add_parser("pruefen", help="Einstufungen und Entscheidungen nachrechnen")
    k.add_argument("datei", type=Path)
    s = sub.add_parser("spur", help="takt,zustand für versuch.py, wahlweise neu eingestuft")
    s.add_argument("datei", type=Path)
    s.add_argument("--grenzen", type=int, nargs=6, metavar="N")
    arg = p.parse_args()
    try:
        if arg.aktion == "aufnahme":
            try:
                import serial
            except ImportError:
                p.exit(2, "Für eine Aufnahme wird pyserial benötigt (in PlatformIO enthalten).\n")
            signal.signal(signal.SIGTERM, abbrechen)
            grenzen = Grenzen(*arg.grenzen) if arg.grenzen else ERKUNDUNG
            with serial.Serial(arg.port, 115200, timeout=0.6, write_timeout=2) as port:
                anzahl = aufnehmen(port, arg.regel, grenzen, arg.intervall_ms, arg.takte, arg.datei,
                                   tuple(arg.last) if arg.last else None)
            print(f"{anzahl} Takte aufgezeichnet in {arg.datei}.")
        elif arg.aktion == "pruefen":
            meta, werte = pruefen(arg.datei)
            print(bericht(meta, werte))
            print(f"Alle {len(werte)} Einstufungen und Entscheidungen des Geräts stimmen mit Python überein.")
        else:
            meta, werte = lies_aufnahme(arg.datei)
            g = Grenzen(*arg.grenzen) if arg.grenzen else Grenzen(**meta["grenzen"])
            w = csv.writer(sys.stdout, lineterminator="\n")
            w.writerow(("takt", "zustand"))
            w.writerows(neu_einstufen(werte, g))
    except (OSError, ValueError, KeyError, TypeError, csv.Error) as fehler:
        p.exit(2, f"Körpersignale: {fehler}\n")


if __name__ == "__main__":
    main()
