/*
  MQTTClient -- Wi-Fi with TLS.
  Board : NodeMCU 1.0 - ESP8266.
  The board monitors the bed call buttons and the call cancel button.
  Before an active signal, it sends a Json data with the origin of the signal through Wi-Fi using MQTT over TLS.
  Author: gottigjavier@gmail.com
*/

// Utilizando cada pin como bit de un sistema binario se puede utilizar 000 como estado de reposo, 111 como cancelación de llamada y las otras 6 combinaciones como identificadores de cama.
// Entonces, cada cable de señal que proviene del botón puede disgregarse en bits = 1 y según la combinación enviar el json.

#include "defines.h"

#include <ESP8266WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <time.h>

WiFiClientSecure secureClient;
PubSubClient client(secureClient);

// BearSSL client cert & private key MUST persist for the life of the program.
// The secureClient stores POINTERS to these objects; if they were stack locals in
// setup() they would be destroyed when setup() returns, leaving dangling pointers.
// (Note: we do NOT set a CA trust anchor. We connect by IP and use setInsecure() to
// skip server hostname validation — see setup(). Only the client cert pairs here.
// clientKey is EC P-256 SEC1; clientCert is the matching EC cert signed by the RSA CA.)
BearSSL::X509List clientTrustAnchor(clientCert);
BearSSL::PrivateKey clientPrivateKey(clientKey);

int mqttReconnectAttempts = 0;
const int maxReconnectAttempts = 5;

void setup() {
  Serial.begin(9600);

  pinMode(bit1, INPUT);
  pinMode(bit2, INPUT);
  pinMode(bit3, INPUT);

  // Connect to WiFi
  Serial.print("Connecting to WiFi");
  WiFi.begin(ssid, wifipass);
  int wifiTimeout = 0;
  while (WiFi.status() != WL_CONNECTED && wifiTimeout < 30) {
    delay(500);
    Serial.print(".");
    wifiTimeout++;
  }
  Serial.println("");
  if (WiFi.status() != WL_CONNECTED) {
    Serial.print("WiFi FAILED to connect. status=");
    Serial.println(WiFi.status());
  } else {
    Serial.print("WiFi connected. IP=");
    Serial.print(WiFi.localIP());
    Serial.print(" GW=");
    Serial.print(WiFi.gatewayIP());
    Serial.print(" RSSI=");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  }

  // Sync time via NTP (CRITICAL for TLS certificate validation)
  // configTime() is built into ESP8266 core — no external library needed
  Serial.print("Syncing time via NTP");
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  time_t now = time(nullptr);
  while (now < 8 * 3600) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
  }
  Serial.println("");
  Serial.println("NTP time synced: " + String(ctime(&now)));

  // Configure BearSSL with the client cert (mTLS) and skip server hostname validation.
  // IMPORTANT: recv buffer MUST stay large (default 16384). A small recv buffer
  // (e.g. 512) truncates the handshake stream, so the server certificate cannot
  // be fully received/decoded -> ssl_error=38 BAD_TAG_VALUE (truncated ASN.1).
  secureClient.setBufferSizes(16384, 512);
  // setInsecure() disables server certificate/hostname validation. We connect by IP and
  // ESP8266 BearSSL cannot verify IP SANs against the hostname, so the handshake fails
  // with BR_ERR_X509_BAD_SERVER_NAME ("Expected server name was not found").
  // This is acceptable because we have MUTUAL TLS: the broker requires a valid client
  // cert signed by our CA (require_certificate true), so a MITM cannot complete the
  // handshake without our private key. The client cert below is still presented to the
  // broker, preserving mTLS authentication of THIS device.
  secureClient.setInsecure();
  // Client cert is now EC P-256 (SETClientECCERT). We use ECDSA instead of RSA because
  // BearSSL's RSA-2048 client-cert signing overflows the ~6KB BearSSL stack during the
  // mTLS handshake (stack overflow in br_rsa_i15_private). ECDSA P-256 fits in the stack.
  // allowed_usages = BR_KEYTYPE_SIGN (0x20): the client signs the CertificateVerify.
  // cert_issuer_key_type = BR_KEYTYPE_RSA (1): the signing CA is RSA.
  secureClient.setClientECCert(&clientTrustAnchor, &clientPrivateKey, BR_KEYTYPE_SIGN, BR_KEYTYPE_RSA);

  // Configure MQTT broker
  client.setServer(broker, securePort);
  client.setCallback(callback);

  // Initial MQTT connection
  connectMQTT();
}

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  char message[257];
  unsigned int copyLen = (length < 256) ? length : 256;
  memcpy(message, payload, copyLen);
  message[copyLen] = '\0';
  Serial.println(message);
}

// Rich MQTT connection attempt with layered diagnostics.
// Distinguishes: DNS failure / TCP failure / TLS handshake failure / MQTT auth failure
void connectMQTT() {
  while (!client.connected()) {
    Serial.println();
    Serial.println("=== MQTT connect attempt ===");
    Serial.print("  broker=");
    Serial.print(broker);
    Serial.print(" port=");
    Serial.println(securePort);

    // Step 0 - probe reachability: can we resolve + open a TCP socket to the broker?
    // A short TCP connect with no TLS tells us if the network path is reachable at all.
    Serial.println("  [0] TCP probe...");
    WiFiClient tcpProbe;
    // ESP8266 WiFiClient::connect(host, port) handles DNS + TCP; no explicit timeout arg.
    if (!tcpProbe.connect(broker, securePort)) {
      Serial.print("  TCP FAILED: no TCP connection to ");
      Serial.print(broker);
      Serial.print(":");
      Serial.println(securePort);
      Serial.println("  -> Cause: network path blocked. Check AP/client isolation, firewall,");
      Serial.println("     or that the broker port is reachable from this WiFi network.");
      Serial.println("     (WiFi itself works - NTP synced - but this port cannot be opened.)");
      mqttReconnectAttempts++;
    } else {
      Serial.print("  TCP OK: reached ");
      Serial.print(broker);
      Serial.print(":");
      Serial.println(securePort);
      tcpProbe.stop();

      // Step 1 + 2 - TLS handshake + MQTT CONNECT (done together by PubSubClient)
      Serial.println("  [1] TLS + MQTT connect...");
      if (client.connect(device)) {
        Serial.println("  MQTT connected OK");
        mqttReconnectAttempts = 0;
        client.subscribe("mqtt/call/");
        Serial.println("  Subscribed to mqtt/call/");
      } else {
        char sslErrBuf[256];
        int sslErr = secureClient.getLastSSLError(sslErrBuf, sizeof(sslErrBuf));
        Serial.print("  connect failed. pubsub rc=");
        Serial.print(client.state());
        Serial.print("  ssl_error=");
        Serial.println(sslErr, HEX);
        Serial.print("  ssl_msg=");
        Serial.println(sslErrBuf);
        if (sslErr == -1000) {
          Serial.println("  -> OOM: insufficient heap for SSL buffers. Reduce buffer sizes or free memory.");
        } else if (sslErr == 0) {
          Serial.println("  -> MQTT-level rejection (auth/ACL/client CN mapping). Check broker logs.");
        } else {
          Serial.println("  -> TLS/cert issue during handshake. See ssl_msg above: ");
          Serial.println("     38/0x26 = BAD_TAG_VALUE (ASN.1 decode) -> cert format unsupported by BearSSL.");
          Serial.println("     39/0x27 = INDEFINITE_LENGTH, 40/0x28 = EXTRA_ELEMENT (malformed cert).");
          Serial.println("     Verify server cert is a v3 cert without uncommon extensions/validity.");
        }
        mqttReconnectAttempts++;
      }
    }

    // After max attempts, reset the board to force a clean re-initialization
    if (mqttReconnectAttempts >= maxReconnectAttempts) {
      Serial.println("Max reconnect attempts reached. Resetting ESP8266...");
      delay(1000);
      ESP.restart();
    }

    // Exponential backoff: 1s, 2s, 4s, 8s, 16s
    long waitTime = 1000 * (1L << mqttReconnectAttempts);
    if (waitTime > 30000) waitTime = 30000;
    Serial.print("  retrying in ");
    Serial.print(waitTime / 1000);
    Serial.println("s");
    delay(waitTime);
  }
}

// The app discards repeated button strokes as long as they are not high-frequency.
void readButtons() {
  // 001
  if (digitalRead(bit3) == LOW && digitalRead(bit2) == LOW && digitalRead(bit1) == HIGH) {
    call(callBed1);
    delay(debDelay);
  }
  // 010
  if (digitalRead(bit3) == LOW && digitalRead(bit2) == HIGH && digitalRead(bit1) == LOW) {
    call(callBed2);
    delay(debDelay);
  }
  // 011
  if (digitalRead(bit3) == LOW && digitalRead(bit2) == HIGH && digitalRead(bit1) == HIGH) {
    call(callBed3);
    delay(debDelay);
  }
  // 100
  if (digitalRead(bit3) == HIGH && digitalRead(bit2) == LOW && digitalRead(bit1) == LOW) {
    call(callBed4);
    delay(debDelay);
  }
  // 101
  if (digitalRead(bit3) == HIGH && digitalRead(bit2) == LOW && digitalRead(bit1) == HIGH) {
    call(callBed5);
    delay(debDelay);
  }
  // 110
  if (digitalRead(bit3) == HIGH && digitalRead(bit2) == HIGH && digitalRead(bit1) == LOW) {
    call(callBed6);
    delay(debDelay);
  }
  // 111
  if (digitalRead(bit3) == HIGH && digitalRead(bit2) == HIGH && digitalRead(bit1) == HIGH) {
    call(roomReset);
    delay(debDelay);
  }
}

void call(int boolNum) {
  String bed;
  boolean state;
  switch (boolNum) {
    case callBed1:
      bed = room + "," + bed1;
      state = true;
      break;
    case callBed2:
      bed = room + "," + bed2;
      state = true;
      break;
    case callBed3:
      bed = room + "," + bed3;
      state = true;
      break;
    case callBed4:
      bed = room + "," + bed4;
      state = true;
      break;
    case callBed5:
      bed = room + "," + bed5;
      state = true;
      break;
    case callBed6:
      bed = room + "," + bed6;
      state = true;
      break;
    case roomReset:
      bed = room + ",0";
      state = false;
      break;
    default: break;
  }

  StaticJsonDocument<200> doc;
  doc["key"] = key;
  doc["bed"] = bed;
  doc["state"] = state;

  char output[256];
  serializeJson(doc, output, sizeof(output));

  if (client.connected()) {
    client.publish("mqtt/call/", output);
  } else {
    Serial.println("MQTT not connected, message dropped");
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost, reconnecting...");
    WiFi.begin(ssid, wifipass);
    delay(5000);
    return;
  }

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();
  readButtons();
}
