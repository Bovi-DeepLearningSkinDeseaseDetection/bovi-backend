# Bovi Backend - Contexto del proyecto

Lee este archivo antes de escribir código. El detalle de requisitos, historias y arquitectura está en
el proyecto de arquitectura (`bovi-arquitecture`: `requisitos/` y `architecture/`).

## 1. Qué es

Bovi es una app Android Offline-First que clasifica en el celular lesiones de piel del ganado bovino
(Sana, Dermatofitosis, Papilomatosis, Sarna, Miasis). Este backend solo respalda los datos:
autenticación (JWT), sincronización de animales y evaluaciones, URLs prefirmadas de S3 y
restauración del historial. **No** hace inferencia, ni portal web, ni `/admin`, ni notificaciones,
ni reportes.

## 2. Arquitectura: monolito modular DDD

Mismos bounded contexts que la app móvil (`bovi-mobile-app/lib/`):

| Contexto | Agregados | Endpoints (prefijo `/api/v1`) | HU |
|---|---|---|---|
| `iam` | `User` | `/auth/register`, `/auth/login`, `/auth/refresh` | HU14 |
| `livestock` | `Animal` | `/sync/animals`, `/animals` | HU15 (parte), HU13 |
| `clinical` | `Evaluation` | `/sync/evaluations`, `/media/upload-url`, `/media/download-url`, `/evaluations` | HU12, HU13 |
| `shared` | — | `/health` | RNF15 |

Capas de cada contexto (`src/bovi/<contexto>/`):

- `domain/model/{aggregates,entities,valueobjects,commands,queries,events}`, `domain/exceptions`,
  `domain/services` (puertos). Python puro: sin FastAPI ni SQLAlchemy.
- `application/internal/{commandservices,queryservices,outboundservices,eventhandlers}`,
  `application/acl`.
- `infrastructure/persistence/sqlalchemy/{entities,repositories}`, `infrastructure/storage/s3`,
  y en `iam`: `tokens/jwt`, `hashing/bcrypt`, `authorization/fastapi`.
- `interfaces/rest` (controladores) + `rest/resources` (esquemas Pydantic) + `rest/transform`
  (resource ↔ comando/agregado), `interfaces/acl` (fachada que el contexto ofrece a los demás).

Reglas de dependencia:

- Un contexto **nunca** importa el `domain` ni la `infrastructure` de otro. Solo usa la fachada de
  `interfaces/acl` del otro contexto, a través de un `application/internal/outboundservices`.
- `shared` no importa nada de los contextos.
- Los componentes del TI se reparten así: **SyncRESTController** = `interfaces/rest` de cada contexto ·
  **ClinicalSyncModule** = `clinical/application` + `clinical/domain` · **CloudPersistenceManager** =
  `infrastructure/persistence` + `infrastructure/storage` de cada contexto.

## 3. Stack

Python 3.12 (Docker; en local sirve 3.12+) · FastAPI · SQLAlchemy 2 **síncrono** con psycopg 3 ·
Alembic · Pydantic v2 + pydantic-settings · PostgreSQL 16 (RDS) · S3 con boto3 (en local, un emulador S3 por definir en B2: `minio/minio` ya no se publica) ·
pytest · ruff. Docker Compose en local; EC2 + Nginx + RDS + S3 en `sa-east-1`.

## 4. Piezas de `shared` que ya existen

- `shared/infrastructure/configuration/settings.py`: `Settings` y `get_settings()`. Toda la configuración
  sale de variables de entorno (`.env.example`).
- `shared/infrastructure/persistence/sqlalchemy/configuration/database.py`: `Base` (con convención de
  nombres), `Database` y la dependencia `get_session` (una sesión por request; el servicio de aplicación
  hace el `commit`).
- `shared/domain/exceptions`: `DomainError`, `ValidationError` (422), `NotFoundError` (404),
  `ConflictError` (409), `AuthenticationError` (401), `PermissionDeniedError` (403). Se lanzan con un
  mensaje en español y, si hace falta, un `code` propio (`arete_duplicado`).
- `shared/interfaces/rest/error_handlers.py`: todo error sale como
  `{"code", "message", "details": [{"field", "message"}]}` con mensajes en español, incluidos los de
  validación de Pydantic.
- `bovi/main.py`: `create_app(settings)`; cada contexto registra su router con el prefijo `API_V1_PREFIX`.
- `migrations/env.py`: importa `<contexto>.infrastructure.persistence.sqlalchemy.entities` de cada contexto.

## 5. Modelo de datos (tablas y columnas en español)

- **usuario:** id (UUID), nombre, correo (único, en minúsculas), hash_contrasena, activo,
  consentimiento_aceptado_en, consentimiento_version, creado_en
- **animal:** id (UUID generado en el celular), usuario_id, arete (normalizado: sin espacios y en
  mayúsculas, ≤ 20, `[A-Z0-9-]`), raza, sexo (`hembra` | `macho`), creado_en. Único `(usuario_id, arete)`.
  Si llega otro uuid con un arete que ya existe, se fusiona y se responde el uuid existente.
- **evaluacion:** id (UUID del celular, que también es la clave de idempotencia), usuario_id, animal_id,
  fecha_hora, zona_corporal (`cabeza|cuello|lomo|flanco|patas|ubre|otra`), resultado
  (`sana|lesion|no_concluyente`, calculado por la app), clase_predicha, confianza, probabilidades (JSON),
  clinical_codes (JSON `[{system, code, display}]`), catalog_version, model_version,
  origen_imagen (`camara|galeria`), image_key, creado_en

## 6. Reglas que no se negocian

- **Idempotencia:** `INSERT ... ON CONFLICT DO NOTHING` y estado por registro (aceptado, duplicado,
  rechazado con motivo). Nunca duplicar ni perder (RNF10).
- **La evaluación es inmutable** y el backend no recalcula el resultado.
- **Las imágenes no pasan por el backend:** POST prefirmado con `content-length-range` ≤ 500 KB y solo
  `image/jpeg` (RNF18). Antes de confirmar una evaluación, `HeadObject`.
- **Aislamiento por usuario:** filtra siempre por el `usuario_id` del token, nunca por uno del request.
- **Sin secretos en el código.** En AWS, S3 usa el rol IAM de la EC2.
- **Mensajes en español** para el usuario final. Código, clases y claves JSON en inglés.

## 7. Requisitos que cubre

RF6, RF12, RF13 y parte de RF8. RNF5, RNF6 (parte), RNF7, RNF10, RNF13 (cobertura ≥ 70 % en dominio),
RNF15, RNF16 (50 usuarios, p95 ≤ 500 ms), RNF17 (trazabilidad) y RNF18.

## 8. Convenciones

- Cada endpoint lleva pruebas en pytest basadas en los criterios Dado/Cuando/Entonces de su HU.
  Las que tocan PostgreSQL se marcan `@pytest.mark.integration` y usan el fixture `database`.
- Migraciones siempre con Alembic (`alembic revision --autogenerate`).
- `ruff check` y `ruff format` limpios antes de cada commit (los corre el CI).
- Ramas: `feature/<id>-<descripcion>` desde `develop` (git flow).
