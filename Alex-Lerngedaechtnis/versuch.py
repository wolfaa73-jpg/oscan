"""Ein lokaler Versuch mit einem festen Reflex und einer lernenden Übergangstabelle."""
import argparse
import csv
import struct
from dataclasses import dataclass
from pathlib import Path
from kern import Gedaechtnis, Kontextgedaechtnis, Knoten, MAX_TAKT, ZUSTAENDE


# Feste Bedeutung der Token. Jede Nachricht enthält Takt (uint32) und Token (uint8).
TOKEN = {"OK": 1, "SCHWACH": 2, "AUSFALL": 3, "VORWARNUNG": 4}
RAHMEN = struct.Struct(">IB")


def beispielspur():
    # Alle sechs Takte wird das Signal schwach. Nach 20 solchen Folgen ändert
    # sich der Zusammenhang. Zwei unerwartete Ausfälle treten nach OK auf.
    spur = []
    for block in range(40):
        folge = "AUSFALL" if block < 20 and block % 5 != 4 else "OK"
        spontan = "AUSFALL" if block in (12, 32) else "OK"
        spur.extend(["OK", spontan, "OK", "SCHWACH", folge, "OK"])
    return spur


def lies_spur(pfad, minimum=2):
    with pfad.open(encoding="utf-8-sig", newline="") as datei:
        zeilen = csv.reader(datei, strict=True)
        kopf = next(zeilen, None)
        if kopf not in (["zustand"], ["takt", "zustand"]):
            raise ValueError("Erste Zeile muss 'zustand' oder 'takt,zustand' lauten.")
        spur = []
        letzter_takt = 0
        for nummer, zeile in enumerate(zeilen, start=2):
            if len(zeile) != len(kopf) or zeile[-1] not in ZUSTAENDE:
                raise ValueError(f"Zeile {nummer}: ungültige Spalten oder Zustand.")
            if len(kopf) == 1:
                spur.append(zeile[0])
                continue
            if not zeile[0].isascii() or not zeile[0].isdecimal():
                raise ValueError(f"Zeile {nummer}: ungültiger Takt.")
            takt = int(zeile[0])
            if not letzter_takt < takt <= MAX_TAKT:
                raise ValueError(f"Zeile {nummer}: Takt doppelt, rückläufig oder außerhalb des Bereichs.")
            spur.append((takt, zeile[1]))
            letzter_takt = takt
    if len(spur) < minimum:
        raise ValueError(f"Die Spur braucht mindestens {minimum} Beobachtung(en).")
    return spur


@dataclass
class Bilanz:
    name: str
    nachrichten: int = 0
    nutzbytes: int = 0
    sofortmeldungen: int = 0
    treffer: int = 0
    fehlalarme: int = 0
    ohne_vorwarnung: int = 0
    offen: int = 0
    beginn_unbekannt: int = 0
    fehlende_takte: int = 0

    def sende(self, takt, token):
        paket = RAHMEN.pack(takt, TOKEN[token])
        self.nachrichten += 1
        self.nutzbytes += len(paket)


def messpunkte(spur):
    for nummer, wert in enumerate(spur, start=1):
        yield (nummer, wert) if isinstance(wert, str) else wert


def durchlauf(spur, name, gedaechtnis=None, *, alle_senden=False, feste_warnregel=False, beobachter=None):
    bilanz = Bilanz(name)
    knoten = Knoten(gedaechtnis, alle_senden=alle_senden, feste_warnregel=feste_warnregel)
    letzter = None
    for takt, zustand in messpunkte(spur):
        schritt = knoten.schritt(takt, zustand)
        anschluss = letzter is not None and takt == letzter.takt + 1
        if letzter is not None:
            bilanz.fehlende_takte += takt - letzter.takt - 1
            if letzter.vorwarnung:
                if not anschluss:
                    bilanz.offen += 1
                elif schritt.sofort:
                    bilanz.treffer += 1
                else:
                    bilanz.fehlalarme += 1
        if schritt.sofort:
            bilanz.sofortmeldungen += 1
            if not anschluss:
                bilanz.beginn_unbekannt += 1
            elif not letzter.vorwarnung:
                bilanz.ohne_vorwarnung += 1
        if schritt.statusmeldung:
            bilanz.sende(takt, zustand)
        if schritt.vorwarnung:
            bilanz.sende(takt, "VORWARNUNG")
        if beobachter is not None:
            beobachter(takt, zustand, schritt.anteil, schritt.beleg, schritt.vorwarnung)
        letzter = schritt
    if letzter is not None and letzter.vorwarnung:
        bilanz.offen += 1
    return bilanz


def vergleiche(spur, beobachter=None):
    return [
        durchlauf(spur, "Jeden Takt senden", alle_senden=True),
        durchlauf(spur, "Nur Zustandswechsel"),
        durchlauf(spur, "Bei SCHWACH immer warnen", feste_warnregel=True),
        durchlauf(spur, "Lernen ohne Verblassen", Gedaechtnis(None)),
        durchlauf(spur, "Lernen mit Verblassen", Gedaechtnis(), beobachter=beobachter),
        durchlauf(spur, "Verblassen je Kontext", Kontextgedaechtnis()),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spur", type=Path, help="CSV mit zustand oder takt,zustand")
    parser.add_argument("--details", action="store_true", help="Schätzung für jeden Takt ausgeben")
    args = parser.parse_args()
    try:
        spur = lies_spur(args.spur) if args.spur else beispielspur()
    except (OSError, ValueError, csv.Error) as fehler:
        parser.exit(2, f"Spur unlesbar: {fehler}\n")

    print(f"{len(spur)} Beobachtungen | Vorhersagehorizont: ein Takt | Nachricht: {RAHMEN.size} Byte")
    if not args.spur:
        print("Demo: Ab Takt 121 hat SCHWACH seine frühere Bedeutung als Vorbote verloren.")
    print("Verlauf des verblassenden Gedächtnisses:")
    if args.details:
        print("  Takt Zustand    Ausfallanteil   Beleg   Warnung")

    letzter_entscheid = {}

    def zeige(takt, zustand, anteil, beleg, warnung):
        if args.details:
            print(f"  {takt:4} {zustand:8} {anteil:11.0%} {beleg:8.2f}   {'ja' if warnung else 'nein'}")
        elif warnung != letzter_entscheid.get(zustand, False):
            entscheid = "warnt" if warnung else "warnt nicht mehr"
            print(f"  Takt {takt}: Der Knoten {entscheid} bei {zustand} "
                  f"(Ausfallanteil {anteil:.0%}, gewichtete Beobachtungen {beleg:.1f}).")
        letzter_entscheid[zustand] = warnung

    bilanzen = vergleiche(spur, zeige)
    print("\nVerfahren                 Pakete   Byte   Sofort   Vorher   Fehlalarm   Ohne Vorw.   Offen")
    for b in bilanzen:
        print(f"{b.name:24} {b.nachrichten:7} {b.nutzbytes:6} {b.sofortmeldungen:8} "
              f"{b.treffer:8} {b.fehlalarme:11} {b.ohne_vorwarnung:12} {b.offen:7}")
    print(f"Fehlende Takte zwischen Messungen: {bilanzen[0].fehlende_takte}. "
          f"Ausfallmeldungen mit unbekanntem Beginn: {bilanzen[0].beginn_unbekannt}.")
    print("Sofort = bei erstmals beobachtetem Ausfall gemeldet. Vorher = einen Takt zuvor richtig gewarnt.")


if __name__ == "__main__":
    main()
