# Actualización a la versión 0.4.1-beta (hotfix de la Etapa 1.7)

**Fecha:** 2026-10-08
**Sistema:** Viking Software BETA — Peluquería Vikingos
**Aplica sobre:** versión 0.4.0-beta ya instalada en `C:\Viking Software BETA`

---

## Qué cambia (en criollo)

**El «— MOSTRADOR —» del campo CLIENTE ya no molesta para escribir.**
Antes quedaba escrito como texto fijo dentro del campo y había que
borrarlo a mano antes de tipear el nombre del cliente. Ahora es un
**texto guía** (se ve atenuado con el campo vacío) y **desaparece solo
al seleccionar el campo o empezar a escribir**. Si el campo queda vacío,
la venta se registra como MOSTRADOR, igual que antes.

No cambia nada más: la base de datos, los clientes cargados, la moneda
y el tema quedan exactamente como están.

## Cómo actualizar (paso a paso)

1. Cerrá Viking Software si está abierto.
2. Copiá el contenido del ZIP **encima** de `C:\Viking Software BETA`
   (reemplazá los archivos cuando Windows pregunte).
   - **NO borres la carpeta `datos`**: ahí está tu base de datos con las
     ventas y los clientes que ya registraste.
3. Abrí el programa como siempre. No hay migración: el esquema de la
   base es el mismo de la 0.4.0 (v4).
4. Verificación rápida: en CAJA, el campo CLIENTE muestra
   «— MOSTRADOR —» atenuado; al tocar el campo desaparece y podés
   escribir directo (ej.: «RICH») para ver las sugerencias.

## Si algo sale mal

- El programa no abre o da error → restaurá el respaldo de la carpeta y
  avisá a soporte. También podés volver a correr `INSTALAR.bat`.
- Las pruebas automáticas se pueden correr con `python test_manual.py`:
  debe decir **TODAS LAS PRUEBAS PASARON**.

## Detalle técnico (para soporte)

| Tema | Detalle |
|------|---------|
| Versión | 0.4.1-beta (esquema de base de datos v4, sin cambios) |
| Cambio | `ComboAutocompletable` acepta `placeholder_text` y lo aplica al entry interno: «— MOSTRADOR —» es texto guía que se oculta al enfocar/escribir; campo vacío = MOSTRADOR. El reset tras registrar deja el campo vacío (el guía reaparece solo) |
| Sin dependencias nuevas | Mismos requisitos: customtkinter, openpyxl, Pillow |
