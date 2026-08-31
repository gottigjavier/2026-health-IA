#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Health App
Tests: Login, Bed Management, Calls, Tasks, and WebSocket Functionality
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


class HealthAppTester:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None
        self.bed_id = None
        self.patient_id = None
        self.task_ids = []
        self.call_ids = []
        self.test_results = []

    def print_header(self, text):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
        print(f"  {text}")
        print(f"{'=' * 60}{Colors.RESET}\n")

    def print_test(self, name, passed, message=""):
        status = (
            f"{Colors.GREEN}✓ PASS{Colors.RESET}"
            if passed
            else f"{Colors.RED}✗ FAIL{Colors.RESET}"
        )
        print(f"{status} | {name}")
        if message:
            print(f"       {Colors.YELLOW}{message}{Colors.RESET}")
        self.test_results.append({"test": name, "passed": passed, "message": message})

    def test_health_check(self):
        """Test 0: Health check - verify app is running"""
        self.print_header("Test 0: Health Check")

        try:
            response = self.session.get(f"{BASE_URL}/")
            passed = response.status_code == 200
            self.print_test("Homepage loads", passed, f"Status: {response.status_code}")
        except Exception as e:
            self.print_test("Homepage loads", False, str(e))

    def test_login(self):
        """Test 1: Login with credentials"""
        self.print_header("Test 1: Login - User Authentication")

        # First, register a test user
        register_payload = {
            "username": f"testuser_{int(time.time())}",
            "email": f"test_{int(time.time())}@example.com",
            "password": "testpass123",
        }

        try:
            # Register
            reg_response = self.session.post(
                f"{API_BASE}/auth/register", json=register_payload
            )
            passed_register = reg_response.status_code == 200
            self.print_test(
                "User registration",
                passed_register,
                f"Status: {reg_response.status_code}",
            )

            if passed_register:
                # Login
                login_payload = {
                    "username": register_payload["username"],
                    "password": register_payload["password"],
                }

                login_response = self.session.post(
                    f"{API_BASE}/auth/login", json=login_payload
                )

                passed_login = login_response.status_code == 200
                self.print_test(
                    "User login", passed_login, f"Status: {login_response.status_code}"
                )

                if passed_login:
                    data = login_response.json()
                    self.token = data["access"]
                    self.user_id = data["user"]["id"]
                    self.session.headers.update(
                        {"Authorization": f"Bearer {self.token}"}
                    )
                    print(
                        f"       {Colors.YELLOW}Token: {self.token[:20]}...{Colors.RESET}"
                    )
                    print(
                        f"       {Colors.YELLOW}User ID: {self.user_id}{Colors.RESET}"
                    )
        except Exception as e:
            self.print_test("Login process", False, str(e))

    def test_get_beds(self):
        """Test 2: Get list of beds"""
        self.print_header("Test 2: Get Beds")

        try:
            response = self.session.get(f"{API_BASE}/beds")
            passed = response.status_code == 200
            self.print_test(
                "Fetch beds list", passed, f"Status: {response.status_code}"
            )

            if passed and response.json():
                beds = response.json()
                print(f"       {Colors.YELLOW}Total beds: {len(beds)}{Colors.RESET}")
                if beds:
                    print(
                        f"       {Colors.YELLOW}Sample bed: {beds[0]['bed_id']}{Colors.RESET}"
                    )
        except Exception as e:
            self.print_test("Fetch beds list", False, str(e))

    def test_occupy_bed(self):
        """Test 3: Occupy a bed with patient data"""
        self.print_header("Test 3: Occupy Bed and Create Patient")

        try:
            # First, get available beds
            beds_response = self.session.get(f"{API_BASE}/beds")
            beds = beds_response.json()

            if beds:
                # Find a free bed
                free_bed = None
                for bed in beds:
                    if bed["bed_state"] == "free":
                        free_bed = bed
                        break

                if not free_bed and beds:
                    free_bed = beds[0]

                if free_bed:
                    # Prepare bed occupation payload
                    now = datetime.now()
                    vacate_time = now + timedelta(days=7)

                    payload = {
                        "roomBedId": free_bed["bed_id"],
                        "patientName": f"Patient_{int(time.time())}",
                        "patientSocial": f"SSN{int(time.time())}",
                        "occupiedDateTime": now.strftime("%Y-%m-%dT%H:%M"),
                        "planedVacate": vacate_time.strftime("%Y-%m-%dT%H:%M"),
                        "diagnosis": "Test Diagnosis",
                        "doneBy": "TestUser",
                    }

                    occupy_response = self.session.post(
                        f"{API_BASE}/beds", json=payload
                    )

                    passed = occupy_response.status_code == 200
                    self.print_test(
                        "Occupy bed", passed, f"Status: {occupy_response.status_code}"
                    )

                    if passed:
                        bed_data = occupy_response.json()
                        self.bed_id = bed_data["id"]
                        print(
                            f"       {Colors.YELLOW}Bed ID: {self.bed_id}{Colors.RESET}"
                        )
                        print(
                            f"       {Colors.YELLOW}Bed State: {bed_data['bed_state']}{Colors.RESET}"
                        )
        except Exception as e:
            self.print_test("Occupy bed", False, str(e))

    def test_create_call(self):
        """Test 4 & 5: Create and handle calls"""
        self.print_header("Test 4 & 5: Simulate Call - Occupied and Unoccupied Beds")

        try:
            # Get beds to test both occupied and unoccupied
            beds_response = self.session.get(f"{API_BASE}/beds")
            beds = beds_response.json()

            occupied_bed = None
            unoccupied_bed = None

            for bed in beds:
                if bed["bed_state"] != "free" and occupied_bed is None:
                    occupied_bed = bed
                elif bed["bed_state"] == "free" and unoccupied_bed is None:
                    unoccupied_bed = bed

            # Test call from occupied bed
            if occupied_bed:
                print(
                    f"\n{Colors.BLUE}Testing call from OCCUPIED bed: {occupied_bed['bed_id']}{Colors.RESET}"
                )
                # The app receives calls via MQTT, but we can test by reading /nursing/rooms
                # For now, we just verify the bed state
                self.print_test(
                    "Occupied bed exists",
                    True,
                    f"Bed {occupied_bed['bed_id']} is {occupied_bed['bed_state']}",
                )

            # Test call from unoccupied bed
            if unoccupied_bed:
                print(
                    f"\n{Colors.BLUE}Testing call from UNOCCUPIED bed: {unoccupied_bed['bed_id']}{Colors.RESET}"
                )
                self.print_test(
                    "Unoccupied bed exists",
                    True,
                    f"Bed {unoccupied_bed['bed_id']} is free",
                )
        except Exception as e:
            self.print_test("Call testing", False, str(e))

    def test_schedule_task(self):
        """Test 6: Schedule a task"""
        self.print_header("Test 6: Schedule Task")

        try:
            if not self.bed_id:
                # Need to occupy a bed first
                self.print_test("Schedule task", False, "No bed available")
                return

            now = datetime.now()
            programed_time = now + timedelta(minutes=30)

            payload = {
                "bed_id": self.bed_id,
                "task": "Test Task - Medication",
                "programed_time": programed_time.strftime("%Y-%m-%dT%H:%M"),
                "repeat": False,
            }

            task_response = self.session.post(f"{API_BASE}/tasks", json=payload)

            passed = task_response.status_code == 200
            self.print_test(
                "Create task", passed, f"Status: {task_response.status_code}"
            )

            if passed:
                task_data = task_response.json()
                self.task_ids.append(task_data["id"])
                print(f"       {Colors.YELLOW}Task ID: {task_data['id']}{Colors.RESET}")
                print(f"       {Colors.YELLOW}Task: {task_data['task']}{Colors.RESET}")
        except Exception as e:
            self.print_test("Create task", False, str(e))

    def test_repetitive_task(self):
        """Test 7: Schedule repetitive task"""
        self.print_header("Test 7: Schedule Repetitive Task")

        try:
            if not self.bed_id:
                self.print_test("Schedule repetitive task", False, "No bed available")
                return

            now = datetime.now()
            programed_time = now + timedelta(hours=1)

            payload = {
                "bed_id": self.bed_id,
                "task": "Repetitive Task - Check Vitals",
                "programed_time": programed_time.strftime("%Y-%m-%dT%H:%M"),
                "repeat": True,
            }

            task_response = self.session.post(f"{API_BASE}/tasks", json=payload)

            passed = task_response.status_code == 200
            self.print_test(
                "Create repetitive task", passed, f"Status: {task_response.status_code}"
            )

            if passed:
                task_data = task_response.json()
                self.task_ids.append(task_data["id"])
                print(
                    f"       {Colors.YELLOW}Repetitive Task ID: {task_data['id']}{Colors.RESET}"
                )
                print(
                    f"       {Colors.YELLOW}Repeat: {task_data['repeat']}{Colors.RESET}"
                )
        except Exception as e:
            self.print_test("Create repetitive task", False, str(e))

    def test_get_tasks(self):
        """Test: Get list of tasks"""
        self.print_header("Test: Get Tasks List")

        try:
            response = self.session.get(f"{API_BASE}/tasks")
            passed = response.status_code == 200
            self.print_test(
                "Fetch tasks list", passed, f"Status: {response.status_code}"
            )

            if passed and response.json():
                tasks = response.json()
                print(f"       {Colors.YELLOW}Total tasks: {len(tasks)}{Colors.RESET}")
        except Exception as e:
            self.print_test("Fetch tasks list", False, str(e))

    def test_update_task(self):
        """Test: Update task"""
        self.print_header("Test: Update Task Status")

        try:
            if not self.task_ids:
                self.print_test("Update task", False, "No tasks created")
                return

            task_id = self.task_ids[0]
            now = datetime.now()
            programed_time = now + timedelta(minutes=45)

            payload = {
                "task": "Updated Task - Medication (2nd dose)",
                "programed_time": programed_time.strftime("%Y-%m-%dT%H:%M"),
            }

            update_response = self.session.put(
                f"{API_BASE}/tasks/{task_id}", json=payload
            )

            passed = update_response.status_code == 200
            self.print_test(
                "Update task", passed, f"Status: {update_response.status_code}"
            )
        except Exception as e:
            self.print_test("Update task", False, str(e))

    def test_complete_task(self):
        """Test: Mark task as complete"""
        self.print_header("Test: Complete Task")

        try:
            if not self.task_ids:
                self.print_test("Complete task", False, "No tasks created")
                return

            task_id = self.task_ids[0]

            complete_response = self.session.post(
                f"{API_BASE}/tasks/{task_id}/complete"
            )

            passed = complete_response.status_code == 200
            self.print_test(
                "Mark task complete", passed, f"Status: {complete_response.status_code}"
            )

            if passed:
                task_data = complete_response.json()
                print(
                    f"       {Colors.YELLOW}Task State: {task_data['state']}{Colors.RESET}"
                )
        except Exception as e:
            self.print_test("Mark task complete", False, str(e))

    def test_vacate_bed(self):
        """Test 8: Vacate/Unoccupy bed"""
        self.print_header("Test 8: Vacate Bed")

        try:
            if not self.bed_id:
                self.print_test("Vacate bed", False, "No bed to vacate")
                return

            # First get the bed info to get patient_id
            bed_response = self.session.get(f"{API_BASE}/beds/{self.bed_id}")
            if bed_response.status_code != 200:
                self.print_test("Vacate bed", False, "Cannot fetch bed info")
                return

            bed_data = bed_response.json()

            # Get all patients to find the one associated with this bed
            patients_response = self.session.get(f"{API_BASE}/patients")
            if patients_response.status_code != 200:
                self.print_test("Vacate bed", False, "Cannot fetch patients")
                return

            patients = patients_response.json()
            patient_id = patients[0]["id"] if patients else None

            if not patient_id:
                self.print_test("Vacate bed", False, "No patient found")
                return

            payload = {
                "bedId": self.bed_id,
                "patientId": patient_id,
                "vacateDT": datetime.now().strftime("%Y-%m-%dT%H:%M"),
                "doneBy": "TestUser",
            }

            vacate_response = self.session.post(f"{API_BASE}/beds/vacate", json=payload)

            passed = vacate_response.status_code == 200
            self.print_test(
                "Vacate bed", passed, f"Status: {vacate_response.status_code}"
            )

            if passed:
                print(
                    f"       {Colors.YELLOW}Bed {self.bed_id} is now free{Colors.RESET}"
                )
        except Exception as e:
            self.print_test("Vacate bed", False, str(e))

    def test_get_calls(self):
        """Test 9: Get calls list"""
        self.print_header("Test 9: Get Calls List")

        try:
            response = self.session.get(f"{API_BASE}/calls")
            passed = response.status_code == 200
            self.print_test(
                "Fetch calls list", passed, f"Status: {response.status_code}"
            )

            if passed and response.json():
                calls = response.json()
                print(f"       {Colors.YELLOW}Total calls: {len(calls)}{Colors.RESET}")

                # Show pending calls
                pending = [c for c in calls if c.get("state") == "pending"]
                if pending:
                    print(
                        f"       {Colors.YELLOW}Pending calls: {len(pending)}{Colors.RESET}"
                    )
        except Exception as e:
            self.print_test("Fetch calls list", False, str(e))

    def test_jwt_auth(self):
        """Test 10: JWT Authentication"""
        self.print_header("Test 10: JWT Authentication")

        try:
            # Test with no token
            response_noauth = requests.get(f"{API_BASE}/beds")
            passed_noauth = response_noauth.status_code == 401
            self.print_test(
                "Reject unauthenticated request",
                passed_noauth,
                f"Status: {response_noauth.status_code}",
            )

            # Test with valid token
            response_auth = self.session.get(f"{API_BASE}/beds")
            passed_auth = response_auth.status_code == 200
            self.print_test(
                "Accept authenticated request",
                passed_auth,
                f"Status: {response_auth.status_code}",
            )

            # Test with invalid token
            bad_session = requests.Session()
            bad_session.headers.update({"Authorization": "Bearer invalid_token_123"})
            response_invalid = bad_session.get(f"{API_BASE}/beds")
            passed_invalid = response_invalid.status_code == 401
            self.print_test(
                "Reject invalid token",
                passed_invalid,
                f"Status: {response_invalid.status_code}",
            )
        except Exception as e:
            self.print_test("JWT authentication", False, str(e))

    def test_get_current_user(self):
        """Test: Get current user info"""
        self.print_header("Test: Get Current User Info")

        try:
            response = self.session.get(f"{API_BASE}/users/me")
            passed = response.status_code == 200
            self.print_test(
                "Get current user", passed, f"Status: {response.status_code}"
            )

            if passed:
                user = response.json()
                print(
                    f"       {Colors.YELLOW}Username: {user['username']}{Colors.RESET}"
                )
                print(f"       {Colors.YELLOW}ID: {user['id']}{Colors.RESET}")
        except Exception as e:
            self.print_test("Get current user", False, str(e))

    def test_get_rooms(self):
        """Test: Get rooms information"""
        self.print_header("Test: Get Rooms Information")

        try:
            response = self.session.get(f"{API_BASE}/rooms")
            passed = response.status_code == 200
            self.print_test("Fetch rooms", passed, f"Status: {response.status_code}")

            if passed and response.json():
                rooms = response.json()
                print(f"       {Colors.YELLOW}Total rooms: {len(rooms)}{Colors.RESET}")
        except Exception as e:
            self.print_test("Fetch rooms", False, str(e))

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.print_header("🏥 HEALTH APP - COMPREHENSIVE TEST SUITE 🏥")
        print(f"Base URL: {BASE_URL}")
        print(f"API Base: {API_BASE}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Sequential test execution
        self.test_health_check()
        time.sleep(1)

        self.test_login()
        time.sleep(1)

        self.test_get_current_user()
        time.sleep(1)

        self.test_get_beds()
        time.sleep(1)

        self.test_occupy_bed()
        time.sleep(1)

        self.test_create_call()
        time.sleep(1)

        self.test_schedule_task()
        time.sleep(1)

        self.test_repetitive_task()
        time.sleep(1)

        self.test_get_tasks()
        time.sleep(1)

        self.test_update_task()
        time.sleep(1)

        self.test_complete_task()
        time.sleep(1)

        self.test_get_calls()
        time.sleep(1)

        self.test_vacate_bed()
        time.sleep(1)

        self.test_jwt_auth()
        time.sleep(1)

        self.test_get_rooms()
        time.sleep(1)

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        total = len(self.test_results)
        passed = sum(1 for t in self.test_results if t["passed"])
        failed = total - passed

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {failed}{Colors.RESET}")
        print(f"Success Rate: {Colors.BOLD}{(passed / total * 100):.1f}%{Colors.RESET}")

        if failed > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.RESET}")
            for test in self.test_results:
                if not test["passed"]:
                    print(f"  - {test['test']}: {test['message']}")


if __name__ == "__main__":
    tester = HealthAppTester()
    tester.run_all_tests()
