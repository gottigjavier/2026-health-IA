import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.serializers.json import DjangoJSONEncoder
from ...models import Bed, Patient, Task, Call
from ...choices import CallState
import json
from ..beds.beds_serialized import serial_beds

logger = logging.getLogger(__name__)


def ws_load():
    beds = Bed.objects.filter(active=True).all()
    patients = Patient.objects.filter(inpatient=True).all()
    tasks = Task.objects.filter(active=True).order_by("programed_time").all()
    calls = Call.objects.exclude(state=CallState.CLOSED).order_by("id").all()
    beds_list = serial_beds(beds)
    if patients:
        serialized_patients = [patient.serialize() for patient in patients]
    else:
        serialized_patients = []
    if tasks:
        serialized_tasks = [task.serialize() for task in tasks]
    else:
        serialized_tasks = []
    if calls:
        serialized_calls = [call.serialize() for call in calls]
    else:
        serialized_calls = []
    rooms_state = {
        "beds": beds_list,
        "patients": serialized_patients,
        "calls": serialized_calls,
        "tasks": serialized_tasks,
    }
    return rooms_state


def ws_load_encoded():
    data = ws_load()
    return json.dumps(data, sort_keys=True, indent=1, cls=DjangoJSONEncoder)


def app_ws_update():
    all_data = json.loads(ws_load_encoded())
    layer = get_channel_layer()
    # Log payload summary for debugging
    try:
        logger.info(
            "app_ws_update payload: beds=%d calls=%d tasks=%d",
            len(all_data.get("beds", [])),
            len(all_data.get("calls", [])),
            len(all_data.get("tasks", [])),
        )
    except Exception:
        pass

    async_to_sync(layer.group_send)(
        "appboard",
        {
            "type": "deprocessing",
            "all_data": all_data,
        },
    )
