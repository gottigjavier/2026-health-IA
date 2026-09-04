from django.core.management.base import BaseCommand
from nursing.modular_views.calls.call_mqtt import run_mqtt_forever


class Command(BaseCommand):
    """Django command that runs the dedicated MQTT subscriber worker.

    Subscribes to the call topic and processes bed-call messages from the ESP
    devices. Runs a blocking loop_forever() so there is exactly ONE subscriber,
    instead of the previous on-demand client created per /app/load request
    (which accumulated duplicate subscribers that processed messages repeatedly).
    """

    help = "Run the MQTT subscriber worker (processes bed-call messages)."

    def handle(self, *args, **options):
        self.stdout.write("Starting mqtt_worker...")
        run_mqtt_forever()
