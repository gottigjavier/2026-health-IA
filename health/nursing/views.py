from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Bed, Patient, Call, Task
from .choices import BedState, CallState
from .modular_views.data_analytics import save_event

import json
from .modular_views.calls.call_mqtt import mqtt_service

from .modular_views.tasks.task_ws import tasks_ws_update
from .modular_views.app.app_load import load
from .modular_views.app.app_ws_update import app_ws_update

from .modular_views.calls.call_answered import call_answered

from .modular_views.calls.call_close import call_close

from .modular_views.tasks.task_new import modular_new_task

from .modular_views.tasks.task_edit import modular_edit_task

from .modular_views.tasks.task_delete import modular_delete_task


@login_required
def home(request):
    return render(request, "home.html")


# Update context as http json response ------------------------------


# Start. Initial app state.
@login_required
def initial_load(request):
    if request.method == "GET":
        mqtt_service()
        tasks_ws_update()
        app_ws_update()
        return JsonResponse({"message": "Initial Load OK."}, status=200)
    else:
        return JsonResponse({"error": "Bad request."}, status=400)


# --------------------------------------------------------------------


# ------- Beds Section ----------------------
@csrf_exempt
@login_required
def edit_bed(request):
    if request.method == "PUT":
        data = json.loads(request.body)
        bed_pk = data["bedId"]
        patient_name = data["patientName"]
        patient_social = data["patientSocial"]
        diagnosis = data["diagnosis"]
        occupied_time = data["occupiedDateTime"].replace("T", " ")
        planed_vacate = data["planedVacate"].replace("T", " ")
        done_by = data["doneBy"]
        try:
            bed = Bed.objects.get(id=bed_pk)
            current_patient = Patient.objects.get(id=bed.bed_patient.id)
        except Exception:
            return JsonResponse({"error": "Bed or patient not found."}, status=400)
        if bed and bed.active:
            before = (
                "bed.pk: "
                + str(bed.pk)
                + "; bed: "
                + str(bed.id_bed)
                + "; patient.pk: "
                + str(bed.bed_patient.pk)
                + "; patient.name: "
                + bed.bed_patient.name
                + "; patient.social_security_number: "
                + bed.bed_patient.social_security_number
                + "; patient.short_diagnosis: "
                + bed.bed_patient.short_diagnosis
                + "; bed.active: "
                + str(bed.active)
                + "; bed.state: "
                + bed.bed_state
                + "; bed.occupied_time: "
                + str(bed.occupied_time)
                + "; bed.planed_vacate: "
                + str(bed.planed_vacate)
                + "; bed.vacate_time: "
                + str(bed.vacate_time)
                + "; bed.action_done_by: "
                + bed.action_done_by
            )
            bed.occupied_time = occupied_time
            bed.planed_vacate = planed_vacate
            bed.action_done_by = done_by
            current_patient.name = patient_name
            current_patient.social_security_number = patient_social
            current_patient.short_diagnosis = diagnosis
            current_patient.save()
            bed.save()
            after = (
                "bed.pk: "
                + str(bed.pk)
                + "; bed: "
                + str(bed.id_bed)
                + "; patient.pk: "
                + str(current_patient.pk)
                + "; patient.name: "
                + patient_name
                + "; patient.social_security_number: "
                + patient_social
                + "; patient.short_diagnosis: "
                + diagnosis
                + "; bed.active: "
                + str(bed.active)
                + "; bed.state: "
                + bed.bed_state
                + "; bed.occupied_time: "
                + str(occupied_time)
                + "; bed.planed_vacate: "
                + str(planed_vacate)
                + "; bed.vacate_time: "
                + str(bed.vacate_time)
                + "; bed.action_done_by: "
                + done_by
            )
            save_event(request.user.username, "edit bed", before, after)
            return load()
        else:
            return JsonResponse({"error": "Bed not found or Bed Inactive."}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@login_required
def occupy_bed(request):
    if request.method == "POST":
        data = json.loads(request.body)
        bed_id = data["roomBedId"]
        patient_name = data["patientName"]
        patient_social = data["patientSocial"]
        diagnosis = data["diagnosis"]
        occupied_time = data["occupiedDateTime"].replace("T", " ")
        planed_vacate = data["planedVacate"].replace("T", " ")
        done_by = data["doneBy"]
        patient = Patient()
        patient.name = patient_name if patient_name != "" else "No Name"
        patient.social_security_number = (
            patient_social if patient_social != "" else "0000"
        )
        patient.short_diagnosis = diagnosis if diagnosis != "" else "No Diagnosis"
        patient.action_done_by = done_by if done_by != "" else "Anónimo"
        patient.save()
        bed = Bed()
        bed.bed_patient = patient
        bed.id_bed = bed_id
        bed.active = True
        bed.bed_state = BedState.OCCUPIED
        bed.occupied_time = occupied_time
        bed.planed_vacate = planed_vacate
        bed.action_done_by = done_by if done_by != "" else "Anónimo"
        bed.save()
        before = (
            "bed.pk: "
            + str(bed.pk)
            + "; bed.id_bed: "
            + bed_id
            + "; patient.pk: No Patient; patient.name: No Name; patient.social_security_number: No SSN; patient.short_diagnosis: No Diagnosis; bed.active: False; bed.state: free; bed.occupied_time: No Ocupied Time; bed.planed_vacate: No Planed Vacate; bed.vacate_time: No Vacate Time; bed.action_done_by: No Done By"
        )
        after = (
            "bed.pk: "
            + str(bed.pk)
            + "; bed.id_bed: "
            + bed_id
            + "; patient.pk: "
            + str(patient.pk)
            + "; patient.name: "
            + bed.bed_patient.name
            + "; patient.social_security_number: "
            + str(bed.bed_patient.social_security_number)
            + "; patient.short_diagnosis: "
            + bed.bed_patient.short_diagnosis
            + "; bed.active: True; bed.state: occupied; bed.occupied_time: "
            + str(bed.occupied_time)
            + "; bed.planed_vacate: "
            + str(bed.planed_vacate)
            + "; bed.vacate_time: No Vacate Time; bed.action_done_by: "
            + bed.action_done_by
        )
        save_event(request.user.username, "occupy bed", before, after)
        return load()
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@login_required
def vacate_bed(request):
    if request.method == "POST":
        data = json.loads(request.body)
        bed_pk = data["bedId"]
        patient_pk = data["patientId"]
        vacate_time = data["vacateDT"].replace("T", " ")
        done_by = data["doneBy"]
        patient = Patient.objects.get(pk=patient_pk)
        bed = Bed.objects.get(pk=bed_pk)
        tasks = Task.objects.filter(bed__pk=bed_pk, active=True)
        if tasks:
            for task in tasks:
                task.delete()
        calls = Call.objects.filter(bed__pk=bed_pk).exclude(state=CallState.CLOSED)
        if calls:
            for call in calls:
                call.state = CallState.CLOSED
                call.save()
        patient.inpatient = False
        patient.action_done_by = done_by if done_by != "" else "Anónimo"
        bed.active = False
        bed.bed_state = BedState.FREE
        bed.vacate_time = vacate_time
        bed.action_done_by = done_by if done_by != "" else "Anónimo"
        patient.save()
        bed.save()
        app_ws_update()
        before = (
            "bed.pk: "
            + str(bed.pk)
            + "; bed: "
            + str(bed.id_bed)
            + "; patient.pk: "
            + str(patient.pk)
            + "; patient.name: "
            + str(bed.bed_patient.name)
            + "; patient.social_security_number: "
            + str(bed.bed_patient.social_security_number)
            + "; patient.short_diagnosis: "
            + bed.bed_patient.short_diagnosis
            + "; bed.active: True; bed.state: occupied; bed.occupied_time: "
            + str(bed.occupied_time)
            + "; bed.planed_vacate: "
            + str(bed.planed_vacate)
            + "; bed.vacate_time: "
            + str(bed.vacate_time)
            + "; bed.action_done_by: "
            + done_by
        )
        after = (
            "bed.pk: "
            + str(bed.pk)
            + "; bed: "
            + str(bed.id_bed)
            + "; patient.pk: No Patient; patient.name: No Name; patient.social_security_number: No SSN; patient.short_diagnosis: No Diagnosis; bed.active: False; bed.state: free; bed.occupied_time: No Ocupied Time; bed.planed_vacate: No Planed Vacate; bed.vacate_time: "
            + str(bed.vacate_time)
            + "; bed.action_done_by: No Done By"
        )
        save_event(request.user.username, "vacate bed", before, after)
        return load()
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


# ------- End Beds Section ------------------

# -------- Calls section ----------------

# new_call()


@csrf_exempt
@login_required
def answered_call(request):
    if request.method == "POST":
        return call_answered(request)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@login_required
def close_call(request):
    if request.method == "POST":
        return call_close(request)
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


# ----------- End Calls section --------------------------------


# -----------Tasks section -------------------------------------


@csrf_exempt
@login_required
def new_task(request):
    if request.method == "POST":
        modular_new_task(request)
        return load()
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@login_required
def edit_task(request):
    if request.method == "PUT":
        modular_edit_task(request)
        return load()
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


@csrf_exempt
@login_required
def delete_task(request):
    if request.method == "POST":
        modular_delete_task(request)
        return load()
    else:
        return JsonResponse({"error": "Invalid request method."}, status=400)


# --------------- End Tasks section --------------------------------
