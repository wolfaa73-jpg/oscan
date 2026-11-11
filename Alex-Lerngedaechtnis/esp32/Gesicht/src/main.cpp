#include <Arduino.h>
#define LGFX_USE_V1
#include <LovyanGFX.hpp>
#include <WiFi.h>
#include <esp_wifi.h>
#include <esp_now.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include "../../Gemeinsam/GesichtFormen.h"

class Anzeige : public lgfx::LGFX_Device {
    lgfx::Panel_GC9A01 panel;
    lgfx::Bus_SPI bus;
    lgfx::Light_PWM licht;
public:
    Anzeige() {
        auto b=bus.config();
        b.spi_host=SPI2_HOST;b.spi_mode=0;b.freq_write=40000000;b.freq_read=16000000;
        b.spi_3wire=true;b.use_lock=true;b.dma_channel=SPI_DMA_CH_AUTO;
        b.pin_sclk=6;b.pin_mosi=7;b.pin_miso=-1;b.pin_dc=2;bus.config(b);panel.setBus(&bus);
        auto p=panel.config();
        p.pin_cs=10;p.pin_rst=-1;p.pin_busy=-1;p.panel_width=240;p.panel_height=240;
        p.memory_width=240;p.memory_height=240;p.offset_x=0;p.offset_y=0;
        p.invert=true;p.rgb_order=false;p.readable=false;p.bus_shared=false;panel.config(p);
        auto l=licht.config();l.pin_bl=3;l.invert=false;l.freq=5000;l.pwm_channel=0;
        licht.config(l);panel.setLight(&licht);setPanel(&panel);
    }
} lcd;
struct Nachricht {EmpfindenPaket::Zustand z;uint32_t zeit;};
StaticQueue_t queueStand;
uint8_t queueBytes[sizeof(Nachricht)];
QueueHandle_t nachrichten=nullptr;
EmpfindenPaket::Empfang empfang;
bool zahlen=false, letzteTaste=true, stabileTaste=true, zuletztAlt=true;
uint32_t tasteSeit=0;

// WiFi-Task: nur prüfen und kopieren. Kein Displayzugriff, keine Serial-Ausgabe.
void erhalten(const uint8_t *,const uint8_t *daten,int n) {
    Nachricht m;
    if(n>=0 && EmpfindenPaket::entpacke(daten,static_cast<size_t>(n),m.z)) {
        m.zeit=millis();xQueueOverwrite(nachrichten,&m);
    }
}
void zeichne(bool alt) {
    const auto &z=empfang.zustand;
    const auto b=Gesicht::zeichne(z,alt);
    lcd.startWrite();lcd.fillScreen(b.hintergrund);
    lcd.setTextColor(0xdce5ec,b.hintergrund);lcd.setTextDatum(middle_center);lcd.setFont(&fonts::Font2);
    if(zahlen && !alt) {
        char t[48];
        if(z.temp==-32768)snprintf(t,sizeof(t),"Temperatur fehlt");
        else snprintf(t,sizeof(t),"Temperatur: %.1f C",z.temp/10.0);
        lcd.drawString(t,120,65);
        snprintf(t,sizeof(t),"Gerade: %+d",z.gerade);lcd.drawString(t,120,95);
        snprintf(t,sizeof(t),"Woanders: %+d",z.woanders);lcd.drawString(t,120,125);
        snprintf(t,sizeof(t),"Takt: %lu",static_cast<unsigned long>(z.takt));lcd.drawString(t,120,155);
        lcd.drawString(b.wort,120,185);
    } else {
        for(unsigned i=0;i<b.n;++i) {
            const auto &f=b.formen[i];
            switch(f.art) {
                case Gesicht::ELLIPSE:lcd.fillEllipse(f.x,f.y,f.a,f.b,f.farbe);break;
                case Gesicht::LINIE:lcd.drawLine(f.x,f.y,f.a,f.b,f.farbe);break;
                case Gesicht::RECHTECK:lcd.fillRect(f.x,f.y,f.a,f.b,f.farbe);break;
                case Gesicht::DREIECK:lcd.fillTriangle(f.x,f.y,f.a,f.b,f.c,f.d,f.farbe);break;
            }
        }
        lcd.drawString(b.wort,120,43);
        if(!alt) {char t[30];snprintf(t,sizeof(t),"woanders %+d",z.woanders);lcd.drawString(t,120,202);}
    }
    lcd.setTextColor(0xffa67a,b.hintergrund);lcd.drawString(b.hinweis,120,222);lcd.endWrite();
}
void setup() {
    Serial.begin(115200);pinMode(9,INPUT_PULLUP);
    lcd.init();lcd.setRotation(0);lcd.setBrightness(48);
    nachrichten=xQueueCreateStatic(1,sizeof(Nachricht),queueBytes,&queueStand);
    zeichne(true);
    WiFi.persistent(false);WiFi.mode(WIFI_STA);WiFi.disconnect(false,false);
    const bool ok=esp_wifi_set_channel(EmpfindenPaket::kanal,WIFI_SECOND_CHAN_NONE)==ESP_OK
        && esp_wifi_set_ps(WIFI_PS_NONE)==ESP_OK && esp_now_init()==ESP_OK
        && esp_now_register_recv_cb(erhalten)==ESP_OK;
    Serial.println(ok?"GESICHT,bereit":"GESICHT,funkfehler");
}
void loop() {
    bool neu=false;Nachricht m;
    if(xQueueReceive(nachrichten,&m,0)==pdTRUE)neu=empfang.uebernehme(m.z,m.zeit);
    const uint32_t jetzt=millis();  // erst nach Queue: Empfangszeit darf nicht in der Zukunft liegen
    const bool taste=digitalRead(9);
    if(taste!=letzteTaste){letzteTaste=taste;tasteSeit=jetzt;}
    if(uint32_t(jetzt-tasteSeit)>=40 && taste!=stabileTaste){stabileTaste=taste;if(!taste){zahlen=!zahlen;neu=true;}}
    const bool alt=empfang.alt(jetzt);
    if(neu || alt!=zuletztAlt){zeichne(alt);zuletztAlt=alt;}
    delay(5);
}
