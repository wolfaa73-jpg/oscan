"""Die gesamte Zuordnungstabelle unabhängig vom GPIO prüfen."""
from pathlib import Path
import subprocess
import tempfile
import unittest

class EmpfindenLedTests(unittest.TestCase):
    def test_alle_stufen_richtungen_prioritaeten_und_phasen(self):
        root=Path(__file__).parent
        cpp=r"""
#include <cstdio>
#include "EmpfindenLed.h"
int main() {
 for (int g=-30;g<=30;++g) for(int w=-30;w<=30;++w)
 for(int a=0;a<2;++a) for(int v=0;v<2;++v) for(unsigned t=0;t<4;++t) {
  const auto m=EmpfindenLed::muster(g,w,a,v);
  const auto c=EmpfindenLed::bild(m,t);
  printf("%d %d %d\n",c.r,c.g,c.b);
 }
}
"""
        with tempfile.TemporaryDirectory() as d:
            p,exe=Path(d,'led.cpp'),Path(d,'led');p.write_text(cpp)
            subprocess.run(['c++','-std=c++11','-Wall','-Wextra','-Werror','-I',str(root/'esp32/Lernknoten'),str(p),'-o',str(exe)],check=True)
            out=iter(subprocess.check_output([str(exe)],text=True).splitlines())
        counts=0
        def farbe(w,h): return (0,h//4,h) if w<0 else (h,h//4,0)
        for g in range(-30,31):
            for w in range(-30,31):
                for a in (False,True):
                    for v in (False,True):
                        for t in range(4):
                            if v: expected=(4,0,4)
                            elif a: expected=(2,2,2)
                            elif w and t==3: expected=farbe(w,min(4,abs(w)+1))
                            elif g: expected=farbe(g,[2,3,4,6,8,12,16][min(6,abs(g))])
                            else: expected=(0,2,0)
                            actual=tuple(map(int,next(out).split()))
                            self.assertEqual(actual,expected,(g,w,a,v,t));self.assertLessEqual(max(actual),16)
                            counts+=1
        self.assertEqual(counts,59536)
        self.assertIsNone(next(out,None))

if __name__=='__main__':unittest.main()
