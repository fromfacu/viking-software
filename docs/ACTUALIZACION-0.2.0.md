# Actualización a la versión 0.2.0-beta (Etapa 1.5)

**Fecha:** 2026-10-06
**Sistema:** Viking Software BETA — Peluquería Vikingos
**Aplica sobre:** versión 0.1.0-beta (Etapa 1) ya instalada en `C:\Viking Software BETA`

---

## Qué cambia (en criollo)

1. **Pestaña CAJA (la de siempre), mejorada:**
   - Selector de barbero **obligatorio**: si no elegís quién atiende, la venta
     no se guarda y el sistema te avisa.
   - Cartel grande **"ATIENDE: <NOMBRE>"** para ver de lejos quién está activo.
   - Campos nuevos: **Cliente** (opcional), **Método de pago**
     (Efectivo / Transferencia / Tarjeta / QR Mercado Pago) y **Propina**.
   - La tabla del día ahora muestra barbero, cliente, método y propina.
   - El total del día incluye las propinas y muestra gastos y neto.

2. **Pestaña ADMINISTRACIÓN (nueva, pide clave):**
   - Clave de fábrica: **vikingos** (cámbiala desde el botón "Cambiar clave").
   - **Barberos:** agregar, renombrar, activar/desactivar y eliminar
     (solo se puede eliminar si nunca registró una venta; si tiene ventas,
     el sistema te sugiere desactivarlo para no perder el historial).
   - **Inventario:** agregar, editar, activar/desactivar y eliminar
     servicios y productos del catálogo.
   - **Movimientos:** buscar ventas por fecha y **corregirlas o eliminarlas**
     (el caso típico: una venta cargada al barbero equivocado).
   - **Gastos:** registrar salidas de dinero (insumos, adelantos, etc.).

3. **Reportes Excel (nuevo formato, como el libro JULIO):**
   - Hoja **Registro**: tabla maestra con todas las columnas nuevas.
   - Hoja **Dashboard**: resumen general, por barbero, por método de pago,
     por tipo, gastos, neto y el 50% de referencia para el reparto.
   - **Una hoja por barbero** ("Resumen Juliano", "Resumen Alexander", etc.)
     con bloques por día (LUNES, MARTES...), columnas MONTO y PROPINA,
     TOTAL por día con fórmulas `=SUM`, y cierre con TOTAL FACTURADO,
     PROPINAS DEL PERÍODO y TOTAL CON PROPINAS.

## Cómo actualizar (paso a paso)

1. Cerrá Viking Software si está abierto.
2. Copiá el contenido del ZIP **encima** de `C:\Viking Software BETA`
   (reemplazá los archivos cuando Windows pregunte).
   - **NO borres la carpeta `datos`**: ahí está tu base de datos con las
     ventas que ya registraste.
3. Abrí el programa como siempre (doble clic en el acceso directo o
   ejecutar `main.py`).
4. La primera vez, el sistema actualiza la base de datos solo (migración
   automática v1 → v2). Tus ventas anteriores quedan intactas, con barbero
   "—" (sin asignar). Si querés, asignalas desde Administración → Movimientos.
5. Verificación rápida: pestaña CAJA debe mostrar el selector de barbero
   y el cartel "SIN BARBERO SELECCIONADO"; la pestaña ADMINISTRACIÓN debe
   pedir clave (`vikingos`).

## Si algo sale mal

- El programa no abre o da error → restaurá el respaldo: antes de actualizar,
  Windows guarda tu versión vieja si hiciste copia de la carpeta. También
  podés volver a correr `INSTALAR.bat`.
- Las pruebas automáticas se pueden correr con `python test_manual.py`:
  debe decir **TODAS LAS PRUEBAS PASARON**.

## Detalle técnico (para soporte)

| Tema | Detalle |
|------|---------|
| Versión | 0.2.0-beta (esquema de base de datos v2) |
| Migración | Automática e idempotente al arrancar: crea tablas `barberos`, `gastos`, `config` y agrega a `ventas` las columnas `barbero_id`, `cliente`, `metodo_pago`, `propina` (ALTER TABLE condicional vía `PRAGMA table_info`) |
| Compatibilidad | Las ventas de la Etapa 1 se conservan; barbero queda "—" hasta asignarlo |
| Clave admin | Se guarda como hash SHA-256 en la tabla `config`; nunca en texto plano |
| Nuevas clases | `Barbero`, `Gasto`, `MetodoPago` en modelos; `BarberoRepository`, `GastoRepository`, `ConfigRepository` en datos; `GastoService`, `AdminService` en servicios |
| Sin dependencias nuevas | Mismos requisitos: customtkinter, openpyxl, Pillow |
