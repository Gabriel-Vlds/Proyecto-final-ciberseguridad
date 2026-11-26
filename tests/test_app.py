import unittest

from app import app, DEMO_PASSWORD, DEMO_USERNAME


class ClinicPortalTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def csrf_token(self):
        response = self.client.get("/login")
        return response.get_data(as_text=True).split('name="csrf_token" value="')[1].split('"')[0]

    def test_health_endpoint_and_security_headers(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")

    def test_login_page_does_not_show_configured_credentials(self):
        response = self.client.get("/login")
        page = response.get_data(as_text=True)
        self.assertNotIn("Usuario de prueba:", page)
        self.assertNotIn(DEMO_PASSWORD, page)

    def test_login_dashboard_api_and_logout(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        token = self.csrf_token()
        response = self.client.post(
            "/login",
            data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD, "csrf_token": token},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/dashboard").status_code, 200)
        self.assertIn("Mariana Torres", self.client.get("/dashboard").get_data(as_text=True))
        self.assertIn("Carlos Vega", self.client.get("/dashboard").get_data(as_text=True))
        self.assertEqual(len(self.client.get("/api/resultados").json["resultados"]), 2)
        self.assertEqual(self.client.get("/api/resultados/1").json["patient_name"], "Mariana Torres")
        with self.client.session_transaction() as session:
            token = session["csrf_token"]
        response = self.client.post("/logout", data={"csrf_token": token})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get("/api/resultados").status_code, 302)

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post("/login", data={"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
        self.assertEqual(response.status_code, 400)

    def test_invalid_credentials_do_not_authenticate(self):
        token = self.csrf_token()
        response = self.client.post(
            "/login",
            data={"username": DEMO_USERNAME, "password": "incorrecta", "csrf_token": token},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("incorrectos", response.get_data(as_text=True))
        self.assertEqual(self.client.get("/api/resultados").status_code, 302)


if __name__ == "__main__":
    unittest.main()
