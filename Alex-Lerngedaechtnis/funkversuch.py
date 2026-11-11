"""Vorab festgelegte Funk-Wärmeauswertung. Ein Argument: die vollständige Aufnahme.csv.
Liest ihre JSON und Empfinden-/Vorhersage-Nebendateien; verändert keine Messdaten.
"""
import argparse
import csv
import hashlib
import json
import statistics
from pathlib import Path
import koerper

PHASEN=(("Anlauf",1,1800,0),("Aus vorher",1801,3600,0),("Bereit vorher",3601,5400,1),
        ("Senden",5401,7200,2),("Bereit nachher",7201,9000,1),("Aus nachher",9001,10800,0))


def modus(t):
    return 1 if 3601<=t<=5400 or 7201<=t<=9000 else 2 if 5401<=t<=7200 else 0


def auswertung(werte,empfinden):
    if len(werte)!=10800 or len(empfinden)!=10800:raise ValueError("Erwartet: 10800 vollständige Takte")
    for i,(w,e) in enumerate(zip(werte,empfinden),1):
        if i>1 and w['zeit_ms']<=werte[i-2]['zeit_ms']:
            raise ValueError("Aufnahmezeit läuft nicht vorwärts")
        reiz=(16 if modus(i) else 0)|(8 if modus(i)==2 else 0)
        if w["takt"]!=i or e["takt"]!=i or w["reiz"]!=reiz or w["temp_dc"] is None or not e["gueltig"]:
            raise ValueError(f"Takt {i}: Lücke, Fehlmessung, fremder Reiz, Sendefehler oder falsche Funkphase")
    def mean(seq):return statistics.mean(seq)
    phasen=[]
    for name,a,b,m in PHASEN:
        idx=range(a-1+900,b)  # vorab gesetzt: erste 900 Takte jeder Phase verwerfen
        temp=mean(werte[i]["temp_dc"]/10 for i in idx)
        neu=[empfinden[i] for i in idx]
        erste=[i for i in range(a-1,min(a+59,b)) if abs(empfinden[i]["gerade"])>=2 and not empfinden[i]["anlauf"]]
        phasen.append(dict(name=name,von=a,bis=b,modus=m,gewertet=len(neu),empfinden_gewertet=sum(not e["anlauf"] for e in neu),temperatur_c=temp,
                           mass_gerade_mg=mean(e["mass_gerade_mg"] for e in neu),
                           mass_woanders_mg=mean(e["mass_woanders_mg"] for e in neu),
                           gerade_ab2=sum(abs(e["gerade"])>=2 and not e["anlauf"] for e in neu),
                           woanders_ab2=sum(abs(e["woanders"])>=2 and not e["anlauf"] for e in neu),
                           nie_auffaellig=0,erste_ueberraschung_60=None if not erste else erste[0]+1,
                           ueberrascht_erste_60=len(erste)))
    def kontraste(feld):
        aus=(phasen[1][feld]+phasen[5][feld])/2
        bereit=(phasen[2][feld]+phasen[4][feld])/2
        return dict(bereit_minus_aus=bereit-aus,senden_minus_bereit=phasen[3][feld]-bereit,
                    aus_nachher_minus_vorher=phasen[5][feld]-phasen[1][feld])
    return dict(version=1,takte=10800,phasen=phasen,temperatur_kontraste_c=kontraste("temperatur_c"),
                mass_gerade_kontraste_mg=kontraste("mass_gerade_mg"),mass_woanders_kontraste_mg=kontraste("mass_woanders_mg"))


def pruefe(pfad):
    if pfad.with_name(pfad.stem+".abbruch.txt").exists():raise ValueError("Aufnahme hat eine Abbruchdatei")
    meta,werte=koerper.pruefen(pfad)
    if meta.get("funkversuch")!={"version":1,"kanal":6,"takte":10800} or not meta.get("empfinden") or not meta.get("vorhersage"):
        raise ValueError("Freigegebener Funkplan samt Empfinden/Vorhersage fehlt in JSON")
    if meta.get("intervall_ms")!=1000 or meta.get("fortsetzung") or meta.get("sichern_alle") or any(meta.get(x) for x in ("last","leck","bremse","erkundung")):
        raise ValueError("Funkplan verlangt frischen Sekundentakt ohne weitere Reize")
    datei=pfad.with_name(pfad.stem+".empfinden.csv")
    with datei.open(newline="") as f: e=[{k:int(v) for k,v in z.items()} for z in csv.DictReader(f)]
    out=auswertung(werte,e)
    dateien=[pfad,pfad.with_suffix('.json'),datei,pfad.with_name(pfad.stem+'.vorhersage.csv')]
    out['quellen']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dateien}
    out['zeitspanne_ms']=werte[-1]['zeit_ms']-werte[0]['zeit_ms']
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv',type=Path);a=p.parse_args()
    try: aus=pruefe(a.csv)
    except (ValueError,OSError,KeyError) as error:p.exit(2,f"Funkprüfung: {error}\n")
    print(json.dumps(aus,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
