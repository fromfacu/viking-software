"""Punto de entrada — Viking Software BETA · Etapa 1.8 (versión 0.5.0).

Autor: Facundo David Barreto
Cliente: Peluquería Vikingos (Juliano — propietario)

Ensambla las capas (de adentro hacia afuera) y arranca la aplicación:

    modelos  →  base_datos  →  servicios  →  interfaz

Ejecución:
    python main.py            (desarrollo, muestra la consola)
    venv\\Scripts\\pythonw.exe main.py   (acceso directo, sin consola)

En el primer arranque se crea datos\\viking.db con el catálogo semilla,
el barbero semilla (Juliano, el dueño — los empleados se agregan desde
Administración → BARBEROS) y los métodos de pago semilla (EFECTIVO /
TRANSFERENCIA / TARJETA / QR / Mercado Pago). Si la base venía de una
etapa anterior, las migraciones (hasta esquema v5) se aplican solas y
sin perder datos: se suman la tabla de clientes (con fecha de nacimiento
desde v5), la columna cliente_id en ventas, la tabla de adelantos y los
barberos existentes conservan su comisión.
"""

import logging
from pathlib import Path

from viking.base_datos import (AdelantoRepository, BarberoRepository,
                               CatalogoRepository, ClienteRepository,
                               ConexionDB, ConfigRepository, GastoRepository,
                               MetodoPagoRepository, VentaRepository)
from viking.servicios import (AdminService, ExportadorExcel, GastoService,
                              RegistroVentaService)

RAIZ = Path(__file__).resolve().parent


def configurar_log() -> None:
    """Log de errores y eventos en logs\\viking.log (sección 3.2 del plano)."""
    carpeta_logs = RAIZ / "logs"
    carpeta_logs.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=carpeta_logs / "viking.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        encoding="utf-8",
    )


def main() -> None:
    configurar_log()
    log = logging.getLogger("viking")
    log.info("Arranque de Viking Software BETA 0.5.0-beta")

    try:
        _arrancar()
        log.info("Cierre de Viking Software BETA")
    except Exception:
        # El acceso directo usa pythonw.exe (sin consola): si algo falla al
        # abrir, sin esta captura el programa "no abre" y no dice nada.
        # Ahora el error queda en logs\viking.log y salta un cartel.
        log.exception("ERROR FATAL al abrir Viking Software")
        _aviso_error_fatal()
        raise SystemExit(1)


def _aviso_error_fatal() -> None:
    """Cartel de emergencia cuando el programa no pudo abrirse.

    Se crea una ventana Tk mínima solo para el aviso; si ni eso se puede,
    el detalle igualmente ya quedó registrado en logs\\viking.log.
    """
    try:
        import tkinter as tk
        from tkinter import messagebox

        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror(
            "VIKING SOFTWARE — NO PUDO ABRIRSE",
            "EL PROGRAMA NO PUDO ABRIRSE.\n\n"
            "El detalle del error quedó guardado en el archivo:\n"
            "logs\\viking.log\n\n"
            "MANDÁ ESE ARCHIVO (O UNA FOTO) A SOPORTE.\n"
            "También podés hacer doble clic en DIAGNOSTICO.bat:\n"
            "junta toda la información en logs\\diagnostico.txt.")
        raiz.destroy()
    except Exception:
        pass


def _arrancar() -> None:
    """Ensambla las capas de adentro hacia afuera y abre la ventana."""
    db = ConexionDB(RAIZ / "datos" / "viking.db")
    db.inicializar()  # crea tablas base + migra a v5 si hace falta

    repo_catalogo = CatalogoRepository(db)
    repo_ventas = VentaRepository(db)
    repo_barberos = BarberoRepository(db)
    repo_gastos = GastoRepository(db)
    repo_config = ConfigRepository(db)
    repo_metodos = MetodoPagoRepository(db)
    repo_clientes = ClienteRepository(db)
    repo_adelantos = AdelantoRepository(db)

    servicio_reg = RegistroVentaService(repo_ventas, repo_barberos,
                                        repo_metodos, repo_clientes)
    servicio_gastos = GastoService(repo_gastos)
    servicio_admin = AdminService(repo_barberos, repo_catalogo, repo_ventas,
                                  repo_config, repo_metodos, repo_clientes,
                                  repo_adelantos)
    servicio_exp = ExportadorExcel(repo_ventas, repo_gastos, repo_barberos,
                                   repo_config, repo_adelantos,
                                   RAIZ / "assets" / "logo_vk.png",
                                   RAIZ / "exportaciones")

    # La interfaz se importa al final: es la capa más externa y solo
    # recibe servicios ya construidos.
    from viking.interfaz import VikingApp

    app = VikingApp(servicio_reg, servicio_exp, repo_catalogo, repo_barberos,
                    repo_metodos, repo_clientes, servicio_gastos,
                    servicio_admin, repo_config, repo_adelantos,
                    RAIZ / "assets" / "logo_vk.png")
    app.mainloop()


if __name__ == "__main__":
    main()
