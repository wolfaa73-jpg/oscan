"""Getrennte synthetische Körpersignale und reproduzierbare Vergleiche (Rechenaufgabe 2).

Nur Standardbibliothek, keine Gerätezugriffe. Definitionen: SIGNAL-LABOR.md.
"""
import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from vokabular import (GROBWOERTER, GROBERBE, SIGNALE, Wortgedaechtnis,
                       binnen_vor, grob, kritisch, phasen, warnungen)

VERSION = 1
FAMILIEN = ("bloecke", "zufallsmaske", "seltene_ausnahme", "ueberlagerung")
SAETZE = ("entwicklung", "kontrolle")
VERFAHREN = ("Feste Regel", "Festes Erbe", "Startwert", "Ohne Erbe",
             "Letzter Durchgang", "Immer warnen")
ZAEHLER = ("takte", "auswertbar", "warntakte", "treffertakte", "zieltakte",
           "phasen", "vorgewarnt", "verpasst", "verdeckt")


@dataclass(frozen=True)
class Einstellungen:
    takte: int = 960
    horizont: int = 30
    waerme_p: float = 0.38
    ausnahme_p: float = 0.05
    schwelle: float = 0.6

    def __post_init__(self):
        for name, unten, oben in (("takte", 2, 1000000), ("horizont", 1, 600)):
            wert = getattr(self, name)
            if type(wert) is not int or not unten <= wert <= oben:
                raise ValueError(f"{name} muss ganzzahlig zwischen {unten} und {oben} liegen.")
        if self.takte <= self.horizont:
            raise ValueError("Die Spur muss länger als der Horizont sein.")
        for name in ("waerme_p", "ausnahme_p", "schwelle"):
            wert = getattr(self, name)
            if not math.isfinite(wert) or not 0 <= wert <= 1:
                raise ValueError(f"{name} muss endlich und zwischen 0 und 1 liegen.")


def zufall(satz, familie, seed, signal):
    # Anders als verschobene Zahlenintervalle überschneiden sich die Namensräume
    # auch bei sehr großen Reihen nicht. Keine prozessabhängige hash()-Funktion.
    text = json.dumps([VERSION, satz, familie, seed, signal], separators=(",", ":"))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest(), "big"))


def generiere(familie, seed, satz="entwicklung", einstellungen=None):
    """Eine Liste eigener Stufen je Signal; versteckte Generatorzustände bleiben hier.

    waerme_p ist die Chance eines warmen Durchgangs auf kritisch, nicht die
    Trefferquote beliebiger warmer Takte. Zwischen Durchgängen liegt > Horizont OK.
    """
    e = einstellungen or Einstellungen()
    if familie not in FAMILIEN or satz not in SAETZE or type(seed) is not int or seed < 0:
        raise ValueError("Unbekannte Familie/Satz oder ungültiger Startwert.")
    spuren = {}
    for signal, hoch, kritisch_wort in SIGNALE:
        rng = zufall(satz, familie, seed, signal)
        spur = ["OK"] * rng.randint(1, 12)
        tief = bool(rng.getrandbits(1))
        rest = rng.randint(3, 8)
        while len(spur) < e.takte:
            # Ziehungen bleiben je Zyklus in derselben Reihenfolge, auch bei p=0/1.
            maske, ausnahme = rng.random(), rng.random()
            hoch_dauer = rng.randint(1, min(12, e.horizont))
            kritisch_dauer = rng.randint(2, 8)
            pause = e.horizont + rng.randint(2, 12)
            neue_blocklaenge = rng.randint(3, 8)
            if signal == "temperatur":
                ausfall = maske < e.waerme_p
            elif familie == "zufallsmaske":
                ausfall = maske < 0.5
            elif familie == "seltene_ausnahme":
                ausfall = ausnahme >= e.ausnahme_p
            else:
                ausfall = tief ^ (ausnahme < e.ausnahme_p)
            if familie == "ueberlagerung" and signal == "temperatur":
                # Lange warme Phasen haben bei gleicher Schwere Vorrang vor
                # Speicher/Schleife. Die übrigen Signale behalten ihren eigenen Takt.
                hoch_dauer = rng.randint(max(1, e.horizont // 2), e.horizont)
            spur.extend([hoch] * hoch_dauer)
            if ausfall:
                spur.extend([kritisch_wort] * kritisch_dauer)
            spur.extend(["OK"] * pause)
            rest -= 1
            if rest == 0:
                tief = not tief
                rest = neue_blocklaenge
        spuren[signal] = spur[:e.takte]
    return [{signal: spur[t] for signal, spur in spuren.items()} for t in range(e.takte)]


def schwerstes(stufen):
    """Gleicher Vorrang wie koerperwort, aber bereits eingestufte Signale als Eingang."""
    return [next((zeile[signal] for schwere in ("AUSFALL", "SCHWACH")
                  for signal, _, _ in SIGNALE if grob(zeile[signal]) == schwere), "OK")
            for zeile in stufen]


def letzter_durchgang(woerter):
    """Warne bei SCHWACH, wenn der letzte abgeschlossene Nicht-OK-Lauf kritisch war.

    Noch kein abgeschlossener Lauf: keine Warnung. Abschluss erst beim beobachteten
    OK; der laufende Ausgang und Generator-Grenzen werden nicht vorausgelesen.
    """
    aktiv = hatte_ausfall = letzter_ausfall = False
    ergebnis = []
    for wort in woerter:
        z = grob(wort)
        if z == "OK":
            if aktiv:
                letzter_ausfall = hatte_ausfall
            aktiv = hatte_ausfall = False
        else:
            aktiv = True
            hatte_ausfall |= z == "AUSFALL"
        ergebnis.append(z == "SCHWACH" and letzter_ausfall)
    return ergebnis


class SchnellesDreiergedaechtnis(Wortgedaechtnis):
    """Gleiches Lernen; absorbierender 2x2-Blick in O(log Horizont) statt O(Horizont).

    Gilt ausschließlich für zwei nichtkritische und ein kritisches Wort. Nahe der
    Entscheidungsschwelle wird die Originalrechnung benutzt, um Rundungswechsel
    zu vermeiden. Referenzmodus und Paritätstests bleiben verfügbar.
    """
    def __init__(self, *args, schwelle=0.6, **kwargs):
        super().__init__(*args, **kwargs)
        self.schwelle = schwelle
        self.ruhig = tuple(w for w in self.woerter if not kritisch(w))
        self.ziel = tuple(w for w in self.woerter if kritisch(w))
        if len(self.ruhig) != 2 or len(self.ziel) != 1:
            raise ValueError("Der schnelle Blick braucht genau zwei ruhige und ein kritisches Wort.")

    def kritisch_binnen(self, wort, horizont):
        if wort not in self.ruhig:
            return super().kritisch_binnen(wort, horizont)
        a, b = self.ruhig
        c = self.ziel[0]
        zeilen = []
        for z in (a, b):
            gewichte = [self.gewichte[z][f] + self.erbe[z][f] for f in (a, b, c)]
            beleg = sum(gewichte)
            zeilen.append([v / beleg for v in gewichte] if beleg else
                          [float(z == a), float(z == b), 0.0])
        (aa, ab, ac), (ba, bb, bc) = zeilen
        va, vb, treffer = float(wort == a), float(wort == b), 0.0
        rest = horizont
        while rest:
            if rest & 1:
                treffer += va * ac + vb * bc
                va, vb = va * aa + vb * ba, va * ab + vb * bb
            rest >>= 1
            if rest:
                ac, bc = ac + aa * ac + ab * bc, bc + ba * ac + bb * bc
                aa, ab, ba, bb = (aa * aa + ab * ba, aa * ab + ab * bb,
                                  ba * aa + bb * ba, ba * ab + bb * bb)
        if abs(treffer - self.schwelle) < 1e-10:
            return super().kritisch_binnen(wort, horizont)
        return treffer


def einzelwarnungen(woerter, woerterbuch, erbe, verfahren, e, referenz=False):
    if verfahren == "Feste Regel":
        return [grob(w) == "SCHWACH" for w in woerter]
    if verfahren == "Immer warnen":
        return [not kritisch(w) for w in woerter]
    if verfahren == "Letzter Durchgang":
        return letzter_durchgang(woerter)
    if verfahren not in VERFAHREN:
        raise ValueError("Unbekanntes Verfahren.")
    klasse = Wortgedaechtnis if referenz else SchnellesDreiergedaechtnis
    extra = {} if referenz else dict(schwelle=e.schwelle)
    modell = klasse(woerterbuch, erbe, erbe=0 if verfahren == "Ohne Erbe" else 3,
                   startwert=verfahren == "Startwert", **extra)
    return warnungen(woerter, modell, e.horizont, e.schwelle)


def verfahren(stufen, e, referenz=False):
    woerter = schwerstes(stufen)
    grobe = [grob(w) for w in woerter]
    for name in VERFAHREN:
        warn = einzelwarnungen(grobe, GROBWOERTER, GROBERBE, name, e, referenz)
        yield "grob", name, warn, {signal: warn for signal, _, _ in SIGNALE}
        je = {signal: einzelwarnungen([s[signal] for s in stufen], ("OK", hoch, krit),
                                     ((hoch, krit),), name, e, referenz)
              for signal, hoch, krit in SIGNALE}
        gesamt = [not kritisch(w) and any(je[s][t] for s in je) for t, w in enumerate(woerter)]
        yield "je_signal", name, gesamt, je


def zaehle(woerter, warn, horizont, auswertbar, verdeckt=0):
    """Rohzähler: volle Zukunft für alle gezählten Takte, Phasen mit vollem Vorfenster.

    Die letzten H Takte dienen nur als bekannte Zukunft; sie sind keine negativen
    Beispiele. Phasen beginnen zwischen H und len-H-1. zusammen=1 verbindet nur
    unmittelbar benachbarte kritische Takte; 0 würde sogar diese trennen.
    """
    ende = len(woerter) - horizont
    takte = [t for t in range(ende) if auswertbar[t]]
    ziel = binnen_vor([kritisch(w) for w in woerter], horizont)
    gewarnt = [t for t in takte if warn[t]]
    beginne = [b for b, _ in phasen(woerter, zusammen=1) if horizont <= b < ende]
    vorgewarnt = sum(any(warn[t] and not kritisch(woerter[t])
                         for t in range(b - horizont, b)) for b in beginne)
    return dict(takte=ende, auswertbar=len(takte), warntakte=len(gewarnt),
                treffertakte=sum(t in ziel for t in gewarnt),
                zieltakte=sum(t in ziel for t in takte), phasen=len(beginne),
                vorgewarnt=vorgewarnt, verpasst=len(beginne) - vorgewarnt,
                verdeckt=verdeckt)


def anteile(z):
    def teilen(a, b):
        return z[a] / z[b] if z[b] else None
    return dict(warnanteil=teilen("warntakte", "auswertbar"),
                trefferquote=teilen("treffertakte", "warntakte"),
                grundrate=teilen("zieltakte", "auswertbar"),
                phasenquote=teilen("vorgewarnt", "phasen"))


def auswerten(stufen, e, referenz=False):
    woerter = schwerstes(stufen)
    ende = len(stufen) - e.horizont
    for sicht, name, warn, je in verfahren(stufen, e, referenz):
        z = zaehle(woerter, warn, e.horizont, [not kritisch(w) for w in woerter])
        yield dict(sicht=sicht, verfahren=name, signal="gesamt", **z, **anteile(z))
        for signal, hoch, _ in SIGNALE:
            eigene = [s[signal] for s in stufen]
            verdeckt = sum(w == hoch and woerter[t] != hoch for t, w in enumerate(eigene[:ende]))
            z = zaehle(eigene, je[signal], e.horizont, [w == hoch for w in eigene], verdeckt)
            yield dict(sicht=sicht, verfahren=name, signal=signal, **z, **anteile(z))


def auftrag(arg):
    satz, familie, seed, e, referenz = arg
    stufen = generiere(familie, seed, satz, e)
    return [dict(satz=satz, familie=familie, seed=seed, **z)
            for z in auswerten(stufen, e, referenz)]


def quellhashes():
    root = Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in ("signallabor.py", "vokabular.py", "kern.py", "SIGNAL-LABOR.md")}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--satz", choices=SAETZE, required=True)
    p.add_argument("--anzahl", type=int, default=1000, help="Startwerte ab 0 je Familie")
    p.add_argument("--familien", choices=FAMILIEN, nargs="+", default=list(FAMILIEN))
    p.add_argument("--takte", type=int, default=960)
    p.add_argument("--horizont", type=int, default=30)
    p.add_argument("--waerme-p", type=float, default=0.38)
    p.add_argument("--ausnahme-p", type=float, default=0.05)
    p.add_argument("--schwelle", type=float, default=0.6)
    p.add_argument("--prozesse", type=int, default=1)
    p.add_argument("--referenz", action="store_true", help="Unbeschleunigte Originalrechnung")
    p.add_argument("--ausgabe", type=Path, required=True, help="Neuer Ergebnisordner, wird nie überschrieben")
    a = p.parse_args()
    try:
        e = Einstellungen(a.takte, a.horizont, a.waerme_p, a.ausnahme_p, a.schwelle)
        if a.anzahl < 1 or not 1 <= a.prozesse <= 32 or len(a.familien) != len(set(a.familien)):
            raise ValueError("Positive Anzahl, 1–32 Prozesse und eindeutige Familien nötig.")
        hashes = quellhashes()
        a.ausgabe.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as exc:
        p.exit(2, f"Signallabor: {exc}\n")
    manifest = dict(schema=VERSION, status="unvollstaendig", satz=a.satz, anzahl=a.anzahl,
                    familien=a.familien, einstellungen=asdict(e), quellhashes=hashes,
                    referenz=a.referenz, python=list(sys.version_info[:3]),
                    seedverfahren="SHA256([version,satz,familie,seed,signal]), seed=0..anzahl-1")
    meta = a.ausgabe / "manifest.json"
    meta.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    jobs = ((a.satz, f, seed, e, a.referenz) for f in a.familien for seed in range(a.anzahl))
    pool = ProcessPoolExecutor(a.prozesse) if a.prozesse > 1 else None
    summen = defaultdict(lambda: dict(spuren=0, **{k: 0 for k in ZAEHLER}))
    fertig = 0
    try:
        reihe = pool.map(auftrag, jobs, chunksize=4) if pool else map(auftrag, jobs)
        with (a.ausgabe / "einzel.csv").open("w", encoding="utf-8", newline="") as f:
            writer = None
            for zeilen in reihe:
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(zeilen[0]))
                    writer.writeheader()
                writer.writerows(zeilen)
                for z in zeilen:
                    k = tuple(z[n] for n in ("satz", "familie", "sicht", "verfahren", "signal"))
                    summen[k]["spuren"] += 1
                    for feld in ZAEHLER:
                        summen[k][feld] += z[feld]
                fertig += 1
                if fertig % 100 == 0:
                    print(f"{fertig}/{a.anzahl * len(a.familien)} Spuren fertig", flush=True)
        with (a.ausgabe / "summen.csv").open("w", encoding="utf-8", newline="") as f:
            writer = None
            for k, z in sorted(summen.items()):
                row = dict(zip(("satz", "familie", "sicht", "verfahren", "signal"), k), **z, **anteile(z))
                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=list(row))
                    writer.writeheader()
                writer.writerow(row)
        manifest.update(status="vollstaendig", spuren=fertig,
                        ergebnisse={name: hashlib.sha256((a.ausgabe / name).read_bytes()).hexdigest()
                                    for name in ("einzel.csv", "summen.csv")})
        meta.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Fertig: {fertig} Spuren, {fertig * 48} Einzelzeilen.")
    finally:
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)


if __name__ == "__main__":
    main()
