"""Portal de resultados de la Clinica Diagnostica Norte (laboratorio educativo).

Tres vulnerabilidades se pueden activar a proposito con variables de entorno, solo para
demostrarlas en el laboratorio local y compararlas con la version corregida:
  VULN_SQLI=1  -> /api/pacientes concatena la entrada en la consulta SQL
  VULN_XSS=1   -> /buscar inserta la entrada en el HTML sin escapar y sin CSP
  VULN_IDOR=1  -> /api/resultados no verifica de quien es el resultado
Con los tres en 0 (valor por defecto) la aplicacion es la version corregida.
"""
import hmac
import logging
import os
import secrets
import sqlite3
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

required_settings = ("SECRET_KEY", "DEMO_USERNAME", "DEMO_PASSWORD", "PATIENT_PASSWORD")
missing_settings = [name for name in required_settings if not os.environ.get(name)]
if missing_settings:
    raise RuntimeError(
        f"Faltan variables de entorno: {', '.join(missing_settings)}. "
        "Configuralas en el archivo .env local (ver .env.example)."
    )


def flag(name):
    return os.environ.get(name, "0") == "1"


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SECRET_KEY"],
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    VULN_SQLI=flag("VULN_SQLI"),
    VULN_XSS=flag("VULN_XSS"),
    VULN_IDOR=flag("VULN_IDOR"),
)

DEMO_USERNAME = os.environ["DEMO_USERNAME"]
DEMO_PASSWORD = os.environ["DEMO_PASSWORD"]
PATIENT_PASSWORD = os.environ["PATIENT_PASSWORD"]
DATABASE_PATH = Path(os.environ.get("DATABASE_PATH", Path(__file__).with_name("clinica.db")))
SCHEMA_PATH = Path(__file__).with_name("schema.sql")

# Registro de seguridad (no guarda contrasenas)
LOG_DIR = Path(os.environ.get("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
_handler = RotatingFileHandler(LOG_DIR / "seguridad.log", maxBytes=100_000, backupCount=3, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
security_log = logging.getLogger("seguridad")
security_log.setLevel(logging.INFO)
if not security_log.handlers:
    security_log.addHandler(_handler)


def get_db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = get_db()
    connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    users = (
        (DEMO_USERNAME, DEMO_PASSWORD, "Equipo de diagnóstico Norte", "staff"),
        ("mariana", PATIENT_PASSWORD, "Mariana Torres", "patient"),
        ("carlos", PATIENT_PASSWORD, "Carlos Vega", "patient"),
    )
    for username, password, full_name, role in users:
        connection.execute(
            "INSERT OR IGNORE INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), full_name, role),
        )

    def user_id(username):
        return connection.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]

    patients = (
        (1, "PAC-001", "Mariana Torres", "1988-03-14", "Hemograma completo", user_id("mariana")),
        (2, "PAC-002", "Carlos Vega", "1975-09-27", "Perfil metabólico", user_id("carlos")),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO patients (id, patient_code, full_name, birth_date, study, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        patients,
    )

    results = (
        (1, 1, "2026-11-20", "R1-R6", "Finalizado", "Sin hallazgos críticos. Resultados dentro de rangos de referencia."),
        (2, 2, "2026-11-22", "R2-R6", "Finalizado", "Glucosa elevada. Se recomienda control médico y seguimiento."),
    )
    connection.executemany(
        """
        INSERT OR IGNORE INTO results (id, patient_id, result_date, findings_code, status, summary)
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


def is_patient():
    return session.get("role") == "patient"


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
    # VULN_XSS=1 reproduce el defecto original: /buscar sin Content-Security-Policy
    if not (app.config["VULN_XSS"] and request.endpoint == "buscar"):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self'; img-src 'self' data:; "
            "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
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
            session.clear()
            session["authenticated"] = True
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["customer_name"] = user["full_name"]
            create_csrf_token()
            security_log.info("LOGIN_OK usuario=%r ip=%s", username, request.remote_addr)
            return redirect(url_for("dashboard"))
        security_log.warning("LOGIN_FALLIDO usuario=%r ip=%s", username[:50], request.remote_addr)
        error = "Usuario o contrasena incorrectos."

    csrf_token = session.get("csrf_token") or create_csrf_token()
    return render_template("login.html", error=error, csrf_token=csrf_token)


@app.get("/dashboard")
@require_login
def dashboard():
    sql = """
        SELECT p.id, p.patient_code, p.full_name, p.birth_date, p.study,
               r.id AS result_id, r.result_date, r.findings_code, r.status
        FROM patients p
        LEFT JOIN results r ON r.patient_id = p.id
    """
    params = ()
    if is_patient():  # la interfaz solo muestra lo propio
        sql += " WHERE p.user_id = ?"
        params = (session["user_id"],)
    connection = get_db()
    patients = connection.execute(sql + " ORDER BY p.id", params).fetchall()
    connection.close()
    return render_template(
        "dashboard.html",
        customer_name=session["customer_name"],
        patients=[dict(patient) for patient in patients],
        csrf_token=session["csrf_token"],
    )


@app.post("/logout")
@require_login
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="portal-clinica-diagnostica-norte")


# ---------------------------------------------------------------- IDOR / BOLA
RESULT_SELECT = """
    SELECT r.id, r.patient_id, p.patient_code, p.full_name AS patient_name,
           p.user_id AS owner_id, r.result_date, r.findings_code, r.status, r.summary
    FROM results r
    JOIN patients p ON p.id = r.patient_id
"""


def public_result(row):
    data = dict(row)
    data.pop("owner_id")
    return data


@app.get("/api/resultados")
@require_login
def results():
    connection = get_db()
    rows = connection.execute(RESULT_SELECT + " ORDER BY r.id").fetchall()
    connection.close()
    if not app.config["VULN_IDOR"] and is_patient():
        rows = [row for row in rows if row["owner_id"] == session["user_id"]]
    return jsonify(resultados=[public_result(row) for row in rows])


@app.get("/api/resultados/<int:result_id>")
@require_login
def result_detail(result_id):
    connection = get_db()
    row = connection.execute(RESULT_SELECT + " WHERE r.id = ?", (result_id,)).fetchone()
    connection.close()
    if row is None:
        abort(404)
    # CORRECCION: autorizacion a nivel de objeto (el servidor no confia en el ID que manda el usuario)
    if not app.config["VULN_IDOR"] and is_patient() and row["owner_id"] != session["user_id"]:
        security_log.warning(
            "IDOR_BLOQUEADO usuario_id=%s rol=%s recurso=/api/resultados/%s ip=%s",
            session.get("user_id"), session.get("role"), result_id, request.remote_addr,
        )
        abort(403)
    return jsonify(public_result(row))


# ---------------------------------------------------------------- XSS reflejado
@app.get("/buscar")
@require_login
def buscar():
    raw_q = request.args.get("q", "")
    q = raw_q.strip() if app.config["VULN_XSS"] else raw_q.strip()[:50]
    if "<" in q or ">" in q:
        security_log.warning("XSS_SOSPECHOSO ip=%s q=%r", request.remote_addr, q)
    connection = get_db()
    rows = connection.execute(
        "SELECT patient_code, full_name FROM patients WHERE full_name LIKE ?",
        (f"%{q}%",),
    ).fetchall()
    connection.close()
    if app.config["VULN_XSS"]:
        # VULNERABLE: q se inserta tal cual en el HTML
        items = "".join(f"<li>{r['patient_code']} - {r['full_name']}</li>" for r in rows)
        return make_response(f"<h1>Resultados para: {q}</h1><ul>{items}</ul>")
    # CORREGIDO: Jinja escapa {{ q }}, se limita la entrada y el CSP vuelve a aplicar
    return render_template("buscar.html", q=q, rows=rows)


# ---------------------------------------------------------------- SQL Injection
@app.get("/api/pacientes")
@require_login
def pacientes():
    codigo = request.args.get("codigo", "")
    if any(mark in codigo for mark in ("'", "--", ";", "/*")):
        security_log.warning("SQLI_SOSPECHOSO ip=%s codigo=%r", request.remote_addr, codigo[:80])
    connection = get_db()
    try:
        if app.config["VULN_SQLI"]:
            # VULNERABLE: la entrada se concatena en la consulta
            query = (
                "SELECT patient_code, full_name, study FROM patients "
                f"WHERE patient_code = '{codigo}'"
            )
            rows = connection.execute(query).fetchall()
        else:
            # CORREGIDO: consulta parametrizada, la entrada nunca se interpreta como SQL
            rows = connection.execute(
                "SELECT patient_code, full_name, study FROM patients WHERE patient_code = ?",
                (codigo,),
            ).fetchall()
    except sqlite3.Error as error:
        connection.close()
        return jsonify(error=str(error)), 500
    connection.close()
    return jsonify(pacientes=[dict(row) for row in rows])


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
