# Viking Software

> Sistema de gestión offline-first para una peluquería: caja rápida, clientes, barberos, gastos, liquidaciones y reportes Excel.

**Versión de referencia:** `0.5.0-beta` · **Etapa 1 completada** · **Autor:** Facundo David Barreto · **Fecha:** octubre de 2026

[!\[Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python\&logoColor=white)](https://www.python.org/)
[!\[SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite\&logoColor=white)](https://www.sqlite.org/)
[!\[Excel](https://img.shields.io/badge/Excel-openpyxl-217346?logo=microsoftexcel\&logoColor=white)](https://openpyxl.readthedocs.io/)
[!\[Status](https://img.shields.io/badge/status-beta-orange)](#estado)

## Qué demuestra este proyecto

Este no es un CRUD de tutorial. Es una aplicación de escritorio desarrollada alrededor de un problema comercial real: **registrar operaciones en segundos, conservar trazabilidad y convertir cada movimiento en información útil para el negocio**.

La Etapa 1 quedó operativa en producción en el mostrador del cliente. El sistema funciona sin internet, mantiene una base SQLite local y exporta un libro Excel con información de caja, clientes y liquidaciones. fileciteturn0file0L45-L58

### Funcionalidades principales

* &#x20;Caja rápida: venta en menos de cinco segundos.
* &#x20;Barbero obligatorio para mantener trazabilidad.
* &#x20;Métodos de pago administrables.
* &#x20;Propinas y liquidación por comisión.
* &#x20;Gastos y adelantos como egresos de caja.
* &#x20;Base de clientes con celular único.
* &#x20;Autocompletado y detección de posibles errores de tipeo.
* &#x20;Fecha de nacimiento preparada para funcionalidades CRM.
* &#x20;Exportación `.xlsx` con registro, dashboard, balance, clientes y liquidación por barbero.
* &#x20;Modo oscuro / claro persistido.
* &#x20;Moneda configurable.
* &#x20;Migraciones automáticas de esquema.
* &#x20;Suite de pruebas de dominio, persistencia, reglas de negocio y exportación.
* &#x20;Diagnóstico de fallos para soporte en Windows.

La documentación del proyecto registra diez entregas incrementales entre el 6 y el 8 de octubre de 2026, con cada versión probada y ajustada sobre el uso real del mostrador. fileciteturn0file0L56-L82

## Arquitectura

El código está organizado por responsabilidades:

```text
viking-software/
├── main.py
├── requirements.txt
├── test\_manual.py
├── assets/
│   └── logo\_vk.png
├── docs/
│   ├── GUIA-DE-INSTALACION.md
│   └── ACTUALIZACION-\*.md
└── viking/
    ├── modelos.py       # Entidades y dominio
    ├── base\_datos.py    # SQLite + repositorios + migraciones
    ├── servicios.py     # Reglas de negocio + exportación Excel
    └── interfaz.py      # UI de escritorio
```

La separación en **dominio → persistencia → servicios → interfaz** permite evolucionar el sistema sin rehacer toda la aplicación. La base utiliza transacciones y WAL, y las versiones incorporan migraciones automáticas. fileciteturn0file0L180-L198

## Stack

|Capa|Tecnología|
|-|-|
|Lenguaje|Python 3.12+|
|UI|CustomTkinter / Tkinter|
|Persistencia|SQLite 3|
|Reportes|openpyxl|
|Imágenes|Pillow|
|Testing|Suite propia en Python|
|Plataforma|Windows|

## Ejecución local

### 1\. Clonar

```bash
git clone https://github.com/TU-USUARIO/viking-software.git
cd viking-software
```

### 2\. Crear entorno virtual

```bash
python -m venv .venv
.venv\\Scripts\\activate
```

### 3\. Instalar dependencias

```bash
python -m pip install -r requirements.txt
```

### 4\. Ejecutar pruebas

```bash
python test\_manual.py
```

Resultado esperado:

```text
TODAS LAS PRUEBAS PASARON
```

### 5\. Ejecutar la aplicación

```bash
python main.py
```

También se conserva `INSTALAR.bat` para la instalación asistida en Windows.

> \*\*Nota de seguridad:\*\* este repositorio es una publicación de portfolio de un proyecto cliente. No contiene bases de datos de producción ni exportaciones reales. Las credenciales y configuraciones del equipo productivo no deben copiarse a entornos públicos.

## Decisiones técnicas destacables

### Offline-first

La operación crítica no depende de internet. Esto elimina una dependencia especialmente peligrosa para un mostrador: que una caída de red detenga las ventas. fileciteturn0file0L96-L100

### Datos como producto secundario

Una venta no termina en el registro: alimenta el historial del cliente, la liquidación del barbero y las métricas del negocio. fileciteturn0file0L201-L203

### Integridad operativa

El proyecto incluye pruebas automáticas, diagnóstico de un clic, manifiesto de integridad y una rutina de respaldo simple basada en la base local. fileciteturn0file0L186-L198

### Evolución incremental

La arquitectura no intenta resolver CRM, nube y automatización el primer día. Primero estabiliza el mostrador; después escala sobre los datos reales. Ese criterio guía la ruta de Etapa 2. fileciteturn0file0L215-L223

## Ruta de evolución

La siguiente etapa está planteada como un ecosistema híbrido:

```text
Celulares de barberos
        │
        ▼
   VIKING POS ──────► Servidor cloud
                          │
                  ┌───────┴───────┐
                  ▼               ▼
                 CRM             n8n
```

Orden previsto:

1. Interfaz web local para cada barbero.
2. CRM sobre la base de clientes existente.
3. VPS + sincronización.
4. Automatizaciones con n8n.

La documentación del proyecto prioriza ese orden porque cada fase agrega valor sin obligar a implementar toda la infraestructura de una vez. fileciteturn0file0L311-L327

## Documentación

* `docs/GUIA-DE-INSTALACION.md` — instalación y troubleshooting.
* `docs/ACTUALIZACION-0.2.0.md` → `0.5.0.md` — evolución técnica.
* `MANIFEST.md` — manifiesto de distribución de la versión entregada.

## Estado

**Beta / Etapa 1 completada.** El sistema entregado ya resuelve la operación de mostrador y deja una base técnica preparada para CRM, nube y automatización. fileciteturn0file0L345-L350

## Autor

**Facundo David Barreto**  
Desarrollo de software · Python · automatización · sistemas de gestión

Este repositorio forma parte de mi portfolio como desarrollador y documenta el proceso completo: problema → diseño → implementación → pruebas → puesta en producción → evolución.

\---

### Uso del código

El repositorio se publica con fines de portfolio y demostración técnica. El proyecto fue desarrollado para un cliente; para reutilización comercial o redistribución del código, solicitar autorización al autor y al titular correspondiente.

