"""Capa de presentación — Viking Software BETA · Etapa 1.8 (versión 0.5.0).

Autor: Facundo David Barreto
Cliente: Peluquería Vikingos (Juliano — propietario)

Dos pestañas principales:
    * CAJA — la pantalla de caja rápida de siempre, con selector
      obligatorio de barbero + indicador grande del barbero activo,
      cliente con AUTOCOMPLETADO (se escribe y sugiere los clientes
      cargados con una LISTA PROPIA que nunca roba el teclado; Enter,
      clic o ↓/↑ + Enter elige la sugerencia), método de pago
      (lista administrable) y propina.
      Reglas NO negociables: cero animaciones, todo en el hilo principal,
      mensajes de 3 bloques.
    * ADMINISTRACIÓN — protegida con clave; sub-pestañas BARBEROS (con
      comisión % y ADELANTOS del dueño), INVENTARIO, MOVIMIENTOS
      (corregir/eliminar), GASTOS, CLIENTES (alta/edición/baja, con
      detector de errores de tipeo y FECHA DE NACIMIENTO opcional) y
      MÉTODOS Y MONEDA (medios de cobro + símbolo de moneda del sistema).

Reglas de las Etapas 1.6, 1.7 y 1.8:
    * TODOS los textos fijos de la interfaz van en MAYÚSCULAS. Los datos
      que carga el usuario se muestran como fueron cargados.
    * Las listas validadas (barbero, descripción, método, moneda) son de
      SOLO SELECCIÓN (readonly). EXCEPCIÓN pedida: el campo CLIENTE admite
      escritura con sugerencias automáticas (autocompletado) para agilizar
      el registro; también acepta un nombre suelto sin ficha.
    * MODO OSCURO / MODO CLARO: el botón de la cabecera alterna la paleta
      completa y la elección queda guardada (config "tema"). El modo claro
      usa COLORES PASTELES con texto oscuro de alto contraste: las
      pestañas seleccionadas llevan texto blanco sobre el color
      institucional y las no seleccionadas, blanco sobre pizarra.
    * Todos los importes se muestran con el símbolo de la moneda del
      sistema (config "moneda_simbolo", se elige en MÉTODOS Y MONEDA).

La interfaz SOLO llama a servicios; nunca toca SQL ni valida reglas
de negocio por su cuenta.
"""

import logging
import re
import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
from datetime import date, datetime
from pathlib import Path
from tkinter import messagebox, simpledialog

import customtkinter as ctk
from PIL import Image

from .modelos import MONEDAS, TipoItem
from .servicios import (ClientePosibleDuplicado, ErrorValidacion,
                        formato_moneda)

log = logging.getLogger("viking")

# ------------------------------------------------------------------
# Tokens de diseño — paletas MODO OSCURO / MODO CLARO
# Los colores institucionales (acentos) no cambian entre modos; el resto
# de tokens los reasigna aplicar_tema() y se leen en tiempo de construcción
# de cada widget (por eso al alternar el tema se RECONSTRUYE la interfaz).
# ------------------------------------------------------------------
ACENTO_VERDE = "#2D5A27"
ACENTO_ROJO = "#E63946"
ACENTO_AZUL = "#1D3557"
HOVER_AZUL = "#16324F"
HOVER_ROJO = "#B62E3A"

TEMAS = {
    "oscuro": {
        "FONDO_PRINCIPAL": "#181818", "FONDO_PANEL": "#202020",
        "CAMPO_FONDO": "#2A2A2A", "CAMPO_BORDE": "#3A3A3A",
        "DESPLEGABLE_FONDO": "#202020", "BOTON_NEUTRO": "#3A3A3A",
        "BOTON_NEUTRO_HOVER": "#4A4A4A", "FILA_PAR": "#262626",
        "TEXTO_PRINCIPAL": "#FFFFFF", "TEXTO_SUAVE": "#B0B0B0",
        "VERDE_TEXTO": "#7FB069",
        "SEG_NO_SELECCIONADO": "#2A2A2A", "SEG_NO_SELEC_HOVER": "#4A4A4A",
        "BOTON_COMBO": "#1D3557", "BOTON_COMBO_ALERTA": "#E63946",
    },
    # Paleta CLARA (Etapa 1.8): pasteles fríos + texto casi negro.
    # Todo par texto/fondo supera el contraste 4.5:1 (verificado):
    #   #14202E sobre blanco 15.9:1 · sobre #C7D2E0 10.8:1
    #   blanco sobre #5C6B82 (pestaña no seleccionada) 5.4:1
    #   #14202E (flecha) sobre #A9BFD9 (botón combo) 8.7:1
    "claro": {
        "FONDO_PRINCIPAL": "#E8EDF3", "FONDO_PANEL": "#FFFFFF",
        "CAMPO_FONDO": "#FFFFFF", "CAMPO_BORDE": "#8A94A6",
        "DESPLEGABLE_FONDO": "#FFFFFF", "BOTON_NEUTRO": "#C7D2E0",
        "BOTON_NEUTRO_HOVER": "#AEBFD2", "FILA_PAR": "#EFF4F9",
        "TEXTO_PRINCIPAL": "#14202E", "TEXTO_SUAVE": "#4A5568",
        "VERDE_TEXTO": "#2D5A27",
        "SEG_NO_SELECCIONADO": "#5C6B82", "SEG_NO_SELEC_HOVER": "#4E5B70",
        "BOTON_COMBO": "#A9BFD9", "BOTON_COMBO_ALERTA": "#E88B93",
    },
}

# Tokens activos (aplicar_tema los reasigna).
FONDO_PRINCIPAL = TEMAS["oscuro"]["FONDO_PRINCIPAL"]
FONDO_PANEL = TEMAS["oscuro"]["FONDO_PANEL"]
CAMPO_FONDO = TEMAS["oscuro"]["CAMPO_FONDO"]
CAMPO_BORDE = TEMAS["oscuro"]["CAMPO_BORDE"]
DESPLEGABLE_FONDO = TEMAS["oscuro"]["DESPLEGABLE_FONDO"]
BOTON_NEUTRO = TEMAS["oscuro"]["BOTON_NEUTRO"]
BOTON_NEUTRO_HOVER = TEMAS["oscuro"]["BOTON_NEUTRO_HOVER"]
FILA_PAR = TEMAS["oscuro"]["FILA_PAR"]
TEXTO_PRINCIPAL = TEMAS["oscuro"]["TEXTO_PRINCIPAL"]
TEXTO_SUAVE = TEMAS["oscuro"]["TEXTO_SUAVE"]
VERDE_TEXTO = TEMAS["oscuro"]["VERDE_TEXTO"]
SEG_NO_SELECCIONADO = TEMAS["oscuro"]["SEG_NO_SELECCIONADO"]
SEG_NO_SELEC_HOVER = TEMAS["oscuro"]["SEG_NO_SELEC_HOVER"]
BOTON_COMBO = TEMAS["oscuro"]["BOTON_COMBO"]
BOTON_COMBO_ALERTA = TEMAS["oscuro"]["BOTON_COMBO_ALERTA"]

F_BASE = ("Segoe UI", 15)
F_GRANDE = ("Segoe UI", 18, "bold")
F_TOTAL = ("Segoe UI", 26, "bold")
F_BARBERO = ("Segoe UI", 18, "bold")

ESTILO_ARBOL = "Viking.Treeview"

# Opción fija del selector de clientes: venta sin cliente registrado.
MOSTRADOR = "— MOSTRADOR —"


def aplicar_tema(modo: str) -> None:
    """Activa la paleta 'oscuro' o 'claro'. Reasigna los tokens globales:
    los widgets leen los tokens al CONSTRUIRSE, así que después de llamar
    a esta función hay que reconstruir la interfaz (ver VikingApp)."""
    global FONDO_PRINCIPAL, FONDO_PANEL, CAMPO_FONDO, CAMPO_BORDE
    global DESPLEGABLE_FONDO, BOTON_NEUTRO, BOTON_NEUTRO_HOVER, FILA_PAR
    global TEXTO_PRINCIPAL, TEXTO_SUAVE, VERDE_TEXTO
    global SEG_NO_SELECCIONADO, SEG_NO_SELEC_HOVER
    global BOTON_COMBO, BOTON_COMBO_ALERTA
    t = TEMAS.get(modo, TEMAS["oscuro"])
    FONDO_PRINCIPAL = t["FONDO_PRINCIPAL"]
    FONDO_PANEL = t["FONDO_PANEL"]
    CAMPO_FONDO = t["CAMPO_FONDO"]
    CAMPO_BORDE = t["CAMPO_BORDE"]
    DESPLEGABLE_FONDO = t["DESPLEGABLE_FONDO"]
    BOTON_NEUTRO = t["BOTON_NEUTRO"]
    BOTON_NEUTRO_HOVER = t["BOTON_NEUTRO_HOVER"]
    FILA_PAR = t["FILA_PAR"]
    TEXTO_PRINCIPAL = t["TEXTO_PRINCIPAL"]
    TEXTO_SUAVE = t["TEXTO_SUAVE"]
    VERDE_TEXTO = t["VERDE_TEXTO"]
    SEG_NO_SELECCIONADO = t["SEG_NO_SELECCIONADO"]
    SEG_NO_SELEC_HOVER = t["SEG_NO_SELEC_HOVER"]
    BOTON_COMBO = t["BOTON_COMBO"]
    BOTON_COMBO_ALERTA = t["BOTON_COMBO_ALERTA"]
    ctk.set_appearance_mode("light" if modo == "claro" else "dark")


def _estilo_treeview(master) -> None:
    estilo = ttk.Style(master)
    estilo.theme_use("clam")
    estilo.configure(ESTILO_ARBOL, background=FONDO_PANEL,
                     fieldbackground=FONDO_PANEL,
                     foreground=TEXTO_PRINCIPAL, rowheight=34,
                     font=("Segoe UI", 12), borderwidth=0)
    estilo.configure(f"{ESTILO_ARBOL}.Heading", background=ACENTO_AZUL,
                     foreground="#FFFFFF", font=("Segoe UI", 12, "bold"),
                     relief="flat")
    estilo.map(ESTILO_ARBOL, background=[("selected", ACENTO_AZUL)])


def _arbol(master, columnas, anchos) -> ttk.Treeview:
    """Treeview con scroll. columnas: (id, título, ancho, ancla)."""
    marco = ctk.CTkFrame(master, fg_color="transparent")
    tree = ttk.Treeview(marco, columns=[c[0] for c in columnas],
                        show="headings", style=ESTILO_ARBOL)
    for cid, titulo, ancho, ancla in columnas:
        tree.heading(cid, text=titulo)
        tree.column(cid, width=ancho, anchor=ancla, stretch=(ancla == "w"))
    barra = ttk.Scrollbar(marco, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=barra.set)
    tree.pack(side="left", fill="both", expand=True)
    barra.pack(side="right", fill="y")
    marco.tree = tree
    return marco


def _display_cliente(c) -> str:
    """Formato canónico del cliente en las listas: 'APELLIDO, NOMBRE —
    CELULAR' (el celular es el dato que identifica a cada cliente)."""
    return f"{c.apellido}, {c.nombre} — {c.celular}".upper()


class ComboAutocompletable(ctk.CTkFrame):
    """Campo de cliente con SUGERENCIAS flotantes propias (Etapa 1.7).

    A medida que se escribe, filtra y sugiere las opciones que coinciden
    — ej.: tipeando 'RICH' aparecen todos los Richard cargados — y al
    elegir una (clic, o ↓/↑ + Enter) el campo se autocompleta. Si el
    texto no coincide con ninguna ficha, queda como nombre suelto.

    La lista es PROPIA (Toplevel + Listbox de tkinter puro) y NO el
    desplegable interno del ComboBox: según la versión de CustomTkinter,
    ese desplegable puede ser un MENÚ nativo que al abrirse captura el
    teclado y no deja seguir escribiendo (bug corregido en 0.4.3). La
    lista propia JAMÁS toma el foco: el operador sigue tipeando con la
    lista abierta.

    ``proveedor`` es una función texto -> lista de opciones que consulta
    la base en cada tecla (la lista siempre está al día). A diferencia
    de las listas validadas (readonly), este campo SÍ admite escritura:
    esa es justamente su función.
    """

    # Teclas que NO disparan un filtrado nuevo (navegación, modificadoras).
    TECLAS_SIN_FILTRO = frozenset({
        "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
        "Caps_Lock", "Left", "Right", "Home", "End", "Up", "Down",
        "Return", "Escape", "Tab", "Prior", "Next", "Insert", "Delete",
        "Win_L", "Win_R", "Menu", "Num_Lock", "Scroll_Lock",
        "F1", "F2", "F3", "F4", "F5", "F6",
        "F7", "F8", "F9", "F10", "F11", "F12",
    })

    MAX_VISIBLES = 8

    # Opciones visuales que sí aplican al CTkEntry interno. El resto
    # (values, button_color, dropdown_*) eran del ComboBox: se ignoran.
    _KW_ENTRADA = ("font", "width", "height", "fg_color", "border_color",
                   "border_width", "text_color", "justify", "corner_radius")

    def __init__(self, master, proveedor, placeholder_text: str | None = None,
                 **kwargs):
        self._proveedor = proveedor  # función texto -> lista de opciones
        self._guia_texto = placeholder_text or ""
        self._guia_manual = False    # True si el placeholder nativo no existe
        self._guia_activa = False    # guía manual visible en este momento
        self._lista: tk.Toplevel | None = None
        self._listbox: tk.Listbox | None = None
        self._scroll: tk.Scrollbar | None = None
        self._alto_fila = 24
        super().__init__(master, fg_color="transparent")

        kwargs.pop("values", None)
        kw = {k: kwargs.pop(k) for k in list(kwargs) if k in self._KW_ENTRADA}
        if kwargs:
            log.info("ComboAutocompletable ignora opciones del ComboBox: %s",
                     ", ".join(sorted(kwargs)))
        kw.setdefault("placeholder_text_color", TEXTO_SUAVE)

        try:
            self.entrada = ctk.CTkEntry(
                self, placeholder_text=self._guia_texto or None, **kw)
            self.entrada.delete(0, "end")  # activa el placeholder nativo
        except Exception:
            # Variante de CTk sin placeholder en el Entry: guía manual por
            # foco que no depende de ninguna versión (fallback 0.4.2).
            log.info("Placeholder nativo no disponible: se usa guía manual")
            self._guia_manual = True
            self.entrada = ctk.CTkEntry(self, **kw)
        self.entrada.pack(fill="x", expand=True)

        interno = self._interno()
        interno.bind("<KeyPress>", self._al_pulsar)
        interno.bind("<KeyRelease>", self._al_teclear)
        interno.bind("<FocusOut>", self._al_perder_foco)
        # El <Destroy> va sobre el Entry interno (tk puro): en los CTkFrame
        # el binding cae sobre el canvas interno y no sobre el frame.
        interno.bind("<Destroy>", self._al_destruir)
        interno.bind("<Unmap>", self._al_ocultarse)
        if self._guia_manual and self._guia_texto:
            interno.bind("<FocusIn>", lambda _e: self._ocultar_guia())
            self._mostrar_guia()

    # ---------------- utilidades internas ----------------
    def _interno(self):
        """El tk.Entry real dentro del CTkEntry (para bindings de tecla)."""
        return getattr(self.entrada, "_entry", self.entrada)

    # ---------------- API pública ----------------
    def get(self) -> str:
        if self._guia_activa:
            return ""
        return self.entrada.get()

    def set(self, valor: str) -> None:
        """Escribe texto sin abrir la lista (no genera eventos de tecla)."""
        self._ocultar_guia()
        self.entrada.delete(0, "end")
        if valor:
            self.entrada.insert(0, valor)
        if self._guia_manual and not valor:
            self._mostrar_guia()

    def limpiar(self) -> None:
        """Campo vacío, lista cerrada y texto guía visible (nunca sólido)."""
        self._ocultar_lista()
        self._ocultar_guia()
        self.entrada.delete(0, "end")  # CTkEntry reactiva aquí su placeholder
        if self._guia_manual:
            self._mostrar_guia()

    def configure(self, **kwargs) -> None:
        # Compatibilidad con la llamada configure(values=...) del panel:
        # las sugerencias salen del proveedor en cada tecla, no de values.
        kwargs.pop("values", None)
        for k in ("button_color", "button_hover_color", "dropdown_fg_color",
                  "dropdown_hover_color", "dropdown_text_color",
                  "dropdown_font"):
            kwargs.pop(k, None)
        if kwargs:
            self.entrada.configure(**kwargs)

    def focus_set(self) -> None:
        self.entrada.focus_set()

    # ---------------- texto guía (placeholder) ----------------
    def _mostrar_guia(self) -> None:
        if (self._guia_manual and not self._guia_activa
                and not self.entrada.get()):
            self._guia_activa = True
            self.entrada.insert(0, self._guia_texto)
            try:
                self.entrada.configure(text_color=TEXTO_SUAVE)
            except Exception:
                pass

    def _ocultar_guia(self) -> None:
        if self._guia_manual and self._guia_activa:
            self._guia_activa = False
            self.entrada.delete(0, "end")
            try:
                self.entrada.configure(text_color=TEXTO_PRINCIPAL)
            except Exception:
                pass

    # ---------------- tecleo y navegación ----------------
    def _al_teclear(self, evento) -> None:
        if evento.keysym in self.TECLAS_SIN_FILTRO:
            return
        texto = "" if self._guia_activa else self.entrada.get()
        try:
            opciones = list(self._proveedor(texto))
        except Exception:
            log.exception("Falló el autocompletado")
            return
        if opciones:
            self._mostrar_opciones(opciones)
        else:
            self._ocultar_lista()

    def _al_pulsar(self, evento):
        """Navegación por teclado con la lista abierta: ↓/↑ mueven el
        resaltado, Enter elige la sugerencia, Escape la cierra y Tab la
        cierra dejando pasar el foco al siguiente campo."""
        if not self._lista_abierta():
            return None
        tecla = evento.keysym
        if tecla == "Escape":
            self._ocultar_lista()
            return "break"
        if tecla in ("Down", "Up"):
            self._mover_seleccion(1 if tecla == "Down" else -1)
            return "break"
        if tecla == "Return":
            sel = self._listbox.curselection()
            if sel:
                self._elegir(self._listbox.get(sel[0]))
            else:
                self._ocultar_lista()
            return "break"
        if tecla == "Tab":
            self._ocultar_lista()
        return None

    # ---------------- lista de sugerencias ----------------
    def _lista_abierta(self) -> bool:
        return (self._lista is not None and self._lista.winfo_exists()
                and bool(self._lista.winfo_ismapped()))

    def _asegurar_lista(self) -> None:
        if self._lista is not None and self._lista.winfo_exists():
            return
        raiz = self.winfo_toplevel()
        top = tk.Toplevel(raiz)
        top.wm_overrideredirect(True)   # sin bordes: se ve como desplegable
        top.transient(raiz)
        top.configure(bg=CAMPO_BORDE)
        lb = tk.Listbox(
            top, font=F_BASE, bg=DESPLEGABLE_FONDO, fg=TEXTO_PRINCIPAL,
            selectbackground=ACENTO_AZUL, selectforeground="#FFFFFF",
            highlightthickness=0, relief="flat", borderwidth=0,
            activestyle="none", exportselection=False)
        scroll = tk.Scrollbar(top, orient="vertical", command=lb.yview)
        lb.configure(yscrollcommand=scroll.set)
        lb.pack(side="left", fill="both", expand=True, padx=1, pady=1)
        lb.bind("<ButtonRelease-1>", self._al_clic_lista)
        # Candado anti-robo de teclado: si esta ventana llegara a enfocarse
        # (clic, gestor de ventanas), el foco vuelve al campo al instante.
        top.bind("<FocusIn>", lambda _e: self.entrada.focus_set())
        try:
            self._alto_fila = max(
                tkfont.Font(font=F_BASE).metrics("linespace") + 4, 22)
        except Exception:
            self._alto_fila = 24
        self._lista, self._listbox, self._scroll = top, lb, scroll

    def _mostrar_opciones(self, opciones: list[str]) -> None:
        self._asegurar_lista()
        lb = self._listbox
        lb.delete(0, "end")
        for op in opciones:
            lb.insert("end", op)
        visibles = min(len(opciones), self.MAX_VISIBLES)
        lb.configure(height=visibles)
        if len(opciones) > self.MAX_VISIBLES:
            self._scroll.pack(side="right", fill="y")
        else:
            self._scroll.pack_forget()
        lb.selection_clear(0, "end")
        lb.selection_set(0)
        lb.activate(0)
        lb.see(0)
        self.entrada.update_idletasks()
        x = self.entrada.winfo_rootx()
        y = self.entrada.winfo_rooty() + self.entrada.winfo_height()
        ancho = max(self.entrada.winfo_width(), 240)
        alto = visibles * self._alto_fila + 4
        self._lista.geometry(f"{ancho}x{alto}+{x}+{y}")
        self._lista.deiconify()

    def _ocultar_lista(self) -> None:
        if self._lista is not None and self._lista.winfo_exists():
            self._lista.withdraw()

    def _al_clic_lista(self, evento) -> None:
        idx = self._listbox.nearest(evento.y)
        if 0 <= idx < self._listbox.size():
            self._elegir(self._listbox.get(idx))

    def _elegir(self, texto: str) -> None:
        self.set(texto)               # set() no genera KeyRelease: no refiltra
        self._ocultar_lista()
        try:
            self._interno().icursor("end")
        except Exception:
            pass
        self.entrada.focus_set()

    def _mover_seleccion(self, delta: int) -> None:
        lb = self._listbox
        total = lb.size()
        if total <= 0:
            return
        sel = lb.curselection()
        i = (sel[0] if sel else 0) + delta
        i = max(0, min(i, total - 1))
        lb.selection_clear(0, "end")
        lb.selection_set(i)
        lb.activate(i)
        lb.see(i)

    # ---------------- cierre por foco / destrucción ----------------
    def _al_perder_foco(self, _evento) -> None:
        if self._guia_manual:
            self._mostrar_guia()
        # Se espera un instante: si el foco se fue a la propia lista
        # (clic sobre una sugerencia), la lista NO se cierra — el clic
        # la cerrará al elegir.
        self.after(150, self._cerrar_si_foco_afuera)

    def _cerrar_si_foco_afuera(self) -> None:
        if not self._lista_abierta():
            return
        foco = self.focus_get()
        if foco in (self.entrada, self._interno(), self._listbox, self._lista):
            return
        self._ocultar_lista()

    def _al_destruir(self, evento) -> None:
        # El Toplevel cuelga de la raíz (no del campo): hay que cerrarlo
        # a mano cuando el campo se destruye (p. ej. al cambiar de tema).
        if evento.widget is self._interno() and self._lista is not None:
            try:
                if self._lista.winfo_exists():
                    self._lista.destroy()
            except Exception:
                pass
            self._lista = self._listbox = self._scroll = None

    def _al_ocultarse(self, evento) -> None:
        """Si el campo deja de verse (cambio de pestaña, rebuild de la
        interfaz), la lista flotante se cierra: nunca queda suelta."""
        if evento.widget is self._interno():
            self._ocultar_lista()


class VikingApp(ctk.CTk):
    """Ventana principal. Regla de oro POS: el hilo principal jamás se
    bloquea y la pantalla de caja rápida tiene CERO animaciones."""

    def __init__(self, servicio_registro, servicio_exportacion, repo_catalogo,
                 repo_barberos, repo_metodos, repo_clientes, gasto_service,
                 admin_service, config_repo, repo_adelantos, logo_path: Path):
        super().__init__()
        self.servicio_registro = servicio_registro
        self.servicio_exportacion = servicio_exportacion
        self.repo_catalogo = repo_catalogo
        self.repo_barberos = repo_barberos
        self.repo_metodos = repo_metodos
        self.repo_clientes = repo_clientes
        self.gasto_service = gasto_service
        self.admin_service = admin_service
        self.config_repo = config_repo
        self.repo_adelantos = repo_adelantos
        self.logo_path = Path(logo_path)
        self._admin_ok = False  # la clave se pide una vez por sesión
        # Símbolo de moneda vigente, siempre leído de la configuración.
        self.simbolo_fn = lambda: self.admin_service.obtener_moneda()

        self.title("VIKING SOFTWARE BETA")
        self.geometry("1280x780")
        self.minsize(1150, 720)

        # Tema guardado (config "tema"): se aplica ANTES de construir.
        self.tema = self.config_repo.obtener("tema", "oscuro")
        if self.tema not in TEMAS:
            self.tema = "oscuro"
        aplicar_tema(self.tema)
        self.configure(fg_color=FONDO_PRINCIPAL)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.panel_admin = None  # se crea al entrar con clave
        self._construir_cuerpo()
        self._refrescar_dia()

    # --------------------------------------------------------------
    def _construir_cuerpo(self) -> None:
        """Cabecera + pestañas + paneles. Lo usan el arranque y el
        cambio de tema (la interfaz se reconstruye con la paleta nueva)."""
        self.cabecera = Cabecera(self, self.logo_path, self.tema,
                                 self._alternar_tema)
        self.cabecera.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))

        # Pestañas principales: la SELECCIONADA usa el azul institucional
        # con texto blanco; las demás, pizarra (claro) / gris (oscuro)
        # con texto blanco — legible en AMBOS modos.
        self.tabs = ctk.CTkTabview(
            self, fg_color=FONDO_PANEL, segmented_button_fg_color=CAMPO_FONDO,
            segmented_button_selected_color=ACENTO_AZUL,
            segmented_button_selected_hover_color=HOVER_AZUL,
            segmented_button_unselected_color=SEG_NO_SELECCIONADO,
            segmented_button_unselected_hover_color=SEG_NO_SELEC_HOVER,
            text_color="#FFFFFF", anchor="w",
            command=self._al_cambiar_pestaña)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.tab_caja = self.tabs.add("  CAJA  ")
        self.tab_admin = self.tabs.add("  ADMINISTRACIÓN  ")
        self.tab_caja.grid_columnconfigure(0, weight=1)
        # Fila 0 (panel de carga) congelada: weight=0 → jamás se estira.
        # Fila 1 (tabla del día) elástica: absorbe todo el espacio sobrante,
        # con un piso de 180 px para que nunca desaparezca.
        self.tab_caja.grid_rowconfigure(0, weight=0)
        self.tab_caja.grid_rowconfigure(1, weight=1, minsize=180)

        self.panel_carga = PanelCargaRapida(
            self.tab_caja, self.servicio_registro, self.repo_catalogo,
            self.repo_barberos, self.repo_metodos, self.repo_clientes,
            self.simbolo_fn,
            al_guardar=self._tras_guardar,
            al_exportar=self._abrir_exportacion)
        self.panel_carga.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 8))

        self.tabla_dia = TablaRegistroDiario(self.tab_caja, self.simbolo_fn)
        self.tabla_dia.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    # --------------------------------------------------------------
    def _alternar_tema(self) -> None:
        """MODO OSCURO ↔ MODO CLARO: guarda la elección y reconstruye la
        interfaz con la paleta nueva. La selección de barbero y método se
        conserva (mismo turno)."""
        self.tema = "claro" if self.tema == "oscuro" else "oscuro"
        self.config_repo.establecer("tema", self.tema)
        aplicar_tema(self.tema)
        log.info("Tema de la interfaz: %s", self.tema)

        barbero_sel = self.panel_carga.combo_barbero.get()
        metodo_sel = self.panel_carga.combo_metodo.get()
        self.cabecera.destroy()
        self.tabs.destroy()
        self.panel_admin = None  # se reconstruye al entrar a Administración
        self.configure(fg_color=FONDO_PRINCIPAL)
        self._construir_cuerpo()
        if barbero_sel in self.panel_carga._barberos:
            self.panel_carga.combo_barbero.set(barbero_sel)
            self.panel_carga._actualizar_indicador()
        if metodo_sel in self.panel_carga._metodos:
            self.panel_carga.combo_metodo.set(metodo_sel)
        self._refrescar_dia()
        self.tabs.set("  CAJA  ")

    # --------------------------------------------------------------
    def _fecha_hoy(self) -> str:
        return date.today().isoformat()

    def _refrescar_dia(self) -> None:
        """Tabla y tarjetero se alimentan SIEMPRE del repositorio (disco)."""
        hoy = self._fecha_hoy()
        ventas = self.servicio_registro.repo.ventas_del_dia(hoy)
        total = self.servicio_registro.repo.total_del_dia(hoy)
        gastos = self.gasto_service.repo.total_entre_fechas(hoy, hoy)
        self.tabla_dia.cargar(ventas)
        self.panel_carga.tarjetero.actualizar(total, gastos,
                                              self.simbolo_fn())

    def _tras_guardar(self) -> None:
        self._refrescar_dia()
        if self.panel_admin is not None:
            self.panel_admin.refrescar()

    def _al_cambiar_datos_admin(self) -> None:
        """El Admin tocó barberos/catálogo/métodos/clientes/movimientos/
        moneda: la caja y el propio panel se enteran."""
        self._refrescar_dia()
        self.panel_carga.recargar_barberos()
        self.panel_carga.recargar_metodos()
        self.panel_carga.recargar_clientes()
        self.panel_carga._rellenar_catalogo()
        if self.panel_admin is not None:
            self.panel_admin.refrescar()

    def _al_cambiar_pestaña(self) -> None:
        if self.tabs.get() == "  ADMINISTRACIÓN  " and not self._admin_ok:
            clave = simpledialog.askstring(
                "ADMINISTRACIÓN", "CLAVE DE ADMINISTRACIÓN:",
                show="•", parent=self)
            if clave is None or not self.config_repo.verificar_clave_admin(clave):
                if clave is not None:
                    messagebox.showwarning(
                        "ADMINISTRACIÓN",
                        "NO SE ABRIÓ EL PANEL PORQUE LA CLAVE NO ES CORRECTA. "
                        "VERIFICÁ LA CLAVE Y VOLVÉ A INTENTAR.", parent=self)
                self.tabs.set("  CAJA  ")
                return
            self._admin_ok = True
        if self.tabs.get() == "  ADMINISTRACIÓN  " and self._admin_ok:
            if self.panel_admin is None:
                self.panel_admin = PanelAdmin(
                    self.tab_admin, self.admin_service, self.repo_barberos,
                    self.repo_catalogo, self.servicio_registro.repo,
                    self.repo_metodos, self.repo_clientes, self.gasto_service,
                    self.repo_adelantos, self.simbolo_fn,
                    al_cambiar_datos=self._al_cambiar_datos_admin)
                self.panel_admin.pack(fill="both", expand=True, padx=8, pady=8)
            self.panel_admin.refrescar()

    def _abrir_exportacion(self) -> None:
        ExportarDialog(self, self.servicio_exportacion, self._fecha_hoy())


class Cabecera(ctk.CTkFrame):
    """Logo VK oficial + título + botón de tema + indicador de estado."""

    def __init__(self, master, logo_path: Path, tema: str, al_alternar_tema):
        super().__init__(master, fg_color=FONDO_PANEL, corner_radius=8)
        self.grid_columnconfigure(1, weight=1)
        if logo_path.exists():
            img = Image.open(logo_path)
            ancho_px, alto_px = img.size
            alto = 44
            # Se conserva la proporción original del logo: nunca se deforma.
            ancho = max(1, round(alto * ancho_px / alto_px))
            imagen = ctk.CTkImage(light_image=img, dark_image=img,
                                  size=(ancho, alto))
            ctk.CTkLabel(self, text="", image=imagen).grid(row=0, column=0,
                                                           padx=(12, 8), pady=8)
        ctk.CTkLabel(self, text="VIKING SOFTWARE BETA", font=F_GRANDE,
                     text_color=TEXTO_PRINCIPAL, anchor="w").grid(row=0, column=1,
                                                                  sticky="w")
        # Botón de tema: ofrece el modo contrario al activo.
        texto_tema = "☀  MODO CLARO" if tema == "oscuro" else "☾  MODO OSCURO"
        ctk.CTkButton(self, text=texto_tema, font=F_BASE, width=190, height=40,
                      fg_color=BOTON_NEUTRO, hover_color=BOTON_NEUTRO_HOVER,
                      text_color=TEXTO_PRINCIPAL,
                      command=al_alternar_tema).grid(row=0, column=2,
                                                     padx=(12, 6), pady=8)
        ind = ctk.CTkLabel(self, text="●  MODO OFFLINE ACTIVO", font=F_BASE,
                           text_color="#FFFFFF", fg_color=ACENTO_AZUL,
                           corner_radius=16)
        ind.grid(row=0, column=3, padx=12, pady=8)


class PanelCargaRapida(ctk.CTkFrame):
    """Objetivo: una venta en < 5 segundos.

    Selector de barbero OBLIGATORIO con indicador grande del barbero activo,
    selector de ítem del catálogo (lista validada de SOLO SELECCIÓN: no se
    puede escribir sobre ella), precio precompletado, cliente con
    AUTOCOMPLETADO (sugiere las fichas cargadas al tipear; acepta nombre
    suelto o MOSTRADOR), método de pago (lista administrable), propina, y
    botón REGISTRAR VENTA de gran tamaño. Tras guardar: limpia el
    formulario, MANTIENE el barbero y el método (mismo turno) y devuelve
    el foco al selector de ítem.
    """

    def __init__(self, master, servicio_registro, repo_catalogo, repo_barberos,
                 repo_metodos, repo_clientes, simbolo_fn, al_guardar,
                 al_exportar):
        super().__init__(master, fg_color=FONDO_PANEL, corner_radius=8)
        self.servicio = servicio_registro
        self.catalogo = repo_catalogo
        self.repo_barberos = repo_barberos
        self.repo_metodos = repo_metodos
        self.repo_clientes = repo_clientes
        self.simbolo_fn = simbolo_fn
        self.al_guardar = al_guardar
        self.al_exportar = al_exportar
        self._barberos = {}  # nombre -> id
        self._metodos = {}   # NOMBRE EN MAYÚSCULAS -> escritura canónica (base)
        self._clientes = {}  # "APELLIDO, NOMBRE — CELULAR" -> (id, "Nombre Apellido")

        ALTO = 44

        def fila(pady=2):
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=12, pady=pady)
            return f

        def etiqueta(master, texto):
            return ctk.CTkLabel(master, text=texto, font=F_BASE,
                                text_color=TEXTO_SUAVE)

        # -- r0: título + exportar --------------------------------------
        r0 = fila(pady=(10, 2))
        ctk.CTkLabel(r0, text="PANEL DE CARGA RÁPIDA", font=F_GRANDE,
                     text_color=TEXTO_PRINCIPAL).pack(side="left")
        ctk.CTkButton(r0, text="  EXPORTAR DATOS", font=F_BASE,
                      fg_color=ACENTO_AZUL, hover_color=HOVER_AZUL,
                      text_color="#FFFFFF", width=170, height=ALTO,
                      command=self.al_exportar).pack(side="right")

        # -- r1: barbero (obligatorio) + indicador grande ----------------
        r1 = fila()
        etiqueta(r1, "BARBERO QUE ATIENDE *:").pack(side="left", padx=(0, 8))
        # El BOTÓN del combo usa BOTON_COMBO_ALERTA (rojo institucional en
        # oscuro / rojo pastel en claro): la flecha toma el color del texto
        # y en claro el texto es oscuro — con un botón pastel se lee bien.
        self.combo_barbero = ctk.CTkComboBox(
            r1, values=["— ELEGIR BARBERO —"], font=F_BASE, width=280, height=ALTO,
            fg_color=CAMPO_FONDO, border_color=ACENTO_ROJO,
            button_color=BOTON_COMBO_ALERTA,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
            state="readonly",
            command=lambda _v: self._actualizar_indicador())
        self.combo_barbero.pack(side="left")
        self.combo_barbero.set("— ELEGIR BARBERO —")
        self.indicador_barbero = ctk.CTkLabel(
            r1, text="SIN BARBERO SELECCIONADO", font=F_BARBERO,
            text_color=TEXTO_SUAVE, fg_color=FILA_PAR, corner_radius=8)
        self.indicador_barbero.pack(side="left", fill="x", expand=True,
                                    padx=(12, 0))

        # -- r2: tipo + descripción (la descripción absorbe el ancho) ----
        r2 = fila()
        self.tipo_var = ctk.StringVar(value=TipoItem.SERVICIO.value)
        ctk.CTkSegmentedButton(
            r2, values=[TipoItem.SERVICIO.value, TipoItem.PRODUCTO.value],
            variable=self.tipo_var, font=F_BASE, height=ALTO,
            selected_color=ACENTO_AZUL, selected_hover_color=HOVER_AZUL,
            unselected_color=SEG_NO_SELECCIONADO,
            unselected_hover_color=SEG_NO_SELEC_HOVER,
            text_color="#FFFFFF",
            command=lambda _v: self._rellenar_catalogo()).pack(side="left",
                                                               padx=(0, 10))
        etiqueta(r2, "DESCRIPCIÓN:").pack(side="left", padx=(0, 8))
        # Lista validada: SELECCIÓN pura (readonly). No se puede escribir
        # sobre ella — los ítems salen siempre del catálogo (INVENTARIO).
        self.combo = ctk.CTkComboBox(
            r2, values=[], font=F_BASE, height=ALTO,
            fg_color=CAMPO_FONDO, border_color=ACENTO_AZUL, button_color=BOTON_COMBO,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
            state="readonly", command=self._al_elegir_item)
        self.combo.pack(side="left", fill="x", expand=True)

        # -- r3: precio / cantidad / propina -----------------------------
        r3 = fila()
        etiqueta(r3, "PRECIO:").pack(side="left", padx=(0, 6))
        self.campo_precio = ctk.CTkEntry(r3, font=F_BASE, width=140, height=ALTO,
                                         fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                         text_color=TEXTO_PRINCIPAL)
        self.campo_precio.pack(side="left", padx=(0, 12))
        self.campo_precio.bind("<KeyRelease>", lambda _e: self._recalcular_subtotal())
        etiqueta(r3, "CANTIDAD:").pack(side="left", padx=(0, 6))
        self.campo_cantidad = ctk.CTkEntry(r3, font=F_BASE, width=80, height=ALTO,
                                           fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                           text_color=TEXTO_PRINCIPAL)
        self.campo_cantidad.pack(side="left", padx=(0, 12))
        self.campo_cantidad.insert(0, "1")
        self.campo_cantidad.bind("<KeyRelease>", lambda _e: self._recalcular_subtotal())
        etiqueta(r3, "PROPINA:").pack(side="left", padx=(0, 6))
        self.campo_propina = ctk.CTkEntry(r3, font=F_BASE, width=130, height=ALTO,
                                          fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                          text_color=TEXTO_PRINCIPAL)
        self.campo_propina.pack(side="left", padx=(0, 12))
        self.campo_propina.insert(0, "0")
        self.campo_propina.bind("<KeyRelease>", lambda _e: self._recalcular_subtotal())
        self.etiqueta_subtotal = ctk.CTkLabel(
            r3, text=f"SUBTOTAL: {formato_moneda(0, self.simbolo_fn())}",
            font=F_GRANDE, text_color=TEXTO_PRINCIPAL)
        self.etiqueta_subtotal.pack(side="right")

        # -- r4: cliente (autocompletado sobre la base) + método de pago --
        r4 = fila()
        etiqueta(r4, "CLIENTE:").pack(side="left", padx=(0, 6))
        # AUTOCOMPLETADO: al escribir sugiere los clientes de la base (por
        # nombre, apellido, celular o mail) y al elegir uno el campo se
        # autocompleta y queda VINCULADO. Si no coincide con ninguna ficha,
        # se acepta el texto suelto (nombre sin ficha) o MOSTRADOR.
        # «— MOSTRADOR —» es un texto GUÍA (placeholder): se ve atenuado con
        # el campo vacío y desaparece al seleccionarlo — no interrumpe la
        # escritura ni hay que borrarlo a mano.
        self.combo_cliente = ComboAutocompletable(
            r4, proveedor=self._proveedor_clientes,
            values=[MOSTRADOR], placeholder_text=MOSTRADOR,
            font=F_BASE, height=ALTO,
            fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE, button_color=BOTON_COMBO,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE)
        self.combo_cliente.pack(side="left", fill="x", expand=True, padx=(0, 12))
        self.combo_cliente.limpiar()
        etiqueta(r4, "MÉTODO DE PAGO:").pack(side="left", padx=(0, 6))
        self.metodo_var = ctk.StringVar(value="")
        self.combo_metodo = ctk.CTkComboBox(
            r4, values=[], variable=self.metodo_var,
            font=F_BASE, width=270, height=ALTO, fg_color=CAMPO_FONDO,
            border_color=CAMPO_BORDE, button_color=BOTON_COMBO,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
            state="readonly")
        self.combo_metodo.pack(side="left")

        # -- r5: botón grande + tarjetero ---------------------------------
        r5 = fila(pady=(4, 2))
        self.tarjetero = TarjeteroTotal(r5)
        self.tarjetero.pack(side="right", fill="y", padx=(10, 0))
        self.boton_registrar = ctk.CTkButton(
            r5, text="REGISTRAR VENTA", font=("Segoe UI", 20, "bold"),
            fg_color=ACENTO_ROJO, hover_color=HOVER_ROJO,
            text_color="#FFFFFF", height=68, corner_radius=8,
            command=self._registrar)
        self.boton_registrar.pack(side="left", fill="both", expand=True)
        for campo in (self.combo, self.campo_precio, self.campo_cantidad,
                      self.campo_propina):
            campo.bind("<Return>", lambda _e: self._registrar())

        # -- r6: mensajes de 3 bloques ------------------------------------
        self.mensaje = ctk.CTkLabel(self, text="", font=F_BASE,
                                    text_color=TEXTO_PRINCIPAL, anchor="w",
                                    justify="left")
        self.mensaje.pack(fill="x", padx=16, pady=(0, 8))
        # OJO: en CTk 6 el <Configure> llega desde el canvas interno del
        # label (e.widget no es el CTkLabel) — configurar siempre self.mensaje.
        self.mensaje.bind("<Configure>", lambda e: self.mensaje.configure(
            wraplength=max(e.width - 10, 200)))

        self.recargar_barberos()
        self.recargar_metodos()
        self.recargar_clientes()
        self._rellenar_catalogo()
        self.combo.focus_set()

    # --------------------------------------------------------------
    # Barbero
    # --------------------------------------------------------------
    def recargar_barberos(self) -> None:
        self._barberos = {b.nombre: b.id for b in self.repo_barberos.listar()}
        nombres = list(self._barberos) or ["— SIN BARBEROS CARGADOS —"]
        self.combo_barbero.configure(values=nombres)
        if self.combo_barbero.get() not in self._barberos:
            self.combo_barbero.set("— ELEGIR BARBERO —")
            self._actualizar_indicador()

    def _barbero_id_actual(self) -> int:
        return self._barberos.get(self.combo_barbero.get(), 0)

    def _actualizar_indicador(self) -> None:
        nombre = self.combo_barbero.get()
        if nombre in self._barberos:
            self.indicador_barbero.configure(text=f"ATIENDE: {nombre.upper()}",
                                             text_color="#FFFFFF",
                                             fg_color=ACENTO_AZUL)
        else:
            self.indicador_barbero.configure(text="SIN BARBERO SELECCIONADO",
                                             text_color=TEXTO_SUAVE,
                                             fg_color=FILA_PAR)

    # --------------------------------------------------------------
    # Métodos de pago (lista administrable desde Administración)
    # --------------------------------------------------------------
    def recargar_metodos(self) -> None:
        """Recarga la lista desde disco. La lista se MUESTRA en mayúsculas
        y se guarda con la escritura canónica registrada en la base."""
        self._metodos = {nombre.upper(): nombre
                         for nombre in self.repo_metodos.listar_nombres()}
        valores = list(self._metodos) or ["EFECTIVO"]
        actual = self.combo_metodo.get()
        self.combo_metodo.configure(values=valores)
        if actual not in self._metodos:
            self.combo_metodo.set(valores[0])

    # --------------------------------------------------------------
    # Clientes (base administrable desde Administración → CLIENTES)
    # --------------------------------------------------------------
    def recargar_clientes(self) -> None:
        """Recarga el mapa desde disco. Se muestra como
        'APELLIDO, NOMBRE — CELULAR' (el celular identifica a cada cliente)
        y se guarda el vínculo (cliente_id) + el nombre como texto.
        El texto ya escrito NO se toca: puede ser una sugerencia elegida
        o un nombre suelto en curso de tipeo."""
        self._clientes = {}
        for c in self.repo_clientes.listar():
            self._clientes[_display_cliente(c)] = (c.id, c.nombre_completo)
        # La lista estática (botón de flecha) muestra la base completa;
        # al tipear, el autocompletado la reemplaza por las sugerencias.
        self.combo_cliente.configure(values=[MOSTRADOR] + list(self._clientes))

    def _proveedor_clientes(self, texto: str) -> list[str]:
        """Sugerencias del autocompletado: con el campo vacío ofrece la
        lista completa; al tipear, consulta la base (nombre, apellido,
        celular o mail) y sugiere solo las fichas que coinciden."""
        texto = (texto or "").strip()
        if not texto or texto == MOSTRADOR:
            return [MOSTRADOR] + list(self._clientes)
        return [_display_cliente(c)
                for c in self.repo_clientes.buscar(texto, limite=8)]

    # --------------------------------------------------------------
    # Catálogo
    # --------------------------------------------------------------
    def _tipo_actual(self) -> TipoItem:
        return TipoItem(self.tipo_var.get())

    def _items(self):
        return self.catalogo.listar_activos(self._tipo_actual())

    def _rellenar_catalogo(self) -> None:
        self.combo.configure(values=[i.nombre for i in self._items()])
        self.combo.set("")
        self.campo_precio.delete(0, "end")
        self._recalcular_subtotal()

    def _al_elegir_item(self, nombre: str) -> None:
        item = self.catalogo.buscar_por_nombre(nombre)
        if item is not None:
            self.campo_precio.delete(0, "end")
            self.campo_precio.insert(0, f"{item.precio_unitario:.2f}")
            self._recalcular_subtotal()
            self.campo_cantidad.focus_set()

    # --------------------------------------------------------------
    # Registro
    # --------------------------------------------------------------
    def _recalcular_subtotal(self) -> None:
        simbolo = self.simbolo_fn()
        try:
            precio = float(self.campo_precio.get().replace(",", "."))
            cantidad = int(self.campo_cantidad.get())
            propina = float(self.campo_propina.get().replace(",", ".") or 0)
            total = round(precio * cantidad + max(propina, 0), 2)
            self.etiqueta_subtotal.configure(
                text=f"SUBTOTAL: {formato_moneda(round(precio * cantidad, 2), simbolo)}"
                     + (f"  +  PROPINA {formato_moneda(propina, simbolo)}" if propina > 0 else "")
                     + f"   →   TOTAL: {formato_moneda(total, simbolo)}")
        except (ValueError, TypeError):
            self.etiqueta_subtotal.configure(
                text=f"SUBTOTAL: {formato_moneda(0, simbolo)}")

    def _registrar(self) -> None:
        texto_cli = self.combo_cliente.get().strip()
        if texto_cli in self._clientes:
            cli_id, cli_txt = self._clientes[texto_cli]
        elif not texto_cli or texto_cli == MOSTRADOR:
            cli_id, cli_txt = None, ""
        else:
            cli_id, cli_txt = None, texto_cli  # nombre suelto, sin ficha
        try:
            venta = self.servicio.registrar(
                self._tipo_actual(), self.combo.get(),
                self.campo_precio.get().replace(",", "."), self.campo_cantidad.get(),
                barbero_id=self._barbero_id_actual(),
                metodo_pago=self._metodos.get(self.combo_metodo.get(),
                                              self.combo_metodo.get()),
                cliente=cli_txt, cliente_id=cli_id,
                propina=self.campo_propina.get().replace(",", ".") or 0)
        except ErrorValidacion as exc:
            texto = str(exc)
            self.mensaje.configure(text=texto.upper(), text_color=ACENTO_ROJO)
            if "descripción" in texto:
                self.combo.focus_set()
            elif "barbero" in texto:
                self.combo_barbero.focus_set()
            else:
                self.campo_precio.focus_set()
            return

        # Confirmación: cambio de estado de UN SOLO FRAME (cero animación)
        barbero = self.combo_barbero.get()
        simbolo = self.simbolo_fn()
        self.mensaje.configure(
            text=f"VENTA REGISTRADA: {venta.descripcion.upper()} × {venta.cantidad} — "
                 f"{formato_moneda(venta.total, simbolo)} ({barbero.upper()}). "
                 "PODÉS CARGAR LA SIGUIENTE.",
            text_color=VERDE_TEXTO)
        self.al_guardar()

        # Formulario listo para la próxima venta; barbero y método SE MANTIENEN
        self.combo.set("")
        self.campo_precio.delete(0, "end")
        self.campo_cantidad.delete(0, "end")
        self.campo_cantidad.insert(0, "1")
        self.campo_propina.delete(0, "end")
        self.campo_propina.insert(0, "0")
        # Cliente vacío: vuelve a mostrarse el texto guía «— MOSTRADOR —»
        self.combo_cliente.limpiar()
        self.etiqueta_subtotal.configure(
            text=f"SUBTOTAL: {formato_moneda(0, simbolo)}")
        self.combo.focus_set()


class TarjeteroTotal(ctk.CTkFrame):
    """SUMA TOTAL DEL DÍA (ventas + propinas), gastos y neto.
    Siempre desde disco, nunca de un acumulador en memoria."""

    def __init__(self, master):
        super().__init__(master, fg_color=ACENTO_AZUL, corner_radius=8)
        ctk.CTkLabel(self, text="SUMA TOTAL DEL DÍA", font=F_BASE,
                     text_color="#D6E4F0").pack(padx=20, pady=(8, 0))
        self.valor = ctk.CTkLabel(self, text="$ 0,00", font=F_TOTAL,
                                  text_color="#FFFFFF")
        self.valor.pack(padx=20)
        self.detalle = ctk.CTkLabel(self, text="GASTOS: $ 0,00 · NETO: $ 0,00",
                                    font=("Segoe UI", 12), text_color="#D6E4F0")
        self.detalle.pack(padx=20, pady=(0, 8))

    def actualizar(self, total: float, gastos: float = 0.0,
                   simbolo: str = "$") -> None:
        self.valor.configure(text=formato_moneda(total, simbolo))
        self.detalle.configure(
            text=f"GASTOS: {formato_moneda(gastos, simbolo)} · "
                 f"NETO: {formato_moneda(round(total - gastos, 2), simbolo)}")


class TablaRegistroDiario(ctk.CTkFrame):
    """Tabla del día en tiempo real, con barbero, cliente, método y propina."""

    COLUMNAS = (
        ("hora", "HORA", 80, "center"),
        ("barbero", "BARBERO", 100, "center"),
        ("tipo", "TIPO", 85, "center"),
        ("descripcion", "DESCRIPCIÓN", 240, "w"),
        ("cliente", "CLIENTE", 110, "w"),
        ("metodo", "MÉTODO", 170, "center"),
        ("cantidad", "CANT.", 55, "center"),
        ("subtotal", "SUBTOTAL", 110, "e"),
        ("propina", "PROPINA", 90, "e"),
        ("total", "TOTAL", 110, "e"),
    )

    def __init__(self, master, simbolo_fn):
        super().__init__(master, fg_color=FONDO_PANEL, corner_radius=8)
        self.simbolo_fn = simbolo_fn
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(self, text="TABLA DEL DÍA (TIEMPO REAL)", font=F_GRANDE,
                     text_color=TEXTO_PRINCIPAL, anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(10, 4))
        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.tree = marco.tree
        self.tree.tag_configure("par", background=FILA_PAR)

    def cargar(self, ventas: list[tuple]) -> None:
        simbolo = self.simbolo_fn()
        self.tree.delete(*self.tree.get_children())
        for i, f in enumerate(ventas):
            (vid, fecha_hora, barbero, tipo, descripcion, cliente, metodo,
             precio, cantidad, subtotal, propina, total) = f
            hora = fecha_hora.split("T")[1] if "T" in fecha_hora else fecha_hora
            tag = ("par",) if i % 2 == 1 else ()
            self.tree.insert("", "end", iid=str(vid), tags=tag, values=(
                hora, barbero, str(tipo).upper(), descripcion, cliente or "—",
                str(metodo).upper(), cantidad, formato_moneda(subtotal, simbolo),
                formato_moneda(propina, simbolo) if propina > 0 else "—",
                formato_moneda(total, simbolo)))
        if ventas:
            self.tree.see(self.tree.get_children()[-1])


# ==================================================================
# ADMINISTRACIÓN (protegida con clave)
# ==================================================================
class PanelAdmin(ctk.CTkFrame):
    """Sub-pestañas: BARBEROS, INVENTARIO, MOVIMIENTOS, GASTOS,
    CLIENTES y MÉTODOS Y MONEDA."""

    def __init__(self, master, admin_service, repo_barberos, repo_catalogo,
                 repo_ventas, repo_metodos, repo_clientes, gasto_service,
                 repo_adelantos, simbolo_fn, al_cambiar_datos):
        super().__init__(master, fg_color=FONDO_PANEL, corner_radius=8)
        self.admin = admin_service
        self.repo_barberos = repo_barberos
        self.repo_catalogo = repo_catalogo
        self.repo_ventas = repo_ventas
        self.repo_metodos = repo_metodos
        self.repo_clientes = repo_clientes
        self.gasto_service = gasto_service
        self.repo_adelantos = repo_adelantos
        self.simbolo_fn = simbolo_fn
        self.al_cambiar_datos = al_cambiar_datos

        fila = ctk.CTkFrame(self, fg_color="transparent")
        fila.pack(fill="x", padx=8, pady=(8, 0))
        ctk.CTkLabel(fila, text="PANEL DE ADMINISTRACIÓN", font=F_GRANDE,
                     text_color=TEXTO_PRINCIPAL).pack(side="left")
        ctk.CTkButton(fila, text="CAMBIAR CLAVE", font=F_BASE, width=180,
                      height=40, fg_color=BOTON_NEUTRO,
                      hover_color=BOTON_NEUTRO_HOVER,
                      text_color=TEXTO_PRINCIPAL,
                      command=self._cambiar_clave).pack(side="right")

        self.subtabs = ctk.CTkTabview(
            self, fg_color=FONDO_PRINCIPAL,
            segmented_button_fg_color=CAMPO_FONDO,
            segmented_button_selected_color=ACENTO_ROJO,
            segmented_button_selected_hover_color=HOVER_ROJO,
            segmented_button_unselected_color=SEG_NO_SELECCIONADO,
            segmented_button_unselected_hover_color=SEG_NO_SELEC_HOVER,
            text_color="#FFFFFF", anchor="w")
        self.subtabs.pack(fill="both", expand=True, padx=8, pady=8)

        self.pest_barberos = PestañaBarberos(self.subtabs.add(" BARBEROS "),
                                             self.admin, self.repo_barberos,
                                             self.repo_adelantos,
                                             self.simbolo_fn,
                                             self.al_cambiar_datos)
        self.pest_barberos.pack(fill="both", expand=True)
        self.pest_inventario = PestañaInventario(self.subtabs.add(" INVENTARIO "),
                                                 self.admin, self.simbolo_fn,
                                                 self.al_cambiar_datos)
        self.pest_inventario.pack(fill="both", expand=True)
        self.pest_movimientos = PestañaMovimientos(
            self.subtabs.add(" MOVIMIENTOS "), self.admin, self.repo_ventas,
            self.repo_barberos, self.repo_metodos, self.repo_clientes,
            self.simbolo_fn, self.al_cambiar_datos)
        self.pest_movimientos.pack(fill="both", expand=True)
        self.pest_gastos = PestañaGastos(self.subtabs.add(" GASTOS "),
                                         self.gasto_service, self.simbolo_fn,
                                         self.al_cambiar_datos)
        self.pest_gastos.pack(fill="both", expand=True)
        self.pest_clientes = PestañaClientes(self.subtabs.add(" CLIENTES "),
                                             self.admin, self.repo_clientes,
                                             self.al_cambiar_datos)
        self.pest_clientes.pack(fill="both", expand=True)
        self.pest_metodos = PestañaMetodosPago(
            self.subtabs.add(" MÉTODOS Y MONEDA "), self.admin,
            self.repo_metodos, self.al_cambiar_datos)
        self.pest_metodos.pack(fill="both", expand=True)

    def refrescar(self) -> None:
        self.pest_barberos.refrescar()
        self.pest_inventario.refrescar()
        self.pest_movimientos.refrescar()
        self.pest_gastos.refrescar()
        self.pest_clientes.refrescar()
        self.pest_metodos.refrescar()

    def _cambiar_clave(self) -> None:
        actual = simpledialog.askstring("CAMBIAR CLAVE", "CLAVE ACTUAL:",
                                        show="•", parent=self)
        if actual is None:
            return
        nueva = simpledialog.askstring("CAMBIAR CLAVE", "CLAVE NUEVA (MÍN. 4):",
                                       show="•", parent=self)
        if nueva is None:
            return
        try:
            self.admin.cambiar_clave(actual, nueva)
            messagebox.showinfo("CAMBIAR CLAVE",
                                "LA CLAVE DE ADMINISTRACIÓN SE CAMBIÓ "
                                "CORRECTAMENTE.", parent=self)
        except ErrorValidacion as exc:
            messagebox.showwarning("CAMBIAR CLAVE", str(exc).upper(), parent=self)


def _formulario(master, campos) -> dict[str, ctk.CTkEntry]:
    """Fila de etiqueta+entry por cada campo; devuelve {nombre: entry}."""
    entradas = {}
    for fila, (nombre, etiqueta, ancho, placeholder) in enumerate(campos):
        ctk.CTkLabel(master, text=etiqueta, font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=fila, column=0, sticky="e",
                                                  padx=(8, 8), pady=4)
        entrada = ctk.CTkEntry(master, font=F_BASE, width=ancho, height=40,
                               fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                               text_color=TEXTO_PRINCIPAL,
                               placeholder_text=placeholder)
        entrada.grid(row=fila, column=1, sticky="w", pady=4)
        entradas[nombre] = entrada
    return entradas


class PestañaBarberos(ctk.CTkFrame):
    """ABM del equipo + comisión % de cada barbero (0–100) + ADELANTOS
    que el dueño les entrega a cuenta de la liquidación (Etapa 1.8).

    La comisión se calcula SOBRE LO FACTURADO; las propinas son 100 %
    del barbero. Los adelantos son EGRESO de caja (hoja BALANCE del
    reporte) y se descuentan del NETO A COBRAR del barbero en su hoja
    individual de liquidación."""

    COLUMNAS = (("id", "ID", 50, "center"), ("nombre", "NOMBRE", 240, "w"),
                ("comision", "COMISIÓN %", 110, "center"),
                ("estado", "ESTADO", 110, "center"))

    COLUMNAS_ADELANTOS = (("fecha", "FECHA", 155, "center"),
                          ("monto", "MONTO", 130, "e"),
                          ("nota", "NOTA", 230, "w"))

    def __init__(self, master, admin, repo_barberos, repo_adelantos,
                 simbolo_fn, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.admin, self.repo = admin, repo_barberos
        self.repo_adelantos = repo_adelantos
        self.simbolo_fn = simbolo_fn
        self.al_cambiar_datos = al_cambiar_datos
        # El panel de ADELANTOS necesita más aire que la tabla de barberos
        # (fecha + monto + nota), por eso la derecha pesa más.
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        # -- fila 0: ficha del barbero (nombre + comisión) --------------
        form = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        form.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 8))
        self.campos = _formulario(form, [
            ("nombre", "NOMBRE:", 240, "EJ.: JULIANO"),
            ("comision", "COMISIÓN %:", 90, "EJ.: 10")])
        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.grid(row=0, column=2, rowspan=2, padx=16)
        # Botones en DOS columnas (3 + 2): la ficha queda baja y la fila
        # de tablas (barberos | adelantos) gana altura útil.
        for i, (texto, comando, color) in enumerate((
                ("AGREGAR", self._agregar, ACENTO_VERDE),
                ("RENOMBRAR", self._renombrar, ACENTO_AZUL),
                ("GUARDAR COMISIÓN", self._guardar_comision, ACENTO_AZUL),
                ("ACTIVAR / DESACTIVAR", self._alternar_estado, BOTON_NEUTRO),
                ("ELIMINAR", self._eliminar, ACENTO_ROJO))):
            # Los botones neutros toman el color de texto del tema para
            # seguir siendo legibles en MODO CLARO.
            extra = ({"text_color": TEXTO_PRINCIPAL,
                      "hover_color": BOTON_NEUTRO_HOVER}
                     if color == BOTON_NEUTRO else {"text_color": "#FFFFFF"})
            ctk.CTkButton(botones, text=texto, font=F_BASE, width=210, height=40,
                          fg_color=color, command=comando, **extra
                          ).grid(row=i % 3, column=i // 3, padx=4, pady=3)

        _estilo_treeview(self)
        # -- fila 1 izquierda: tabla de barberos -------------------------
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._cargar_seleccion())

        # -- fila 1 derecha: panel de ADELANTOS --------------------------
        panel = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        panel.grid(row=1, column=1, sticky="nsew", padx=4, pady=4)
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        self.titulo_adelantos = ctk.CTkLabel(
            panel, text="ADELANTOS — (ELEGÍ UN BARBERO)", font=F_GRANDE,
            text_color=TEXTO_PRINCIPAL, anchor="w")
        self.titulo_adelantos.grid(row=0, column=0, sticky="ew",
                                   padx=12, pady=(10, 4))

        carga = ctk.CTkFrame(panel, fg_color="transparent")
        carga.grid(row=1, column=0, sticky="ew", padx=12)
        ctk.CTkLabel(carga, text="MONTO:", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=0,
                                                  sticky="e", padx=(0, 8), pady=4)
        self.campo_monto_adelanto = ctk.CTkEntry(
            carga, font=F_BASE, width=150, height=40, fg_color=CAMPO_FONDO,
            border_color=CAMPO_BORDE, text_color=TEXTO_PRINCIPAL,
            placeholder_text="EJ.: 50000")
        self.campo_monto_adelanto.grid(row=0, column=1, sticky="w", pady=4)
        ctk.CTkLabel(carga, text="NOTA (OPC.):", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=2,
                                                  sticky="e", padx=(16, 8), pady=4)
        self.campo_nota_adelanto = ctk.CTkEntry(
            carga, font=F_BASE, width=230, height=40, fg_color=CAMPO_FONDO,
            border_color=CAMPO_BORDE, text_color=TEXTO_PRINCIPAL,
            placeholder_text="EJ.: A CUENTA DE SUELDO")
        self.campo_nota_adelanto.grid(row=0, column=3, sticky="w", pady=4)

        botones_ad = ctk.CTkFrame(panel, fg_color="transparent")
        botones_ad.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 4))
        ctk.CTkButton(botones_ad, text="REGISTRAR ADELANTO", font=F_BASE,
                      width=220, height=40, fg_color=ACENTO_VERDE,
                      text_color="#FFFFFF",
                      command=self._registrar_adelanto).pack(side="left",
                                                             padx=(0, 8))
        ctk.CTkButton(botones_ad, text="ELIMINAR ADELANTO", font=F_BASE,
                      width=210, height=40, fg_color=ACENTO_ROJO,
                      text_color="#FFFFFF",
                      command=self._eliminar_adelanto).pack(side="left")

        marco_ad = _arbol(panel, self.COLUMNAS_ADELANTOS, None)
        marco_ad.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 4))
        self.tree_adelantos = marco_ad.tree
        ctk.CTkLabel(
            panel, font=("Segoe UI", 12), text_color=TEXTO_SUAVE,
            justify="left", anchor="w", wraplength=640,
            text="LOS ADELANTOS SON UN EGRESO DE CAJA (HOJA BALANCE DEL "
                 "REPORTE) Y SE DESCUENTAN DEL NETO A COBRAR DEL BARBERO "
                 "EN SU HOJA DE LIQUIDACIÓN."
        ).grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        self.refrescar()

    def _seleccion(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _cargar_seleccion(self) -> None:
        sel = self.tree.selection()
        if sel:
            valores = self.tree.item(sel[0], "values")
            self.campos["nombre"].delete(0, "end")
            self.campos["nombre"].insert(0, valores[1])
            self.campos["comision"].delete(0, "end")
            self.campos["comision"].insert(
                0, valores[2].replace("%", "").strip())
        self._refrescar_adelantos()

    def refrescar(self) -> None:
        # Conservar la selección a través del reconstruido: sin esto,
        # registrar un adelanto dispara el refresco global, el árbol
        # pierde la fila marcada y el panel de ADELANTOS se vaciaría.
        seleccion_previa = self._seleccion()
        self.tree.delete(*self.tree.get_children())
        for b in self.repo.listar(solo_activos=False):
            self.tree.insert("", "end", iid=str(b.id), values=(
                b.id, b.nombre, f"{b.comision:g} %",
                "ACTIVO" if b.activo else "INACTIVO"))
        if (seleccion_previa is not None
                and self.tree.exists(str(seleccion_previa))):
            self.tree.selection_set(str(seleccion_previa))
        self._refrescar_adelantos()

    # ---------------- Adelantos (Etapa 1.8) ----------------
    def _refrescar_adelantos(self) -> None:
        """Lista los últimos adelantos del barbero SELECCIONADO en la
        tabla de la izquierda (siempre desde disco)."""
        self.tree_adelantos.delete(*self.tree_adelantos.get_children())
        bid = self._seleccion()
        if bid is None:
            self.titulo_adelantos.configure(
                text="ADELANTOS — (ELEGÍ UN BARBERO)")
            return
        barbero = self.repo.obtener(bid)
        if barbero is None:
            self.titulo_adelantos.configure(
                text="ADELANTOS — (ELEGÍ UN BARBERO)")
            return
        self.titulo_adelantos.configure(
            text=f"ADELANTOS — {barbero.nombre.upper()}")
        simbolo = self.simbolo_fn()
        for aid, fecha, _nom, monto, nota in \
                self.repo_adelantos.listar_por_barbero(bid):
            self.tree_adelantos.insert("", "end", iid=str(aid), values=(
                datetime.fromisoformat(fecha).strftime("%d/%m/%Y %H:%M"),
                formato_moneda(monto, simbolo), nota or "—"))

    def _adelanto_seleccion(self):
        sel = self.tree_adelantos.selection()
        return int(sel[0]) if sel else None

    def _registrar_adelanto(self) -> None:
        bid = self._seleccion()
        if bid is None:
            messagebox.showwarning(
                "ADELANTOS", "NO SE REGISTRÓ EL ADELANTO PORQUE NO HAY "
                "NINGÚN BARBERO SELECCIONADO EN LA TABLA DE LA IZQUIERDA. "
                "TOCÁ UNA FILA Y VOLVÉ A INTENTAR.", parent=self)
            return
        try:
            self.admin.registrar_adelanto(
                bid, self.campo_monto_adelanto.get().replace(",", "."),
                self.campo_nota_adelanto.get())
        except ErrorValidacion as exc:
            messagebox.showwarning("ADELANTOS", str(exc).upper(), parent=self)
            return
        self.campo_monto_adelanto.delete(0, "end")
        self.campo_nota_adelanto.delete(0, "end")
        self._refrescar_adelantos(); self.al_cambiar_datos()

    def _eliminar_adelanto(self) -> None:
        aid = self._adelanto_seleccion()
        if aid is None:
            messagebox.showwarning(
                "ADELANTOS", "NO SE ELIMINÓ NADA PORQUE NO HAY NINGÚN "
                "ADELANTO SELECCIONADO. TOCÁ UNA FILA DE LA LISTA DE "
                "ADELANTOS Y VOLVÉ A INTENTAR.", parent=self)
            return
        valores = self.tree_adelantos.item(str(aid), "values")
        if not messagebox.askyesno(
                "ADELANTOS",
                f"¿ELIMINAR EL ADELANTO DE {valores[1]} DEL {valores[0]}? "
                "EL NETO A COBRAR DEL BARBERO SE RECALCULA SOLO.",
                parent=self):
            return
        try:
            self.admin.eliminar_adelanto(aid)
        except ErrorValidacion as exc:
            messagebox.showwarning("ADELANTOS", str(exc).upper(), parent=self)
            return
        self._refrescar_adelantos(); self.al_cambiar_datos()

    def _agregar(self) -> None:
        try:
            self.admin.agregar_barbero(
                self.campos["nombre"].get(),
                comision=self.campos["comision"].get().replace(",", ".") or 50)
        except ErrorValidacion as exc:
            messagebox.showwarning("BARBEROS", str(exc).upper(), parent=self)
            return
        self.campos["nombre"].delete(0, "end")
        self.campos["comision"].delete(0, "end")
        self.refrescar(); self.al_cambiar_datos()

    def _renombrar(self) -> None:
        bid = self._seleccion()
        if bid is None:
            messagebox.showwarning("BARBEROS", "NO SE RENOMBRÓ A NADIE PORQUE NO "
                                   "HAY NINGÚN BARBERO SELECCIONADO EN LA TABLA. "
                                   "TOCÁ UNA FILA Y VOLVÉ A INTENTAR.", parent=self)
            return
        try:
            self.admin.renombrar_barbero(bid, self.campos["nombre"].get())
        except ErrorValidacion as exc:
            messagebox.showwarning("BARBEROS", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()

    def _guardar_comision(self) -> None:
        bid = self._seleccion()
        if bid is None:
            messagebox.showwarning("BARBEROS", "NO SE GUARDÓ LA COMISIÓN PORQUE "
                                   "NO HAY NINGÚN BARBERO SELECCIONADO EN LA TABLA. "
                                   "TOCÁ UNA FILA Y VOLVÉ A INTENTAR.", parent=self)
            return
        try:
            self.admin.set_comision_barbero(
                bid, self.campos["comision"].get().replace(",", "."))
        except ErrorValidacion as exc:
            messagebox.showwarning("BARBEROS", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()

    def _alternar_estado(self) -> None:
        bid = self._seleccion()
        if bid is None:
            return
        barbero = self.repo.obtener(bid)
        if barbero:
            self.repo.set_activo(bid, not barbero.activo)
            self.refrescar(); self.al_cambiar_datos()

    def _eliminar(self) -> None:
        bid = self._seleccion()
        if bid is None:
            return
        nombre = self.tree.item(str(bid), "values")[1]
        if not messagebox.askyesno("BARBEROS",
                                   f"¿ELIMINAR A {nombre.upper()}? SOLO ES POSIBLE "
                                   "SI NO TIENE VENTAS REGISTRADAS.", parent=self):
            return
        try:
            self.admin.eliminar_barbero(bid)
        except ErrorValidacion as exc:
            messagebox.showwarning("BARBEROS", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()


class PestañaInventario(ctk.CTkFrame):
    COLUMNAS = (("id", "ID", 50, "center"), ("nombre", "NOMBRE", 260, "w"),
                ("tipo", "TIPO", 100, "center"), ("precio", "PRECIO", 120, "e"),
                ("estado", "ESTADO", 110, "center"))

    def __init__(self, master, admin, simbolo_fn, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.admin = admin
        self.simbolo_fn = simbolo_fn
        self.al_cambiar_datos = al_cambiar_datos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        form = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        form.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        self.campos = _formulario(form, [
            ("nombre", "NOMBRE:", 260, "EJ.: CORTE"),
            ("precio", "PRECIO:", 130, "EJ.: 8500")])
        ctk.CTkLabel(form, text="TIPO:", font=F_BASE, text_color=TEXTO_SUAVE
                     ).grid(row=0, column=2, sticky="e", padx=(16, 8))
        self.tipo_var = ctk.StringVar(value=TipoItem.SERVICIO.value)
        ctk.CTkComboBox(form, values=[t.value for t in TipoItem],
                        variable=self.tipo_var, font=F_BASE, width=170, height=40,
                        fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                        button_color=BOTON_COMBO, text_color=TEXTO_PRINCIPAL,
                        dropdown_fg_color=DESPLEGABLE_FONDO,
                        dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
                        state="readonly").grid(row=0, column=3, sticky="w")

        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.grid(row=0, column=4, rowspan=2, padx=16)
        for texto, comando, color in (
                ("AGREGAR", self._agregar, ACENTO_VERDE),
                ("GUARDAR CAMBIOS", self._actualizar, ACENTO_AZUL),
                ("ACTIVAR / DESACTIVAR", self._alternar_estado, BOTON_NEUTRO),
                ("ELIMINAR", self._eliminar, ACENTO_ROJO)):
            # Los botones neutros toman el color de texto del tema para
            # seguir siendo legibles en MODO CLARO.
            extra = ({"text_color": TEXTO_PRINCIPAL,
                      "hover_color": BOTON_NEUTRO_HOVER}
                     if color == BOTON_NEUTRO else {"text_color": "#FFFFFF"})
            ctk.CTkButton(botones, text=texto, font=F_BASE, width=210, height=40,
                          fg_color=color, command=comando, **extra).pack(pady=3)

        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._cargar_seleccion())
        self.refrescar()

    def _seleccion(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _cargar_seleccion(self) -> None:
        sel = self.tree.selection()
        if sel:
            _id, nombre, tipo, precio, _estado = self.tree.item(sel[0], "values")
            self.campos["nombre"].delete(0, "end")
            self.campos["nombre"].insert(0, nombre)
            self.campos["precio"].delete(0, "end")
            # El precio se muestra con símbolo y miles ("G$ 60.000,00"):
            # al cargarlo en el campo se conservan solo dígitos y la coma
            # decimal — funciona con cualquier símbolo de moneda.
            limpio = re.sub(r"[^\d,]", "", precio).replace(",", ".")
            self.campos["precio"].insert(0, limpio)
            self.tipo_var.set(tipo)

    def refrescar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        simbolo = self.simbolo_fn()
        for i in self.admin.catalogo.listar_todos():
            self.tree.insert("", "end", iid=str(i[0]), values=(
                i[0], i[1], i[2], formato_moneda(i[3], simbolo),
                "ACTIVO" if i[4] else "INACTIVO"))

    def _agregar(self) -> None:
        # Parámetros POR NOMBRE: el orden visual del formulario (nombre,
        # precio, tipo) no coincide con la firma del servicio (nombre, tipo,
        # precio). Llamar por posición desde acá rompe la validación.
        try:
            self.admin.agregar_item(nombre=self.campos["nombre"].get(),
                                    tipo=TipoItem(self.tipo_var.get()),
                                    precio=self.campos["precio"].get().replace(",", "."))
        except ErrorValidacion as exc:
            messagebox.showwarning("INVENTARIO", str(exc).upper(), parent=self)
            return
        self.campos["nombre"].delete(0, "end")
        self.campos["precio"].delete(0, "end")
        self.refrescar(); self.al_cambiar_datos()

    def _actualizar(self) -> None:
        iid = self._seleccion()
        if iid is None:
            messagebox.showwarning("INVENTARIO", "NO SE ACTUALIZÓ NADA PORQUE NO "
                                   "HAY NINGÚN ÍTEM SELECCIONADO. TOCÁ UNA FILA, "
                                   "MODIFICÁ Y VOLVÉ A INTENTAR.", parent=self)
            return
        try:
            self.admin.actualizar_item(iid, nombre=self.campos["nombre"].get(),
                                       tipo=TipoItem(self.tipo_var.get()),
                                       precio=self.campos["precio"].get().replace(",", "."))
        except ErrorValidacion as exc:
            messagebox.showwarning("INVENTARIO", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()

    def _alternar_estado(self) -> None:
        iid = self._seleccion()
        if iid is None:
            return
        item = self.admin.catalogo.obtener(iid)
        if item:
            self.admin.catalogo.set_activo(iid, not bool(item[4]))
            self.refrescar(); self.al_cambiar_datos()

    def _eliminar(self) -> None:
        iid = self._seleccion()
        if iid is None:
            return
        nombre = self.tree.item(str(iid), "values")[1]
        if not messagebox.askyesno("INVENTARIO",
                                   f"¿ELIMINAR «{nombre}» DEL CATÁLOGO? LAS VENTAS "
                                   "YA REGISTRADAS NO SE MODIFICAN.", parent=self):
            return
        try:
            self.admin.eliminar_item(iid)
        except ErrorValidacion as exc:
            messagebox.showwarning("INVENTARIO", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()


class PestañaClientes(ctk.CTkFrame):
    """Base de clientes (Etapa 1.7): nombre, apellido, celular (clave
    única que identifica al cliente en las estadísticas) y mail opcional.
    Etapa 1.8: FECHA DE NACIMIENTO opcional (DD/MM/AAAA, base del CRM).

    Detector de errores de tipeo: si NOMBRE + MAIL coinciden con una ficha
    existente pero el CELULAR es distinto, se consulta al operador antes
    de guardar (corregir la ficha existente / crear una nueva / cancelar).

    Eliminar un cliente NO toca el historial: las ventas ya registradas
    conservan su nombre como texto.
    """

    COLUMNAS = (("id", "ID", 50, "center"), ("apellido", "APELLIDO", 180, "w"),
                ("nombre", "NOMBRE", 180, "w"), ("celular", "CELULAR", 150, "center"),
                ("mail", "MAIL", 220, "w"),
                ("nacimiento", "NACIMIENTO", 130, "center"))

    def __init__(self, master, admin, repo_clientes, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.admin, self.repo = admin, repo_clientes
        self.al_cambiar_datos = al_cambiar_datos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        form = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        form.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        self.campos = _formulario(form, [
            ("nombre", "NOMBRE *:", 220, "EJ.: JUAN"),
            ("apellido", "APELLIDO *:", 220, "EJ.: PÉREZ"),
            ("celular", "CELULAR *:", 220, "EJ.: 3704111222"),
            ("mail", "MAIL (OPC.):", 220, "EJ.: JUAN@MAIL.COM"),
            ("nacimiento", "NACIMIENTO (OPC.):", 220, "EJ.: 15/08/1990")])
        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.grid(row=0, column=2, rowspan=5, padx=16)
        for texto, comando, color in (
                ("AGREGAR", self._agregar, ACENTO_VERDE),
                ("GUARDAR CAMBIOS", self._actualizar, ACENTO_AZUL),
                ("ELIMINAR", self._eliminar, ACENTO_ROJO)):
            ctk.CTkButton(botones, text=texto, font=F_BASE, width=210, height=40,
                          fg_color=color, text_color="#FFFFFF",
                          command=comando).pack(pady=3)
        ctk.CTkLabel(
            form, font=("Segoe UI", 12), text_color=TEXTO_SUAVE,
            justify="left", wraplength=1080,
            text="EL CELULAR IDENTIFICA A CADA CLIENTE EN LAS ESTADÍSTICAS "
                 "DEL REPORTE: NO PUEDE REPETIRSE. SI NOMBRE + MAIL YA EXISTEN "
                 "CON OTRO CELULAR, SE CONSULTA SI FUE UN ERROR DE TIPEO. "
                 "EL NACIMIENTO ES OPCIONAL Y SE ESCRIBE DD/MM/AAAA "
                 "(EJ.: 15/08/1990). LAS VENTAS YA REGISTRADAS CONSERVAN "
                 "EL NOMBRE AUNQUE EL CLIENTE SE ELIMINE."
        ).grid(row=5, column=0, columnspan=3, sticky="w", padx=8, pady=(2, 8))

        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.tree.bind("<<TreeviewSelect>>", lambda _e: self._cargar_seleccion())
        self.refrescar()

    def _seleccion(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _cargar_seleccion(self) -> None:
        sel = self.tree.selection()
        if sel:
            (_id, apellido, nombre, celular, mail,
             nacimiento) = self.tree.item(sel[0], "values")
            for campo, valor in (("nombre", nombre), ("apellido", apellido),
                                 ("celular", celular),
                                 ("mail", "" if mail == "—" else mail),
                                 ("nacimiento",
                                  "" if nacimiento == "—" else nacimiento)):
                self.campos[campo].delete(0, "end")
                self.campos[campo].insert(0, valor)

    def refrescar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for c in self.repo.listar():
            self.tree.insert("", "end", iid=str(c.id), values=(
                c.id, c.apellido, c.nombre, c.celular, c.mail or "—",
                c.fecha_nacimiento or "—"))

    def _limpiar(self) -> None:
        for campo in self.campos.values():
            campo.delete(0, "end")

    def _datos_formulario(self) -> tuple:
        """(nombre, apellido, celular, mail, fecha_nacimiento) tal como
        están en los campos."""
        return tuple(self.campos[c].get()
                     for c in ("nombre", "apellido", "celular", "mail",
                               "nacimiento"))

    def _agregar(self) -> None:
        datos = self._datos_formulario()
        try:
            self.admin.agregar_cliente(*datos)
        except ClientePosibleDuplicado as exc:
            self._consultar_tipeo_alta(exc, datos)
            return
        except ErrorValidacion as exc:
            messagebox.showwarning("CLIENTES", str(exc).upper(), parent=self)
            return
        self._limpiar()
        self.refrescar(); self.al_cambiar_datos()

    def _consultar_tipeo_alta(self, exc: ClientePosibleDuplicado,
                              datos: tuple) -> None:
        """Coinciden NOMBRE + MAIL con una ficha existente pero el CELULAR
        es otro: se consulta si fue un ERROR DE TIPEO antes de guardar."""
        ex = exc.existente
        respuesta = messagebox.askyesnocancel(
            "CLIENTES",
            f"YA EXISTE UN CLIENTE CON ESE NOMBRE Y MAIL: {ex.apellido}, "
            f"{ex.nombre} — CELULAR {ex.celular}.\n\n"
            f"EL CELULAR QUE ESCRIBISTE ({exc.celular_nuevo}) ES DISTINTO. "
            "¿FUE UN ERROR DE TIPEO?\n\n"
            "• SÍ = CORREGIR LA FICHA EXISTENTE CON EL CELULAR NUEVO.\n"
            "• NO = ES OTRO CLIENTE: CREAR UNA FICHA NUEVA IGUALMENTE.\n"
            "• CANCELAR = NO GUARDAR NADA.",
            parent=self)
        if respuesta is None:
            return
        try:
            if respuesta:      # SÍ: error de tipeo → se corrige la ficha vieja
                self.admin.actualizar_cliente(ex.id, *datos, forzar=True)
                messagebox.showinfo(
                    "CLIENTES",
                    f"SE CORRIGIÓ LA FICHA DE {ex.apellido}, {ex.nombre}: "
                    f"SU CELULAR AHORA ES {exc.celular_nuevo}.", parent=self)
            else:              # NO: es otra persona → ficha nueva forzada
                self.admin.agregar_cliente(*datos, forzar=True)
        except ErrorValidacion as exc2:
            messagebox.showwarning("CLIENTES", str(exc2).upper(), parent=self)
            return
        self._limpiar()
        self.refrescar(); self.al_cambiar_datos()

    def _actualizar(self) -> None:
        cid = self._seleccion()
        if cid is None:
            messagebox.showwarning("CLIENTES", "NO SE ACTUALIZÓ NADA PORQUE NO "
                                   "HAY NINGÚN CLIENTE SELECCIONADO. TOCÁ UNA "
                                   "FILA, MODIFICÁ Y VOLVÉ A INTENTAR.",
                                   parent=self)
            return
        datos = self._datos_formulario()
        try:
            self.admin.actualizar_cliente(cid, *datos)
        except ClientePosibleDuplicado as exc:
            # Otro cliente ya tiene ese nombre + mail con otro celular.
            ex = exc.existente
            if not messagebox.askyesno(
                    "CLIENTES",
                    f"EXISTE OTRO CLIENTE CON ESE NOMBRE Y MAIL: {ex.apellido}, "
                    f"{ex.nombre} — CELULAR {ex.celular}.\n\n"
                    f"EL CELULAR QUE ESCRIBISTE ({exc.celular_nuevo}) ES "
                    "DISTINTO: PODRÍA SER UN ERROR DE TIPEO.\n\n"
                    "• SÍ = GUARDAR LOS CAMBIOS EN LA FICHA SELECCIONADA "
                    "IGUALMENTE.\n"
                    "• NO = NO GUARDAR NADA.", parent=self):
                return
            try:
                self.admin.actualizar_cliente(cid, *datos, forzar=True)
            except ErrorValidacion as exc2:
                messagebox.showwarning("CLIENTES", str(exc2).upper(), parent=self)
                return
        except ErrorValidacion as exc:
            messagebox.showwarning("CLIENTES", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()

    def _eliminar(self) -> None:
        cid = self._seleccion()
        if cid is None:
            messagebox.showwarning("CLIENTES", "NO SE ELIMINÓ NADA PORQUE NO "
                                   "HAY NINGÚN CLIENTE SELECCIONADO. TOCÁ UNA "
                                   "FILA Y VOLVÉ A INTENTAR.", parent=self)
            return
        valores = self.tree.item(str(cid), "values")
        if not messagebox.askyesno(
                "CLIENTES",
                f"¿ELIMINAR AL CLIENTE «{valores[2]} {valores[1]}»? LAS VENTAS "
                "YA REGISTRADAS CONSERVAN SU NOMBRE EN EL HISTORIAL.",
                parent=self):
            return
        try:
            self.admin.eliminar_cliente(cid)
        except ErrorValidacion as exc:
            messagebox.showwarning("CLIENTES", str(exc).upper(), parent=self)
            return
        self._limpiar()
        self.refrescar(); self.al_cambiar_datos()


class PestañaMetodosPago(ctk.CTkFrame):
    """Medios de cobro que ofrece la caja + MONEDA del sistema.

    Eliminar un método NO toca el historial: las ventas ya registradas
    guardan el nombre como texto. Protección: la caja siempre necesita
    al menos UN método de pago (lo valida AdminService).

    La moneda cambia el SÍMBOLO con que se leen todos los importes del
    sistema (pantalla y reportes). No convierte ni cotiza valores.
    """

    COLUMNAS = (("id", "ID", 60, "center"),
                ("nombre", "MÉTODO DE PAGO", 320, "w"))

    def __init__(self, master, admin, repo_metodos, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.admin, self.repo = admin, repo_metodos
        self.al_cambiar_datos = al_cambiar_datos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # -- Sección 1: métodos de pago ---------------------------------
        form = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        form.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        self.campos = _formulario(form, [
            ("nombre", "NOMBRE:", 280, "EJ.: BILLETERA VIRTUAL")])
        botones = ctk.CTkFrame(form, fg_color="transparent")
        botones.grid(row=0, column=2, padx=16)
        for texto, comando, color in (
                ("AGREGAR", self._agregar, ACENTO_VERDE),
                ("ELIMINAR", self._eliminar, ACENTO_ROJO)):
            ctk.CTkButton(botones, text=texto, font=F_BASE, width=210, height=40,
                          fg_color=color, text_color="#FFFFFF",
                          command=comando).pack(pady=3)
        ctk.CTkLabel(
            form, font=("Segoe UI", 12), text_color=TEXTO_SUAVE,
            text="LAS VENTAS YA REGISTRADAS CONSERVAN EL MÉTODO AUNQUE SE "
                 "ELIMINE. LA CAJA SIEMPRE NECESITA AL MENOS UNO."
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=8, pady=(0, 8))

        # -- Sección 2: moneda del sistema -------------------------------
        moneda = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        moneda.grid(row=1, column=0, sticky="ew", padx=4, pady=(0, 8))
        ctk.CTkLabel(moneda, text="MONEDA DEL SISTEMA:", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=0,
                                                  padx=(12, 8), pady=10)
        self.combo_moneda = ctk.CTkComboBox(
            moneda, values=list(MONEDAS), font=F_BASE, width=120, height=40,
            fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
            button_color=BOTON_COMBO, text_color=TEXTO_PRINCIPAL,
            dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
            state="readonly")
        self.combo_moneda.grid(row=0, column=1, pady=10)
        self.combo_moneda.set(self.admin.obtener_moneda())
        ctk.CTkButton(moneda, text="GUARDAR MONEDA", font=F_BASE, width=210,
                      height=40, fg_color=ACENTO_AZUL, text_color="#FFFFFF",
                      hover_color=HOVER_AZUL,
                      command=self._guardar_moneda).grid(row=0, column=2,
                                                         padx=12)
        ctk.CTkLabel(
            moneda, font=("Segoe UI", 12), text_color=TEXTO_SUAVE,
            text="CAMBIA EL SÍMBOLO CON QUE SE LEEN TODOS LOS IMPORTES "
                 "(PANTALLA Y REPORTES EXCEL). NO MODIFICA PRECIOS NI "
                 "COTIZACIONES."
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10))

        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=2, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.refrescar()

    def _seleccion(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def refrescar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for mid, nombre in self.repo.listar():
            self.tree.insert("", "end", iid=str(mid),
                             values=(mid, nombre.upper()))
        self.combo_moneda.set(self.admin.obtener_moneda())

    def _agregar(self) -> None:
        try:
            self.admin.agregar_metodo_pago(self.campos["nombre"].get())
        except ErrorValidacion as exc:
            messagebox.showwarning("MÉTODOS DE PAGO", str(exc).upper(), parent=self)
            return
        self.campos["nombre"].delete(0, "end")
        self.refrescar(); self.al_cambiar_datos()

    def _eliminar(self) -> None:
        mid = self._seleccion()
        if mid is None:
            messagebox.showwarning("MÉTODOS DE PAGO",
                                   "NO SE ELIMINÓ NADA PORQUE NO HAY NINGÚN "
                                   "MÉTODO SELECCIONADO. TOCÁ UNA FILA Y VOLVÉ "
                                   "A INTENTAR.", parent=self)
            return
        fila = self.repo.obtener(mid)
        nombre = fila[1] if fila else "?"
        if not messagebox.askyesno(
                "MÉTODOS DE PAGO",
                f"¿ELIMINAR EL MÉTODO DE PAGO «{nombre.upper()}»? LAS VENTAS "
                "YA REGISTRADAS CONSERVAN ESE NOMBRE EN EL HISTORIAL.",
                parent=self):
            return
        try:
            self.admin.eliminar_metodo_pago(mid)
        except ErrorValidacion as exc:
            messagebox.showwarning("MÉTODOS DE PAGO", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()

    def _guardar_moneda(self) -> None:
        try:
            self.admin.set_moneda(self.combo_moneda.get())
        except ErrorValidacion as exc:
            messagebox.showwarning("MONEDA", str(exc).upper(), parent=self)
            return
        self.al_cambiar_datos()  # re-etiqueta todos los importes al instante
        messagebox.showinfo(
            "MONEDA",
            f"LA MONEDA DEL SISTEMA AHORA ES {self.combo_moneda.get()}. "
            "TODOS LOS IMPORTES SE MUESTRAN CON ESE SÍMBOLO, EN PANTALLA "
            "Y EN LOS REPORTES.", parent=self)


class PestañaMovimientos(ctk.CTkFrame):
    """Corregir o eliminar ventas ya registradas (errores de carga)."""

    COLUMNAS = (("id", "ID", 50, "center"), ("fecha", "FECHA Y HORA", 150, "center"),
                ("barbero", "BARBERO", 100, "center"), ("tipo", "TIPO", 90, "center"),
                ("descripcion", "DESCRIPCIÓN", 200, "w"), ("cliente", "CLIENTE", 100, "w"),
                ("metodo", "MÉTODO", 170, "center"), ("total", "TOTAL", 100, "e"))

    def __init__(self, master, admin, repo_ventas, repo_barberos, repo_metodos,
                 repo_clientes, simbolo_fn, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.admin, self.repo_ventas = admin, repo_ventas
        self.repo_barberos = repo_barberos
        self.repo_metodos = repo_metodos
        self.repo_clientes = repo_clientes
        self.simbolo_fn = simbolo_fn
        self.al_cambiar_datos = al_cambiar_datos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        filtro = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        filtro.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        hoy = date.today().isoformat()
        ctk.CTkLabel(filtro, text="DESDE (AAAA-MM-DD):", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=0, padx=(12, 6), pady=10)
        self.desde = ctk.CTkEntry(filtro, font=F_BASE, width=140, height=40,
                                  fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                  text_color=TEXTO_PRINCIPAL)
        self.desde.grid(row=0, column=1, pady=10)
        self.desde.insert(0, hoy)
        ctk.CTkLabel(filtro, text="HASTA:", font=F_BASE, text_color=TEXTO_SUAVE
                     ).grid(row=0, column=2, padx=(12, 6))
        self.hasta = ctk.CTkEntry(filtro, font=F_BASE, width=140, height=40,
                                  fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                  text_color=TEXTO_PRINCIPAL)
        self.hasta.grid(row=0, column=3, pady=10)
        self.hasta.insert(0, hoy)
        ctk.CTkButton(filtro, text="BUSCAR", font=F_BASE, width=130, height=40,
                      fg_color=ACENTO_AZUL, text_color="#FFFFFF",
                      command=self.refrescar).grid(row=0, column=4, padx=12)
        ctk.CTkButton(filtro, text="EDITAR SELECCIONADO", font=F_BASE, width=210,
                      height=40, fg_color=ACENTO_VERDE, text_color="#FFFFFF",
                      command=self._editar).grid(row=0, column=5, padx=6)
        ctk.CTkButton(filtro, text="ELIMINAR SELECCIONADO", font=F_BASE, width=210,
                      height=40, fg_color=ACENTO_ROJO, text_color="#FFFFFF",
                      command=self._eliminar).grid(row=0, column=6, padx=6)

        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.refrescar()

    def refrescar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        d, h = self.desde.get().strip(), self.hasta.get().strip()
        simbolo = self.simbolo_fn()
        try:
            filas = self.repo_ventas.ventas_entre_fechas(d, h)
        except Exception:
            messagebox.showwarning(
                "MOVIMIENTOS", "NO SE BUSCARON MOVIMIENTOS PORQUE LA FECHA NO "
                "TIENE FORMATO AAAA-MM-DD. CORREGILA COMO 2026-10-06 Y TOCÁ "
                "BUSCAR.", parent=self)
            return
        for f in filas:
            self.tree.insert("", "end", iid=str(f[0]), values=(
                f[0], f[1].replace("T", " "), f[2], str(f[3]).upper(), f[4],
                f[5] or "—", str(f[6]).upper(), formato_moneda(f[11], simbolo)))

    def _editar(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("MOVIMIENTOS", "NO SE EDITÓ NADA PORQUE NO HAY "
                                   "NINGÚN MOVIMIENTO SELECCIONADO. TOCÁ UNA FILA "
                                   "Y VOLVÉ A INTENTAR.", parent=self)
            return
        vid = int(sel[0])
        f = self.repo_ventas.obtener(vid)
        if f is None:
            return
        # SELECT_VENTAS devuelve una tupla; el diálogo trabaja con dict.
        venta = {"id": f[0], "barbero": f[2], "tipo": f[3], "descripcion": f[4],
                 "cliente": f[5], "metodo_pago": f[6], "precio_unitario": f[7],
                 "cantidad": f[8], "propina": f[10]}
        DialogoEditarVenta(self, venta, self.repo_barberos, self.repo_metodos,
                           self.repo_clientes, self._guardar_edicion)

    def _guardar_edicion(self, vid: int, campos: dict) -> bool:
        try:
            self.admin.editar_venta(vid, barbero_id=campos["barbero_id"],
                                    tipo=campos["tipo"],
                                    descripcion=campos["descripcion"],
                                    precio_unitario=campos["precio"],
                                    cantidad=campos["cantidad"],
                                    cliente=campos["cliente"],
                                    cliente_id=campos["cliente_id"],
                                    metodo_pago=campos["metodo"],
                                    propina=campos["propina"])
        except ErrorValidacion as exc:
            messagebox.showwarning("MOVIMIENTOS", str(exc).upper(), parent=self)
            return False
        self.refrescar(); self.al_cambiar_datos()
        return True

    def _eliminar(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        vid = int(sel[0])
        valores = self.tree.item(sel[0], "values")
        if not messagebox.askyesno(
                "MOVIMIENTOS",
                f"¿ELIMINAR EL MOVIMIENTO #{vid} ({valores[4]} — {valores[7]})? "
                "ESTA ACCIÓN NO SE PUEDE DESHACER.", parent=self):
            return
        try:
            self.admin.eliminar_venta(vid)
        except ErrorValidacion as exc:
            messagebox.showwarning("MOVIMIENTOS", str(exc).upper(), parent=self)
            return
        self.refrescar(); self.al_cambiar_datos()


class DialogoEditarVenta(ctk.CTkToplevel):
    """Ventana modal para corregir una venta (barbero equivocado, etc.)."""

    def __init__(self, master, venta, repo_barberos, repo_metodos,
                 repo_clientes, al_guardar):
        super().__init__(master)
        self.venta = venta
        self.al_guardar = al_guardar
        self.title(f"EDITAR MOVIMIENTO #{venta['id']}")
        self.configure(fg_color=FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._barberos = {b.nombre: b.id for b in repo_barberos.listar()}
        # Métodos administrables: se muestran en mayúsculas y se guardan
        # con la escritura canónica. Si la venta usa un método histórico
        # ya eliminado, se ofrece igual para no perderlo al corregir.
        self._metodos = {nombre.upper(): nombre
                         for nombre in repo_metodos.listar_nombres()}
        metodo_actual = str(venta["metodo_pago"] or "")
        if metodo_actual.upper() not in self._metodos:
            self._metodos[metodo_actual.upper()] = metodo_actual

        # Clientes registrados con AUTOCOMPLETADO: se escribe y sugiere
        # las fichas que coinciden. Si la venta guarda un texto histórico
        # que ya no está en la base, se ofrece como opción extra para no
        # perderlo al corregir.
        self._clientes = {}
        for c in repo_clientes.listar():
            self._clientes[_display_cliente(c)] = (c.id, c.nombre_completo)
        cliente_actual = venta["cliente"] or ""
        valores_cliente = [MOSTRADOR] + list(self._clientes)
        coincide = next((d for d, (_i, t) in self._clientes.items()
                         if t == cliente_actual), None)
        if cliente_actual and coincide is None:
            valores_cliente.append(cliente_actual)  # texto histórico libre
        cliente_inicial = coincide or cliente_actual or MOSTRADOR

        def proveedor_clientes(texto: str) -> list[str]:
            texto = (texto or "").strip()
            if not texto or texto == MOSTRADOR:
                return valores_cliente
            return [_display_cliente(c)
                    for c in repo_clientes.buscar(texto, limite=8)]

        campos = ctk.CTkFrame(self, fg_color="transparent")
        campos.pack(padx=20, pady=16)

        def fila(f, etiqueta, widget):
            ctk.CTkLabel(campos, text=etiqueta, font=F_BASE,
                         text_color=TEXTO_SUAVE).grid(row=f, column=0, sticky="e",
                                                      padx=(0, 8), pady=4)
            widget.grid(row=f, column=1, sticky="w", pady=4)
            return widget

        self.barbero = fila(0, "BARBERO:", ctk.CTkComboBox(
            campos, values=list(self._barberos), font=F_BASE, width=260, height=40,
            fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE, button_color=BOTON_COMBO,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE,
            state="readonly"))
        self.barbero.set(venta["barbero"])

        self.tipo = fila(1, "TIPO:", ctk.CTkComboBox(
            campos, values=[t.value for t in TipoItem], font=F_BASE, width=260,
            height=40, fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
            button_color=BOTON_COMBO, text_color=TEXTO_PRINCIPAL,
            dropdown_fg_color=DESPLEGABLE_FONDO, dropdown_text_color=TEXTO_PRINCIPAL,
            dropdown_font=F_BASE, state="readonly"))
        self.tipo.set(str(venta["tipo"]).upper())

        def entrada(f, etiqueta, valor):
            e = ctk.CTkEntry(campos, font=F_BASE, width=260, height=40,
                             fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                             text_color=TEXTO_PRINCIPAL)
            e.insert(0, str(valor))
            return fila(f, etiqueta, e)

        self.descripcion = entrada(2, "DESCRIPCIÓN:", venta["descripcion"])
        self.precio = entrada(3, "PRECIO:", venta["precio_unitario"])
        self.cantidad = entrada(4, "CANTIDAD:", venta["cantidad"])

        self.combo_cliente = fila(5, "CLIENTE:", ComboAutocompletable(
            campos, proveedor=proveedor_clientes, values=valores_cliente,
            font=F_BASE, width=260, height=40,
            fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE, button_color=BOTON_COMBO,
            text_color=TEXTO_PRINCIPAL, dropdown_fg_color=DESPLEGABLE_FONDO,
            dropdown_text_color=TEXTO_PRINCIPAL, dropdown_font=F_BASE))
        self.combo_cliente.set(cliente_inicial)

        self.metodo = fila(6, "MÉTODO DE PAGO:", ctk.CTkComboBox(
            campos, values=list(self._metodos), font=F_BASE, width=260,
            height=40, fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
            button_color=BOTON_COMBO, text_color=TEXTO_PRINCIPAL,
            dropdown_fg_color=DESPLEGABLE_FONDO, dropdown_text_color=TEXTO_PRINCIPAL,
            dropdown_font=F_BASE, state="readonly"))
        self.metodo.set(metodo_actual.upper())
        self.propina = entrada(7, "PROPINA:", venta["propina"])

        botones = ctk.CTkFrame(self, fg_color="transparent")
        botones.pack(pady=(0, 16))
        ctk.CTkButton(botones, text="GUARDAR CAMBIOS", font=F_BASE, width=200,
                      height=44, fg_color=ACENTO_VERDE, text_color="#FFFFFF",
                      command=self._guardar).pack(side="left", padx=8)
        ctk.CTkButton(botones, text="CANCELAR", font=F_BASE, width=130, height=44,
                      fg_color=BOTON_NEUTRO, hover_color=BOTON_NEUTRO_HOVER,
                      text_color=TEXTO_PRINCIPAL,
                      command=self.destroy).pack(side="left", padx=8)

    def _guardar(self) -> None:
        sel_cli = self.combo_cliente.get()
        if sel_cli in self._clientes:
            cli_id, cli_txt = self._clientes[sel_cli]
        elif sel_cli == MOSTRADOR:
            cli_id, cli_txt = None, ""
        else:
            cli_id, cli_txt = None, sel_cli   # texto histórico libre
        campos = {
            "barbero_id": self._barberos.get(self.barbero.get(), 0),
            "tipo": TipoItem(self.tipo.get()),
            "descripcion": self.descripcion.get(),
            "precio": self.precio.get().replace(",", "."),
            "cantidad": self.cantidad.get(),
            "cliente": cli_txt,
            "cliente_id": cli_id,
            "metodo": self._metodos.get(self.metodo.get(), self.metodo.get()),
            "propina": self.propina.get().replace(",", ".") or 0,
        }
        if self.al_guardar(self.venta["id"], campos):
            self.destroy()


class PestañaGastos(ctk.CTkFrame):
    COLUMNAS = (("id", "ID", 50, "center"), ("fecha", "FECHA Y HORA", 160, "center"),
                ("categoria", "CATEGORÍA", 160, "w"),
                ("descripcion", "DESCRIPCIÓN", 340, "w"),
                ("monto", "MONTO", 120, "e"))

    def __init__(self, master, gasto_service, simbolo_fn, al_cambiar_datos):
        super().__init__(master, fg_color="transparent")
        self.gasto_service = gasto_service
        self.simbolo_fn = simbolo_fn
        self.al_cambiar_datos = al_cambiar_datos
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        form = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        form.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 8))
        self.campos = _formulario(form, [
            ("categoria", "CATEGORÍA:", 200, "EJ.: INSUMOS"),
            ("descripcion", "DESCRIPCIÓN:", 300, "EJ.: LAVANDINA"),
            ("monto", "MONTO:", 130, "EJ.: 3500")])
        ctk.CTkButton(form, text="REGISTRAR GASTO", font=F_BASE, width=210,
                      height=44, fg_color=ACENTO_VERDE, text_color="#FFFFFF",
                      command=self._agregar).grid(row=1, column=2, rowspan=2, padx=16)
        ctk.CTkButton(form, text="ELIMINAR SELECCIONADO", font=F_BASE, width=210,
                      height=44, fg_color=ACENTO_ROJO, text_color="#FFFFFF",
                      command=self._eliminar).grid(row=1, column=3, rowspan=2, padx=6)

        _estilo_treeview(self)
        marco = _arbol(self, self.COLUMNAS, None)
        marco.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.tree = marco.tree
        self.refrescar()

    def refrescar(self) -> None:
        self.tree.delete(*self.tree.get_children())
        hoy = date.today().isoformat()
        simbolo = self.simbolo_fn()
        for g in self.gasto_service.repo.listar_entre_fechas(hoy, hoy):
            self.tree.insert("", "end", iid=str(g[0]), values=(
                g[0], g[1].replace("T", " "), g[2], g[3],
                formato_moneda(g[4], simbolo)))

    def _agregar(self) -> None:
        try:
            self.gasto_service.registrar(self.campos["categoria"].get(),
                                         self.campos["descripcion"].get(),
                                         self.campos["monto"].get().replace(",", "."))
        except ErrorValidacion as exc:
            messagebox.showwarning("GASTOS", str(exc).upper(), parent=self)
            return
        for c in self.campos.values():
            c.delete(0, "end")
        self.refrescar(); self.al_cambiar_datos()

    def _eliminar(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        gid = int(sel[0])
        valores = self.tree.item(sel[0], "values")
        if not messagebox.askyesno("GASTOS",
                                   f"¿ELIMINAR EL GASTO «{valores[3]}» "
                                   f"({valores[4]})?", parent=self):
            return
        self.gasto_service.repo.eliminar(gid)
        self.refrescar(); self.al_cambiar_datos()


class ExportarDialog(ctk.CTkToplevel):
    """Exportación institucional: tabla maestra + dashboard + estadísticas
    de clientes + hoja por barbero con liquidación de comisión."""

    def __init__(self, master, servicio_exportacion, hoy: str):
        super().__init__(master)
        self.servicio = servicio_exportacion
        self.title("EXPORTAR A EXCEL INSTITUCIONAL")
        self.configure(fg_color=FONDO_PRINCIPAL)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        cuerpo = ctk.CTkFrame(self, fg_color=FONDO_PANEL, corner_radius=8)
        cuerpo.pack(padx=20, pady=20, fill="both", expand=True)
        ctk.CTkLabel(cuerpo, text="RANGO DE FECHAS A EXPORTAR", font=F_GRANDE,
                     text_color=TEXTO_PRINCIPAL).pack(padx=16, pady=(16, 8))

        fila = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fila.pack(padx=16, pady=8)
        ctk.CTkLabel(fila, text="DESDE:", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=0, padx=6)
        self.desde = ctk.CTkEntry(fila, width=140, font=F_BASE, height=40,
                                  fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                  text_color=TEXTO_PRINCIPAL)
        self.desde.grid(row=0, column=1, padx=6)
        self.desde.insert(0, hoy)
        ctk.CTkLabel(fila, text="HASTA:", font=F_BASE,
                     text_color=TEXTO_SUAVE).grid(row=0, column=2, padx=6)
        self.hasta = ctk.CTkEntry(fila, width=140, font=F_BASE, height=40,
                                  fg_color=CAMPO_FONDO, border_color=CAMPO_BORDE,
                                  text_color=TEXTO_PRINCIPAL)
        self.hasta.grid(row=0, column=3, padx=6)
        self.hasta.insert(0, hoy)

        self.mensaje = ctk.CTkLabel(cuerpo, text="FORMATO AAAA-MM-DD. EL ARCHIVO "
                                    "INCLUYE REGISTRO MAESTRO, DASHBOARD GENERAL, "
                                    "ESTADÍSTICAS DE CLIENTES Y UNA HOJA POR "
                                    "BARBERO CON LA LIQUIDACIÓN DE COMISIÓN "
                                    "(FORMATO LIBRO MENSUAL).",
                                    font=F_BASE, text_color=TEXTO_SUAVE,
                                    wraplength=420, justify="left")
        self.mensaje.pack(padx=16, pady=(0, 8))

        botones = ctk.CTkFrame(cuerpo, fg_color="transparent")
        botones.pack(pady=(4, 16))
        ctk.CTkButton(botones, text="EXPORTAR", font=F_BASE, width=150, height=44,
                      fg_color=ACENTO_VERDE, text_color="#FFFFFF",
                      command=self._exportar).pack(side="left", padx=8)
        ctk.CTkButton(botones, text="CERRAR", font=F_BASE, width=110, height=44,
                      fg_color=BOTON_NEUTRO, hover_color=BOTON_NEUTRO_HOVER,
                      text_color=TEXTO_PRINCIPAL,
                      command=self.destroy).pack(side="left", padx=8)

    def _exportar(self) -> None:
        try:
            ruta = self.servicio.exportar(self.desde.get().strip(),
                                          self.hasta.get().strip())
        except ErrorValidacion as exc:
            self.mensaje.configure(text=str(exc).upper(), text_color=ACENTO_ROJO)
            return
        except OSError:
            self.mensaje.configure(
                text=("NO SE PUDO GUARDAR EL ARCHIVO PORQUE EL SISTEMA BLOQUEÓ "
                      "LA ESCRITURA. CERRÁ EL EXCEL SI EL REPORTE ESTÁ ABIERTO "
                      "Y VOLVÉ A INTENTAR."),
                text_color=ACENTO_ROJO)
            return
        # La ruta NO se pasa a mayúsculas: es un dato del sistema de archivos.
        self.mensaje.configure(text=f"ARCHIVO GUARDADO CORRECTAMENTE EN:\n{ruta}",
                               text_color=VERDE_TEXTO)
