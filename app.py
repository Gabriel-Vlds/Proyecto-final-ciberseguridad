import hmac
import logging
from logging.handlers import RotatingFileHandler
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

Path("logs").mkdir(exist_ok=True)
_handler = RotatingFileHandler("logs/seguridad.log", maxBytes=100_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
security_log = logging.getLogger("seguridad")
security_log.setLevel(logging.INFO)
security_log.addHandler(_handler)

required_settings = ("SECRET_KEY", "DEMO_USERNAME", "DEMO_PASSWORD")
missing_settings = [name for name in required_settings if not os.environ.get(name)]
if missing_settings:
    raise RuntimeError(
        f"Faltan variables de entorno: {', '.join(missing_settings)}. "
        "Configuralas en el archivo .env local."
    )

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

DEMO_USERNAME = os.environ["DEMO_USERNAME"]
DEMO_PASSWORD = os.environ["DEMO_PASSWORD"]
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).with_name("clinica.db")))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_db()
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    connection.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """,
        (DEMO_USERNAME, generate_password_hash(DEMO_PASSWORD), "Equipo de diagnóstico Norte", "staff"),
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """,
        ("laboratorio", generate_password_hash("LaboratorioNorte!2026"), "Dra. Laura Mendez", "staff"),
    )

    patients = (
        (1, "PAC-001", "Mariana Torres", "1988-03-14", "Hemograma completo"),
        (2, "PAC-002", "Carlos Vega", "1975-09-27", "Perfil metabólico"),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO patients
            (id, patient_code, full_name, birth_date, study)
        VALUES (?, ?, ?, ?, ?)
        """,
        patients,
    )

    results = (
        (1, 1, "2026-11-20", "R1-R6", "Finalizado", "Sin hallazgos críticos. Resultados dentro de rangos de referencia."),
        (2, 2, "2026-11-22", "R2-R6", "Finalizado", "Glucosa elevada. Se recomienda control médico y seguimiento."),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO results
            (id, patient_id, result_date, findings_code, status, summary)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        results,
    )
    connection.commit()
    connection.close()


init_database()


def create_csrf_token():
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    return token


def require_login(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            security_log.warning("ACCESO_SIN_SESION ip=%s ruta=%s", request.remote_addr, request.path)
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.before_request
def enforce_csrf():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected, supplied):
            security_log.warning("CSRF_INVALIDO ip=%s ruta=%s", request.remote_addr, request.path)
            abort(400, description="Token CSRF invalido o ausente.")


@app.after_request
def add_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; style-src 'self'; img-src 'self' data:; "
        "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.get("/")
def index():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        connection = get_db()
        user = connection.execute(
            "SELECT id, username, password_hash, full_name, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        connection.close()
        if user and hmac.compare_digest(username, user["username"]) and check_password_hash(
            user["password_hash"], password
        ):
            security_log.info("LOGIN_OK usuario=%r ip=%s", username, request.remote_addr)
            session.clear()
            session["authenticated"] = True
            session["user_id"] = user["id"]
            session["customer_name"] = user["full_name"]
            create_csrf_token()
            return redirect(url_for("dashboard"))
        security_log.warning("LOGIN_FALLIDO usuario=%r ip=%s", username[:50], request.remote_addr)
        error = "Usuario o contrasena incorrectos."

    csrf_token = session.get("csrf_token") or create_csrf_token()
    return render_template("login.html", error=error, csrf_token=csrf_token)


@app.get("/dashboard")
@require_login
def dashboard():
    connection = get_db()
    patients = connection.execute(
        """
        SELECT p.id, p.patient_code, p.full_name, p.birth_date, p.study,
               r.id AS result_id, r.result_date, r.findings_code, r.status
        FROM patients p
        LEFT JOIN results r ON r.patient_id = p.id
        ORDER BY p.id
        """
    ).fetchall()
    connection.close()
    return render_template(
        "dashboard.html",
        customer_name=session["customer_name"],
        patients=[dict(patient) for patient in patients],
        csrf_token=session["csrf_token"],
    )


@app.get("/buscar")
@require_login
def buscar():
    q = request.args.get("q", "").strip()[:50]
    if "<" in q or ">" in q:
        security_log.warning("XSS_SOSPECHOSO ip=%s q=%r", request.remote_addr, q)
    connection = get_db()
    rows = connection.execute(
        "SELECT patient_code, full_name FROM patients WHERE full_name LIKE ?",
        (f"%{q}%",),
    ).fetchall()
    connection.close()
    # DESPUES: Jinja escapa {{ q }} y el CSP vuelve a aplicar
    return render_template("buscar.html", q=q, rows=rows)


@app.post("/logout")
@require_login
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="portal-clinica-diagnostica-norte")


@app.get("/api/resultados")
@require_login
def results():
    connection = get_db()
    rows = connection.execute(
        """
        SELECT r.id, r.patient_id, p.patient_code, p.full_name AS patient_name,
               r.result_date, r.findings_code, r.status, r.summary
        FROM results r
        JOIN patients p ON p.id = r.patient_id
        ORDER BY r.id
        """
    ).fetchall()
    connection.close()
    return jsonify(resultados=[dict(row) for row in rows])


@app.get("/api/resultados/<int:result_id>")
@require_login
def result_detail(result_id):
    connection = get_db()
    row = connection.execute(
        """
        SELECT r.id, r.patient_id, p.patient_code, p.full_name AS patient_name,
               r.result_date, r.findings_code, r.status, r.summary
        FROM results r
        JOIN patients p ON p.id = r.patient_id
        WHERE r.id = ?
        """,
        (result_id,),
    ).fetchone()
    connection.close()
    if row is None:
        abort(404)
    return jsonify(dict(row))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
