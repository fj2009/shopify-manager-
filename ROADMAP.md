# Roadmap de desarrollo

Plan por fases. Cada fase termina con algo utilizable y verificable; el orden protege las
dependencias (no se construye UI sin API estable, ni API sin DB migrada).

## Fase 1 — Infraestructura y base de datos
- [x] Migraciones con Alembic (reemplaza `create_all`) y auto-migración al arrancar
- [x] Seed idempotente de datos demo (vendedores, catálogo, stock crítico)
- [x] Makefile con `migrate` y `seed`; compose actualizado

## Fase 2 — Integración con Shopify
- [x] OAuth completo (install → callback → intercambio de token)
- [x] Persistencia de tienda + access token
- [x] Sincronización de catálogo: productos, variantes, stock (GraphQL con rate-limit)
- [x] Worker que drena la cola de webhooks: `orders/create`, `products/update`

## Fase 3 — Registro rápido (Fast-Entry)
- [x] Venta en un solo request: buscador predictivo de lámparas + autocompletado de cliente
- [x] Descuento de stock en local y confirmación opcional del pedido en Shopify
- [x] Página `/ventas` del frontend funcional

## Fase 4 — Pedidos y notas de taller
- [x] Ciclo de estados: `pending → workshop → shipped → delivered`
- [x] CRUD de notas de taller por pedido (visibles para empaque/envío)
- [x] Página `/pedidos` con timeline

## Fase 5 — Dashboard de rendimiento (gamificación)
- [x] Métricas: día vs meta mensual, top productos, stock crítico, tendencia
- [x] Gráficos (Recharts) y tabla de ranking de vendedores

## Fase 6 — CRM post-venta
- [x] Tabla de follow-ups con fecha óptima (entrega + 15 días)
- [x] Worker de programación de recordatorios
- [x] Bandeja de seguimiento en frontend

## Fase 7 — Autenticación, seguridad y despliegue
- [x] Login JWT para vendedores + RBAC
- [x] CI/CD de build, lint y tests
- [x] Docker Compose de producción (worker como servicio propio, HTTPS, secrets)

## Criterio de "fase terminada"
El backend compila (`python -m compileall app`), el compose valida (`docker compose config`),
y ninguna ruta queda sin su contrato en `docs/API.md`.