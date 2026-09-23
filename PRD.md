# PRD — Sistema de Gestión Integral para Ventas de Lámparas (Shopify Ecosystem)

**Documento de Requerimientos Técnicos y Estratégicos para el equipo de desarrollo.**

---

## 1. Visión del Producto

El objetivo no es replicar el panel de Shopify, sino crear una capa de inteligencia operativa situada entre el inventario de Shopify y la realidad del vendedor. El sistema debe eliminar la fricción en el registro de ventas, el seguimiento de pedidos personalizados y la gestión de clientes, permitiendo que el vendedor pase menos tiempo llenando formularios y más tiempo vendiendo.

## 2. Arquitectura Técnica Requerida

Para cumplir con la exigencia de ejecución Local y Externa (Nube), el equipo debe implementar una arquitectura de Contenedores.

- **Infraestructura:** Docker & Docker Compose (Obligatorio). Esto garantiza que el entorno sea idéntico en la laptop del desarrollador, en un servidor local o en AWS/Google Cloud/Azure.
- **Backend:** Node.js (NestJS) o Python (FastAPI). Se busca un lenguaje con tipado fuerte y alta eficiencia en el manejo de APIs asíncronas.
- **Frontend:** React.js o Next.js con Tailwind CSS. El diseño debe ser "Admin-First": limpio, modo oscuro/claro, con dashboards basados en KPIs y carga instantánea.
- **Base de Datos:** PostgreSQL. Necesitamos integridad relacional para los registros de ventas y clientes.
- **Caché/Cola:** Redis. Para optimizar la sincronización con Shopify y evitar bloqueos por límites de tasa (Rate Limits) de la API.

## 3. Parámetros de Integración con Shopify

El equipo debe utilizar la **Shopify Admin API (GraphQL)** por encima de la REST API para optimizar el consumo de datos y la velocidad de respuesta.

- **Webhooks:** Implementar Webhooks para que cualquier cambio en Shopify (nuevo pedido, cambio de inventario) se refleje en la App en tiempo real sin necesidad de refrescar.
- **Autenticación:** OAuth 2.0 para la conexión segura con la tienda.

## 4. Módulos Críticos (Solucionando el "Dolor" del Vendedor)

### A. Módulo de "Registro Rápido" (Fast-Entry)

- **El Problema:** Los vendedores odian los formularios largos.
- **La Solución:** Interfaz de "One-Click". Buscador predictivo de lámparas, selección de variantes rápidas y autocompletado de datos de clientes mediante integración con la base de datos de Shopify.

### B. Gestión de Pedidos Especiales/Personalizados

- **El Problema:** Las lámparas a veces llevan cambios (color de cable, tipo de bombilla) que Shopify no maneja bien en el registro estándar.
- **La Solución:** Un sistema de "Notas de Taller" vinculado al pedido, donde el vendedor pueda añadir especificaciones técnicas que viajen directamente al equipo de empaque/envío.

### C. Dashboard de Rendimiento del Vendedor (Gamificación)

- **El Problema:** El vendedor no sabe cuánto le falta para su meta en tiempo real.
- **La Solución:** Un tablero visual con:
  - Ventas del día vs. Meta mensual.
  - Top 3 lámparas más vendidas por el vendedor.
  - Alertas de "Stock Crítico" para que el vendedor no venda algo que no hay.

### D. CRM de Seguimiento Post-Venta

- **El Problema:** Se pierde el contacto con el cliente una vez que se entrega la lámpara.
- **La Solución:** Un recordatorio automático para el vendedor: "El cliente X compró una lámpara hace 15 días, contactalo para saber si quedó satisfecha con la instalación".

## 5. Estándares de Calidad (Non-Negotiables)

1. **Optimización del Backend:**
   - Implementar Pagination y Lazy Loading en todas las listas.
   - Cualquier consulta a la base de datos debe estar indexada.
   - Tiempo de respuesta de la API < 200ms.
2. **Estética del Frontend:**
   - Diseño basado en componentes (Atomic Design).
   - Experiencia de usuario (UX) optimizada para tablets y laptops (donde suelen estar los vendedores).
   - Uso de librerías de visualización de datos modernas (ej. Recharts o Chart.js).
3. **Despliegue:**
   - Pipeline de CI/CD (GitHub Actions o GitLab CI).
   - Documentación completa de la API (Swagger/OpenAPI).

---

## 💡 Consejo Final de Mentor (para el Dueño)

Cuando el equipo te presente los avances, no preguntes "¿Ya funciona?". Pregunta: "Muéstrame cómo un vendedor registra una venta en menos de 30 segundos".

La clave del éxito de esta aplicación no está en la tecnología (que es el medio), sino en la reducción de clics. Si el vendedor siente que la herramienta le facilita la vida y no que es "más trabajo administrativo", la adoptarán y tus ventas subirán porque ellos estarán más enfocados en el cliente y menos en la computadora.