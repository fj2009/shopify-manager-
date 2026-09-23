# Shopify Manager

Sistema de gestión integral para ventas de lámparas conectado a la **Shopify Admin API**.

Una capa de inteligencia operativa entre el inventario de Shopify y la realidad del vendedor:
registro de ventas en menos de 30 segundos, pedidos personalizados con notas de taller,
gamificación de metas mensuales y CRM de seguimiento post-venta. Corre igual en local y en
la nube gracias a Docker.

> El objetivo no es duplicar el panel de Shopify, sino eliminar la fricción del registro:
> si el vendedor siente que la herramienta le facilita la vida, la adopta y las ventas suben.

---

## Contenido

- [Características](#características)
- [Arquitectura](#arquitectura)
- [Stack tecnológico](#stack-tecnológico)
- [Estructura del repositorio](#estructura-del-repositorio)
- [Cómo empezar (local)](#cómo-empezar-local)
- [Variables de entorno](#variables-de-entorno)
- [Integración con Shopify](#integración-con-shopify)
- [Despliegue en producción](#despliegue-en-producción)
- [API](#api)
- [Flujo de datos y workers](#flujo-de-datos-y-workers)
- [Calidad y CI/CD](#calidad-y-cicd)
- [Roadmap](#roadmap)
- [Documentación](#documentación)

---

## Características

### 1. Registro rápido (Fast-Entry)
- Buscador predictivo de lámparas (nombre, variante o SKU) con autocompletado de cliente.
- La venta se registra en un único request: cantidad, precio y nota de taller, todo junto.
- Validación y descuento de **stock en vivo**; `409` si no alcanza.
- Opcionalmente la venta se emite como *draft order* en Shopify de forma asíncrona.

### 2. Pedidos personalizados y Notas de Taller
- Las lámparas llevan cambios (color de cable, tipo de bombilla) que el catálogo estándar no
  refleja: el vendedor las anota en el pedido y viajan directo a empaque/envío.
- Ciclo de estados auditable: `pending → workshop → shipped → delivered` (`cancelled` repone stock).

### 3. Dashboard de rendimiento (gamificación)
- Ventas e ingresos de hoy y del mes, ranking de vendedores contra su meta, top 3 lámparas y
  tendencia de 14 días en gráficos.
- Alerta de **stock crítico** (umbral configurable) para no vender lo que no hay.

### 4. CRM post-venta
- Recordatorio automático: "el cliente X compró hace 15 días, contactalo".
- Bandeja de seguimiento con detección de vencidos y cierre con resultado.

### 5. Autenticación
- Cuentas de vendedor con contraseñas PBKDF2-SHA256 y sesión JWT (HS256).
- `POST /sales` queda protegida: el vendedor sale del propio token.

---

## Arquitectura

```
┌─────────────────┐      HTTP/JSON      ┌──────────────────────────────────────────┐
│  Frontend       │ ──────────────────► │  Backend FastAPI (app/api/v1)            │
│  Next.js 14     │                     │  ┌───────────┐  ┌─────────────────────┐ │
│  Tailwind +     │  Bearer JWT         │  │ Routes    │  │ PostgreSQL (models) │ │
│  Recharts       │                     │  │ auth/sales│  │ Alembic migrations  │ │
└─────────────────┘                     │  │ products/ │  └─────────────────────┘ │
    :3000                               │  │ dashboard │  ┌─────────────────────┐ │
                                        │  │ followups │  │ Redis               │ │
                                        │  │ shopify   │  │ webhooks + outbound │ │
                                        │  └───────────┘  └─────────────────────┘ │
                                        │         ▲                    ▲          │
                                        └─────────┼────────────────────┼──────────┘
                                                  │                    │ consume
                                        ┌─────────┴──────┐  ┌──────────┴────────┐
                                        │ Shopify OAuth  │  │ Worker            │
                                        │ + GraphQL      │  │ consumer/followup │
                                        └────────────────┘  └───────────────────┘
```

Decisiones clave:
- **GraphQL Admin API** en lugar de REST: menos requests, más datos por operación.
- **Redis como bufé**: webhooks entrantes y ventas salientes se encolan; el worker los procesa
  sin bloquear la API y respeta los rate limits de Shopify (429 / `THROTTLED`) con backoff.
- **Contenedores**: el mismo `docker compose` corre en la laptop, en un VPS o en AWS/Cloud Run.

---

## Stack tecnológico

| Capa | Tecnología |
| --- | --- |
| Infraestructura | Docker + Docker Compose |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 async · Alembic |
| Frontend | Next.js 14 · React 18 · TypeScript · Tailwind CSS · Recharts |
| Base de datos | PostgreSQL 16 |
| Caché / cola | Redis 7 |
| Autenticación | JWT (HS256) · PBKDF2-SHA256 |
| Integración | Shopify Admin GraphQL · OAuth 2.0 · Webhooks |
| CI | GitHub Actions |

---

## Estructura del repositorio

```
shopify-manager/
├── backend/
│   ├── app/
│   │   ├── api/v1/routes/     # auth, sales, products, clients, dashboard, followups, shopify
│   │   ├── core/              # config, database, security, deps, seed
│   │   ├── models/            # SQLAlchemy (5 entidades + eventos + follow_ups)
│   │   ├── schemas/           # Pydantic
│   │   ├── services/shopify/  # client GraphQL, catalog, orders, oauth, security
│   │   └── worker/            # queue, consumer (webhooks+outbound), followup
│   └── alembic/               # migraciones 0001…0006
├── frontend/
│   ├── app/                   # dashboard, /ventas, /pedidos, /productos, /clientes, /login
│   ├── components/            # Sidebar, KpiCard, SalesChart, ventas/*
│   └── lib/                   # api (fetch + JWT), auth (sesión localStorage)
├── docs/API.md                # referencia completa de endpoints
├── infra/Caddyfile            # reverse proxy de ejemplo (HTTPS)
├── PRD.md                     # requerimientos de producto
├── ROADMAP.md                 # plan por fases
├── docker-compose.yml         # entorno local
├── docker-compose.prod.yml    # overrides de producción
└── .github/workflows/ci.yml
```

---

## Cómo empezar (local)

Requisitos: **Docker** + **Docker Compose** (v2).

```bash
git clone <repo-url>
cd shopify-manager

cp .env.example .env

docker compose up --build
```

| Servicio | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Docs OpenAPI (Swagger) | http://localhost:8000/docs |

Cargar los datos demo (vendedores, catálogo con precios, stock crítico):

```bash
make seed
```

Usuario demo: `ana@tienda.com` · contraseña: `secret123`

Comandos útiles con Make:

| Comando | Descripción |
| --- | --- |
| `make up` / `make down` | Levantar / detener el stack |
| `make logs` | Seguir los logs de todos los servicios |
| `make reset` | Detener y borrar volúmenes (pierde datos) |
| `make migrate` | Ejecutar migraciones de Alembic |
| `make seed` | Poblar datos demo |
| `make followup` | Backfill manual de seguimientos post-venta |
| `make check` | Compilar todo el backend (verificación rápida) |

---

## Variables de entorno

| Variable | Descripción | Default |
| --- | --- | --- |
| `SECRET_KEY` | Clave maestra de la app (cámbiala siempre) | `change-me` |
| `POSTGRES_USER/PASSWORD/DB` | Credenciales de PostgreSQL | `shopify` |
| `DATABASE_URL` | DSN de la base (asyncpg) | `postgresql+asyncpg://…` |
| `REDIS_URL` | Conexión a Redis | `redis://redis:6379/0` |
| `SHOPIFY_API_KEY` | Api key de la Custom App | `""` |
| `SHOPIFY_API_SECRET` | Secret de la Custom App | `""` |
| `SHOPIFY_APP_URL` | URL pública de la app (callback OAuth) | `https://…` |
| `SHOPIFY_API_VERSION` | Versión de la Admin API | `2024-10` |
| `LOW_STOCK_THRESHOLD` | Umbral de stock crítico | `5` |
| `FOLLOW_UP_DAYS` | Días hasta el seguimiento post-venta | `15` |
| `JWT_SECRET` | Firma de los tokens | `change-me` |
| `NEXT_PUBLIC_API_URL` | URL de la API vista por el navegador | `http://localhost:8000` |

No commitees `.env` (está en `.gitignore`).

---

## Integración con Shopify

1. Crea una **Custom App** en `https://<tienda>/admin/settings/apps/developers`.
2. Obtén `API key` y `API secret` y rellénalos en `.env`.
3. Registra los webhooks para que la app se actualice en tiempo real:

| Topic | Efecto |
| --- | --- |
| `orders/create` / `orders/updated` | Upsert de cliente y reflejo del pedido en `sales` |
| `products/update` | Re-sincronización del producto (precio, variantes, stock) |

### Flujo OAuth
1. El usuario entra a `GET /api/v1/shopify/install?shop=tienda.myshopify.com`.
2. Shopify redirige a `/api/v1/shopify/callback` → se valida el **HMAC** de la petición.
3. Se intercambia el `code` por access token y se guarda la conexión (`shop_connections`).
4. Se dispara la sincronización inicial del catálogo.

### Rate limits
La Admin GraphQL factura por coste de tokens por operación. El cliente
(`app/services/shopify/client.py`) detecta HTTP `429` y errores `THROTTLED` y espera con
backoff automático. Respeta además `X-Shopify-Shop-Api-Call-Limit`.

---

## Despliegue en producción

```bash
make prod
# equivalente a: docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

El override de producción elimina los volúmenes de desarrollo y el `--reload`, fija
`ENVIRONMENT=production` y deja el stack a la espera de un reverse proxy con HTTPS
(`infra/Caddyfile` incluido) o de la plataforma que prefieras (VPS + Caddy/Traefik,
AWS ECS, Google Cloud Run).

Recuerda en producción: cambiar `SECRET_KEY`/`JWT_SECRET`, definir `POSTGRES_PASSWORD`
real, y apuntar `NEXT_PUBLIC_API_URL` y `SHOPIFY_APP_URL` al dominio público.

---

## API

Documentación interactiva en `/docs` (Swagger/OpenAPI) y referencia escrita en `docs/API.md`.

Resumen de endpoints (`/api/v1`):

| Módulo | Endpoint | Descripción |
| --- | --- | --- |
| Autenticación | `POST /auth/login` · `POST /auth/register` | Sesión JWT |
| Ventas | `POST /sales` | Registro rápido (protegido) |
| Ventas | `GET /sales` | Lista paginada y filtrable, enriquecida con cliente/producto |
| Ventas | `GET · PATCH /sales/{id}` · `/sales/{id}/status` | Detalle y ciclo de estados |
| Ventas | `POST · DELETE /sales/{id}/notes` | Notas de taller |
| Productos | `GET /products/search` | Búsqueda predictiva |
| Dashboard | `GET /dashboard/overview` | KPIs, metas, top 3, stock crítico, tendencia |
| Clientes | `GET /clients` | Búsqueda predictiva |
| Post-venta | `GET /followups` · `PATCH /followups/{id}` | Bandeja y cierre de seguimientos |
| Shopify | `GET /shopify/{install,callback,status}` · `POST /sync` | OAuth y sincronización |
| Shopify | `POST /shopify/webhooks/{topic}` | Recepción de webhooks firmados |

---

## Flujo de datos y workers

```
Webhook de Shopify ─► POST /webhooks/{topic} ─► Redis (shopify:webhooks)
                                                    │
Venta Fast-Entry  ─► POST /sales ─► commit DB ─► Redis (shopify:outbound)
                                                    │
                                            Worker (app.worker.consumer)
                                                    │
              ┌─────────────────┬───────────────────┴──────────────────┐
              ▼                 ▼                                      ▼
        Refleja pedidos    Re-sincroniza producto             Emite draft order en
        (orders)           (products)                         Shopify (venta saliente)
```

El mismo worker ejecuta cada hora `backfill_followups()` para crear los seguimientos
post-venta que falten. Todo el procesamiento es asíncrono para que la API responda
siempre por debajo de 200 ms.

---

## Calidad y CI/CD

GitHub Actions (`ci.yml`) valida en cada push/PR:

1. **infra** — `docker compose config` (local y producción).
2. **backend** — instala dependencias, compila `app/`+`alembic/` e importa la app.
3. **frontend** — `npm install`, `npm run lint`, `npm run build`.

Convenciones aceptadas en el repo:
- Migraciones con Alembic (nunca `create_all` en producción).
- Listas paginadas, consultas indexadas.
- Contraseñas con PBKDF2; tokens con HMAC.
- Verificación local rápida: `make check`.

---

## Roadmap

Estado de las fases en `ROADMAP.md`:

- [x] **F1** Infraestructura y base de datos
- [x] **F2** Integración Shopify (OAuth, catálogo, worker)
- [x] **F3** Registro rápido (Fast-Entry)
- [x] **F4** Pedidos y notas de taller
- [x] **F5** Dashboard y gamificación
- [x] **F6** CRM post-venta
- [x] **F7** Autenticación, seguridad y despliegue

Pendientes anotados: suite de tests (pytest y Vitest), límites estrictos del burst de la
API de Shopify en producción y endurecimiento de autenticación a nivel de proxy.

---

## Documentación

- **PRD.md** — visión de producto y requerimientos.
- **ROADMAP.md** — plan de desarrollo por fases.
- **docs/API.md** — referencia de endpoints y decisiones de integración.
- **infra/Caddyfile** — ejemplo de reverse proxy.

## Licencia

*Sin licencia definida aún — pide al propietario decidir antes de publicarlo público.*
