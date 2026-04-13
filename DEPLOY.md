# Pisubí — Deploy

## Opción A: Fly.io (recomendado — volumen persistente)

```bash
# 1. Instalar flyctl
curl -L https://fly.io/install.sh | sh

# 2. Login
fly auth login

# 3. Lanzar (primera vez)
fly launch --name pisubi-backend --region gru

# 4. Crear volumen para SQLite (1 GB)
fly volumes create pisubi_data --size 1 --region gru

# 5. Setear env vars
fly secrets set GROQ_API_KEY=... CEREBRAS_API_KEY=... MISTRAL_API_KEY=...

# 6. Deploy
fly deploy

# 7. Verificar
fly open /health
```

**Nota**: La DB SQLite se persiste en `/app/backend/db` via el volumen `pisubi_data`.
Antes del primer deploy, subir la DB existente:
```bash
fly ssh sftp shell
put backend/db/commodity_monitor.db /app/backend/db/commodity_monitor.db
```

---

## Opción B: Railway

Railway no soporta volúmenes persistentes en free tier.
**Alternativa**: migrar a PostgreSQL usando el plugin de Railway.

Pasos básicos:
1. Crear proyecto en railway.app
2. Add PostgreSQL service → copiar DATABASE_URL
3. Adaptar `backend/db/init_db.py` para usar psycopg2 con DATABASE_URL
4. Deploy con `railway up`

---

## Frontend (Vercel / GitHub Pages)

```bash
cd frontend
npm run build
# dist/ → subir a Vercel o GitHub Pages

# Vercel
vercel --prod

# GitHub Pages (via gh-pages)
npm install --save-dev gh-pages
# En package.json: "homepage": "https://TU_USER.github.io/pisubit"
# scripts: "deploy": "gh-pages -d dist"
npm run deploy
```

Actualizar `frontend/vite.config.ts` para producción:
```ts
// Reemplazar proxy con la URL real del backend
// server.proxy['/api'] → https://pisubi-backend.fly.dev
```

---

## Variables de entorno en producción

| Variable | Descripción |
|---|---|
| `GROQ_API_KEY` | Groq (proveedor LLM principal) |
| `CEREBRAS_API_KEY` | Cerebras (fallback LLM 1) |
| `MISTRAL_API_KEY` | Mistral (fallback LLM 2) |
| `FRED_API_KEY` | FRED (opcional, para Fed Rate / DXY) |
