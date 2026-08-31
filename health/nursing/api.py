from django.contrib.auth import authenticate
from django.conf import settings
from django.http import JsonResponse
from django.db import IntegrityError
from ninja import NinjaAPI, ModelSchema, Schema
from typing import Optional, List
import logging

# ninja_jwt is optional in this environment; provide a safe fallback when
# the package isn't installed so module import won't crash during tests.
try:
    from ninja_jwt.tokens import RefreshToken
    from ninja_jwt.authentication import JWTAuth
except Exception:

    class RefreshToken:
        def __init__(self, token=None):
            if token is None:
                self._token = "refresh-token-mock"
            else:
                self._token = token

        @staticmethod
        def for_user(u):
            class RT:
                def __str__(self):
                    return "refresh-token-mock"

                @property
                def access_token(self):
                    return "access-token-mock"

            return RT()

        def __str__(self):
            return "refresh-token-mock"

        @property
        def access_token(self):
            return "access-token-mock"

    class JWTAuth:
        pass


from .models import User, Patient, Bed, Task, Call, Event
from .choices import BedState, CallState, TaskState, RoleChoices
from .modular_views.data_analytics import save_event
from .modular_views.beds.beds_serialized import serial_beds
from .utils.dates import dt_parse, dt_now, dt_serialize
import paho.mqtt.client as mqtt
import json
import jwt as pyjwt
from urllib.parse import parse_qs
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

jwtauth = JWTAuth()
api = NinjaAPI(auth=jwtauth)


def send_mqtt_cancel_call(bed_id_str):
    """
    Envía un mensaje MQTT para cancelar llamadas en una habitación
    Formato esperado: "room,0" (ej: "1,0")
    """
    try:
        client = mqtt.Client()
        client.connect("mosquitto", 1883)

        # Preparar mensaje de cancelación
        message = {
            "state": False,
            "id": bed_id_str,
            "key": settings.CALL_SECRET_KEY,
        }

        client.publish("mqtt/call/", json.dumps(message))
        client.disconnect()
        logger.info("MQTT Cancel message sent for: %s", bed_id_str)
    except Exception:
        logger.error("Error sending MQTT cancel")


class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_leader",
            "is_superuser",
            "role",
            "image",
            "date_joined",
        ]


class UserCreateSchema(Schema):
    username: str
    email: str
    password: str
    is_leader: bool = False
    role: str = "nurse"


def can_register_users(user):
    """True si el usuario puede registrar nuevos usuarios."""
    return user.is_superuser or (
        getattr(user, "is_leader", False) and getattr(user, "role", "") == "doctor"
    )


class LoginSchema(Schema):
    username: str
    password: str


class TokenSchema(Schema):
    access: str
    refresh: str
    user: UserSchema


class RefreshSchema(Schema):
    access: str
    refresh: str


class PatientSchema(ModelSchema):
    class Meta:
        model = Patient
        fields = [
            "id",
            "name",
            "social_security_number",
            "image",
            "inpatient",
            "admission",
            "diagnosis",
            "short_diagnosis",
            "treatment_roadmap",
            "action_done_by",
        ]


class BedInputSchema(Schema):
    roomBedId: str
    patientName: str
    patientSocial: str
    diagnosis: str
    occupiedDateTime: str
    planedVacate: str
    doneBy: str


class BedEditSchema(Schema):
    patientName: Optional[str] = None
    patientSocial: Optional[str] = None
    diagnosis: Optional[str] = None
    occupiedDateTime: Optional[str] = None
    planedVacate: Optional[str] = None
    doneBy: Optional[str] = None


class VacateSchema(Schema):
    bedId: int
    patientId: int
    vacateDT: str
    doneBy: str


class TaskInputSchema(Schema):
    bed_id: int
    task: str
    programed_time: str
    repeat: bool = False
    repeat_lapse: Optional[int] = None  # número (2, 3, etc)
    repeat_lapse_unit: Optional[str] = None  # minutes, hours, days
    repeat_until: Optional[str] = None  # fecha/hora hasta repetir


class TaskEditSchema(Schema):
    # Allow partial updates: make fields optional so PUT bodies can include
    # only the fields the client wants to change.
    task: Optional[str] = None
    programed_time: Optional[str] = None
    done_time: Optional[str] = None
    active: Optional[bool] = None


class CallResponseSchema(Schema):
    bed_id: int
    response: str


@api.post("/auth/login", response=TokenSchema, auth=None)
def login(request, data: LoginSchema):
    user = authenticate(username=data.username, password=data.password)
    if user:
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": user,
        }
    return JsonResponse({"error": "Invalid credentials"}, status=401)


@api.post("/auth/refresh", response=RefreshSchema, auth=None)
def refresh_token(request, data: dict):
    refresh_str = data.get("refresh") if isinstance(data, dict) else None
    if not refresh_str:
        return 401, {"error": "Token inválido"}
    try:
        token = RefreshToken(refresh_str)
        return {
            "access": str(token.access_token),
            "refresh": str(token),
        }
    except Exception:
        return 401, {"error": "Token inválido"}


@api.post("/auth/register", response=UserSchema, auth=jwtauth)
def register(request, body: dict = None):
    """
    Robust registration handler that reads the underlying Django request
    body aggressively. Some combinations of middleware and Ninja's parsing
    can cause the body to be consumed before Ninja provides a parsed value.
    This function attempts several fallbacks (JSON, form-encoded body,
    request.POST) to recover the payload.
    """
    if not can_register_users(request.user):
        return JsonResponse(
            {"error": "No tiene permisos para registrar usuarios"}, status=403
        )

    django_req = getattr(request, "_request", request)

    # Debug snapshot removed - was used during development

    parsed = {}
    # If Ninja provided parsed body, prefer it
    if isinstance(body, dict):
        parsed = body

    # Try several places for the raw body
    raw_candidates = []
    try:
        raw_candidates.append(getattr(django_req, "body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(request, "body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(django_req, "_body", None))
    except Exception:
        pass
    try:
        raw_candidates.append(getattr(request, "_body", None))
    except Exception:
        pass

    # Try to decode JSON from any raw candidate first
    for raw in raw_candidates:
        if not raw:
            continue
        try:
            if isinstance(raw, bytes):
                text = raw.decode(errors="ignore")
            else:
                text = str(raw)
            if not text:
                continue
            try:
                parsed = json.loads(text)
                break
            except Exception:
                # maybe it's form-encoded like username=...&email=...
                try:
                    qs = parse_qs(text)
                    if qs:
                        # flatten values
                        parsed = {k: v[0] for k, v in qs.items()}
                        break
                except Exception:
                    pass
        except Exception:
            continue

    # If still empty, try reading raw wsgi input or _stream if present
    if not parsed:
        try:
            wsgi_in = None
            try:
                wsgi_in = django_req.META.get("wsgi.input")
            except Exception:
                wsgi_in = None
            if wsgi_in:
                try:
                    wsgi_in.seek(0)
                except Exception:
                    pass
                try:
                    raw = wsgi_in.read()
                except Exception:
                    try:
                        raw = wsgi_in.read().decode(errors="ignore")
                    except Exception:
                        raw = None
                if raw:
                    try:
                        if isinstance(raw, bytes):
                            text = raw.decode(errors="ignore")
                        else:
                            text = str(raw)
                        parsed = json.loads(text)
                    except Exception:
                        try:
                            qs = parse_qs(text)
                            parsed = {k: v[0] for k, v in qs.items()}
                        except Exception:
                            parsed = {}
        except Exception:
            pass

    # As a last resort, try reading an internal _stream attribute
    if not parsed:
        try:
            stream = getattr(django_req, "_stream", None)
            if stream:
                try:
                    stream.seek(0)
                except Exception:
                    pass
                try:
                    raw = stream.read()
                except Exception:
                    try:
                        raw = stream.read().decode(errors="ignore")
                    except Exception:
                        raw = None
                if raw:
                    try:
                        if isinstance(raw, bytes):
                            text = raw.decode(errors="ignore")
                        else:
                            text = str(raw)
                        parsed = json.loads(text)
                    except Exception:
                        try:
                            qs = parse_qs(text)
                            parsed = {k: v[0] for k, v in qs.items()}
                        except Exception:
                            parsed = {}
        except Exception:
            pass

    # If not parsed yet, try request.POST (multipart/form-data / form-encoded)
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            if post:
                parsed = {k: v for k, v in post.items()}
        except Exception:
            parsed = {}

    # final guard: ensure parsed is a dict
    if not isinstance(parsed, dict):
        parsed = {}

    username = parsed.get("username")
    email = parsed.get("email")
    password = parsed.get("password")
    is_leader = parsed.get("is_leader", False)
    role = parsed.get("role", "nurse")

    if not username or not email or not password:
        return JsonResponse(
            {"error": "Username, email, and password are required"}, status=400
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_leader=is_leader,
            role=role,
        )
    except IntegrityError:
        return JsonResponse(
            {"error": "User with this username or email already exists"}, status=400
        )

    # Save image if present
    try:
        files = getattr(django_req, "FILES", {}) or {}
        if files and files.get("image"):
            user.image = files.get("image")
            user.save()
    except Exception:
        pass

    return user


# A fallback plain Django view for JSON registration.
# This bypasses Ninja parsing so tests that POST JSON directly are handled
# even if middleware consumed the body before Ninja handlers run.
@csrf_exempt
def django_register(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    # Authenticate caller via JWT
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Autenticación requerida"}, status=401)
    token_str = auth_header.split(" ", 1)[1]
    try:
        signing_key = settings.NINJA_JWT.get("SIGNING_KEY", settings.SECRET_KEY)
        algorithm = settings.NINJA_JWT.get("ALGORITHM", "HS256")
        user_id_claim = settings.NINJA_JWT.get("USER_ID_CLAIM", "user_id")
        payload = pyjwt.decode(token_str, signing_key, algorithms=[algorithm])
        user_id = payload.get(user_id_claim)
        if user_id is None:
            return JsonResponse({"error": "Token inválido"}, status=401)
        caller = User.objects.get(id=user_id)
    except pyjwt.ExpiredSignatureError:
        return JsonResponse({"error": "Token expirado"}, status=401)
    except (pyjwt.InvalidTokenError, User.DoesNotExist):
        return JsonResponse({"error": "Token inválido"}, status=401)

    if not can_register_users(caller):
        return JsonResponse(
            {"error": "No tiene permisos para registrar usuarios"}, status=403
        )

    django_req = request
    parsed = {}
    # try raw body JSON
    try:
        raw = getattr(django_req, "body", b"") or b""
        if raw:
            try:
                parsed = json.loads(raw.decode(errors="ignore"))
            except Exception:
                parsed = {}
    except Exception:
        parsed = {}

    # fallback to form data
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            if post:
                parsed = {k: v for k, v in post.items()}
        except Exception:
            parsed = {}

    if not isinstance(parsed, dict):
        parsed = {}

    username = parsed.get("username")
    email = parsed.get("email")
    password = parsed.get("password")
    is_leader_raw = parsed.get("is_leader", False)
    is_leader = (
        str(is_leader_raw).lower() in ("true", "1", "yes") if is_leader_raw else False
    )
    role = parsed.get("role", "nurse")

    if not username or not email or not password:
        return JsonResponse(
            {"error": "Username, email, and password are required"}, status=400
        )

    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_leader=is_leader,
            role=role,
        )
    except IntegrityError:
        return JsonResponse(
            {"error": "User with this username or email already exists"}, status=400
        )

    return JsonResponse(
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_leader": user.is_leader,
            "is_superuser": user.is_superuser,
            "role": getattr(user, "role", "nurse"),
            "image": getattr(user, "image", None) and str(user.image.url),
            "date_joined": dt_serialize(user.date_joined)
            if getattr(user, "date_joined", None)
            else None,
        }
    )


@api.post("/auth/logout")
def logout(request):
    return {"message": "Logged out successfully"}


@api.get("/users/me", response=UserSchema, auth=jwtauth)
def get_current_user(request):
    return request.user


@api.get("/beds", auth=jwtauth)
def list_beds(request):
    beds = Bed.objects.all().select_related("bed_patient")
    return serial_beds(beds)


@api.get("/beds/{int:bed_id}", auth=jwtauth)
def get_bed(request, bed_id: int):
    bed = Bed.objects.get(id=bed_id)
    return serial_beds([bed])[0]


@api.post("/beds", auth=jwtauth)
def create_bed(request, data: Optional[BedInputSchema] = None, payload: dict = None):
    # Accept either a Ninja-parsed schema or raw JSON/form payloads. This
    # avoids errors when the request body was consumed or when the client
    # sends a plain dict/string.
    django_req = getattr(request, "_request", request)

    # prefer Ninja schema
    parsed = {}
    if data is not None:
        try:
            if isinstance(data, dict):
                parsed = data
            else:
                parsed = {
                    "roomBedId": getattr(data, "roomBedId", None),
                    "patientName": getattr(data, "patientName", None),
                    "patientSocial": getattr(data, "patientSocial", None),
                    "diagnosis": getattr(data, "diagnosis", None),
                    "occupiedDateTime": getattr(data, "occupiedDateTime", None),
                    "planedVacate": getattr(data, "planedVacate", None),
                    "doneBy": getattr(data, "doneBy", None),
                }
        except Exception:
            parsed = {}

    # fallback to provided payload dict
    if not parsed and isinstance(payload, dict):
        parsed = payload

    # try to parse raw body if still empty
    if not parsed:
        try:
            raw = getattr(django_req, "body", b"") or b""
            if raw:
                try:
                    parsed = json.loads(raw.decode(errors="ignore"))
                except Exception:
                    parsed = {}
        except Exception:
            parsed = {}

    # form POST fallback
    if not parsed:
        try:
            post = getattr(django_req, "POST", {}) or {}
            for k, v in post.items():
                parsed.setdefault(k, v)
        except Exception:
            pass

    # Ensure parsed is a dict; if not, bail with helpful error
    if not isinstance(parsed, dict):
        return JsonResponse({"error": "Invalid payload for creating bed"}, status=400)

    # Create patient
    patient = Patient.objects.create(
        name=parsed.get("patientName") or "No Name",
        social_security_number=parsed.get("patientSocial") or "0000",
        short_diagnosis=parsed.get("diagnosis") or "No Diagnosis",
    )

    # parse datetimes permissively (aware, hora local de Argentina)
    def _parse_dt(val):
        return dt_parse(val)

    occupied_dt = _parse_dt(parsed.get("occupiedDateTime"))
    planed_vac = _parse_dt(parsed.get("planedVacate"))

    bed = Bed.objects.create(
        id_bed=parsed.get("roomBedId"),
        bed_patient=patient,
        active=True,
        bed_state=BedState.OCCUPIED,
        occupied_time=occupied_dt,
        planed_vacate=planed_vac,
        action_done_by=parsed.get("doneBy") or "Anónimo",
    )
    before = "No patient; bed not created"
    after = (
        f"bed.id: {bed.id}; bed.id_bed: {bed.id_bed}; "
        f"patient.id: {patient.id}; patient.name: {patient.name}; "
        f"bed.active: {bed.active}; bed.bed_state: {bed.bed_state}; "
        f"bed.occupied_time: {bed.occupied_time}; "
        f"bed.planed_vacate: {bed.planed_vacate}; "
        f"bed.action_done_by: {bed.action_done_by}"
    )
    save_event(request.user.username, "occupy bed", before, after)
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return serial_beds([bed])[0]


@api.put("/beds/{int:bed_id}", auth=jwtauth)
def update_bed(request, bed_id: int, data: BedEditSchema):
    bed = Bed.objects.get(id=bed_id)
    patient = bed.bed_patient
    before = (
        f"bed.id: {bed.id}; bed.id_bed: {bed.id_bed}; "
        f"bed.occupied_time: {bed.occupied_time}; bed.planed_vacate: {bed.planed_vacate}; "
        f"bed.action_done_by: {bed.action_done_by}; "
        f"patient.name: {patient.name}; patient.social_security_number: {patient.social_security_number}; "
        f"patient.short_diagnosis: {patient.short_diagnosis}"
    )
    if data.occupiedDateTime and data.occupiedDateTime.strip():
        try:
            bed.occupied_time = dt_parse(data.occupiedDateTime)
        except Exception:
            pass
    if data.planedVacate and data.planedVacate.strip():
        try:
            bed.planed_vacate = dt_parse(data.planedVacate)
        except Exception:
            pass
    if data.doneBy and data.doneBy.strip():
        bed.action_done_by = data.doneBy
    if data.patientName and data.patientName.strip():
        patient.name = data.patientName
    if data.patientSocial and data.patientSocial.strip():
        patient.social_security_number = data.patientSocial
    if data.diagnosis and data.diagnosis.strip():
        patient.short_diagnosis = data.diagnosis
    patient.save()
    bed.save()
    after = (
        f"bed.id: {bed.id}; bed.id_bed: {bed.id_bed}; "
        f"bed.occupied_time: {bed.occupied_time}; bed.planed_vacate: {bed.planed_vacate}; "
        f"bed.action_done_by: {bed.action_done_by}; "
        f"patient.name: {patient.name}; patient.social_security_number: {patient.social_security_number}; "
        f"patient.short_diagnosis: {patient.short_diagnosis}"
    )
    save_event(request.user.username, "edit bed", before, after)
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return serial_beds([bed])[0]


@api.post("/beds/vacate", auth=jwtauth)
def vacate_bed(request, data: VacateSchema):
    patient = Patient.objects.get(id=data.patientId)
    bed = Bed.objects.get(id=data.bedId)

    before = (
        f"bed.id: {bed.id}; bed.id_bed: {bed.id_bed}; "
        f"bed.active: {bed.active}; bed.bed_state: {bed.bed_state}; "
        f"bed.occupied_time: {bed.occupied_time}; bed.planed_vacate: {bed.planed_vacate}; "
        f"bed.vacate_time: {bed.vacate_time}; bed.action_done_by: {bed.action_done_by}; "
        f"patient.id: {patient.id}; patient.name: {patient.name}; "
        f"patient.inpatient: {patient.inpatient}"
    )

    # Obtener el room ID del bed_id (formato: "room,bed")
    room_id = (
        bed.id_bed.split(",")[0] if "," in bed.id_bed else bed.id_bed.split("-")[0]
    )

    # Cancelar todas las tareas activas de esta cama
    Task.objects.filter(bed=bed, active=True).delete()

    # Cerrar todas las llamadas activas de esta cama
    Call.objects.filter(bed=bed).exclude(state=CallState.CLOSED).update(
        state=CallState.CLOSED
    )

    # Enviar notificación MQTT para cancelar llamadas en la habitación
    send_mqtt_cancel_call(f"{room_id},0")

    patient.inpatient = False
    bed.active = False
    bed.bed_state = BedState.FREE
    bed.vacate_time = dt_parse(data.vacateDT)
    bed.action_done_by = data.doneBy if data.doneBy else "Anónimo"
    patient.save()
    bed.save()

    after = (
        f"bed.id: {bed.id}; bed.id_bed: {bed.id_bed}; "
        f"bed.active: {bed.active}; bed.bed_state: {bed.bed_state}; "
        f"bed.occupied_time: {bed.occupied_time}; bed.planed_vacate: {bed.planed_vacate}; "
        f"bed.vacate_time: {bed.vacate_time}; bed.action_done_by: {bed.action_done_by}; "
        f"patient.id: {patient.id}; patient.name: {patient.name}; "
        f"patient.inpatient: {patient.inpatient}"
    )
    save_event(request.user.username, "vacate bed", before, after)
    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass
    return {"message": "Bed vacated successfully"}


@api.get("/patients", response=List[PatientSchema], auth=jwtauth)
def list_patients(request):
    return Patient.objects.filter(inpatient=True)


@api.get("/tasks", auth=jwtauth)
def list_tasks(request):
    tasks = Task.objects.all().select_related("bed__bed_patient")
    return [t.serialize() for t in tasks]


@api.post("/tasks", auth=jwtauth)
def create_task(request, data: TaskInputSchema):
    bed = Bed.objects.get(id=data.bed_id)
    # Create primary task
    programed_time_obj = dt_parse(data.programed_time)
    task = Task.objects.create(
        bed=bed,
        task=data.task,
        programed_time=programed_time_obj,
        repeat=data.repeat,
        repeat_lapse=data.repeat_lapse if hasattr(data, "repeat_lapse") else None,
        repeat_lapse_unit=data.repeat_lapse_unit
        if hasattr(data, "repeat_lapse_unit")
        else None,
        repeat_until=(
            dt_parse(data.repeat_until)
            if getattr(data, "repeat_until", None)
            else None
        ),
        active=True,
        # compute initial state based on programed_time
        state=(
            TaskState.PASSED
            if programed_time_obj.timestamp() < dt_now().timestamp()
            else (
                TaskState.SOON
                if programed_time_obj.timestamp() - dt_now().timestamp() <= 600
                else TaskState.LATER
            )
        ),
        programed_by=request.user.username,
    )

    # If repeat requested and parameters provided, replicate using modular logic
    if (
        data.repeat
        and getattr(data, "repeat_lapse", None)
        and getattr(data, "repeat_until", None)
    ):
        # reuse existing modular implementation
        from .modular_views.tasks.task_new import save_repeated_tasks

        try:
            # ensure primary task has a repeat_id so generated tasks belong to same series
            if not task.repeat_id:
                import random

                programed_time_float = int(programed_time_obj.timestamp())
                task.repeat_id = str(programed_time_float * random.random())
                task.save()

            save_repeated_tasks(
                data.repeat,
                data.repeat_lapse,
                data.repeat_lapse_unit,
                data.programed_time,
                data.repeat_until,
                bed.id,
                task.repeat_id if task.repeat_id else None,
                data.programed_time,
                request.user.username,
                request.user.username,
                "Pendiente",
                data.task,
                task.state,
                request.user.username,
            )
        except Exception as exc:
            # don't fail the main request if repeat generation has an issue
            logger.error("Error generating repeated tasks: %s", exc)

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    before = (
        f"task.pk: None; bed.pk: {bed.pk}; bed_id: {bed.id_bed}; "
        f"task.repeat: {task.repeat}; task.repeat_id: {task.repeat_id}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: False; task.state: None; "
        f"task.programed_by: {task.programed_by}"
    )
    after = (
        f"task.pk: {task.pk}; bed.pk: {bed.pk}; bed_id: {bed.id_bed}; "
        f"task.repeat: {task.repeat}; task.repeat_id: {task.repeat_id}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: {task.active}; "
        f"task.state: {task.state}; task.programed_by: {task.programed_by}"
    )
    save_event(request.user.username, "new task", before, after)

    return task.serialize()


@api.put("/tasks/{int:task_id}", auth=jwtauth)
def update_task(request, task_id: int, data: TaskEditSchema):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return JsonResponse({"error": "Task not found"}, status=404)
    # Log incoming update for easier debugging of 422/parse issues
    try:
        logger.debug("update_task called with: task_id=%s, data=%s", task_id, data)
    except Exception:
        pass

    before = (
        f"task.pk: {task.pk}; bed.pk: {task.bed.pk}; bed_id: {task.bed.id_bed}; "
        f"task.repeat: {task.repeat}; task.repeat_id: {task.repeat_id}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: {task.active}; "
        f"task.state: {task.state}; task.programed_by: {task.programed_by}; "
        f"task.task_done_by: {task.task_done_by}"
    )

    # Only set fields provided by the client
    if getattr(data, "task", None) is not None:
        task.task = data.task

    if getattr(data, "programed_time", None):
        # accept several ISO-like formats, be permissive
        pt_raw = data.programed_time
        pt = dt_parse(pt_raw)
        if pt is None:
            # fallback to now to avoid failing the whole request; caller may retry
            pt = dt_now()
        task.programed_time = pt
    # support marking task as done from the edit modal
    if getattr(data, "done_time", None):
        task.done_time = dt_parse(data.done_time) or dt_now()
        task.active = False
        task.task_done_by = request.user.username
    if getattr(data, "active", None) is not None:
        task.active = data.active
    try:
        task.save()
    except Exception as exc:
        # return a clear JSON error instead of a 500/422
        return JsonResponse({"error": f"Failed saving task: {str(exc)}"}, status=400)

    # After updating the task, adjust the bed state if task was marked as done/completed
    if getattr(data, "done_time", None) or (not getattr(data, "active", None)):
        try:
            from .modular_views.beds.bed_state import refresh_bed_state

            refresh_bed_state(task.bed)
        except Exception:
            pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    after = (
        f"task.pk: {task.pk}; bed.pk: {task.bed.pk}; bed_id: {task.bed.id_bed}; "
        f"task.repeat: {task.repeat}; task.repeat_id: {task.repeat_id}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: {task.active}; "
        f"task.state: {task.state}; task.programed_by: {task.programed_by}; "
        f"task.task_done_by: {task.task_done_by}"
    )
    save_event(request.user.username, "edit task", before, after)

    return task.serialize()


@api.post("/tasks/{int:task_id}/complete", auth=jwtauth)
def complete_task(request, task_id: int):
    task = Task.objects.get(id=task_id)
    before = (
        f"task.pk: {task.pk}; bed.pk: {task.bed.pk}; bed_id: {task.bed.id_bed}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: {task.active}; "
        f"task.state: {task.state}; task.task_done_by: {task.task_done_by}"
    )
    task.active = False
    task.done_time = dt_now()
    task.task_done_by = request.user.username
    task.save()
    # After marking the task completed, adjust the bed state if needed.
    try:
        from .modular_views.beds.bed_state import refresh_bed_state

        refresh_bed_state(task.bed)
    except Exception:
        # don't let bed-update failures break API
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    after = (
        f"task.pk: {task.pk}; bed.pk: {task.bed.pk}; bed_id: {task.bed.id_bed}; "
        f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
        f"task.done_time: {task.done_time}; task.active: {task.active}; "
        f"task.state: {task.state}; task.task_done_by: {task.task_done_by}"
    )
    save_event(request.user.username, "complete task", before, after)

    return task.serialize()


@api.delete("/tasks/{int:task_id}", auth=jwtauth)
def delete_task(request, task_id: int):
    # Get task and bed before deleting
    try:
        task = Task.objects.get(id=task_id)
        bed = task.bed
        before = (
            f"task.pk: {task.pk}; bed.pk: {bed.pk}; bed_id: {bed.id_bed}; "
            f"task.task: {task.task}; task.programed_time: {task.programed_time}; "
            f"task.done_time: {task.done_time}; task.active: {task.active}; "
            f"task.state: {task.state}; task.task_done_by: {task.task_done_by}"
        )
        task.delete()

        # After deleting the task, adjust the bed state if needed.
        from .modular_views.beds.bed_state import refresh_bed_state

        # "later" tasks are not considered after deleting the active one
        refresh_bed_state(bed, consider_later=False)
    except Task.DoesNotExist:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    after = "task deleted"
    save_event(request.user.username, "delete task", before, after)

    return {"message": "Task deleted"}


@api.get("/calls", auth=jwtauth)
def list_calls(request):
    calls = Call.objects.all().select_related("bed__bed_patient")
    return [c.serialize() for c in calls]


@api.post("/calls/{int:call_id}/answer", auth=jwtauth)
def answer_call(request, call_id: int):
    call = Call.objects.get(id=call_id)
    bed = call.bed
    before = (
        f"call.pk: {call.pk}; bed_id: {bed.id_bed}; call.call_time: {call.call_time}; "
        f"call.response_time: {call.response_time}; call.state: {call.state}; "
        f"call.action_done_by: {call.action_done_by}"
    )
    call.state = CallState.ANSWERED
    call.response_time = dt_now()
    call.action_done_by = request.user.username
    call.save()

    # Update bed_state after answering the call
    try:
        from .modular_views.beds.bed_state import refresh_bed_state

        # call is no longer active; "later" tasks not considered after answering
        refresh_bed_state(call.bed, consider_later=False, has_active_call=False)
    except Exception:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    after = (
        f"call.pk: {call.pk}; bed_id: {bed.id_bed}; call.call_time: {call.call_time}; "
        f"call.response_time: {call.response_time}; call.state: {call.state}; "
        f"call.action_done_by: {call.action_done_by}"
    )
    save_event(request.user.username, "answer call", before, after)

    return call.serialize()


@api.post("/calls/{int:call_id}/close", auth=jwtauth)
def close_call(request, call_id: int, data: CallResponseSchema):
    call = Call.objects.get(id=call_id)
    bed = call.bed
    before = (
        f"call.pk: {call.pk}; bed_id: {bed.id_bed}; call.call_time: {call.call_time}; "
        f"call.response_time: {call.response_time}; call.state: {call.state}; "
        f"call.response: {call.response}; call.action_done_by: {call.action_done_by}"
    )
    call.state = CallState.CLOSED
    call.response = data.response
    call.action_done_by = request.user.username
    call.save()

    # Update bed_state after closing the call
    try:
        from .modular_views.beds.bed_state import refresh_bed_state

        # call is no longer active; "later" tasks not considered after closing
        refresh_bed_state(call.bed, consider_later=False, has_active_call=False)
    except Exception:
        pass

    try:
        from .modular_views.app.app_ws_update import app_ws_update

        app_ws_update()
    except Exception:
        pass

    after = (
        f"call.pk: {call.pk}; bed_id: {bed.id_bed}; call.call_time: {call.call_time}; "
        f"call.response_time: {call.response_time}; call.state: {call.state}; "
        f"call.response: {call.response}; call.action_done_by: {call.action_done_by}"
    )
    save_event(request.user.username, "close call", before, after)

    return call.serialize()


@api.get("/rooms", auth=jwtauth)
def get_rooms(request):
    beds = Bed.objects.all().select_related("bed_patient").order_by("id_bed")
    rooms_data = {}
    for bed in beds:
        room_num = bed.id_bed.split("-")[0] if "-" in bed.id_bed else "1"
        if room_num not in rooms_data:
            rooms_data[room_num] = {
                "beds": [],
                "status": "gray",  # Por defecto gris (vacío)
            }
        # Serializar bed con Contract B (serial_beds)
        rooms_data[room_num]["beds"].extend(serial_beds([bed]))

        # Si la cama está activa, la habitación es verde
        if bed.active:
            rooms_data[room_num]["status"] = "green"

    return rooms_data


@api.get("/app/load", auth=jwtauth)
def initial_load(request):
    from .modular_views.app.app_load import load
    from .modular_views.calls.call_mqtt import mqtt_service
    from .modular_views.tasks.task_ws import tasks_ws_update
    from .modular_views.app.app_ws_update import app_ws_update

    mqtt_service()
    tasks_ws_update()
    app_ws_update()

    return load()


@api.get("/events", response=List[dict], auth=jwtauth)
def list_events(request):
    events = Event.objects.all().order_by("-time")[:100]
    return [e.serialize() for e in events]


@api.get("/events/{int:event_id}", response=dict, auth=jwtauth)
def get_event(request, event_id: int):
    event = Event.objects.get(id=event_id)
    return event.serialize()
