import unittest

import _env
from app import app
from helpers import new_client

INJECTION = "' OR '1'='1"
UNION = "' UNION SELECT username, password_hash, role FROM users --"


class SqlInjectionTests(unittest.TestCase):
    def setUp(self):
        self.client = new_client("mariana", "PatientTest-123")

    def tearDown(self):
        app.config["VULN_SQLI"] = False

    def test_normal_lookup_works_in_both_modes(self):
        for mode in (True, False):
            app.config["VULN_SQLI"] = mode
            rows = self.client.get("/api/pacientes", query_string={"codigo": "PAC-001"}).json["pacientes"]
            self.assertEqual([r["full_name"] for r in rows], ["Mariana Torres"])

    def test_vulnerable_mode_returns_every_patient(self):
        app.config["VULN_SQLI"] = True
        rows = self.client.get("/api/pacientes", query_string={"codigo": INJECTION}).json["pacientes"]
        self.assertEqual(len(rows), 2)

    def test_vulnerable_mode_can_leak_the_users_table(self):
        app.config["VULN_SQLI"] = True
        rows = self.client.get("/api/pacientes", query_string={"codigo": UNION}).json["pacientes"]
        self.assertTrue(any(r["full_name"].startswith(("scrypt", "pbkdf2")) for r in rows))

    def test_fixed_mode_treats_the_input_as_plain_text(self):
        app.config["VULN_SQLI"] = False
        for payload in (INJECTION, UNION):
            rows = self.client.get("/api/pacientes", query_string={"codigo": payload}).json["pacientes"]
            self.assertEqual(rows, [])

    def test_suspicious_input_is_logged(self):
        self.client.get("/api/pacientes", query_string={"codigo": INJECTION})
        with open(_env.LOG_FILE, encoding="utf-8") as log:
            self.assertIn("SQLI_SOSPECHOSO", log.read())


if __name__ == "__main__":
    unittest.main()
