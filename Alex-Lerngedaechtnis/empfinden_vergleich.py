"""Vorab festgelegter v1/v2-Vergleich an bekannten Daten. Keine Parametersuche."""
import argparse
import json
from pathlib import Path
import empfinden_auswertung as a

DATEIEN = ("koerper-zufallslast-8h-2026-11-10.csv", "koerper-last-2026-11-05.csv",
           "koerper-kaelte-2026-11-10.csv", "fahrt-2026-11-11.bin")
FENSTER = (("Pressluft 1",12500,13000), ("Fön kurz 1",13400,14100),
           ("Fön kurz 2",15200,15900), ("Reiniger und Pressluft",18450,18780),
           ("Fön lang 1",18781,19400), ("Fön lang 2",24120,24500),
           ("Isopropanol und Pressluft",27800,28400), ("Fön lang 3",34100,34600))


def bereit(z):
    return bool(z["neu"][3] and not z["neu"][2])


def haeufigkeiten(rows):
    return dict(n=len(rows), wort_gesperrt=sum(not bereit(z) for z in rows),
                gerade_ab_2=sum(bereit(z) and abs(z["neu"][0]) >= 2 for z in rows),
                woanders_ab_2=sum(bereit(z) and abs(z["neu"][1]) >= 2 for z in rows),
                woanders_led_aktiv=sum(bereit(z) and z["neu"][1] != 0 for z in rows),
                woanders_led_impulse=sum(bereit(z) and z["neu"][1] != 0 and z["takt"] % 4 == 3 for z in rows),
                alt=sum(bool(z["alt"]) for z in rows), nie_auffaellig=0)


def vergleich(eins, zwei):
    if len(eins) != len(zwei) or any(x["takt"] != y["takt"] for x,y in zip(eins,zwei)):
        raise ValueError("Versionen nicht taktgleich")
    schnitt = [i for i,(x,y) in enumerate(zip(eins,zwei)) if bereit(x) and bereit(y)]
    nach_kalt = [i for i,(x,y) in enumerate(zip(eins,zwei)) if x["neu"][3] and y["neu"][3] and x["n"]>1800 and y["n"]>1800]
    return {str(v):dict(eigen=haeufigkeiten([z for z in rows if bereit(z)]),
                       gemeinsam=haeufigkeiten([rows[i] for i in schnitt]),
                       nach_kalt=haeufigkeiten([rows[i] for i in nach_kalt]),
                       zusammen=a.zusammen(rows),
                       mass_verlauf=[dict(zeile=i+1,takt=z["takt"],n=z["n"],nw=z["nw"],ng=z["ng"],
                                           mass_mg=z["neu"][4:6],M_mg=z["neu"][6],L_mg=z["neu"][7])
                                      for i,z in enumerate(rows) if i==0 or (i+1)%1800==0 or i==len(rows)-1])
            for v,rows in ((1,eins),(2,zwei))}


def ereignis(rows, von, bis):
    z = rows[von-1:bis]
    aktive = [(von+i,x["neu"][0]) for i,x in enumerate(z) if bereit(x) and abs(x["neu"][0])>=2]
    return dict(von=von,bis=min(bis,len(rows)),zaehler=haeufigkeiten(z),
                erster_gerade_ab_2=list(aktive[0]) if aktive else None,
                gerade_min=min(x["neu"][0] for x in z),gerade_max=max(x["neu"][0] for x in z))


def starts(rows):
    result=[]
    for i,z in enumerate(rows):
        if not z.get("neustart"): continue
        ende=next((j for j in range(i+1,len(rows)) if rows[j].get("neustart")),len(rows))
        schutz=[x for x in rows[i:ende] if x["boot"]<=600]
        # Before first tick = after prior tick. At cold start use explicit prior.
        vor=[rows[i-1][k] for k in ("qg","qw")] if i and not z["bei_null"] else [float(a.em.F(.04)),.25]
        nach=[schutz[-1][k] for k in ("qg","qw")] if schutz else vor
        result.append(dict(zeile=i+1,takt=z["takt"],grund=z["grund"],bei_null=z["bei_null"],
                           erste_60=ereignis(rows,i+1,min(i+60,ende)),
                           lernschutz_takte=sum(bool(x["neu"][3]) for x in schutz),
                           varianz_vor=vor,varianz_nach=nach,lernplastik_im_schutz=vor!=nach))
    return result


def rechnen():
    laeufe={}
    for v in (1,2):
        vor,emp,z=a.csv_lauf(a.ROH/DATEIEN[0],version=v)
        laeufe[(v,DATEIEN[0])]=z
        _,_,z=a.csv_lauf(a.ROH/DATEIEN[2],vor,emp,version=v)
        laeufe[(v,DATEIEN[2])]=z
        _,_,z=a.csv_lauf(a.ROH/DATEIEN[1],version=v)
        laeufe[(v,DATEIEN[1])]=z
        _,_,z=a.fahrt_lauf(a.ROH/DATEIEN[3],version=v,details=True)
        laeufe[(v,DATEIEN[3])]=z
    # Prevent silently drifting away from the previously published v1 baseline.
    alt=json.loads((a.ROOT/"beispiele/geraetelaeufe-2026-11/empfinden-v1-ergebnisse.json").read_text())
    for n in DATEIEN:
        if a.zusammen(laeufe[(1,n)]) != alt["laeufe"][n]:
            raise ValueError("V1-Reproduktion weicht ab: "+n)
    return dict(version=2,quellen={n:a.sha(a.ROH/n) for n in DATEIEN},
                verfahren={n:a.sha(a.ROOT/n) for n in ("empfinden.py","referenzen/empfinden_v1.py",
                    "empfinden_auswertung.py","empfinden_vergleich.py","EMPFINDEN-PLAN-v2.md")},
                laeufe={n:vergleich(laeufe[(1,n)],laeufe[(2,n)]) for n in DATEIEN},
                starts={str(v):starts(laeufe[(v,DATEIEN[3])]) for v in (1,2)},
                fenster={str(v):{name:ereignis(laeufe[(v,DATEIEN[3])],von,bis) for name,von,bis in FENSTER} for v in (1,2)},
                led_grenze="Ohne Protokoll-voll-Überlagerung; dieser Zustand fehlt in der alten Aufnahme. Stufe 1 zählt.")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ausgabe",type=Path,required=True)
    args=p.parse_args()
    if args.ausgabe.exists(): p.error("Ausgabe existiert bereits")
    aus=rechnen()
    with args.ausgabe.open("x",encoding="utf-8") as f:
        json.dump(aus,f,ensure_ascii=False,indent=2);f.write("\n")

if __name__=="__main__": main()
