# Actualización a la versión 0.4.0-beta (Etapa 1.7)

**Fecha:** 2026-10-08
**Sistema:** Viking Software BETA — Peluquería Vikingos
**Aplica sobre:** versión 0.3.0-beta ya instalada en `C:\Viking Software BETA`

---

## Qué cambia (en criollo)

1. **Base de CLIENTES (Administración → CLIENTES):**
   - Se cargan los clientes con **NOMBRE, APELLIDO, CELULAR y MAIL**
     (el mail es opcional).
   - El **CELULAR** es el dato que identifica a cada cliente: no puede
     repetirse. Es el número con que el sistema arma las estadísticas.
   - Si eliminás un cliente, las ventas que ya tenía **conservan su
     nombre** en el historial y en los reportes viejos.

2. **Autocompletado en la caja:**
   - En el campo CLIENTE de la caja ahora se puede **escribir**: apenas
     tipeás unas letras (ej.: «RICH») el sistema **sugiere los clientes
     cargados** que coinciden (por nombre, apellido, celular o mail).
   - Con un clic (o Enter) sobre la sugerencia, el campo se completa solo
     y la venta queda **vinculada a esa ficha**.
   - Si el cliente no tiene ficha, podés dejar **MOSTRADOR** (como antes)
     o escribir el nombre suelto, sin ficha.
   - «— MOSTRADOR —» aparece como **texto guía** atenuado: al seleccionar
     el campo (o empezar a escribir) desaparece solo, sin borrarlo a mano.
   - El resto de las listas (barbero, descripción, método de pago, moneda)
     siguen siendo de **solo selección**: no admiten escritura.

3. **Detector de errores de tipeo (clientes):**
   - Si al cargar un cliente el **NOMBRE + MAIL ya existen** pero el
     **CELULAR es distinto**, el sistema frena y pregunta si fue un
     **error de tipeo**:
     - **SÍ** → corrige la ficha existente con el celular nuevo.
     - **NO** → entiende que es otra persona y crea la ficha nueva.
     - **CANCELAR** → no guarda nada.
   - Lo mismo avisa al editar una ficha hacia datos de otra.

4. **Hoja CLIENTES en el reporte Excel:**
   - Nueva pestaña **«Clientes»** con las estadísticas del período de
     cada cliente, **identificado por su celular**: operaciones, total
     gastado, propinas, ticket promedio y última visita.
   - Las ventas sin ficha se agrupan al final en
     **«SIN IDENTIFICAR (MOSTRADOR)»**, y cierra el **TOTAL GENERAL**.

5. **MONEDA del sistema (Administración → MÉTODOS Y MONEDA):**
   - Se elige el símbolo de la moneda ($, G$, USD, R$, €) y **todo el
     sistema** pasa a mostrar los importes con ese símbolo: pantalla,
     tabla del día, administración y **el Excel exportado**.
   - **No convierte ni cotiza valores**: solo cambia cómo se leen los
     importes. Ej.: con G$ todo se lee «G$ 60.000,00».

6. **MODO OSCURO / MODO CLARO:**
   - Botón nuevo en la cabecera (☀ / ☾) que alterna toda la paleta.
   - La elección **queda guardada**: al abrir el programa arranca con el
     último modo elegido.

## Cómo actualizar (paso a paso)

1. Cerrá Viking Software si está abierto.
2. Copiá el contenido del ZIP **encima** de `C:\Viking Software BETA`
   (reemplazá los archivos cuando Windows pregunte).
   - **NO borres la carpeta `datos`**: ahí está tu base de datos con las
     ventas que ya registraste.
3. Abrí el programa como siempre (doble clic en el acceso directo o
   ejecutar `main.py`).
4. La primera vez, el sistema actualiza la base de datos solo (migración
   automática → v4): crea la tabla de clientes (vacía) y deja tus ventas
   históricas intactas.
5. Verificación rápida:
   - En CAJA, el campo CLIENTE permite escribir y sugiere fichas.
   - En ADMINISTRACIÓN aparecen las sub-pestañas **CLIENTES** y
     **MÉTODOS Y MONEDA** (con el selector de moneda).
   - En la cabecera está el botón **MODO CLARO / MODO OSCURO**.
   - El reporte exportado incluye la hoja **Clientes**.

## Si algo sale mal

- El programa no abre o da error → restaurá el respaldo de la carpeta y
  avisá a soporte. También podés volver a correr `INSTALAR.bat`.
- Las pruebas automáticas se pueden correr con `python test_manual.py`:
  debe decir **TODAS LAS PRUEBAS PASARON**.

## Detalle técnico (para soporte)

| Tema | Detalle |
|------|---------|
| Versión | 0.4.0-beta (esquema de base de datos v4) |
| Migración | Automática e idempotente al arrancar desde v1/v2/v3: crea la tabla `clientes` (`celular TEXT NOT NULL COLLATE NOCASE UNIQUE`, `mail` opcional) y agrega `ventas.cliente_id INTEGER REFERENCES clientes(id)` + índice (`PRAGMA table_info` + ALTER condicional; `PRAGMA user_version = 4`) |
| Clientes | `ClienteRepository` (ABM + `buscar` parcial con comodines LIKE escapados + `buscar_por_nombre_y_mail` exacto NOCASE). La venta vinculada desnormaliza el nombre; al eliminar un cliente, `cliente_id` → NULL y el texto queda |
| Autocompletado | `ComboAutocompletable` (CTkComboBox con `<KeyRelease>`): filtra contra la base en cada tecla y devuelve el foco al campo para no cortar el tipeo. Caja y diálogo de edición de movimientos |
| Detector de tipeo | `AdminService` lanza `ClientePosibleDuplicado` cuando nombre + mail coinciden y el celular no; la UI consulta (corregir existente / forzar alta / cancelar). `forzar=True` omite la sospecha. Sin mail no aplica |
| Moneda | `config("moneda_simbolo")`, catálogo `("$", "G$", "USD", "R$", "€")`; `formato_moneda` y `formato_celda_moneda('"G$" #,##0.00')` en pantalla y Excel. El exportador lee el símbolo al momento de exportar |
| Tema | Paletas `TEMAS["oscuro"/"claro"]` con tokens reasignados por `aplicar_tema()`; persistido en `config("tema")`; el cambio reconstruye la interfaz conservando barbero y método |
| Exportación | Hojas: Registro → Dashboard → **Clientes** → Resumen por barbero. Clientes: registrados por id, históricos por texto, mostrador agrupado al final + TOTAL GENERAL. Anchos de columnas de importes ampliados para montos de 6 cifras con símbolo |
| Sin dependencias nuevas | Mismos requisitos: customtkinter, openpyxl, Pillow |
