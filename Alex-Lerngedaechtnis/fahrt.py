"""Fahrtmodus des Knotens bedienen und sein Protokoll abholen. Unterwegs startet der Knoten selbst, schreibt
jeden Takt in seinen Flash (Format in esp32/Lernknoten/Fahrt.h) und behält die Vorhersage über Stromausfälle.

    fahrt.py stand  --port PORT            was das Gerät meldet
    fahrt.py an     --port PORT            Fahrtmodus merken, das Gerät startet neu und beginnt
    fahrt.py aus    --port PORT            Fahrtmodus beenden
    fahrt.py holen  --port PORT ziel.bin   Protokoll abholen (löscht nichts, überschreibt nichts)
    fahrt.py leeren --port PORT --ja       Protokoll und Stand auf dem Gerät löschen
    fahrt.py lesen  ziel.bin [ziel.csv]    Protokoll zusammenfassen, wahlweise als CSV schreiben

Jeder Befehl hält den Körpermodus an (STOP). Danach läuft der Fahrtmodus erst nach dem nächsten Einschalten
oder Zurücksetzen wieder. Am UICPAL-S3 startet das Öffnen des Anschlusses das Gerät nicht neu. Was seit dem
letzten Sichern kam, höchstens 30 Takte, steht nicht im Protokoll.
"""
import argparse
import csv
import struct
import sys
import time
from pathlib import Path

SATZ = struct.Struct("<IhBBhhhh")
V2_KENNUNG = b"OSCFAHRT"
V2_KOPF = V2_KENNUNG + struct.pack("<II", 2, 20)
V2_BYTES = 20
KOPF = ("takt", "temp_dc", "last", "ueberrascht", "vorwarnung", "sofort", "zustand", "neustart", "grund", "bei_null",
        "v10_cg", "v60_cg", "mittel_cg", "grenze_cg")
ZUSTAENDE = ("OK", "SCHWACH", "AUSFALL", "?")


def summe(daten, s=0):
    for b in daten:
        s = (s * 31 + b) & 0xFFFFFFFF
    return s


def alte_saetze(daten):
    """Die Sätze des Protokolls als dicts. Ohne Fehlerwert sind mittel_cg und grenze_cg None."""
    if len(daten) % SATZ.size:
        raise ValueError(f"Das Protokoll hat {len(daten)} Byte, das ist kein Vielfaches von {SATZ.size}.")
    for takt, temp, bits, grund, v10, v60, mittel, grenze in SATZ.iter_unpack(daten):
        ohne = bool(bits & 128)
        aus = dict(takt=takt, temp_dc=None if temp == -32768 else temp, last=bits & 1, ueberrascht=bits >> 1 & 1,
                   vorwarnung=bits >> 2 & 1, sofort=bits >> 3 & 1, zustand=ZUSTAENDE[bits >> 4 & 3],
                   neustart=bits >> 6 & 1, grund=(grund & 127) if bits & 64 else 0, bei_null=(grund >> 7) if bits & 64 else 0, v10_cg=v10, v60_cg=v60,
                   mittel_cg=None if ohne else mittel, grenze_cg=None if ohne else grenze)
        if not bits & 64 and grund:
            if not grund & 15 or not grund >> 4:
                raise ValueError("Ungültige Empfinden-Nibbles im Fahrtsatz")
            aus.update(gerade=(grund & 15)-8, woanders=(grund >> 4)-8)
        yield aus


def saetze(daten):
    """V1 unverändert oder explizit gekennzeichnete V2 mit eigenem Reizfeld."""
    if not daten.startswith(V2_KENNUNG):
        yield from alte_saetze(daten)
        return
    if daten[:len(V2_KOPF)] != V2_KOPF or (len(daten)-len(V2_KOPF)) % V2_BYTES:
        raise ValueError("Ungültiges Fahrt-V2-Format oder unvollständiger Satz")
    for pos in range(len(V2_KOPF),len(daten),V2_BYTES):
        raw=daten[pos:pos+V2_BYTES]
        reiz,r1,r2,bekannt=raw[16:]
        if r1 or r2 or bekannt not in (0,1) or reiz & ~63 or (not bekannt and reiz):
            raise ValueError("Ungültiges Reizfeld im Fahrt-V2-Satz")
        s=next(alte_saetze(raw[:16]))
        s.update(reiz=reiz if bekannt else None,
                 funk_sendefehler=bool(reiz & 32) if bekannt else None)
        yield s


def zeilen(port, sekunden):
    """Alles lesen, was in sekunden kommt. Im Fahrtmodus sendet das Gerät laufend, Stille gibt es dann nicht."""
    aus, ende = [], time.monotonic() + sekunden
    while time.monotonic() < ende:
        z = port.readline().strip()
        if z:
            aus.append(z)
    return aus


def warte(port, anfang, frist=5.0):
    ende = time.monotonic() + frist
    while time.monotonic() < ende:
        z = port.readline().strip()
        if z.startswith(anfang):
            return z
        if z == b"FEHLER":
            raise ValueError("Das Gerät meldet FEHLER.")
    raise ValueError(f"Keine Antwort {anfang.decode()} vom Gerät.")


def ruhig(port):
    """Nach dem Öffnen: Start abwarten, dann den Körpermodus anhalten."""
    start = zeilen(port, 4.0)
    port.write(b"STOP\n")
    warte(port, b"KOERPER,aus")
    return [z.decode("ascii", "replace") for z in start if z.startswith((b"NEUSTART,", b"FAHRT,", b"BEREIT"))]


def stand(port):
    port.write(b"FAHRTSTAND\n")
    teile = warte(port, b"FAHRT,").decode().split(",")
    gewollt, log, frei, takt, voll = map(int, teile[1:6])
    satzbytes = int(teile[6]) if len(teile) >= 7 else SATZ.size
    kopfbytes = int(teile[7]) if len(teile) >= 8 else 0
    if satzbytes not in (SATZ.size,V2_BYTES) or kopfbytes not in (0,len(V2_KOPF)) or log<kopfbytes or (log-kopfbytes)%satzbytes:
        raise ValueError("Ungültige Formatangabe im Fahrtstand")
    return dict(gewollt=bool(gewollt), saetze=(log-kopfbytes)//satzbytes, frei_bytes=frei,
                takt=takt, voll=bool(voll), satzbytes=satzbytes)


def holen(port):
    port.write(b"FAHRTLOG\n")
    n = int(warte(port, b"FAHRTLOG,").split(b",")[1])
    daten = bytearray()
    while True:
        z = port.readline().strip()
        if not z:
            raise ValueError(f"Das Protokoll brach nach {len(daten)} von {n} Byte ab.")
        if z.startswith(b"FAHRTLOG,ende,"):
            soll = int(z.split(b",")[2])
            break
        daten += bytes.fromhex(z.decode("ascii"))
    if len(daten) != n or summe(daten) != soll:
        raise ValueError(f"Das Protokoll kam beschädigt an ({len(daten)} von {n} Byte, Prüfsumme "
                         f"{'stimmt' if summe(daten) == soll else 'falsch'}).")
    return bytes(daten)


def bericht(liste):
    if not liste:
        return "Das Protokoll ist leer."
    temp = [s["temp_dc"] for s in liste if s["temp_dc"] is not None]
    out = [f"{len(liste)} Sätze, Takt {liste[0]['takt']} bis {liste[-1]['takt']}, das sind etwa "
           f"{len(liste) / 3600:.2f} Stunden mit Strom. Temperatur {min(temp) / 10:.0f} bis {max(temp) / 10:.0f} °C."]
    for nr, s in enumerate(liste):
        if s["neustart"]:
            out.append(f"  Neustart vor Satz {nr + 1} (Takt {s['takt']}), Grund {s['grund']}, "
                       f"Gedächtnis {'bei null begonnen' if s['bei_null'] else 'geladen'}, {s['temp_dc']} Zehntelgrad.")
    strecken, t = [], 0
    while t < len(liste):
        if liste[t]["ueberrascht"]:
            a = t
            while t < len(liste) and liste[t]["ueberrascht"]:
                t += 1
            mittel = [s["mittel_cg"] for s in liste[a:t]]
            strecken.append(f"Takt {liste[a]['takt']} ({t - a} Takte, "
                            f"{'kälter' if sum(mittel) < 0 else 'wärmer'} als erwartet, "
                            f"{liste[a]['temp_dc'] / 10:.0f} → {liste[t - 1]['temp_dc'] / 10:.0f} °C)")
        else:
            t += 1
    out.append(f"Überrascht in {len(strecken)} Strecken" + (": " + "; ".join(strecken[:60]) if strecken else "") + ".")
    if any("reiz" in s for s in liste):
        bekannt = [s for s in liste if s.get("reiz") is not None]
        out.append(f"Sende-API-Fehler in {sum(bool(s['funk_sendefehler']) for s in bekannt)} von {len(bekannt)} Sätzen mit Reizfeld; {len(liste)-len(bekannt)} Altsätze ohne Reizinformation.")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="aktion", required=True)
    for name in ("stand", "an", "aus", "holen", "leeren"):
        a = sub.add_parser(name)
        a.add_argument("--port", required=True)
        if name == "an":
            a.add_argument("--funk", action="store_true", help="Empfinden per ESP-NOW senden")
            a.add_argument("--empfinden", action="store_true", help="Empfinden im Fahrtmodus mitführen")
        if name == "holen":
            a.add_argument("ziel", type=Path)
        if name == "leeren":
            a.add_argument("--ja", action="store_true", help="wirklich löschen")
    a = sub.add_parser("lesen")
    a.add_argument("datei", type=Path)
    a.add_argument("csv", type=Path, nargs="?")
    arg = p.parse_args(argv)
    try:
        if arg.aktion == "lesen":
            liste = list(saetze(arg.datei.read_bytes()))
            if arg.csv:
                with arg.csv.open("x", encoding="utf-8", newline="") as datei:
                    aus = csv.writer(datei)
                    kopf = KOPF + (("gerade", "woanders") if any("gerade" in s for s in liste) else ())
                    if any("reiz" in s for s in liste): kopf += ("reiz", "funk_sendefehler")
                    aus.writerow(kopf)
                    aus.writerows(["-" if s.get(f) is None else s[f] for f in kopf] for s in liste)
            print(bericht(liste))
            return 0
        if arg.aktion == "holen" and arg.ziel.exists():
            raise ValueError(f"{arg.ziel} gibt es schon.")
        if arg.aktion == "leeren" and not arg.ja:
            raise ValueError("Zum Löschen --ja angeben, und vorher abholen.")
        import serial
        with serial.Serial(arg.port, 115200, timeout=0.6, write_timeout=2) as port:
            for z in ruhig(port):
                print("Gerät:", z)
            if arg.aktion == "an":
                if arg.empfinden or arg.funk:
                    port.write(b"EMPFINDEN 1\n")
                    warte(port, b"EMPFINDEN,ok,")
                if arg.funk:
                    port.write(b"FUNK 2\n")
                    warte(port, b"FUNK,ok")
                port.write(b"FAHRT 1\n")
                warte(port, b"FAHRT,an")
                print("Gerät:", warte(port, b"FAHRT,", frist=30.0).decode())
                return 0
            if arg.aktion == "aus":
                port.write(b"FAHRT 0\n")
                warte(port, b"FAHRT,aus")
            elif arg.aktion == "holen":
                beginn = time.monotonic()
                daten = holen(port)
                with arg.ziel.open("xb") as datei:
                    datei.write(daten)
                print(f"{len(daten)} Byte in {time.monotonic() - beginn:.0f} s nach {arg.ziel}.")
                print(bericht(list(saetze(daten))))
            elif arg.aktion == "leeren":
                port.write(b"FAHRTLEER\n")
                warte(port, b"FAHRT,leer", frist=20.0)
            s = stand(port)
            print(f"Fahrtmodus {'gemerkt' if s['gewollt'] else 'aus'}, {s['saetze']} Sätze im Protokoll, "
                  f"{s['frei_bytes'] // 1024} KB frei (reicht für etwa {max(0, s['frei_bytes'] - 65536) / s['satzbytes'] / 3600:.0f} h), "
                  f"Takt {s['takt']}" + (", Protokoll voll" if s["voll"] else "") + ".")
            if s["gewollt"] and arg.aktion != "an":
                print("Hinweis: Der Fahrtmodus ist gemerkt, läuft nach diesem Befehl aber erst wieder nach dem "
                      "nächsten Einschalten oder Zurücksetzen.")
    except (OSError, ValueError, KeyError) as fehler:
        p.exit(2, f"Fahrt: {fehler}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
