from django.contrib.auth.models import AbstractUser
from django.db import models

# from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from .utils.dates import dt_serialize
from .choices import BedState, CallState, TaskState

mr_fs = FileSystemStorage(location="nursing/medicalrecords")
user_fs = FileSystemStorage(location="nursing/media")


class User(AbstractUser):
    image = models.ImageField(
        storage=user_fs, default="useravatar.png", null=True, blank=True
    )
    is_leader = models.BooleanField(default=False, null=True, blank=True)
    role = models.CharField(default="nurse", max_length=50)  # office, doctor, nurse

    def __str__(self):
        return self.username

    def serialize(self):
        if self.image:
            return {
                "id": self.id,
                "username": self.username,
                "leader": self.is_leader,
                "image": self.image.url,
                "date_joined": dt_serialize(self.date_joined),
                "role": self.role,
            }
        else:
            return {
                "id": self.id,
                "username": self.username,
                "date_joined": dt_serialize(self.date_joined),
            }


class Patient(models.Model):
    name = models.CharField(default="Sin Nombre", max_length=50)
    id_card_number = models.CharField(
        default="00000", null=True, max_length=50
    )  # only in some countries
    social_security_number = models.CharField(default="0000", null=True, max_length=50)
    image = models.ImageField(default="useravatar.png", null=True, blank=True)
    inpatient = models.BooleanField(default=True)
    admission = models.DateTimeField(auto_now_add=True)
    diagnosis = models.TextField(default="Sin Diagnóstico")
    short_diagnosis = models.TextField(default="Sin Diagnóstico")
    treatment_roadmap = models.TextField(default="Sin Tratamiento")
    action_done_by = models.CharField(default="Anónimo", max_length=50)

    # def __str__(self):
    #    return self.name

    def serialize(self):
        if self.image:
            return {
                "id": self.id,
                "name": self.name,
                "image": self.image.url,
                "social_number": self.social_security_number,
                "id_card": self.id_card_number,
                "inpatient": self.inpatient,
                "admission": dt_serialize(self.admission),
                "diagnosis": self.diagnosis,
                "short_diagnosis": self.short_diagnosis,
                "treatment_roadmap": self.treatment_roadmap,
                "action_done_by": self.action_done_by,
            }
        else:
            return {
                "id": self.id,
                "name": self.name,
                "social_number": self.social_security_number,
                "inpatient": self.inpatient,
                "admission": dt_serialize(self.admission),
                "diagnosis": self.diagnosis,
                "short_diagnosis": self.short_diagnosis,
                "treatment_roadmap": self.treatment_roadmap,
                "action_done_by": self.action_done_by,
            }


class Bed(models.Model):
    id_bed = models.CharField(max_length=10)
    bed_patient = models.ForeignKey(
        Patient,
        related_name="bed_patient",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    active = models.BooleanField(default=False)
    bed_state = models.CharField(
        max_length=30,
        default=BedState.FREE,
        choices=BedState.choices,
    )
    # bed states: free, occupied, call, task, call-task
    occupied_time = models.DateTimeField(null=True, blank=True)
    planed_vacate = models.DateTimeField(null=True, blank=True)
    vacate_time = models.DateTimeField(null=True, blank=True)
    action_done_by = models.CharField(default="Anónimo", max_length=50)

    # def __str__(self):
    #    return self.id_bed

    def serialize(self):
        return {
            "id": self.id,
            "id_bed": self.id_bed,
            "bed_patient": self.bed_patient.name,
            "bed_state": self.bed_state,
            "action_done_by": self.action_done_by,
        }


class MedicalRecord(models.Model):
    patient = models.OneToOneField(
        Patient, related_name="record_patient", on_delete=models.CASCADE
    )
    medical_record_id = models.CharField(max_length=50, null=True)
    medical_record_file = models.FileField(storage=mr_fs, null=True)
    action_done_by = models.CharField(default="Anónimo", max_length=50)

    def __str__(self):
        return self.medical_record_id

    def serialize(self):
        return {
            "id": self.id,
            "patient": self.patient.name,
            "medical_record_id": self.medical_record_id,
            "medical_record_file": self.medical_record_file,
            "action_done_by": self.action_done_by,
        }


class Task(models.Model):
    bed = models.ForeignKey(Bed, related_name="task_bed", on_delete=models.CASCADE)
    repeat = models.BooleanField(default=False)
    repeat_id = models.CharField(max_length=50, null=True, blank=True)
    repeat_lapse = models.IntegerField(
        null=True, blank=True
    )  # número de unidades (2, 3, etc)
    repeat_lapse_unit = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ("minutes", "Minutos"),
            ("hours", "Horas"),
            ("days", "Días"),
        ],
    )
    repeat_until = models.DateTimeField(null=True, blank=True)  # hasta cuándo repetir
    task = models.TextField(default="Tarea de Rutina")
    programed_time = models.DateTimeField(null=True, blank=True)
    done_time = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=False)
    state = models.CharField(
        default=TaskState.SOON, max_length=15, choices=TaskState.choices
    )  # later, soon, passed
    programed_by = models.CharField(default="Anónimo", max_length=50)
    task_done_by = models.CharField(default="Pendiente", max_length=50)
    action_done_by = models.CharField(default="Anónimo", max_length=50)

    def serialize(self):
        return {
            "id": self.id,
            "bed_id": self.bed.pk,
            "repeat": self.repeat,
            "repeat_id": self.repeat_id,
            "bed": self.bed.id_bed,
            "patient": self.bed.bed_patient.name,
            "task": self.task,
            "programed_time": dt_serialize(self.programed_time),
            "done_time": dt_serialize(self.done_time),
            "active": self.active,
            "state": self.state,
            "programed_by": self.programed_by,
            "task_done_by": self.task_done_by,
            "action_done_by": self.action_done_by,
        }


class Call(models.Model):
    bed = models.ForeignKey(Bed, related_name="call_bed", on_delete=models.CASCADE)
    response = models.TextField(default="Resapuesta sin novedad")
    call_time = models.DateTimeField(null=True, blank=True)
    response_time = models.DateTimeField(
        null=True, blank=True
    )  # This field is writen when call is answered
    state = models.CharField(
        default=CallState.ACTIVE, max_length=20, choices=CallState.choices
    )  # active, answered, closed
    action_done_by = models.CharField(default="Anónimo", max_length=50)
    # call states : active, answered, closed

    def serialize(self):
        return {
            "id": self.id,
            "bed_id": self.bed.pk,
            "bed": self.bed.id_bed,
            "patient": self.bed.bed_patient.name,
            "call_time": dt_serialize(self.call_time),
            "response_time": dt_serialize(self.response_time),
            "response": self.response,
            "state": self.state,
            "action_done_by": self.action_done_by,
        }


class Event(models.Model):
    loged_user = models.CharField(default="User", max_length=50)
    action = models.CharField(default="No Action", max_length=50)
    time = models.DateTimeField(null=True, blank=True)
    before = models.CharField(default="No Before", max_length=1000)
    after = models.CharField(default="No After", max_length=1000)

    def serialize(self):
        return {
            "id": self.id,
            "loged_user": self.loged_user,
            "action": self.action,
            "time": dt_serialize(self.time),
            "before": self.before,
            "after": self.after,
        }
