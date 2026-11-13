# Bovi · Backend

API REST del prototipo **Bovi**, la app Android que detecta de forma preliminar enfermedades
cutáneas del ganado bovino en los establos de Lurín. La detección corre en el celular; este
backend solo respalda los datos:

1. Registra e inicia sesión al ganadero (JWT).
2. Recibe la sincronización de animales y evaluaciones.
3. Entrega URLs prefirmadas de S3 para subir y descargar las imágenes.
4. Devuelve el historial para restaurarlo en un dispositivo nuevo.

**Stack:** Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 · PostgreSQL 16 ·
Amazon S3 (RustFS en local) · Docker · pytest.

## Arquitectura

Monolito modular con **DDD**, dividido en los mismos bounded contexts que la app móvil:

| Contexto | Responsabilidad |
|---|---|
| `iam` | Ganadero, registro, inicio de sesión, JWT y consentimiento (Ley N.° 29733). |
| `livestock` | Animales del establo (arete único por ganadero). |
| `clinical` | Evaluaciones inmutables, sincronización idempotente, imágenes en S3 e historial. |
| `shared` | Configuración, base de datos, errores en español, OpenAPI y `/health`. |

Cada contexto tiene las mismas capas:

```
src/bovi/<contexto>/
├── domain/          agregados, value objects, comandos, consultas, excepciones, puertos
├── application/     servicios de comandos y consultas, ACL hacia otros contextos
├── infrastructure/  SQLAlchemy (entidades y repositorios), S3, JWT, bcrypt
└── interfaces/      REST (controladores, resources, transform) y ACL que expone el contexto
```

Los componentes del documento TI se reparten así: **SyncRESTController** = `interfaces/rest`,
**ClinicalSyncModule** = `clinical/application` + `clinical/domain`,
**CloudPersistenceManager** = `infrastructure/persistence` y `infrastructure/storage`.

## Desarrollo local

Requisitos: Python 3.12 o superior y Docker.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d db s3 s3-init
alembic upgrade head
uvicorn --factory bovi.main:app_factory --reload
```

- API: http://localhost:8000 · documentación: http://localhost:8000/docs
- RustFS (S3 local): API en http://localhost:9000, consola en http://localhost:9001
  (`bovilocal` / `bovilocal123`).

Para levantar todo en contenedores, incluida la API: `docker compose up --build`.

## Pruebas

```bash
pytest                       # todo (integración: `docker compose up -d db s3 s3-init`)
pytest -m "not integration"  # solo unitarias
pytest -m "not s3"           # sin RustFS
pytest --cov                 # con cobertura
ruff check src tests migrations && ruff format --check src tests migrations
```

Las pruebas de integración usan la base `bovi_test`, que el contenedor `db` crea al iniciarse.
Si PostgreSQL no está levantado se saltan en local; en CI fallan.

## Migraciones

```bash
alembic revision --autogenerate -m "crear tabla usuario"
alembic upgrade head
```

Cada contexto registra sus entidades ORM en `infrastructure/persistence/sqlalchemy/entities/__init__.py`,
que `migrations/env.py` importa. Nunca se crean tablas a mano.

## Variables de entorno

Todas están documentadas en [.env.example](.env.example). En producción (`APP_ENV=production`)
la app no arranca si `JWT_SECRET` tiene menos de 32 caracteres o si `S3_ENDPOINT_URL` está definido.
En AWS, las credenciales de S3 vienen del rol IAM de la EC2, no de variables.

## Despliegue

Producción en AWS (`sa-east-1`): EC2 t3.small con Nginx (HTTPS, Let's Encrypt) delante de la API,
RDS PostgreSQL 16 privado y S3 privado. La infraestructura está en `infra/terraform`, los archivos
del servidor en `deploy/` y el procedimiento completo, con costos, backups y restauración, en
[docs/despliegue.md](docs/despliegue.md). Si es la primera vez con AWS, empiece por
[docs/despliegue-paso-a-paso.md](docs/despliegue-paso-a-paso.md).
