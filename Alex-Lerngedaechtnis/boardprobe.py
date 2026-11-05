"""Eine Messspur seriell an den Replay-Sketch senden und jede Antwort direkt prüfen."""
import argparse
import csv
import time
from pathlib import Path

from kern import Gedaechtnis, Kontextgedaechtnis, Knoten
from versuch import lies_spur, messpunkte


def vergleiche_board(port, spur, regel):
    erwartung = ("BEREIT," + regel.upper()).encode("ascii")
    start = time.monotonic()
    while time.monotonic() - start < 12:
        port.write(b"NEUER_LAUF\n")
        frist = time.monotonic() + 1.2
        while time.monotonic() < frist:
            zeile = port.readline().strip()
            if zeile.startswith(b"BEREIT,"):
                if zeile != erwartung:
                    raise ValueError(f"Falsche Variante: {zeile!r}, erwartet {erwartung!r}.")
                break
        else:
            continue
        break
    else:
        raise ValueError("Keine Bereitschaftsantwort vom Replay-Sketch.")

    k = Knoten(Kontextgedaechtnis() if regel == "kontext" else Gedaechtnis())
    for t, z in messpunkte(spur):
        s = k.schritt(t, z)
        erwartet = f"{t},{z},{int(s.sofort)},{int(s.vorwarnung)}".encode("ascii")
        port.write(f"{t},{z}\n".encode("ascii"))
        antwort = port.readline().strip()
        if antwort != erwartet:
            raise ValueError(f"Takt {t}: erwartet {erwartet!r}, erhalten {antwort!r}.")
    return len(spur)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True)
    p.add_argument("--regel", choices=["kontext", "zeit"], default="zeit")
    p.add_argument("--spur", type=Path, default=Path(__file__).parent / "beispiele/demo.csv")
    a = p.parse_args()
    try:
        import serial
    except ImportError:
        p.exit(2, "Für einen Boardlauf wird pyserial benötigt (in PlatformIO enthalten).\n")
    try:
        spur = lies_spur(a.spur, minimum=1)
        with serial.Serial(a.port, 115200, timeout=0.6, write_timeout=2) as port:
            anzahl = vergleiche_board(port, spur, a.regel)
        print(f"{anzahl} von {anzahl} Antworten passen zur Referenz ({a.regel}).")
    except (OSError, csv.Error, ValueError) as fehler:
        p.exit(2, f"Boardprüfung abgebrochen: {fehler}\n")


if __name__ == "__main__":
    main()
