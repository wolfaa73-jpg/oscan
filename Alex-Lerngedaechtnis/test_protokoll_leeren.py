"""FAHRTLOGLEER: nur das Protokoll löschen, Gedächtnis und Takt behalten.

Wie test_selbstgesicht_flash.py wird die unveränderte main.cpp des Selbstgesichts mit modellierter Hardware
übersetzt. Dazu bekommt das nachgebildete Dateisystem eine Größe, damit das Protokoll wirklich voll werden
kann. Der Knoten (Lernknoten.ino) lässt sich auf dem Rechner nicht übersetzen; seine Änderung ist dieselbe
Schleife über zwei Dateien und wird mit dem Bau geprüft. Keine Aussage über reale Flash-Ausfälle.
"""
import contextlib
import io
import json
import re
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import fahrt
import test_selbstgesicht_flash as basis

ROOT = Path(__file__).parent

FAKE = basis.FAKE
for alt, neu in (
    ("unsigned writes=0;", "unsigned writes=0;size_t total=1000000;"),
    ("size_t totalBytes(){return 1000000;}size_t usedBytes(){return 0;}",
     "size_t totalBytes(){return Fake::total;}"
     "size_t usedBytes(){size_t s=0;for(auto&f:Fake::files)s+=f.second.size();return s;}"),
):
    assert alt in FAKE, alt
    FAKE = FAKE.replace(alt, neu, 1)

DRIVER = r'''
#include "firmware.cpp"
void tick(){Fake::now+=1000;loop();}
void prepare(unsigned n){setup();for(unsigned i=0;i<n;++i)tick();Serial.clear();}
void command(const char*s){Serial.command(s);loop();}
size_t used(){size_t s=0;for(auto&f:Fake::files)s+=f.second.size();return s;}
uint32_t firstTakt(){auto&v=Fake::files[logPfad];return v.size()>=4?(v[0]|v[1]<<8|v[2]<<16|(uint32_t)v[3]<<24):0;}
const char*B(bool b){return b?"true":"false";}
int main(int argc,char**argv){
 if(argc!=2)return 99;const std::string mode=argv[1];
 if(mode=="voll"){
  prepare(90);Fake::total=reserve+used();for(unsigned i=0;i<60;++i)tick();
  const bool fullBefore=voll;const size_t logBefore=Fake::files[logPfad].size()/20;const uint32_t takt0=selbst.takt;
  const auto stateBefore=Fake::files[standPfad];Serial.clear();
  command("FAHRTLOGLEER");std::cout<<"@@CMD\n"<<Serial.out.str();
  const bool logGone=!Fake::files.count(logPfad);const bool stateSame=Fake::files[standPfad]==stateBefore;
  const bool fullAfter=voll;const bool taktSame=selbst.takt==takt0;
  for(unsigned i=0;i<30;++i)tick();
  const size_t newRecords=Fake::files[logPfad].size()/20;const uint32_t first=firstTakt();
  Serial.clear();beginne(3);std::cout<<"@@START\n"<<Serial.out.str();
  Serial.clear();command("FAHRTLOG");while(sendet)tick();std::cout<<"@@LOG\n"<<Serial.out.str();
  std::cerr<<"{\"full_before\":"<<B(fullBefore)<<",\"log_before\":"<<logBefore<<",\"takt0\":"<<takt0
   <<",\"log_gone\":"<<B(logGone)<<",\"state_same\":"<<B(stateSame)<<",\"full_after\":"<<B(fullAfter)
   <<",\"takt_same\":"<<B(taktSame)<<",\"new_records\":"<<newRecords<<",\"first_takt\":"<<first<<"}";
 }else if(mode=="loeschfehler"){
  prepare(90);Fake::undeletable.insert(logPfad);const uint32_t takt0=selbst.takt;
  command("FAHRTLOGLEER");std::cout<<"@@CMD\n"<<Serial.out.str();Serial.clear();
  const auto snapshot=Fake::files;const auto writes=Fake::writes;for(unsigned i=0;i<60;++i)tick();
  const bool stopped=Fake::writes==writes&&Fake::files==snapshot;const bool fullDuring=voll;
  Fake::undeletable.clear();command("FAHRTLOGLEER");std::cout<<"@@RETRY\n"<<Serial.out.str();
  for(unsigned i=0;i<30;++i)tick();
  std::cerr<<"{\"takt0\":"<<takt0<<",\"writes_stopped\":"<<B(stopped)<<",\"full_during\":"<<B(fullDuring)
   <<",\"new_records\":"<<Fake::files[logPfad].size()/20<<",\"first_takt\":"<<firstTakt()
   <<",\"state_kept\":"<<B(Fake::files.count(standPfad))<<"}";
 }else if(mode=="lesefehler"){
  prepare(90);Fake::unreadable.insert(logPfad);for(unsigned i=0;i<30;++i)tick();
  const bool fullBefore=voll;Serial.clear();
  command("FAHRTLOGLEER");std::cout<<"@@CMD\n"<<Serial.out.str();
  Fake::unreadable.clear();  // Das Löschen räumt die unlesbare Datei weg; die neue ist wieder lesbar.
  for(unsigned i=0;i<30;++i)tick();
  std::cerr<<"{\"full_before\":"<<B(fullBefore)<<",\"full_after\":"<<B(voll)
   <<",\"new_records\":"<<Fake::files[logPfad].size()/20<<",\"first_takt\":"<<firstTakt()<<"}";
 }else if(mode=="export"){
  prepare(659);command("FAHRTLOG");const bool running=sendet;const auto log=Fake::files[logPfad];
  Serial.clear();command("FAHRTLOGLEER");const std::string answer=Serial.out.str();
  const bool stillRunning=sendet;const bool logSame=Fake::files[logPfad]==log;
  while(sendet)tick();
  std::cout<<"@@CMD\n"<<answer;
  std::cerr<<"{\"running\":"<<B(running)<<",\"still_running\":"<<B(stillRunning)<<",\"log_same\":"<<B(logSame)<<"}";
 }else if(mode=="ohne_log"){
  prepare(0);command("FAHRTLOGLEER");std::cout<<"@@CMD\n"<<Serial.out.str();
 }else return 98;
}
'''


def abschnitte(text):
    teile = re.split(r"^@@(\w+)\n", text, flags=re.M)
    return {teile[i]: teile[i + 1] for i in range(1, len(teile) - 1, 2)}


class ProtokollLeerenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        d = Path(cls.tmp.name)
        (d / 'Fake.h').write_text(FAKE)
        for name in ('Arduino.h', 'LittleFS.h', 'Preferences.h', 'LovyanGFX.hpp'):
            (d / name).write_text('#include "Fake.h"\n')
        (d / 'firmware.cpp').write_text('#include "' + (ROOT / 'esp32/Selbstgesicht/src/main.cpp').as_posix() + '"\n')
        (d / 'driver.cpp').write_text(DRIVER)
        cls.exe = d / 'probe'
        subprocess.run(['c++', '-std=c++17', '-O2', '-ffp-contract=off', '-Wall', '-Wextra', '-Werror',
                        '-I', str(d), str(d / 'driver.cpp'), '-o', str(cls.exe)], check=True, capture_output=True)

    def run_case(self, name):
        r = subprocess.run([str(self.exe), name], capture_output=True, text=True, check=True)
        return abschnitte(r.stdout), json.loads(r.stderr) if r.stderr else {}

    @staticmethod
    def download(text):
        class Port:
            def __init__(self): self.lines = iter(text.encode().splitlines(keepends=True))
            def write(self, _): pass
            def readline(self): return next(self.lines, b'')
        return list(fahrt.saetze(fahrt.holen(Port())))

    def test_volles_protokoll_wird_geleert_gedaechtnis_und_takt_bleiben(self):
        out, meta = self.run_case('voll')
        self.assertTrue(meta['full_before'])
        self.assertEqual(meta['log_before'], 90)
        self.assertIn('FAHRT,logleer', out['CMD'])
        self.assertNotIn('FEHLER', out['CMD'])
        self.assertTrue(meta['log_gone'])
        self.assertTrue(meta['state_same'])
        self.assertTrue(meta['takt_same'])
        self.assertFalse(meta['full_after'])

    def test_neues_protokoll_setzt_die_takte_fort_und_ist_lesbar(self):
        out, meta = self.run_case('voll')
        self.assertEqual(meta['new_records'], 30)
        self.assertEqual(meta['first_takt'], meta['takt0'] + 1)
        rows = self.download(out['LOG'])
        self.assertEqual([r['takt'] for r in rows], list(range(meta['takt0'] + 1, meta['takt0'] + 31)))

    def test_neustart_laedt_das_behaltene_gedaechtnis(self):
        out, meta = self.run_case('voll')
        self.assertIn(f"SELBST,laeuft,{meta['takt0'] + 30},geladen", out['START'])

    def test_loeschfehler_ist_kein_erfolg_und_sperrt_das_schreiben(self):
        out, meta = self.run_case('loeschfehler')
        self.assertIn('FEHLER', out['CMD'])
        self.assertNotIn('FAHRT,logleer', out['CMD'])
        self.assertTrue(meta['writes_stopped'])
        self.assertTrue(meta['full_during'])

    def test_erneuter_auftrag_nach_loeschfehler_gibt_das_schreiben_frei(self):
        out, meta = self.run_case('loeschfehler')
        self.assertIn('FAHRT,logleer', out['RETRY'])
        self.assertEqual(meta['new_records'], 30)
        self.assertEqual(meta['first_takt'], meta['takt0'] + 1 + 60)
        self.assertTrue(meta['state_kept'])

    def test_unlesbares_protokoll_laesst_sich_wegraeumen(self):
        out, meta = self.run_case('lesefehler')
        self.assertTrue(meta['full_before'])
        self.assertIn('FAHRT,logleer', out['CMD'])
        self.assertFalse(meta['full_after'])
        self.assertEqual(meta['new_records'], 30)
        self.assertEqual(meta['first_takt'], 121)

    def test_waehrend_eines_exports_wird_nichts_geloescht(self):
        out, meta = self.run_case('export')
        self.assertTrue(meta['running'])
        self.assertTrue(meta['still_running'])
        self.assertTrue(meta['log_same'])
        self.assertIn('FEHLER', out['CMD'])

    def test_ohne_protokoll_ist_der_befehl_gueltig(self):
        out, _ = self.run_case('ohne_log')
        self.assertIn('FAHRT,logleer', out['CMD'])
        self.assertNotIn('FEHLER', out['CMD'])


class FahrtPyTests(unittest.TestCase):
    def test_logleeren_braucht_ja_und_oeffnet_vorher_keinen_port(self):
        for aktion in ('leeren', 'logleeren'):
            with self.subTest(aktion=aktion), contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as e:
                    fahrt.main([aktion, '--port', '/dev/null'])
                self.assertEqual(e.exception.code, 2)
                self.assertIn('--ja', err.getvalue())

    def test_logleeren_schickt_den_richtigen_befehl_und_meldet_den_stand(self):
        geschrieben, antworten = [], {
            b'FAHRTLOGLEER\n': b'FAHRT,logleer\n',
            b'FAHRTSTAND\n': b'FAHRT,1,0,1000000,646130,0,20,0,1\n',
        }

        class Port:
            def __init__(self, *a, **k): self.antwort = b''
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def write(self, daten):
                geschrieben.append(daten)
                self.antwort = antworten.get(daten, b'')
            def readline(self):
                antwort, self.antwort = self.antwort, b''
                return antwort

        fake = types.SimpleNamespace(Serial=Port)
        with mock.patch.dict(sys.modules, {'serial': fake}), mock.patch.object(fahrt, 'ruhig', lambda p: []), \
                contextlib.redirect_stdout(io.StringIO()) as aus:
            self.assertEqual(fahrt.main(['logleeren', '--port', 'x', '--ja']), 0)
        self.assertEqual(geschrieben, [b'FAHRTLOGLEER\n', b'FAHRTSTAND\n'])
        self.assertIn('0 Sätze im Protokoll', aus.getvalue())
        self.assertNotIn('Hinweis', aus.getvalue())  # das Display läuft weiter, der Hinweis gilt nur für den Knoten


if __name__ == '__main__':
    unittest.main()
