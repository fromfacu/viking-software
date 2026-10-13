# Caso de estudio — Viking Software

## Problema

Un negocio de peluquería necesitaba reemplazar el registro manual de operaciones por una herramienta propia, rápida y resistente a problemas de conectividad.

## Objetivo de la primera etapa

Crear un sistema de escritorio capaz de registrar ventas, identificar al barbero, administrar clientes y gastos, calcular liquidaciones y producir un reporte Excel útil para la gestión.

## Solución

Se desarrolló una aplicación Windows offline-first con Python, CustomTkinter y SQLite. La lógica se separó en modelos, repositorios, servicios e interfaz para evitar que las reglas comerciales quedaran mezcladas con la UI.

## Resultado

La Etapa 1 quedó instalada y operativa en el mostrador. El sistema registra ventas, clientes, propinas y gastos, y convierte esa información en reportes y liquidaciones. La documentación de cierre indica que la operación crítica no depende de internet y que cada entrega fue verificada antes de producción.

## Qué aprendí / qué demuestra

- Diseño de software orientado a un flujo operativo real.
- Modelado de datos relacional con SQLite.
- Migraciones de esquema sin perder datos.
- Separación por capas.
- Validaciones y reglas de negocio.
- Generación de reportes Excel con fórmulas y múltiples hojas.
- Testing de persistencia, servicios y regresiones.
- Diagnóstico y soporte para usuarios no técnicos.
- Desarrollo incremental basado en feedback de uso real.

## Próxima evolución

La arquitectura permite extender el sistema hacia una interfaz móvil/local para barberos, CRM, sincronización con nube y automatizaciones con n8n, manteniendo el escritorio como punto operativo cuando sea la opción más robusta.
