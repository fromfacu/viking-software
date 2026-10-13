# ACTUALIZACIÓN 0.4.3-beta — La lista de clientes ya no frena la escritura

> Aplica sobre: **0.4.0-beta, 0.4.1-beta o 0.4.2-beta**. No toca la base
> de datos (sigue siendo esquema v4): **no se pierde ni una venta ni un
> cliente**.

## Por qué salió esta versión

Al escribir en el campo CLIENTE (ej.: la letra «m» habiendo un cliente
«Maxi») se abría la lista de sugerencias y **no dejaba seguir
escribiendo**. La causa: el campo usaba el desplegable interno del
ComboBox y, según la versión de CustomTkinter instalada, ese desplegable
es un **menú nativo** que al abrirse captura el teclado (para navegar el
menú con las flechas) — las teclas siguientes iban al menú, no al campo.

## Qué se corrigió

1. **Lista de sugerencias propia.** El campo CLIENTE ahora muestra sus
   sugerencias en una lista flotante hecha a medida que **nunca toma el
   teclado**: se puede seguir tipeando con la lista abierta y la lista se
   va refinando sola (m → «Gómez, Maxi…»; ma → solo «Maxi»).
   - Elegir con **clic**, o con **↓ / ↑ + Enter**.
   - **Escape** la cierra sin borrar lo escrito; **Tab** la cierra y pasa
     al siguiente campo.
   - Se cierra sola al ir a otro campo, cambiar de pestaña o cambiar de
     tema (nunca queda una ventanita suelta en pantalla).

2. **Cero dependencia de los internals de CustomTkinter.** El widget ya
   no toca piezas internas del ComboBox (el origen de los bugs 0.4.1 y
   0.4.2): usa solo tkinter estándar, idéntico en todas las versiones.

3. Sin cambios en el resto: el texto guía «— MOSTRADOR —», el
   autocompletado por nombre/apellido/celular/mail, el vínculo de la
   venta a la ficha y el detector de tipeos funcionan igual que antes.

## Cómo actualizar

Igual que siempre: descomprimir el ZIP **encima** de la carpeta
`C:\Viking Software BETA` y reemplazar todo. Las carpetas `datos`,
`logs` y `exportaciones` no vienen en el ZIP, así que nada se toca.

## Detalle técnico

| Pieza | Cambio |
|---|---|
| `viking/interfaz.py` | `ComboAutocompletable` reescrito: ahora es un `CTkFrame` con `CTkEntry` + lista propia (`Toplevel` + `Listbox` de tkinter puro); foco siempre en el campo; candado anti-robo de foco; cierre por Escape/Tab/FocusOut/Unmap/Destroy |
| Verificación | Probado con entorno gráfico virtual: 20/20 pruebas del widget + caso real (escribir «maxi» con el cliente Maxi cargado) |
| Esquema de datos | Sin cambios (v4) |
