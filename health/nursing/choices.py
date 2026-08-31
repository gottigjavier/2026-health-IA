from django.db import models


class BedState(models.TextChoices):
    FREE = "free"
    OCCUPIED = "occupied"
    CALL = "call"
    TASK = "task"
    CALL_TASK = "call-task"
    SOON = "soon"
    LATER = "later"


class CallState(models.TextChoices):
    ACTIVE = "active"
    ANSWERED = "answered"
    CLOSED = "closed"


class TaskState(models.TextChoices):
    LATER = "later"
    SOON = "soon"
    PASSED = "passed"


class RoleChoices(models.TextChoices):
    OFFICE = "office"
    DOCTOR = "doctor"
    NURSE = "nurse"
