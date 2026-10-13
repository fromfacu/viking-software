# ACTUALIZACIÓN 0.4.2-beta — “El programa no abre” + guía más robusta

> Aplica sobre: **0.4.0-beta o 0.4.1-beta**. No toca la base de datos
> (sigue siendo esquema v4): **no se pierde ni una venta ni un cliente**.

## Por qué salió esta versión

Después de aplicar la 0.4.1 el programa dejó de abrir en la notebook.
La 0.4.1 introdujo el texto guía «— MOSTRADOR —» usando una función del
campo de texto que **no existe igual en todas las variantes de
CustomTkinter**: si la variante instalada no la soporta, el programa
falla al construir la pantalla. Como el acceso directo abre **sin
consola** (pythonw.exe), ese fallo era invisible: doble clic y no pasaba
nada.

## Qué se corrigió

1. **Texto guía a prueba de versiones.** El «— MOSTRADOR —» primero
   intenta usar la guía nativa del campo; si la variante de CustomTkinter
   no la soporta, pasa automáticamente a una **guía manual** (texto
   atenuado que desaparece al seleccionar el campo). Con cualquiera de
   las dos, el comportamiento es el mismo: no es texto sólido, no hay que
   borrarlo a mano y no interrumpe la escritura.

2. **Captura de errores fatales al abrir.** Si el programa falla al
   arrancar, ahora:
   - el detalle técnico queda en `logs\viking.log`, y
   - salta un **cartel** avisando que no pudo abrirse, con instrucciones.

3. **Nuevo `DIAGNOSTICO.bat`** (doble clic, en la carpeta del programa).
   Abre el programa con consola visible y junta toda la evidencia en
   `logs\diagnostico.txt` (versión de Windows, salida del programa y
   últimas líneas del log). Al terminar abre ese archivo con el Bloc de
   notas: **se manda completo (o una foto) a soporte**.

## Cómo actualizar

Igual que siempre: descomprimir el ZIP **encima** de la carpeta
`C:\Viking Software BETA` y reemplazar todo. Las carpetas `datos`,
`logs` y `exportaciones` no vienen en el ZIP, así que nada se toca.

## Detalle técnico

| Pieza | Cambio |
|---|---|
| `viking/interfaz.py` | `ComboAutocompletable`: guía nativa con *fallback* manual (FocusIn/FocusOut); métodos `set()` y `limpiar()` seguros |
| `main.py` | `try/except` global: `log.exception("ERROR FATAL…")` + cartel con `tkinter.messagebox` |
| `DIAGNOSTICO.bat` | Nuevo: diagnóstico de un doble clic hacia `logs\diagnostico.txt` |
| Esquema de datos | Sin cambios (v4) |
