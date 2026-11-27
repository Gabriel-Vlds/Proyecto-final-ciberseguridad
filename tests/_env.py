"""Valores ficticios solo para las pruebas: no tocan tu .env ni tu base de datos real."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="clinica_tests_")
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["DEMO_USERNAME"] = "staff_test"
os.environ["DEMO_PASSWORD"] = "StaffTest-123"
os.environ["PATIENT_PASSWORD"] = "PatientTest-123"
os.environ["DATABASE_PATH"] = os.path.join(_tmp, "test.db")
os.environ["LOG_DIR"] = os.path.join(_tmp, "logs")
for name in ("VULN_SQLI", "VULN_XSS", "VULN_IDOR"):
    os.environ[name] = "0"
LOG_FILE = os.path.join(_tmp, "logs", "seguridad.log")
