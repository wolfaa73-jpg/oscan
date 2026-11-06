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
from kern import Knoten, MAX_BLICK, REGELN, ZUSTAENDE

KOPF = ("takt", "zeit_ms", "temp_dc", "heap", "luecke_us", "zustand", "sofort", "vorwarnung", "reiz")
# Ältere Aufnahmen bleiben lesbar. Am 5. November hieß die letzte Spalte zuerst "last" und
# kannte nur die Last, die ersten Aufnahmen hatten sie noch gar nicht.
KOPF_LAST = KOPF[:-1] + ("last",)
KOPF_ALT = KOPF[:-1]
# Bits der Spalte reiz, wie reize() im Sketch.
LAST, LECK, BREMSE = 1, 2, 4
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
    """K,takt,zustand,sofort,vorwarnung,temp_dc,heap,luecke_us,reiz"""
    teile = zeile.decode("ascii", "replace").split(",")
    if len(teile) != 9 or teile[0] != "K" or teile[2] not in ZUSTAENDE:
        raise ValueError(f"Unerwartete Körperzeile {zeile!r}.")
    takt, sofort, warnung, heap, luecke, reiz = (int(teile[i]) for i in (1, 3, 4, 6, 7, 8))
    temp = None if teile[5] == "-" else int(teile[5])
    return dict(takt=takt, temp_dc=temp, heap=heap, luecke_us=luecke, zustand=teile[2],
                sofort=sofort, vorwarnung=warnung, reiz=reiz)


def exklusiv(port):
    """Belegt den seriellen Port für diesen Prozess allein, bis er geschlossen wird. Jedes weitere
    Öffnen scheitert dann mit EBUSY, auch das eines fremden Programms, das sonst über DTR/RTS das
    Gerät mitten in der Aufnahme zurücksetzen könnte. So geschah es am 5. November."""
    import fcntl
    import termios
    fcntl.ioctl(port.fileno(), termios.TIOCEXCL)


def nachlese(port, leer=4, hoechstens=8.0):
    """Was nach einer unerwarteten Zeile noch kommt, etwa die Startmeldungen nach einem Neustart.
    Liest, bis leer Lesefristen in Folge nichts brachten (am Gerät je 0,6 s), höchstens hoechstens s."""
    zeilen, stumm, ende = [], 0, time.monotonic() + hoechstens
    while stumm < leer and time.monotonic() < ende:
        zeile = port.readline().strip()
        if zeile:
            zeilen.append(zeile)
            stumm = 0
        else:
            stumm += 1
    return zeilen


def aufnehmen(port, regel, grenzen, intervall_ms, takte, ziel, last=None, blick=1, leck=None, bremse=None,
              fortsetzen=None, sichern_alle=0):
    """Körpermodus starten und jede Zeile mitschreiben. Gibt die Zahl der Takte zurück.

    last=(an_s, aus_s) lässt Kern 0 in diesem Rhythmus arbeiten. leck=(byte, boden, halten,
    pause), wahlweise mit flachem Boden und Muster, belegt Speicher, bremse=(start, schritt, bis,
    halten, pause) hält die Hauptschleife an, beide wie LECK und BREMSE im Sketch. Der Knoten spürt alle Reize nur über seine
    Messwerte. blick sind die Takte, die seine Vorwarnung vorausdenkt.

    Weiterlernen über Läufe: fortsetzen ist die vorige Aufnahme im selben Ordner. Das Gerät lädt
    dann seinen gesicherten Stand, statt bei null zu beginnen, und lässt einen Takt Lücke.
    sichern_alle lässt es jeden n-ten Takt selbst sichern und am Ende noch einmal. Takte, die nach
    STOP noch kommen, werden dafür mitgeschrieben, sonst passte der Endstand nicht zur Datei.

    Kommt statt einer Körperzeile etwas anderes, etwa das Startbanner nach einem Neustart,
    hebt <name>.abbruch.txt diese Zeile und alles danach auf, mit dem Grund des Neustarts."""
    if not 100 <= intervall_ms < 2**32:
        raise ValueError("Das Intervall muss mindestens 100 ms betragen.")
    if last is not None and not all(type(s) is int and 0 <= s <= 3600 for s in last):
        raise ValueError("Last und Pause in ganzen Sekunden bis 3600.")
    if type(blick) is not int or not 1 <= blick <= MAX_BLICK:
        raise ValueError(f"Der Blick muss 1 bis {MAX_BLICK} Takte betragen.")
    # Die Bereiche von Leck und Bremse prüft das Gerät, hier nur die Form.
    for name, werte, anzahl in (("Leck", leck, (4, 6)), ("Bremse", bremse, (5,))):
        if werte is not None and (len(werte) not in anzahl or not all(type(w) is int and 0 <= w < 2**32 for w in werte)):
            raise ValueError(f"{name} braucht {' oder '.join(map(str, anzahl))} ganze Zahlen ab null.")
    if type(sichern_alle) is not int or not 0 <= sichern_alle < 2**32:
        raise ValueError("Sichern alle n Takte braucht eine ganze Zahl ab null.")
    if fortsetzen is not None:
        # pruefen findet die vorige Aufnahme über ihren Namen neben dieser.
        if fortsetzen.parent.resolve() != ziel.parent.resolve():
            raise ValueError("Die fortgesetzte Aufnahme muss im selben Ordner liegen.")
        if lies_aufnahme(fortsetzen)[0]["regel"] != regel:
            raise ValueError("Fortgesetzt wird nur mit derselben Lernregel.")
    abbruch = ziel.with_name(ziel.stem + ".abbruch.txt")
    if ziel.exists() or ziel.with_suffix(".json").exists() or abbruch.exists():
        raise ValueError(f"{ziel} oder eine zugehörige .json oder .abbruch.txt gibt es schon.")
    bereit(port, regel)
    anzahl = 0
    stille = 3 * intervall_ms / 1000 + 1
    gestoppt = False
    try:
        port.write(grenzen.befehl() + b"\n")
        if (erhalten := antwort(port, nach_handschlag=True, frist=3.0)) != b"GRENZEN,ok":
            raise ValueError(f"Grenzen nicht übernommen, erhalten {erhalten!r}.")
        # Blick und Reize vor dem Körpermodus, damit keine Körperzeile vor einer Bestätigung kommt.
        befehle = [(f"BLICK {blick}", b"BLICK,ok", "Blick nicht übernommen")]
        if sichern_alle:
            befehle.append((f"SICHERN_ALLE {sichern_alle}", b"SICHERN_ALLE,ok", "Sichern nicht eingestellt"))
        if last is not None:
            befehle.append((f"LAST {last[0]} {last[1]}", b"LAST,ok", "Last nicht gestartet"))
        if leck is not None:
            befehle.append(("LECK " + " ".join(map(str, leck)), b"LECK,ok", "Leck nicht gestartet"))
        if bremse is not None:
            befehle.append(("BREMSE " + " ".join(map(str, bremse)), b"BREMSE,ok", "Bremse nicht gestartet"))
        if fortsetzen is not None:
            befehle.append(("LADEN", b"GELADEN", "Kein gesicherter Stand geladen"))
        befehle.append((f"KOERPER {intervall_ms}", b"KOERPER,an", "Körpermodus nicht gestartet"))
        for befehl, bestaetigung, fehler in befehle:
            port.write(befehl.encode("ascii") + b"\n")
            if (erhalten := antwort(port, frist=3.0)) != bestaetigung:
                raise ValueError(f"{fehler}, erhalten {erhalten!r}.")
        meta = dict(regel=regel, intervall_ms=intervall_ms, grenzen=asdict(grenzen), blick=blick,
                    last=None if last is None else list(last), leck=None if leck is None else list(leck),
                    bremse=None if bremse is None else list(bremse), beginn=time.strftime("%Y-%m-%d %H:%M"),
                    fortsetzung=None if fortsetzen is None else fortsetzen.name, sichern_alle=sichern_alle)
        with ziel.with_suffix(".json").open("x", encoding="utf-8") as datei:
            json.dump(meta, datei, ensure_ascii=False, indent=1)
        with ziel.open("x", encoding="utf-8", newline="") as datei:
            schreiber = csv.writer(datei)
            schreiber.writerow(KOPF)
            beginn = letzte = time.monotonic()

            def schreibe(zeile):
                nonlocal anzahl, letzte
                try:
                    k = lies_koerperzeile(zeile)
                except ValueError:
                    text = [z.decode("ascii", "replace") for z in [zeile] + nachlese(port)]
                    with abbruch.open("x", encoding="utf-8") as aus:
                        aus.write("\n".join(text) + "\n")
                    grund = [z for z in text if z.startswith(("rst:", "NEUSTART,"))]
                    raise ValueError(f"Unerwartete Zeile nach {anzahl} Takten: {text[0]!r}"
                                     + "".join(f", {z}" for z in grund) + f". Alles Weitere in {abbruch.name}.")
                letzte = time.monotonic()
                k["zeit_ms"] = round((letzte - beginn) * 1000)
                k["temp_dc"] = "-" if k["temp_dc"] is None else k["temp_dc"]
                schreiber.writerow([k[feld] for feld in KOPF])
                datei.flush()
                anzahl += 1

            try:
                while takte is None or anzahl < takte:
                    zeile = port.readline().strip()
                    if not zeile:
                        if time.monotonic() - letzte > stille:
                            raise ValueError(f"Seit {stille:.0f} s keine Körperzeile mehr.")
                        continue
                    schreibe(zeile)
            except KeyboardInterrupt:
                pass
            if sichern_alle:
                port.write(b"STOP\n")
                gestoppt = True
                while (zeile := port.readline().strip()) != b"KOERPER,aus":
                    if not zeile:
                        if time.monotonic() - letzte > stille:
                            raise ValueError("Nach STOP kam kein KOERPER,aus.")
                        continue
                    schreibe(zeile)
                port.write(b"SICHERN\n")
                if (erhalten := antwort(port, frist=3.0)) != b"GESICHERT":
                    raise ValueError(f"Endstand nicht gesichert, erhalten {erhalten!r}.")
    except KeyboardInterrupt:
        pass
    finally:
        if not gestoppt:
            port.write(b"STOP\n")
    return anzahl


def lies_aufnahme(pfad):
    meta = json.loads(pfad.with_suffix(".json").read_text(encoding="utf-8"))
    with pfad.open(encoding="utf-8", newline="") as datei:
        zeilen = csv.reader(datei, strict=True)
        kopf = next(zeilen, None)
        if kopf not in (list(KOPF), list(KOPF_LAST), list(KOPF_ALT)):
            raise ValueError("Kopf der Aufnahme ist ungültig.")
        werte = []
        for nummer, zeile in enumerate(zeilen, start=2):
            if len(zeile) != len(kopf):
                raise ValueError(f"Zeile {nummer} ist unvollständig.")
            z = dict(zip(kopf, zeile))
            # "last" kannte nur die Last, also Bit 1. Ganz alte Aufnahmen hatten keine Reize.
            z.setdefault("reiz", z.pop("last", "0"))
            w = {f: int(z[f]) for f in KOPF if f not in ("temp_dc", "zustand")}
            w["temp_dc"] = None if z["temp_dc"] == "-" else int(z["temp_dc"])
            w["zustand"] = z["zustand"]
            werte.append(w)
    return meta, werte


def neu_einstufen(werte, g):
    return [(w["takt"], einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g)) for w in werte]


def gelernt_bis(pfad, bis, kette=()):
    """Der Knoten einer Aufnahme nach ihrem Takt bis, samt allem, was sie fortsetzt. So stand er
    im Gerät, wenn es diesen Takt gesichert hat. bis muss ein Sicherungspunkt sein: ein Vielfaches
    von sichern_alle oder der letzte Takt."""
    if pfad.resolve() in kette:
        raise ValueError(f"{pfad.name} setzt sich selbst fort.")
    meta, werte = lies_aufnahme(pfad)
    alle = meta.get("sichern_alle") or 0
    if not werte or not alle or not (bis == werte[-1]["takt"] or werte[0]["takt"] <= bis < werte[-1]["takt"]
                                     and bis % alle == 0):
        raise ValueError(f"Takt {bis} ist kein Sicherungspunkt von {pfad.name}.")
    knoten = anfang(pfad, meta, werte, kette + (pfad.resolve(),))
    g = Grenzen(**meta["grenzen"])
    for w in werte:
        if w["takt"] > bis:
            break
        knoten.schritt(w["takt"], einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g))
    return knoten


def anfang(pfad, meta, werte, kette=()):
    """Der Knoten vor dem ersten Takt einer Aufnahme. Eine Fortsetzung beginnt mit dem Stand, den das
    Gerät geladen hat, zwei Takte vor ihrem ersten. Dazwischen liegt die Lücke der Pause."""
    knoten = Knoten(REGELN[meta["regel"]](), blick=meta.get("blick", 1))
    if not meta.get("fortsetzung"):
        return knoten
    if not werte or werte[0]["takt"] < 3:
        raise ValueError(f"{pfad.name} setzt fort, beginnt aber nicht nach einer Lücke.")
    vorher = gelernt_bis(pfad.with_name(meta["fortsetzung"]), werte[0]["takt"] - 2, kette)
    if type(vorher.gedaechtnis) is not type(knoten.gedaechtnis):
        raise ValueError("Die fortgesetzte Aufnahme hat eine andere Lernregel.")
    knoten.gedaechtnis, knoten.takt, knoten.zustand = vorher.gedaechtnis, vorher.takt, vorher.zustand
    return knoten


def pruefen(pfad):
    """Jede Einstufung und jede Entscheidung des Geräts mit Python nachrechnen."""
    meta, werte = lies_aufnahme(pfad)
    g = Grenzen(**meta["grenzen"])
    knoten = anfang(pfad, meta, werte)
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
    blick = f", Blick {meta['blick']} Takte" if meta.get("blick", 1) > 1 else ""
    zeilen = [f"{len(werte)} Takte à {meta['intervall_ms']} ms, Regel {meta['regel']}{blick}, Beginn {meta['beginn']}."]
    if meta.get("fortsetzung") and werte:
        zeilen.append(f"Setzt {meta['fortsetzung']} fort, mit dem Stand nach Takt {werte[0]['takt'] - 2}.")
    if meta.get("sichern_alle"):
        zeilen.append(f"Das Gerät sicherte jeden {meta['sichern_alle']}. Takt und am Ende.")
    if temps:
        zeilen.append(f"Chiptemperatur {grad(min(temps))} bis {grad(max(temps))} °C, "
                      f"Median {grad(statistics.median(temps))} °C"
                      + (f", {len(werte) - len(temps)} Takte ohne Messwert." if len(temps) < len(werte) else "."))
    if heaps:
        zeilen.append(f"Freier Speicher {tausender(min(heaps))} bis {tausender(max(heaps))} Byte.")
        zeilen.append(f"Schleifenlücke Median {tausender(statistics.median(luecken))} µs, "
                      f"größte {tausender(max(luecken))} µs.")
    if any(w["reiz"] for w in werte):
        for name, teil in (("Unter Last", [w for w in werte if w["reiz"] & LAST]),
                           ("Mit Leck", [w for w in werte if w["reiz"] & LECK]),
                           ("Mit Bremse", [w for w in werte if w["reiz"] & BREMSE]),
                           ("In Ruhe", [w for w in werte if not w["reiz"]])):
            t = [w["temp_dc"] for w in teil if w["temp_dc"] is not None]
            if not teil:
                continue
            zeilen.append(f"{name} ({len(teil)} Takte): "
                          + (f"Temperatur Median {grad(statistics.median(t))} °C, höchstens {grad(max(t))} °C, "
                             if t else "")
                          + f"Speicher ab {tausender(min(w['heap'] for w in teil))} Byte, Lücke Median "
                          f"{tausender(statistics.median(w['luecke_us'] for w in teil))} µs, größte "
                          f"{tausender(max(w['luecke_us'] for w in teil))} µs.")
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
    a.add_argument("--blick", type=int, default=1, help=f"Takte, die die Vorwarnung vorausdenkt, 1 bis {MAX_BLICK}")
    a.add_argument("--leck", type=int, nargs="+", metavar="N",
                   help="Speicherleck BYTE BODEN HALTEN PAUSE [FLACH MUSTER]: BYTE je Takt, bis nur noch BODEN Byte "
                        "frei sind, HALTEN Takte am Boden, dann PAUSE Takte frei. Durchgänge, deren Bit im MUSTER "
                        "gesetzt ist, halten schon bei FLACH Byte an")
    a.add_argument("--bremse", type=int, nargs=5, metavar=("START", "SCHRITT", "BIS", "HALTEN", "PAUSE"),
                   help="Hauptschleife steht je Takt START, START+SCHRITT … bis BIS ms still, HALTEN Takte bei BIS, "
                        "dann PAUSE Takte nicht")
    a.add_argument("--fortsetzen", type=Path, metavar="VORIGE",
                   help="Mit dem gesicherten Stand weiterlernen, den die vorige Aufnahme im selben Ordner hinterließ")
    a.add_argument("--sichern-alle", type=int, default=0, metavar="N",
                   help="Das Gerät sichert jeden N-ten Takt und am Ende, damit eine spätere Aufnahme fortsetzen kann")
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
                exklusiv(port)
                anzahl = aufnehmen(port, arg.regel, grenzen, arg.intervall_ms, arg.takte, arg.datei,
                                   tuple(arg.last) if arg.last else None, arg.blick,
                                   tuple(arg.leck) if arg.leck else None, tuple(arg.bremse) if arg.bremse else None,
                                   arg.fortsetzen, arg.sichern_alle)
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
