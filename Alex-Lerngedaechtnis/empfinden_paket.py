"""12-Byte-Paket v1, Python-Zwilling von esp32/Gemeinsam/EmpfindenPaket.h."""
from dataclasses import dataclass
import struct
ANLAUF, UEBERRASCHT, SCHWACH, AUSFALL, VOLL, SUCHT, ERKLAERT = 1,2,4,8,16,32,64
KANAL=6
FORMAT=struct.Struct("<BBIhbbBB")

@dataclass(frozen=True)
class Zustand:
    takt: int
    temp: int
    gerade: int=0
    woanders: int=0
    bits: int=0

def crc(daten):
    c=0
    for b in daten:
        c^=b
        for _ in range(8): c=((c<<1)^(7 if c&128 else 0))&255
    return c

def gueltig(z):
    return (all(type(x) is int for x in (z.takt,z.temp,z.gerade,z.woanders,z.bits)) and 0<=z.takt<=0xffffffff
            and (z.temp==-32768 or -1000<=z.temp<=2000) and -30<=z.gerade<=30 and -30<=z.woanders<=30
            and 0<=z.bits<128 and not (z.bits&SCHWACH and z.bits&AUSFALL)
            and not (z.bits&SUCHT and z.bits&ERKLAERT) and not(z.bits&(SUCHT|ERKLAERT) and z.bits&UEBERRASCHT))

def packe(z):
    if not gueltig(z):raise ValueError("Ungültiger Zustand")
    b=FORMAT.pack(0x4f,1,z.takt,z.temp,z.gerade,z.woanders,z.bits,0)
    return b[:-1]+bytes([crc(b[:-1])])

def entpacke(b):
    if len(b)!=12:raise ValueError("Paketlänge")
    k,v,t,temp,g,w,bits,c=FORMAT.unpack(b)
    z=Zustand(t,temp,g,w,bits)
    if k!=0x4f or v!=1 or c!=crc(b[:-1]) or not gueltig(z):raise ValueError("Paket beschädigt oder unbekannt")
    return z
