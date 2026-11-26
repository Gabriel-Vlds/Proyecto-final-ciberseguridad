# Laboratorio local: Flask y OWASP ZAP

Aplicacion educativa que simula un inicio de sesion y un panel bancario. Todas las personas, cuentas, saldos y transacciones son inventados; no procesa dinero ni se conecta con ningun banco. Solo debe ejecutarse en el equipo local.

## Requisitos

- Python 3.10 o posterior
- OWASP ZAP Desktop, o Docker para ejecutar ZAP Baseline

## Preparar y ejecutar

Desde la carpeta del proyecto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edita .env y define valores locales para SECRET_KEY, DEMO_USERNAME y DEMO_PASSWORD.
python app.py
```

La aplicacion escucha unicamente en `127.0.0.1:5000` y no activa el modo debug. Abre <http://127.0.0.1:5000>.

El archivo `.env` contiene la clave de sesion y las credenciales locales. Esta excluido de Git; no lo publiques ni reutilices sus valores en otros servicios. El archivo `.env.example` solo es una plantilla con valores de reemplazo. Esta aplicacion es exclusivamente para el laboratorio local; no la publiques ni despliegues.

## Rutas para verificar

| Metodo | Ruta | Resultado esperado |
| --- | --- | --- |
| GET | `/` | Redireccion a login o al panel si ya iniciaste sesion |
| GET/POST | `/login` | Formulario y autenticacion de demostracion |
| GET | `/dashboard` | Panel protegido; sin sesion redirige al login |
| POST | `/logout` | Cierra la sesion (requiere token CSRF) |
| GET | `/api/health` | JSON de estado, disponible sin autenticacion |
| GET | `/api/accounts` | Cuentas ficticias, requiere autenticacion |

Con el servidor iniciado, comprueba el estado en otra terminal:

```bash
curl -i http://127.0.0.1:5000/api/health
```

Ejecuta las pruebas automatizadas:

```bash
python -m unittest discover -s tests -v
```

## Analizar con OWASP ZAP

1. Inicia la aplicacion y mantenla ejecutandose en `127.0.0.1:5000`.
2. En ZAP Desktop, abre **Quick Start → Manual Explore**, introduce `http://127.0.0.1:5000` y explora el sitio. Inicia sesion con las credenciales de demostracion para que ZAP pueda recorrer el panel; verifica que el alcance/contexto incluya solo este host.
3. Usa el spider y el escaneo pasivo para observar las solicitudes y alertas. La aplicacion incluye protecciones basicas, por lo que un hallazgo no implica necesariamente una vulnerabilidad explotable.

Alternativa por consola con ZAP Baseline (Docker en macOS):

```bash
docker run --rm -t ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t http://host.docker.internal:5000
```

Baseline realiza rastreo y análisis pasivo; no es un escaneo activo. Limita las pruebas a esta aplicacion local autorizada. No apuntes ZAP a sitios de terceros. Si la actividad requiere escaneo activo, confirma primero que el objetivo sea exclusivamente este laboratorio y que entiendes que puede enviar solicitudes modificadoras.
