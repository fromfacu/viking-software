# ACTUALIZACIÓN 0.5.0-beta — Adelantos, Balance en el Excel y nacimiento de clientes

> Aplica sobre: **0.4.x-beta**. Al abrir, la base migra sola del esquema
> v4 al **v5** (se crea la tabla `adelantos` y se agrega
> `clientes.fecha_nacimiento`): **no se pierde ni una venta, ni un
> cliente, ni un barbero**.

## Qué trae esta versión

1. **ADELANTOS a los barberos** (Administración → BARBEROS, panel
   derecho). Seleccionás al barbero, escribís el MONTO y —si querés— una
   NOTA («A cuenta de sueldo»), y pulsás **REGISTRAR ADELANTO**. La fecha
   y hora las pone el sistema solas.
   - El adelanto es un **egreso de caja**: sale en la hoja **BALANCE**
     del reporte.
   - Además se **descuenta del NETO A COBRAR** del barbero en su hoja de
     liquidación del Excel (no se pierde: vuelve cuando liquidás).
   - ¿Lo cargaste mal? Seleccionás la fila y **ELIMINAR ADELANTO**.

2. **Hoja BALANCE en el reporte Excel** (entre DASHBOARD y CLIENTES):
   la caja del período en una mirada —
   **INGRESOS** (ventas + propinas cobradas) − **EGRESOS** (gastos +
   adelantos) = **BALANCE**. Abajo va el detalle de cada adelanto con
   fecha, barbero, monto y nota. Si el balance da negativo, se muestra
   en rojo.

3. **NETO A COBRAR en la hoja de cada barbero:** bloque nuevo
   ADELANTOS DEL PERÍODO y cierre **NETO A COBRAR = LIQUIDACIÓN −
   ADELANTOS**. Son fórmulas vivas: si editás el % de comisión en el
   Excel, todo se recalcula solo. Si un barbero no vendió nada pero
   recibió adelantos, igual tiene hoja en el reporte.

4. **Fecha de NACIMIENTO del cliente** (Administración → CLIENTES):
   campo opcional en formato DD/MM/AAAA. Se normaliza sola
   («5/8/1990» → «05/08/1990») y rechaza fechas que no existen o que
   son futuras. Aparece en la tabla y en la hoja CLIENTES del reporte.
   Es la base para el CRM de la Etapa 2 (cumpleaños, campañas).

5. **MODO CLARO rediseñado en colores pasteles:** las pestañas, las
   listas desplegables y los campos ahora tienen fondos claros con letra
   oscura legible (contraste medido, nivel WCAG AA). El **modo oscuro
   queda exactamente igual** que antes.

6. **La semilla carga solo al dueño.** Una instalación nueva crea un
   único barbero: **Juliano** (propietario). Los empleados —como
   Alexander— se agregan desde Administración → BARBEROS con su % de
   comisión. Las bases ya instaladas conservan los barberos que tienen.

## Cómo actualizar

Igual que siempre: descomprimir el ZIP **encima** de la carpeta
`C:\Viking Software BETA` y reemplazar todo. Las carpetas `datos`,
`logs` y `exportaciones` no vienen en el ZIP, así que nada se toca.
Al abrir, el programa migra la base a v5 automáticamente.

## Detalle técnico

| Pieza | Cambio |
|---|---|
| `viking/modelos.py` | `Cliente` con `fecha_nacimiento`; dataclass nuevo `Adelanto` (uuid, monto, nota, fecha del sistema) |
| `viking/base_datos.py` | Esquema v5: tabla `adelantos` (índices por fecha y barbero) + columna `clientes.fecha_nacimiento`; migración idempotente v1/v2 → v5; semilla de barberos = solo Juliano; `AdelantoRepository` (alta, baja, listados y total por rango, con desempate por id) |
| `viking/servicios.py` | `registrar_adelanto` / `eliminar_adelanto` con validaciones en 3 bloques; nacimiento validado (formato real, no futuro, normalizado DD/MM/AAAA); exportador con hoja **BALANCE**, bloque **ADELANTOS + NETO A COBRAR** en la hoja del barbero y columna **NACIMIENTO** en CLIENTES |
| `viking/interfaz.py` | Panel de adelantos en BARBEROS (carga + historial); campo NACIMIENTO en CLIENTES; paleta MODO CLARO pastel legible (fichas y desplegables con colores propios por tema); corrección: la tabla de barberos conserva la selección al refrescar |
| `main.py` | Cableado del repositorio de adelantos; versión 0.5.0-beta |
| Verificación | Suite automática (18 grupos) + pruebas de interfaz en entorno gráfico virtual (adelantos, nacimiento, ambos temas) + render visual del Excel exportado |
| Esquema de datos | **v4 → v5** automático al abrir |
