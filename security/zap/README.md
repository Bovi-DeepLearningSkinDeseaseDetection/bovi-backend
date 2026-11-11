# Escaneo OWASP ZAP (RNF5)

**Criterio:** escaneo OWASP ZAP sin hallazgos de riesgo alto.

## Resultado (11/11/2026)

`zap-api-scan.py` (ZAP estable) sobre la API completa a partir de su OpenAPI, **autenticado** con
el token de un ganadero de prueba, así que también se atacaron las rutas protegidas (39 variantes de
endpoint: auth, sync, media, historial y health).

| Riesgo | Hallazgos |
|---|---|
| Alto | **0** |
| Medio | **0** |
| Bajo | **0** |
| Informativo | 3 |

Reglas aprobadas: 120, entre ellas inyección SQL (también por tiempo, para PostgreSQL), XSS,
inyección de comandos, *path traversal*, XXE, SSTI, *Log4Shell*, fugas de `.env` y de metadatos de
la nube. Reporte completo: [reporte.html](reporte.html) y [reporte.md](reporte.md).

### Hallazgos informativos (no requieren cambios)

| Hallazgo | Por qué es correcto |
|---|---|
| *A Client Error response code was returned* (41) | Son los 404 de rutas que no existen y los 422 de los parámetros inválidos que ZAP envía a propósito. La API responde con su error en español y sin detalles internos. |
| *Authentication Request Identified* (1) | ZAP reconoce `/auth/login`. Solo informa. |
| *Non-Storable Content* | Es intencional: todas las respuestas llevan `Cache-Control: no-store` porque contienen tokens y URLs prefirmadas. |

## Medidas que el escaneo verificó

- Cabeceras en todas las respuestas: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Content-Security-Policy: default-src 'none'`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store`.
- Sin la cabecera `Server` de uvicorn ni trazas en los errores 500.
- Consultas con parámetros de SQLAlchemy (sin SQL armado a mano con datos del usuario).
- En producción, Nginx agrega TLS 1.2+, HSTS y el límite de intentos en `/auth`
  (ver [docs/despliegue.md](../../docs/despliegue.md)).

## Cómo repetirlo

En Linux o macOS:

```bash
docker compose up -d --build db s3 s3-init api
sh security/zap/run-zap.sh
```

En Windows (Git Bash), anteponga `MSYS_NO_PATHCONV=1` y monte la carpeta con `$(pwd -W)`.

Antes del piloto conviene repetirlo contra producción (`API_INTERNAL=https://<dominio>` y sin
`--network`), para incluir Nginx y TLS en el análisis.
