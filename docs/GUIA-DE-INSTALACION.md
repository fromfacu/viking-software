# Guía de Instalación Paso a Paso — Viking Software BETA · Etapa 1

**Código:** VIK-ERP-BETA-001 · **Versión:** 0.1.0-beta
**Equipo destino:** LAPTOP-ECIR5J2E (usuario JULIANO) — Windows 11 Home 64-bit
**Carpeta del sistema:** `C:\Viking Software BETA`
**Tiempo estimado total:** 20 minutos

Hay dos caminos. El **Camino A (automático)** hace casi todo solo; el
**Camino B (manual)** muestra cada paso para entender qué se está instalando.
Elegí uno solo.

---

## Camino A — Instalación automática (recomendado)

### Paso 1 · Instalar Python 3.12

1. Entrá a [python.org/downloads](https://www.python.org/downloads/) y descargá
el **«Windows installer (64-bit)»** de Python **3.12 o superior**
(si ya tenés 3.13 o 3.14 instalado, sirve igual: saltá al paso 3).
2. Ejecutalo y **marcá la casilla `Add python.exe to PATH`** antes de pulsar
*Install Now*. Sin esa casilla, todo lo demás falla.
3. Verificá: tecla **Windows** → escribí `cmd` → Enter → tipeá:

```bat
   python --version
```

Resultado esperado: `Python 3.12.x` o superior.

> **SQLite no se instala aparte:** viaja embebido dentro de Python. Lo mismo
> Tkinter. Los únicos paquetes externos son los 3 de `requirements.txt`.

### Paso 2 · Copiar la carpeta del sistema

Copiá la carpeta entera **`Viking Software BETA`** (la que contiene
`main.py`, `INSTALAR.bat`, la subcarpeta `viking\`, etc.) a la raíz del disco,
para que quede exactamente así:

```javascript
C:\Viking Software BETA\
├── INSTALAR.bat
├── main.py
├── test_manual.py
├── requirements.txt
├── assets\logo_vk.png
├── viking\
├── datos\            (vacía: la base se crea sola)
├── exportaciones\    (vacía: aquí caen los reportes)
├── logs\
└── docs\
```

> La carpeta tiene un espacio en el nombre: todos los comandos de esta guía
> ya vienen con las comillas necesarias. No las quites.

### Paso 3 · Ejecutar el instalador

Doble clic en **`C:\Viking Software BETA\INSTALAR.bat`**.

El instalador hace, en orden: verificar Python → crear el entorno virtual →
instalar las 3 dependencias → correr la prueba automática del sistema →
crear el acceso directo **«Viking Software»** en el escritorio.

Cuando diga `INSTALACION COMPLETA`, seguí en el **Paso 4**.

---

## Camino B — Instalación manual (mismos resultados, paso a paso)

Hacé los Pasos 1 y 2 del Camino A (Python + copiar la carpeta) y luego,
en **Símbolo del sistema** (`cmd`):

### Paso B1 · Crear el entorno virtual e instalar dependencias

```bat
cd /d "C:\Viking Software BETA"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Resultado esperado:
`Successfully installed customtkinter-5.2.2 openpyxl-3.1.5 pillow-10.4.0`
(junto con sus sub-dependencias `darkdetect` y `et-xmlfile`).

### Paso B2 · Primer arranque (crea la base de datos)

```bat
python main.py
```

Resultado esperado: se abre la ventana de **Viking Software BETA** con el logo
VK, el indicador **«● Modo Offline Activo»** y el tarjetero en **$ 0,00**.
En segundo plano se creó `datos\viking.db` con el catálogo semilla
(7 ítems: 4 servicios y 3 productos).

Cerrá la ventana y corré la prueba automática:

```bat
python test_manual.py
```

Resultado esperado: `TODAS LAS PRUEBAS PASARON`.

### Paso B3 · Crear el acceso directo de escritorio

Clic derecho en el escritorio → **Nuevo → Acceso directo** → destino:

```javascript
"C:\Viking Software BETA\venv\Scripts\pythonw.exe" "C:\Viking Software BETA\main.py"
```

- **Nombre:** `Viking Software`
- `pythonw.exe` abre la app **sin** la ventana negra de consola.
- Las comillas son obligatorias: la ruta tiene un espacio.

---

## Paso 4 · Excluir la carpeta en el antivirus (ambos caminos)

El equipo corre **McAfee** y **Windows Defender**. Para evitar bloqueos o
lentitud al escribir la base de datos, agregá `C:\Viking Software BETA`
a las exclusiones de ambos:

- **Defender:** Seguridad de Windows → Protección antivirus y contra amenazas
→ Administrar la configuración → Exclusiones → Agregar carpeta.
- **McAfee:** Configuración → Análisis en tiempo real → Archivos excluidos.

## Paso 5 · Prueba de humo operativa

1. Abrí **Viking Software** desde el acceso directo.
2. Registrá una venta de prueba: elegí **Servicio**, escribí `Corte` y
seleccioná **Corte Caballero** del desplegable (precio se precompleta),
cantidad `1`, pulsá **REGISTRAR VENTA**.
3. Verificá que aparece en la **Tabla del día** y que el **tarjetero** suma
`$ 8.000,00`.
4. Pulsá **Exportar Datos**, dejá el rango del día y **Exportar**. Abrí el
`.xlsx` generado en `C:\Viking Software BETA\exportaciones` con Excel:
debe tener logo, encabezados azul/rojo y la fila **GRAN TOTAL**.
5. Cerrá y reabrí la app: la venta de prueba **debe seguir en la tabla**
(persistencia en disco).

## Verificación post-instalación

| Prueba | Comando / acción | Resultado esperado |
| --- | --- | --- |
| Intérprete | `python --version` | Python 3.12.x |
| Dependencias | `pip list` (con venv activo) | customtkinter, openpyxl, Pillow |
| Base de datos | Existe `datos\viking.db` | Creado tras el primer arranque |
| Registro | Venta de prueba | Fila en tabla del día + tarjetero actualizado |
| Persistencia | Cerrar y reabrir la app | La venta sigue en la tabla |
| Exportación | Exportar rango del día | .xlsx con logo, colores y gran total |
| Acceso directo | Doble clic en «Viking Software» | Abre sin ventana de consola |

## Respaldo y Rollback (deshacer la instalación)

**Respaldo semanal:** copiar el archivo `datos\viking.db` a otra unidad o
pendrive. Copiar el archivo alcanza: ahí vive toda la información del negocio.

**Rollback completo:**

```bat
rem 1. Cerrar la aplicación
rem 2. Preservar los datos (¡primero los datos!)
copy "C:\Viking Software BETA\datos\viking.db" "D:\Respaldos\viking_respaldo.db"
rem 3. Eliminar el programa
rmdir /s /q "C:\Viking Software BETA"
rem 4. (Opcional) Desinstalar Python desde "Agregar o quitar programas"
```

Reinstalar = repetir esta guía y restaurar `viking.db` dentro de `datos\`.

## Solución de problemas frecuentes

| Síntoma | Causa probable | Acción |
| --- | --- | --- |
| `'python' no se reconoce...` | No se marcó *Add to PATH* | Reinstalar Python 3.12 marcando la casilla |
| La app tarda en abrir o falla al guardar | Antivirus escaneando la carpeta | Paso 4 (exclusiones) |
| Ventana con íconos/cuadros raros | Zoom de Windows al 150 % | Es normal: los textos escalan; no afecta el uso |
| «La base de datos no pudo escribir» | Disco lleno o db bloqueada | Cerrar y reabrir; revisar `logs\viking.log` |

---

*Viking Software BETA · Plano Técnico Etapa 1 — Facundo David Barreto · Octubre 2026*