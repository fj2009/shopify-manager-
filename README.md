# Shopify Manager

Sistema de gestión integral para ventas de lámparas conectado a Shopify.

Capa de inteligencia operativa entre el inventario de Shopify y la realidad del vendedor:
registro de ventas en segundos, pedidos personalizados con notas de taller, gamificación
de metas y CRM de seguimiento post-venta. Ver `PRD.md` para los requerimientos completos.

## Stack

- **Infraestructura:** Docker + Docker Compose (entorno idéntico en local y nube)
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy (async) + Redis
- **Frontend:** Next.js 14 + React 18 + Tailwind CSS + Recharts
- **Base de datos:** PostgreSQL 16
- **Caché/Cola:** Redis 7

## Arranque rápido (local)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger (OpenAPI): http://localhost:8000/docs

Las migraciones de Alembic se ejecutan solas al arrancar el backend. Para poblar datos demo
(vendedores, catálogo, precios) y poder usar la app de inmediato:

```bash
make seed
```

Credenciales demo (cambia en producción): `ana@tienda.com` / `secret123`.

Usar `make` para tareas comunes:

```bash
make up      # levantar contenedores en background
make logs    # seguir logs
make down    # detener
make reset   # detener y borrar volúmenes (pierde datos)
```

## Estructura

```
├── docker-compose.yml      # postgres + redis + backend + frontend
├── backend/                # FastAPI (app/ core, models, schemas, api, services, worker)
├── frontend/               # Next.js + Tailwind (app/, components/, lib/)
├── docs/                   # API.md (referencia de endpoints)
└── .github/workflows/ci.yml
```

## Despliegue externo

`docker-compose.yml` es multi-entorno: en la nube (AWS ECS, Cloud Run, VPS + Traefik o
Caddy) se despliega el mismo stack, se define la `POSTGRES_PASSWORD` real en `.env` y se
apunta `NEXT_PUBLIC_API_URL` y `SHOPIFY_APP_URL` al dominio público, siempre con HTTPS.

## Integración con Shopify

1. Crea una **Custom App** en `https://<tienda>/admin/settings/apps/developers`.
2. Genera `API key`, `API secret` y un `access token` de Admin.
3. Llenar `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `SHOPIFY_APP_URL` en `.env`.
4. Registrar los webhooks: `orders/create`, `orders/updated`, `products/update`.
   La app los recibe en `POST /api/v1/shopify/webhooks/{topic}` y los encola en Redis.

Apuntes para el equipo:

- **Límites de consulta:** la Admin API GraphQL usa el coste de tokens por operación.
  Todo tráfico saliente a Shopify debe pasar por la capa de caché/cola (Redis) y respetar
  `X-Shopify-Shop-Api-Call-Limit`.
- **Tiempo de respuesta API < 200ms:** listas con paginación + lazy loading y consultas indexadas.
- **Frontend:** diseño Atomic Design, Admin-First, oscuro/claro, pensado para tablet y laptop.