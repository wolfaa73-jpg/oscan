"""Reproduzierbarer Vergleich mit sechs Familien synthetischer Messspuren."""
import argparse
import csv
import random
from collections import defaultdict
from html import escape
from pathlib import Path

from kern import Erbgedaechtnis, Gedaechtnis, Kontextgedaechtnis
from versuch import beispielspur, durchlauf, vergleiche

FAMILIEN = ("Stabil", "Bedeutungswechsel", "Rückkehr", "Selten", "Ohne Vorzeichen", "Stille und Wechsel")
ANZAHL = 20
TAKTE = 480
ERBSTUFEN = (0, 1, 2, 3, 6, 12)
ZEITSTUFEN = (12, 24, 48, 96, 192)
KONTEXTSTUFEN = (3, 6, 12, 24)


def generiere(familie, seed):
    """Die Generatoren kennen ihre Phasen, der Knoten sieht nur den aktuellen Zustand."""
    if familie not in FAMILIEN:
        raise ValueError(f"Unbekannte Familie: {familie}")
    rng = random.Random(seed)
    vorher = "OK"
    spur = []
    for takt in range(TAKTE):
        # Zwei Ziehungen pro Takt halten die Zufallsfolgen paarweise vergleichbar.
        ereignis, signal = rng.random(), rng.random()
        if familie == "Ohne Vorzeichen":
            risiko = 0.10
        else:
            bei_schwach = 0.85
            if familie == "Bedeutungswechsel" and takt >= TAKTE // 2:
                bei_schwach = 0.04
            if familie == "Rückkehr" and TAKTE // 3 <= takt < 2 * TAKTE // 3:
                bei_schwach = 0.04
            if familie == "Stille und Wechsel" and takt >= 2 * TAKTE // 3:
                bei_schwach = 0.04
            risiko = bei_schwach if vorher == "SCHWACH" else 0.015
        if ereignis < risiko:
            jetzt = "AUSFALL"
        else:
            schwach_rate = 0.025 if familie == "Selten" else 0.28
            if familie == "Stille und Wechsel" and TAKTE // 3 <= takt < 2 * TAKTE // 3:
                schwach_rate = 0.0
            jetzt = "SCHWACH" if signal < schwach_rate else "OK"
        spur.append(jetzt)
        vorher = jetzt
    return spur


def messreihe(startseed=1000):
    for familie in FAMILIEN:
        for seed in range(startseed, startseed + ANZAHL):
            for b in vergleiche(generiere(familie, seed)):
                yield dict(familie=familie, seed=seed, verfahren=b.name, treffer=b.treffer,
                           fehlwarnungen=b.fehlalarme, verpasst=b.ohne_vorwarnung,
                           offen=b.offen, sofort=b.sofortmeldungen,
                           beginn_unbekannt=b.beginn_unbekannt, nutzbytes=b.nutzbytes)


def summiere(zeilen):
    summen = defaultdict(lambda: [0, 0, 0, 0])
    for z in zeilen:
        werte = summen[z["familie"], z["verfahren"]]
        for i, feld in enumerate(("treffer", "fehlwarnungen", "verpasst", "nutzbytes")):
            werte[i] += z[feld]
    return summen


def vergleichsreihe(verfahren, startseed=1000):
    """Dieselben Spuren für Paare aus Bezeichnung und Gedächtnisfabrik, summiert je Familie."""
    for bezeichnung, fabrik in verfahren:
        for familie in FAMILIEN:
            werte = [0, 0, 0]
            for seed in range(startseed, startseed + ANZAHL):
                b = durchlauf(generiere(familie, seed), str(bezeichnung), fabrik())
                for i, wert in enumerate((b.treffer, b.fehlalarme, b.ohne_vorwarnung)):
                    werte[i] += wert
            yield bezeichnung, familie, werte


def erbe_reihe(startseed=1000):
    """Nur die Zahl fester Beobachtungen SCHWACH -> AUSFALL ändert sich."""
    return vergleichsreihe([(s, lambda s=s: Erbgedaechtnis({("SCHWACH", "AUSFALL"): s}))
                            for s in ERBSTUFEN], startseed)


def halbwertszeit_reihe(startseed=1000):
    """Zeit- und Kontextregel mit anderen Halbwertszeiten. 24 und 6 sind die Standardregeln."""
    return vergleichsreihe([(f"Zeit {h}", lambda h=h: Gedaechtnis(h)) for h in ZEITSTUFEN]
                           + [(f"Kontext {h}", lambda h=h: Kontextgedaechtnis(h)) for h in KONTEXTSTUFEN],
                           startseed)


def verlauf_svg():
    log = []
    vergleiche(beispielspur(), lambda t, z, p, n, w: log.append((t, z, p, w)))
    def x(t):
        return 46 + (t - 1) * 680 / 239
    def y(p):
        return 150 - 108 * p
    schwach = [r for r in log if r[1] == "SCHWACH"]
    punkte = " ".join(f"{x(t):.1f},{y(p):.1f}" for t, _, p, _ in schwach)
    elemente = [f'<polyline points="{punkte}" fill="none" stroke="#184c79" stroke-width="2"/>']
    for t, _, p, w in schwach:
        if w:
            elemente.append(f'<circle cx="{x(t):.1f}" cy="{y(p):.1f}" r="4" fill="#184c79"><title>Warnung in Takt {t}</title></circle>')
    for t, z, _, _ in log:
        if z == "AUSFALL":
            elemente.append(f'<path d="M{x(t):.1f} 171v10" stroke="#983817" stroke-width="3"><title>Ausfall in Takt {t}</title></path>')
    return f'''<svg viewBox="0 0 760 215" role="img" aria-labelledby="grafiktitel beschreibung">
    <title id="grafiktitel">Gedächtnis auf der ursprünglichen Demo</title>
    <desc id="beschreibung">Die Linie verbindet Schätzungen bei schwachem Signal. Der erste Warnpunkt liegt bei Takt 34, ab Takt 136 endet die Warnung.</desc>
    <rect x="{x(121)}" y="25" width="{x(240)-x(121)}" height="160" fill="#eef3ed"/>
    <text x="46" y="19">Häufiger Vorbote</text><text x="{x(121)+5}" y="19">Schwaches Signal verliert seine Bedeutung</text>
    <path d="M46 {y(.6)}H726" stroke="#65756d" stroke-dasharray="5 5"/>
    <text x="4" y="{y(.6)+4}">60 %</text><text x="4" y="154">0 %</text>
    {''.join(elemente)}<text x="46" y="203">Takt 1</text><text x="{x(121)}" y="203">121</text><text x="700" y="203">240</text></svg>'''


def als_html(summen, reihe, startseed):
    erbzeilen = defaultdict(str)
    for staerke, _familie, (treffer, fehl, _verpasst) in reihe:
        erbzeilen[staerke] += f"<td>{treffer:,} / {fehl:,}</td>".replace(",", " ")
    erbtabelle = "".join(f'<tr><th scope="row">{s}</th>{z}</tr>' for s, z in erbzeilen.items())
    erbkopf = "".join(f"<th>{f}</th>" for f in FAMILIEN)
    tabellen = []
    for familie in FAMILIEN:
        zeilen = []
        for (f, name), werte in summen.items():
            if f == familie:
                zellen = "".join(f"<td>{wert:,}</td>".replace(",", " ") for wert in werte)
                zeilen.append(f'<tr><th scope="row">{escape(name)}</th>{zellen}</tr>')
        tabellen.append(f"<h3>{familie}</h3><table><thead><tr><th>Verfahren</th><th>Richtig vorher</th>"
                        "<th>Fehlwarnungen</th><th>Verpasst</th><th>Nutzbytes</th></tr></thead>"
                        f"<tbody>{''.join(zeilen)}</tbody></table>")
    return f'''<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Alex’ Lernlabor · Versuchsbericht</title><style>
    body{{font:17px/1.5 system-ui,sans-serif;color:#172d33;background:#f9faf7;max-width:54rem;margin:3rem auto;padding:0 1rem}}
    h1,h2,h3{{line-height:1.2}} h2{{margin-top:2.2rem}} p{{max-width:72ch}}
    figure{{margin:1rem 0;background:white;padding:1rem;border:1px solid #cfd9d1}}
    svg{{width:100%;height:auto;font:12px system-ui}} figcaption,footer{{font-size:.9rem}}
    table{{width:100%;border-collapse:collapse;background:white;font-size:.9rem}} td,th{{padding:.42rem;text-align:right;border-bottom:1px solid #cbd5cf}}
    th:first-child{{text-align:left}} section{{overflow-x:auto}} code{{font-size:.9em}}</style></head><body>
    <main><p>Alex’ Lernlabor · Version 0.3</p><h1>Wann hilft es, zu vergessen?</h1>
    <p>Ein Knoten schätzt nach jedem Signal, ob der Sensor im nächsten Takt ausfällt.
    Für die ursprüngliche Demo sinken die Fehlwarnungen durch Verblassen von elf auf fünf.
    Die richtigen Vorwarnungen sinken von 13 auf zwölf. Mit einem kleinen festen Erbe warnt der Knoten
    so oft richtig wie die feste Regel, 16-mal, und gibt acht statt 24 Fehlwarnungen.</p>
    <figure>{verlauf_svg()}<figcaption>Die Linie zeigt den gewichteten Ausfallanteil nach einem schwachen Signal.
    Punkte kennzeichnen tatsächlich ausgegebene Warnungen. Die Striche darunter markieren beobachtete Ausfälle.
    Zur Warnschwelle von 60 % kommen mindestens drei gewichtete Beobachtungen hinzu.</figcaption></figure>
    <h2>Sechs Belastungsproben</h2><p>Jeder Block umfasst {ANZAHL} synthetische Spuren à {TAKTE} Takte.
    Die Startwerte reichen von {startseed} bis {startseed+ANZAHL-1}. Jeder Lauf beginnt leer. Alle Verfahren bekommen dieselben Beobachtungen, die Warnregeln bleiben gleich.
    „Verpasst“ zählt beobachtete Ausfallbeginne ohne Vorwarnung. Ein bereits beim Start laufender Ausfall bleibt davon ausgenommen.</p>
    <p>Stabil hält den Zusammenhang konstant. Bedeutungswechsel entwertet ihn auf halber Strecke.
    Bei Rückkehr gilt er im letzten Drittel erneut. Selten enthält nur wenige schwache Signale.
    Ohne Vorzeichen entstehen die Ausfälle unabhängig vom vorherigen Zustand. Bei Stille und Wechsel fehlt das schwache Signal im mittleren Drittel und verliert danach seine Vorhersagekraft. Die Zusatzregel „Verblassen je Kontext“ halbiert alte Belege nach sechs neuen Beobachtungen desselben Ausgangszustands.
    „Erbe und Kontext“ rechnet zusätzlich mit drei festen Beobachtungen „SCHWACH → AUSFALL“. Sie verblassen nie, eigene Erfahrung kann sie überstimmen.</p>
    <section>{''.join(tabellen)}</section>
    <h2>Wie viel Erbe ist genug?</h2><p>Dieselben Spuren mit „Erbe und Kontext“. Nur die Zahl der festen Beobachtungen ändert sich.
    Jede Zelle zeigt richtige Vorwarnungen / Fehlwarnungen. Null entspricht „Verblassen je Kontext“.
    Drei ist der Mindestbeleg einer Warnung und die Einstellung des Verfahrens. Wo sich die Bedeutung ändert, bringt mehr Erbe
    etwas mehr Vorwarnungen und deutlich mehr Fehlwarnungen. Ohne Vorzeichen wird es zum Vorurteil.</p>
    <section><table><thead><tr><th>Erbe</th>{erbkopf}</tr></thead>
    <tbody>{erbtabelle}</tbody></table></section><footer><p>Reproduzieren mit <code>python3 labor.py --satz {'kontrolle' if startseed == 1000 else 'entwicklung'} --bericht Bericht.html</code>.
    Ergebnisse je Spur lassen sich mit <code>--csv</code> exportieren, die Erbe-Reihe mit <code>--erbe-reihe</code> im Terminal ausgeben. Gezählt werden Modell-Nutzbytes pro Nachricht. Funkverkehr und Energieverbrauch müssen am Gerät gemessen werden.</p></footer></main></body></html>'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bericht", type=Path)
    p.add_argument("--csv", type=Path, help="Alle Verfahren je Familie und Seed")
    p.add_argument("--demo-spur", type=Path, help="Dieselbe 240-Takt-Spur für den seriellen Prüfstand")
    p.add_argument("--satz", choices=("entwicklung", "kontrolle"), default="kontrolle")
    p.add_argument("--erbe-reihe", action="store_true", help="Erbe von 0 bis 12 festen Beobachtungen vergleichen")
    p.add_argument("--halbwertszeiten", action="store_true", help="Zeit- und Kontextregel mit anderen Halbwertszeiten")
    args = p.parse_args()
    startseed = 1000 if args.satz == "kontrolle" else 0
    zeilen = list(messreihe(startseed))
    summen = summiere(zeilen)
    reihe = list(erbe_reihe(startseed)) if args.bericht or args.erbe_reihe else []
    if args.bericht:
        args.bericht.write_text(als_html(summen, reihe, startseed), encoding="utf-8")
    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(zeilen[0]))
            writer.writeheader()
            writer.writerows(zeilen)
    if args.demo_spur:
        with args.demo_spur.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(("takt", "zustand"))
            writer.writerows(enumerate(beispielspur(), start=1))
    print("Familie | Verfahren | Richtig vorher | Fehlwarnungen | Verpasst | Nutzbytes")
    for (familie, name), werte in summen.items():
        print(" | ".join(map(str, [familie, name, *werte])))
    if args.erbe_reihe:
        print("\nErbe | Familie | Richtig vorher | Fehlwarnungen | Verpasst")
        for staerke, familie, werte in reihe:
            print(" | ".join(map(str, [staerke, familie, *werte])))
    if args.halbwertszeiten:
        print("\nRegel und Halbwertszeit | Familie | Richtig vorher | Fehlwarnungen | Verpasst")
        for regel, familie, werte in halbwertszeit_reihe(startseed):
            print(" | ".join(map(str, [regel, familie, *werte])))


if __name__ == "__main__":
    main()
