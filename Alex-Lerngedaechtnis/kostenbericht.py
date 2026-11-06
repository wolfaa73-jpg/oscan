"""Geprüfte Kostenübersicht und gepaarte Bootstrap-Intervalle einer eingefrorenen Auswahl."""
import argparse
import csv
import json
import math
import random
import sys
from array import array
from pathlib import Path

import kostenlabor as k

BOOTSTRAP_SEED = 20261106
WIEDERHOLUNGEN = 500
VERHAELTNISSE = (1, 10, 100)
SUCHNAMEN = {
    "erbe_schwelle": "Erbe: Schwelle gewählt",
    "startwert_schwelle": "Startwert: Schwelle gewählt",
    "startwert_halbwertszeit": "Startwert: Halbwertszeit gewählt",
    "startwert_gemeinsam": "Startwert: gemeinsames Raster",
}
BASELINES = (("erbe-s12", "Festes Erbe, Default"),
             ("startwert-h06-s12", "Startwert, Default"),
             ("fest", "Feste Regel"), ("immer", "Immer warnen"),
             ("nie", "Nie warnen"), ("letzter", "Letzter Durchgang"))


def quantil(werte, p):
    """Linear interpoliertes empirisches Quantil, Position (n-1)*p."""
    if not werte or not 0 <= p <= 1:
        raise ValueError("Ungültige Quantil-Eingabe.")
    sortiert = sorted(werte)
    position = (len(sortiert) - 1) * p
    lo, hi = math.floor(position), math.ceil(position)
    return sortiert[lo] + (sortiert[hi] - sortiert[lo]) * (position - lo)


class BootstrapPlan:
    """Ganze gepaarte Spuren; jede Familie behält ihre ursprüngliche Stichprobengröße.

    Derselbe Ziehungsplan gilt für alle Vergleiche. Damit bleibt die Paarung auch
    zwischen den verschiedenen eingefrorenen Verfahren erhalten.
    """
    def __init__(self, groessen, wiederholungen=WIEDERHOLUNGEN, seed=BOOTSTRAP_SEED):
        if (not groessen or type(wiederholungen) is not int or wiederholungen < 2
                or any(type(n) is not int or n < 1 for n in groessen.values())):
            raise ValueError("Bootstrap braucht nichtleere Familien und mindestens zwei Wiederholungen.")
        self.groessen = dict(sorted(groessen.items()))
        self.wiederholungen, self.seed = wiederholungen, seed
        rng = random.Random(seed)
        typ = "H" if max(groessen.values()) <= 65536 else "I"
        self.ziehungen = [
            tuple(array(typ, (rng.randrange(n) for _ in range(n))) for n in self.groessen.values())
            for _ in range(wiederholungen)
        ]

    def intervall(self, differenzen, takte_pro_spur):
        if set(differenzen) != set(self.groessen) or any(
                len(differenzen[f]) != n for f, n in self.groessen.items()):
            raise ValueError("Bootstrap-Familien oder Spurenzahlen stimmen nicht.")
        if type(takte_pro_spur) is not int or takte_pro_spur < 1:
            raise ValueError("Positive Instrumenttakte pro Spur nötig.")
        if any(not math.isfinite(x) for werte in differenzen.values() for x in werte):
            raise ValueError("Nichtendliche Kostendifferenz.")
        werte = [differenzen[f] for f in self.groessen]
        nenner = sum(self.groessen.values()) * takte_pro_spur
        faktor = 1000 / nenner
        # Kosten sind ganzzahlig, erst die letzte Normierung verwendet Fließkomma.
        schaetzung = sum(sum(x) for x in werte) * faktor
        stichproben = [sum(sum(w[i] for i in indices) for w, indices in zip(werte, ziehung)) * faktor
                       for ziehung in self.ziehungen]
        return dict(differenz_pro_1000=schaetzung,
                    untergrenze=quantil(stichproben, .025), obergrenze=quantil(stichproben, .975))


def _ganze_zahl(wert, name):
    if type(wert) is int and wert >= 0:
        return wert
    if isinstance(wert, str) and wert.isascii() and wert.isdecimal():
        return int(wert)
    raise ValueError(f"Ungültiger ganzzahliger Zähler: {name}.")


def _manifest(ordner, satz):
    m = json.loads((ordner / "manifest.json").read_text(encoding="utf-8"))
    erwartet = ({"summen.csv", "auswahl.json", "familien-auswahl.csv"} if satz == "entwicklung"
                else {"summen.csv", "einzel.csv", "auswahl-pruefung.csv"})
    if (m.get("schema") != 1 or m.get("status") != "vollstaendig" or m.get("satz") != satz
            or set(m.get("ergebnisse", {})) != erwartet or m.get("familien") != list(k.s.FAMILIEN)):
        raise ValueError("Unvollständiges oder unbekanntes Eingabemanifest.")
    for name, digest in m["ergebnisse"].items():
        if k.sha(ordner / name) != digest:
            raise ValueError("Eine Ergebnisprüfsumme stimmt nicht.")
    if (type(m.get("anzahl")) is not int or m["anzahl"] < 1
            or type(m.get("seedstart")) is not int or m["seedstart"] < 0
            or m.get("spuren") != len(k.s.FAMILIEN) * m["anzahl"]):
        raise ValueError("Widersprüchliche Spurenzahlen im Manifest.")
    k.s.Einstellungen(**m["einstellungen"])
    return m


def _zeile(row):
    z = dict(row)
    for feld in (*k.FELDER, "halbwertszeit", "schwellenindex"):
        z[feld] = _ganze_zahl(z[feld], feld)
    for feld in ("spuren", "seed"):
        if feld in z:
            z[feld] = _ganze_zahl(z[feld], feld)
    c = k.konfig(z["modell"], z["halbwertszeit"], z["schwellenindex"])
    if z["konfiguration"] != c["konfiguration"] or float(z["schwelle"]) != z["schwellenindex"] / 20:
        raise ValueError("Widersprüchliche Konfigurationskennung.")
    if not (0 <= z["treffertakte"] <= z["warntakte"] <= z["auswertbar"] <= z["takte"]
            and z["treffertakte"] <= z["zieltakte"] <= z["auswertbar"]
            and z["fehlwarntakte"] == z["warntakte"] - z["treffertakte"]
            and z["verpasste_zieltakte"] == z["zieltakte"] - z["treffertakte"]
            and z["vorgewarnt"] + z["verpasst"] == z["phasen"]):
        raise ValueError("Widersprüchliche Rohzähler.")
    for name, wert in k.quoten(z).items():
        if name in z:
            if (wert is None and z[name] != "") or (wert is not None and float(z[name]) != wert):
                raise ValueError("Eine Quote stimmt nicht mit ihren Rohzählern überein.")
    return z


def _summen(ordner, meta, configs):
    erwartet = {(f, signal, c["konfiguration"]) for f in ("alle", *k.s.FAMILIEN)
                for signal, werte in configs.items() for c in werte}
    ergebnis = {}
    with (ordner / "summen.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            z = _zeile(row)
            key = z["familie"], z["signal"], z["konfiguration"]
            if key not in erwartet or key in ergebnis:
                raise ValueError("Unerwartete oder doppelte Summenzeile.")
            n = meta["anzahl"] * (len(k.s.FAMILIEN) if z["familie"] == "alle" else 1)
            if z["spuren"] != n or z["takte"] != n * (meta["einstellungen"]["takte"] - meta["einstellungen"]["horizont"]):
                raise ValueError("Summenzeile hat falsche Spurenzahl oder Taktzahl.")
            ergebnis[key] = z
    if set(ergebnis) != erwartet:
        raise ValueError("Fehlende Summenzeilen.")
    for signal, werte in configs.items():
        for c in werte:
            gesamt = ergebnis["alle", signal, c["konfiguration"]]
            for feld in k.FELDER:
                if gesamt[feld] != sum(ergebnis[f, signal, c["konfiguration"]][feld] for f in k.s.FAMILIEN):
                    raise ValueError("Gesamtsumme stimmt nicht mit den Familiensummen überein.")
    return ergebnis


def pruefe_eingaben(entwicklung, kontrolle):
    """Prüft Hashes, Auswahl, Splitdefinition und sämtliche Summenzeilen vor Auswertung."""
    dev, con = _manifest(entwicklung, "entwicklung"), _manifest(kontrolle, "kontrolle")
    auswahl = json.loads((entwicklung / "auswahl.json").read_text(encoding="utf-8"))
    configs = k.pruefe_auswahl(auswahl)
    if not (dev["quellhashes"] == con["quellhashes"] == auswahl["quellhashes"]
            and dev["einstellungen"] == con["einstellungen"] == auswahl["einstellungen"]
            and con.get("auswahl_sha256") == k.sha(entwicklung / "auswahl.json")
            and auswahl["entwicklung"]["summen_sha256"] == dev["ergebnisse"]["summen.csv"]
            and auswahl["entwicklung"]["seedstart"] == dev["seedstart"]
            and auswahl["entwicklung"]["anzahl"] == dev["anzahl"]
            and auswahl["kontrolle"]["seedstart"] == con["seedstart"]
            and auswahl["kontrolle"]["anzahl"] == con["anzahl"]):
        raise ValueError("Manifeste, Splitdefinition oder eingefrorene Auswahl widersprechen sich.")
    devconfigs = {signal: k.alle_konfigurationen() for signal, _, _ in k.s.SIGNALE}
    devsummen = _summen(entwicklung, dev, devconfigs)
    # Nur die vorhandene Entwicklungsentscheidung einschließlich Tiebreak bestätigen.
    # Kontrollwerte werden weder an waehle übergeben noch für eine neue Wahl genutzt.
    kandidaten = {(f,signal): [row for key,row in devsummen.items() if key[:2] == (f,signal)]
                  for f in ("alle",*k.s.FAMILIEN) for signal,_,_ in k.s.SIGNALE}
    for z in auswahl["auswahl"]:
        row = devsummen["alle", z["signal"], z["konfiguration"]]
        if z["entwicklungskosten"] != k.kostenzahl(row, z["kostenmodell"], z["verhaeltnis"]):
            raise ValueError("Eingefrorene Entwicklungskosten widersprechen den Summen.")
        beste = k.waehle(kandidaten["alle",z["signal"]],z["kostenmodell"],z["verhaeltnis"],z["suche"])
        if beste["konfiguration"] != z["konfiguration"]:
            raise ValueError("Eingefrorene Entwicklungsauswahl verletzt Optimum oder Tiebreak.")
    familien_erwartet = {(f,signal,art,r,suche) for f in k.s.FAMILIEN for signal,_,_ in k.s.SIGNALE
                         for art in k.KOSTEN for r in range(1,101) for suche in k.SUCHEN}
    familien_gesehen = set()
    with (entwicklung / "familien-auswahl.csv").open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            key = row["familie"],row["signal"],row["kostenmodell"],int(row["verhaeltnis"]),row["suche"]
            if key not in familien_erwartet or key in familien_gesehen:
                raise ValueError("Unerwartete Entwicklungsdiagnostik.")
            c = k.konfig(row["modell"],int(row["halbwertszeit"]),int(row["schwellenindex"]))
            if c["konfiguration"] != row["konfiguration"] or not k.passt(c,row["suche"]):
                raise ValueError("Ungültige Entwicklungskonfiguration.")
            kosten = k.kostenzahl(devsummen[key[0],key[1],row["konfiguration"]],key[2],key[3])
            if int(row["entwicklungskosten"]) != kosten:
                raise ValueError("Familienweise Entwicklungskosten widersprechen ihren Summen.")
            beste = k.waehle(kandidaten[key[0],key[1]],key[2],key[3],key[4])
            if beste["konfiguration"] != row["konfiguration"]:
                raise ValueError("Familienweise Entwicklungsauswahl verletzt Optimum oder Tiebreak.")
            familien_gesehen.add(key)
    if familien_gesehen != familien_erwartet:
        raise ValueError("Entwicklungsdiagnostik ist unvollständig.")
    consummen = _summen(kontrolle, con, configs)
    erwartet = {(f,z["signal"],z["kostenmodell"],z["verhaeltnis"],z["suche"]): z
                for f in ("alle",*k.s.FAMILIEN) for z in auswahl["auswahl"]}
    gesehen = set()
    with (kontrolle / "auswahl-pruefung.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["familie"],row["signal"],row["kostenmodell"],int(row["verhaeltnis"]),row["suche"])
            if key not in erwartet or key in gesehen:
                raise ValueError("Unerwartete Kontrollentscheidung.")
            z = erwartet[key]
            if any(str(row[n]) != str(wert) for n,wert in z.items()):
                raise ValueError("Eine Kontrollentscheidung verändert die eingefrorene Auswahl.")
            if int(row["kontrollkosten"]) != k.kostenzahl(consummen[key[0],z["signal"],z["konfiguration"]],
                                                         z["kostenmodell"],z["verhaeltnis"]):
                raise ValueError("Kontrollkosten stimmen nicht.")
            gesehen.add(key)
    if gesehen != set(erwartet):
        raise ValueError("Kontrollentscheidungen fehlen.")
    return dev, con, auswahl, devsummen, consummen, configs


def _default(suche):
    return "erbe-s12" if suche == "erbe_schwelle" else "startwert-h06-s12"


def lese_paare(kontrolle, meta, auswahl, summen, configs):
    """Rohwerte nur für die geplanten Intervalle halten; alle Kontrollsummen nachrechnen."""
    auswertungen = [z for z in auswahl["auswahl"] if z["verhaeltnis"] in VERHAELTNISSE]
    if len(auswertungen) != 72:
        raise ValueError("Genau 72 vorgeplante Vergleiche nötig.")
    benoetigt = {(z["signal"], c) for z in auswertungen for c in (z["konfiguration"], _default(z["suche"]))}
    n = meta["anzahl"]
    daten = {key: {f: [None] * n for f in k.s.FAMILIEN} for key in benoetigt}
    erwartet = {(f, signal, c["konfiguration"]) for f in k.s.FAMILIEN for signal, werte in configs.items() for c in werte}
    seen = {key: 0 for key in erwartet}
    roh_summen = {key: [0] * len(k.FELDER) for key in erwartet}
    spurmerkmale = {}
    takte = meta["einstellungen"]["takte"] - meta["einstellungen"]["horizont"]
    with (kontrolle / "einzel.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            z = _zeile(row)
            key = z["familie"], z["signal"], z["konfiguration"]
            index = z["seed"] - meta["seedstart"]
            if key not in erwartet or not 0 <= index < n or z["takte"] != takte:
                raise ValueError("Unerwartete Kontrollspur oder Instrumenttakte.")
            spurkey = z["familie"],z["signal"],z["seed"]
            merkmale = tuple(z[feld] for feld in ("takte","auswertbar","zieltakte","phasen"))
            if spurmerkmale.setdefault(spurkey,merkmale) != merkmale:
                raise ValueError("Gepaarte Konfigurationen beschreiben unterschiedliche Kontrollspuren.")
            bit = 1 << index
            if seen[key] & bit:
                raise ValueError("Doppelte Kontrollspur.")
            seen[key] |= bit
            for i, feld in enumerate(k.FELDER):
                roh_summen[key][i] += z[feld]
            if key[1:] in daten:
                daten[key[1:]][key[0]][index] = (z["fehlwarntakte"], z["verpasste_zieltakte"], z["verpasst"])
    voll = (1 << n) - 1
    for key in erwartet:
        if seen[key] != voll or any(roh_summen[key][i] != summen[key][feld] for i,feld in enumerate(k.FELDER)):
            raise ValueError("Kontrollspuren fehlen oder ihre Summe ist widersprüchlich.")
    return auswertungen, daten


def intervalle(auswertungen, daten, meta, wiederholungen=WIEDERHOLUNGEN):
    plan = BootstrapPlan({f: meta["anzahl"] for f in k.s.FAMILIEN}, wiederholungen)
    takte = meta["einstellungen"]["takte"] - meta["einstellungen"]["horizont"]
    for z in auswertungen:
        default = _default(z["suche"])
        a, b = daten[z["signal"],z["konfiguration"]], daten[z["signal"],default]
        feld = 1 if z["kostenmodell"] == "takt" else 2
        r = z["verhaeltnis"]
        differenzen = {f: [(x[0]-y[0]) + r*(x[feld]-y[feld]) for x,y in zip(a[f],b[f])]
                       for f in k.s.FAMILIEN}
        yield dict(signal=z["signal"], kostenmodell=z["kostenmodell"], verhaeltnis=r, suche=z["suche"],
                   konfiguration=z["konfiguration"], default=default, **plan.intervall(differenzen, takte),
                   spuren=sum(plan.groessen.values()), wiederholungen=wiederholungen, bootstrap_seed=BOOTSTRAP_SEED)


def halbwertsprofil(devsummen):
    for key, row in sorted(devsummen.items()):
        if row["schwellenindex"] != 12:
            continue
        # h1..24 und alle Baselines einschließlich festem Erbe; keine neue Wahl.
        yield dict(**row, **{f"kosten_{art}_r{r}_pro_1000": k.kostenzahl(row,art,r)*1000/row["takte"]
                            for art in k.KOSTEN for r in VERHAELTNISSE})


def schwellenwechsel(auswahlzeilen):
    """Nur Darstellung: benachbarte Preisverhältnisse derselben eingefrorenen Wahl."""
    gruppen = {}
    for row in auswahlzeilen:
        key = row["signal"],row["kostenmodell"],row["suche"]
        if (key[0] not in {s for s,_,_ in k.s.SIGNALE} or key[1] not in k.KOSTEN or key[2] not in k.SUCHEN
                or type(row["verhaeltnis"]) is not int or not 1 <= row["verhaeltnis"] <= 100):
            raise ValueError("Ungültige eingefrorene Auswahlgruppe.")
        c = k.konfig(row["modell"],row["halbwertszeit"],row["schwellenindex"])
        if row["konfiguration"] != c["konfiguration"] or not k.passt(c,row["suche"]):
            raise ValueError("Widersprüchliche eingefrorene Konfiguration.")
        gruppe = gruppen.setdefault(key,{})
        if row["verhaeltnis"] in gruppe:
            raise ValueError("Doppeltes eingefrorenes Kostenverhältnis.")
        gruppe[row["verhaeltnis"]] = c
    if not gruppen:
        raise ValueError("Keine eingefrorene Auswahl vorhanden.")
    for key,gruppe in sorted(gruppen.items()):
        if set(gruppe) != set(range(1,101)):
            raise ValueError("Eingefrorene Auswahl deckt nicht alle Kostenverhältnisse 1–100 ab.")
        bereich = None
        for r in range(1,101):
            c = gruppe[r]
            if bereich is not None and bereich["konfiguration"] == c["konfiguration"]:
                bereich["r_bis"] = r
                continue
            if bereich is not None:
                yield bereich
            bereich = dict(zip(("signal","kostenmodell","suche"),key),r_von=r,r_bis=r,
                           konfiguration=c["konfiguration"],modell=c["modell"],
                           halbwertszeit=c["halbwertszeit"],schwelle=c["schwellenindex"]/20)
        yield bereich


def bericht(dev, con, auswahl, devsummen, consummen, cis):
    prozent = lambda x: "–" if x is None else f"{100*x:.2f}".replace(".",",")+" %"
    zahl = lambda x: f"{x:.3f}".replace(".",",")
    signalnamen = {"temperatur": "Temperatur", "speicher": "Speicher", "schleife": "Schleife"}
    aus = {(z["signal"],z["kostenmodell"],z["verhaeltnis"],z["suche"]): z for z in auswahl["auswahl"]}
    ci = {(z["signal"],z["kostenmodell"],z["verhaeltnis"],z["suche"]): z for z in cis}
    zeilen = ["# Warnschwellen und Erb-Halbwertszeit: Kontrollbericht", "",
              "Die folgenden Einstellungen wurden ausschließlich auf Entwicklung gewählt und vor der",
              "Kontrolle eingefroren. Dieser Bericht wählt keine Konfiguration anhand der Kontrollwerte.", "",
              f"Entwicklung: {dev['spuren']} Spuren; unabhängige Kontrolle: {con['spuren']} Spuren.",
              f"Je Spur {con['einstellungen']['takte']} Instrumenttakte, davon die letzten {con['einstellungen']['horizont']} nur als bekannte Zukunft.",
              "Alle Warnkosten und Warnanteile zählen **sämtliche eigenen nichtkritischen Takte, auch OK**.",
              "Trefferquote = richtige Warntakte / Warntakte; Grundrate = Zieltakte / nichtkritische Takte.",
              "Kritische Phasen haben ein vollständiges Vorfenster; angrenzende kritische Takte bilden eine Phase.", "",
              "`takt`: r × verpasste Zieltakte + falsche Warntakte. `phase`: r × unangekündigte Phasen + falsche Warntakte.",
              "r bezeichnet jeweils den Preis des genannten Verlusts in Einheiten eines falschen Warntakts.",
              "Die Modelle sind nicht austauschbar. Kosten sind je 1.000 ausgewertete Instrumenttakte normiert,",
              "nicht je 1.000 nichtkritische Takte. Signalweise Kosten sind keine addierbaren Kosten einer gemeinsamen Geräteaktion.", "",
              "## Unsicherheit", "",
              "[intervalle.csv](intervalle.csv) enthält die 72 vorgeplanten Kostendifferenzen zur jeweiligen",
              "Defaultkonfiguration für r=1,10,100. Negative Werte bedeuten geringere gemessene Kosten.",
              "Je Vergleich 500 gepaarte Bootstrap-Ziehungen ganzer Spuren, getrennt innerhalb der vier Familien;",
              "die ursprüngliche Familiengröße bleibt erhalten. 2,5-/97,5-%-Quantile werden linear interpoliert.",
              "Das sind punktweise 95-%-Intervalle, kein gemeinsamer Signifikanztest über alle Vergleiche.",
              "Die Unsicherheit bezieht sich auf diesen synthetischen Generator; sie erfasst keine unbekannten realen Fehlerursachen.", "",
              "## Vorab festgelegte Kontrollvergleiche", ""]
    for signal, _, _ in k.s.SIGNALE:
        for art in k.KOSTEN:
            for r in VERHAELTNISSE:
                zeilen += [f"### {signalnamen[signal]} · {art} · r={r}", "",
                           "| Verfahren | h des Erbes | Schwelle | Kosten / 1.000 | Warnanteil | Trefferquote | Grundrate | Verpasst / Phasen |",
                           "|---|---:|---:|---:|---:|---:|---:|---:|"]
                reihen = [(aus[signal,art,r,suche]["konfiguration"], SUCHNAMEN[suche]) for suche in k.SUCHEN] + list(BASELINES)
                for c, label in reihen:
                    row = consummen["alle",signal,c]
                    h = "fest" if row["modell"] == "erbe" else str(row["halbwertszeit"]) if row["modell"] == "startwert" else "–"
                    schwelle = str(row["schwellenindex"]/20).replace(".",",") if row["modell"] in ("erbe","startwert") else "–"
                    q = k.quoten(row)
                    zeilen.append(f"| {label} | {h} | {schwelle} | {zahl(k.kostenzahl(row,art,r)*1000/row['takte'])} | "
                                  f"{prozent(q['warnanteil'])} | {prozent(q['trefferquote'])} | {prozent(q['grundrate'])} | "
                                  f"{row['verpasst']} / {row['phasen']} |")
                c = ci[signal,art,r,"startwert_gemeinsam"]
                zeilen += ["", f"Gemeinsames Raster gegenüber unverändertem Startwert: Kostendifferenz {zahl(c['differenz_pro_1000'])}",
                           f"je 1.000 Takte, punktweises Bootstrap-Intervall [{zahl(c['untergrenze'])}; {zahl(c['obergrenze'])}].", ""]
    zeilen += ["## Entwicklungsprofil und Grenzen", "",
               "[halbwertsprofil.csv](halbwertsprofil.csv) zeigt das gesamte Halbwertszeitraster 1–24 bei Schwelle 0,6,",
               "je Familie und gepoolt, einschließlich der Baselines. Dieses Profil ist Entwicklungsdiagnostik,",
               "keine weitere unabhängige Kontrollbestätigung. Ein Optimum hängt vom Signal, der Musterfamilie und",
               "vom gewählten Kostenbegriff ab; aus einer einzelnen besten Rasterzelle folgt kein allgemeiner Gewinner.",
               "Die vollständig eingefrorenen Entscheidungen für r=1…100 stehen im Entwicklungsordner in `auswahl.json`;",
               "[schwellenwechsel.csv](schwellenwechsel.csv) fasst aufeinanderfolgende Preisverhältnisse mit gleicher Wahl zusammen:",
               "je Signal, Kostenmodell und Suchraum stehen dort r_von, r_bis, Konfiguration, Erb-Halbwertszeit und Schwelle.",
               "Diese Bereiche stellen ausschließlich die bereits eingefrorene Auswahl dar; es wird nichts neu optimiert.",
               "Die zugehörigen Kontrollkosten stehen in `auswahl-pruefung.csv`. Preisgrenzen sind diskrete Entwicklungswechsel,",
               "keine universellen ökonomischen Grenzen. Kleinste Kostenunterschiede sind keine belastbare Geräteempfehlung.", "",
               "Alle künstlichen Ausfälle besitzen ein hohes Vorzeichen innerhalb des Horizonts. Das begünstigt die feste Regel.",
               "Es wurden keine Geräteaufnahmen zum Einstellen oder Prüfen verwendet. Physikalische Erwärmung, unbekannte Ausfälle",
               "ohne Vorzeichen und reale Energie-/RAM-/Aktionskosten sind nicht modelliert. Aufgaben 4–7 und die unabhängige",
               "Prüfung an echten Aufnahmen bleiben offen. Nach Betrachtung dieser Kontrolle ist sie für nachträgliche Anpassungen",
               "kein unberührter Kontrollsatz mehr.", "",
               "## Nachprüfung", "",
               "Vor Berichtserstellung wurden sämtliche Ergebnisprüfsummen, Splitdefinitionen und die unveränderte Auswahl geprüft.",
               "Optimum und Tiebreak jeder eingefrorenen Wahl wurden ausschließlich aus dem Entwicklungsraster bestätigt.",
               "Alle Kontrollsummen wurden aus den Einzelspuren neu addiert; jede erwartete Kombination aus Familie, Signal,",
               "Konfiguration und Seed kommt genau einmal vor. Taktzahl, nichtkritische Takte, Zieltakte und Phasen müssen",
               "für alle Konfigurationen desselben Seeds übereinstimmen. Die Bootstrap-Paarung verwendet dieselbe Spur beider Verfahren.",
               "Der Berichtsmanifest enthält nur neutrale Dateinamen, Hashes und Verfahrensparameter.", ""]
    return "\n".join(zeilen)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--entwicklung", type=Path, required=True)
    p.add_argument("--kontrolle", type=Path, required=True)
    p.add_argument("--ausgabe", type=Path, required=True)
    a = p.parse_args()
    try:
        dev, con, auswahl, devsummen, consummen, configs = pruefe_eingaben(a.entwicklung,a.kontrolle)
        auswertungen, daten = lese_paare(a.kontrolle,con,auswahl,consummen,configs)
        a.ausgabe.mkdir(parents=True,exist_ok=False)
        meta = dict(schema=1,status="unvollstaendig",bootstrap=dict(seed=BOOTSTRAP_SEED,wiederholungen=WIEDERHOLUNGEN,
                    einheit="ganze gepaarte Spur, innerhalb jeder Familie",quantile=[.025,.975],interpolation="linear"),
                    eingaben=dict(entwicklung_manifest=k.sha(a.entwicklung/"manifest.json"),
                                  kontrolle_manifest=k.sha(a.kontrolle/"manifest.json"),
                                  auswahl=k.sha(a.entwicklung/"auswahl.json")),
                    berichtscode_sha256=k.sha(Path(__file__)),python=list(sys.version_info[:3]))
        k.json_schreiben(a.ausgabe/"manifest.json",meta)
        cis = list(intervalle(auswertungen,daten,con))
        wechsel = list(schwellenwechsel(auswahl["auswahl"]))
        k.csv_schreiben(a.ausgabe/"intervalle.csv",cis)
        k.csv_schreiben(a.ausgabe/"halbwertsprofil.csv",halbwertsprofil(devsummen))
        k.csv_schreiben(a.ausgabe/"schwellenwechsel.csv",wechsel)
        (a.ausgabe/"KOSTEN-ERGEBNISSE.md").write_text(bericht(dev,con,auswahl,devsummen,consummen,cis),encoding="utf-8")
        meta.update(status="vollstaendig",intervalle=len(cis),schwellenbereiche=len(wechsel),kontrollspuren=con["spuren"],
                    ergebnisse={name:k.sha(a.ausgabe/name) for name in ("intervalle.csv","halbwertsprofil.csv","schwellenwechsel.csv","KOSTEN-ERGEBNISSE.md")})
        k.json_schreiben(a.ausgabe/"manifest.json",meta)
        print(f"Kostenbericht fertig: {len(cis)} Intervalle, {con['spuren']} gepaarte Kontrollspuren je Vergleich.")
    except (OSError,ValueError,KeyError,TypeError) as exc:
        # Keine privaten Dateipfade oder Eingabewerte in Protokolle übernehmen.
        p.exit(2,"Kostenbericht: Eingabedaten unvollständig, widersprüchlich oder Ausgabe nicht verfügbar.\n")


if __name__ == "__main__":
    main()
