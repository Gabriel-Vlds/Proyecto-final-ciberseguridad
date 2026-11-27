import unittest

import _env
from app import app
from helpers import new_client

PAYLOAD = '<script>document.title="XSS"</script>'


class XssTests(unittest.TestCase):
    def setUp(self):
        self.client = new_client("staff_test", "StaffTest-123")

    def tearDown(self):
        app.config["VULN_XSS"] = False

    def test_vulnerable_mode_reflects_script_and_drops_csp(self):
        app.config["VULN_XSS"] = True
        response = self.client.get("/buscar", query_string={"q": PAYLOAD})
        self.assertIn(PAYLOAD, response.get_data(as_text=True))
        self.assertNotIn("Content-Security-Policy", response.headers)

    def test_fixed_mode_escapes_input_and_keeps_csp(self):
        app.config["VULN_XSS"] = False
        response = self.client.get("/buscar", query_string={"q": PAYLOAD})
        page = response.get_data(as_text=True)
        self.assertNotIn("<script>document", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_fixed_mode_limits_input_to_50_characters(self):
        response = self.client.get("/buscar", query_string={"q": "a" * 80})
        self.assertNotIn("a" * 51, response.get_data(as_text=True))

    def test_suspicious_input_is_logged(self):
        self.client.get("/buscar", query_string={"q": PAYLOAD})
        with open(_env.LOG_FILE, encoding="utf-8") as log:
            self.assertIn("XSS_SOSPECHOSO", log.read())


if __name__ == "__main__":
    unittest.main()
