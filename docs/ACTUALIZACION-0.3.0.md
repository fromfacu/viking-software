# Actualización a la versión 0.3.0-beta (Etapa 1.6)

**Fecha:** 2026-10-07
**Sistema:** Viking Software BETA — Peluquería Vikingos
**Aplica sobre:** versión 0.2.x-beta ya instalada en `C:\Viking Software BETA`

---

## Qué cambia (en criollo)

1. **Logo oficial:** la interfaz y los reportes Excel ahora muestran el
   logo VK oficial (el de la carpeta `assets`), sin deformarse.

2. **Textos en MAYÚSCULAS:** todos los rótulos, botones, mensajes y
   encabezados de la interfaz se muestran en mayúsculas.

3. **Campos más grandes y listas de solo selección:**
   - Los campos y botones de la caja y de Administración son más altos y
   anchos, con letra más grande, para leerlos mejor a distancia.
   - Las listas validadas (barbero, descripción, método de pago, tipo)
   **ya no admiten escribir a mano**: solo se elige de la lista. Así no
   quedan ventas con textos inventados fuera del catálogo.

4. **Comisión por barbero (Administración → BARBEROS):**
   - Campo nuevo **COMISIÓN %**: al agregar un barbero o con el botón
   **GUARDAR COMISIÓN** sobre la fila seleccionada. Ejemplo: Alexander 10.
   - En el reporte Excel, la hoja **"Resumen <Barbero>"** ahora cierra con
   el bloque **LIQUIDACIÓN DEL BARBERO**:
     - COMISIÓN PACTADA (% SOBRE LO FACTURADO) — celda **editable**: si la
       cambiás en el Excel, todo se recalcula solo.
     - COMISIÓN A PAGAR = % × TOTAL FACTURADO (**sin contar propinas**).
     - PROPINAS (100 % DEL BARBERO).
     - TOTAL A LIQUIDAR (COMISIÓN + PROPINAS).
   - El **Dashboard** suma la columna **A LIQUIDAR** por barbero.

5. **Métodos de pago administrables (Administración → MÉTODOS DE PAGO):**
   - Se pueden **agregar** (ej.: BILLETERA VIRTUAL) o **eliminar**
   (ej.: QR / MERCADO PAGO) medios de cobro.
   - Las ventas ya registradas **conservan** el método con que se cobraron.
   - Protección: la caja siempre necesita al menos un método; el sistema
   no deja eliminar el último.

6. **Corrección de errores:**
   - INVENTARIO ahora acepta el precio al agregar o modificar ítems
   (antes rechazaba cualquier precio por un orden de datos invertido).
   - El botón ELIMINAR del Inventario funciona (antes no hacía nada).

## Cómo actualizar (paso a paso)

1. Cerrá Viking Software si está abierto.
2. Copiá el contenido del ZIP **encima** de `C:\Viking Software BETA`
   (reemplazá los archivos cuando Windows pregunte).
   - **NO borres la carpeta `datos`**: ahí está tu base de datos con las
   ventas que ya registraste.
3. Abrí el programa como siempre (doble clic en el acceso directo o
   ejecutar `main.py`).
4. La primera vez, el sistema actualiza la base de datos solo (migración
   automática v2 → v3): los barberos existentes quedan con **comisión
   50 %** (el reparto histórico) hasta que la ajustes, y los métodos de
   pago quedan como antes (EFECTIVO / TRANSFERENCIA / TARJETA /
   QR / Mercado Pago).
5. Verificación rápida: en CAJA, la descripción se elige de la lista (no
   se puede escribir); en ADMINISTRACIÓN → BARBEROS aparece la columna
   COMISIÓN % y el botón GUARDAR COMISIÓN; existe la sub-pestaña
   MÉTODOS DE PAGO.

## Si algo sale mal

- El programa no abre o da error → restaurá el respaldo de la carpeta y
  avisá a soporte. También podés volver a correr `INSTALAR.bat`.
- Las pruebas automáticas se pueden correr con `python test_manual.py`:
  debe decir **TODAS LAS PRUEBAS PASARON**.

## Detalle técnico (para soporte)

| Tema | Detalle |
|------|---------|
| Versión | 0.3.0-beta (esquema de base de datos v3) |
| Migración | Automática e idempotente al arrancar: `barberos` gana la columna `comision REAL NOT NULL DEFAULT 50.0 CHECK (0–100)` y se crea la tabla `metodos_pago` con semilla (ALTER/CREATE condicional vía `PRAGMA table_info` + `CREATE TABLE IF NOT EXISTS`) |
| Métodos de pago | Ya no son un enum fijo: son filas de `metodos_pago` (`UNIQUE COLLATE NOCASE`). La caja valida y guarda la escritura canónica; las ventas históricas conservan el texto original |
| Comisión | `Barbero.comision` (0–100). Liquidación en el export con fórmulas vivas: `COMISIÓN = ROUND(TOTAL_FACTURADO × %, 2)` y `TOTAL A LIQUIDAR = COMISIÓN + PROPINAS`; el % queda en celda editable con formato `0.00%` |
| Correcciones | `PestañaInventario` llama a `AdminService.agregar_item/actualizar_item` con parámetros por nombre (bug del precio); se agrega `AdminService.eliminar_item` (el botón ELIMINAR lo llamaba y no existía) |
| Interfaz | Textos fijos en MAYÚSCULAS; listas validadas `state="readonly"`; fuente base 15, campos de 44 px y desplegables con letra grande |
| Sin dependencias nuevas | Mismos requisitos: customtkinter, openpyxl, Pillow |
