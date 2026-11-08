# SpinePredict — Apoyo al diagnóstico de columna lumbosacra

> Sistema web Django para apoyo al diagnóstico de hernia de disco, espondilolistesis y columna normal mediante un modelo XGBoost.

Repositorio: [https://github.com/AlexQCh21/SpinePredict](https://github.com/AlexQCh21/SpinePredict)

## Descripción

SpinePredict es una aplicación web basada en Django para gestionar pacientes, usuarios autorizados (administradores y especialistas), historiales de diagnóstico y resultados de predicción. El sistema ofrece un flujo guiado de diagnóstico en tres etapas, registra interacciones, presenta métricas resumidas y genera reportes PDF.

Este repositorio es apto para desarrollo y demostración controlada. Antes de usarlo en un entorno clínico real, se deben completar la validación clínica, el endurecimiento de seguridad, la gestión de secretos y los controles operativos correspondientes.

## Características

- Registro, búsqueda, detalle, edición y activación/desactivación de pacientes.
- Acceso por roles: administradores y especialistas.
- Flujo de diagnóstico guiado para especialistas (selección de paciente, ingreso de mediciones y resultado).
- Clasificación asistida por modelo de machine learning (XGBoost): Hernia de Disco, Espondilolistesis o Normal.
- Historial de diagnósticos con precisión/confianza, filtros por rol y paginación (10 registros por página).
- Generación de informe PDF por diagnóstico.
- Gestión de perfil propio y cambio de contraseña.
- Auditoría de acciones administrativas y de pacientes (administradores).
- Modo demo compartido con cuentas por rol y restauración automática.
- Páginas de error HTTP personalizadas (400, 403, 403 CSRF, 404, 500).
- Endpoint de salud: `/healthz/`.

## Tecnologías

- **Python 3.12** y **Django 5.1.2**.
- **PostgreSQL/Supabase Postgres** en producción; **SQLite** en desarrollo local.
- **Supabase Storage (S3 compatible)** para archivos multimedia en producción (bucket privado con URLs firmadas).
- **Gunicorn** + **WhiteNoise** para despliegue.
- **Docker / Docker Compose**.
- **NumPy, pandas, scikit-learn, XGBoost, joblib** para predicción.
- **ReportLab, PyPDF, xhtml2pdf** para reportes PDF.
- **Pillow** y **django-storages[boto3]** para manejo de imágenes.
- **HTML, CSS y JavaScript** (Bootstrap Icons / Bootstrap en la interfaz).

## Estructura del proyecto

```text
Prediccion/
├── djangocrud/                  # Configuración Django y URLs raíz
├── tasks/                       # App principal (modelos, vistas, forms, templates, static)
│   ├── management/commands/     # seed_demo, limpiar_demo
│   ├── migrations/              # Incluye 0009_demo_fields
│   └── templates/               # Incluye 400/403/404/500/403_csrf
├── media/                       # Archivos locales (solo desarrollo)
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── cleanup_loop.sh
├── .env.example
├── DEPLOYMENT.md
├── manage.py
├── requirements.txt
└── README.md
```

## Instalación local (desarrollo)

### Requisitos

- Python 3.12 (o compatible).
- Git.

### Pasos

```powershell
git clone https://github.com/AlexQCh21/SpinePredict.git
cd SpinePredict
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Configura variables mínimas (opcional en local; por defecto usa SQLite y `DEBUG=1`):

```powershell
$env:DJANGO_SECRET_KEY = "clave-local"
$env:DJANGO_DEBUG = "1"
$env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost"
```

Aplica migraciones y ejecuta:

```powershell
python manage.py migrate
python manage.py seed_demo   # opcional: crea datos/cuentas demo
python manage.py createsuperuser
python manage.py runserver
```

- App: <http://127.0.0.1:8000/>
- Login: <http://127.0.0.1:8000/accounts/login/>
- Salud: <http://127.0.0.1:8000/healthz/>

## Despliegue con Docker + Supabase (VPS Oracle, IP pública)

Consulta [DEPLOYMENT.md](DEPLOYMENT.md) para el procedimiento detallado. Resumen:

1. Crea un proyecto en Supabase con **Postgres** y **Storage**.
2. Crea un bucket **privado** para media y genera credenciales S3 compatibles.
3. Copia `.env.example` a `.env` y completa: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS=http://TU_IP:8000`, `DATABASE_URL` (con `sslmode=require`), claves S3 de Supabase y `DEMO_MODE`. `docker-compose.yml` declara todas las variables requeridas y Docker Compose lee `.env` automáticamente para interpolarlas (sin `env_file`); si faltan `DJANGO_SECRET_KEY` o `DATABASE_URL`, `docker compose config`/arranque fallará con un mensaje claro.
4. Construye y levanta:

```bash
docker compose up -d --build
# Si DEMO_MODE=1, incluye el servicio de limpieza horaria:
docker compose --profile demo up -d --build
```

5. Abre el puerto 8000 en el firewall/red de Oracle y accede a `http://TU_IP_PUBLICA:8000/`.

> Este despliegue usa HTTP (sin dominio). Para producción real se recomienda dominio + HTTPS (TLS) y revisión de seguridad.

## Variables de entorno

| Variable | Propósito | Ejemplo |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave criptográfica de Django | `cambia-esta-clave` |
| `DJANGO_DEBUG` | Modo debug (`0` en producción) | `0` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos (coma) | `TU_IP,localhost` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes CSRF confiables | `http://TU_IP:8000` |
| `DATABASE_URL` | URL Postgres (Supabase) | `postgres://...?...sslmode=require` |
| `DB_CONN_MAX_AGE` | Persistencia de conexión DB | `60` |
| `DB_SSL_REQUIRE` | Exigir SSL al parsear DB URL | `1` |
| `DB_DISABLE_SERVER_SIDE_CURSORS` | Compatibilidad con poolers | `0`/`1` |
| `SUPABASE_S3_ENDPOINT` | Endpoint S3 de Supabase Storage | `https://<ref>.storage.supabase.co/storage/v1/s3` |
| `SUPABASE_S3_REGION` | Región S3 | `us-east-1` |
| `SUPABASE_S3_ACCESS_KEY_ID` | Access key S3 | (secreto) |
| `SUPABASE_S3_SECRET_ACCESS_KEY` | Secret key S3 | (secreto) |
| `SUPABASE_S3_BUCKET` | Bucket privado | `spinepredict-media` |
| `SUPABASE_MEDIA_EXPIRE` | Segundos de validez de URL firmada | `3600` |
| `DEMO_MODE` | Habilita modo demo (`1`/`0`) | `1` |
| `DEMO_CLEANUP_INTERVAL_SECONDS` | Intervalo de limpieza/restauración | `3600` |
| `DEMO_ADMIN_USERNAME` / `DEMO_ADMIN_PASSWORD` | Cuenta demo administrador | `demo_admin` / `Admin12345` |
| `DEMO_SPECIALIST_USERNAME` / `DEMO_SPECIALIST_PASSWORD` | Cuenta demo especialista | `demo_especialista` / `Especialista12345` |
| `GUNICORN_WORKERS` / `GUNICORN_TIMEOUT` | Ajustes de Gunicorn | `2` / `120` |

No subas `.env` ni secretos al repositorio. Las variables se obtienen desde `docker-compose.yml` (declaración explícita) con valores definidos en `.env`.

## Modo demo compartido

- Las cuentas demo son **compartidas** entre todos los visitantes: `demo_admin` y `demo_especialista` (contraseñas definidas en `.env`).
- En la pantalla de login aparecen botones de acceso por rol cuando `DEMO_MODE=1`.
- Cada hora el servicio `cleanup` ejecuta `limpiar_demo --refresh-seed`:
  - elimina pacientes/historiales/auditorías **no demo** creados por visitantes (incluyendo archivos asociados);
  - restaura cuentas, pacientes y diagnósticos demo a su estado canónico (`seed_demo --refresh`).
- `/admin/` se deshabilita en modo demo.

## Páginas de error HTTP

Se integran vistas/handlers personalizados para:
- `400` Solicitud inválida
- `403` Acceso denegado
- `403` CSRF / Sesión expirada
- `404` Página no encontrada
- `500` Error interno del servidor

Las plantillas usan un diseño común y no dependen de datos de base de datos.

## Comandos útiles

```bash
python manage.py migrate
python manage.py seed_demo [--refresh]
python manage.py limpiar_demo [--refresh-seed]
python manage.py collectstatic --noinput
python manage.py check
python manage.py test tasks
```

## Pruebas

```bash
python manage.py test tasks
```

La suite cubre permisos/roles, flujo de diagnóstico, auditoría, perfil, paginación y páginas de error.

## Contribución

1. Crea una rama enfocada desde `main`.
2. Implementa el cambio mínimo completo.
3. Agrega/actualiza tests cuando haya cambios de comportamiento.
4. Ejecuta `python manage.py check` y `python manage.py test tasks`.
5. Abre un pull request con resumen, notas de prueba y capturas si hay cambios de UI.

Evita commitear secretos, `.env`, bases locales, `venv`, `media`, `staticfiles` o artefactos generados.

## Licencia

Por definir.

## Contacto

Por definir.
