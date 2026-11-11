import unittest
import empfinden_vergleich as v

class VergleichTests(unittest.TestCase):
    def zeile(self,takt,anlauf,w):
        return dict(takt=takt,n=2000,nw=0,ng=0,alt=1,alte_grenze_mg=800,neu=[2,w,anlauf,1,200,500,37000,37000])

    def test_nenner_und_led_stufe_eins(self):
        a=[self.zeile(3,1,0),self.zeile(4,0,1)]
        b=[self.zeile(3,0,-1),self.zeile(4,0,1)]
        r=v.vergleich(a,b)
        self.assertEqual(r['1']['eigen']['n'],1)
        self.assertEqual(r['2']['eigen']['n'],2)
        self.assertEqual(r['2']['gemeinsam']['n'],1)
        self.assertEqual(r['1']['nach_kalt']['wort_gesperrt'],1)
        self.assertEqual(r['2']['eigen']['woanders_ab_2'],0)
        self.assertEqual(r['2']['eigen']['woanders_led_aktiv'],2)
        self.assertEqual(r['2']['eigen']['woanders_led_impulse'],1)
        self.assertEqual(r['1']['nach_kalt']['alt'],2)

    def test_nicht_ausgerichtete_lauefe_abgelehnt(self):
        with self.assertRaises(ValueError): v.vergleich([self.zeile(3,0,1)],[self.zeile(4,0,1)])

    def test_fahrt_42600_takte_cpp_python_und_laden(self):
        import copy
        import subprocess
        import tempfile
        from pathlib import Path
        import fahrt
        import empfinden as em
        import selbstvorhersage as sv
        import empfinden_auswertung as aus
        records=list(fahrt.saetze((aus.ROH/v.DATEIEN[3]).read_bytes()))
        cpp=r'''
#include <cstdio>
#include "Vorhersage.h"
#include "Empfinden.h"
int main(){
 Selbstvorhersage v; Empfinden e; v.starte(); e.starte();
 uint8_t vs[sizeof(v)]={},es[Empfinden::standBytes]; bool gespeichert=false;
 unsigned t,action;int temp,last;
 while(scanf("%u %d %d %u",&t,&temp,&last,&action)==4){
  if(action){
   if(action==2){v.starte();e.starte();}
   else {
    if(gespeichert&&!v.importiere(vs))return 2;
    e.exportiere(es); e=Empfinden(); if(!e.importiere(es))return 3;
   }
   e.neustart();
  }
  v.takt(t,temp!=-32768,temp,last);e.takt(t,temp!=-32768,temp,v.hatFehler(),v.mittel());
  puts(e.zeile());
  if(t%30==0){v.exportiere(vs);gespeichert=true;}
 }
 e.exportiere(es);for(auto b:es)printf("%02x",b);puts("");
}'''
        expected=[];lines=[];e=em.Empfinden();s=sv.Selbstvorhersage();checkpoint=None
        for r in records:
            action=2 if r['neustart'] and r['bei_null'] else int(r['neustart'])
            if action:
                if action==2:s=sv.Selbstvorhersage();e=em.Empfinden()
                elif checkpoint is not None:s=copy.deepcopy(checkpoint)
                neu=em.Empfinden();neu.importiere(e.exportiere());e=neu;e.neustart()
            z=s.takt(r['temp_dc'],r['last'])
            expected.append(em.zeile(r['takt'],e.takt(r['temp_dc'],None if z is None else z['mittel'])))
            lines.append(f"{r['takt']} {r['temp_dc'] if r['temp_dc'] is not None else -32768} {r['last']} {action}\n")
            if r['takt']%30==0:checkpoint=copy.deepcopy(s)
        with tempfile.TemporaryDirectory() as td:
            src=Path(td,'test.cpp');exe=Path(td,'test');src.write_text(cpp)
            subprocess.run(['c++','-std=c++11','-O2','-ffp-contract=off','-I',str(aus.ROOT/'esp32/Lernknoten'),str(src),'-o',str(exe)],check=True)
            got=subprocess.run([str(exe)],input=''.join(lines),text=True,capture_output=True,check=True).stdout.splitlines()
        self.assertEqual(got[:-1],expected)
        self.assertEqual(got[-1],e.exportiere().hex())
        self.assertEqual(len(expected),42600)
