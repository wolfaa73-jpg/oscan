"""Vorab festgelegte Prüfung der 24h-Aufnahme; keine Gerätezugriffe, keine Auswahl."""
import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import koerper
from kern import Knoten, REGELN
from kostenlabor import wahrscheinlichkeiten
from signallabor import letzter_durchgang
from vokabular import SIGNALE, grob, kritisch, stufen_je_signal

VERSION = "24h-v1"
HORIZONTE = (30, 60)
METHODEN = ("Feste Regel", "Festes Erbe", "Startwert h6/.6", "Startwert #4",
            "Letzter Durchgang", "Immer warnen", "Nie warnen")
ERB_H = dict(temperatur=1, speicher=15, schleife=17)
QUELLEN = ("pruefung24h.py", "PRUEFPROTOKOLL-24H.md", "koerper.py", "kern.py",
           "vokabular.py", "kostenlabor.py", "signallabor.py")


class Prueffehler(ValueError):
    def __init__(self, code, abweichungen=()):
        super().__init__(code)
        self.abweichungen = list(abweichungen)


def sha(pfad):
    return hashlib.sha256(pfad.read_bytes()).hexdigest()


def identitaeten(pfad):
    # Keine Dateinamen, Metadaten-Freitexte oder lokalen Pfade ausgeben.
    return {"csv_sha256": sha(pfad), "json_sha256": sha(pfad.with_suffix(".json"))}


def integer(wert, unten=0, oben=2**32 - 1):
    return type(wert) is int and unten <= wert <= oben


def vorpruefung(pfad):
    """Struktur zuerst; danach Originalprüfer UND vollständige Abweichungsliste."""
    if pfad.with_name(pfad.stem + ".abbruch.txt").exists():
        raise Prueffehler("AUFNAHME_MIT_ABBRUCHDATEI")
    with pfad.open(encoding="utf-8", newline="") as datei:
        if next(csv.reader(datei), None) != list(koerper.KOPF):
            raise Prueffehler("CSV_KOPF")
    try:
        meta, werte = koerper.lies_aufnahme(pfad)
    except (ValueError, TypeError, KeyError):
        raise Prueffehler("CSV_ODER_JSON_UNGUELTIG") from None
    if not isinstance(meta, dict):
        raise Prueffehler("METADATEN")
    for name, soll in (("regel", "startwert"), ("blick", 60),
                       ("intervall_ms", 1000), ("sichern_alle", 600)):
        if type(meta.get(name)) is not type(soll) or meta[name] != soll:
            raise Prueffehler("METADATEN_" + name.upper())
    if "fortsetzung" not in meta or meta["fortsetzung"] is not None:
        raise Prueffehler("KEIN_FRISCHER_LAUF")
    try:
        g = koerper.Grenzen(**meta["grenzen"])
    except (KeyError, TypeError, ValueError):
        raise Prueffehler("GRENZEN") from None
    if not werte:
        raise Prueffehler("LEERE_AUFNAHME")
    vorher_ms = -1
    for nummer, w in enumerate(werte, 1):
        if w["takt"] != nummer:
            raise Prueffehler("TAKTFOLGE_AB_" + str(nummer))
        if not integer(w["zeit_ms"], 0, 2**63 - 1) or w["zeit_ms"] < vorher_ms:
            raise Prueffehler("ZEITFOLGE_AB_" + str(nummer))
        vorher_ms = w["zeit_ms"]
        if (not integer(w["heap"]) or not integer(w["luecke_us"])
                or not integer(w["reiz"], 0, 7)
                or (w["temp_dc"] is not None and not integer(w["temp_dc"], 0, koerper.MAX_TEMP))
                or w["zustand"] not in ("OK", "SCHWACH", "AUSFALL")
                or w["sofort"] not in (0, 1) or w["vorwarnung"] not in (0, 1)):
            raise Prueffehler("WERTEBEREICH_AB_" + str(nummer))
    original_ok = True
    try:
        koerper.pruefen(pfad)
    except (ValueError, KeyError, TypeError):
        original_ok = False
    k = Knoten(REGELN["startwert"](), blick=60)
    abweichungen = []
    for w in werte:
        zustand = koerper.einstufen(w["temp_dc"], w["heap"], w["luecke_us"], g)
        s = k.schritt(w["takt"], zustand)
        if (zustand, int(s.sofort), int(s.vorwarnung)) != (w["zustand"], w["sofort"], w["vorwarnung"]):
            abweichungen.append((w["takt"], w["zustand"], zustand, w["sofort"], int(s.sofort),
                                w["vorwarnung"], int(s.vorwarnung)))
    if not original_ok or abweichungen:
        raise Prueffehler("GERAET_PYTHON_UNGLEICH", abweichungen)
    return meta, werte, g


def vorhersagen(woerter, hoch, krit, horizont, h, referenz=False):
    erbe = wahrscheinlichkeiten(woerter, hoch, krit, None, horizont, referenz)
    start = wahrscheinlichkeiten(woerter, hoch, krit, 6, horizont, referenz)
    gewaehlt = wahrscheinlichkeiten(woerter, hoch, krit, h, horizont, referenz)
    return dict(zip(METHODEN, (
        [w == hoch for w in woerter], [p >= .6 for p in erbe],
        [p >= .6 for p in start], [p >= .95 for p in gewaehlt],
        letzter_durchgang(woerter), [not kritisch(w) for w in woerter],
        [False] * len(woerter))))


def zaehlen(woerter, warn, horizont, nur_hoch=False):
    """Eigene O(n)-Zählung; keine gemeinsame Zählerimplementierung mit #4."""
    if type(horizont) is not int or not 1 <= horizont <= 600:
        raise ValueError("Horizont")
    n = len(woerter)
    if n != len(warn) or n <= 2 * horizont:
        raise ValueError("Vollstaendige Fenster erforderlich")
    ende = n - horizont
    krit = [kritisch(w) for w in woerter]
    zukunft = [0]
    vorwarn = [0]
    for k, w in zip(krit, warn):
        zukunft.append(zukunft[-1] + k)
        vorwarn.append(vorwarn[-1] + (bool(w) and not k))
    z = dict(takte=ende, auswertbar=0, warntakte=0, treffertakte=0, zieltakte=0,
             phasen=0, vorgewarnt=0)
    for t in range(ende):
        if not krit[t] and (not nur_hoch or grob(woerter[t]) == "SCHWACH"):
            ziel = zukunft[t + horizont + 1] > zukunft[t + 1]
            z["auswertbar"] += 1
            z["warntakte"] += bool(warn[t])
            z["treffertakte"] += bool(warn[t]) and ziel
            z["zieltakte"] += ziel
        if horizont <= t and krit[t] and not krit[t - 1]:
            z["phasen"] += 1
            z["vorgewarnt"] += vorwarn[t] > vorwarn[t - horizont]
    z["verpasst"] = z["phasen"] - z["vorgewarnt"]
    z["fehlwarntakte"] = z["warntakte"] - z["treffertakte"]
    z["verpasste_zieltakte"] = z["zieltakte"] - z["treffertakte"]
    z["kosten_phase_r10"] = 10 * z["verpasst"] + z["fehlwarntakte"]
    z["kosten_takt_r10"] = 10 * z["verpasste_zieltakte"] + z["fehlwarntakte"]
    for feld, a, b in (("warnanteil", "warntakte", "auswertbar"),
                       ("trefferquote", "treffertakte", "warntakte"),
                       ("grundrate", "zieltakte", "auswertbar"),
                       ("phasenquote", "vorgewarnt", "phasen")):
        z[feld] = z[a] / z[b] if z[b] else None
    return z


def auswertung(werte, g, horizonte=HORIZONTE, referenz=False):
    """Modelle nur aus Präfixen; Auswertung danach. Keine Auswahl auf der Aufnahme."""
    stufen = [stufen_je_signal(w["temp_dc"], w["heap"], w["luecke_us"], g) for w in werte]
    grobe = [w["zustand"] for w in werte]
    zeilen, sichern = [], []
    for horizont in horizonte:
        je = {signal: vorhersagen([w[signal] for w in stufen], hoch, krit, horizont,
                                  ERB_H[signal], referenz) for signal, hoch, krit in SIGNALE}
        grobe_modelle = {signal: vorhersagen(grobe, "SCHWACH", "AUSFALL", horizont,
                                           ERB_H[signal], referenz) for signal, _, _ in SIGNALE}
        for sicht, modelle in (("grob", grobe_modelle), ("je_signal", je)):
            for methode in METHODEN:
                warn = {signal: modelle[signal][methode] for signal, _, _ in SIGNALE}
                gesamt = [w != "AUSFALL" and any(warn[s][t] for s in warn)
                          for t, w in enumerate(grobe)]
                for signal, zielwoerter, w in [("gesamt", grobe, gesamt)] + [
                    (signal, [z[signal] for z in stufen], warn[signal]) for signal, _, _ in SIGNALE]:
                    for filtername in (("alle_nichtkritisch", "nur_hoch") if signal != "gesamt"
                                       else ("alle_nichtkritisch",)):
                        zeilen.append(dict(horizont=horizont, sicht=sicht, methode=methode,
                                           signal=signal, filter=filtername,
                                           **zaehlen(zielwoerter, w, horizont, filtername == "nur_hoch")))
                for t, w in enumerate(werte):
                    # Speicheraufruf erfolgt nach der Messung; Folgetakt ebenfalls vorab festgelegt.
                    if w["takt"] % 600 in (0, 1) and w["takt"] > 1:
                        sichern.append(dict(horizont=horizont, sicht=sicht, methode=methode,
                                            takt=w["takt"], gesamt=int(gesamt[t]),
                                            **{s: int(warn[s][t]) for s in warn}))
    return zeilen, sichern


def hypothesen(zeilen):
    def finde(h, methode, signal, filtername="alle_nichtkritisch"):
        return next(z for z in zeilen if (z["horizont"], z["sicht"], z["methode"], z["signal"], z["filter"])
                    == (h, "je_signal", methode, signal, filtername))
    def pruefe(name, werte, bestanden):
        return dict(hypothese=name, status=("NICHT_PRUEFBAR" if any(v is None for v in werte)
                                           else "ERFUELLT" if bestanden else "NICHT_ERFUELLT"))
    mem = finde(30, "Startwert h6/.6", "speicher", "nur_hoch")
    erbe = finde(30, "Festes Erbe", "speicher", "nur_hoch")
    vals = [mem[k] for k in ("trefferquote", "warnanteil", "phasenquote")] + [erbe["warnanteil"]]
    h1 = pruefe("H1 Speicher: Praezision>=.65, Warnanteil<=.8*Erbe, Phasenquote>=.80 (30)", vals,
                all(v is not None for v in vals) and vals[0] >= .65
                and vals[1] <= .8 * vals[3] and vals[2] >= .8)
    ges = finde(60, "Startwert h6/.6", "gesamt")
    vals = [ges[k] for k in ("warnanteil", "trefferquote", "phasenquote")]
    h2 = pruefe("H2 Gesamt: Warnanteil<=.45, Praezision>=.65, Phasenquote>=.90 (60)", vals,
                all(v is not None for v in vals) and vals[0] <= .45 and vals[1] >= .65 and vals[2] >= .9)
    result = [h1, h2]
    for signal, _, _ in SIGNALE:
        a, b = finde(30, "Startwert #4", signal), finde(30, "Startwert h6/.6", signal)
        # Ohne kritische Phase ist die behauptete Übertragung nicht prüfbar.
        result.append(pruefe("H3 " + signal + ": Kosten_phase_r10(#4)<=Default (30)",
                             [1 if a["phasen"] else None],
                             a["kosten_phase_r10"] <= b["kosten_phase_r10"]))
    return result


def tabelle(kopf, reihen):
    return ["| " + " | ".join(kopf) + " |", "| " + " | ".join("---" for _ in kopf) + " |"] + [
        "| " + " | ".join(str(w) for w in row) + " |" for row in reihen]


def anteil(x):
    return "NA" if x is None else f"{100*x:.6f}%"


def druckbericht(pfad):
    hashes = identitaeten(pfad)
    meta, werte, g = vorpruefung(pfad)
    if len(werte) < 86400:
        raise Prueffehler("KEINE_VOLLSTAENDIGEN_86400_TAKTE")
    zeilen, sichern = auswertung(werte, g)
    if identitaeten(pfad) != hashes:
        raise Prueffehler("DATEIEN_WAEHREND_PRUEFUNG_VERAENDERT")
    out = ["# Prüfbericht " + VERSION, "", "koerper.py pruefen: BESTANDEN. Geräteabweichungen: 0.",
           "Kein automatischer Nachweis des Zeitpunkts der ersten Datensicht; siehe Protokoll.", ""]
    out += [f"{k}: `{v}`" for k, v in hashes.items()]
    out += [f"Quelle {name}: `{sha(Path(__file__).parent / name)}`" for name in QUELLEN]
    out += ["", f"Takte: {len(werte)}; erste/letzte Nummer: 1/{werte[-1]['takt']}; "
            f"Empfangsspanne_ms: {werte[-1]['zeit_ms']-werte[0]['zeit_ms']}; "
            f"fehlende Temperaturwerte: {sum(w['temp_dc'] is None for w in werte)}.",
            "Grenzen: " + json.dumps(vars(g), sort_keys=True), "",
            "## Vorab festgelegte Hypothesen", ""]
    out += tabelle(("Hypothese", "Befund"), [(h["hypothese"], h["status"]) for h in hypothesen(zeilen)])
    for h in HORIZONTE:
        for sicht in ("grob", "je_signal"):
            for signal in ("gesamt", *(s for s, _, _ in SIGNALE)):
                for filtername in (("alle_nichtkritisch", "nur_hoch") if signal != "gesamt"
                                   else ("alle_nichtkritisch",)):
                    rows = [z for z in zeilen if (z["horizont"], z["sicht"], z["signal"], z["filter"])
                            == (h, sicht, signal, filtername)]
                    out += ["", f"## H={h}, {sicht}, {signal}, {filtername}", ""]
                    if filtername == "nur_hoch":
                        out += tabelle(("Verfahren", "N", "W", "Treffer", "Ziele", "Warnanteil", "Präzision", "Grundrate",
                                        "Phasen", "ohne Warnung"),
                                       [(z["methode"], z["auswertbar"], z["warntakte"], z["treffertakte"], z["zieltakte"],
                                         anteil(z["warnanteil"]), anteil(z["trefferquote"]), anteil(z["grundrate"]),
                                         z["phasen"], z["verpasst"]) for z in rows])
                        continue
                    out += tabelle(("Verfahren", "N", "W", "Treffer", "Ziele", "Warnanteil", "Präzision", "Grundrate",
                                     "Phasen", "ohne Warnung", "Fehlwarn", "verpasste Zieltakte", "Kphase", "Ktakt", "Kphase/1000", "Ktakt/1000"),
                                    [(z["methode"], z["auswertbar"], z["warntakte"], z["treffertakte"], z["zieltakte"],
                                      anteil(z["warnanteil"]), anteil(z["trefferquote"]), anteil(z["grundrate"]),
                                      z["phasen"], z["verpasst"], z["fehlwarntakte"], z["verpasste_zieltakte"],
                                      z["kosten_phase_r10"], z["kosten_takt_r10"],
                                      f"{1000*z['kosten_phase_r10']/z['takte']:.6f}",
                                      f"{1000*z['kosten_takt_r10']/z['takte']:.6f}") for z in rows])
    out += ["", "## Speichertakte und fest eingeplante Folgetakte (alle bleiben in der Wertung)", ""]
    out += tabelle(("Takt", "Lücke_us", "Stufe", "Schleifenstufe", "Gerätwarnung", "sofort", "im Zielnenner H30/H60"),
                    [(w["takt"], w["luecke_us"], w["zustand"],
                      stufen_je_signal(w["temp_dc"], w["heap"], w["luecke_us"], g)["schleife"],
                      w["vorwarnung"], w["sofort"],
                      str(w["takt"] <= len(werte)-30) + "/" + str(w["takt"] <= len(werte)-60))
                     for w in werte if w["takt"] > 1 and w["takt"] % 600 in (0, 1)])
    out += ["", "Warnungen aller Verfahren an diesen Takten (T/S/L = Temperatur/Speicher/Schleife):", ""]
    out += tabelle(("H", "Sicht", "Verfahren", "Takt", "Gesamt", "T", "S", "L"),
                    [(z["horizont"], z["sicht"], z["methode"], z["takt"], z["gesamt"],
                      z["temperatur"], z["speicher"], z["schleife"]) for z in sichern])
    return "\n".join(out) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    arg = parser.parse_args(argv)
    try:
        ausgabe = druckbericht(arg.csv)
    except Prueffehler as error:
        print("ABBRUCH: " + str(error))
        print("Keine Guetetabellen. Geraeteabweichungen: " + str(len(error.abweichungen)))
        if error.abweichungen:
            print("\n".join(tabelle(("Takt", "Geraet Stufe", "Python Stufe", "Geraet sofort", "Python sofort",
                                      "Geraet Warnung", "Python Warnung"), error.abweichungen)))
        return 2
    except (OSError, ValueError, KeyError, TypeError, csv.Error, UnicodeError):
        # Kein Pfad oder Eingabetext aus fremden Metadaten in Übergabe-Logs.
        print("ABBRUCH: EINGABE_NICHT_LESBAR_ODER_UNGUELTIG. Keine Guetetabellen.")
        return 2
    print(ausgabe, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
