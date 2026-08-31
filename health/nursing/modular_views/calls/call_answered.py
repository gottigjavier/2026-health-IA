import logging
from django.http import JsonResponse
from ...models import Call, Bed
from ...choices import BedState, CallState
from ..data_analytics import save_event
from ..app.app_load import load
from ..app.app_ws_update import ws_load
import json

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------------------
# for dev test usin rooms.js need recive parameter (bed) from consumer.py
# --> ans_call = await sync_to_async(answ_call)(bed)

# for prod using only mosquitto just use "ws_load" in consumer.py
# --> from .modular_views.app.app_ws_update import ws_load
# --> ans_call = await sync_to_async(ws_load)
# Managed by try and except in consumer.py


def answ_call(bed):
    return ws_load()


# -----------------------------------------------------------------------------------------


def call_answered(request):
    data = json.loads(request.body)
    calls_list = data["saveCallsList"]
    for answ_call in calls_list:
        call = Call.objects.get(bed__id_bed=answ_call["bed"], state=CallState.ACTIVE)
        if call:
            try:
                bed = Bed.objects.get(id_bed=answ_call["bed"], active=True)
                prev_bed_state = bed.bed_state
                before = (
                    f"call.pk: {call.pk}; bed_id: {bed.id_bed}; "
                    f"call.call_time: {call.call_time}; call.state: {call.state}; "
                    f"bed.bed_state: {prev_bed_state}"
                )
                call.response_time = answ_call["response_time"].replace("T", " ")
                call.state = CallState.ANSWERED
                if bed.bed_state == BedState.CALL_TASK:
                    bed.bed_state = BedState.TASK
                else:
                    bed.bed_state = BedState.OCCUPIED
                bed.save()
                call.save()
                after = (
                    f"call.pk: {call.pk}; bed_id: {bed.id_bed}; "
                    f"call.call_time: {call.call_time}; call.response_time: {call.response_time}; "
                    f"call.state: {call.state}; bed.bed_state: {bed.bed_state}"
                )
                save_event(request.user.username, "answer call", before, after)
                logger.info(
                    "call_answered: bed=%s prev_state=%s new_state=%s call_id=%s",
                    bed.id_bed,
                    prev_bed_state,
                    bed.bed_state,
                    call.id,
                )
                # broadcast app state after answering
                try:
                    from ..app.app_ws_update import app_ws_update

                    app_ws_update()
                    logger.info(
                        "call_answered: broadcasted app_ws_update after answer of call %s",
                        call.id,
                    )
                except Exception:
                    pass
            except Exception:
                return JsonResponse({"message": "Bed answered Error."}, status=400)
        else:
            return JsonResponse({"message": "Call does not exist."}, status=400)
    return load()
