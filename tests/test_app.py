import unittest

import _env
from app import app
from helpers import login, new_client


class PortalBasicTests(unittest.TestCase):
    def setUp(self):
        for name in ("VULN_SQLI", "VULN_XSS", "VULN_IDOR"):
            app.config[name] = False

    def test_health_and_security_headers(self):
        response = new_client().get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_login_page_does_not_show_credentials(self):
        page = new_client().get("/login").get_data(as_text=True)
        self.assertNotIn("StaffTest-123", page)

    def test_staff_login_dashboard_and_logout(self):
        client = new_client()
        self.assertEqual(client.get("/dashboard").status_code, 302)
        self.assertEqual(login(client, "staff_test", "StaffTest-123").status_code, 302)
        dashboard = client.get("/dashboard").get_data(as_text=True)
        self.assertIn("Mariana Torres", dashboard)
        self.assertIn("Carlos Vega", dashboard)
        self.assertEqual(len(client.get("/api/resultados").json["resultados"]), 2)
        with client.session_transaction() as session:
            token = session["csrf_token"]
        self.assertEqual(client.post("/logout", data={"csrf_token": token}).status_code, 302)
        self.assertEqual(client.get("/api/resultados").status_code, 302)

    def test_post_without_csrf_token_is_rejected(self):
        response = new_client().post("/login", data={"username": "x", "password": "y"})
        self.assertEqual(response.status_code, 400)

    def test_invalid_credentials_do_not_authenticate(self):
        client = new_client()
        response = login(client, "staff_test", "incorrecta")
        self.assertEqual(response.status_code, 200)
        self.assertIn("incorrectos", response.get_data(as_text=True))
        self.assertEqual(client.get("/api/resultados").status_code, 302)


if __name__ == "__main__":
    unittest.main()
