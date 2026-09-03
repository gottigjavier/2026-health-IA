/*
  MQTTClient -- Wi-Fi.
  Board : NodeMCU 1.0 - ESP8266.
  The board monitors the bed call buttons and the call cancel button.
  Before an active signal, it sends a Json data with the origin of the signal through Wi-Fi using the MQTT protocol.
  Author: gottigjavier@gmail.com
*/

// Utilizando cada pin como bit de un sistema binario se puede utilizar 000 como estado de reposo, 111 como cancelación de llamada y las otras 6 combinaciones como identificadores de cama.
// Entonces, cada cable de señal que proviene del botón puede disgregarse en bits = 1 y según la combinación enviar el json.

#include "defines.h"

#include "EspMQTTClient.h"
#include <ArduinoJson.h>


EspMQTTClient client(
  ssid,
  wifipass,
  broker,  // MQTT Broker server ip
  //"MQTTUsername",   // Can be omitted if not needed
  //"MQTTPassword",   // Can be omitted if not needed
  device,  // Client name that uniquely identify your device
  port     // The MQTT port, default to 1883. this line can be omitted
);


void setup() {
  //  pinMode(pinBed1, INPUT);
  //  pinMode(pinBed2, INPUT);
  pinMode(bit1, INPUT);  // Initialize pins as an input buttons
  pinMode(bit2, INPUT);
  pinMode(bit3, INPUT);
  Serial.begin(9600);

  // Optionnal functionnalities of EspMQTTClient :
  client.enableDebuggingMessages();  // Enable debugging messages sent to serial output
}

// This function is called once everything is connected (Wifi and MQTT)
// WARNING : YOU MUST IMPLEMENT IT IF YOU USE EspMQTTClient
void onConnectionEstablished() {

  // Subscribe to "mqtt/call/" and display received message to Serial
  client.subscribe("mqtt/call/", [](const String& topic, const String& payload) {
    Serial.println("From system:  topic " + topic + " - -  payload " + payload);
  });
}


// The app discards repeated button strokes as long as they are not high-frequency.
void readButtons() {
  //  if ( digitalRead(pinBed1) == HIGH ){
  //    call(pinBed1);
  //    delay(debDelay);
  //  }
  //  if ( digitalRead(pinBed2) == HIGH ){
  //    call(pinBed2);
  //    delay(debDelay);
  //  }
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
    //case pinBed1: bed = room + "," + bed1; state = true; break;
    //case pinBed2: bed = room + "," + bed2; state = true; break;
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
  // Add values in the document
  doc["key"] = key;
  doc["bed"] = bed;
  doc["state"] = state;

  // JSON to String (serializion)
  String output;
  serializeJson(doc, output);

  // Print JSON for debugging
  //Serial.println(output);

  // Publish a message to "mytopic/test"
  client.publish("mqtt/call/", output);  // You can activate the retain flag by setting the third parameter to true
}

void loop() {
  client.loop();
  readButtons();
}
