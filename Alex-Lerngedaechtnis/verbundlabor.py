"""Zwei Lernknoten, gezielte Transportfehler und ein offline lesbares Zustandsfenster."""
import argparse
import json
import multiprocessing
import queue
import socket
import time
import uuid
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from kern import Knoten, REGELN
from verbund import Messknoten, Paket, Zentrale, PAKET_BYTES
from versuch import beispielspur


def simulation():
    quelle = beispielspur()
    zeit = [0]
    hub = Zentrale([1, 2], antwortfrist=0.75, gueltigkeit=3)
    generation = 0
    knoten = {}
    protokoll = []
    statistik = Counter()
    zwischenspeicher = {}
    ereignisse = []

    def anbinden(nummer, lernen=None):
        nonlocal generation
        generation += 1
        sitzung = hub.anmelden(nummer, uuid.UUID(int=generation).bytes)
        def lese():
            index = zeit[0] - 1
            return index + 1 + (10000 if nummer == 2 else 0), quelle[(index + (3 if nummer == 2 else 0)) % len(quelle)]
        knoten[nummer] = Messknoten(nummer, sitzung, lernen or Knoten(REGELN["erbe"]()), lese)

    for nr in (1, 2):
        anbinden(nr)

    def empfange(daten, jetzt, hinweis):
        entscheid = hub.empfange(daten, jetzt)
        statistik[entscheid] += 1
        if entscheid != "ANGENOMMEN" or hinweis:
            ereignisse.append(dict(takt=zeit[0], text=hinweis or "Meldung geprüft", ergebnis=entscheid))

    for t in range(1, 61):
        zeit[0] = t
        if t == 22:
            anbinden(1, knoten[1].lernen)
            ereignisse.append(dict(takt=t, text="Knoten 1 erhält eine neue Sitzung. Sein Gedächtnis bleibt verfügbar.", ergebnis="ANMELDUNG"))
        if t == 30:
            hub = Zentrale([1, 2], antwortfrist=0.75, gueltigkeit=3)
            for nr in (1, 2):
                anbinden(nr, knoten[nr].lernen)
            ereignisse.append(dict(takt=t, text="Zentrale neu gestartet, beide Verbindungen neu zugeordnet.", ergebnis="ANMELDUNG"))

        antworten = {}
        fragen = {nr: hub.frage(nr, float(t)) for nr in (1, 2)}
        for nr, frage in fragen.items():
            statistik["FRAGEN"] += 1
            if nr == 1 and 13 <= t <= 18:
                statistik["VERLOREN"] += 1
                ereignisse.append(dict(takt=t, text="Abfrage an Knoten 1 geht verloren.", ergebnis="KANAL"))
                continue
            daten = knoten[nr].antwort(frage)
            statistik["ANTWORTEN"] += 1
            antworten[nr] = daten
            if (t, nr) in ((12, 1), (29, 2), (40, 1)):
                zwischenspeicher[t] = daten
            if (t, nr) == (40, 1):
                ereignisse.append(dict(takt=t, text="Antwort von Knoten 1 wird bis zur nächsten Runde verzögert.", ergebnis="KANAL"))
                continue
            if (t, nr) == (46, 2):
                continue
            empfange(daten, t + 0.1, "")
        if t == 7:
            empfange(antworten[1], t + 0.2, "Dieselbe Antwort kommt ein zweites Mal.")
        if t == 9:
            falsch = bytearray(antworten[2])
            falsch[20] ^= 1
            empfange(bytes(falsch), t + 0.2, "Eine Nachricht wurde auf dem Weg beschädigt.")
        if t == 22:
            empfange(zwischenspeicher[12], t + 0.2, "Eine Antwort aus der alten Sitzung trifft ein.")
        if t == 30:
            empfange(zwischenspeicher[29], t + 0.2, "Eine Antwort an die frühere Zentrale trifft ein.")
        if t == 41:
            empfange(zwischenspeicher[40], t + 0.2, "Eine Antwort aus der vergangenen Runde trifft ein.")
        if t == 46:
            empfange(antworten[2], t + 0.8, "Eine Antwort überschreitet die Empfangsfrist.")
        zellen = []
        for nr in (1, 2):
            g = knoten[nr].lernen.gedaechtnis
            sicht = hub.sicht(nr, t + 0.9)
            zellen.append(dict(nummer=nr, sitzung=knoten[nr].sitzung.hex(), sicht=asdict(sicht)))
            zellen[-1]["quelle"] = quelle[(t - 1 + (3 if nr == 2 else 0)) % len(quelle)]
            zellen[-1]["erbe"] = [[g.erbe[z][f] for f in ("OK", "SCHWACH", "AUSFALL")]
                                for z in ("OK", "SCHWACH", "AUSFALL")]
            zellen[-1]["erfahrung"] = [[g.gewichte[z][f] for f in ("OK", "SCHWACH", "AUSFALL")]
                                     for z in ("OK", "SCHWACH", "AUSFALL")]
        protokoll.append(dict(takt=t, knoten=zellen, ereignisse=[e for e in ereignisse if e["takt"] == t]))
    statistik["ZUSATZPAKETE"] = 4  # Duplikat, beschädigte Kopie und zwei Kopien aus alten Sitzungen.
    statistik["MODELL_NUTZBYTES"] = (statistik["FRAGEN"] + statistik["ANTWORTEN"]
                                    + statistik["ZUSATZPAKETE"]) * PAKET_BYTES
    return dict(version="verbund-1", herkunft="Deterministische Simulation", statistik=dict(statistik),
                verlauf=protokoll, ereignisse=ereignisse)


def udp_arbeiter(nummer, sitzung, bereit):
    """Ein separater Prozess, dessen Sensor bei jeder neuen Abfrage einen Messpunkt liefert."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(("127.0.0.1", 0))
        except OSError as fehler:
            bereit.put((nummer, None, str(fehler)))
            return
        sock.settimeout(5)
        bereit.put((nummer, sock.getsockname()[1], None))
        punkte = iter(enumerate(beispielspur(), 1))
        k = Messknoten(nummer, sitzung, Knoten(REGELN["erbe"]()), lambda: next(punkte))
        while k.runde < len(beispielspur()):
            try:
                daten, absender = sock.recvfrom(2048)
            except socket.timeout:
                return
            antwort = k.antwort(daten)
            if antwort is not None:
                sock.sendto(antwort, absender)


def udp_probe():
    kontext = multiprocessing.get_context("spawn")
    bereit = kontext.Queue()
    hub = Zentrale([1, 2], antwortfrist=1.5, gueltigkeit=3)
    prozesse = []
    referenzen = {nr: Knoten(REGELN["erbe"]()) for nr in (1, 2)}
    anzahl = 0
    beginn = time.monotonic()
    try:
        for nr in (1, 2):
            sitzung = hub.anmelden(nr)
            p = kontext.Process(target=udp_arbeiter, args=(nr, sitzung, bereit))
            p.start()
            prozesse.append(p)
        ports = {}
        for _ in range(2):
            nummer, port, fehler = bereit.get(timeout=10)
            if fehler:
                raise RuntimeError(f"Knoten {nummer} konnte seinen lokalen Port nicht öffnen: {fehler}")
            ports[nummer] = port
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.settimeout(2)
            for takt, zustand in enumerate(beispielspur(), 1):
                for nr in (1, 2):
                    daten = hub.frage(nr, time.monotonic())
                    sock.sendto(daten, ("127.0.0.1", ports[nr]))
                    antwort, adresse = sock.recvfrom(2048)
                    if adresse != ("127.0.0.1", ports[nr]):
                        raise RuntimeError("Antwort kam von einem anderen Testprozess.")
                    entscheid = hub.empfange(antwort, time.monotonic())
                    erwartet = referenzen[nr].schritt(takt, zustand)
                    sichtbar = hub.sicht(nr, time.monotonic())
                    if (entscheid != "ANGENOMMEN" or sichtbar.zustand != erwartet.zustand
                            or sichtbar.takt != takt or sichtbar.vorwarnung != erwartet.vorwarnung
                            or sichtbar.sofort != erwartet.sofort):
                        raise RuntimeError(f"Abweichung bei Knoten {nr}, Takt {takt}, {entscheid}.")
                    anzahl += 1
        for p in prozesse:
            p.join(timeout=5)
            if p.exitcode != 0:
                raise RuntimeError("Ein Testknoten endete nicht ordnungsgemäß.")
        return dict(herkunft="UDP auf 127.0.0.1, zwei separate Knotenprozesse",
                    passende_antworten=anzahl, erwartet=480,
                    protokoll_bytes=anzahl * 2 * PAKET_BYTES,
                    dauer_s=round(time.monotonic() - beginn, 3))
    finally:
        for p in prozesse:
            if p.is_alive():
                p.terminate()
            p.join(timeout=3)
        bereit.close()
        bereit.join_thread()


def bericht(daten):
    payload = json.dumps(daten, ensure_ascii=False).replace("<", "\\u003c")
    template = Path(__file__).with_name("verbund-vorlage.html").read_text(encoding="utf-8")
    return template.replace("/*DATEN*/", payload)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bericht", type=Path)
    p.add_argument("--json", type=Path)
    p.add_argument("--udp", action="store_true", help="Zwei lokale Prozesse über UDP prüfen")
    a = p.parse_args()
    if a.bericht and a.udp:
        p.error("Für den Zustandsbericht den Simulationslauf ohne --udp wählen.")
    try:
        daten = udp_probe() if a.udp else simulation()
    except (OSError, RuntimeError, queue.Empty) as fehler:
        p.exit(2, f"Verbundversuch abgebrochen: {fehler or 'Testknoten antwortete nicht rechtzeitig.'}\n")
    if a.bericht:
        a.bericht.write_text(bericht(daten), encoding="utf-8")
    if a.json:
        a.json.write_text(json.dumps(daten, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(daten.get("statistik", daten), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
