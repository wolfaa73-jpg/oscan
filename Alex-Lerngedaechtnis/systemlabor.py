"""Vergleicht OSCan-Disposition bei wechselnden Systemzuständen; keine Hardwareänderung."""
import argparse
import csv
import hashlib
import json
import random
import statistics
from collections import Counter
from dataclasses import asdict
from html import escape
from pathlib import Path

from labor import FAMILIEN, generiere
from systemkern import Arbeitsprozesse, Systemkern, VERFAHREN
from versuch import lies_spur, messpunkte

# Fest vor diesem Vergleich gewählt; die Lernparameter bleiben die aus OSCan 0.4.
STARTSEED, ANZAHL, BOOTSTRAP = 2000, 50, 1000
KOSTEN = (1, 5, 10, 20)


def auswerten(spur, verfahren, mit_verlauf=False):
    system = Systemkern(verfahren)
    zahlen = Counter({k: 0 for k in (
        "beobachtungen", "ausfallbeginne", "beginn_unbekannt", "treffer", "fehlalarme",
        "verpasst", "offen", "negative_gelegenheiten", "reserve_runden", "reserve_genutzt",
        "reserve_unnoetig", "primaer", "ausgesetzt", "fehlende_takte")})
    letzter = None
    verlauf = []
    for takt, zustand in messpunkte(spur):
        plan = system.schritt(takt, zustand)
        zahlen["beobachtungen"] += 1
        anschluss = letzter is not None and takt == letzter.takt + 1
        beobachtbar = anschluss and letzter.zustand is not None and zustand is not None
        beginn = beobachtbar and zustand == "AUSFALL" and letzter.zustand != "AUSFALL"
        if letzter is not None:
            zahlen["fehlende_takte"] += takt - letzter.takt - 1
            if letzter.vorwarnung:
                zahlen["offen" if not beobachtbar else "treffer" if beginn else "fehlalarme"] += 1
            if beobachtbar and letzter.zustand != "AUSFALL" and not beginn:
                zahlen["negative_gelegenheiten"] += 1
            if letzter.reserve_fuer == takt:
                zahlen["reserve_runden"] += 1
                if zustand is not None and zustand != "AUSFALL":
                    zahlen["reserve_unnoetig"] += 1
        if beginn:
            zahlen["ausfallbeginne"] += 1
            zahlen["verpasst"] += int(not letzter.vorwarnung)
        elif zustand == "AUSFALL" and not beobachtbar:
            zahlen["beginn_unbekannt"] += 1
        zahlen[{"PRIMAER": "primaer", "RESERVE": "reserve_genutzt", "WARTEN": "ausgesetzt"}[plan.ziel]] += 1
        if mit_verlauf:
            verlauf.append(asdict(plan))
        letzter = plan
    if letzter is not None and letzter.vorwarnung:
        zahlen["offen"] += 1
    if not zahlen["beobachtungen"]:
        raise ValueError("Die Spur darf nicht leer sein.")
    n, tp, fp = zahlen["ausfallbeginne"], zahlen["treffer"], zahlen["fehlalarme"]
    ergebnis = dict(verfahren=verfahren, **zahlen,
                    recall=tp / n if n else None,
                    praezision=tp / (tp + fp) if tp + fp else None,
                    fehlalarmrate=fp / zahlen["negative_gelegenheiten"] if zahlen["negative_gelegenheiten"] else None,
                    vorwarnzeit_takte=1 if tp else None)
    if mit_verlauf:
        ergebnis["verlauf"] = verlauf
    return ergebnis


def wechselspur():
    """Deterministische Gegenprobe: Gefahr, Entwarnung, Rückkehr, je 40 Vorzeichen."""
    spur = []
    for gefahr in (True, False, True):
        for _ in range(40):
            spur.extend(("OK", "OK", "OK", "SCHWACH", "AUSFALL" if gefahr else "OK", "OK"))
    return spur


def anpassung(verfahren):
    verlauf = auswerten(wechselspur(), verfahren, True)["verlauf"]
    ergebnis = []
    for phase, erwartet in enumerate((True, False, True)):
        beginn = phase * 240 + 1
        signale = [p for p in verlauf[phase * 240:(phase + 1) * 240] if p["zustand"] == "SCHWACH"]
        treffer = next((i for i in range(len(signale) - 2)
                        if all(p["vorwarnung"] == erwartet for p in signale[i:i + 3])), None)
        ergebnis.append(dict(phase=("Gefahr", "Entwarnung", "Rückkehr")[phase],
                             erste_passende_serie_ab_signal=None if treffer is None else treffer + 1,
                             bestaetigt_nach_signalen=None if treffer is None else treffer + 3,
                             bestaetigt_nach_takten=None if treffer is None else signale[treffer + 2]["takt"] - beginn))
    return ergebnis


def quantil(werte, p):
    werte = sorted(werte)
    ort = (len(werte) - 1) * p
    i = int(ort)
    return werte[i] if i == len(werte) - 1 else werte[i] + (werte[i + 1] - werte[i]) * (ort - i)


def paarvergleich(zeilen, kosten, wiederholungen=BOOTSTRAP):
    """95%-Perzentilintervall, paarweises Resampling ganzer Spuren, nicht einzelner Takte."""
    gruppen = {}
    for z in zeilen:
        gruppen.setdefault((z["familie"], z["seed"]), {})[z["verfahren"]] = z
    ergebnis = []
    for familie in sorted({z["familie"] for z in zeilen}):
        paare = [gruppe for (f, _), gruppe in sorted(gruppen.items()) if f == familie]
        for verfahren in VERFAHREN:
            if verfahren == "fest":
                continue
            delta = []
            for gruppe in paare:
                a, b = gruppe[verfahren], gruppe["fest"]
                assert a["beobachtungen"] == b["beobachtungen"]
                delta.append(1000 * (a["reserve_runden"] - b["reserve_runden"]
                                      + kosten * (a["ausgesetzt"] - b["ausgesetzt"])) / a["beobachtungen"])
            rng = random.Random(20261105)
            mittel = [sum(rng.choice(delta) for _ in delta) / len(delta) for _ in range(wiederholungen)]
            ergebnis.append(dict(familie=familie, verfahren=verfahren, kosten_aussetzen=kosten,
                                 delta_pro_1000=statistics.mean(delta),
                                 intervall95=[quantil(mittel, .025), quantil(mittel, .975)]))
    return ergebnis


def kontrolle():
    zeilen, quellen = [], []
    for familie in FAMILIEN:
        for seed in range(STARTSEED, STARTSEED + ANZAHL):
            spur = generiere(familie, seed)
            quellen.append(dict(familie=familie, seed=seed,
                                sha256=hashlib.sha256("\n".join(spur).encode()).hexdigest()))
            for verfahren in VERFAHREN:
                zeilen.append(dict(familie=familie, seed=seed, **auswerten(spur, verfahren)))
    return dict(format="OSCan-Systemversuch-1", art="synthetischer Systemversuch",
                startseed=STARTSEED, anzahl_pro_familie=ANZAHL, bootstrap=BOOTSTRAP,
                parameter=dict(schwelle=.6, mindestbeleg=3, zeit_halbwert=24,
                               kontext_halbwert=6, erbe=3),
                quellen=quellen, ergebnisse=zeilen,
                kostenvergleich=[z for kosten in KOSTEN for z in paarvergleich(zeilen, kosten)],
                anpassung={v: anpassung(v) for v in VERFAHREN})


def prozessprobe():
    system = Systemkern("erbe")
    zahlen = Counter({"PRIMAER": 0, "RESERVE": 0, "WARTEN": 0})
    with Arbeitsprozesse() as arbeiter:
        for takt, zustand in enumerate(wechselspur(), 1):
            plan = system.schritt(takt, zustand)
            digest = arbeiter.ausfuehren(plan)
            assert (digest is None) == (plan.ziel == "WARTEN")
            zahlen[plan.ziel] += 1
    return dict(art="Zwei lokale Prozesse, simulierte Ressourcenverfügbarkeit",
                verfahren="erbe", auftraege=720, ergebnisse=dict(zahlen),
                gepruefte_antworten=zahlen["PRIMAER"] + zahlen["RESERVE"],
                pruefung="Auftragsnummer und SHA-256 jeder ausgeführten Arbeit verglichen")


def als_html(daten):
    zeilen = daten["ergebnisse"]
    tabellen = []
    for familie in dict.fromkeys(z["familie"] for z in zeilen):
        rows = []
        for v in VERFAHREN:
            teil = [z for z in zeilen if z["familie"] == familie and z["verfahren"] == v]
            werte = [sum(z[k] for z in teil) for k in ("treffer", "fehlalarme", "verpasst", "reserve_runden", "ausgesetzt")]
            rows.append(f'<tr><th>{escape(v)}</th>' + ''.join(f'<td>{n}</td>' for n in werte) + '</tr>')
        tabellen.append(f'<h3>{escape(familie)}</h3><div class="scroll"><table><thead><tr><th>Regel</th><th>Richtig vorher</th><th>Fehlalarm</th><th>Verpasst</th><th>Reservetakte</th><th>Ausgesetzt</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    kosten = []
    for z in daten.get("kostenvergleich", []):
        lo, hi = z["intervall95"]
        kosten.append(f'<tr><td>{escape(z["familie"])}</td><td>{z["verfahren"]}</td><td>{z["kosten_aussetzen"]}</td><td>{z["delta_pro_1000"]:.1f}</td><td>{lo:.1f} bis {hi:.1f}</td></tr>')
    anpass = []
    for v, phasen in daten.get("anpassung", {}).items():
        cells = ''.join('<td>' + (str(p["bestaetigt_nach_signalen"]) if p["bestaetigt_nach_signalen"] is not None else 'nicht erreicht') + '</td>' for p in phasen)
        anpass.append(f'<tr><th>{v}</th>{cells}</tr>')
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OSCan · Systementscheidungen prüfen</title><style>
    body{{font:17px/1.55 system-ui,sans-serif;background:#f6f6ee;color:#17342f;max-width:68rem;margin:3rem auto;padding:0 1.2rem}}h1,h2,h3{{line-height:1.2}}h1{{font-size:clamp(2rem,5vw,3.8rem);max-width:18ch}}h2{{margin-top:2.5rem}}p{{max-width:78ch}}.lead{{font-size:1.2rem}}.card{{padding:1.3rem;border:1px solid #b8c8bf;background:white;margin:1rem 0}}.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{padding:.65rem;border-bottom:1px solid #cbd6cf;text-align:right}}th:first-child,td:first-child{{text-align:left}}code{{font-size:.9em}}summary{{cursor:pointer;padding:1rem;background:#e5eee6}}a{{color:#056449}}</style></head><body><main>
    <p>OSCan · Laufzeitversuch auf Basis 0.4</p><h1>Was ändert das Gedächtnis am Handeln?</h1>
    <p class="lead">Ein Systemzustand wird zur Entscheidung: normal arbeiten, eine Reserve für den nächsten Takt einplanen oder bei Ausfall den Primär-Arbeiter sperren.</p>
    <div class="card"><strong>Beobachtung → Gedächtnis → Vorschlag → fester Disponent → Arbeiter</strong><p>Die Lernregel schlägt Vorsorge vor. Der feste Ablauf begrenzt die Aktion auf einen Auftrag und eine Reservierung je Takt. Ein beobachteter Ausfall sperrt den Primär-Arbeiter bei jeder Regel. Fehlendes Wissen und Taktlücken entwerten alte Reservierungen.</p></div>
    <p><strong>Prüfstand:</strong> {escape(daten["art"])}. Sechs Verfahren sehen dieselben Zustände in derselben Reihenfolge. Die Generatorphasen sind nur der Auswertung bekannt. Im Kontrolllauf: 300 Spuren, 144.000 Zustände, 864.000 Regelentscheidungen, Seeds 2000–2049. Die Lernparameter aus 0.4 bleiben unverändert.</p>
    <p><strong>Geltungsbereich:</strong> ausführbarer Laufzeitprototyp auf dem vorhandenen Betriebssystem. Die Tabellen modellieren Ressourcenverfügbarkeit. Sie belegen keine Echtzeit-, Energie- oder Leistungsgewinne eines vollständigen Betriebssystems. Der separate Prozessversuch prüft echte lokale Arbeitsaufträge.</p>
    <h2>Vorwarnung und Ressourcennutzung</h2><p>Jeder korrekte Voralarm liegt genau einen logischen Takt vor dem Ausfallbeginn. Mehr Vorwarnzeit lernt dieser Kern noch nicht. Fehlalarm bedeutet: Der direkt folgende bekannte Takt beginnt keinen Ausfall. Lücken und ein offenes Ende bleiben unbewertet. „Ausgesetzt“ zählt Modellaufträge ohne verfügbaren Arbeiter. Die Reserve gilt als zuverlässig und nach einem Takt bereit.</p>
    {''.join(tabellen)}
    <h2>Wie schnell folgt das System einem Bedeutungswechsel?</h2><p>Zusätzliche deterministische Gegenprobe: 40 gefährliche, 40 harmlose, dann wieder 40 gefährliche schwache Signale. Gezählt werden Signale bis zur ersten Serie von drei passenden Entscheidungen innerhalb der Phase. Dies ist eine operative Messdefinition, kein Beweis dauerhafter Anpassung.</p>
    <div class="scroll"><table><thead><tr><th>Regel</th><th>Gefahr</th><th>Entwarnung</th><th>Rückkehr</th></tr></thead><tbody>{''.join(anpass)}</tbody></table></div>
    <h2>Wann lohnt sich Vorsorge?</h2><p>Modellkosten = Reservetakte + r × ausgesetzte Aufträge. Vier ausdrücklich angenommene Werte für r, keine nachträgliche Auswahl eines Gewinners. Negative Differenzen bedeuten geringere Modellkosten als die feste SCHWACH-Regel. Die 95%-Bootstrap-Intervalle resampeln 50 vollständige, gepaarte Spuren je Familie 1.000-mal. Sie gelten nur innerhalb des jeweiligen Generatormodells; die vielen Tabellen sind keine korrigierten Signifikanztests.</p>
    <details><summary>Alle Kostenvergleiche und Intervalle anzeigen</summary><div class="scroll"><table><thead><tr><th>Familie</th><th>Regel</th><th>r</th><th>Δ je 1.000 Takte</th><th>95%-Intervall</th></tr></thead><tbody>{''.join(kosten)}</tbody></table></div></details>
    <h2>Weiterarbeiten</h2><p>Start, Annahmen und nächste Integrationsschritte stehen in <a href="SYSTEM-UEBERGABE.md">SYSTEM-UEBERGABE.md</a>. Der <a href="Verbund.html">Verbundversuch</a> prüft zusätzlich Knotenidentität, Sitzungen und veraltete Nachrichten.</p>
    <p><code>python3 systemlabor.py kontrolle --json beispiele/system-ergebnis.json --csv beispiele/system-kontrolle.csv --bericht Systembericht.html</code></p>
    </main></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="aktion", required=True)
    k = sub.add_parser("kontrolle", help="Alle sechs Familien auf zusätzlichen Seeds vergleichen")
    k.add_argument("--bericht", type=Path)
    k.add_argument("--csv", type=Path)
    k.add_argument("--json", type=Path)
    p = sub.add_parser("prozesse", help="Disposition mit zwei wirklichen lokalen Arbeitern prüfen")
    p.add_argument("--json", type=Path)
    s = sub.add_parser("spur", help="Eigene Zustandsfolge chronologisch durchspielen")
    s.add_argument("datei", type=Path)
    s.add_argument("--json", type=Path)
    args = parser.parse_args()
    try:
        if args.aktion == "kontrolle":
            daten = kontrolle()
            if args.bericht:
                args.bericht.write_text(als_html(daten), encoding="utf-8")
            if args.csv:
                with args.csv.open("w", encoding="utf-8", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(daten["ergebnisse"][0]), lineterminator="\n")
                    w.writeheader()
                    w.writerows(daten["ergebnisse"])
            print(f'{len(daten["quellen"])} Spuren, {len(daten["ergebnisse"])} Einzelauswertungen.')
        elif args.aktion == "prozesse":
            daten = prozessprobe()
            print(json.dumps(daten, ensure_ascii=False, indent=2))
        else:
            spur = lies_spur(args.datei)
            daten = dict(art="Eingelesene Zustandsfolge; Herkunft vom Nutzer zu dokumentieren",
                         sha256=hashlib.sha256(args.datei.read_bytes()).hexdigest(),
                         ergebnisse=[auswerten(spur, v, True) for v in VERFAHREN])
            print(json.dumps([{k: w for k, w in z.items() if k != "verlauf"} for z in daten["ergebnisse"]], ensure_ascii=False, indent=2))
        if args.json:
            args.json.write_text(json.dumps(daten, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    except (ValueError, OSError, csv.Error, EOFError) as fehler:
        parser.exit(2, f"Systemversuch: {fehler}\n")


if __name__ == "__main__":
    main()
