# Mosquitto + firmware NodeMCU (ESP8266)

Documentación y recordatorios de la parte hardware/broker del sistema de llamadas.

## Recordatorios frecuentes

> Estos pasos se olvidan habitualmente. El control de la conexión USB es **manual e intencional**:
> cada conexión nueva del NodeMCU requiere darle permisos a mano. No se automatiza.

### 1. Verificar que el NodeMCU está detectado

Al conectar el ESP por USB, comprobar que aparece el puerto y cuáles son sus permisos:

```bash
ll /dev/ttyUSB0
```

Si no aparece, revisar con `lsusb` que el adaptador USB-serial esté presente y el cable/índice de dispositivo correcto.

### 2. Dar permisos de lectura/escritura (cada conexión nueva)

El puerto se resetea al desconectar/reconectar el cable, así que el permiso se pierde y hay que volver a darlo:

```bash
sudo chmod uo+rw /dev/ttyUSB0
```

### 3. Flashear desde Arduino IDE

1. Abrir `HealthMQTTClient/HealthMQTTClient.ino` en Arduino IDE.
2. Verificar configuración en **Tools**:
   - **Board**: NodeMCU 1.0 (ESP-12E Module)
   - **Port**: `/dev/ttyUSB0`
3. Presionar **Upload** (el botón de flasheo).

> Nota: durante el flasheo, ver el **Serial Monitor en 9600 baud** para confirmar la conexión MQTT.

---

## Contenido de la carpeta

| Ruta | Qué es |
|------|--------|
| `mosquitto.conf` | Config del broker Mosquitto (mTLS, solo puerto 8883). |
| `config/` | Configuración del broker usada por el contenedor. |
| `certs/` | Certificados: CA, y certificados de cliente (`esp-room1`, `django`). Regenerarlos con `certs/generate.sh`. |
| `HealthMQTTClient/` | Firmware del NodeMCU (`.ino`) y `defines.h` (certificado de cliente, pinout, mapeo de botones). |

## Mapeo de botones (firmware, 3 pines = bits)

Cada botón del ESP es un pin (bit). Las 8 combinaciones binarias:

| Combinación | Acción |
|-------------|--------|
| `000` | Reposo (ningún botón) |
| `001` | Cama 1 |
| `010` | Cama 2 |
| `011` | Cama 3 |
| `100` | Cama 4 |
| `101` | Cama 5 |
| `110` | Cama 6 |
| `111` | Reset / contestar llamada de la habitación |

El firmware soporta hasta **6 camas por habitación**; la config de la aplicación define cuántas son camas reales (por defecto 4).
