"""Genera eventos de seguridad controlados contra la app LOCAL (127.0.0.1:5000).
Uso: con la app corriendo en otra terminal:  python generar_eventos.py
Despues revisa logs/seguridad.log
"""
import http.cookiejar
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv

load_dotenv()
BASE = "http://127.0.0.1:5000"


def nuevo_cliente():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def pedir(op, ruta, datos=None):
    body = urllib.parse.urlencode(datos).encode() if datos is not None else None
    try:
        r = op.open(urllib.request.Request(BASE + ruta, data=body), timeout=5)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, ""


def token(op):
    _, html = pedir(op, "/login")
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def login(op, usuario, clave):
    return pedir(op, "/login", {"username": usuario, "password": clave, "csrf_token": token(op)})[0]


staff = nuevo_cliente()
print("1. Acceso a /dashboard sin sesion:", pedir(staff, "/dashboard")[0])
print("2. POST sin token CSRF:", pedir(staff, "/login", {"username": "x", "password": "y"})[0])
print("3. Login con contrasena incorrecta:", login(staff, os.environ["DEMO_USERNAME"], "incorrecta"))
print("4. Login correcto:", login(staff, os.environ["DEMO_USERNAME"], os.environ["DEMO_PASSWORD"]))
print("5. Busqueda con <script>:", pedir(staff, "/buscar?q=" + urllib.parse.quote('<script>document.title="XSS"</script>'))[0])
print("6. Entrada con comilla en /api/pacientes:", pedir(staff, "/api/pacientes?codigo=" + urllib.parse.quote("' OR '1'='1"))[0])

paciente = nuevo_cliente()
print("7. Login como mariana:", login(paciente, "mariana", os.environ["PATIENT_PASSWORD"]))
print("8. mariana pide el resultado 2 (de otro paciente):", pedir(paciente, "/api/resultados/2")[0],
      "(403 = corregido, 200 = vulnerable)")
print("Listo. Revisa logs/seguridad.log")
