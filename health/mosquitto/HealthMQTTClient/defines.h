/****************************************************************************************************************************
  defines.h for ESP8266 HealthMQTTClient

  Based on and modified for Javier Gottig
  Licensed under MIT license
 *****************************************************************************************************************************/

// Wi-Fi and MQTT conection

const char* ssid = "SSID";
const char* wifipass = "Wifi Password";
const char* broker = "192.168.0.36";
const char* device = "Board of Room: 1"; // Put the room number to identify the device.
const int port = 1883;
const int securePort = 8883;

// NTP Configuration
const char* ntpServer = "pool.ntp.org";
const long gmtOffset_sec = -10800;  // GMT-3 for Argentina (adjust as needed)
const int daylightOffset_sec = 0;

// TLS Configuration
// CA certificate to validate the Mosquitto broker.
// -----------------------------------------------------------------------------
// LOS VALORES REALES NO SE COMMITEAN AL REPO (secretos PKI).
//
// DÓNDE BUSCARLO: health/mosquitto/certs/ca.crt  (generado por certs/generate.sh)
// CÓMO COPIARLO: abrí certs/ca.crt, copiá el contenido ENTRE (y sin incluir) las
// líneas "-----BEGIN CERTIFICATE-----" y "-----END CERTIFICATE-----" y pegalo
// dentro de R"EOF( ... )EOF", reemplazando el texto de abajo.
// -----------------------------------------------------------------------------
const char caCert[] PROGMEM = R"EOF(
REEMPLAZAR con el contenido de health/mosquitto/certs/ca.crt
(desde "-----BEGIN CERTIFICATE-----" hasta "-----END CERTIFICATE-----", inclusive)
)EOF";

// Client certificate (mTLS) — presented to the broker so it can authenticate this device
// From: certs/client-esp-room1.crt
// -----------------------------------------------------------------------------
// LOS VALORES REALES NO SE COMMITEAN AL REPO (secretos PKI).
//
// DÓNDE BUSCARLO: health/mosquitto/certs/client-esp-room1.crt
// CÓMO COPIARLO: pegá el contenido entre "-----BEGIN CERTIFICATE-----" y
// "-----END CERTIFICATE-----" dentro de R"EOF( ... )EOF".
// -----------------------------------------------------------------------------
const char clientCert[] PROGMEM = R"EOF(
REEMPLAZAR con el contenido de health/mosquitto/certs/client-esp-room1.crt
(desde "-----BEGIN CERTIFICATE-----" hasta "-----END CERTIFICATE-----", inclusive)
)EOF";

// Client private key (mTLS) — pairs with clientCert to prove device identity.
// From: certs/client-esp-room1.key (EC P-256 / prime256v1)
// -----------------------------------------------------------------------------
// SECRETO — ¡NUNCA se commitea! Si se filtra, cualquiera puede hacerse pasar por
// este dispositivo. Está también ignoreado en .gitignore.
//
// DÓNDE BUSCARLO: health/mosquitto/certs/client-esp-room1.key
// CÓMO COPIARLO: pegá el contenido entre "-----BEGIN EC PRIVATE KEY-----" y
// "-----END EC PRIVATE KEY-----" dentro de R"EOF( ... )EOF".
//
// IMPORTANTE (no borrar): el ESP8266 BearSSL lee la key EC como SEC1
// "BEGIN EC PRIVATE KEY". Se usa EC P-256 en vez de RSA porque el client-cert
// RSA-2048 (br_rsa_i15_private) desborda el stack BearSSL (~6KB) durante el
// handshake mTLS. ECDSA P-256 usa mucho menos stack y entra. El cert está
// firmado por la CA (RSA).
// -----------------------------------------------------------------------------
const char clientKey[] PROGMEM = R"EOF(
REEMPLAZAR con el contenido de health/mosquitto/certs/client-esp-room1.key
(desde "-----BEGIN EC PRIVATE KEY-----" hasta "-----END EC PRIVATE KEY-----", inclusive)
)EOF";


// Source of the active signal. To configure the Json
const String bed1 = "1";
const String bed2 = "2";
const String bed3 = "3";
const String bed4 = "4";
const String bed5 = "5";
const String bed6 = "6";
const String room = "1";
const String key = "this&is$a$key&to?prevent?hacking";


// Push Buttons connection
//const int pinBed1 = 5; // GPIO5 - D1
//const int pinBed2 = 4; // GPIO4 - D2
const int bit1 = 14; // GPIO14 - D5
const int bit2 = 12; // GPIO12 - D6
const int bit3 = 13; // GPIO13 - D7

// beds
const int callBed1 = 1;
const int callBed2 = 2;
const int callBed3 = 3;
const int callBed4 = 4;
const int callBed5 = 5;
const int callBed6 = 6;
const int roomReset = 0;


// Debounce delay
const int debDelay = 1000;
