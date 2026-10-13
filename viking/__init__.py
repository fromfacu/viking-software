"""Viking Software BETA — Módulo de Registro y Gestión (Etapa 1: Recolección de Datos).

Autor: Facundo David Barreto
Cliente: Peluquería Vikingos (Juliano — propietario)

Paquete principal del sistema. Capas:
    modelos.py      — objetos de dominio puros, sin base de datos ni pantalla.
    base_datos.py   — conexión y repositorios (único lugar donde existe SQL).
    servicios.py    — reglas de negocio: validación, cálculo, exportación.
    interfaz.py     — pantallas CustomTkinter que solo llaman a servicios.
"""

__version__ = "0.5.0-beta"
__codigo__ = "VIK-ERP-BETA-001"
__autor__ = "Facundo David Barreto"
