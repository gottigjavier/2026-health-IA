from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from health.nursing.models import Event, Bed, Patient, Task, Call
from health.nursing.choices import BedState, CallState, TaskState
from health.nursing.modular_views.data_analytics import save_event


User = get_user_model()


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
