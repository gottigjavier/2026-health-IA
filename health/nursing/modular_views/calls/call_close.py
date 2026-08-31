from django.http import JsonResponse
from ..data_analytics import save_event
from ...models import Call
from ...choices import CallState
from ..app.app_load import load
import json


def call_close(request):
    data = json.loads(request.body)
    call_id = data["callId"]
    call_time = data["callTime"].replace("T", " ")
    call_response = data["text"]
    call_answered_by = data["answeredBy"]
    call = Call.objects.get(id=call_id)
    if call:
        call.state = CallState.CLOSED
        call.response = (
            call_response
            if call_response != ""
            else "Respuesta Sin Novedad (por defecto)"
        )
        call.response_time = call_time
        call.action_done_by = call_answered_by if call_answered_by != "" else "Anónimo"
        call.save()
        before = (
            "call.pk: "
            + str(call.pk)
            + "; call.bed_id: "
            + str(call.bed.id_bed)
            + "; call.patient_name: "
            + call.bed.bed_patient.name
            + "; call.call_time: "
            + str(call.call_time)
            + "; call.response_time: "
            + str(call_time)
            + "; call.response: "
            + str(call_response)
            + "; call.state: answered; call.answered_by: "
            + call_answered_by
            + "; call.action_done_by: "
            + call.action_done_by
        )
        after = (
            "call.pk: "
            + str(call.pk)
            + "; call.bed_id: "
            + str(call.bed.id_bed)
            + "; call.patient_name: "
            + call.bed.bed_patient.name
            + "; call.call_time: "
            + str(call.call_time)
            + "; call.response_time: "
            + str(call_time)
            + "; call.response: "
            + str(call_response)
            + "; call.state: closed; call.answered_by: "
            + call_answered_by
            + "; call.action_done_by: "
            + call.action_done_by
        )
        save_event(request.user.username, "close call", before, after)
        return load()
    else:
        return JsonResponse({"message": "Call does not exist."}, status=400)
