from ...models import Bed, Patient, Task, Call
from ...choices import CallState
from ..beds.beds_serialized import serial_beds


def build_board_data() -> dict:
    """Arma el estado completo del board en Contract B. Fuente única de verdad."""
    beds = Bed.objects.filter(active=True).select_related("bed_patient").order_by("id").all()
    patients = Patient.objects.filter(inpatient=True).all()
    tasks = Task.objects.filter(active=True).order_by("programed_time").select_related("bed__bed_patient").all()
    calls = Call.objects.exclude(state=CallState.CLOSED).order_by("id").select_related("bed__bed_patient").all()
    return {
        "beds": serial_beds(beds),
        "patients": [p.serialize() for p in patients],
        "calls": [c.serialize() for c in calls],
        "tasks": [t.serialize() for t in tasks],
    }
