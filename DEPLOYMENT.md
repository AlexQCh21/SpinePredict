# Despliegue en Oracle VPS (Docker + Supabase)

Este documento describe el despliegue de **SpinePredict** en un VPS de Oracle con **IP pública y sin dominio** usando Docker Compose, **Supabase Postgres** y **Supabase Storage (S3 compatible, bucket privado)**.

## 1. Requisitos

- VPS Oracle (Ubuntu recomendado) con Docker Engine y Docker Compose plugin.
- IP pública del VPS y acceso para abrir el puerto `8000/tcp`.
- Proyecto en [Supabase](https://supabase.com):
  - Base de datos Postgres.
  - Storage con bucket **privado** para media.
  - Credenciales S3 compatibles (endpoint, region, access key, secret key).

## 2. Preparar Supabase

### Postgres
1. Crea el proyecto en Supabase.
2. Obtén la cadena de conexión Postgres (`DATABASE_URL`).
3. Usa `sslmode=require` en la URL.

Ejemplo:
```text
postgres://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres?sslmode=require
```

> Si usas pooler (transaction mode), puede ser necesario ajustar `DB_DISABLE_SERVER_SIDE_CURSORS=1`. Prueba con `0` primero.

### Storage (bucket privado)
1. Crea un bucket (ej. `spinepredict-media`) y mantenlo **privado**.
2. Habilita/obtén credenciales S3 compatibles desde Supabase Storage.
3. Configura en `.env`: `SUPABASE_S3_ENDPOINT`, `SUPABASE_S3_REGION`, `SUPABASE_S3_ACCESS_KEY_ID`, `SUPABASE_S3_SECRET_ACCESS_KEY`, `SUPABASE_S3_BUCKET`.
4. `SUPABASE_MEDIA_EXPIRE=3600` genera URLs firmadas con validez de 1 hora.

No migres `db.sqlite3` ni la carpeta `media/` local: la BD se inicializa con migraciones y `seed_demo`.

## 3. Configurar el VPS (Oracle)

1. Conéctate por SSH.
2. Instala Docker y Compose (según documentación oficial).
3. Clona el repositorio:
   ```bash
   git clone https://github.com/AlexQCh21/SpinePredict.git
   cd SpinePredict
   ```
4. Crea el archivo de entorno:
   ```bash
   cp .env.example .env
   nano .env
   ```
5. Completa como mínimo:
   - `DJANGO_SECRET_KEY` (valor largo y aleatorio)
   - `DJANGO_DEBUG=0`
   - `DJANGO_ALLOWED_HOSTS=TU_IP_PUBLICA,localhost,127.0.0.1`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=http://TU_IP_PUBLICA:8000`
   - `DATABASE_URL=...sslmode=require`
   - Credenciales `SUPABASE_S3_*`
   - `DEMO_MODE=1` (si quieres demo compartido)

> `docker-compose.yml` declara explícitamente todas las variables de entorno requeridas y Docker Compose carga `.env` automáticamente para interpolar sus valores (no se usa `env_file`). Si faltan `DJANGO_SECRET_KEY` o `DATABASE_URL`, Compose mostrará un error antes de levantar los contenedores.

## 4. Abrir puerto 8000

### Firewall del SO (Ubuntu/iptables/ufw según imagen)
Ejemplo con `ufw`:
```bash
sudo ufw allow 8000/tcp
sudo ufw reload
```

### Oracle Cloud (Security List / NSG)
En la VCN/subred o NSG de la instancia, agrega una regla de ingreso:
- Source: `0.0.0.0/0` (o el rango que necesites)
- Protocol: TCP
- Destination port: `8000`

Sin esto, la app no será accesible desde internet aunque Gunicorn esté corriendo.

## 5. Levantar servicios

```bash
docker compose up -d --build
```

Con limpieza horaria del modo demo:
```bash
docker compose --profile demo up -d --build
```

Verificar:
```bash
docker compose ps
docker compose logs -f web
curl http://127.0.0.1:8000/healthz/
```

Accede desde tu navegador: `http://TU_IP_PUBLICA:8000/`

## 6. Qué hace el arranque

El contenedor `web` ejecuta `entrypoint.sh`:
1. `python manage.py migrate --noinput`
2. Si `DEMO_MODE` está activo: `seed_demo --refresh` y `limpiar_demo --refresh-seed`
3. `collectstatic --noinput`
4. Gunicorn en `0.0.0.0:8000`

El servicio `cleanup` (perfil `demo`) ejecuta cada `DEMO_CLEANUP_INTERVAL_SECONDS` (por defecto 3600 s):
- elimina registros no demo creados por visitantes;
- restaura el estado canónico del demo.

## 7. Cuentas demo

Con `DEMO_MODE=1`, el login muestra botones para entrar como:
- Administrador: `DEMO_ADMIN_USERNAME` / `DEMO_ADMIN_PASSWORD` (por defecto `demo_admin` / `Admin12345`)
- Especialista: `DEMO_SPECIALIST_USERNAME` / `DEMO_SPECIALIST_PASSWORD` (por defecto `demo_especialista` / `Especialista12345`)

Cambia las contraseñas en `.env` si lo deseas. Los datos son compartidos y se restauran automáticamente.

## 8. Operación

Actualizar despliegue:
```bash
git pull
docker compose --profile demo up -d --build
```

Ejecutar comandos manualmente:
```bash
docker compose exec web python manage.py seed_demo --refresh
docker compose exec web python manage.py limpiar_demo --refresh-seed
docker compose exec web python manage.py check
```

Respaldos: configura backups en Supabase Postgres y políticas de retención en Storage según tus necesidades.

## 9. Limitaciones (sin dominio/HTTPS)

- El acceso es por `http://IP:8000` (sin TLS). Las cookies/CSRF funcionan con `DJANGO_CSRF_TRUSTED_ORIGINS` correcto, pero para producción real se recomienda dominio + HTTPS (reverse proxy Nginx/Caddy + certificado).
- XGBoost/scikit-learn pueden requerir memoria suficiente en el VPS; ajusta `GUNICORN_WORKERS`/swap si es necesario.
- Modo demo es para pruebas controladas, no para datos clínicos reales.
