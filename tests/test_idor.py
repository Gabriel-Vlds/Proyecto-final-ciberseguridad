import unittest

import _env
from app import app
from helpers import new_client


class IdorTests(unittest.TestCase):
    def setUp(self):
        self.mariana = new_client("mariana", "PatientTest-123")

    def tearDown(self):
        app.config["VULN_IDOR"] = False

    def test_vulnerable_mode_lets_a_patient_read_another_patients_result(self):
        app.config["VULN_IDOR"] = True
        response = self.mariana.get("/api/resultados/2")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["patient_name"], "Carlos Vega")

    def test_fixed_mode_blocks_other_patients_result_and_logs_it(self):
        app.config["VULN_IDOR"] = False
        self.assertEqual(self.mariana.get("/api/resultados/2").status_code, 403)
        with open(_env.LOG_FILE, encoding="utf-8") as log:
            self.assertIn("IDOR_BLOQUEADO", log.read())

    def test_fixed_mode_still_shows_own_result(self):
        app.config["VULN_IDOR"] = False
        response = self.mariana.get("/api/resultados/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["patient_name"], "Mariana Torres")

    def test_fixed_mode_filters_the_list_for_patients_but_not_for_staff(self):
        app.config["VULN_IDOR"] = False
        self.assertEqual(len(self.mariana.get("/api/resultados").json["resultados"]), 1)
        staff = new_client("staff_test", "StaffTest-123")
        self.assertEqual(len(staff.get("/api/resultados").json["resultados"]), 2)
        self.assertEqual(staff.get("/api/resultados/2").status_code, 200)


if __name__ == "__main__":
    unittest.main()
