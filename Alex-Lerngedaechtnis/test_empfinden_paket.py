import random
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
import empfinden_paket as p

ROOT=Path(__file__).parent

class EmpfindenPaketTests(unittest.TestCase):
    def test_cpp_python_10000_pakete_und_beschaedigung(self):
        rng=random.Random(20261111);werte=[]
        flags=[f for f in range(128) if p.gueltig(p.Zustand(0,370,bits=f))]
        for _ in range(10000):werte.append(p.Zustand(rng.randrange(2**32),rng.choice([-32768,rng.randrange(-1000,2001)]),rng.randrange(-30,31),rng.randrange(-30,31),rng.choice(flags)))
        cpp=r"""
#include <cstdio>
#include "EmpfindenPaket.h"
int main() {
 unsigned t,b;int temp,g,w;uint8_t buf[12];
 while(scanf("%u %d %d %d %u",&t,&temp,&g,&w,&b)==5) {
  EmpfindenPaket::Zustand z,neu;z.takt=t;z.temp=temp;z.gerade=g;z.woanders=w;z.bits=b;
  if(!EmpfindenPaket::packe(z,buf)||!EmpfindenPaket::entpacke(buf,12,neu))return 2;
  if(neu.takt!=t || neu.temp!=temp || neu.gerade!=g || neu.woanders!=w || neu.bits!=b)return 3;
  for(unsigned i=0;i<12;++i)printf("%02x",buf[i]);puts("");
  for(unsigned k=0;k<96;++k) {buf[k/8]^=1u<<(k%8);if(EmpfindenPaket::entpacke(buf,12,neu))return 4;buf[k/8]^=1u<<(k%8);}
  if(EmpfindenPaket::entpacke(buf,11,neu)||EmpfindenPaket::entpacke(buf,13,neu))return 5;
 }
}
"""
        with tempfile.TemporaryDirectory() as d:
            quelle,exe=Path(d,'paket.cpp'),Path(d,'paket');quelle.write_text(cpp)
            subprocess.run(['c++','-std=c++11','-O2','-I',str(ROOT/'esp32/Gemeinsam'),str(quelle),'-o',str(exe)],check=True)
            aus=subprocess.check_output([str(exe)],input=''.join(f'{z.takt} {z.temp} {z.gerade} {z.woanders} {z.bits}\n' for z in werte),text=True).splitlines()
        self.assertEqual(len(aus),len(werte))
        for z,b in zip(werte,aus):
            self.assertEqual(b,p.packe(z).hex());self.assertEqual(p.entpacke(bytes.fromhex(b)),z)
        b=p.packe(p.Zustand(0x12345678,370,-3,2,2))
        self.assertEqual(b[:11],bytes.fromhex('4f01785634127201fd0202'))
        for k in range(96):
            bad=bytearray(b);bad[k//8]^=1<<(k%8)
            with self.assertRaises(ValueError):p.entpacke(bad)
        for bits in (128,12,96,34,66):
            bad=bytearray(b);bad[10]=bits;bad[11]=p.crc(bad[:11])
            with self.assertRaises(ValueError):p.entpacke(bad)
        for bad in (b[:-1],b+b'0'):
            with self.assertRaises(ValueError):p.entpacke(bad)

    def test_empfang_duplikat_reihenfolge_ausfall_und_zeitumlauf(self):
        cpp=r"""
#include "EmpfindenPaket.h"
int main() {
 EmpfindenPaket::Empfang e;EmpfindenPaket::Zustand z;z.temp=370;z.takt=100;
 if(!e.alt(0)||!e.uebernehme(z,0xfffffff0u))return 1;
 if(e.uebernehme(z,0xfffffff1u))return 2;
 z.takt=99;if(e.uebernehme(z,0xfffffff2u))return 3;
 if(e.alt(100))return 4;
 if(!e.alt(6000))return 5;
 z.takt=100;if(e.uebernehme(z,6000))return 8;
 z.takt=1;if(!e.uebernehme(z,6001)||e.alt(6002))return 6;
 z.takt=0xffffffffu;EmpfindenPaket::Empfang f;f.uebernehme(z,0);
 z.takt=0;if(!f.uebernehme(z,1))return 7;
}
"""
        with tempfile.TemporaryDirectory() as d:
            pth,exe=Path(d,'test.cpp'),Path(d,'test');pth.write_text(cpp)
            subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-I',str(ROOT/'esp32/Gemeinsam'),str(pth),'-o',str(exe)],check=True)
            subprocess.run([str(exe)],check=True)

    def test_reine_zeichenlogik_alle_zustaende_und_stufen(self):
        from gesicht_bilder import formen
        werte=[(123,370,g,w,b,0) for b in (0,2,32,64) for g in range(-6,7) for w in (-3,0,3)]
        bilder=formen(werte)
        for z,b in zip(werte,bilder):
            self.assertEqual(b['wort'],{0:'ruhig',2:'ueberrascht',32:'am Suchen',64:'erklaert'}[z[4]])
            augen=[f for f in b['formen'] if f[0]==0][:4:2]
            self.assertEqual(len(augen),2)
            self.assertEqual(augen[0][3],10+2*abs(z[2]))
            self.assertEqual(b['hintergrund'],0x101e32 if z[3]<0 else 0x2c1d13 if z[3]>0 else 0x111921)
            dreiecke=[f for f in b['formen'] if f[0]==3]
            if z[2]:self.assertEqual(dreiecke[0][2]<dreiecke[0][4],z[2]>0)
            else:self.assertEqual(dreiecke,[])
        a=formen([(0,370,0,0,9,0),(0,-32768,0,0,0,0),(0,370,5,3,2,1)])
        self.assertEqual([x['wort'] for x in a],['ANLAUF','MESSUNG FEHLT','KEIN SIGNAL'])
        self.assertEqual(a[0]['hinweis'],'AUSFALL')

if __name__=='__main__':unittest.main()
