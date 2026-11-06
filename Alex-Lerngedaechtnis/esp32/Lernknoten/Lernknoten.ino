// Serieller Replay-Prüfstand. Eine vollständige Zeile löst genau eine Beobachtung aus.
// Im Körpermodus misst sich der Knoten in eigenem Takt selbst.
#include "Knoten.h"
#include "Koerper.h"
#include "Reize.h"
#include <string.h>
#ifdef ARDUINO_ARCH_ESP32
#include <Preferences.h>
#include <esp_heap_caps.h>
#include <esp_system.h>
#endif

#if defined(ALEX_KONTEXT) && defined(ALEX_ERBE)
#error "Pro Firmware nur eine Lernregel: ALEX_KONTEXT oder ALEX_ERBE"
#elif defined(ALEX_ERBE)
Knoten knoten(Regel::ERBE);
const char *const bereit = "BEREIT,ERBE";
const char *const standKey = "erbe";
#elif defined(ALEX_KONTEXT)
Knoten knoten(Regel::KONTEXT);
const char *const bereit = "BEREIT,KONTEXT";
const char *const standKey = "kontext";
#else
Knoten knoten;
const char *const bereit = "BEREIT,ZEIT";
const char *const standKey = "zeit";
#endif
char zeile[64];
size_t laenge = 0;
bool verwerfen = false;
const char *const namen[] = {"OK", "SCHWACH", "AUSFALL"};
const uint32_t maxTemp = 100000;  // Zehntelgrad, nur Plausibilitätsgrenze der Eingabe
Grenzen grenzen = {};
bool grenzenGesetzt = false;
bool koerperAn = false;

// Liest eine Dezimalzahl ohne Vorzeichen und rückt den Zeiger vor.
bool zahl(const char *&text, uint32_t &wert) {
    if (*text < '0' || *text > '9') return false;
    wert = 0;
    while (*text >= '0' && *text <= '9') {
        const unsigned ziffer = *text++ - '0';
        if (wert > (UINT32_MAX - ziffer) / 10) return false;
        wert = wert * 10 + ziffer;
    }
    return true;
}

// Genau anzahl Zahlen, durch je ein Leerzeichen getrennt, bis zum Zeilenende.
bool felder(const char *text, uint32_t *werte, unsigned anzahl) {
    for (unsigned i = 0; i < anzahl; ++i) {
        if (i && *text++ != ' ') return false;
        if (!zahl(text, werte[i])) return false;
    }
    return *text == '\0';
}

bool befehl(const char *name, const char *&rest) {
    const size_t n = strlen(name);
    if (strncmp(zeile, name, n) != 0 || zeile[n] != ' ') return false;
    rest = zeile + n + 1;
    return true;
}

#ifdef ARDUINO_ARCH_ESP32
// Durchläufe mit eigener Arbeit (Messung, Ausgabe, LED) zählen nicht zur Lücke.
bool eigeneArbeit = false;

// Last auf Kern 0 im Rhythmus des Rechners. Der Knoten erfährt davon nur über
// seine Messwerte, die Ausgabe vermerkt die Phase nur für die Auswertung.
volatile bool lastAktiv = false;
volatile uint32_t lastAnMs = 0;
volatile uint32_t lastAusMs = 0;
TaskHandle_t lastTask = nullptr;
volatile uint32_t lastSenke = 0;

void lastSchleife(void *) {
    uint32_t x = 1;
    for (;;) {
        if (!lastAnMs) {
            lastAktiv = false;
            vTaskDelay(pdMS_TO_TICKS(100));
            continue;
        }
        lastAktiv = true;
        const uint32_t ende = millis() + lastAnMs;
        while (lastAnMs && static_cast<int32_t>(millis() - ende) < 0) {
            const uint32_t stueck = millis() + 10;
            while (static_cast<int32_t>(millis() - stueck) < 0) x = x * 1664525u + 1013904223u;
            lastSenke = x;
            vTaskDelay(1);  // Leerlauf von Kern 0 hält den Task-Wachhund ruhig
        }
        lastAktiv = false;
        const uint32_t pause = millis() + lastAusMs;
        while (lastAnMs && static_cast<int32_t>(millis() - pause) < 0) vTaskDelay(pdMS_TO_TICKS(100));
    }
}

// Speicherleck und Bremse der Hauptschleife, beide im Takt des Körpers. Auch davon
// erfährt der Knoten nur über seine Messwerte.
Leck leck;
Bremse bremse;
void *bloecke[512];
unsigned belegt = 0;
uint32_t stauMs = 0;    // Stillstand, der im nächsten Durchlauf von loop() ansteht
bool gebremst = false;  // seit dem letzten Takt stand die Schleife einmal still

void leckFrei() {
    while (belegt) heap_caps_free(bloecke[--belegt]);
}

// Vor der Messung: einen Block belegen oder alles freigeben, wie es der Ablauf will.
void leckTakt() {
    switch (leck.takt()) {
    case Leck::BELEGEN: {
        const uint32_t frei = ESP.getFreeHeap();
        void *block = belegt < sizeof(bloecke) / sizeof(bloecke[0]) && frei > leck.boden
                      && frei - leck.boden >= leck.block
                    ? heap_caps_malloc(leck.block, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT) : nullptr;
        if (block) bloecke[belegt++] = block;
        else leck.voll();
        break;
    }
    case Leck::FREIGEBEN:
        leckFrei();
        break;
    default:
        break;
    }
}

#ifdef ALEX_RGB_PIN
bool blitzAn = false;
uint32_t blitzEnde = 0;
Zustand ledZustand = UNBEKANNT;

// Grün OK, Gelb SCHWACH, Rot AUSFALL, schwaches Weiß bereit. Gedämpft, fürs Auge reicht das.
void zeigeZustand(Zustand z) {
    static const uint8_t farbe[4][3] = {{0, 6, 0}, {10, 5, 0}, {12, 0, 0}, {3, 3, 3}};
    neopixelWrite(ALEX_RGB_PIN, farbe[z][0], farbe[z][1], farbe[z][2]);
    ledZustand = z;
    eigeneArbeit = true;
}

// Vorwarnung: kurz blau, danach wieder die Farbe des Zustands.
void blitze(Zustand z) {
    neopixelWrite(ALEX_RGB_PIN, 0, 0, 16);
    ledZustand = z;
    blitzAn = true;
    blitzEnde = millis() + 150;
    eigeneArbeit = true;
}
#endif
#endif

// Welche Reize gerade wirken, als Bits für die Auswertung: 1 Last, 2 Leck, 4 Bremse.
unsigned reize() {
#ifdef ARDUINO_ARCH_ESP32
    return (lastAktiv ? 1u : 0u) | (belegt ? 2u : 0u) | (gebremst ? 4u : 0u);
#else
    return 0;
#endif
}

// Körpermodus und alle Reize aus, die LED zurück auf bereit.
void ruhe() {
    koerperAn = false;
#ifdef ARDUINO_ARCH_ESP32
    lastAnMs = 0;
    leck = Leck();
    leckFrei();
    bremse = Bremse();
    stauMs = 0;
    gebremst = false;
#ifdef ALEX_RGB_PIN
    blitzAn = false;
    zeigeZustand(UNBEKANNT);
#endif
#endif
}

// Ein Körpertakt: einstufen, lernen, Rohwerte und Entscheidung ausgeben.
bool koerperTakt(bool tempGueltig, int32_t temp, uint32_t heap, uint32_t luecke) {
    const Zustand zustand = einstufen(tempGueltig, temp, heap, luecke, grenzen);
    const uint32_t takt = knoten.takt() + 1;
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    Serial.print("K,");
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.print(entscheidung.warnung ? ",1," : ",0,");
    if (tempGueltig) Serial.print(temp); else Serial.print('-');
    Serial.print(',');
    Serial.print(heap);
    Serial.print(',');
    Serial.print(luecke);
    Serial.print(',');
    Serial.print(reize());
    Serial.println("");
#if defined(ARDUINO_ARCH_ESP32) && defined(ALEX_RGB_PIN)
    if (entscheidung.warnung) blitze(zustand); else zeigeZustand(zustand);
#endif
    return true;
}

#ifdef ARDUINO_ARCH_ESP32
uint32_t intervallMs = 0;
uint32_t naechsterTick = 0;
uint32_t letzteRunde = 0;
uint32_t luecke = 0;

// Die Lücke ist der größte Abstand zwischen zwei Durchläufen von loop() seit dem
// letzten Takt. Durchläufe mit eigener Arbeit zählen nicht mit, gemessen wird
// also nur fremde Wartezeit.
void koerperSchleife() {
    const uint32_t jetzt = micros();
    if (!eigeneArbeit && jetzt - letzteRunde > luecke) luecke = jetzt - letzteRunde;
    eigeneArbeit = false;
    letzteRunde = jetzt;
    if (stauMs) {
        // Die Bremse: Dieser Durchlauf steht still, die Lücke misst das als fremde Wartezeit.
        const uint32_t ms = stauMs;
        stauMs = 0;
        gebremst = true;
        delay(ms);
        return;
    }
#ifdef ALEX_RGB_PIN
    if (blitzAn && static_cast<int32_t>(millis() - blitzEnde) >= 0) {
        blitzAn = false;
        zeigeZustand(ledZustand);
    }
#endif
    if (!koerperAn || static_cast<int32_t>(millis() - naechsterTick) < 0) return;
    leckTakt();
    const float grad = temperatureRead();
    const bool gueltig = !isnan(grad);
    const int32_t temp = gueltig ? static_cast<int32_t>(lroundf(grad * 10.0f)) : 0;
    if (!koerperTakt(gueltig, temp, ESP.getFreeHeap(), luecke)) {
        ruhe();
        Serial.println("FEHLER");
    }
    gebremst = false;
    stauMs = bremse.takt();
    eigeneArbeit = true;
    luecke = 0;
    naechsterTick += intervallMs;
    // Nach einem Stillstand nicht nachholen, sondern ab jetzt neu takten.
    if (static_cast<int32_t>(millis() - naechsterTick) >= 0) naechsterTick = millis() + intervallMs;
}
#endif

#ifdef ARDUINO_ARCH_ESP32
// Warum das Gerät zuletzt neu gestartet ist, als Zahl und Name. Die Nummern sind die von
// esp_reset_reason_t in ESP-IDF 4.4. Ein Neustart mitten in einer Aufnahme ist sonst nicht zu klären.
void meldeNeustart() {
    static const char *const gruende[] = {"UNBEKANNT", "EINSCHALTEN", "EXTERN", "SOFTWARE", "PANIK",
                                          "INT_WACHHUND", "TASK_WACHHUND", "WACHHUND", "TIEFSCHLAF",
                                          "UNTERSPANNUNG", "SDIO"};
    const int grund = esp_reset_reason();
    Serial.print("NEUSTART,");
    Serial.print(grund);
    Serial.print(',');
    Serial.println(grund >= 0 && grund < static_cast<int>(sizeof(gruende) / sizeof(gruende[0])) ? gruende[grund] : "?");
}
#endif

bool lernstand(bool speichern) {
    uint8_t daten[Knoten::standBytes];
    uint8_t alt[Knoten::standBytes];
    if (speichern && !knoten.exportiere(daten)) return false;
    Preferences nvs;
    if (!nvs.begin("alex-lernlabor", !speichern)) return false;
    const char *key = standKey;
    const bool lesbar = nvs.getBytesLength(key) == sizeof(alt)
                     && nvs.getBytes(key, alt, sizeof(alt)) == sizeof(alt);
    bool ok;
    if (speichern) {
        ok = (lesbar && memcmp(daten, alt, sizeof(alt)) == 0)
          || nvs.putBytes(key, daten, sizeof(daten)) == sizeof(daten);
    } else {
        ok = lesbar && knoten.importiere(alt);
    }
    nvs.end();
    if (ok) Serial.println(speichern ? "GESICHERT" : "GELADEN");
    return ok;
}

bool verarbeiteZeile() {
    const char *rest = nullptr;
    if (strcmp(zeile, "SICHERN") == 0) return lernstand(true);
    if (strcmp(zeile, "LADEN") == 0) return lernstand(false);
    if (strcmp(zeile, "NEUER_LAUF") == 0) {
        knoten.neuerLauf();
        ruhe();
        Serial.println(bereit);
        return true;
    }
    if (strcmp(zeile, "STOP") == 0) {
        ruhe();
        Serial.println("KOERPER,aus");
        return true;
    }
    if (befehl("GRENZEN", rest)) {
        uint32_t w[6];
        if (!felder(rest, w, 6) || w[0] > maxTemp || w[1] > maxTemp) return false;
        const Grenzen neu = {static_cast<int32_t>(w[0]), static_cast<int32_t>(w[1]), w[2], w[3], w[4], w[5]};
        if (!neu.gueltig()) return false;
        grenzen = neu;
        grenzenGesetzt = true;
        Serial.println("GRENZEN,ok");
        return true;
    }
    if (befehl("BLICK", rest)) {
        // Takte, die die Vorwarnung vorausdenkt. Nicht während des Körpermodus, sonst passt
        // die Aufnahme nicht mehr zu ihrer Nachrechnung.
        uint32_t takte;
        if (koerperAn || !felder(rest, &takte, 1) || !knoten.setzeBlick(takte)) return false;
        Serial.println("BLICK,ok");
        return true;
    }
    if (befehl("MESSWERT", rest)) {
        // Rohwerte von außen, etwa eine aufgezeichnete Spur. "-" steht für eine nicht lesbare Temperatur.
        const bool gueltig = *rest != '-';
        uint32_t temp = 0, w[2];
        if (gueltig) {
            if (!zahl(rest, temp) || temp > maxTemp) return false;
        } else {
            ++rest;
        }
        if (*rest++ != ' ' || !felder(rest, w, 2)) return false;
        return grenzenGesetzt && !koerperAn && koerperTakt(gueltig, static_cast<int32_t>(temp), w[0], w[1]);
    }
#ifdef ARDUINO_ARCH_ESP32
    if (befehl("KOERPER", rest)) {
        uint32_t ms;
        if (!felder(rest, &ms, 1) || ms < 100 || !grenzenGesetzt) return false;
        intervallMs = ms;
        naechsterTick = millis() + ms;
        luecke = 0;
        koerperAn = true;
        Serial.println("KOERPER,an");
        return true;
    }
    if (befehl("LAST", rest)) {
        // Arbeitsphase und Pause in Sekunden, LAST 0 0 beendet die Last.
        uint32_t w[2];
        if (!felder(rest, w, 2) || w[0] > 3600 || w[1] > 3600) return false;
        lastAusMs = w[1] * 1000;
        lastAnMs = w[0] * 1000;
        if (w[0] && !lastTask
            && xTaskCreatePinnedToCore(lastSchleife, "last", 3072, nullptr, 1, &lastTask, 0) != pdPASS) return false;
        Serial.println("LAST,ok");
        return true;
    }
    if (befehl("LECK", rest)) {
        // Byte je Takt, Boden in Byte, Takte am Boden, Takte Pause, wahlweise ein flacher Boden und das
        // Muster der Durchgänge, die schon an ihm anhalten. LECK 0 0 0 0 beendet und gibt frei.
        uint32_t w[6] = {};
        if (!felder(rest, w, 6)) {
            w[4] = w[5] = 0;
            if (!felder(rest, w, 4)) return false;
        }
        Leck neu;
        if ((w[0] | w[1] | w[2] | w[3] | w[4] | w[5]) && !neu.starte(w[0], w[1], w[2], w[3], w[4], w[5])) return false;
        leckFrei();
        leck = neu;
        Serial.println("LECK,ok");
        return true;
    }
    if (befehl("BREMSE", rest)) {
        // Start, Schritt und Ende des Stillstands in ms, Takte am Ende, Takte Pause. BREMSE 0 0 0 0 0 beendet.
        uint32_t w[5];
        if (!felder(rest, w, 5)) return false;
        Bremse neu;
        if ((w[0] | w[1] | w[2] | w[3] | w[4]) && !neu.starte(w[0], w[1], w[2], w[3], w[4])) return false;
        bremse = neu;
        stauMs = 0;
        Serial.println("BREMSE,ok");
        return true;
    }
#endif
    if (koerperAn) return false;
    const char *text = zeile;
    uint32_t takt;
    if (!zahl(text, takt) || *text++ != ',') return false;
    Zustand zustand = UNBEKANNT;
    for (unsigned i = 0; i < 3; ++i) {
        if (strcmp(text, namen[i]) == 0) zustand = static_cast<Zustand>(i);
    }
    Entscheidung entscheidung;
    if (!knoten.schritt(takt, zustand, entscheidung)) return false;
    Serial.print(takt);
    Serial.print(',');
    Serial.print(namen[zustand]);
    Serial.print(entscheidung.sofort ? ",1" : ",0");
    Serial.println(entscheidung.warnung ? ",1" : ",0");
    return true;
}

void setup() {
    Serial.begin(115200);
#if defined(ARDUINO_ARCH_ESP32) && defined(ALEX_RGB_PIN)
    zeigeZustand(UNBEKANNT);
#endif
    Serial.println("takt,zustand,sofort,vorwarnung");
#ifdef ARDUINO_ARCH_ESP32
    meldeNeustart();
#endif
}

void loop() {
#ifdef ARDUINO_ARCH_ESP32
    koerperSchleife();
#endif
    while (Serial.available() > 0) {
        const int c = Serial.read();
        if (c == '\n') {
            if (laenge && zeile[laenge - 1] == '\r') --laenge;
            zeile[laenge] = '\0';
            if (verwerfen || !verarbeiteZeile()) Serial.println("FEHLER");
            laenge = 0;
            verwerfen = false;
        } else if (c <= 0 || c > 127 || laenge >= sizeof(zeile) - 1) {
            verwerfen = true;
        } else {
            zeile[laenge++] = static_cast<char>(c);
        }
    }
}
