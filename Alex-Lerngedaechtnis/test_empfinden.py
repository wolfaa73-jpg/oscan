"""Hostgleichheit, Zustandsprüfung und bekannte künstliche Wahrheit."""
import copy
import math
from pathlib import Path
import random
import subprocess
import tempfile
import unittest
import numpy as np
import empfinden as e
import kunstkoerper as kk
import selbstvorhersage as sv

ROOT = Path(__file__).parent
QUELLE = r"""
#include <cstdio>
#include "Vorhersage.h"
#include "Empfinden.h"
int main() {
    static Selbstvorhersage v;
    static Empfinden e;
    static uint8_t vs[sizeof(v)], es[Empfinden::standBytes];
    v.starte(); e.starte();
    unsigned t=0; int temp,last;
    while (scanf("%d %d", &temp, &last)==2) {
        ++t;
        if (t==6500) {
            v.exportiere(vs); e.exportiere(es);
            v=Selbstvorhersage(); e=Empfinden();
            if (!v.importiere(vs) || !e.importiere(es)) return 2;
            e.neustart();
        }
        v.takt(t,temp!=-32768,temp,last);
        e.takt(t,temp!=-32768,temp,v.hatFehler(),v.mittel());
        puts(e.zeile());
    }
    e.exportiere(es);
    for (unsigned i=0;i<sizeof(es);++i) printf("%02x",es[i]);
    puts("");
    es[20]^=1;
    if (e.importiere(es)) return 3;
}
"""

class EmpfindenTests(unittest.TestCase):
    def test_schwellen_und_hysterese(self):
        for sign in (-1,1):
            for k in range(1,20):
                self.assertEqual(e.stufe(e.F(sign*2**k), e.F(1)),sign*k)
                self.assertEqual(e.stufe(sign*np.nextafter(e.F(2**k),e.F(0)), e.F(1)),sign*(k-1))
        self.assertEqual(e.stufe(1.9,1),0)
        self.assertEqual(e.stufe(1.5,1,1),1)
        self.assertEqual(e.stufe(1.49,1,1),0)
        self.assertEqual(e.stufe(-1.9,1,1),0)

    def test_sichern_laden_atomisch_und_neustart(self):
        a=e.Empfinden()
        for t in range(2500): a.takt(370, e.F(.1))
        b=e.Empfinden(); b.importiere(a.exportiere())
        self.assertEqual(b.exportiere(),a.exportiere())
        for i in range(e.FORMAT.size):
            kaputt=bytearray(a.exportiere()); kaputt[i]^=1
            with self.assertRaises(ValueError): b.importiere(kaputt)
            self.assertEqual(b.exportiere(),a.exportiere())
        b.neustart(); q=b.qg
        for _ in range(600):
            z=b.takt(200,e.F(-5))
            self.assertLessEqual(z[0],-2)
            self.assertEqual(z[2],0)
        self.assertEqual(b.qg,q)
        self.assertFalse(b.takt(200,e.F(-5))[2])

    def test_fehlend_lernt_nichts_kein_erfundenes_wort(self):
        a=e.Empfinden()
        for _ in range(2000): a.takt(370,e.F(.1))
        stand=a.exportiere()
        for _ in range(100):
            z=a.takt(None,e.F(100))
            self.assertEqual(z[:4],[0,0,0,0])
        self.assertEqual(a.exportiere(),stand)

    def test_langsamer_sinn_bei_bekanntem_umgebungswechsel(self):
        a=e.Empfinden()
        for _ in range(2000): a.takt(370,e.F(0))
        aus=[a.takt(290,e.F(0)) for _ in range(1200)]
        self.assertLessEqual(aus[-1][1],-2)
        self.assertLess(aus[-1][6],aus[-1][7])
        self.assertLess(float(np.sqrt(a.qw)),.7)

    def test_woanders_mass_lernt_ueber_und_unter_den_prior(self):
        ruhig=e.Empfinden();wechsel=e.Empfinden()
        for t in range(28800):
            ruhig.takt(370,e.F(0))
            wechsel.takt(round(370+20*math.sin(2*math.pi*t/3600)),e.F(0))
        self.assertLess(float(np.sqrt(ruhig.qw)),.2)
        self.assertGreater(float(np.sqrt(wechsel.qw)),.5)
        self.assertGreater(wechsel.nw,7200)

    def test_v1_stand_wird_explizit_uebernommen(self):
        from referenzen import empfinden_v1 as alt
        a=alt.Empfinden()
        for _ in range(2000):a.takt(370,alt.F(.1))
        b=e.Empfinden();b.importiere(a.exportiere());b.neustart()
        self.assertEqual(b.M,a.M);self.assertEqual(b.L,a.L)
        self.assertEqual(b.qw,a.qw)
        self.assertEqual(int.from_bytes(b.exportiere()[4:8],'little'),2)
        self.assertLessEqual(b.takt(200,e.F(-5))[0],-2)

    def test_unplausible_messung_wie_fehlerwert(self):
        a=e.Empfinden();stand=a.exportiere()
        for temp,mittel in ((2001,e.F(0)),(-1001,e.F(0)),(370,e.F(float('nan')))):
            self.assertEqual(a.takt(temp,mittel)[3],0)
            self.assertEqual(a.exportiere(),stand)

    def test_massband_friert_beim_schock(self):
        a=e.Empfinden()
        for _ in range(2000): a.takt(370,e.F(.1))
        q=a.qg
        for _ in range(1000): a.takt(370,e.F(4))
        self.assertEqual(q,a.qg)

    def test_kunstkoerper_und_12000_takte_zeilen_und_stand_gleich(self):
        last=kk.lastreihe(12000,240,240,20261111)
        temp=[round(10*x) for x in kk.temperaturen(last,saat=81)]
        # Bekannter Eingriff, keine echten Aufnahmen zur Grenzwahl.
        for i in range(9000,10000):
            temp[i]-=round(80*math.exp(-(i-9000)/300))
        for i in (0,1,55,9100,9101,11999): temp[i]=None
        temp[13],temp[20]=2001,-1001
        a=e.Empfinden(); v=sv.Selbstvorhersage(); soll=[]
        for t,(x,l) in enumerate(zip(temp,last),1):
            if t==6500:
                neu=e.Empfinden(); neu.importiere(a.exportiere()); a=neu; a.neustart()
                v=copy.deepcopy(v)
            z=v.takt(x,l)
            soll.append(e.zeile(t,a.takt(x,None if z is None else z['mittel'])))
        with tempfile.TemporaryDirectory() as d:
            cpp,exe=Path(d,'probe.cpp'),Path(d,'probe')
            cpp.write_text(QUELLE)
            subprocess.run(['c++','-std=c++11','-O2','-ffp-contract=off','-Wall','-Wextra','-Werror','-I',
                            str(ROOT/'esp32/Lernknoten'),str(cpp),'-o',str(exe)],check=True)
            aus=subprocess.run([str(exe)],input=''.join(f'{-32768 if x is None else x} {l}\n' for x,l in zip(temp,last)),
                               text=True,capture_output=True,check=True).stdout.splitlines()
        self.assertEqual(aus[:-1],soll)
        self.assertEqual(aus[-1],a.exportiere().hex())
        self.assertTrue(any(abs(int(z.split(',')[2]))>=2 for z in soll[9000:9040]))



class EmpfindenIntegrationTests(unittest.TestCase):
    def test_neue_aufnahme_und_manipulierte_nebenzeile(self):
        import koerper
        from test_labor import KoerperTests
        from koerper import Grenzen
        # Echte Host-Sketch-Ausgabe als serieller Eingang des Aufnahmeprogramms.
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d,'sketch')
            subprocess.run(['c++','-std=c++11','-DALEX_STARTWERT','-ffp-contract=off',str(ROOT/'esp32/host.cpp'),'-o',str(exe)],check=True)
            befehle=['NEUER_LAUF','GRENZEN 380 390 65536 16384 20000 200000','BLICK 60','VORHERSAGE 1','EMPFINDEN 1']
            befehle+=['MESSWERT 370 300000 300']*100
            z=subprocess.run([str(exe)],input='\n'.join(befehle)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()
            # BEREIT und vier Bestätigungen, dann Nebendatei-Zeilen vor jedem K-Takt.
            antworten=[x.encode() for x in z[1:6]]+[b'KOERPER,an']+[x.encode() for x in z[6:]]
            ziel=Path(d,'probe.csv'); gesendet=[]
            port=KoerperTests.port(antworten,gesendet)
            g=Grenzen(380,390,65536,16384,20000,200000)
            self.assertEqual(koerper.aufnehmen(port,'startwert',g,1000,100,ziel,blick=60,empfinden=True),100)
            meta,werte=koerper.pruefen(ziel)
            self.assertEqual(koerper.empfinden_pruefen(ziel,meta,werte),100)
            self.assertIn(b'EMPFINDEN 1\n',gesendet)
            neben=Path(d,'probe.empfinden.csv'); original=neben.read_text()
            neben.write_text(original.replace('1,0,0,1,1,','1,2,0,1,1,',1))
            with self.assertRaises(ValueError): koerper.pruefen(ziel)
            neben.write_text(original)
            with self.assertRaises(ValueError): koerper.empfinden_pruefen(ziel,dict(meta,empfinden={}),werte)
            neben.unlink()
            with self.assertRaises(ValueError): koerper.empfinden_pruefen(ziel,meta,werte)

    def test_alte_csv_mit_v1_referenz_pruefen(self):
        import csv
        import koerper
        from referenzen import empfinden_v1 as alt
        a=alt.Empfinden();v=sv.Selbstvorhersage();werte=[];zeilen=[]
        for t in range(1,2501):
            temp=370+10*(t%3)
            z=v.takt(temp,0)
            zeilen.append([t]+a.takt(temp,z['mittel']))
            werte.append(dict(takt=t,temp_dc=temp,reiz=0))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d,'alt.csv')
            with p.with_name('alt.empfinden.csv').open('w',newline='') as out:
                c=csv.writer(out);c.writerow(alt.KOPF);c.writerows(zeilen)
            meta=dict(intervall_ms=1000,empfinden=dict(zip(koerper.EMPFINDEN_FELDER_V1,alt.KONSTANTEN)))
            self.assertEqual(koerper.empfinden_pruefen(p,meta,werte),2500)
            meta['empfinden']=dict(zip(koerper.EMPFINDEN_FELDER,e.KONSTANTEN))
            with self.assertRaises(ValueError):koerper.empfinden_pruefen(p,meta,werte)
        for version,konstanten in ((1,alt.KONSTANTEN),(2,e.KONSTANTEN)):
            antwort=('EMPFINDEN,ok,'+','.join(map(str,konstanten))).encode()
            self.assertEqual(koerper.lies_empfindenstart(antwort)['version'],version)

    def test_nvs_fehlender_schluessel_bleibt_still(self):
        sketch=(ROOT/'esp32/Lernknoten/Lernknoten.ino').read_text()
        a=sketch.index('bool fahrtEmpfinden(');b=sketch.index('\n}',a)+2
        funktion=sketch[a:b]
        cpp=r'''
#include <stdexcept>
struct Preferences {
 static bool vorhanden;static unsigned wert,lesen;
 bool begin(const char*,bool){return true;}
 bool isKey(const char*){return vorhanden;}
 unsigned getUChar(const char*,unsigned){++lesen;if(!vorhanden)throw std::runtime_error("NVS-Lesefehler");return wert;}
 unsigned putUChar(const char*,unsigned v){vorhanden=true;wert=v;return 1;}
 void end(){}
};
bool Preferences::vorhanden=false;unsigned Preferences::wert=0,Preferences::lesen=0;
'''+funktion+r'''
int main(){
 if(fahrtEmpfinden() || Preferences::lesen)return 1;
 if(!fahrtEmpfinden(true,true)||!fahrtEmpfinden())return 2;
 if(!fahrtEmpfinden(true,false)||fahrtEmpfinden())return 3;
}
'''
        with tempfile.TemporaryDirectory() as d:
            p,exe=Path(d,'nvs.cpp'),Path(d,'nvs');p.write_text(cpp)
            subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror',str(p),'-o',str(exe)],check=True)
            subprocess.run([str(exe)],check=True)

    def test_ausgeschaltet_bytegleich_und_schalter(self):
        with tempfile.TemporaryDirectory() as d:
            # Der alte vollständige Sketch wird aus dem festgelegten Ausgangscommit gebaut.
            import tarfile, io
            alt=Path(d,'alt'); alt.mkdir()
            archiv=subprocess.check_output(['git','archive','847de18','Alex-Lerngedaechtnis/esp32'],cwd=ROOT.parent)
            with tarfile.open(fileobj=io.BytesIO(archiv)) as t: t.extractall(alt)
            neu=Path(d,'neu'); vorher=Path(d,'vorher')
            for quelle,exe in ((ROOT/'esp32/host.cpp',neu),(alt/'Alex-Lerngedaechtnis/esp32/host.cpp',vorher)):
                subprocess.run(['c++','-std=c++11','-DALEX_STARTWERT','-ffp-contract=off',str(quelle),'-o',str(exe)],check=True)
            befehle=['NEUER_LAUF','GRENZEN 380 390 65536 16384 20000 200000','BLICK 60','VORHERSAGE 1']
            befehle += [f'MESSWERT {370+10*(t%3)} 300000 300' for t in range(2000)]
            eingabe='\n'.join(befehle)+'\n'
            def run(exe,text): return subprocess.run([str(exe)],input=text,text=True,capture_output=True,check=True).stdout
            self.assertEqual(run(neu,eingabe),run(vorher,eingabe))
            aus=run(neu,'EMPFINDEN 1\nVORHERSAGE 0\nEMPFINDEN 0\nVORHERSAGE 0\n')
            self.assertIn('FEHLER',aus)
            self.assertTrue(aus.endswith('VORHERSAGE,aus\n'))

    def test_fahrtsatz_stufen_und_neustart_alle_kombinationen(self):
        import fahrt
        import struct
        for g in range(-7,8):
            for w in range(-7,8):
                daten=struct.pack('<IhBBhhhh',1,370,0,(g+8)|((w+8)<<4),3700,3700,0,80)
                s=list(fahrt.saetze(daten))[0]
                self.assertEqual((s['gerade'],s['woanders'],s['grund'],s['bei_null']),(g,w,0,0))
        for bits,grund in ((64,129),(0,0)):
            s=list(fahrt.saetze(struct.pack('<IhBBhhhh',1,370,bits,grund,0,0,0,0)))[0]
            self.assertNotIn('gerade',s)
        with self.assertRaises(ValueError):
            list(fahrt.saetze(struct.pack('<IhBBhhhh',1,370,0,16,0,0,0,0)))

if __name__=='__main__': unittest.main()
