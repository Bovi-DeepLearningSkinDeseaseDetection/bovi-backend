# Prueba de carga (RNF16)

**Criterio:** soportar 50 usuarios concurrentes con p95 ≤ 500 ms en la sincronización de evaluaciones.
**Herramienta:** k6, escenario [`loadtest/sync.js`](../../loadtest/sync.js).

## Escenario

Cada usuario virtual es un ganadero que recupera la conexión y hace lo mismo que la app:

1. `POST /media/upload-url` con 5 evaluaciones.
2. Sube las 5 fotos (120 KB cada una) directo a S3 con el POST prefirmado.
3. `POST /sync/evaluations` con el lote de 5 (con animal, zona corporal y códigos clínicos).
4. Una de cada cuatro veces consulta `GET /evaluations?limit=50`.
5. Espera de 1 a 3 segundos y repite.

Antes de empezar se registran los 50 ganaderos y cada uno sincroniza un animal.

## Resultado en el entorno local (11/11/2026)

- **Entorno:** docker-compose en la PC de desarrollo, con PostgreSQL 16 y RustFS.
- **API:** contenedor limitado a **2 vCPU y 2 GB** (como una t3.small), 2 workers de uvicorn.
- **Carga:** 50 usuarios virtuales durante 2 minutos.

| Métrica | Resultado | Criterio |
|---|---|---|
| p95 `POST /sync/evaluations` | **95 ms** (mediana 32 ms, p99 314 ms, máx. 546 ms) | ≤ 500 ms ✓ |
| Errores en la sincronización | **0 de 2054 lotes** | < 1 % ✓ |
| p95 `POST /media/upload-url` | 39 ms | ≤ 500 ms ✓ |
| p95 `GET /evaluations` | 48 ms | ≤ 500 ms ✓ |
| Evaluaciones sincronizadas | 10 270, todas con foto verificada en S3 | sin pérdidas ni duplicados |
| Solicitudes a la API | 15 012 (110 por segundo), 0 % de error | |
| Comprobaciones de k6 | 100 % | > 99 % ✓ |

El p95 global de k6 (638 ms) no corresponde a la API: lo suben el registro inicial de los 50 usuarios
(bcrypt de costo 12, a propósito lento) y la subida de las fotos a S3, que no pasa por el backend.

## Límites de esta medición

- La base y S3 corren en la misma máquina. En AWS, RDS y S3 agregan unos milisegundos de red por
  consulta y por `HeadObject`. Los `HeadObject` van en paralelo, así que el margen hasta 500 ms es amplio.
- La CPU es la de la PC limitada a 2 núcleos, no la de una t3.small, cuyo rendimiento sostenido
  depende de los créditos de CPU.

**Pendiente:** repetir contra producción antes del piloto, con un usuario por cada ganadero real y
fuera del horario de uso:

```bash
docker run --rm -v "$PWD/loadtest:/scripts" grafana/k6 run -e BASE_URL=https://api.bovi.pe /scripts/sync.js
```

Esa prueba deja datos de carga en producción (usuarios `carga-*@bovi.test` y sus fotos):
bórrelos al terminar.

## Cómo repetir en local

```bash
docker compose up -d --build db s3 s3-init api
docker update --cpus 2 --memory 2g --memory-swap 2g $(docker compose ps -q api)
docker run --rm --network bovi-backend_default -v "$PWD/loadtest:/scripts" grafana/k6 run \
  -e BASE_URL=http://api:8000 -e S3_PUBLIC=http://localhost:9000 -e S3_INTERNAL=http://s3:9000 \
  /scripts/sync.js
```

## Hallazgo para la app

S3 exige que el campo `file` vaya **al final** del formulario multipart, después de todos los
`fields` de la URL prefirmada. En la primera corrida, k6 enviaba los campos en otro orden y S3 rechazó
el 88 % de las fotos. El cliente de la app (dio `FormData`) debe agregar primero los `fields`, en el
orden recibido, y la foto al final.
