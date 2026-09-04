# import json
from django.db import transaction
from ...models import Call, Bed
from ...choices import BedState, CallState
from ...utils.dates import dt_now
from ..data_analytics import save_event
from ..app.app_ws_update import ws_load, app_ws_update
from ..beds.bed_state import refresh_bed_state
import logging

logger = logging.getLogger(__name__)


def new_call(bed):
    with transaction.atomic():
        try:
            active_bed = Bed.objects.select_for_update().get(id_bed=bed, active=True)
        except Exception:
            active_bed = {}
            logger.warning("new_call: bed %s not found or not active", bed)
            return ws_load()

        existing_call = Call.objects.filter(
            state=CallState.ACTIVE, bed__id_bed=bed
        ).first()
        if existing_call:
            logger.info("new_call: active call already exists for bed %s", bed)
            return ws_load()

        before = f"bed_id: {bed}; bed_state: {active_bed.bed_state}; call.active: False"

        if active_bed.bed_state == BedState.TASK:
            active_bed.bed_state = BedState.CALL_TASK
        else:
            active_bed.bed_state = BedState.CALL
        active_bed.save()

        new_call = Call()
        new_call.bed = active_bed
        new_call.call_time = dt_now()
        new_call.response_time = dt_now()
        new_call.state = CallState.ACTIVE
        new_call.save()

        after = (
            f"bed_id: {bed}; bed_state: {active_bed.bed_state}; "
            f"call.pk: {new_call.pk}; call.call_time: {new_call.call_time}; "
            f"call.state: {new_call.state}"
        )
        save_event("system", "new call", before, after)

        logger.info("new_call: created call for bed %s", bed)

        try:
            app_ws_update()
        except Exception:
            pass
        return ws_load()


def answer_room_calls(room):
    """Answer ALL active calls in a room from the single per-room answer button.

    The ESP has ONE answer/cancel button per room, published as bed="<room>,0"
    (e.g. "1,0"). When staff presses it they are physically in the room facing
    every patient who called, so it must mark every ACTIVE call of that room as
    ANSWERED (grey + silent). It does NOT close them -- closing happens later
    from the web UI, saving the textual response.
    """
    prefix = f"{room},"
    touched_bed_ids = []
    with transaction.atomic():
        active_calls = Call.objects.select_for_update().filter(
            bed__id_bed__startswith=prefix, state=CallState.ACTIVE
        )
        for c in active_calls:
            c.state = CallState.ANSWERED
            c.response_time = dt_now()
            c.save()
            if c.bed_id not in touched_bed_ids:
                touched_bed_ids.append(c.bed_id)

    # Recompute bed state + refresh the app board outside the row lock.
    for bed_id in touched_bed_ids:
        try:
            bed = Bed.objects.get(id=bed_id)
            refresh_bed_state(bed, consider_later=False, has_active_call=False)
        except Exception:
            logger.warning("answer_room_calls: could not refresh bed %s", bed_id)

    try:
        app_ws_update()
    except Exception:
        pass
    return ws_load()
