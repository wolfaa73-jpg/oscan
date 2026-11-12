// Prüfstand am Rechner: dieselbe Selbst.h wie auf dem Display. Eingabe je Zeile "temp_dc last", temp_dc
// -32768 = nicht lesbar. Eine Zeile "N" ist ein Stromausfall: Stand sichern, alles vergessen, laden.
// Ausgabe je Takt: Vorhersagezeile (falls vorhanden), Empfindenzeile, Satz als Hex, Gesichtszustand.
#include <cstdio>
#include <cstring>
#include "Selbst.h"
#include "../Gemeinsam/GesichtFormen.h"
int main() {
    static Selbst s, leer;
    static uint8_t stand[Selbst::standBytes];
    s.beginne();
    char zeile[64];
    while (fgets(zeile, sizeof(zeile), stdin)) {
        if (zeile[0] == 'N') {
            s.exportiere(stand);
            const uint32_t takt = s.takt;
            s = leer;
            if (!s.importiere(stand, takt)) return 2;
            continue;
        }
        int temp, last;
        if (sscanf(zeile, "%d %d", &temp, &last) != 2) return 3;
        uint8_t satz[FahrtV2::bytes];
        const auto z = s.schritt(temp != -32768, temp, last, 1, false, satz);
        if (*s.vorhersage.zeile()) puts(s.vorhersage.zeile());
        puts(s.empfinden.zeile());
        for (unsigned i = 0; i < sizeof(satz); ++i) printf("%02x", satz[i]);
        const auto bild = Gesicht::zeichne(z, false);
        printf("\nGESICHT,%lu,%d,%d,%d,%u,%s\n", static_cast<unsigned long>(z.takt), z.temp, z.gerade, z.woanders,
               z.bits, bild.wort);
    }
    Lichtplan licht;
    licht.starte(20261112);
    unsigned wechsel = 0, hell = 0;
    bool vor = false;
    for (unsigned i = 0; i < 100000; ++i) {
        const bool h = licht.weiter();
        wechsel += h != vor; hell += h; vor = h;
    }
    printf("LICHT,%u,%u\n", wechsel, hell);
}
