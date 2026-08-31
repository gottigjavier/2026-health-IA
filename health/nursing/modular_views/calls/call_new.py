# import json
from django.db import transaction
from ...models import Call, Bed
from ...choices import BedState, CallState
from ...utils.dates import dt_now
from ..data_analytics import save_event
from ..app.app_ws_update import ws_load, app_ws_update
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
