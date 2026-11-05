"""TCP-Erreichbarkeit eines eigenen Testdienstes aufzeichnen und für das Labor einlesen."""
import argparse
import csv
import errno
import ipaddress
import math
import socket
import sys
import time
from pathlib import Path

from kern import MAX_TAKT

KOPF = ("takt", "start_ms", "dauer_ms", "ergebnis")
AUSFAELLE = {errno.ECONNREFUSED: "ABGELEHNT", errno.ETIMEDOUT: "TIMEOUT",
            errno.ENETUNREACH: "NETZ_UNERREICHBAR", errno.EHOSTUNREACH: "HOST_UNERREICHBAR"}


def probe(ip, port, timeout):
    start = time.monotonic_ns()
    ergebnis = "VERBUNDEN"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            sock.connect((ip, port))
    except socket.timeout:
        ergebnis = "TIMEOUT"
    except OSError as fehler:
        if fehler.errno not in AUSFAELLE:
            raise
        ergebnis = AUSFAELLE[fehler.errno]
    return (time.monotonic_ns() - start) / 1e6, ergebnis


def aufzeichnen(datei, ip, port, anzahl, intervall_ms, timeout_ms):
    if not (1 <= port <= 65535 and 1 <= anzahl <= MAX_TAKT and 0 < timeout_ms < intervall_ms):
        raise ValueError("Port, Anzahl oder Zeitbereich ungültig. Timeout muss kürzer als ein Takt sein.")
    with datei.open("x", encoding="utf-8", newline="") as log:
        w = csv.writer(log)
        w.writerow(KOPF)
        beginn = time.monotonic_ns()
        dauer = intervall_ms * 1_000_000
        takt = 1
        while takt <= anzahl:
            ziel = beginn + (takt - 1) * dauer
            time.sleep(max(0, (ziel - time.monotonic_ns()) / 1e9))
            jetzt = time.monotonic_ns()
            # Verpasste Zeitfenster nach Suspend oder Last als Lücken erhalten.
            takt = max(takt, (jetzt - beginn) // dauer + 1)
            if takt > anzahl:
                break
            ms, ergebnis = probe(ip, port, timeout_ms / 1000)
            w.writerow((takt, f"{(jetzt - beginn) / 1e6:.3f}", f"{ms:.6f}", ergebnis))
            log.flush()
            takt += 1


def klassifizieren(rohdatei, grenze):
    if not math.isfinite(grenze) or grenze <= 0:
        raise ValueError("Positive, endliche Schwelle in Millisekunden erwartet.")
    spur = []
    with rohdatei.open(encoding="utf-8-sig", newline="") as roh:
        r = csv.reader(roh, strict=True)
        if next(r, None) != list(KOPF):
            raise ValueError("Rohdatenkopf ist ungültig.")
        letzter_takt, letzter_start = 0, -1.0
        for nummer, zeile in enumerate(r, start=2):
            if len(zeile) != 4:
                raise ValueError(f"Rohdatenzeile {nummer} ist unvollständig.")
            t, start, ms, ergebnis = zeile
            t, start, ms = int(t), float(start), float(ms)
            if not (letzter_takt < t <= MAX_TAKT and math.isfinite(start) and start > letzter_start
                    and start >= 0 and math.isfinite(ms) and ms >= 0):
                raise ValueError(f"Zeitwerte in Rohdatenzeile {nummer} sind ungültig.")
            if ergebnis == "VERBUNDEN":
                zustand = "SCHWACH" if ms >= grenze else "OK"
            elif ergebnis in AUSFAELLE.values():
                zustand = "AUSFALL"
            else:
                raise ValueError(f"Unbekanntes Messergebnis in Zeile {nummer}.")
            spur.append((t, zustand))
            letzter_takt, letzter_start = t, start
    if not spur:
        raise ValueError("Die Rohdatei enthält keine abgeschlossene Messung.")
    return spur


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    a = sub.add_parser("aufnahme")
    a.add_argument("datei", type=Path)
    a.add_argument("--ip", type=ipaddress.IPv4Address, required=True)
    a.add_argument("--port", type=int, required=True)
    a.add_argument("--takte", type=int, default=240)
    a.add_argument("--intervall-ms", type=int, default=1000)
    a.add_argument("--timeout-ms", type=int, default=400)
    k = sub.add_parser("spur")
    k.add_argument("rohdatei", type=Path)
    k.add_argument("--schwach-ms", type=float, required=True)
    arg = p.parse_args()
    try:
        if arg.aktion == "aufnahme":
            aufzeichnen(arg.datei, str(arg.ip), arg.port, arg.takte, arg.intervall_ms, arg.timeout_ms)
        else:
            spur = klassifizieren(arg.rohdatei, arg.schwach_ms)
            w = csv.writer(sys.stdout, lineterminator="\n")
            w.writerow(("takt", "zustand"))
            w.writerows(spur)
    except (ValueError, OSError, csv.Error) as fehler:
        p.exit(2, f"Messung abgebrochen: {fehler}\n")


if __name__ == "__main__":
    main()
