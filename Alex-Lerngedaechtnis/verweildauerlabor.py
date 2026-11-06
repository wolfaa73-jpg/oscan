"""Vorab festgelegter Vergleich des getrennten Dauer-/Richtungsmodells."""
import argparse
import csv
import hashlib
import json
import subprocess
from collections import defaultdict
from pathlib import Path

import signallabor as s
from verweildauer import Verweildauergedaechtnis
from vokabular import GROBWOERTER, GROBERBE, SIGNALE, grob, kritisch, warnungen

NAME = 'Verweildauer und Richtung'
QUELLEN = ('verweildauer.py', 'verweildauerlabor.py', 'test_verweildauer.py',
           'test_verweildauerlabor.py',
           'VERWEILDAUER-PLAN.md', 'signallabor.py', 'vokabular.py', 'kern.py')
ZAHLEN = s.ZAEHLER + ('fehlwarntakte', 'verpasste_zieltakte')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hashes():
    root = Path(__file__).resolve().parent
    return {n: sha(root / n) for n in QUELLEN}


def modelle(stufen, e):
    yield from s.verfahren(stufen, e)
    woerter = s.schwerstes(stufen)
    for sicht in ('grob', 'je_signal'):
        if sicht == 'grob':
            w = warnungen([grob(z) for z in woerter],
                         Verweildauergedaechtnis(GROBWOERTER, GROBERBE),
                         e.horizont, e.schwelle)
            je = {signal: w for signal, _, _ in SIGNALE}
        else:
            je = {signal: warnungen([z[signal] for z in stufen],
                                   Verweildauergedaechtnis(('OK', hoch, krit), ((hoch, krit),)),
                                   e.horizont, e.schwelle)
                  for signal, hoch, krit in SIGNALE}
            w = [not kritisch(z) and any(je[signal][t] for signal, _, _ in SIGNALE)
                 for t, z in enumerate(woerter)]
        yield sicht, NAME, w, je
        nie = [False] * len(stufen)
        yield sicht, 'Nie warnen', nie, {signal: nie for signal, _, _ in SIGNALE}


def zeilen(stufen, e):
    gesamt = s.schwerstes(stufen)
    for sicht, name, warn, je in modelle(stufen, e):
        for signal, hoch, _ in (('gesamt', None, None),) + SIGNALE:
            woerter = gesamt if signal == 'gesamt' else [z[signal] for z in stufen]
            w = warn if signal == 'gesamt' else je[signal]
            for maske in (('nichtkritisch',) if signal == 'gesamt' else ('nichtkritisch', 'hoch')):
                geeignet = [not kritisch(z) if maske == 'nichtkritisch' else z == hoch for z in woerter]
                z = s.zaehle(woerter, w, e.horizont, geeignet)
                z['fehlwarntakte'] = z['warntakte'] - z['treffertakte']
                z['verpasste_zieltakte'] = z['zieltakte'] - z['treffertakte']
                yield dict(sicht=sicht, verfahren=name, signal=signal, maske=maske, **z)


def csv_schreiben(path, rows):
    with path.open('x', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def kennzahlen(row):
    return {**s.anteile(row),
            'taktkosten10_pro1000': (10 * row['verpasste_zieltakte'] + row['fehlwarntakte']) * 1000 / row['takte'],
            'phasenkosten10_pro1000': (10 * row['verpasst'] + row['fehlwarntakte']) * 1000 / row['takte']}


def bericht(rows, satz, freeze):
    text = ['# Verweildauer und Richtung: synthetischer Vergleich', '',
            'Taktwertung ist maßgeblich. Alle Ergebnisse beschreiben künstliche Spuren, keine Geräteprüfung.',
            f'Satz: {satz}. Freeze-Commit: {freeze or "noch keine unabhängige Prüfung"}.', '',
            'Keine Parameterwahl anhand dieser Ergebnisse. Alle eigenen nichtkritischen Takte zählen;',
            'die letzten 30 Takte liefern nur Zukunft. Hohe Signaltakte und einzelne Familien stehen in den CSVs.',
            'Trefferquote bedeutet Anteil richtiger Warntakte, nicht Anteil vorhergesagter Phasen.',
            'Immer warnen behält die vorhandene Sicht: grob wird bei einem fremden kritischen Signal',
            'kein globaler Alarm ausgegeben. Deshalb kann sein Warnanteil im eigenen Signalnenner',
            'unter 100 % liegen. In der Sicht je_signal warnt die Referenz an jedem geeigneten eigenen Takt.',
            'Kosten r=10 sind Modellannahmen; Takt- und Phasenkosten besitzen verschiedene Fehlereinheiten.',
            'Signalweise Kosten nicht addieren, wenn Signale dieselbe Aktion auslösen.', '']
    agg = defaultdict(lambda: {k: 0 for k in ZAHLEN})
    for row in rows:
        if row['maske'] == 'nichtkritisch':
            key = row['sicht'], row['signal'], row['verfahren']
            for k in ZAHLEN:
                agg[key][k] += row[k]
    percent = lambda x: '—' if x is None else f'{100*x:.2f} %'
    for sicht in ('grob', 'je_signal'):
        for signal in ('gesamt',) + tuple(z[0] for z in SIGNALE):
            text += [f'## {sicht}, {signal}', '',
                     '| Verfahren | Warnanteil | Trefferquote | Grundrate | Verpasste Phasen | Taktkosten /1000 | Phasenkosten /1000 |',
                     '|---|---:|---:|---:|---:|---:|---:|']
            for name in s.VERFAHREN + ('Nie warnen', NAME):
                row = agg[sicht, signal, name]
                q = kennzahlen(row)
                text.append(f'| {name} | {percent(q["warnanteil"])} | {percent(q["trefferquote"])} | '
                            f'{percent(q["grundrate"])} | {row["verpasst"]}/{row["phasen"]} | '
                            f'{q["taktkosten10_pro1000"]:.2f} | {q["phasenkosten10_pro1000"]:.2f} |')
            text.append('')
    text += ['## Aussagegrenzen', '',
             'Die Mischung gewichtet Familien durch gleich viele gleich lange Spuren. Einzelne Familien',
             'können anders ausfallen; kein globaler Gewinner wird aus dem Gesamtwert abgeleitet.',
             'Dauer und Richtung sind im Kandidaten bedingt unabhängig. Das Ein-Takt-Dauerprior ist',
             'eine zusätzliche Annahme. Fehlende Dauerabdeckung unterdrückt eine Warnung, beweist aber',
             'keine Sicherheit. Erste linkszensierte Läufe werden nicht als vollständige Dauern gelernt.',
             'Kein Beleg für Echtzeit, RAM, Energie oder Nutzen an echten 6-/24-Stunden-Aufnahmen.', '']
    return '\n'.join(text)


def run(satz, out, freeze=None):
    if satz not in ('entwicklung', 'kontrolle'):
        raise ValueError('Unbekannter Satz.')
    before = hashes()
    if satz == 'kontrolle':
        if not freeze or len(freeze) != 40 or any(c not in '0123456789abcdef' for c in freeze):
            raise ValueError('Vorher festgehaltener vollständiger Freeze-Commit erforderlich.')
        root = Path(__file__).resolve().parent
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        if head != freeze:
            raise ValueError('Arbeitsstand entspricht nicht dem Freeze-Commit.')
        for name in QUELLEN:
            version = subprocess.check_output(['git', 'show', f'{freeze}:Alex-Lerngedaechtnis/{name}'], cwd=root)
            if hashlib.sha256(version).hexdigest() != before[name]:
                raise ValueError('Quellen weichen vom Freeze ab.')
    out.mkdir(parents=True, exist_ok=False)
    manifest = dict(version=1, status='unvollstaendig', satz=satz,
                    freeze=freeze, quellen=before, parameter=dict(horizont=30, halbwertszeit=6, schwelle=0.6))
    mp = out / 'manifest.json'
    mp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    start, count = (300000, 16) if satz == 'entwicklung' else (300100, 32)
    e = s.Einstellungen()
    rows = []
    for familie in s.FAMILIEN:
        for seed in range(start, start + count):
            rows.extend(dict(familie=familie, seed=seed, **r)
                        for r in zeilen(s.generiere(familie, seed, satz, e), e))
    if hashes() != before:
        raise ValueError('Quellen haben sich während des Laufs verändert.')
    csv_schreiben(out / 'spuren.csv', rows)
    sums = defaultdict(lambda: {k: 0 for k in ZAHLEN})
    keys = ('familie', 'sicht', 'verfahren', 'signal', 'maske')
    for row in rows:
        for k in ZAHLEN:
            sums[tuple(row[n] for n in keys)][k] += row[k]
    aggregate = [dict(zip(keys, key), **value, **kennzahlen(value)) for key, value in sorted(sums.items())]
    csv_schreiben(out / 'vergleich.csv', aggregate)
    (out / 'bericht.md').write_text(bericht(rows, satz, freeze), encoding='utf-8')
    manifest.update(status='vollstaendig', seeds=dict(von=start, anzahl=count),
                    dateien={n: sha(out / n) for n in ('spuren.csv', 'vergleich.csv', 'bericht.md')})
    mp.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('satz', choices=('entwicklung', 'kontrolle'))
    p.add_argument('--ausgabe', type=Path, required=True)
    p.add_argument('--freeze')
    a = p.parse_args()
    try:
        run(a.satz, a.ausgabe, a.freeze)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        p.exit(2, f'Vergleich abgebrochen ({type(exc).__name__}); keine gültige Fertigmeldung.\n')
    print('Vergleich vollständig; Manifest und Bericht erstellt.')


if __name__ == '__main__':
    main()
