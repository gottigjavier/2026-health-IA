from ..tasks.task_ws import tasks_scheduler
from .app_ws_update import app_ws_update
from django.http import JsonResponse
from ...models import Bed, Patient, Task, Call
from ...choices import CallState
from ..beds.beds_serialized import serial_beds


def load():    
    beds = Bed.objects.filter(active=True).all()
    patients = Patient.objects.filter(inpatient=True).all()
    tasks = Task.objects.filter(active=True).order_by('programed_time').all()
    calls = Call.objects.exclude(state=CallState.CLOSED).order_by('id').all()
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
    rooms_state ={
        'beds': beds_list,
        'patients': serialized_patients,
        'calls': serialized_calls,
        'tasks': serialized_tasks
        }
    tasks_scheduler()
    app_ws_update()
    return JsonResponse(rooms_state, safe=False)
