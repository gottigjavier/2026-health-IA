# import json
from datetime import datetime
from django.db import transaction
from ...models import Call, Bed
from ..data_analytics import save_event
from ..app.app_ws_update import ws_load, app_ws_update


def new_call(bed):
    with transaction.atomic():
        try:
            active_bed = Bed.objects.select_for_update().get(id_bed=bed, active=True)
        except Exception:
            active_bed = {}
            print(f"new_call: bed {bed} not found or not active")
            return ws_load()

        existing_call = Call.objects.filter(state="active", bed__id_bed=bed).first()
        if existing_call:
            print(f"new_call: active call already exists for bed {bed}")
            return ws_load()

        before = f"bed_id: {bed}; bed_state: {active_bed.bed_state}; call.active: False"

        if active_bed.bed_state == "task":
            active_bed.bed_state = "call-task"
        else:
            active_bed.bed_state = "call"
        active_bed.save()

        new_call = Call()
        new_call.bed = active_bed
        new_call.call_time = datetime.now()
        new_call.response_time = datetime.now()
        new_call.state = "active"
        new_call.save()

        after = (
            f"bed_id: {bed}; bed_state: {active_bed.bed_state}; "
            f"call.pk: {new_call.pk}; call.call_time: {new_call.call_time}; "
            f"call.state: {new_call.state}"
        )
        save_event("system", "new call", before, after)

        print(f"new_call: created call for bed {bed}")

        try:
            app_ws_update()
        except Exception:
            pass
        return ws_load()
