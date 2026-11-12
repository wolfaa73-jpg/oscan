"""Fehlereinspritzung in echte Sketchfunktionen und Rücklesen aus dem Flashmodell."""
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import fahrt

ROOT=Path(__file__).parent
SKETCH=(ROOT/'esp32/Lernknoten/Lernknoten.ino').read_text()


def funktion(name):
    pos=SKETCH.index(name+'(')
    # Skip forward declarations when present.
    while SKETCH.find(';',pos)<SKETCH.find('{',pos):pos=SKETCH.index(name+'(',pos+len(name))
    start=SKETCH.rfind('\n',0,pos)+1
    ende=SKETCH.index('\n}',pos)+2
    return SKETCH[start:ende]


def cpp_lauf(source):
    with tempfile.TemporaryDirectory() as td:
        p=Path(td,'probe.cpp');exe=Path(td,'probe');p.write_text(source)
        subprocess.run(['c++','-std=c++11','-O2','-ffp-contract=off','-Wall','-Wextra','-Werror','-I',str(ROOT/'esp32/Lernknoten'),str(p),'-o',str(exe)],check=True,capture_output=True)
        return subprocess.run([str(exe)],text=True,capture_output=True)


class FahrtFunkTests(unittest.TestCase):
    def test_sendefehler_nur_fahrt_weiter_versuch_abbruch_mutante(self):
        vor=r'''
#include <cstdint>
#include <string>
#include "../Gemeinsam/EmpfindenPaket.h"
#define ARDUINO_ARCH_ESP32
struct Ser {template<class T>void print(T){} void println(const char*){}}Serial;
enum Zustand{OK,SCHWACH,AUSFALL};
struct Entscheidung{bool sofort=false,warnung=false;};
struct K {unsigned t=0;unsigned takt(){return t;}bool schritt(unsigned x,Zustand,Entscheidung&){t=x;return true;}}knoten;
struct V {void takt(unsigned,bool,int,unsigned){}const char*zeile(){return "";}bool hatFehler(){return true;}float mittel(){return 0;}}vorhersage;
struct E {void takt(unsigned,bool,int,bool,float){}const char*zeile(){return "";}int gerade(){return 0;}int woanders(){return 0;}bool aktiv(){return true;}bool anlauf(){return false;}}empfinden;
struct F {unsigned modus=2,fehler=56;bool plan=false;bool vorTakt(unsigned){return true;}unsigned senden(const EmpfindenPaket::Zustand&){return fehler;}}funk;
int grenzen=0;bool frischGeladen=false,fahrtAn=false;unsigned sichernAlle=0;
const char*namen[]={"OK","SCHWACH","AUSFALL"};
Zustand einstufen(bool,int,uint32_t,uint32_t,int){return OK;}
unsigned reize(){return 1;}
bool saveOK=true;bool lernstand(bool,bool){return saveOK;}
bool fahrtProtokollVoll(){return false;}
unsigned logCount=0,letzterReiz=0;
void fahrtTakt(bool,int32_t,unsigned reiz,Zustand,const Entscheidung&){++logCount;letzterReiz=reiz;}
'''
        nach=r'''
int main(){
 fahrtAn=true;
 for(unsigned i=0;i<90;++i)if(!koerperTakt(true,370,300000,1))return 1;
 if(logCount!=90 || letzterReiz!=57)return 2;
 funk.plan=true;if(koerperTakt(true,370,300000,1))return 3;
 funk.plan=false;fahrtAn=false;if(koerperTakt(true,370,300000,1))return 4;
 funk.fehler=24;if(!koerperTakt(true,370,300000,1))return 5;
 fahrtAn=true;sichernAlle=1;saveOK=false;if(koerperTakt(true,370,300000,1))return 6;
}'''
        body=funktion('koerperTakt')
        self.assertEqual(cpp_lauf(vor+body+nach).returncode,0)
        mutant=body.replace('(!(reiz & 32u) || (fahrtAn && !funk.plan))','!(reiz & 32u)')
        self.assertNotEqual(mutant,body)
        self.assertNotEqual(cpp_lauf(vor+mutant+nach).returncode,0)

    def test_funk_nvs_fehlender_schluessel_ohne_get(self):
        vor=r'''
#include <stdexcept>
struct Preferences{static bool da;static unsigned wert,reads;
 bool begin(const char*,bool){return true;}bool isKey(const char*){return da;}
 unsigned getUChar(const char*,unsigned){++reads;if(!da)throw std::runtime_error("missing");return wert;}
 unsigned putUChar(const char*,unsigned v){da=true;wert=v;return 1;}void end(){}};
bool Preferences::da=false;unsigned Preferences::wert=0,Preferences::reads=0;
'''
        nach='int main(){if(fahrtFunk()||Preferences::reads)return 1;if(!fahrtFunk(true,true)||!fahrtFunk())return 2;if(!fahrtFunk(true,false)||fahrtFunk())return 3;}'
        self.assertEqual(cpp_lauf(vor+funktion('fahrtFunk')+nach).returncode,0)

    def test_flash_export_erhaelt_alt_restart_zustand_und_sendefehler(self):
        vor=r'''
#include <cstdio>
#include <cstring>
#include <string>
#include <sstream>
#include <map>
#include <vector>
#include <algorithm>
#include "Fahrt.h"
#include "Vorhersage.h"
#include "Empfinden.h"
#define FILE_READ 0
#define FILE_WRITE 1
#define FILE_APPEND 2
std::map<std::string,std::vector<uint8_t>> disk;
std::string lesefehler;
struct File{
 std::vector<uint8_t>*v=nullptr;size_t pos=0;
 operator bool()const{return v!=nullptr;}
 size_t size()const{return v?v->size():0;}
 size_t read(uint8_t*p,size_t n){n=std::min(n,v->size()-pos);memcpy(p,v->data()+pos,n);pos+=n;return n;}
 size_t write(const uint8_t*p,size_t n){v->insert(v->end(),p,p+n);return n;}
 void close(){}
};
struct FS{
 bool begin(bool){return true;}bool exists(const char*p){return disk.count(p);}
 File open(const char*p,int mode){File f;if(mode==FILE_READ&&(!exists(p)||lesefehler==p))return f;f.v=&disk[p];if(mode==FILE_WRITE)f.v->clear();return f;}
 size_t totalBytes(){return 1000000;}size_t usedBytes(){return 0;}
 bool rename(const char*a,const char*b){disk[b]=disk[a];disk.erase(a);return true;}
}LittleFS;
struct Ser {std::ostringstream o;template<class T>void print(T x){o<<x;}template<class T>void println(T x){o<<x<<'\n';}}Serial;
Selbstvorhersage vorhersage;Empfinden empfinden;bool fahrtAn=true;
enum Zustand{OK,SCHWACH,AUSFALL};struct Entscheidung{bool warnung=false,sofort=false;};
unsigned esp_reset_reason(){return 6;}
'''
        start=SKETCH.index('const char *const fahrtLog =');end=SKETCH.index('\nbool fahrtLade()',start)
        body=SKETCH[start:end]+funktion('fahrtTakt')
        nach=r'''
int main(){
 uint8_t alt[16];Fahrtsatz::packe(alt,1,true,370,false,false,false,false,2,true,3,true,0,0,true,0,1);
 disk[fahrtLog]=std::vector<uint8_t>(alt,alt+16);auto original=disk[fahrtLog];
 vorhersage.starte();empfinden.starte();fahrtTaktNr=1;fahrtErster=true;
 Entscheidung e;
 for(unsigned i=0;i<60;++i){
  if(i==30)fahrtErster=true; // second saved block after a simulated restart
  vorhersage.takt(i+1,true,370,1);empfinden.takt(i+1,true,370,vorhersage.hatFehler(),vorhersage.mittel());
  fahrtTakt(true,370,i%3==0?57:25,static_cast<Zustand>(i%3),e);
 }
 if(fahrtVoll||disk[fahrtLog]!=original||disk[fahrtLogV2].size()!=1200)return 1;
 if(!fahrtLogSenden())return 2;
 std::printf("%s",Serial.o.str().c_str());
 disk[fahrtLogV2].push_back(7); // interrupted append must not be hidden or extended
 const auto kaputt=disk[fahrtLogV2];
 if(fahrtLogKorrekt()||fahrtLogSenden())return 3;
 fahrtSichere();if(!fahrtVoll||disk[fahrtLogV2]!=kaputt)return 4;
 disk[fahrtLogV2].pop_back();fahrtVoll=false;lesefehler=fahrtLog;
 if(fahrtLogKorrekt()||fahrtLogSenden())return 5;
 fahrtSichere();if(!fahrtVoll||disk[fahrtLogV2].size()!=1200)return 6;
}'''
        r=cpp_lauf(vor+body+nach);self.assertEqual(r.returncode,0,r.stderr)
        lines=r.stdout.splitlines();n=int(lines[0].split(',')[1]);data=bytes.fromhex(''.join(lines[1:-1]))
        self.assertEqual(len(data),n);self.assertEqual(fahrt.summe(data),int(lines[-1].split(',')[2]))
        rows=list(fahrt.saetze(data));self.assertEqual(len(rows),61)
        self.assertIsNone(rows[0]['reiz']);self.assertEqual(rows[0]['zustand'],'AUSFALL')
        for i,r in enumerate(rows[1:]):
            self.assertEqual(r['reiz'],57 if i%3==0 else 25)
            self.assertEqual(r['funk_sendefehler'],i%3==0)
            self.assertEqual(r['zustand'],fahrt.ZUSTAENDE[i%3])
            self.assertEqual(r['neustart'],int(i in (0,30)))
        self.assertIn('20 von 60',fahrt.bericht(rows))

    def test_v2_abgeschnitten_reserviert_und_version_abweisen(self):
        raw=fahrt.SATZ.pack(1,370,0,0,0,0,0,0)
        good=fahrt.V2_KOPF+raw+bytes((56,0,0,1))
        self.assertTrue(next(fahrt.saetze(good))['funk_sendefehler'])
        for n in range(8,len(good)):
            if n==16:continue # valid empty V2 stream
            with self.assertRaises(ValueError):list(fahrt.saetze(good[:n]))
        for pos,value in ((8,3),(12,16),(32,64),(33,1),(34,1),(35,2),(35,0)):
            bad=bytearray(good);bad[pos]=value
            with self.assertRaises(ValueError):list(fahrt.saetze(bytes(bad)))
        self.assertEqual(list(fahrt.saetze(raw))[0]['takt'],1)

    def test_stand_beider_formate(self):
        class Port:
            def __init__(self,line):self.line=line
            def write(self,b):pass
            def readline(self):return self.line
        for line,size,n in ((b'FAHRT,1,160,500000,10,0',16,10),
                            (b'FAHRT,1,216,500000,10,0,20,16',20,10),
                            (b'FAHRT,1,0,500000,0,0,20,0',20,0)):
            s=fahrt.stand(Port(line));self.assertEqual((s['satzbytes'],s['saetze']),(size,n))
