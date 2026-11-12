// Selbstgesicht: Das Display fühlt selbst. Rechenkern in ../Selbst.h, hier nur Fühler, Licht, Flash,
// Bildschirm und die Befehle am USB. Funk bleibt aus, WiFi wird gar nicht erst eingebunden.
//
// Befehle (115200 Baud, eine Zeile):
//   SELBST        Stand in einer Zeile
//   LICHT 0|1     eigene Last aus oder an (gemerkt). Aus: Das Licht bleibt gedimmt.
//   ZEILEN 0|1    je Takt die Zeilen VORHERSAGE und EMPFINDEN mitschreiben (nicht gemerkt)
//   FAHRTSTAND, FAHRTLOG, FAHRTLEER, STOP   wie am Lernknoten, damit fahrt.py das Protokoll holen kann.
//                 Anders als der Knoten hält das Display dabei nicht an: STOP antwortet nur, und das
//                 Protokoll geht stückweise zwischen den Takten hinaus.
#include <Arduino.h>
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <LittleFS.h>
#include <Preferences.h>
#include "../Selbst.h"
#include "../../Gemeinsam/GesichtFormen.h"

// Anschlüsse wie in ../../Gesicht/src/main.cpp.
class Anzeige : public lgfx::LGFX_Device {
    lgfx::Panel_GC9A01 panel;
    lgfx::Bus_SPI bus;
    lgfx::Light_PWM licht;
public:
    Anzeige() {
        auto b = bus.config();
        b.spi_host = SPI2_HOST; b.spi_mode = 0; b.freq_write = 40000000; b.freq_read = 16000000;
        b.spi_3wire = true; b.use_lock = true; b.dma_channel = SPI_DMA_CH_AUTO;
        b.pin_sclk = 6; b.pin_mosi = 7; b.pin_miso = -1; b.pin_dc = 2; bus.config(b); panel.setBus(&bus);
        auto p = panel.config();
        p.pin_cs = 10; p.pin_rst = -1; p.pin_busy = -1; p.panel_width = 240; p.panel_height = 240;
        p.memory_width = 240; p.memory_height = 240; p.offset_x = 0; p.offset_y = 0;
        p.invert = true; p.rgb_order = false; p.readable = false; p.bus_shared = false; panel.config(p);
        auto l = licht.config(); l.pin_bl = 3; l.invert = false; l.freq = 5000; l.pwm_channel = 0;
        licht.config(l); panel.setLight(&licht); setPanel(&panel);
    }
} lcd;

// Helligkeit von 255. Beide gesetzt: gedimmt wie im Funkgesicht, hell deutlich darüber.
const uint8_t lichtDunkel = 48, lichtHell = 200;
const char *const logPfad = "/selbst.log", *const standPfad = "/selbst.bin", *const standNeu = "/selbst.neu";
const uint32_t standMagie = 0x534c4553;  // "SELS"
const uint32_t reserve = 65536;          // so viel bleibt im Dateisystem frei, dann endet das Protokoll
struct StandKopf { uint32_t magie, version, groesse, takt, summe; };

Selbst selbst;
Lichtplan lichtplan;
EmpfindenPaket::Zustand zustand, gezeichnet;
uint8_t puffer[Fahrtsatz::block * FahrtV2::bytes], standPuffer[Selbst::standBytes];
unsigned gepuffert = 0, grund = 0;
bool dateisystem = false, voll = false, lichtAn = true, hell = false, zeilen = false;
bool zahlen = false, letzteTaste = true, stabileTaste = true, neuZeichnen = true;
uint32_t tasteSeit = 0, naechsterTakt = 0;
size_t sendeOrt = 0, sendeEnde = 0;
uint32_t sendeSumme = 0;
bool sendet = false;
char eingabe[32];
unsigned eingabeLaenge = 0;

uint32_t summe(const uint8_t *p, size_t n, uint32_t s = 0) {
    while (n--) s = s * 31u + *p++;
    return s;
}

size_t logBytes() {
    if (!dateisystem || !LittleFS.exists(logPfad)) return 0;
    File f = LittleFS.open(logPfad, FILE_READ);
    const size_t n = f ? f.size() : 0;
    f.close();
    return n;
}

bool einstellung(const char *name, bool vorgabe, bool setzen = false, bool wert = false) {
    Preferences nvs;
    if (!nvs.begin("selbstgesicht", false)) return vorgabe;
    bool an = nvs.isKey(name) ? nvs.getUChar(name, 0) == 1 : vorgabe;
    if (setzen) an = nvs.putUChar(name, wert ? 1 : 0) == 1 ? wert : an;
    nvs.end();
    return an;
}

// Erst die Sätze, dann der Stand über eine zweite Datei: Ein Stromausfall mittendrin lässt den alten Stand.
void sichere() {
    if (!dateisystem) { voll = true; return; }
    if (!voll) {
        bool ok = logBytes() % FahrtV2::bytes == 0 && LittleFS.totalBytes() - LittleFS.usedBytes() > reserve;
        if (ok) {
            File f = LittleFS.open(logPfad, FILE_APPEND);
            ok = f && f.write(puffer, sizeof(puffer)) == sizeof(puffer);
            f.close();
        }
        voll = !ok;
    }
    selbst.exportiere(standPuffer);
    const StandKopf kopf = {standMagie, 1, sizeof(standPuffer), selbst.takt, summe(standPuffer, sizeof(standPuffer))};
    File f = LittleFS.open(standNeu, FILE_WRITE);
    const bool ok = f && f.write(reinterpret_cast<const uint8_t *>(&kopf), sizeof(kopf)) == sizeof(kopf)
                    && f.write(standPuffer, sizeof(standPuffer)) == sizeof(standPuffer);
    f.close();
    if (ok) LittleFS.rename(standNeu, standPfad);
}

bool lade() {
    if (!dateisystem || !LittleFS.exists(standPfad)) return false;
    File f = LittleFS.open(standPfad, FILE_READ);
    StandKopf kopf = {};
    const bool gelesen = f && f.read(reinterpret_cast<uint8_t *>(&kopf), sizeof(kopf)) == sizeof(kopf)
                         && kopf.magie == standMagie && kopf.version == 1 && kopf.groesse == sizeof(standPuffer)
                         && f.size() == sizeof(kopf) + sizeof(standPuffer)
                         && f.read(standPuffer, sizeof(standPuffer)) == sizeof(standPuffer);
    f.close();
    return gelesen && kopf.summe == summe(standPuffer, sizeof(standPuffer)) && selbst.importiere(standPuffer, kopf.takt);
}

void beginne(unsigned neustartgrund) {
    grund = neustartgrund;
    gepuffert = 0;
    if (!lade()) selbst.beginne(static_cast<uint32_t>(logBytes() / FahrtV2::bytes));
    voll = !dateisystem || logBytes() % FahrtV2::bytes != 0;
    lichtplan.starte(20261112u ^ (selbst.takt * 2654435761u));
    hell = false;
    lcd.setBrightness(lichtDunkel);
    Serial.print("SELBST,laeuft,");
    Serial.print(selbst.takt);
    Serial.println(selbst.beiNull ? ",null" : ",geladen");
}

void zeichne() {
    const auto &z = zustand;
    const auto b = Gesicht::zeichne(z, false);
    lcd.startWrite(); lcd.fillScreen(b.hintergrund);
    lcd.setTextColor(0xdce5ec, b.hintergrund); lcd.setTextDatum(middle_center); lcd.setFont(&fonts::Font2);
    char t[48];
    if (zahlen) {
        if (z.temp == -32768) snprintf(t, sizeof(t), "Temperatur fehlt");
        else snprintf(t, sizeof(t), "Temperatur: %.1f C", z.temp / 10.0);
        lcd.drawString(t, 120, 60);
        snprintf(t, sizeof(t), "Gerade: %+d", z.gerade); lcd.drawString(t, 120, 85);
        snprintf(t, sizeof(t), "Woanders: %+d", z.woanders); lcd.drawString(t, 120, 110);
        snprintf(t, sizeof(t), "Takt: %lu", static_cast<unsigned long>(z.takt)); lcd.drawString(t, 120, 135);
        snprintf(t, sizeof(t), "Licht: %s", !lichtAn ? "fest" : hell ? "hell" : "dunkel"); lcd.drawString(t, 120, 160);
        lcd.drawString(b.wort, 120, 185);
    } else {
        for (unsigned i = 0; i < b.n; ++i) {
            const auto &f = b.formen[i];
            switch (f.art) {
                case Gesicht::ELLIPSE: lcd.fillEllipse(f.x, f.y, f.a, f.b, f.farbe); break;
                case Gesicht::LINIE: lcd.drawLine(f.x, f.y, f.a, f.b, f.farbe); break;
                case Gesicht::RECHTECK: lcd.fillRect(f.x, f.y, f.a, f.b, f.farbe); break;
                case Gesicht::DREIECK: lcd.fillTriangle(f.x, f.y, f.a, f.b, f.c, f.d, f.farbe); break;
            }
        }
        lcd.drawString(b.wort, 120, 43);
        if (z.bits & EmpfindenPaket::ANLAUF && z.temp != -32768 && selbst.beiNull && z.takt < 1800) {
            // Nur nach einem Beginn bei null stimmt die Rechnung aus dem Takt, und nur ungefähr.
            snprintf(t, sizeof(t), "noch etwa %lu min", static_cast<unsigned long>((1800 - z.takt) / 60 + 1));
            lcd.drawString(t, 120, 202);
        } else if (!(z.bits & EmpfindenPaket::ANLAUF)) {
            snprintf(t, sizeof(t), "woanders %+d", z.woanders); lcd.drawString(t, 120, 202);
        }
    }
    lcd.setTextColor(0xffa67a, b.hintergrund); lcd.drawString(b.hinweis, 120, 222); lcd.endWrite();
}

void takt() {
    const float grad = temperatureRead();
    const bool gueltig = !isnan(grad);
    const int32_t temp = gueltig ? static_cast<int32_t>(lroundf(grad * 10.0f)) : 0;
    zustand = selbst.schritt(gueltig, temp, hell, grund, voll, puffer + gepuffert * FahrtV2::bytes);
    if (zeilen) {
        if (*selbst.vorhersage.zeile()) Serial.println(selbst.vorhersage.zeile());
        Serial.println(selbst.empfinden.zeile());
    }
    if (++gepuffert == Fahrtsatz::block) { sichere(); gepuffert = 0; }
    const bool heller = lichtAn && lichtplan.weiter();
    if (heller != hell) { hell = heller; lcd.setBrightness(hell ? lichtHell : lichtDunkel); neuZeichnen = neuZeichnen || zahlen; }
    if (zahlen || zustand.gerade != gezeichnet.gerade || zustand.woanders != gezeichnet.woanders
        || zustand.bits != gezeichnet.bits || (zustand.temp == -32768) != (gezeichnet.temp == -32768)
        || ((zustand.bits & EmpfindenPaket::ANLAUF) && zustand.takt / 60 != gezeichnet.takt / 60)) neuZeichnen = true;
}

// Ein Stück Protokoll je Durchlauf, damit die Takte pünktlich bleiben. Die Datei wird jedes Mal neu
// geöffnet, weil zwischendurch neue Sätze ans Ende kommen können.
void sendeStueck() {
    uint8_t satz[FahrtV2::bytes];
    char text[2 * FahrtV2::bytes + 1];
    File f = LittleFS.open(logPfad, FILE_READ);
    bool ok = f && f.seek(sendeOrt);
    for (unsigned i = 0; ok && i < 60 && sendeOrt < sendeEnde; ++i) {
        ok = f.read(satz, sizeof(satz)) == sizeof(satz);
        if (!ok) break;
        for (unsigned k = 0; k < sizeof(satz); ++k) snprintf(text + 2 * k, 3, "%02x", satz[k]);
        Serial.println(text);
        sendeSumme = summe(satz, sizeof(satz), sendeSumme);
        sendeOrt += sizeof(satz);
    }
    f.close();
    if (!ok) { sendet = false; Serial.println("FEHLER"); return; }
    if (sendeOrt >= sendeEnde) {
        sendet = false;
        Serial.print("FAHRTLOG,ende,"); Serial.println(static_cast<unsigned long>(sendeSumme));
    }
}

bool schalter(const char *name, bool &ziel) {
    const size_t n = strlen(name);
    if (strncmp(eingabe, name, n) || eingabe[n] != ' ' || (eingabe[n + 1] != '0' && eingabe[n + 1] != '1') || eingabe[n + 2])
        return false;
    ziel = eingabe[n + 1] == '1';
    return true;
}

bool befehl() {
    char text[112];
    bool wert;
    if (!strcmp(eingabe, "STOP")) { Serial.println("KOERPER,aus"); return true; }
    if (!strcmp(eingabe, "SELBST")) {
        snprintf(text, sizeof(text), "SELBST,%lu,%d,%d,%d,%u,%d,%d,%d", static_cast<unsigned long>(selbst.takt),
                 zustand.temp, zustand.gerade, zustand.woanders, zustand.bits, lichtAn ? 1 : 0, hell ? 1 : 0, voll ? 1 : 0);
        Serial.println(text);
        return true;
    }
    if (schalter("LICHT", wert)) {
        lichtAn = einstellung("licht", true, true, wert);
        Serial.println(lichtAn ? "LICHT,1" : "LICHT,0");
        return lichtAn == wert;
    }
    if (schalter("ZEILEN", wert)) { zeilen = wert; Serial.println(wert ? "ZEILEN,1" : "ZEILEN,0"); return true; }
    if (!dateisystem) return false;
    if (!strcmp(eingabe, "FAHRTSTAND")) {
        // wie am Knoten: gewollt, Bytes im Export, frei, Takt, voll, Satzgröße, Kopfgröße; dazu 1 = läuft weiter
        const size_t n = logBytes();
        snprintf(text, sizeof(text), "FAHRT,1,%lu,%lu,%lu,%d,%u,%u,1",
                 static_cast<unsigned long>(n ? n + FahrtV2::kopfBytes : 0),
                 static_cast<unsigned long>(LittleFS.totalBytes() - LittleFS.usedBytes()),
                 static_cast<unsigned long>(selbst.takt), voll ? 1 : 0, FahrtV2::bytes, n ? FahrtV2::kopfBytes : 0);
        Serial.println(text);
        return true;
    }
    if (!strcmp(eingabe, "FAHRTLOG")) {
        const size_t n = logBytes();
        if (sendet || n % FahrtV2::bytes) return false;
        Serial.print("FAHRTLOG,"); Serial.println(static_cast<unsigned long>(n ? n + FahrtV2::kopfBytes : 0));
        sendeSumme = 0;
        if (!n) { Serial.println("FAHRTLOG,ende,0"); return true; }
        uint8_t kopf[FahrtV2::kopfBytes];
        FahrtV2::kopf(kopf);
        for (unsigned k = 0; k < sizeof(kopf); ++k) snprintf(text + 2 * k, 3, "%02x", kopf[k]);
        Serial.println(text);
        sendeSumme = summe(kopf, sizeof(kopf));
        sendeOrt = 0; sendeEnde = n; sendet = true;
        return true;
    }
    if (!strcmp(eingabe, "FAHRTLEER")) {
        // Protokoll und Gedächtnis löschen, danach beginnt das Display bei null.
        if (sendet) return false;
        for (const char *pfad : {logPfad, standPfad, standNeu})
            if (LittleFS.exists(pfad)) LittleFS.remove(pfad);
        Serial.println("FAHRT,leer");
        beginne(Selbst::pause);
        neuZeichnen = true;
        return true;
    }
    return false;
}

void setup() {
    Serial.begin(115200); pinMode(9, INPUT_PULLUP);
    lcd.init(); lcd.setRotation(0); lcd.setBrightness(lichtDunkel);
    dateisystem = LittleFS.begin(true);
    lichtAn = einstellung("licht", true);
    beginne(static_cast<unsigned>(esp_reset_reason()));
    zustand.bits = EmpfindenPaket::ANLAUF; zustand.temp = 0; zustand.takt = selbst.takt;
    gezeichnet = zustand;
    zeichne(); neuZeichnen = false;
    naechsterTakt = millis() + 1000;
}

void loop() {
    const uint32_t jetzt = millis();
    if (static_cast<int32_t>(jetzt - naechsterTakt) >= 0) {
        naechsterTakt += 1000;
        if (static_cast<int32_t>(jetzt - naechsterTakt) >= 0) naechsterTakt = jetzt + 1000;  // nach langem Hänger nicht aufholen
        takt();
    }
    const bool taste = digitalRead(9);
    if (taste != letzteTaste) { letzteTaste = taste; tasteSeit = jetzt; }
    if (uint32_t(jetzt - tasteSeit) >= 40 && taste != stabileTaste) {
        stabileTaste = taste;
        if (!taste) { zahlen = !zahlen; neuZeichnen = true; }
    }
    if (neuZeichnen) { zeichne(); gezeichnet = zustand; neuZeichnen = false; }
    while (Serial.available()) {
        const int c = Serial.read();
        if (c == '\r') continue;
        if (c != '\n') {
            if (eingabeLaenge < sizeof(eingabe) - 1) eingabe[eingabeLaenge++] = static_cast<char>(c);
            else eingabeLaenge = sizeof(eingabe);  // zu lang: bis zum Zeilenende verwerfen
            continue;
        }
        const bool zuLang = eingabeLaenge >= sizeof(eingabe);
        eingabe[zuLang ? 0 : eingabeLaenge] = 0;
        eingabeLaenge = 0;
        if (zuLang || !*eingabe || !befehl()) Serial.println("FEHLER");
    }
    if (sendet) sendeStueck();
    delay(5);
}
