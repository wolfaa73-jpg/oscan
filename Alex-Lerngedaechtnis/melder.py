"""Warnungen des Knotens per MQTT weitergeben, etwa an das Matrix-Panel.

Gesendet wird, wenn sich Zustand, Sofortmeldung oder Vorwarnung ändern, und sonst alle
herzschlag Sekunden, damit der Empfänger einen verstummten Sender erkennt. Jede Nachricht
bleibt beim Broker liegen (retained), ein neu verbundener Empfänger sieht sofort den Stand.

Der Melder darf eine Aufnahme nie stören: Er startet je Nachricht einen Kindprozess, wartet
nicht auf ihn und schluckt jeden Fehler. Fehlt der Broker, fehlen nur die Meldungen.

Der Kindprozess ist /usr/bin/python3 mit diesem Modul. macOS lässt die PlatformIO-Python, unter
der die Aufnahme läuft, nicht ins lokale Netz, mosquitto_pub aus Homebrew ebenso wenig
(Errno 65 bzw. "Bad file descriptor"). Deshalb spricht veroeffentliche() MQTT 3.1.1 selbst."""
import json
import socket
import subprocess
import sys
import time

THEMA = "oscan/warnung"


def _laenge(n):
    """Restlänge im festen Kopf, sieben Bit je Byte."""
    aus = bytearray()
    while True:
        n, b = divmod(n, 128)
        aus.append(b | (128 if n else 0))
        if not n:
            return bytes(aus)


def _text(t):
    t = t.encode("utf-8")
    return len(t).to_bytes(2, "big") + t


def veroeffentliche(host, thema, text, port=1883, frist=5.0):
    """Eine Nachricht mit QoS 0 und retain, dann trennen. Kein Paket außer der Standardbibliothek."""
    with socket.create_connection((host, port), frist) as s:
        s.settimeout(frist)
        rumpf = _text("MQTT") + bytes([4, 2, 0, 60]) + _text(f"oscan-melder-{time.time_ns() % 10**9}")
        s.sendall(b"\x10" + _laenge(len(rumpf)) + rumpf)
        if s.recv(4)[:4] != b"\x20\x02\x00\x00":
            raise OSError("Broker hat die Verbindung nicht angenommen.")
        rumpf = _text(thema) + text.encode("utf-8")
        s.sendall(b"\x31" + _laenge(len(rumpf)) + rumpf + b"\xe0\x00")


def sender(host, thema=THEMA, python="/usr/bin/python3"):
    """Sendefunktion über einen Kindprozess, ohne auf sein Ende zu warten."""
    laufend = []

    def senden(text):
        # Beendete Prozesse abräumen, hängende nach 10 s beenden, damit nichts aufläuft.
        for p in laufend[:]:
            if p.poll() is not None:
                laufend.remove(p)
            elif time.monotonic() - p.gestartet > 10:
                p.kill()
        try:
            p = subprocess.Popen([python, "-B", "-I", __file__, host, thema, text],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p.gestartet = time.monotonic()
            laufend.append(p)
        except OSError:
            pass
    return senden


class Melder:
    def __init__(self, senden, herzschlag=30.0, uhr=time.time):
        self.senden, self.herzschlag, self.uhr = senden, herzschlag, uhr
        self.letzter = None
        self.gesendet = None

    def _schicke(self, daten):
        try:
            self.senden(json.dumps(daten, separators=(",", ":")))
        except Exception:
            pass

    def takt(self, k):
        """k ist eine gelesene Körperzeile wie aus lies_koerperzeile."""
        jetzt = self.uhr()
        stand = (k["zustand"], int(k["sofort"]), int(k["vorwarnung"]))
        if stand == self.letzter and self.gesendet is not None and jetzt - self.gesendet < self.herzschlag:
            return
        self.letzter, self.gesendet = stand, jetzt
        self._schicke(dict(aktiv=True, zustand=stand[0], sofort=stand[1], vorwarnung=stand[2],
                           takt=k["takt"], ts=round(jetzt)))

    def ende(self):
        """Die Aufnahme ist vorbei. Der Empfänger zeigt dann nicht weiter den letzten Stand."""
        self._schicke(dict(aktiv=False, ts=round(self.uhr())))


if __name__ == "__main__":
    veroeffentliche(*sys.argv[1:4])
