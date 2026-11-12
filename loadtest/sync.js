// RNF16: 50 ganaderos concurrentes con p95 <= 500 ms en la sincronización de evaluaciones.
//
// Cada usuario virtual hace lo que hace la app al recuperar la conexión: pide URLs de subida,
// sube las fotos directo a S3 y sincroniza el lote. De vez en cuando consulta su historial.
//
//   docker run --rm --network bovi-backend_default -v "$PWD/loadtest:/scripts" grafana/k6 run \
//     -e BASE_URL=http://api:8000 -e S3_PUBLIC=http://localhost:9000 -e S3_INTERNAL=http://s3:9000 \
//     /scripts/sync.js
//
// Contra producción: -e BASE_URL=https://api.bovi.pe (sin S3_PUBLIC ni S3_INTERNAL).

import http from "k6/http";
import { check, sleep } from "k6";
import { randomBytes } from "k6/crypto";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const API = `${BASE_URL}/api/v1`;
const USERS = Number(__ENV.USERS || 50);
const BATCH = Number(__ENV.BATCH || 5);
// Las URLs prefirmadas traen el host que ve la app; dentro de Docker S3 tiene otro nombre.
const S3_PUBLIC = __ENV.S3_PUBLIC || "";
const S3_INTERNAL = __ENV.S3_INTERNAL || "";

// Foto de unos 120 KB: el tamaño típico de una evaluación comprimida (RNF11).
const PHOTO = new Uint8Array(randomBytes(120 * 1024));
PHOTO.set([0xff, 0xd8, 0xff, 0xe0]);

export const options = {
  setupTimeout: "180s",
  scenarios: {
    farmers: {
      executor: "constant-vus",
      vus: USERS,
      duration: __ENV.DURATION || "2m",
    },
  },
  thresholds: {
    "http_req_duration{name:sync_evaluations}": ["p(95)<500"],
    "http_req_failed{name:sync_evaluations}": ["rate<0.01"],
    "http_req_duration{name:upload_url}": ["p(95)<500"],
    "http_req_duration{name:history}": ["p(95)<500"],
    checks: ["rate>0.99"],
  },
  summaryTrendStats: ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],
};

function uuid() {
  const b = new Uint8Array(randomBytes(16));
  b[6] = (b[6] & 0x0f) | 0x40;
  b[8] = (b[8] & 0x3f) | 0x80;
  const h = Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20)}`;
}

// S3 exige que `file` sea el último campo del formulario, y un objeto de k6 no garantiza el
// orden: se arma el multipart a mano (lo mismo debe cuidar la app).
const BOUNDARY = "----bovi-k6-boundary";

function utf8(text) {
  const out = new Uint8Array(text.length);
  for (let i = 0; i < text.length; i++) out[i] = text.charCodeAt(i);
  return out;
}

function multipart(fields) {
  let head = "";
  for (const [name, value] of Object.entries(fields)) {
    head += `--${BOUNDARY}\r\nContent-Disposition: form-data; name="${name}"\r\n\r\n${value}\r\n`;
  }
  head += `--${BOUNDARY}\r\nContent-Disposition: form-data; name="file"; filename="foto.jpg"\r\n`;
  head += "Content-Type: image/jpeg\r\n\r\n";
  const parts = [utf8(head), PHOTO, utf8(`\r\n--${BOUNDARY}--\r\n`)];
  const body = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let offset = 0;
  for (const p of parts) {
    body.set(p, offset);
    offset += p.length;
  }
  return body.buffer;
}

function json(body, token, name) {
  return {
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    tags: { name },
  };
}

export function setup() {
  const run = uuid().slice(0, 8);
  const farmers = [];
  for (let i = 0; i < USERS; i++) {
    const res = http.post(
      `${API}/auth/register`,
      JSON.stringify({
        name: `Ganadero de carga ${i}`,
        email: `carga-${run}-${i}@bovi.test`,
        password: "establo2026",
        consent_accepted: true,
      }),
      json(null, null, "register"),
    );
    check(res, { "registro 201": (r) => r.status === 201 });
    const token = res.json("access_token");
    const animalId = uuid();
    http.post(
      `${API}/sync/animals`,
      JSON.stringify({
        animals: [
          { id: animalId, ear_tag: `PE-${i}`, breed: "Holstein", sex: "female", created_at: new Date().toISOString() },
        ],
      }),
      json(null, token, "sync_animals"),
    );
    farmers.push({ token, animalId });
  }
  return { farmers };
}

function evaluation(id, animalId) {
  return {
    id,
    evaluated_at: new Date().toISOString(),
    image_origin: "camera",
    probabilities: [
      { label: "dermatofitosis", probability: 0.006108 },
      { label: "miasis", probability: 0.000231 },
      { label: "papilomatosis", probability: 0.015779 },
      { label: "piel_sana", probability: 0.002489 },
      { label: "sarna", probability: 0.975393 },
    ],
    predicted_class: "sarna",
    confidence: 0.975393,
    outcome: "lesion",
    clinical_codes: [{ system: "http://id.nlm.nih.gov/mesh", code: "D008924", display: "Mite Infestations" }],
    catalog_version: "2026.1",
    model_version: "v7c_peso_pap",
    inference_ms: 180,
    animal_id: animalId,
    body_zone: "flank",
  };
}

export default function (data) {
  const { token, animalId } = data.farmers[(__VU - 1) % data.farmers.length];
  const ids = Array.from({ length: BATCH }, uuid);

  const urls = http.post(`${API}/media/upload-url`, JSON.stringify({ evaluation_ids: ids }), json(null, token, "upload_url"));
  check(urls, { "upload-url 200": (r) => r.status === 200 });

  for (const item of urls.json("items")) {
    const target = S3_PUBLIC ? item.upload.url.replace(S3_PUBLIC, S3_INTERNAL) : item.upload.url;
    const put = http.post(target, multipart(item.upload.fields), {
      headers: { "Content-Type": `multipart/form-data; boundary=${BOUNDARY}` },
      tags: { name: "s3_upload" },
    });
    check(put, { "foto en S3": (r) => r.status === 204 || r.status === 200 || r.status === 201 });
  }

  const sync = http.post(
    `${API}/sync/evaluations`,
    JSON.stringify({ evaluations: ids.map((id) => evaluation(id, animalId)) }),
    json(null, token, "sync_evaluations"),
  );
  check(sync, {
    "sync 200": (r) => r.status === 200,
    "lote aceptado": (r) => r.status === 200 && r.json("accepted") === BATCH,
  });

  if (__ITER % 4 === 0) {
    const history = http.get(`${API}/evaluations?limit=50`, json(null, token, "history"));
    check(history, { "historial 200": (r) => r.status === 200 });
  }

  // La app sincroniza en segundo plano: entre lote y lote hay segundos, no milisegundos.
  sleep(1 + Math.random() * 2);
}
