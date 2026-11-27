# Portal de resultados · Clínica Diagnóstica Norte (laboratorio de seguridad de aplicaciones)

Proyecto final de Ciberseguridad (Tecmilenio, SEDI IX). Aplicación **educativa** en Python y Flask con SQLite y datos
**ficticios**. Solo debe ejecutarse en el equipo local (`127.0.0.1`). No la publiques ni la despliegues.

La app trae tres vulnerabilidades que se pueden **activar a propósito** con interruptores del archivo `.env`, para
demostrar el "antes" y compararlo con la versión corregida:

| Interruptor | Vulnerabilidad | Ruta | Corrección (con el interruptor en 0) |
| --- | --- | --- | --- |
| `VULN_SQLI=1` | SQL Injection | `GET /api/pacientes?codigo=` | Consulta parametrizada |
| `VULN_XSS=1` | XSS reflejado | `GET /buscar?q=` | Escape automático de Jinja, límite de 50 caracteres y CSP |
| `VULN_IDOR=1` | Control de acceso roto (IDOR/BOLA) | `GET /api/resultados/<id>` | Autorización por objeto: 403 si el resultado no es del usuario |

Con los tres en `0` (valor por defecto) la app es la versión corregida. Cada intento sospechoso queda en
`logs/seguridad.log`.

## Requisitos

- Python 3.10 o posterior
- OWASP ZAP Desktop
- Docker Desktop (solo para `mejora_respaldos/`)

## Preparar y ejecutar

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# Edita .env: define SECRET_KEY, DEMO_USERNAME, DEMO_PASSWORD y PATIENT_PASSWORD (valores locales tuyos)
python app.py
```

Abre <http://127.0.0.1:5000>. Cuentas: el usuario de personal es `DEMO_USERNAME`; los pacientes de laboratorio son
`mariana` y `carlos`, con la contraseña `PATIENT_PASSWORD`. Para cambiar de modo, edita `.env`, detén la app y vuelve a
ejecutar `python app.py`. Si ya tenías un `clinica.db` de otra versión, bórralo.

## Rutas

| Método | Ruta | Resultado |
| --- | --- | --- |
| GET | `/` | Redirección a login o al panel |
| GET/POST | `/login` | Formulario y autenticación |
| GET | `/dashboard` | Panel protegido (un paciente solo ve lo suyo) |
| POST | `/logout` | Cierra la sesión (requiere token CSRF) |
| GET | `/api/health` | Estado del servicio, sin autenticación |
| GET | `/api/resultados` | Resultados (los pacientes ven solo los propios si IDOR está corregido) |
| GET | `/api/resultados/<id>` | Un resultado por ID |
| GET | `/buscar?q=` | Búsqueda de pacientes por nombre |
| GET | `/api/pacientes?codigo=` | Consulta de un paciente por código |

## Demostrar cada vulnerabilidad (solo en tu laboratorio)

Inicia sesión primero en el navegador y luego usa la URL.

- **SQLi** (`VULN_SQLI=1`): con `mariana` abre `/api/pacientes?codigo=PAC-001` (devuelve 1 paciente) y después
  `/api/pacientes?codigo=' OR '1'='1` (devuelve todos). Con `' UNION SELECT username, password_hash, role FROM users --`
  se filtran los hashes de la tabla de usuarios. Con `VULN_SQLI=0` ambas devuelven una lista vacía.
- **XSS** (`VULN_XSS=1`): abre `/buscar?q=<script>document.title="XSS"</script>`; el título de la pestaña cambia. Con
  `VULN_XSS=0` el texto se muestra sin ejecutarse.
- **IDOR** (`VULN_IDOR=1`): inicia sesión como `mariana` (su panel solo muestra su resultado), abre `/api/resultados/1`
  y cambia el ID a `2`: aparecen los datos de Carlos Vega. Con `VULN_IDOR=0` responde 403.

## Registros de seguridad

`python generar_eventos.py` (con la app corriendo) genera eventos controlados y `logs/seguridad.log` registra:
`LOGIN_OK`, `LOGIN_FALLIDO`, `ACCESO_SIN_SESION`, `CSRF_INVALIDO`, `XSS_SOSPECHOSO`, `SQLI_SOSPECHOSO` e
`IDOR_BLOQUEADO`. No se guardan contraseñas y `logs/` está excluido de Git.

## Pruebas automatizadas

```bash
python -m unittest discover -s tests -v
```

Las pruebas usan valores ficticios propios (no leen tu `.env`) y comprueban cada vulnerabilidad en modo vulnerable y en
modo corregido.

## Analizar con OWASP ZAP

1. Con la app en `127.0.0.1:5000`, abre **Quick Start → Manual Explore** con `http://127.0.0.1:5000`.
2. Inicia sesión en el navegador de ZAP y recorre el panel, `/buscar` y `/api/pacientes`.
3. Lanza un escaneo activo con la política **Default Policy** solo sobre este host local.
4. Repite con el interruptor en `1` y en `0` y compara las alertas.

## Mejora organizacional (Opción C)

`mejora_respaldos/` contiene el laboratorio de respaldos y recuperación (Docker): copias completas e incrementales,
SHA-256, verificación de integridad, retención de 90 días, restauración y cron.

## Seguridad del repositorio

No hay credenciales en el código: todo valor secreto viene del `.env` local, que Git ignora. Los datos son ficticios.
