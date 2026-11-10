"""Selbsterkundung wie Erkundung.h im Sketch, Takt für Takt gleich und ganzzahlig.

Der Knoten sucht unter freien Pins selbst einen, der ihn kühlt, und setzt ihn danach bei Wärme ein.
Den Ablauf beschreibt Erkundung.h. Diese Fassung rechnet nach, was das Gerät gemeldet hat, und ist das
Vorbild der Tests. Jede Abweichung vom Header ist ein Fehler, auch eine in der Reihenfolge der Zufallszahlen.
"""
from math import isqrt

MAX_PINS, MAX_FENSTER, MAX_ZEILEN, MAX_TEMP = 24, 8, 4, 2000
# Pins, die der Sketch am ESP32-S3 N16R8 überhaupt prüft, in dieser Reihenfolge. Nie dabei: 0, 3, 45, 46
# (Strapping), 19 und 20 (USB), 26 bis 37 (Flash und PSRAM), 43 und 44 (UART0 für Serial), 48 (RGB-LED).
ERLAUBTE_PINS = (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21, 38, 39, 40, 41, 42, 47)
# Passive Probe mit Pull-up und Pull-down: F folgt beiden (frei), M bleibt tief (Last gegen Masse, etwa
# eine Transistorbasis), P bleibt hoch (etwas zieht oder treibt nach Plus), U verhält sich verkehrt herum.
# Geschaltet werden nur F und M.
KLASSEN = "FMPU"
KANDIDATEN = "FM"
URTEILE = ("OFFEN", "VERDACHT", "KUEHLT", "KEINE")
GRUENDE = ("PROBE", "PRUEFUNG", "EINSATZ", "WECHSEL")
_M32 = 0xFFFFFFFF


def rund(a, b):
    """a/b als ganze Zahl, halbe vom Betrag her aufwärts, wie rund() in Erkundung.h. Verlangt b > 0."""
    return (2 * a + b) // (2 * b) if a >= 0 else -((-2 * a + b) // (2 * b))


def kandidaten(klassen):
    """Die Pins, die geschaltet werden dürfen, aufsteigend, aus {pin: klasse} der Probe."""
    return sorted(pin for pin, klasse in klassen.items() if klasse in KANDIDATEN)


class Erkundung:
    """Wie struct Erkundung. takt() nimmt die Temperatur in Zehntelgrad, None heißt nicht lesbar, und gibt
    die Zeilen zurück, die das Gerät nach der Körperzeile dieses Takts sendet. ein[i] ist danach der
    Zustand des i-ten Kandidaten."""

    def __init__(self, pins, ruhe, an, mittel, schwelle, fenster, pruefe, saat, warm):
        pins = list(pins)
        zahlen = (ruhe, an, mittel, schwelle, fenster, pruefe, saat)
        if (not 1 <= len(pins) <= MAX_PINS or not all(type(p) is int and 0 <= p <= 255 for p in pins)
                or not all(type(w) is int and 0 <= w <= _M32 for w in zahlen) or type(warm) is not int
                or not 1 <= mittel <= min(ruhe, an) or ruhe > 3600 or an > 3600 or not 1 <= schwelle <= 1000
                or not 3 <= fenster <= MAX_FENSTER or pruefe > 86400 or not saat
                or any(b <= a for a, b in zip(pins, pins[1:]))):
            raise ValueError("Ungültige Erkundung: Pins aufsteigend, 1 <= mittel <= ruhe, an <= 3600, "
                             "1 <= schwelle <= 1000, 3 <= fenster <= 8, pruefe <= 86400, saat nicht 0.")
        self.n, self.nummer = len(pins), pins
        self.ruhe, self.an_takte, self.mittel, self.schwelle = ruhe, an, mittel, schwelle
        self.fenster, self.pruefe, self.zufall, self.warm = fenster, pruefe, saat, warm
        self.runde, self.runde_pos = list(range(self.n)), self.n
        self.ein = [False] * self.n
        self.letzter_wechsel = [0] * self.n
        self.werte = [[0] * fenster for _ in range(self.n)]
        self.versuche = [0] * self.n
        self.kopf = [0] * self.n
        self.modus, self.phase = "ERKUNDEN", "VOR"
        self.schritt = self.zahl = self.vor_zahl = self.seit_pruefung = 0
        self.summe = self.vor_summe = 0
        self.ziel = self.kuehler = 0
        self.probe = self.abschalten = self.pruefe_kuehler = False
        self.zeilen = []

    def takt(self, t, temp):
        self.zeilen = []
        gueltig = temp is not None and 0 <= temp <= MAX_TEMP
        if self.phase == "REGEL":
            self._regle(t, gueltig, temp)
            if self.pruefe:
                self.seit_pruefung += 1
                if self.seit_pruefung >= self.pruefe:
                    self._beginne()
            return self.zeilen
        self.schritt += 1
        laenge = self.ruhe if self.phase == "VOR" else self.an_takte
        if self.schritt > laenge - self.mittel and gueltig:
            self.summe += temp
            self.zahl += 1
        if self.schritt >= laenge:
            if self.phase == "VOR":
                self._schalte_um(t)
            else:
                self._werte_aus(t)
        return self.zeilen

    def urteil(self, i):
        k, s, q = self.versuche[i], self._summe(i), self._quadrate(i)
        a = -s - k * self.schwelle * self.mittel
        if k >= 3 and a >= 0 and a * a * (k - 1) >= 4 * (k * q - s * s):
            return "KUEHLT"
        if k >= 1 and a >= 0 and k < self.fenster:
            return "VERDACHT"
        return "KEINE" if k >= 3 else "OFFEN"

    def _beginne(self):
        self.phase, self.schritt, self.summe, self.zahl = "VOR", 0, 0, 0

    def _regeln(self, neu):
        self.phase, self.seit_pruefung = "REGEL", 0
        if neu:
            self.pruefe_kuehler = True

    def _schalte_um(self, t):
        self.vor_summe, self.vor_zahl = self.summe, self.zahl
        if self.modus == "ERKUNDEN":
            self.ziel, self.probe = self._waehle(), True
        else:
            anderer = None if self.pruefe_kuehler else self._anderen()
            self.probe = anderer is not None
            self.ziel = anderer if self.probe else self.kuehler
            self.pruefe_kuehler = not self.pruefe_kuehler
        self.abschalten = self.ein[self.ziel]
        self._schalte(t, self.ziel, not self.abschalten, "PROBE" if self.probe else "PRUEFUNG")
        self.phase, self.schritt, self.summe, self.zahl = "NACH", 0, 0, 0

    def _werte_aus(self, t):
        if self.probe:
            self._schalte(t, self.ziel, False, "PROBE")
        vollstaendig = self.vor_zahl == self.mittel and self.zahl == self.mittel
        wirkung = 0
        if vollstaendig:
            wirkung = self.vor_summe - self.summe if self.abschalten else self.summe - self.vor_summe
            self._merke(self.ziel, wirkung)
        self._melde_versuch(t, vollstaendig, wirkung)
        bester = self._bester_kuehler()
        if self.modus == "ERKUNDEN":
            if bester is not None:
                self.modus, self.kuehler = "EINSATZ", bester
                self._regeln(True)
            else:
                self._beginne()
            return
        if bester is None or bester != self.kuehler:
            if self.ein[self.kuehler]:
                self._schalte(t, self.kuehler, False, "WECHSEL")
            if bester is None:
                self.modus = "ERKUNDEN"
                self._beginne()
                return
            self.kuehler = bester
            self._regeln(True)
            return
        self._regeln(False)

    def _regle(self, t, gueltig, temp):
        k = self.kuehler
        if not gueltig or t - self.letzter_wechsel[k] < self.mittel:
            return
        if not self.ein[k] and temp >= self.warm:
            self._schalte(t, k, True, "EINSATZ")
        elif self.ein[k] and temp <= self.warm - 10:
            self._schalte(t, k, False, "EINSATZ")

    def _schalte(self, t, i, wert, grund):
        self.ein[i], self.letzter_wechsel[i] = wert, t
        if len(self.zeilen) < MAX_ZEILEN:
            self.zeilen.append(f"PIN,{t},{self.nummer[i]},{int(wert)},{grund}")

    def _waehle(self):
        beste = None
        for i in range(self.n):
            if self.urteil(i) == "VERDACHT" and (beste is None or self._kleiner_mittel(i, beste)):
                beste = i
        return beste if beste is not None else self._aus_runde()

    def _anderen(self):
        if self.n < 2:
            return None
        while True:
            i = self._aus_runde()
            if i != self.kuehler:
                return i

    def _aus_runde(self):
        if self.runde_pos >= self.n:
            for i in range(self.n - 1, 0, -1):
                j = self._zufallszahl() % (i + 1)
                self.runde[i], self.runde[j] = self.runde[j], self.runde[i]
            self.runde_pos = 0
        i = self.runde[self.runde_pos]
        self.runde_pos += 1
        return i

    def _zufallszahl(self):
        x = self.zufall
        x ^= (x << 13) & _M32
        x ^= x >> 17
        x ^= (x << 5) & _M32
        self.zufall = x
        return x

    def _merke(self, i, wirkung):
        self.werte[i][self.kopf[i]] = wirkung
        self.kopf[i] = (self.kopf[i] + 1) % self.fenster
        if self.versuche[i] < self.fenster:
            self.versuche[i] += 1

    def _summe(self, i):
        return sum(self.werte[i][:self.versuche[i]])

    def _quadrate(self, i):
        return sum(w * w for w in self.werte[i][:self.versuche[i]])

    def _kleiner_mittel(self, i, j):
        return self._summe(i) * self.versuche[j] < self._summe(j) * self.versuche[i]

    def _bester_kuehler(self):
        bester = None
        for i in range(self.n):
            if self.urteil(i) == "KUEHLT" and (bester is None or self._kleiner_mittel(i, bester)):
                bester = i
        return bester

    def _melde_versuch(self, t, vollstaendig, wirkung):
        if len(self.zeilen) >= MAX_ZEILEN:
            return
        i, m = self.ziel, self.mittel
        k, s, q = self.versuche[i], self._summe(i), self._quadrate(i)
        mittel_hg = rund(s * 10, k * m) if k else 0
        streuung_hg = isqrt((k * q - s * s) * 100 // (k * (k - 1) * m * m)) if k >= 2 else 0
        werte = (f"{rund(self.vor_summe * 10, m)},{rund(self.summe * 10, m)},{rund(wirkung * 10, m)}"
                 if vollstaendig else "-,-,-")
        self.zeilen.append(f"VERSUCH,{t},{self.nummer[i]},{'AUS' if self.abschalten else 'AN'},{werte},"
                           f"{mittel_hg},{streuung_hg},{k},{self.urteil(i)}")
