"""Capa de dominio — Viking Software BETA · Etapa 1.8 (versión 0.5.0).

Autor: Facundo David Barreto
Cliente: Peluquería Vikingos (Juliano — propietario)

Objetos puros del negocio de Peluquería Vikingos. Ninguna clase de este
módulo conoce la base de datos ni la pantalla: eso garantiza que las
reglas del dominio se puedan probar de forma aislada.

Novedades Etapa 1.5:
    * Cada venta registra el barbero que la realizó (trazabilidad).
    * Cada venta puede llevar cliente, método de pago y propina.
    * Nuevos objetos: Barbero y Gasto.

Novedades Etapa 1.6 (0.3.0):
    * Barbero lleva ``comision``: porcentaje (0–100) que le corresponde
      sobre lo facturado. Las propinas NO se descuentan: son 100 % suyas.
    * El método de pago deja de ser un enum cerrado: es TEXTO administrable
      desde la pestaña Administración (tabla ``metodos_pago``).

Novedades Etapa 1.7 (0.4.0):
    * Nuevo objeto ``Cliente`` (nombre, apellido, celular, mail opcional):
      la venta puede vincularse a un cliente registrado (``cliente_id``).
      El celular es la CLAVE ÚNICA que identifica a cada cliente en las
      estadísticas del reporte.
    * Nueva constante ``MONEDAS``: símbolos de moneda admitidos para la
      lectura de importes en TODA la aplicación y los reportes. No es un
      tema de cotización: solo cambia el símbolo con que se muestran los
      números (ej.: G$ para guaraníes).

Novedades Etapa 1.8 (0.5.0):
    * ``Cliente`` gana ``fecha_nacimiento`` (opcional, "DD/MM/AAAA"):
      base del CRM de la Etapa 2 (saludos y promociones de cumpleaños).
    * Nuevo objeto ``Adelanto``: dinero que el dueño le adelanta a un
      barbero a cuenta de su liquidación. Es un EGRESO de caja y se
      descuenta del NETO A COBRAR del barbero en el reporte.

VERIFICACIÓN DE CORRECCIÓN — VENTA
    Pre-condición:  precio_unitario > 0, cantidad > 0, descripcion no vacía,
                    barbero_id válido y metodo_pago no vacío (validadas por
                    RegistroVentaService antes de construir el objeto).
    Post-condición: subtotal == precio_unitario × cantidad (2 decimales);
                    total == subtotal + propina.
    Invariante:     el objeto es inmutable (frozen): una venta registrada jamás
                    cambia desde la caja; las correcciones de errores se hacen
                    desde Administración y quedan registradas en el log.
"""

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

# Método de pago que asume una venta si nadie indica otro. La lista
# completa y vigente la administra la tabla metodos_pago (base_datos).
METODO_PAGO_DEFECTO = "EFECTIVO"

# Monedas admitidas para la LECTURA de importes (símbolo solamente).
# Se elige una vez en Administración → MÉTODOS Y MONEDA y se guarda en la
# tabla config (clave "moneda_simbolo"). No convierte ni cotiza valores.
MONEDA_DEFECTO = "$"
MONEDAS = ("$", "G$", "USD", "R$", "€")


class TipoItem(Enum):
    """Las dos únicas familias de ítems que vende la peluquería."""

    SERVICIO = "SERVICIO"
    PRODUCTO = "PRODUCTO"


@dataclass(frozen=True)
class ItemCatalogo:
    """Ítem vendible del catálogo (servicio o producto)."""

    nombre: str
    tipo: TipoItem
    precio_unitario: float
    activo: bool = True


@dataclass(frozen=True)
class Barbero:
    """Integrante del equipo. La baja es lógica (activo=False): las ventas
    históricas conservan su autor aunque el barbero se retire.

    ``comision`` es el porcentaje (0–100) que le corresponde sobre el total
    FACTURADO (subtotales, sin propinas). Las propinas son siempre 100 %
    del barbero: se suman aparte en la liquidación.
    """

    id: int
    nombre: str
    activo: bool = True
    comision: float = 50.0          # porcentaje 0–100 (defecto histórico: 50)


@dataclass(frozen=True)
class Cliente:
    """Cliente registrado de la peluquería (Etapa 1.7).

    ``celular`` es la clave única: identifica al cliente en la base y en la
    hoja CLIENTES del reporte exportado. ``mail`` es opcional.
    ``fecha_nacimiento`` (Etapa 1.8) es opcional, en formato "DD/MM/AAAA":
    es la base del CRM de cumpleaños de la Etapa 2.
    """

    id: int
    nombre: str
    apellido: str
    celular: str
    mail: str = ""
    fecha_nacimiento: str = ""

    @property
    def nombre_completo(self) -> str:
        """Texto que se desnormaliza en la venta: 'Juan Pérez'."""
        return f"{self.nombre} {self.apellido}".strip()


@dataclass(frozen=True)
class Adelanto:
    """Adelanto de sueldo que el dueño le da a un barbero (Etapa 1.8).

    Es un EGRESO de caja (figura en la hoja BALANCE del reporte) y se
    descuenta del NETO A COBRAR del barbero en su hoja de liquidación.
    ``fecha_hora`` la asigna SIEMPRE el servicio (reloj del sistema).
    ``uuid`` es la llave que la Etapa 2 usará para sincronizar sin
    duplicar filas.
    """

    barbero_id: int
    monto: float
    nota: str = ""                  # opcional: motivo del adelanto
    uuid: str = field(default_factory=lambda: str(uuid4()))
    fecha_hora: str = ""            # la asigna el servicio, nunca el usuario


@dataclass(frozen=True)
class Venta:
    """Venta registrada en el mostrador.

    ``uuid`` la identifica de forma única e irrepetible: es la llave que la
    Etapa 2 usará para sincronizar con el ERP central sin duplicar filas.
    ``fecha_hora`` la asigna SIEMPRE el servicio (reloj del sistema), jamás
    el usuario.
    ``metodo_pago`` es texto libre administrado (EFECTIVO, TRANSFERENCIA…);
    se guarda con la escritura canónica registrada en metodos_pago.
    ``cliente_id`` vincula con la tabla clientes (None = mostrador);
    ``cliente`` conserva el nombre como texto para que el historial
    sobreviva aunque el cliente se elimine.
    """

    tipo: TipoItem
    descripcion: str
    precio_unitario: float
    cantidad: int
    barbero_id: int
    metodo_pago: str = METODO_PAGO_DEFECTO
    cliente: str = ""                 # texto desnormalizado ("Juan Pérez")
    cliente_id: int | None = None     # vínculo con clientes (None = mostrador)
    propina: float = 0.0              # opcional: >= 0
    uuid: str = field(default_factory=lambda: str(uuid4()))
    fecha_hora: str = ""              # la asigna el servicio, nunca el usuario

    @property
    def subtotal(self) -> float:
        """Post-condición: precio × cantidad redondeado a 2 decimales."""
        return round(self.precio_unitario * self.cantidad, 2)

    @property
    def total(self) -> float:
        """Lo que efectivamente pagó el cliente: subtotal + propina."""
        return round(self.subtotal + self.propina, 2)


@dataclass(frozen=True)
class Gasto:
    """Salida de dinero de la caja (insumos, adelantos, servicios, etc.)."""

    categoria: str
    descripcion: str
    monto: float
    uuid: str = field(default_factory=lambda: str(uuid4()))
    fecha_hora: str = ""              # la asigna el servicio
