import paho.mqtt.client as mqtt
import json
import logging
import ssl
import time
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .call_new import new_call, answer_room_calls

logger = logging.getLogger(__name__)

MQTT_TOPIC = "mqtt/call/"


def _on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("mqtt_service --> connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
        logger.info("mqtt_service --> subscribed to %s", MQTT_TOPIC)
    else:
        logger.error("mqtt_service --> bad connection. Code: %s", rc)


def _on_message(client, userdata, message):
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
            # The ESP has a single answer/cancel button per room (bed="<room>,0").
            # Answer ALL active calls of that room server-side (grey + silence),
            # so it no longer depends on the web panel being open/connected.
            room = bed.split(",")[0]
            ans_call = answer_room_calls(room)
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


def build_mqtt_client():
    """Build a TLS-configured paho client wired to the call_topic handlers.

    Caller is responsible for connect() and starting the network loop.
    """
    client = mqtt.Client()
    client.on_connect = _on_connect
    client.on_message = _on_message

    # For Docker the broker is reachable via the 'mosquitto' pod hostname.
    client.tls_set(
        ca_certs=settings.MQTT_TLS_CA_CERT,
        certfile=settings.MQTT_TLS_CLIENT_CERT,
        keyfile=settings.MQTT_TLS_CLIENT_KEY,
        tls_version=ssl.PROTOCOL_TLS,
    )
    # NOTE: the method is tls_insecure_set(), NOT tls_insecure().
    # paho-mqtt has no tls_insecure() method -- using it raised AttributeError
    # that was swallowed by the outer except, so mqtt_service() silently never
    # subscribed and the broker dropped every ESP message ("no mqtt broker found").
    client.tls_insecure_set(False)
    return client


def build_and_connect():
    client = build_mqtt_client()
    client.connect("mosquitto", settings.MQTT_PORT)
    return client


def run_mqtt_forever():
    """Blocking MQTT subscriber loop. Run as a dedicated management command.

    Used by ``python manage.py mqtt_worker`` so the broker subscription lives in
    its own process, decoupled from the HTTP/daphne server. This guarantees a
    SINGLE subscriber -- the on-demand creation inside /app/load was creating a
    new paho client + thread on every panel reload, accumulating duplicate
    subscribers that processed the same message multiple times.
    """
    logger.info("starting mqtt_worker (blocking loop_forever)")
    while True:
        client = build_and_connect()
        client.loop_forever(retry_first_connection=False)
        # loop_forever returns if the connection drops; log and reconnect.
        logger.warning("MQTT connection lost; reconnecting in 5s")
        time.sleep(5)


# Backward-compatible wrapper kept for callers that used mqtt_service().
# Prefer run_mqtt_forever() for standalone workers, or build_mqtt_client() +
# loop_start() when an embedded non-blocking subscriber is needed.
def mqtt_service():
    client = build_and_connect()
    client.loop_start()
    return client
