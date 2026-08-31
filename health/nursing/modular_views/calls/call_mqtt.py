import paho.mqtt.client as mqtt
import json
import logging
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .call_new import new_call
from ..app.app_ws_update import ws_load

logger = logging.getLogger(__name__)


def mqtt_service():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            logger.info("mqtt_service --> connected to MQTT Broker!")
            client.subscribe("mqtt/call/")
            logger.info("mqtt_service --> subscribed to mqtt/call/")
        else:
            logger.error("mqtt_service --> bad connection. Code: %s", rc)

    def on_message(client, userdata, message):
        msg = message.payload
        try:
            data = json.loads(msg)

            if data.get("key") != settings.CALL_SECRET_KEY:
                logger.warning(
                    "call_mqtt: rejected MQTT message with invalid key from bed=%s",
                    data.get("bed", "<missing>"),
                )
                return

            # no need to send status // without "," -> answer call
            if ",0" not in data["bed"]:
                data["state"] = True
            else:
                data["state"] = False
            if data["state"]:
                key = data["key"]
                state = data["state"]
                bed = data["bed"]
                n_call = new_call(bed)
                call = {"key": key, "state": state, "bed": bed, "call": n_call}
            else:
                key = data["key"]
                state = data["state"]
                bed = data["bed"]
                ans_call = ws_load()
                call = {"key": key, "state": state, "bed": bed, "call": ans_call}
            layer = get_channel_layer()
            async_to_sync(layer.group_send)(
                "callsboard",
                {
                    "type": "deprocessing",
                    "call": call,
                },
            )
        except Exception:
            logger.exception("call_mqtt: error processing MQTT message")

    try:
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
        # Corriendo la app en 'localhost' o '0.0.0.0' la IP debe ser una de estas dos.

        # Corriendo la app en Docker, colocar una IP como 192.168.0.xx y
        # observar en el mensaje de error en qué puerto está escuchando mosquitto.
        # En este caso es 10.10.8.1 (voilà). Entonces:

        # Para localhost
        # client.connect("0.0.0.0", 1883)

        # Para Docker - usar el hostname del contenedor
        client.connect("mosquitto", 1883)

        client.loop_start()
        # client.loop_forever()
    except Exception:
        logger.error("no mqtt broker found")
