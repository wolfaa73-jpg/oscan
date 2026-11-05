"""Eine Messspur seriell an den Replay-Sketch senden und jede Antwort direkt prüfen."""
import argparse
import csv
import time
from pathlib import Path

from kern import Knoten, REGELN
from versuch import lies_spur, messpunkte


def bereit(port, regel):
    """NEUER_LAUF senden, bis die erwartete Variante antwortet. Das RAM des Knotens ist danach leer."""
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


def antwort(port, nach_handschlag=False, frist=0.0):
    """Nächste Antwortzeile. Mit frist wird länger gewartet, etwa auf einen Flashzugriff."""
    ende = time.monotonic() + frist
    zeile = port.readline().strip()
    while not zeile and time.monotonic() < ende:
        zeile = port.readline().strip()
    # Wiederholte NEUER_LAUF-Befehle bei langsamem Start werden alle beantwortet,
    # und zwar vor der ersten Antwort danach. Diese späten Bereitmeldungen überspringen.
    while nach_handschlag and zeile.startswith(b"BEREIT,"):
        zeile = port.readline().strip()
    return zeile


def spiele(port, knoten, punkte, nach_handschlag=True):
    """Messpunkte senden und jede Antwort mit der Entscheidung des Python-Knotens vergleichen."""
    for nummer, (t, z) in enumerate(punkte):
        s = knoten.schritt(t, z)
        erwartet = f"{t},{z},{int(s.sofort)},{int(s.vorwarnung)}".encode("ascii")
        port.write(f"{t},{z}\n".encode("ascii"))
        erhalten = antwort(port, nach_handschlag and nummer == 0)
        if erhalten != erwartet:
            raise ValueError(f"Takt {t}: erwartet {erwartet!r}, erhalten {erhalten!r}.")
    return len(punkte)


def vergleiche_board(port, spur, regel):
    bereit(port, regel)
    return spiele(port, Knoten(REGELN[regel]()), list(messpunkte(spur)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", required=True)
    p.add_argument("--regel", choices=list(REGELN), default="zeit")
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
