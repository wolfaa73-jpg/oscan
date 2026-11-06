"""Schwellen und Erb-Halbwertszeiten: Entwicklung auswählen, neue Kontrolle nur prüfen."""
import argparse
import bisect
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import signallabor as s
from vokabular import Wortgedaechtnis, binnen_vor, kritisch

SCHWELLEN = tuple(i / 20 for i in range(1, 20))
SUCHEN = ("erbe_schwelle", "startwert_schwelle", "startwert_halbwertszeit", "startwert_gemeinsam")
KOSTEN = ("takt", "phase")
FELDER = ("takte", "auswertbar", "warntakte", "treffertakte", "zieltakte",
          "fehlwarntakte", "verpasste_zieltakte", "phasen", "vorgewarnt", "verpasst")
SCHLUESSEL = ("familie", "signal", "konfiguration", "modell", "halbwertszeit", "schwellenindex")


class ParameterGedaechtnis(s.SchnellesDreiergedaechtnis):
    """Nur das Erbe erhält eine eigene Halbwertszeit; eigene Erfahrung bleibt bei 6.

    None = unveränderliches Erbe. An jeder Rastergrenze wird exakt nachgerechnet.
    """
    def __init__(self, woerter, erbfolgen, erb_halbwertszeit=None, referenz=False):
        if erb_halbwertszeit is not None and (isinstance(erb_halbwertszeit, bool)
                or not math.isfinite(erb_halbwertszeit) or erb_halbwertszeit <= 0):
            raise ValueError("Erb-Halbwertszeit muss positiv und endlich sein.")
        super().__init__(woerter, erbfolgen, startwert=False, halbwertszeit=6.0)
        self.erb_faktor = None if erb_halbwertszeit is None else 0.5 ** (1 / erb_halbwertszeit)
        self.referenz = referenz

    def beobachte(self, vorher, jetzt):
        super().beobachte(vorher, jetzt)
        if self.erb_faktor is not None and vorher is not None and vorher != jetzt:
            for folge in self.erbe[vorher]:
                self.erbe[vorher][folge] *= self.erb_faktor

    def kritisch_binnen(self, wort, horizont):
        if type(horizont) is not int or not 1 <= horizont <= 600:
            raise ValueError("Horizont muss ganzzahlig zwischen 1 und 600 liegen.")
        if self.referenz:
            return Wortgedaechtnis.kritisch_binnen(self, wort, horizont)
        p = super().kritisch_binnen(wort, horizont)
        grenze = round(p * 20)
        if 1 <= grenze <= 19 and abs(p - grenze / 20) < 1e-10:
            return Wortgedaechtnis.kritisch_binnen(self, wort, horizont)
        return p


def wahrscheinlichkeiten(woerter, hoch, krit, halbwertszeit=None, horizont=30, referenz=False):
    modell = ParameterGedaechtnis(("OK", hoch, krit), ((hoch, krit),), halbwertszeit, referenz)
    scores, vorher = [], None
    for wort in woerter:
        modell.beobachte(vorher, wort)
        scores.append(modell.kritisch_binnen(wort, horizont)
                      if not kritisch(wort) and modell.beleg(wort) >= 3 else -1.0)
        vorher = wort
    return scores


def rasterzaehler(woerter, scores, horizont=30, schwellen=SCHWELLEN):
    """Alle Schwellen aus Histogrammen; keine Zukunft fließt in die Scores ein."""
    if type(horizont) is not int or not 1 <= horizont <= 600:
        raise ValueError("Ungültiger Horizont.")
    if len(woerter) != len(scores) or len(woerter) <= 2 * horizont:
        raise ValueError("Gleich lange Folgen und ein vollständiges Bewertungsfenster nötig.")
    if not schwellen or tuple(sorted(set(schwellen))) != tuple(schwellen):
        raise ValueError("Schwellen müssen eindeutig und aufsteigend sein.")
    if any(not math.isfinite(x) or not 0 <= x <= 1 for x in schwellen):
        raise ValueError("Ungültige Schwelle.")
    if any(not math.isfinite(x) for x in scores):
        raise ValueError("Ungültiger Score.")
    ende = len(woerter) - horizont
    krit = [kritisch(w) for w in woerter]
    ziel = binnen_vor(krit, horizont)
    beginne = [t for t in range(horizont, ende) if krit[t] and not krit[t - 1]]
    n = len(schwellen)
    warnhist, treffhist, phasenhist = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    auswertbar = zieltakte = 0
    for t in range(ende):
        if krit[t]:
            continue
        auswertbar += 1
        ist_ziel = t in ziel
        zieltakte += ist_ziel
        k = bisect.bisect_right(schwellen, scores[t])
        warnhist[k] += 1
        treffhist[k] += ist_ziel
    for b in beginne:
        maximum = max((scores[t] for t in range(b - horizont, b) if not krit[t]), default=-1.0)
        phasenhist[bisect.bisect_right(schwellen, maximum)] += 1
    warn = treffer = vorgewarnt = 0
    rueckwaerts = []
    for i in range(n, 0, -1):
        warn += warnhist[i]
        treffer += treffhist[i]
        vorgewarnt += phasenhist[i]
        rueckwaerts.append(dict(schwelle=schwellen[i - 1], takte=ende, auswertbar=auswertbar,
                               warntakte=warn, treffertakte=treffer, zieltakte=zieltakte,
                               fehlwarntakte=warn-treffer, verpasste_zieltakte=zieltakte-treffer,
                               phasen=len(beginne), vorgewarnt=vorgewarnt, verpasst=len(beginne)-vorgewarnt))
    return list(reversed(rueckwaerts))


def konfig(modell, h=0, index=12):
    if type(h) is not int or type(index) is not int:
        raise ValueError("Halbwertszeit und Schwellenindex müssen ganzzahlig sein.")
    if modell in ("fest", "immer", "nie", "letzter"):
        if h != 0 or index != 12:
            raise ValueError("Baselines haben keine frei wählbaren Parameter.")
        name = modell
    elif modell == "erbe" and h == 0 and index in range(1, 20):
        name = f"erbe-s{index:02}"
    elif modell == "startwert" and h in range(1, 25) and index in range(1, 20):
        name = f"startwert-h{h:02}-s{index:02}"
    else:
        raise ValueError("Unbekannte Konfiguration.")
    return dict(konfiguration=name, modell=modell, halbwertszeit=h, schwellenindex=index)


def alle_konfigurationen():
    return ([konfig("erbe", index=i) for i in range(1, 20)]
            + [konfig("startwert", h, i) for h in range(1, 25) for i in range(1, 20)]
            + [konfig(m) for m in ("fest", "immer", "nie", "letzter")])


def defaults():
    return [konfig("erbe"), konfig("startwert", 6), *[konfig(m) for m in ("fest", "immer", "nie", "letzter")]]


def signalzeilen(stufen, e, konfigurationen, referenz=False):
    """Konfigurationen je Signal; alle Warnkosten umfassen auch eigene OK-Takte."""
    for signal, hoch, krit in s.SIGNALE:
        woerter = [z[signal] for z in stufen]
        gruppen = defaultdict(list)
        for c in konfigurationen[signal]:
            gruppen[c["modell"], c["halbwertszeit"]].append(c)
        for (modell, h), configs in sorted(gruppen.items()):
            if modell in ("erbe", "startwert"):
                scores = wahrscheinlichkeiten(woerter, hoch, krit, h or None, e.horizont, referenz)
            else:
                warn = ([w == hoch for w in woerter] if modell == "fest" else
                        [not kritisch(w) for w in woerter] if modell == "immer" else
                        s.letzter_durchgang(woerter) if modell == "letzter" else
                        [False] * len(woerter))
                scores = [1.0 if w else -1.0 for w in warn]
            configs = sorted(configs, key=lambda c: c["schwellenindex"])
            rows = rasterzaehler(woerter, scores, e.horizont, tuple(c["schwellenindex"] / 20 for c in configs))
            for c, z in zip(configs, rows):
                yield dict(signal=signal, **c, **z)


def auftrag(arg):
    satz, familie, seed, e, configs = arg
    spur = s.generiere(familie, seed, satz, e)
    return [dict(familie=familie, seed=seed, **z) for z in signalzeilen(spur, e, configs)]


def kostenzahl(row, art, verhaeltnis):
    if art not in KOSTEN or type(verhaeltnis) is not int or not 1 <= verhaeltnis <= 100:
        raise ValueError("Unbekanntes Kostenmodell oder Kostenverhältnis.")
    return verhaeltnis * row["verpasste_zieltakte" if art == "takt" else "verpasst"] + row["fehlwarntakte"]


def passt(row, suche):
    return ((suche == "erbe_schwelle" and row["modell"] == "erbe") or
            (suche == "startwert_schwelle" and row["modell"] == "startwert" and row["halbwertszeit"] == 6) or
            (suche == "startwert_halbwertszeit" and row["modell"] == "startwert" and row["schwellenindex"] == 12) or
            (suche == "startwert_gemeinsam" and row["modell"] == "startwert"))


def waehle(rows, art, verhaeltnis, suche):
    if suche not in SUCHEN:
        raise ValueError("Unbekanntes Auswahlregime.")
    kandidaten = [r for r in rows if passt(r, suche)]
    if not kandidaten:
        raise ValueError("Keine Kandidaten.")
    return min(kandidaten, key=lambda r: (kostenzahl(r, art, verhaeltnis), r["verpasst"], r["warntakte"],
                                          abs(r["schwellenindex"] - 12), abs(r["halbwertszeit"] - 6),
                                          r["halbwertszeit"], r["schwellenindex"]))


def quoten(row):
    def q(a, b):
        return row[a] / row[b] if row[b] else None
    return dict(warnanteil=q("warntakte", "auswertbar"), trefferquote=q("treffertakte", "warntakte"),
                grundrate=q("zieltakte", "auswertbar"), phasenquote=q("vorgewarnt", "phasen"))


def csv_schreiben(path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = None
        for row in rows:
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=list(row), lineterminator="\n")
                writer.writeheader()
            writer.writerow(row)


def json_schreiben(path, wert):
    path.write_text(json.dumps(wert, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quellhashes():
    root = Path(__file__).resolve().parent
    return {name: sha(root / name) for name in ("kostenlabor.py", "signallabor.py", "vokabular.py",
                                               "kern.py", "KOSTEN-PLAN.md")}


def reihe(satz, seedstart, anzahl, e, configs, prozesse, out, einzel=False):
    summen = defaultdict(lambda: dict(spuren=0, **{k: 0 for k in FELDER}))
    jobs = ((satz, f, seed, e, configs) for f in s.FAMILIEN for seed in range(seedstart, seedstart + anzahl))
    pool = ProcessPoolExecutor(prozesse) if prozesse > 1 else None
    raw = (out / "einzel.csv").open("w", encoding="utf-8", newline="") if einzel else None
    writer = None
    try:
        resultate = pool.map(auftrag, jobs, chunksize=2) if pool else map(auftrag, jobs)
        for nummer, rows in enumerate(resultate, 1):
            if raw:
                if writer is None:
                    writer = csv.DictWriter(raw, fieldnames=list(rows[0]), lineterminator="\n")
                    writer.writeheader()
                writer.writerows(rows)
            for row in rows:
                for familie in (row["familie"], "alle"):
                    key = (familie, *[row[k] for k in SCHLUESSEL[1:]])
                    z = summen[key]
                    z["spuren"] += 1
                    for feld in FELDER:
                        z[feld] += row[feld]
            if nummer % 100 == 0:
                print(f"{nummer}/{anzahl * len(s.FAMILIEN)} Spuren fertig", flush=True)
    finally:
        if raw:
            raw.close()
        if pool:
            pool.shutdown(wait=True, cancel_futures=True)
    rows = [dict(zip(SCHLUESSEL, key), schwelle=key[-1]/20, **z, **quoten(z))
            for key, z in sorted(summen.items())]
    csv_schreiben(out / "summen.csv", rows)
    return rows


def auswahlzeilen(rows):
    for signal, _, _ in s.SIGNALE:
        teil = [r for r in rows if r["signal"] == signal]
        for art in KOSTEN:
            for r in range(1, 101):
                for suche in SUCHEN:
                    beste = waehle(teil, art, r, suche)
                    yield dict(signal=signal, kostenmodell=art, verhaeltnis=r, suche=suche,
                               **{k: beste[k] for k in ("konfiguration", "modell", "halbwertszeit", "schwellenindex")},
                               entwicklungskosten=kostenzahl(beste, art, r))


def pruefe_auswahl(a):
    if a["schema"] != 1 or a["quellhashes"] != quellhashes() or a["tiebreakversion"] != 1:
        raise ValueError("Auswahl passt nicht zum aktuellen Code und Plan.")
    ids = {c["konfiguration"]: c for c in alle_konfigurationen()}
    gesehen = set()
    for z in a["auswahl"]:
        k = (z["signal"], z["kostenmodell"], z["verhaeltnis"], z["suche"])
        if any(type(z[f]) is not int for f in ("verhaeltnis", "halbwertszeit", "schwellenindex", "entwicklungskosten")):
            raise ValueError("Auswahl braucht ganzzahlige Parameter und Kosten.")
        if k in gesehen or z["konfiguration"] not in ids or not passt(z, z["suche"]):
            raise ValueError("Ungültige oder doppelte Auswahl.")
        if any(z[f] != ids[z["konfiguration"]][f] for f in ("modell", "halbwertszeit", "schwellenindex")):
            raise ValueError("Widersprüchliche Konfiguration.")
        gesehen.add(k)
    erwartet = {(signal, art, r, suche) for signal,_,_ in s.SIGNALE for art in KOSTEN
                for r in range(1,101) for suche in SUCHEN}
    if gesehen != erwartet:
        raise ValueError("Die Auswahl ist unvollständig.")
    reserve = a["kontrolle"]
    if type(reserve["seedstart"]) is not int or type(reserve["anzahl"]) is not int or reserve["seedstart"] < 10000 or reserve["anzahl"] < 1:
        raise ValueError("Ungültige Kontrollreserve.")
    return {signal: list({c["konfiguration"]: c for c in [*defaults(),
                         *[ids[z["konfiguration"]] for z in a["auswahl"] if z["signal"] == signal]]}.values())
            for signal, _, _ in s.SIGNALE}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="aktion", required=True)
    d = sub.add_parser("entwicklung")
    d.add_argument("--anzahl", type=int, default=250)
    d.add_argument("--seedstart", type=int, default=0)
    d.add_argument("--kontrollstart", type=int, default=10000)
    d.add_argument("--kontrollanzahl", type=int, default=500)
    d.add_argument("--takte", type=int, default=960)
    c = sub.add_parser("kontrolle")
    c.add_argument("--auswahl", type=Path, required=True)
    for parser in (d, c):
        parser.add_argument("--prozesse", type=int, default=4)
        parser.add_argument("--ausgabe", type=Path, required=True)
    a = p.parse_args()
    try:
        if not 1 <= a.prozesse <= 32:
            raise ValueError("1–32 Prozesse nötig.")
        if a.aktion == "entwicklung":
            if a.anzahl < 1 or a.seedstart < 0 or a.kontrollanzahl < 1 or a.kontrollstart < 10000:
                raise ValueError("Ungültige Datensatzgrenzen.")
            e = s.Einstellungen(takte=a.takte)
            config = {signal: alle_konfigurationen() for signal, _, _ in s.SIGNALE}
            satz, seedstart, anzahl = "entwicklung", a.seedstart, a.anzahl
        else:
            auswahl = json.loads(a.auswahl.read_text())
            config = pruefe_auswahl(auswahl)
            e = s.Einstellungen(**auswahl["einstellungen"])
            satz, seedstart, anzahl = "kontrolle", auswahl["kontrolle"]["seedstart"], auswahl["kontrolle"]["anzahl"]
        a.ausgabe.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError, KeyError) as exc:
        p.exit(2, f"Kostenlabor: {exc}\n")
    meta = dict(schema=1, status="unvollstaendig", satz=satz, seedstart=seedstart, anzahl=anzahl,
                familien=list(s.FAMILIEN), einstellungen=s.asdict(e), quellhashes=quellhashes(),
                python=list(sys.version_info[:3]))
    if a.aktion == "kontrolle":
        meta["auswahl_sha256"] = sha(a.auswahl)
    json_schreiben(a.ausgabe / "manifest.json", meta)
    rows = reihe(satz, seedstart, anzahl, e, config, a.prozesse, a.ausgabe, einzel=satz == "kontrolle")
    if quellhashes() != meta["quellhashes"]:
        raise ValueError("Quellen oder Plan wurden während der Rechnung verändert.")
    if a.aktion == "entwicklung":
        ausgew = list(auswahlzeilen([r for r in rows if r["familie"] == "alle"]))
        auswahl = dict(schema=1, tiebreakversion=1, quellhashes=meta["quellhashes"], einstellungen=s.asdict(e),
                       entwicklung=dict(seedstart=seedstart, anzahl=anzahl, summen_sha256=sha(a.ausgabe/"summen.csv")),
                       kontrolle=dict(seedstart=a.kontrollstart, anzahl=a.kontrollanzahl), auswahl=ausgew)
        json_schreiben(a.ausgabe / "auswahl.json", auswahl)
        csv_schreiben(a.ausgabe / "familien-auswahl.csv",
                      (dict(familie=f, **z) for f in s.FAMILIEN
                       for z in auswahlzeilen([r for r in rows if r["familie"] == f])))
        pruefe_auswahl(auswahl)
    else:
        # Kein Wählen, kein Sortieren nach Kontrollkosten: nur eingefrorene Entscheidungen ablesen.
        index = {(r["familie"], r["signal"], r["konfiguration"]): r for r in rows}
        csv_schreiben(a.ausgabe / "auswahl-pruefung.csv",
                      (dict(familie=f, **z, kontrollkosten=kostenzahl(index[f,z["signal"],z["konfiguration"]],
                              z["kostenmodell"],z["verhaeltnis"])) for f in ("alle",*s.FAMILIEN) for z in auswahl["auswahl"]))
        if sha(a.auswahl) != meta["auswahl_sha256"]:
            raise ValueError("Auswahl wurde während der Kontrolle verändert.")
    meta.update(status="vollstaendig", spuren=anzahl*len(s.FAMILIEN),
                ergebnisse={f.name: sha(f) for f in sorted(a.ausgabe.iterdir()) if f.name != "manifest.json"})
    json_schreiben(a.ausgabe / "manifest.json", meta)
    print(f"{satz} fertig: {meta['spuren']} Spuren, {len(rows)} Summenzeilen.")


if __name__ == "__main__":
    main()
