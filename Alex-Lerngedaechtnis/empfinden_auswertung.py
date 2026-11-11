"""Festgelegte Nachrechnung der freigegebenen Aufnahmen; keine Anpassung an Ergebnisse.
Aufruf: python empfinden_auswertung.py --ausgabe ergebnis.json (überschreibt nichts).
"""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import empfinden as em
from referenzen import empfinden_v1
import fahrt
import selbstvorhersage as sv

ROOT = Path(__file__).parent
ROH = ROOT / "beispiele/geraetelaeufe-2026-11/roh"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def folge(werte):
    pos, aus = 1, []
    for wort, g in itertools.groupby(werte):
        n = sum(1 for _ in g)
        aus.append([pos, n, wort])
        pos += n
    return aus


def zusammen(zeilen):
    gueltig = [z for z in zeilen if z["neu"][3] and not z["neu"][2]]
    return dict(takte=len(zeilen), gewertet=len(gueltig), anlauf=sum(z["neu"][2] for z in zeilen),
                fehlend=sum(not z["neu"][3] for z in zeilen),
                nie_auffaellig=0, alte_vorhersage=sum(z["alt"] for z in gueltig),
                gerade=sum(abs(z["neu"][0]) >= 2 for z in gueltig),
                woanders=sum(abs(z["neu"][1]) >= 2 for z in gueltig),
                anders_als_alt=sum((abs(z["neu"][0]) >= 2) != bool(z["alt"]) for z in gueltig),
                mass_am_anfang_mg=zeilen[0]["neu"][4:6], mass_am_ende_mg=zeilen[-1]["neu"][4:6],
                alte_grenze_am_ende_mg=zeilen[-1]["alte_grenze_mg"],
                folge_gerade=folge([z["neu"][0] if z["neu"][3] and not z["neu"][2] else None for z in zeilen]),
                folge_woanders=folge([z["neu"][1] if z["neu"][3] and not z["neu"][2] else None for z in zeilen]))


def referenz(version):
    if version not in (1, 2):
        raise ValueError("Unbekannte Empfinden-Version")
    return empfinden_v1 if version == 1 else em


def zustand(e):
    return dict(n=e.n, ng=e.ng, nw=e.nw, boot=e.boot,
                qg=float(e.qg), qw=float(e.qw))


def csv_lauf(pfad, v=None, e=None, version=2):
    v, e = v or sv.Selbstvorhersage(), e or referenz(version).Empfinden()
    temp,last=sv.lies(pfad)
    zeilen=[]
    for x,l in zip(temp,last):
        alt=v.takt(x,l)
        zeilen.append(dict(neu=e.takt(x, None if alt is None else alt["mittel"]),
                           alt=0 if alt is None else int(alt["ueberrascht"]),
                           alte_grenze_mg=None if alt is None or alt["grenze"] is None else sv.milli(alt["grenze"])))
        zeilen[-1].update(zustand(e))
        zeilen[-1]["takt"] = len(zeilen)
    return v,e,zeilen


def fahrt_lauf(pfad, version=2, details=False):
    modul=referenz(version)
    v,e=sv.Selbstvorhersage(),modul.Empfinden()
    saetze=list(fahrt.saetze(pfad.read_bytes()))
    zeilen, abschnitte, beginn=[],[],0
    sv_stand=None
    for i,s in enumerate(saetze):
        if s["neustart"]:
            if i:
                abschnitte.append(dict(von=beginn+1,bis=i,ergebnis=zusammen(zeilen[beginn:i])))
            beginn=i
            if s["bei_null"]:
                v,e=sv.Selbstvorhersage(),modul.Empfinden()
            elif sv_stand is not None:
                v=copy.deepcopy(sv_stand)
            e.neustart()
        alt=v.takt(s["temp_dc"],s["last"])
        zeilen.append(dict(neu=e.takt(s["temp_dc"],None if alt is None else alt["mittel"]),
                           alt=s["ueberrascht"], alte_grenze_mg=None if s["grenze_cg"] is None else s["grenze_cg"]*10))
        zeilen[-1].update(zustand(e))
        zeilen[-1].update(takt=s["takt"], neustart=s["neustart"], grund=s["grund"], bei_null=s["bei_null"])
        if s["takt"] % 30 == 0:
            sv_stand=copy.deepcopy(v)
    if zeilen: abschnitte.append(dict(von=beginn+1,bis=len(zeilen),ergebnis=zusammen(zeilen[beginn:])))
    return (zusammen(zeilen), abschnitte, zeilen) if details else (zusammen(zeilen), abschnitte)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--ausgabe",type=Path,required=True);p.add_argument("--version",type=int,choices=(1,2),default=2);a=p.parse_args()
    if a.ausgabe.exists(): p.error("Ausgabe existiert bereits")
    dateien=[ROH/n for n in ("koerper-zufallslast-8h-2026-11-10.csv","koerper-last-2026-11-05.csv",
                             "koerper-kaelte-2026-11-10.csv","fahrt-2026-11-11.bin")]
    aus=dict(version=a.version,quellen={f.name:sha(f) for f in dateien},
             verfahren={f:sha(ROOT/f) for f in (("referenzen/empfinden_v1.py" if a.version==1 else "empfinden.py"),"empfinden_auswertung.py",("EMPFINDEN-PLAN.md" if a.version==1 else "EMPFINDEN-PLAN-v2.md"))},laeufe={})
    v,e,z=csv_lauf(dateien[0],version=a.version);aus["laeufe"][dateien[0].name]=zusammen(z)
    _,_,z=csv_lauf(dateien[2],v,e);aus["laeufe"][dateien[2].name]=zusammen(z)
    _,_,z=csv_lauf(dateien[1],version=a.version);aus["laeufe"][dateien[1].name]=zusammen(z)
    f,abschnitte=fahrt_lauf(dateien[3],version=a.version);aus["laeufe"][dateien[3].name]=f;aus["fahrt_abschnitte"]=abschnitte
    with a.ausgabe.open("x",encoding="utf-8") as f: json.dump(aus,f,ensure_ascii=False,indent=2);f.write("\n")
    return 0

if __name__=="__main__": main()
