# API Reference

Base URL: `http://localhost:8000/api/v1` · Docs interactivas: `/docs` (Swagger/OpenAPI)

## autenticación `/auth`

| Endpoint | Descripción |
| --- | --- |
| `POST /auth/register` | Crea vendedor → `{ "email", "full_name", "password", "monthly_target" }` devuelve token JWT |
| `POST /auth/login` | `{ "email", "password" }` → `{ "access_token", "seller", ... }` |

Las rutas protegidas (p. ej. `POST /sales`) exigen `Authorization: Bearer <token>`.
Contraseñas con PBKDF2-SHA256 (120k iteraciones) en `app/core/security.py`.

## ventas `/sales`

### POST /sales → Registro rápido en un solo request (requiere JWT)

```json
{
  "client_email": "cliente@mail.com",
  "product_variant_shopify_id": "gid://shopify/ProductVariant/123",
  "quantity": 1,
  "unit_price": "1299.00",
  "workshop_note": "Cable negro de 2m, sin regulador"
}
```

- El vendedor sale del token JWT (no se recibe `seller_id`).
- Upsert de cliente por email, crea la venta con estado `pending`.
- **Valida stock** → `409 Stock insuficiente` si no alcanza; descuenta stock y recalcula
  `critically_low_stock` del producto.
- Si llega `workshop_note`, crea una `WorkshopNote` vinculada al pedido.
- La venta se encola en `shopify:outbound` y el worker la promueve a **draft order** en
  Shopify (si hay tienda conectada), guardando el `shopify_order_id`.

### GET /sales?page=1&limit=50&seller_id=1&status=pending

Lista paginada y filtrable. Devuelve items enriquecidos (cliente y producto) para las vistas.

### GET /sales/{id} → detalle

Venta + cliente + producto + notas de taller + timeline de estados.

### PATCH /sales/{id}/status → `{ "status": "workshop", "actor": "vendedor" }`

Transición validada con el flujo: `pending → workshop → shipped → delivered` (y `cancelled`).
Un cambio a `cancelled` **repon el stock** de la variante. Cada cambio queda en `sale_status_events`.

### POST /sales/{id}/notes · DELETE /sales/{id}/notes/{note_id}

Notas de taller (especificaciones que viajan a empaque/envío).

### Al pasar a `delivered`

Se crea automáticamente un `FollowUp` con `planned_on = hoy + FOLLOW_UP_DAYS` (15).

## seguimiento post-venta `/followups`

| Endpoint | Descripción |
| --- | --- |
| `GET /followups?status=pending&horizon_days=3` | Bandeja de clientes a contactar (fecha prevista ≤ horizonte). Campos `overdue` marcan vencidos |
| `PATCH /followups/{id}` → `{ "status": "done"\|"skipped", "note": "..." }` | Cierra el seguimiento con resultado |

El worker ejecuta `backfill_followups()` cada hora (crea los que falten para ventas entregadas)
y se puede correr ad-hoc con `python -m app.worker.followup`.

## productos `/products`

- `GET /products/search?q=lampara&limit=10` → búsqueda predictiva (título, variante o SKU).
  Devuelve variantes aplanadas con `price` y `stock` para el Fast-Entry.

## dashboard `/dashboard`

| Endpoint | Descripción |
| --- | --- |
| `GET /dashboard/overview` | KPIs (ventas/ingresos hoy y mes), progreso de metas por vendedor, top 3 lámparas, stock crítico y tendencia de 14 días. Excluye ventas `cancelled` |
| `GET /dashboard/today` | Resumen compacto (ventas de hoy, metas, nº de stock crítico) |
| `GET /dashboard/top-products?seller_id=1&limit=3` | Top lámparas más vendidas |

## clientes `/clients`

- `GET /clients?q=cable&limit=10` → búsqueda predictiva por nombre o email (autocompletado).

## shopify `/shopify`

- `GET /shopify/install?shop=tienda.myshopify.com` → redirige a OAuth de Shopify
  (validación HMAC en el callback vía `services/shopify/security.py`).
- `GET /shopify/callback?shop=...&code=...` → intercambia el `code` por token,
  persiste la conexión (`shop_connections`) y sincroniza el catálogo.
- `POST /shopify/sync` → re-sincroniza el catálogo completo de la primera tienda conectada.
- `GET /shopify/status` → tiendas conectadas.
- `POST /shopify/webhooks/{topic}` → recibe webhooks firmados (HMAC-SHA256 del body,
  header `X-Shopify-Hmac-Sha256`) y los encola en Redis (`shopify:webhooks`).

### Worker (`app/worker/consumer.py`)

Servicio `worker` en docker-compose que drena la cola en bucle:

| Topic | Acción |
| --- | --- |
| `orders/create` / `orders/updated` | Upsert de cliente y reflejo del pedido en `sales` (estado según `financial_status`) |
| `products/update` | Re-sincroniza el producto vía GraphQL (título, variantes, stock) |

Para procesar más topics solo hay que mapearlos en `HANDLERS`.

### Sincronización de catálogo (`services/shopify/catalog.py`)

- GraphQL paginado por cursor (`first:100`), respetando el límite de coste de la API.
- Upsert de productos/variantes/stock; `critically_low_stock` se recalcula con el umbral
  `LOW_STOCK_THRESHOLD` (defecto: 5 unidades).
- El cliente GraphQL (`services/shopify/client.py`) reintenta con backoff en HTTP 429 y
  errores `THROTTLED`.

## Convenciones de calidad

- Todas las listas usan paginación y `LIMIT` (nunca retornar colecciones completas).
- Columnas usadas en `WHERE`/`ORDER BY` están indexadas en los modelos.
- Toda salida a Shopify pasa por `app/services/shopify/client.py` (maneja 429 / rate limits).
- Webhooks se procesan de forma asíncrona vía Redis (`app/worker/queue.py`); el
  worker de proceso (drenar cola + reconsiliar stock/pedidos) lo añade el equipo.