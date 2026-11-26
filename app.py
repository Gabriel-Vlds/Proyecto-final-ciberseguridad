import hmac
import os
import secrets
from functools import wraps

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, redirect, render_template, request, session, url_for

load_dotenv()

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

ACCOUNTS = [
    {
        "type": "Cuenta de cheques",
        "number": "•••• •••• •••• 4821",
        "balance": 8420.65,
        "currency": "USD",
    },
    {
        "type": "Cuenta de ahorros",
        "number": "•••• •••• •••• 9073",
        "balance": 15350.20,
        "currency": "USD",
    },
]

TRANSACTIONS = [
    {"date": "2026-04-18", "description": "Supermercado Central", "amount": -68.42},
    {"date": "2026-04-16", "description": "Deposito de nomina", "amount": 2450.00},
    {"date": "2026-04-14", "description": "Cafe del Parque", "amount": -12.80},
]


def create_csrf_token():
    token = secrets.token_urlsafe(32)
    session["csrf_token"] = token
    return token


def require_login(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.before_request
def enforce_csrf():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        supplied = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected, supplied):
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
        if hmac.compare_digest(username, DEMO_USERNAME) and hmac.compare_digest(
            password, DEMO_PASSWORD
        ):
            session.clear()
            session["authenticated"] = True
            session["customer_name"] = "Alex Rivera (cliente ficticio)"
            create_csrf_token()
            return redirect(url_for("dashboard"))
        error = "Usuario o contrasena incorrectos."

    csrf_token = session.get("csrf_token") or create_csrf_token()
    return render_template("login.html", error=error, csrf_token=csrf_token)


@app.get("/dashboard")
@require_login
def dashboard():
    return render_template(
        "dashboard.html",
        customer_name=session["customer_name"],
        accounts=ACCOUNTS,
        transactions=TRANSACTIONS,
        csrf_token=session["csrf_token"],
    )


@app.post("/logout")
@require_login
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/api/health")
def health():
    return jsonify(status="ok", service="demo-bank")


@app.get("/api/accounts")
@require_login
def accounts():
    return jsonify(accounts=ACCOUNTS)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
