"""Die unveränderte Selbstgesicht-main.cpp mit modellierter Hardware prüfen.

Rechenkern, Flashablauf, Befehle und loop stammen aus der echten Firmware. Die
Stubs ersetzen nur Arduino/LCD/Dateisystem; keine Aussage über reale Stromausfälle.
"""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import fahrt

ROOT = Path(__file__).parent
FAKE = r'''
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <string>
#include <vector>
using std::isnan;
namespace Fake {
uint32_t now=0;
std::map<std::string,std::vector<uint8_t>> files;
std::set<std::string> unreadable,undeletable,lyingDelete;
unsigned writes=0;
}
#define FILE_READ 0
#define FILE_WRITE 1
#define FILE_APPEND 2
#define INPUT_PULLUP 0
#define SPI2_HOST 0
#define SPI_DMA_CH_AUTO 0
struct File {
 std::vector<uint8_t>*v=nullptr;size_t pos=0;
 operator bool()const{return v!=nullptr;}
 size_t size()const{return v?v->size():0;}
 bool seek(size_t n){pos=n;return v&&n<=v->size();}
 size_t read(uint8_t*p,size_t n){if(!v||pos>v->size())return 0;n=std::min(n,v->size()-pos);memcpy(p,v->data()+pos,n);pos+=n;return n;}
 size_t write(const uint8_t*p,size_t n){++Fake::writes;v->insert(v->end(),p,p+n);return n;}
 void close(){}
};
struct FS {
 bool begin(bool){return true;}
 bool exists(const char*p){return Fake::files.count(p);}
 File open(const char*p,int mode){
  File f;if(mode==FILE_READ&&(!exists(p)||Fake::unreadable.count(p)))return f;
  f.v=&Fake::files[p];if(mode==FILE_WRITE)f.v->clear();return f;
 }
 size_t totalBytes(){return 1000000;}size_t usedBytes(){return 0;}
 bool rename(const char*a,const char*b){Fake::files[b]=Fake::files[a];Fake::files.erase(a);return true;}
 bool remove(const char*p){if(Fake::undeletable.count(p))return false;if(Fake::lyingDelete.count(p))return true;return Fake::files.erase(p)>0;}
}LittleFS;
struct Ser {
 std::ostringstream out;std::string input;size_t pos=0;
 void begin(unsigned){}
 int available(){return pos<input.size();}int read(){return input[pos++];}
 template<class T>void print(T x){out<<x;}template<class T>void println(T x){out<<x<<'\n';}
 void clear(){out.str("");out.clear();}
 void command(const char*s){input=std::string(s)+"\n";pos=0;}
}Serial;
struct Preferences {
 bool begin(const char*,bool){return true;}bool isKey(const char*){return false;}
 unsigned getUChar(const char*,unsigned){return 0;}unsigned putUChar(const char*,unsigned){return 1;}void end(){}
};
uint32_t millis(){return Fake::now;}void delay(unsigned n){Fake::now+=n;}
void pinMode(unsigned,unsigned){}bool digitalRead(unsigned){return true;}
unsigned esp_reset_reason(){return 3;}float temperatureRead(){return 45.0f;}
const int middle_center=0;
namespace fonts {const int Font2=0;}
namespace lgfx {
struct Config {
 int spi_host=0,spi_mode=0,freq_write=0,freq_read=0,dma_channel=0,pin_sclk=0,pin_mosi=0,pin_miso=0,pin_dc=0;
 bool spi_3wire=false,use_lock=false;
 int pin_cs=0,pin_rst=0,pin_busy=0,panel_width=0,panel_height=0,memory_width=0,memory_height=0,offset_x=0,offset_y=0;
 bool invert=false,rgb_order=false,readable=false,bus_shared=false;
 int pin_bl=0,freq=0,pwm_channel=0;
};
struct Component {Config config(){return {};}void config(Config){}template<class T>void setBus(T*){}template<class T>void setLight(T*){}};
using Panel_GC9A01=Component;using Bus_SPI=Component;using Light_PWM=Component;
struct LGFX_Device {
 template<class T>void setPanel(T*){}void init(){}void setRotation(unsigned){}void setBrightness(unsigned){}
 void startWrite(){}void endWrite(){}void fillScreen(uint32_t){}void setTextColor(uint32_t,uint32_t){}void setTextDatum(int){}
 template<class T>void setFont(T*){}template<class...T>void drawString(T...){}
 template<class...T>void fillEllipse(T...){}template<class...T>void drawLine(T...){}
 template<class...T>void fillRect(T...){}template<class...T>void fillTriangle(T...){}
};
}
'''
DRIVER = r'''
#include "firmware.cpp"
void tick(){Fake::now+=1000;loop();}
void prepare(unsigned n){setup();for(unsigned i=0;i<n;++i)tick();Serial.clear();}
void command(const char*s){Serial.command(s);loop();}
int main(int argc,char**argv){
 if(argc!=2)return 99;const std::string mode=argv[1];
 if(mode=="normal"||mode=="diagnose"){
  prepare(659);if(mode=="diagnose"){command("ZEILEN 1");Serial.clear();}
  const unsigned before=selbst.takt;const auto n=Fake::files[logPfad].size()/20;
  command("FAHRTLOG");while(sendet)tick();
  std::cout<<Serial.out.str();Serial.clear();tick();
  const bool resumed=Serial.out.str().find("EMPFINDEN,")!=std::string::npos;
  std::cerr<<"{\"records\":"<<n<<",\"stored_after\":"<<Fake::files[logPfad].size()/20
   <<",\"ticks\":"<<selbst.takt-before<<",\"resumed\":"<<(resumed?"true":"false")<<"}";
 }else if(mode=="read_download"||mode=="read_status"){
  prepare(90);Fake::unreadable.insert(logPfad);
  command(mode=="read_download"?"FAHRTLOG":"FAHRTSTAND");std::cout<<Serial.out.str();
 }else if(mode=="empty"||mode=="missing"){
  prepare(0);if(mode=="empty")Fake::files[logPfad]={};
  command("FAHRTLOG");std::cout<<Serial.out.str();
 }else if(mode=="read_save"||mode=="read_boot"){
  prepare(90);const auto before=Fake::files;const auto writes=Fake::writes;
  Fake::unreadable.insert(logPfad);
  if(mode=="read_boot")beginne(3);
  for(unsigned i=0;i<60;++i)tick();
  std::cerr<<"{\"unchanged\":"<<(Fake::files==before?"true":"false")
    <<",\"writes\":"<<Fake::writes-writes<<",\"full\":"<<(voll?"true":"false")<<"}";
 }else if(mode=="delete_log"||mode=="delete_state"||mode=="delete_temp"||mode=="delete_lie"||mode=="delete_ok"){
  prepare(90);Fake::files[standNeu]={1,2,3};
  if(mode=="delete_log")Fake::undeletable.insert(logPfad);
  if(mode=="delete_state")Fake::undeletable.insert(standPfad);
  if(mode=="delete_temp")Fake::undeletable.insert(standNeu);
  if(mode=="delete_lie")Fake::lyingDelete.insert(logPfad);
  command("FAHRTLEER");std::cout<<Serial.out.str();Serial.clear();
  const unsigned after=selbst.takt;const auto snapshot=Fake::files;const auto writes=Fake::writes;
  for(unsigned i=0;i<60;++i)tick();
  const bool stopped=Fake::writes==writes && Fake::files==snapshot;
  Fake::undeletable.clear();Fake::lyingDelete.clear();
  Serial.clear();command("FAHRTLEER");
  const bool retry=selbst.takt==0 && Fake::files.empty() && Serial.out.str().find("FAHRT,leer")!=std::string::npos;
  for(unsigned i=0;i<30;++i)tick();
  std::cerr<<"{\"takt_after_command\":"<<after<<",\"writes_stopped\":"<<(stopped?"true":"false")
    <<",\"retry_ok\":"<<(retry?"true":"false")<<",\"new_records\":"<<Fake::files[logPfad].size()/20<<"}";
 }else if(mode=="export_error"){
  prepare(659);zeilen=true;command("FAHRTLOG");
  Fake::unreadable.insert(logPfad);tick();
  const bool ended=!sendet;Serial.clear();tick();
  std::cerr<<"{\"ended\":"<<(ended?"true":"false")<<",\"resumed\":"
    <<(Serial.out.str().find("EMPFINDEN,")!=std::string::npos?"true":"false")<<"}";
 }else return 98;
}
'''


class SelbstgesichtFlashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        d = Path(cls.tmp.name)
        (d/'Fake.h').write_text(FAKE)
        for name in ('Arduino.h','LittleFS.h','Preferences.h','LovyanGFX.hpp'):
            (d/name).write_text('#include "Fake.h"\n')
        # Include the actual unchanged source, without extracting/reimplementing its functions.
        (d/'firmware.cpp').write_text('#include "'+(ROOT/'esp32/Selbstgesicht/src/main.cpp').as_posix()+'"\n')
        (d/'driver.cpp').write_text(DRIVER)
        cls.exe = d/'probe'
        subprocess.run(['c++','-std=c++17','-O2','-ffp-contract=off','-Wall','-Wextra','-Werror',
                        '-I',str(d),str(d/'driver.cpp'),'-o',str(cls.exe)],check=True,capture_output=True)

    def run_case(self, name):
        r = subprocess.run([str(self.exe),name],capture_output=True,text=True,check=True)
        return r.stdout, json.loads(r.stderr) if r.stderr else {}

    def download(self, text):
        class Port:
            def __init__(self): self.lines=iter(text.encode().splitlines(keepends=True))
            def write(self,_): pass
            def readline(self): return next(self.lines,b'')
        return list(fahrt.saetze(fahrt.holen(Port())))

    def test_download_snapshot_bei_weiterlaufendem_schreiben(self):
        text,meta=self.run_case('normal')
        rows=self.download(text)
        self.assertEqual(len(rows),630)
        self.assertEqual([r['takt'] for r in rows],list(range(1,631)))
        self.assertGreater(meta['stored_after'],meta['records'])
        self.assertGreater(meta['ticks'],0)
        self.assertFalse(meta['resumed'])

    def test_diagnose_pause_und_fortsetzung_ohne_lernpause(self):
        text,meta=self.run_case('diagnose')
        self.assertEqual(len(self.download(text)),630)
        self.assertNotIn('EMPFINDEN,',text)
        self.assertNotIn('VORHERSAGE,',text)
        self.assertTrue(meta['resumed'])
        self.assertGreater(meta['ticks'],0)
        self.assertGreater(meta['stored_after'],meta['records'])

    def test_download_lesefehler_ist_keine_leere_datei(self):
        text,_=self.run_case('read_download')
        self.assertIn('FEHLER',text)
        self.assertNotIn('FAHRTLOG,0',text)
        with self.assertRaises(ValueError):self.download(text)

    def test_status_lesefehler_ist_kein_leeres_protokoll(self):
        text,_=self.run_case('read_status')
        self.assertIn('FEHLER',text)
        self.assertNotIn('FAHRT,1,0',text)

    def test_echt_leere_und_fehlende_datei_bleiben_lesbar(self):
        for name in ('empty','missing'):
            with self.subTest(name=name):
                text,_=self.run_case(name)
                self.assertEqual(self.download(text),[])

    def test_lesefehler_sperrt_log_und_stand_schreiben(self):
        for name in ('read_save','read_boot'):
            with self.subTest(name=name):
                _,meta=self.run_case(name)
                self.assertTrue(meta['unchanged'])
                self.assertEqual(meta['writes'],0)
                self.assertTrue(meta['full'])

    def test_loeschfehler_kein_erfolg_keine_folgeschreibvorgaenge(self):
        for name in ('delete_log','delete_state','delete_temp','delete_lie'):
            with self.subTest(name=name):
                text,meta=self.run_case(name)
                self.assertIn('FEHLER',text)
                self.assertNotIn('FAHRT,leer',text)
                self.assertEqual(meta['takt_after_command'],90)
                self.assertTrue(meta['writes_stopped'])
                self.assertTrue(meta['retry_ok'])
                self.assertEqual(meta['new_records'],30)

    def test_erfolgreiches_leeren_startet_bei_null(self):
        text,meta=self.run_case('delete_ok')
        self.assertIn('FAHRT,leer',text)
        self.assertEqual(meta['takt_after_command'],0)
        self.assertTrue(meta['retry_ok'])
        self.assertEqual(meta['new_records'],30)

    def test_diagnose_nach_abgebrochenem_export_wieder_aktiv(self):
        _,meta=self.run_case('export_error')
        self.assertTrue(meta['ended'])
        self.assertTrue(meta['resumed'])
