from unittest import mock
import importlib
import json

from django.test import TestCase
from django.test import Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from nursing.models import Event, Bed, Patient, Task, Call
from nursing.choices import BedState, CallState, TaskState
from nursing.modular_views.beds.beds_serialized import serial_beds
from nursing.modular_views.data_analytics import save_event
from nursing.modular_views.app import app_load


User = get_user_model()


# Shapes Contract B canónicos (fuente única: serial_beds + model.serialize)
CANONICAL_BED_KEYS = {
    "id", "bed_id", "bed_active", "bed_occupied_time", "bed_planed_vacate",
    "bed_state", "patient", "patient_id", "patient_security_number", "image",
    "diagnosis", "action_done_by",
}
CANONICAL_TASK_KEYS = {
    "id", "bed_id", "repeat", "repeat_id", "bed", "patient", "task",
    "programed_time", "done_time", "active", "state", "programed_by",
    "task_done_by", "action_done_by",
}
CANONICAL_CALL_KEYS = {
    "id", "bed_id", "bed", "patient", "call_time", "response_time",
    "response", "state", "action_done_by",
}

NAIVE_DT_REGEX = r"[+-]\d{2}:\d{2}$|Z$"


class EventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="12345",
            short_diagnosis="Test Diagnosis",
        )
        self.bed = Bed.objects.create(
            id_bed="1-1", bed_patient=self.patient, active=True, bed_state=BedState.OCCUPIED
        )

    def test_create_event(self):
        event = Event.objects.create(
            loged_user="testuser",
            action="test action",
            time=timezone.now(),
            before="before state",
            after="after state",
        )
        self.assertEqual(event.loged_user, "testuser")
        self.assertEqual(event.action, "test action")
        self.assertEqual(event.before, "before state")
        self.assertEqual(event.after, "after state")

    def test_save_event_function(self):
        save_event("testuser", "occupy bed", "No patient", "bed occupied")
        events = Event.objects.filter(action="occupy bed")
        self.assertEqual(events.count(), 1)
        self.assertEqual(events.first().loged_user, "testuser")

    def test_save_event_without_error(self):
        try:
            save_event("testuser", "test action", "before", "after")
            saved = Event.objects.filter(action="test action").exists()
            self.assertTrue(saved)
        except Exception as e:
            self.fail(f"save_event raised exception: {e}")

    def test_save_event_with_empty_fields(self):
        save_event("", "", "", "")
        events = Event.objects.filter(loged_user="")
        self.assertEqual(events.count(), 1)

    def test_event_serialization(self):
        event = Event.objects.create(
            loged_user="testuser",
            action="test action",
            time=timezone.now(),
            before="before",
            after="after",
        )
        serialized = event.serialize()
        self.assertEqual(serialized["loged_user"], "testuser")
        self.assertEqual(serialized["action"], "test action")


class EventTrackingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient", social_security_number="12345"
        )
        self.bed = Bed.objects.create(
            id_bed="1-1", bed_patient=self.patient, active=True, bed_state=BedState.OCCUPIED
        )

    def test_event_created_on_task_creation(self):
        initial_count = Event.objects.count()
        Task.objects.create(
            bed=self.bed,
            task="Test Task",
            programed_time=timezone.now(),
            active=True,
            state=TaskState.LATER,
            programed_by="testuser",
        )
        self.assertEqual(Event.objects.count(), initial_count + 1)

    def test_event_created_on_task_completion(self):
        task = Task.objects.create(
            bed=self.bed,
            task="Test Task",
            programed_time=timezone.now(),
            active=True,
            state=TaskState.LATER,
            programed_by="testuser",
        )
        initial_count = Event.objects.count()

        task.active = False
        task.done_time = timezone.now()
        task.task_done_by = "testuser"
        task.save()

        self.assertEqual(Event.objects.count(), initial_count + 1)

    def test_event_created_on_call_answer(self):
        call = Call.objects.create(
            bed=self.bed, call_time=timezone.now(), state=CallState.ACTIVE
        )
        initial_count = Event.objects.count()

        call.state = CallState.ANSWERED
        call.response_time = timezone.now()
        call.action_done_by = "testuser"
        call.save()

        self.assertEqual(Event.objects.count(), initial_count + 1)

    def test_event_created_on_bed_occupancy(self):
        patient2 = Patient.objects.create(
            name="Patient 2", social_security_number="67890"
        )
        bed2 = Bed.objects.create(
            id_bed="1-2", bed_patient=patient2, active=True, bed_state=BedState.FREE
        )
        initial_count = Event.objects.count()

        bed2.bed_state = BedState.OCCUPIED
        bed2.save()

        self.assertEqual(Event.objects.count(), initial_count + 1)

    def test_event_created_on_bed_vacate(self):
        self.bed.bed_state = BedState.FREE
        self.bed.active = False
        self.bed.save()

        initial_count = Event.objects.count()

        self.bed.bed_state = BedState.FREE
        self.bed.active = False
        self.bed.vacate_time = timezone.now()
        self.bed.save()

        self.assertEqual(Event.objects.count(), initial_count + 1)


class SaveEventEdgeCasesTest(TestCase):
    def test_save_event_with_very_long_strings(self):
        long_string = "x" * 1000
        try:
            save_event(long_string, long_string, long_string, long_string)
            event = Event.objects.last()
            self.assertEqual(len(event.loged_user), 1000)
        except Exception:
            self.fail("save_event should handle long strings")

    def test_save_event_with_special_characters(self):
        try:
            save_event("user@domain.com", "action <>&", "before\n\t\r", "after")
            event = Event.objects.last()
            self.assertIsNotNone(event)
        except Exception:
            self.fail("save_event should handle special characters")

    def test_save_event_with_none_values(self):
        try:
            save_event(None, None, None, None)
            event = Event.objects.last()
            self.assertIsNotNone(event)
        except Exception:
            self.fail("save_event should handle None values")


class BedContractTest(TestCase):
    """Fase A T1.1 — Congela el shape Contract B de serial_beds() (fuente única Bed)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="884455",
            short_diagnosis="Post-operatorio",
        )
        self.bed = Bed.objects.create(
            id_bed="1,1",
            bed_patient=self.patient,
            active=True,
            bed_state=BedState.OCCUPIED,
            occupied_time=timezone.now(),
            planed_vacate=timezone.now(),
            action_done_by="Dres. López",
        )
        self.bed_without_patient = Bed.objects.create(
            id_bed="2,1",
            bed_patient=None,
            active=False,
            bed_state=BedState.FREE,
        )

    def test_bed_shape_with_patient(self):
        serialized = serial_beds([self.bed])[0]
        self.assertEqual(set(serialized.keys()), CANONICAL_BED_KEYS)

    def test_bed_id_format(self):
        serialized = serial_beds([self.bed])[0]
        self.assertEqual(serialized["bed_id"], "1,1")
        self.assertIsInstance(serialized["bed_id"], str)

    def test_bed_active_type(self):
        serialized = serial_beds([self.bed])[0]
        self.assertIsInstance(serialized["bed_active"], bool)

    def test_bed_patient_name(self):
        serialized = serial_beds([self.bed])[0]
        self.assertEqual(serialized["patient"], "Test Patient")
        self.assertEqual(serialized["patient_id"], self.patient.pk)
        self.assertEqual(serialized["patient_security_number"], "884455")

    def test_bed_naive_timestamps(self):
        serialized = serial_beds([self.bed])[0]
        for field in ("bed_occupied_time", "bed_planed_vacate"):
            value = serialized[field]
            if value is not None:
                self.assertNotRegex(value, NAIVE_DT_REGEX)

    def test_bed_without_patient(self):
        serialized = serial_beds([self.bed_without_patient])[0]
        self.assertEqual(serialized["patient"], None)
        self.assertEqual(serialized["patient_id"], None)
        self.assertEqual(serialized["patient_security_number"], None)
        self.assertEqual(serialized["image"], None)
        self.assertEqual(serialized["diagnosis"], None)


class TaskContractTest(TestCase):
    """Fase A T1.2 — Congela el shape Contract B de Task.serialize()."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="884455",
            short_diagnosis="Post-operatorio",
        )
        self.bed = Bed.objects.create(
            id_bed="1,1",
            bed_patient=self.patient,
            active=True,
            bed_state=BedState.OCCUPIED,
        )
        self.task = Task.objects.create(
            bed=self.bed,
            repeat=False,
            repeat_id=None,
            task="Dar medicación",
            programed_time=timezone.now(),
            active=True,
            state=TaskState.SOON,
            programed_by="admin",
        )

    def test_task_shape(self):
        serialized = self.task.serialize()
        self.assertEqual(set(serialized.keys()), CANONICAL_TASK_KEYS)

    def test_task_bed_string(self):
        serialized = self.task.serialize()
        self.assertIsInstance(serialized["bed"], str)
        self.assertIn(",", serialized["bed"])
        self.assertEqual(serialized["bed"], "1,1")

    def test_task_bed_id_int(self):
        serialized = self.task.serialize()
        self.assertIsInstance(serialized["bed_id"], int)
        self.assertEqual(serialized["bed_id"], self.bed.pk)

    def test_task_naive_timestamps(self):
        serialized = self.task.serialize()
        for field in ("programed_time", "done_time"):
            value = serialized[field]
            if value is not None:
                self.assertNotRegex(value, NAIVE_DT_REGEX)


class CallContractTest(TestCase):
    """Fase A T1.3 — Congela el shape Contract B de Call.serialize()."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="884455",
            short_diagnosis="Post-operatorio",
        )
        self.bed = Bed.objects.create(
            id_bed="1,1",
            bed_patient=self.patient,
            active=True,
            bed_state=BedState.OCCUPIED,
        )
        self.call = Call.objects.create(
            bed=self.bed,
            call_time=timezone.now(),
            response_time=timezone.now(),
            response="Respuesta sin novedad",
            state=CallState.ACTIVE,
            action_done_by="admin",
        )

    def test_call_shape(self):
        serialized = self.call.serialize()
        self.assertEqual(set(serialized.keys()), CANONICAL_CALL_KEYS)

    def test_call_bed_string(self):
        serialized = self.call.serialize()
        self.assertIsInstance(serialized["bed"], str)
        self.assertIn(",", serialized["bed"])
        self.assertEqual(serialized["bed"], "1,1")

    def test_call_bed_id_int(self):
        serialized = self.call.serialize()
        self.assertIsInstance(serialized["bed_id"], int)
        self.assertEqual(serialized["bed_id"], self.bed.pk)

    def test_call_naive_timestamps(self):
        serialized = self.call.serialize()
        for field in ("call_time", "response_time"):
            value = serialized[field]
            if value is not None:
                self.assertNotRegex(value, NAIVE_DT_REGEX)


class BoardDataContractTest(TestCase):
    """Fase A T1.4 — Congela el shape board_data {beds,patients,calls,tasks} (Contract B)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="884455",
            short_diagnosis="Post-operatorio",
            inpatient=True,
        )
        self.bed = Bed.objects.create(
            id_bed="1,1",
            bed_patient=self.patient,
            active=True,
            bed_state=BedState.OCCUPIED,
            occupied_time=timezone.now(),
        )
        self.task = Task.objects.create(
            bed=self.bed,
            task="Dar medicación",
            programed_time=timezone.now(),
            active=True,
            state=TaskState.SOON,
            programed_by="admin",
        )
        self.call = Call.objects.create(
            bed=self.bed,
            call_time=timezone.now(),
            state=CallState.ACTIVE,
        )

    def _load_json(self):
        """Llama load() aislado de scheduler/websocket (infra no testeable en TestCase)
        y devuelve el dict del payload board_data.
        """
        with mock.patch.object(app_load, "tasks_scheduler"), \
             mock.patch.object(app_load, "app_ws_update"):
            response = app_load.load()
        return json.loads(response.content)

    def test_load_shape(self):
        """load() devuelve JsonResponse con keys {beds,patients,calls,tasks}."""
        data = self._load_json()
        self.assertEqual(set(data.keys()), {"beds", "patients", "calls", "tasks"})

    def test_load_beds_are_contract_b(self):
        data = self._load_json()
        self.assertEqual(set(data["beds"][0].keys()), CANONICAL_BED_KEYS)
        self.assertEqual(data["beds"][0]["bed_id"], "1,1")

    def test_load_tasks_are_contract_b(self):
        data = self._load_json()
        self.assertEqual(set(data["tasks"][0].keys()), CANONICAL_TASK_KEYS)

    def test_load_calls_are_contract_b(self):
        data = self._load_json()
        self.assertEqual(set(data["calls"][0].keys()), CANONICAL_CALL_KEYS)


class ApiContractTest(TestCase):
    """Fase C T3.5 — Los endpoints REST /api/beds, /api/tasks, /api/calls
    devuelven Contract B (mismo shape que serial_beds()/serialize()).

    Los endpoints usan `auth=jwtauth` (ninja_jwt JWTAuth). En TestCase no hay
    token JWT real, así que se parchea `JWTAuth.authenticate` para devolver el
    user de test (a nivel de clase → aplica a todos los handlers autenticados).
    """

    def setUp(self):
        from ninja_jwt.authentication import JWTAuth

        self.JWTAuth = JWTAuth
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.patient = Patient.objects.create(
            name="Test Patient",
            social_security_number="884455",
            short_diagnosis="Post-operatorio",
            inpatient=True,
        )
        self.bed = Bed.objects.create(
            id_bed="1,1",
            bed_patient=self.patient,
            active=True,
            bed_state=BedState.OCCUPIED,
            occupied_time=timezone.now(),
        )
        self.task = Task.objects.create(
            bed=self.bed,
            task="Dar medicación",
            programed_time=timezone.now(),
            active=True,
            state=TaskState.SOON,
            programed_by="admin",
        )
        self.call = Call.objects.create(
            bed=self.bed,
            call_time=timezone.now(),
            state=CallState.ACTIVE,
        )
        self.client = Client()
        # HttpBearer.__call__ devuelve None si no hay header Authorization → 401.
        # Seteamos un token fake; JWTAuth.authenticate está parcheado para ignorarlo.
        self.client.defaults = {"HTTP_AUTHORIZATION": "Bearer faketoken"}
        # Autenticar como self.user para todos los requests del test
        patcher = mock.patch.object(self.JWTAuth, "authenticate", return_value=self.user)
        patcher.start()
        self.addCleanup(patcher.stop)

    # --- Bed ---

    def test_get_beds_returns_contract_b(self):
        resp = self.client.get("/api/beds")
        self.assertEqual(resp.status_code, 200)
        beds = resp.json()
        self.assertIsInstance(beds, list)
        self.assertEqual(set(beds[0].keys()), CANONICAL_BED_KEYS)
        self.assertEqual(beds[0]["bed_id"], "1,1")
        self.assertIsInstance(beds[0]["bed_id"], str)
        for field in ("bed_occupied_time", "bed_planed_vacate"):
            value = beds[0][field]
            if value is not None:
                self.assertNotRegex(value, NAIVE_DT_REGEX)

    def test_get_bed_single_returns_contract_b(self):
        resp = self.client.get(f"/api/beds/{self.bed.pk}")
        self.assertEqual(resp.status_code, 200)
        bed = resp.json()
        self.assertEqual(set(bed.keys()), CANONICAL_BED_KEYS)
        self.assertEqual(bed["bed_id"], "1,1")

    def test_post_bed_returns_contract_b(self):
        resp = self.client.post(
            "/api/beds",
            data=json.dumps(
                {
                    "roomBedId": "2,1",
                    "patientName": "New Patient",
                    "patientSocial": "111222",
                    "diagnosis": "Test Diagnosis",
                    "occupiedDateTime": "2026-09-01T10:00:00",
                    "planedVacate": "2026-09-08T10:00:00",
                    "doneBy": "testuser",
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        bed = resp.json()
        self.assertEqual(set(bed.keys()), CANONICAL_BED_KEYS)
        self.assertEqual(bed["bed_id"], "2,1")

    # --- Task ---

    def test_get_tasks_returns_contract_b(self):
        resp = self.client.get("/api/tasks")
        self.assertEqual(resp.status_code, 200)
        tasks = resp.json()
        self.assertIsInstance(tasks, list)
        self.assertEqual(set(tasks[0].keys()), CANONICAL_TASK_KEYS)
        self.assertIsInstance(tasks[0]["bed"], str)
        self.assertEqual(tasks[0]["bed"], "1,1")

    def test_post_task_returns_contract_b(self):
        resp = self.client.post(
            "/api/tasks",
            data=json.dumps(
                {
                    "bed_id": self.bed.pk,
                    "task": "Nueva tarea",
                    "programed_time": "2026-09-02T15:00:00",
                    "repeat": False,
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        task = resp.json()
        self.assertEqual(set(task.keys()), CANONICAL_TASK_KEYS)
        self.assertIsInstance(task["bed"], str)

    # --- Call ---

    def test_get_calls_returns_contract_b(self):
        resp = self.client.get("/api/calls")
        self.assertEqual(resp.status_code, 200)
        calls = resp.json()
        self.assertIsInstance(calls, list)
        self.assertEqual(set(calls[0].keys()), CANONICAL_CALL_KEYS)
        self.assertIsInstance(calls[0]["bed"], str)

    def test_answer_call_returns_contract_b(self):
        resp = self.client.post(f"/api/calls/{self.call.pk}/answer")
        self.assertEqual(resp.status_code, 200)
        call = resp.json()
        self.assertEqual(set(call.keys()), CANONICAL_CALL_KEYS)
        self.assertIn(call["state"], ("active", "answered", "closed"))


class DeprecationTest(TestCase):
    """Fase F T6.3 — views.py deprecado.

    Contract real de deprecación:
    1. /nursing/rooms se PRESERVA vía ruta directa a modular_views.rooms
       (simulador legacy) → 200.
    2. Ningún endpoint legacy resuelve a un handler de nursing.views.
    3. Los módulos nursing.views y nursing.urls ya NO existen.

    DESVIACIÓN DOCUMENTADA (hallazgo Lote 6, regla de oro #471):
    el design esperaba 404 para /nursing/home, /nursing/occupy_bed, etc. Pero
    el SPA catch-all de healthproject/urls.py (re_path que sirve index.html a
    cualquier path no-API/no-asset) responde 200 a esas URLs. El propio plan de
    archivos del design NO modifica ese catch-all, así que 404 es inalcanzable
    sin un cambio de comportamiento adicional (fuera de scope). Por eso no se
    aserta 404: se congela el contrato REAL — views.py ya no sirve ninguna URL.
    """

    def setUp(self):
        self.client = Client()

    def test_rooms_preserved_direct_route_returns_200(self):
        """/nursing/rooms sigue respondiendo 200 (simulador legacy)."""
        resp = self.client.get("/nursing/rooms")
        self.assertEqual(resp.status_code, 200)

    def test_rooms_resolves_to_modular_views_not_views_py(self):
        """rooms apunta a modular_views.rooms (ruta directa), NO a views.py."""
        from django.urls import resolve
        from nursing.modular_views.rooms import rooms as modular_rooms

        match = resolve("/nursing/rooms")
        self.assertIs(match.func, modular_rooms)

    def test_legacy_endpoints_do_not_resolve_to_views_py(self):
        """Ningún endpoint legacy de views.py queda enrutado a un handler suyo."""
        from django.urls import resolve

        legacy_urls = (
            "/nursing/home",
            "/nursing/initial_load",
            "/nursing/occupy_bed",
            "/nursing/edit_bed",
            "/nursing/vacate_bed",
            "/nursing/answered_call",
            "/nursing/close_call",
            "/nursing/new_task",
            "/nursing/edit_task",
            "/nursing/delete_task",
        )
        for url in legacy_urls:
            func = resolve(url).func
            module = func.__module__
            self.assertNotIn(
                "nursing.views", module, f"{url} resuelve a {module} (views.py vivo)"
            )

    def test_views_and_urls_modules_deleted(self):
        """nursing.views y nursing.urls ya no existen como módulos importables."""
        with self.assertRaises(ImportError):
            importlib.import_module("nursing.views")
        with self.assertRaises(ImportError):
            importlib.import_module("nursing.urls")
