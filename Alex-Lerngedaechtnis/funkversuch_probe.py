"""Künstliche Prüfung der Funk-Wärmeauswertung, kein gemessener Funkversuch."""
import argparse
import json
from pathlib import Path
import empfinden as em
import selbstvorhersage as sv
import kunstkoerper as kk
import funkversuch as f

def kuenstlich(bereit=2.,send=.5,drift=0.,saat=1,umgebung=False):
    last=[0]*10800
    temp=kk.temperaturen(last,tau=30,hub=0,ruhe=37,rauschen=0,anteile=kk.GEMESSEN['anteile'] if umgebung else (),stufe=0,saat=saat)
    v,e=sv.Selbstvorhersage(),em.Empfinden();werte=[];neben=[];vor=[];extra=0.
    for i,x in enumerate(temp,1):
        m=f.modus(i);extra+=((bereit if m else 0)+(send if m==2 else 0)-extra)/30
        dc=round(10*(x+extra+drift*i))
        reiz=(16 if m else 0)|(8 if m==2 else 0)
        z=v.takt(dc,0);a=e.takt(dc,z['mittel']);vor.append(z)
        werte.append(dict(takt=i,temp_dc=dc,reiz=reiz,zeit_ms=i*1000,heap=300000,luecke_us=300))
        neben.append(dict(zip(em.KOPF,[i]+a)))
    return werte,neben,vor

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('ausgabe',type=Path);a=p.parse_args()
    if a.ausgabe.exists():p.error('Ausgabe existiert bereits')
    ergebnisse=[]
    for bereit,send in ((0.,0.),(2.,.5)):
        for saat in range(1,9):
            w,e,_=kuenstlich(bereit,send,saat=saat,umgebung=True)
            z=f.auswertung(w,e)
            ergebnisse.append(dict(bereitschaft_wahr_c=bereit,senden_zusaetzlich_wahr_c=send,saat=saat,
                                  **z['temperatur_kontraste_c'],
                                  ueberraschung_beim_einschalten=z['phasen'][2]['erste_ueberraschung_60']))
    out=dict(kuenstlich=True,zeitkonstante_s=30,umgebung='kunstkoerper.GEMESSEN',takte_je_lauf=10800,laeufe=ergebnisse)
    with a.ausgabe.open('x') as datei:json.dump(out,datei,indent=2);datei.write('\n')
    return 0

if __name__=='__main__':main()
