"""Wiederanlauf am Gerät prüfen: erster Teil und SICHERN, Strom trennen, LADEN und zweiter Teil."""
import argparse
import csv
import random
from pathlib import Path

from boardprobe import antwort, bereit, spiele
from kern import Knoten, REGELN
from versuch import lies_spur, messpunkte

# Sichern und Laden greifen auf den Flash zu. Der erste Eintrag nach dem
# Aufspielen kann dabei deutlich länger brauchen als eine Messzeile.
FLASHFRIST = 3.0


def sichern(port, spur, regel, grenze):
    bereit(port, regel)
    spiele(port, Knoten(REGELN[regel]()), list(messpunkte(spur))[:grenze])
    port.write(b"SICHERN\n")
    erhalten = antwort(port, frist=FLASHFRIST)
    if erhalten != b"GESICHERT":
        raise ValueError(f"Das Gerät hat den Stand nicht gesichert, erhalten {erhalten!r}.")


def laden(port, spur, regel, grenze):
    punkte = list(messpunkte(spur))
    k = Knoten(REGELN[regel]())
    for t, z in punkte[:grenze]:
        k.schritt(t, z)
    bereit(port, regel)
    port.write(b"LADEN\n")
    erhalten = antwort(port, nach_handschlag=True, frist=FLASHFRIST)
    if erhalten != b"GELADEN":
        raise ValueError(f"Kein gesicherter Stand geladen, erhalten {erhalten!r}.")
    # Der Grenztakt muss abgewiesen werden, der nächste muss passen. Erst beides
    # zusammen zeigt, dass der geladene Stand genau an der Grenze endet.
    t, z = punkte[grenze - 1]
    port.write(f"{t},{z}\n".encode("ascii"))
    if antwort(port) != b"FEHLER":
        raise ValueError(f"Der geladene Stand endet vor Takt {t}.")
    return spiele(port, k, punkte[grenze:], nach_handschlag=False)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("teil", choices=("sichern", "laden"))
    p.add_argument("--port", required=True)
    p.add_argument("--regel", choices=list(REGELN), default="zeit")
    p.add_argument("--spur", type=Path, default=Path(__file__).parent / "beispiele/demo.csv")
    p.add_argument("--grenze", type=int, help="Messpunkte vor dem Sichern. Beim Sichern sonst zufällig.")
    a = p.parse_args()
    try:
        import serial
    except ImportError:
        p.exit(2, "Für einen Boardlauf wird pyserial benötigt (in PlatformIO enthalten).\n")
    try:
        spur = lies_spur(a.spur)
        grenze = a.grenze
        if grenze is None and a.teil == "sichern":
            # Ein zufälliger Grenztakt unterscheidet den neuen Stand von einem älteren im NVS.
            grenze = random.randint(len(spur) // 6, len(spur) * 5 // 6)
        if grenze is None:
            raise ValueError("Zum Laden wird der Grenztakt vom Sichern gebraucht (--grenze).")
        if not 1 <= grenze < len(spur):
            raise ValueError("Die Grenze muss innerhalb der Spur liegen.")
        with serial.Serial(a.port, 115200, timeout=0.6, write_timeout=2) as port:
            if a.teil == "sichern":
                sichern(port, spur, a.regel, grenze)
                print(f"{grenze} Antworten passen, Stand gesichert. Jetzt Strom trennen, wieder einschalten und:")
                print(f"  python3 wiederanlauf.py laden --port {a.port} --regel {a.regel} --grenze {grenze}")
            else:
                anzahl = laden(port, spur, a.regel, grenze)
                print(f"Stand geladen, endet genau an der Grenze. {anzahl} von {anzahl} weiteren Antworten "
                      f"passen zum durchgehenden Lauf ({a.regel}).")
    except (OSError, csv.Error, ValueError) as fehler:
        p.exit(2, f"Wiederanlauf abgebrochen: {fehler}\n")


if __name__ == "__main__":
    main()
