# Despliegue en AWS (B4)

Runbook para poner el backend en producción según la arquitectura física: **EC2 t3.small** con
Nginx (HTTPS) y la API en Docker, **RDS PostgreSQL 16** en una subred privada y **S3** para las
fotos, todo en `sa-east-1`. La infraestructura está en [`infra/terraform`](../infra/terraform).

> ¿Primera vez con AWS? Siga [despliegue-paso-a-paso.md](despliegue-paso-a-paso.md): crea la
> cuenta, instala las herramientas y despliega, explicado desde cero.

> Crear la infraestructura **genera costos** en la cuenta de AWS. Revise la sección 1 antes de
> ejecutar `terraform apply`.

## 1. Costos referenciales

| Servicio | USD / mes |
|---|---|
| EC2 t3.small 24x7 + disco de 20 GB + IP elástica (incluye el cargo por IPv4 pública) | ~ 22 |
| RDS db.t4g.micro + 20 GB gp3 + backups (los primeros 20 GB de backup no cuestan) | ~ 18 |
| S3 (pocos GB) y transferencia de las fotos | < 2 |
| Health check de Route 53 | ~ 0.75 |
| SSM Parameter Store estándar, SNS por correo, endpoint de S3 | 0 |
| **Total aproximado** | **~ 43** |

Precios de referencia: verifíquelos en la AWS Pricing Calculator. Terraform crea un presupuesto
(`monthly_budget_usd`, 50 por defecto) que avisa por correo al 80 % del gasto real y al 100 % del
pronóstico.

## 2. Requisitos

- Cuenta de AWS con un usuario administrador y la AWS CLI configurada en la PC (`aws configure`).
- Terraform 1.6 o superior (o la imagen `hashicorp/terraform`).
- Un dominio para la API (por ejemplo `api.bovi.pe`). Let's Encrypt necesita un nombre de dominio.
- Acceso de lectura al repositorio desde la EC2 (una *deploy key* de GitHub si es privado).

## 3. Crear la infraestructura

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # domain_name y alert_email
terraform init
terraform plan
terraform apply
```

Al terminar:

1. Confirme la suscripción a las alarmas en el correo que envía AWS (dos correos si el health check
   está activo).
2. Cree en su proveedor de DNS un registro **A** de `domain_name` hacia el output `api_public_ip`.
3. Guarde los outputs: `terraform output`.

El estado de Terraform (`terraform.tfstate`) contiene la contraseña de RDS y el secreto JWT: queda
en su PC y fuera de git. No lo comparta; si trabajan dos personas, muévanlo a un bucket S3 cifrado.

## 4. Primer despliegue en la EC2

Entre sin SSH con Session Manager (el puerto 22 está cerrado):

```bash
aws ssm start-session --target <api_instance_id> --region sa-east-1
sudo su - ubuntu
```

En la EC2:

```bash
git clone https://github.com/Bovi-DeepLearningSkinDeseaseDetection/bovi-backend.git /opt/bovi/app
cd /opt/bovi/app
DOMAIN=api.bovi.pe EMAIL=alertas@bovi.pe sh deploy/scripts/init-tls.sh   # primer certificado
sh deploy/scripts/deploy.sh                                              # rama main
```

`deploy.sh` trae la configuración desde Parameter Store (`render-env.sh` escribe `/opt/bovi/api.env`
con permisos 600), construye la imagen, levanta Nginx y la API, y espera a que el healthcheck diga
`healthy`. Las migraciones de Alembic se aplican solas al iniciar el contenedor.

### Verificación

```bash
curl -s https://api.bovi.pe/health          # {"status":"ok","database":"ok",...}
curl -sI https://api.bovi.pe/health | grep -i strict-transport
```

Pruebe el flujo completo desde la app (registro, sincronización y restauración) antes del piloto.

## 5. Actualizar

```bash
sh /opt/bovi/app/deploy/scripts/deploy.sh                 # última versión de main
REF=v1.1.0 sh /opt/bovi/app/deploy/scripts/deploy.sh      # una etiqueta o rama
```

**Volver atrás:** ejecute `deploy.sh` con el `REF` anterior. Si la versión nueva traía una migración,
revísela antes: `docker compose -f deploy/docker-compose.prod.yml --env-file /opt/bovi/compose.env
run --rm api alembic downgrade -1`.

## 6. Backups y restauración (RNF15)

| Objetivo | Cómo se cumple |
|---|---|
| Backups diarios | RDS hace un backup automático cada día a las 03:00 de Lima y los guarda 7 días. |
| RPO ≤ 24 h | Además del backup diario, RDS guarda los registros de transacciones: se puede restaurar a cualquier momento de los últimos 7 días, con unos 5 minutos de pérdida como máximo. |
| RTO ≤ 4 h | Restaurar crea una instancia nueva en 15 a 30 minutos; luego se cambia `DATABASE_URL` en Parameter Store y se ejecuta `deploy.sh`. |
| Fotos | S3 es duradero por diseño y el bucket está versionado: una foto reemplazada se recupera durante 30 días. |
| Borrado accidental | RDS tiene *deletion protection* y deja un snapshot final si se elimina. |

### Prueba de restauración

Hágala antes del piloto y registre el resultado (lo pide el criterio de RNF15). Desde la PC:

```bash
DB_ID=$(terraform -chdir=infra/terraform output -raw rds_identifier) sh deploy/scripts/test-restore.sh
```

El script restaura una instancia temporal al último punto disponible, mide el tiempo y, cuando
usted termina de comparar los conteos de `usuario`, `animal` y `evaluacion`, la elimina. Cuesta unos
centavos.

| Fecha | Punto restaurado | RPO medido | RTO medido | Conteos coinciden | Responsable |
|---|---|---|---|---|---|
| | | | | | |

### Restauración real (desastre)

1. Restaure a un punto en el tiempo con un identificador nuevo (`aws rds restore-db-instance-to-point-in-time`,
   como en `test-restore.sh`, sin borrarla).
2. Actualice el parámetro `/bovi/prod/DATABASE_URL` con el nuevo endpoint.
3. Ejecute `deploy.sh`. La app reintenta las sincronizaciones pendientes por su cuenta: con la
   idempotencia, lo que se haya perdido entre el backup y la caída vuelve a subir sin duplicarse.
4. Importe la instancia nueva en Terraform o actualice `database.tf`.

## 7. Monitoreo

Alarmas por correo (SNS):

- La EC2 falla el chequeo de estado: además del aviso, AWS la **recupera sola** en otro servidor físico.
- CPU de la EC2 o de RDS sobre 80 % durante 15 minutos.
- RDS con menos de 2 GB libres (el disco crece solo hasta 50 GB).
- `https://<dominio>/health` no responde 200 desde tres regiones (Route 53).
- Presupuesto mensual.

Registros: `docker compose -f deploy/docker-compose.prod.yml --env-file /opt/bovi/compose.env logs -f api`
en la EC2, y los registros de PostgreSQL (consultas de más de 500 ms) en CloudWatch Logs.

## 8. Seguridad (RNF5, RNF6, RNF7)

- Solo HTTPS con TLS 1.2 o superior, HSTS y cabeceras de seguridad; 30 intentos de inicio de sesión
  por minuto por IP; cuerpos de 1 MB como máximo (las fotos van directo a S3).
- La EC2 no tiene access keys: usa su rol de IAM (S3 solo bajo `evaluaciones/`, sus parámetros SSM y
  Session Manager). IMDSv2 obligatorio.
- RDS en subred privada, cifrado y con TLS forzado; solo acepta conexiones de la EC2.
- S3 privado, cifrado y solo por HTTPS.
- Secretos en Parameter Store como `SecureString`; nunca en el repositorio.

Recomendación: la API usa el usuario maestro de RDS. Antes de un uso real, cree un rol de PostgreSQL
con permisos solo sobre las tablas de la aplicación y use ese en `DATABASE_URL`.

## 9. Configurar la app móvil

La URL base de la API en la app es `https://<dominio>/api/v1`. Las fotos se suben a la URL que
entrega `/media/upload-url` (el bucket en `sa-east-1`); la app no necesita conocer el bucket.

## 10. Apagar o eliminar

- **Pausar el piloto:** detenga la EC2 y RDS desde la consola (RDS se vuelve a encender sola a los
  7 días). La IP elástica sigue cobrando mientras exista.
- **Eliminar todo:** desactive `deletion_protection` en `database.tf`, `terraform apply` y luego
  `terraform destroy`. RDS deja un snapshot final, que también cobra almacenamiento hasta que se borre.
  El bucket solo se puede eliminar vacío.
