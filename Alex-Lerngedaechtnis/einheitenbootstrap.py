"""Gepaarter Bootstrap ganzer Durchgänge; keine 24-Stunden-Auswertung.

Definitionen und Grenzen stehen in EINHEITEN-BOOTSTRAP-PLAN.md.
"""
import argparse
import csv
import hashlib
import json
import math
import random
from pathlib import Path

import signallabor as s
from koerper import BREMSE, LECK, Grenzen, pruefen
from vokabular import SIGNALE, binnen_vor, grob, kritisch, koerperwort, laeufe, phasen, stufen_je_signal

ZAHLEN = ('takte', 'auswertbar', 'warntakte', 'treffertakte', 'zieltakte', 'phasen', 'vorgewarnt')
MASSE = ('warnanteil', 'trefferquote', 'grundrate')
ARTEN = {'leck': 'speicher', 'hitze': 'temperatur', 'bremse': 'schleife'}
WIEDERHOLUNGEN = 2000
BOOTSTRAP_SEED = 20261106


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quotient(row, name):
    a, b = {'warnanteil': ('warntakte', 'auswertbar'),
            'trefferquote': ('treffertakte', 'warntakte'),
            'grundrate': ('zieltakte', 'auswertbar')}[name]
    return row[a] / row[b] if row[b] else None


def addiere(rows):
    rows = list(rows)
    return {k: sum(r[k] for r in rows) for k in ZAHLEN}


def quantil(werte, p):
    if not werte:
        raise ValueError('Leere Quantilstichprobe.')
    w = sorted(werte)
    pos = (len(w) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    return w[lo] + (w[hi] - w[lo]) * (pos - lo)


def pruefe_paare(a, b):
    if len(a) != len(b) or not a:
        raise ValueError('Keine vollständig gepaarten Einheiten.')
    for x, y in zip(a, b):
        for r in (x, y):
            if set(r) != set(ZAHLEN) or any(type(r[k]) is not int or r[k] < 0 for k in ZAHLEN):
                raise ValueError('Ungültige Einheitenzähler.')
            if not (r['treffertakte'] <= r['warntakte'] <= r['auswertbar'] <= r['takte']
                    and r['treffertakte'] <= r['zieltakte'] <= r['auswertbar']
                    and r['vorgewarnt'] <= r['phasen']):
                raise ValueError('Widersprüchliche Einheitenzähler.')
        if any(x[k] != y[k] for k in ('takte', 'auswertbar', 'zieltakte', 'phasen')):
            raise ValueError('Unterschiedliche Aufgaben in einem Einheitenpaar.')


def bootstrap(a, b, modus='einzel', wiederholungen=WIEDERHOLUNGEN, seed=BOOTSTRAP_SEED):
    """Verhältnisse gepaarter Zählersummen; keine Takte oder Rohfolgen resampeln."""
    pruefe_paare(a, b)
    if modus not in ('einzel', 'block8') or type(wiederholungen) is not int or wiederholungen < 1:
        raise ValueError('Ungültiger Bootstrapmodus.')
    n = len(a)
    minimum = 2 if modus == 'einzel' else 16
    sa, sb = addiere(a), addiere(b)
    result = {}
    for name in MASSE:
        va, vb = quotient(sa, name), quotient(sb, name)
        result[name] = dict(punkt_a=va, punkt_b=vb, differenz=None if va is None or vb is None else va-vb,
                            unten=None, oben=None, definiert=0, wiederholungen=wiederholungen,
                            einheiten=n, status='zu_wenige_einheiten')
    if n < minimum:
        return result
    rng = random.Random(seed)
    werte = {name: [] for name in MASSE}
    for _ in range(wiederholungen):
        if modus == 'einzel':
            indices = [rng.randrange(n) for _ in range(n)]
        else:
            indices = []
            while len(indices) < n:
                start = rng.randrange(n)
                indices.extend((start + j) % n for j in range(min(8, n-len(indices))))
        za, zb = addiere(a[i] for i in indices), addiere(b[i] for i in indices)
        for name in MASSE:
            va, vb = quotient(za, name), quotient(zb, name)
            if va is not None and vb is not None:
                werte[name].append(va - vb)
    for name in MASSE:
        w = werte[name]
        result[name].update(definiert=len(w), status='vollstaendig' if len(w) == wiederholungen else 'undefinierte_ziehungen')
        if len(w) == wiederholungen:
            result[name].update(unten=quantil(w, 0.025), oben=quantil(w, 0.975))
    return result


def ganze_einheiten(werte, stufen, horizont):
    """[von,bis) für ganze beobachtete Zyklen, mit vollständiger Zukunft."""
    ende = len(werte) - horizont
    starts = {}
    for art, bit in (('leck', LECK), ('bremse', BREMSE)):
        starts[art] = [t for t in range(1, len(werte))
                       if werte[t]['reiz'] & bit and not werte[t-1]['reiz'] & bit]
    starts['hitze'] = [a for a, _ in laeufe([z['temperatur'] != 'OK' for z in stufen], 10) if a > 0]
    return {art: [(a, b) for a, b in zip(starts[art], starts[art][1:]) if b <= ende]
            for art in ARTEN}


def zaehlfunktion(woerter, warn, auswertbar, horizont):
    """Feste Originalfolge einmal beschriften; Grenzen ändern keine Zielbezüge."""
    if len(woerter) != len(warn) or len(warn) != len(auswertbar):
        raise ValueError('Ungültige Bewertungsfolge.')
    ziel = binnen_vor([kritisch(w) for w in woerter], horizont)
    beginne = {a for a, _ in phasen(woerter, 10) if a >= horizont}
    gewarnt = {a for a in beginne if any(warn[t] and not kritisch(woerter[t])
                                       for t in range(a-horizont, a))}
    prefix = {k: [0] for k in ZAHLEN}
    for t in range(len(warn)):
        values = (1, bool(auswertbar[t]), bool(auswertbar[t] and warn[t]),
                  bool(auswertbar[t] and warn[t] and t in ziel),
                  bool(auswertbar[t] and t in ziel), t in beginne, t in gewarnt)
        for k, value in zip(ZAHLEN, values):
            prefix[k].append(prefix[k][-1] + value)
    def count(von, bis):
        if not 0 <= von <= bis <= len(warn):
            raise ValueError('Ungültiger Bewertungsbereich.')
        return {k: v[bis] - v[von] for k, v in prefix.items()}
    return count


def zaehle(woerter, warn, auswertbar, horizont, von, bis):
    return zaehlfunktion(woerter, warn, auswertbar, horizont)(von, bis)


def vergleichsverfahren(stufen, horizont, geraet=None):
    e = s.Einstellungen(takte=len(stufen), horizont=horizont)
    out = {}
    for sicht, name, warn, je in s.verfahren(stufen, e):
        if sicht == 'grob' and name == 'Feste Regel':
            out['Feste Regel'] = warn, je
        if name in ('Festes Erbe', 'Startwert'):
            out[('Grob' if sicht == 'grob' else 'Je Signal') + (', Erbe fest' if name == 'Festes Erbe' else ', Startwert')] = warn, je
    gesamt = s.schwerstes(stufen)
    out['Immer warnen (eigene Signalreferenz)'] = [not kritisch(w) for w in gesamt], {
        signal: [not kritisch(z[signal]) for z in stufen] for signal, _, _ in SIGNALE}
    out['Nie warnen'] = [False] * len(stufen), {signal: [False] * len(stufen) for signal, _, _ in SIGNALE}
    if geraet is not None:
        out['Gerät'] = list(geraet), {signal: list(geraet) for signal, _, _ in SIGNALE}
    return out


def auswerten(werte, stufen, horizont, geraet=None, wiederholungen=WIEDERHOLUNGEN):
    modelle = vergleichsverfahren(stufen, horizont, geraet)
    gesamt = s.schwerstes(stufen)
    masks = {'gesamt': [not kritisch(w) for w in gesamt]}
    woerter = {'gesamt': gesamt}
    for signal, hoch, _ in SIGNALE:
        woerter[signal] = [z[signal] for z in stufen]
        masks[signal] = [w == hoch for w in woerter[signal]]
    ganz, punkte, intervalle, units = [], [], [], []
    grenzen = ganze_einheiten(werte, stufen, horizont)
    for signal in woerter:
        for name, (warn, je) in modelle.items():
            z = zaehle(woerter[signal], warn if signal == 'gesamt' else je[signal], masks[signal],
                       horizont, 0, len(werte))
            ganz.append(dict(signal=signal, verfahren=name, **z, **{m: quotient(z, m) for m in MASSE}))
    for art, bounds in grenzen.items():
        for nummer, (a, b) in enumerate(bounds, 1):
            units.append(dict(art=art, nummer=nummer, von_takt=werte[a]['takt'],
                              bis_takt_inklusiv=werte[b-1]['takt'], takte=b-a))
        for signal in ('gesamt', ARTEN[art]):
            per = {}
            for name, (warn, je) in modelle.items():
                w = warn if signal == 'gesamt' else je[signal]
                count = zaehlfunktion(woerter[signal], w, masks[signal], horizont)
                per[name] = [count(a, b) for a, b in bounds]
                z = addiere(per[name])
                punkte.append(dict(art=art, signal=signal, verfahren=name, einheiten=len(bounds),
                                   **z, **{m: quotient(z, m) for m in MASSE}))
            if not bounds:
                continue
            for name in per:
                refs = ['Feste Regel']
                if name == 'Je Signal, Startwert':
                    refs.append('Je Signal, Erbe fest')
                if name == 'Gerät':
                    refs.append('Grob, Erbe fest')
                for ref in refs:
                    for modus in ('einzel', 'block8'):
                        for mass, z in bootstrap(per[name], per[ref], modus, wiederholungen).items():
                            intervalle.append(dict(art=art, signal=signal, verfahren=name,
                                                   referenz=ref, modus=modus, mass=mass, **z))
    return ganz, punkte, intervalle, units


def csv_schreiben(path, rows, felder=None):
    with path.open('x', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=felder or list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def bericht(ganz, punkte, profil):
    prozent = lambda v: '—' if v is None else f'{100*v:.2f} %'
    text = ['# Bootstrap ganzer Einheiten', '', f'Profil: {profil}. Maßgeblich ist die Taktwertung.',
            'Keine unabhängige Bestätigung: Wiederziehen einer bereits ausgewerteten Aufnahme.',
            'Alle Warnungen wurden auf der ursprünglichen Reihenfolge gelernt; keine neuen Übergänge.', '',
            'Immer warnen ist hier ausdrücklich eine eigene Signalreferenz: in Signaltabellen jede',
            'geeignete eigene Stufe, auch bei fremdem kritischem Signal; gesamt nur global nichtkritisch.',
            '## Historische Punktwertung', '',
            'Zum Anschluss an dokumentierte Prozentwerte einschließlich der letzten H Takte.',
            'Deren unvollständige Zukunft kann die Trefferquote beeinflussen; Bootstrapwerte folgen getrennt.', '']
    original = ganz[0]['takte'] if ganz else 0
    horizont = 30 if profil == '6h' else 60
    volle_zukunft = max(0, original - horizont)
    text += ['## Abdeckung vollständiger Einheiten', '',
             f'Original: {original} Instrumenttakte; davon {volle_zukunft} mit vollständig beobachteter',
             f'{horizont}-Takt-Zukunft. Kritische Takte zählen hier zur Zeitabdeckung; die Kennzahlen',
             'verwenden weiterhin ihren jeweiligen nichtkritischen beziehungsweise hohen Signalnenner.', '']
    for art in ARTEN:
        r = next((r for r in punkte if r['art'] == art and r['signal'] == 'gesamt'), None)
        n, takte = (r['einheiten'], r['takte']) if r else (0, 0)
        anteil = takte / volle_zukunft if volle_zukunft else None
        text.append(f'- {art}: {n} ganze Einheiten, {takte} von {volle_zukunft} Instrumenttakten '
                    f'({prozent(anteil)}); {volle_zukunft-takte} Takte außerhalb vollständiger Einheiten.')
    text.append('')
    for titel, rows, keys in [('Gesamte Aufnahme', ganz, ('signal',)),
                             ('Vollständige Einheiten mit voller Zukunft', punkte, ('art', 'signal'))]:
        groups = sorted(set(tuple(r[k] for k in keys) for r in rows))
        for key in groups:
            text += [f'### {titel}: ' + ', '.join(key), '',
                     '| Verfahren | Geeignete Takte | Warntakte | Warnanteil | Trefferquote | Grundrate |',
                     '|---|---:|---:|---:|---:|---:|']
            for r in rows:
                if tuple(r[k] for k in keys) == key:
                    text.append(f'| {r["verfahren"]} | {r["auswertbar"]} | {r["warntakte"]} | '
                                f'{prozent(r["warnanteil"])} | {prozent(r["trefferquote"])} | {prozent(r["grundrate"])} |')
            text.append('')
    text += ['## Intervalle und Grenzen', '',
             '[intervalle.csv](intervalle.csv) enthält gepaarte Differenzen einschließlich der direkten',
             'Startwert-/Erbevergleiche. Positive Warnanteilsdifferenz bedeutet mehr Warnungen, positive',
             'Trefferdifferenz mehr richtige Warntakte unter den ausgegebenen Warnungen; das ist kein',
             'einheitlicher Nutzenscore. [einheiten.csv](einheiten.csv) zeigt die vollständigen Grenzen.',
             'Fehlende Intervalle bedeuten zu wenige Einheiten oder undefinierte Nenner; nicht null Unsicherheit.',
             'Die einfache Wiederziehung setzt Austauschbarkeit voraus, die bei Lernstand und Reizblöcken',
             'fraglich ist. Block8 ist eine vorab festgelegte Sensitivität und verlangt mindestens 16 Einheiten.',
             'Langsame Erwärmung und andere Abhängigkeiten können auch diese Intervalle unzureichend machen.',
             'Die drei Einheitenarten werden nicht zusammengezählt. Keine Behauptung statistischer',
             'Signifikanz oder allgemeiner Zuverlässigkeit; keine unabhängigen Gerätewiederholungen.', '']
    return '\n'.join(text)


def pruefe_profilname(path, profil):
    name = path.name.lower()
    if profil not in ('6h', '30min') or '24h' in str(path).lower() or '24-h' in str(path).lower():
        raise ValueError('Nicht freigegebenes Aufnahmeprofil.')
    if not ('6h' in name if profil == '6h' else '30min' in name or '30m-' in name):
        raise ValueError('Dateiname passt nicht zum ausdrücklich freigegebenen Profil.')


def laden(path, profil):
    pruefe_profilname(path, profil)
    meta = json.loads(path.with_suffix('.json').read_text(encoding='utf-8'))
    if meta.get('fortsetzung'):
        raise ValueError('Fortsetzungsketten sind für diesen Plan nicht freigegeben.')
    # Vor dem Aufruf des bestehenden Lesers: harte Größen-/Dauergrenze, kein
    # stiller 24h-Ersatz. Dateinamen werden nicht in Artefakte geschrieben.
    maximum = 22000 if profil == '6h' else 1900
    with path.open(encoding='utf-8', newline='') as f:
        n = 0
        for n, _ in enumerate(csv.reader(f)):
            if n > maximum:
                raise ValueError('Aufnahme überschreitet das freigegebene Profil.')
    if type(meta.get('intervall_ms')) is not int or meta['intervall_ms'] <= 0:
        raise ValueError('Ungültiges Zeitintervall.')
    if n * meta['intervall_ms'] > (22000 if profil == '6h' else 1900) * 1000:
        raise ValueError('Aufnahmedauer überschreitet das Profil.')
    meta, werte = pruefen(path)
    if not werte or any(b['takt'] != a['takt'] + 1 for a, b in zip(werte, werte[1:])):
        raise ValueError('Aufnahme leer oder nicht lückenlos.')
    h = 30 if profil == '6h' else 60
    if len(werte) <= 2*h:
        raise ValueError('Aufnahme zu kurz für das geplante Fenster.')
    if profil == '30min' and (meta.get('regel') != 'startwert' or meta.get('blick', 1) != 60):
        raise ValueError('30min-Gerätevergleich verlangt Startwert und Blick 60.')
    g = Grenzen(**meta['grenzen'])
    stufen = [stufen_je_signal(w['temp_dc'], w['heap'], w['luecke_us'], g) for w in werte]
    return werte, stufen, h


def run(path, profil, out):
    pruefe_profilname(path, profil)  # vor jedem Lesen/Hashen einer möglichen Aufnahme
    before = {n: sha(Path(__file__).resolve().parent / n) for n in
              ('einheitenbootstrap.py', 'EINHEITEN-BOOTSTRAP-PLAN.md', 'koerper.py',
               'vokabular.py', 'signallabor.py', 'kern.py', 'neustart.py')}
    input_hash = sha(path)
    meta_hash = sha(path.with_suffix('.json'))
    werte, stufen, h = laden(path, profil)
    ganz, punkte, intervals, units = auswerten(werte, stufen, h,
        [bool(w['vorwarnung']) for w in werte] if profil == '30min' else None)
    if sha(path) != input_hash or sha(path.with_suffix('.json')) != meta_hash:
        raise ValueError('Eingabe änderte sich während der Auswertung.')
    if any(sha(Path(__file__).resolve().parent / n) != digest for n, digest in before.items()):
        raise ValueError('Quellen änderten sich während der Auswertung.')
    out.mkdir(parents=True, exist_ok=False)
    csv_schreiben(out / 'historische-punktwerte.csv', ganz)
    csv_schreiben(out / 'einheiten-punktwerte.csv', punkte)
    csv_schreiben(out / 'intervalle.csv', intervals, list(intervals[0]) if intervals else
                   ('art','signal','verfahren','referenz','modus','mass','status'))
    csv_schreiben(out / 'einheiten.csv', units, ('art','nummer','von_takt','bis_takt_inklusiv','takte'))
    (out / 'bericht.md').write_text(bericht(ganz, punkte, profil), encoding='utf-8')
    dateien = ('historische-punktwerte.csv','einheiten-punktwerte.csv','intervalle.csv','einheiten.csv','bericht.md')
    manifest = dict(version=1, status='vollstaendig', profil=profil, horizont=h, quellen=before,
                    aufnahme_sha256=input_hash, sidecar_sha256=meta_hash,
                    wiederholungen=WIEDERHOLUNGEN, bootstrap_seed=BOOTSTRAP_SEED,
                    dateien={n: sha(out / n) for n in dateien})
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('csv', type=Path)
    p.add_argument('--profil', choices=('6h','30min'), required=True)
    p.add_argument('--ausgabe', type=Path, required=True)
    a = p.parse_args()
    try:
        run(a.csv, a.profil, a.ausgabe)
    except (ValueError, OSError, KeyError, TypeError, csv.Error) as exc:
        p.exit(2, f'Auswertung abgebrochen ({type(exc).__name__}); keine gültige Fertigmeldung.\n')
    print('Bootstrap abgeschlossen; Ergebnisse sind in neuer Ausgabe gespeichert.')


if __name__ == '__main__':
    main()
