"""Genera eventos de seguridad controlados contra la app LOCAL (127.0.0.1:5000).
Uso: con la app corriendo en otra terminal:  python generar_eventos.py
"""
import http.cookiejar
import re
import urllib.error
import urllib.parse
import urllib.request

from dotenv import load_dotenv
import os

load_dotenv()
BASE = "http://127.0.0.1:5000"
jar = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def pedir(ruta, datos=None):
    body = urllib.parse.urlencode(datos).encode() if datos is not None else None
    try:
        r = op.open(urllib.request.Request(BASE + ruta, data=body), timeout=5)
        return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, ""


def token():
    _, html = pedir("/login")
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


print("1. Acceso a /dashboard sin sesion:", pedir("/dashboard")[0])
print("2. POST sin token CSRF:", pedir("/login", {"username": "x", "password": "y"})[0])
print("3. Login con contrasena incorrecta:", pedir("/login", {"username": os.environ["DEMO_USERNAME"], "password": "incorrecta", "csrf_token": token()})[0])
print("4. Login correcto:", pedir("/login", {"username": os.environ["DEMO_USERNAME"], "password": os.environ["DEMO_PASSWORD"], "csrf_token": token()})[0])
print("5. Busqueda con <script>:", pedir("/buscar?q=" + urllib.parse.quote('<script>document.title="XSS"</script>'))[0])
print("Listo. Revisa logs/seguridad.log")
