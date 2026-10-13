"""Capa de datos — Viking Software BETA · Etapa 1.8 (versión 0.5.0).

Autor: Facundo David Barreto
Cliente: Peluquería Vikingos (Juliano — propietario)

Único lugar del sistema donde existe SQL. Motor: SQLite 3 embebido
(un solo archivo ``datos/viking.db`` que se respalda copiándolo).

Reglas de esta capa:
    * Toda escritura ocurre dentro de una transacción ACID: el bloque
      ``with con:`` confirma (COMMIT) si todo salió bien o revierte
      (ROLLBACK) ante cualquier error. Si se corta la luz a mitad de una
      operación, queda completa o no queda — nunca a medias.
    * Toda conexión se CIERRA explícitamente (``contextlib.closing``):
      en Windows una conexión abierta bloquea el archivo .db.

Esquema v2 (Etapa 1.5) — migración automática e idempotente:
    Al arrancar, ``inicializar()`` crea las tablas nuevas (barberos, gastos,
    config) y agrega a ``ventas`` las columnas nuevas (barbero_id, cliente,
    metodo_pago, propina) si la base venía de la Etapa 1. Las ventas viejas
    se conservan intactas con barbero "—" (sin asignar).

Esquema v3 (Etapa 1.6) — migración automática e idempotente:
    * ``barberos`` gana la columna ``comision`` (REAL 0–100, defecto 50).
    * Nueva tabla ``metodos_pago``: los medios de cobro dejan de estar
      fijos en el código y se administran desde la pestaña Administración.

Esquema v4 (Etapa 1.7) — migración automática e idempotente:
    * Nueva tabla ``clientes`` (nombre, apellido, celular ÚNICO, mail
      opcional). El celular es la clave que identifica a cada cliente en
      las estadísticas del reporte.
    * ``ventas`` gana la columna ``cliente_id`` (REFERENCES clientes).
      Las ventas viejas quedan con cliente_id NULL y su texto libre en
      ``cliente``: el historial no se pierde.

Esquema v5 (Etapa 1.8) — migración automática e idempotente:
    * ``clientes`` gana la columna ``fecha_nacimiento`` (TEXT, opcional,
      formato "DD/MM/AAAA"): base del CRM de cumpleaños de la Etapa 2.
      Los clientes ya cargados quedan con la fecha vacía.
    * Nueva tabla ``adelantos``: dinero que el dueño (Juliano) le
      adelanta a un barbero a cuenta de su liquidación. Es un egreso de
      caja (hoja BALANCE del reporte) y se descuenta del NETO A COBRAR
      del barbero en su hoja individual.
"""

import sqlite3
from contextlib import closing
from hashlib import sha256
from pathlib import Path

from .modelos import (Adelanto, Barbero, Cliente, Gasto, ItemCatalogo,
                      TipoItem, Venta)

VERSION_ESQUEMA = 5

# Esquema base (tablas que no cambian desde la Etapa 1).
ESQUEMA_BASE_SQL = """
CREATE TABLE IF NOT EXISTS items_catalogo (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    tipo            TEXT NOT NULL CHECK (tipo IN ('SERVICIO','PRODUCTO')),
    precio_unitario REAL NOT NULL CHECK (precio_unitario > 0),
    activo          INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid            TEXT NOT NULL UNIQUE,
    fecha_hora      TEXT NOT NULL,
    tipo            TEXT NOT NULL CHECK (tipo IN ('SERVICIO','PRODUCTO')),
    descripcion     TEXT NOT NULL,
    precio_unitario REAL NOT NULL CHECK (precio_unitario > 0),
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    subtotal        REAL NOT NULL CHECK (subtotal = ROUND(precio_unitario * cantidad, 2)),
    sincronizado    INTEGER NOT NULL DEFAULT 0,
    creado_en       TEXT NOT NULL DEFAULT (datetime('now')),
    actualizado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_ventas_sync  ON ventas(sincronizado);
"""

# Tablas nuevas de la Etapa 1.5.
ESQUEMA_V2_SQL = """
CREATE TABLE IF NOT EXISTS barberos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL UNIQUE,
    activo     INTEGER NOT NULL DEFAULT 1,
    creado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gastos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid         TEXT NOT NULL UNIQUE,
    fecha_hora   TEXT NOT NULL,
    categoria    TEXT NOT NULL,
    descripcion  TEXT NOT NULL,
    monto        REAL NOT NULL CHECK (monto > 0),
    sincronizado INTEGER NOT NULL DEFAULT 0,
    creado_en    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_gastos_fecha ON gastos(fecha_hora);

CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
"""

# Tabla nueva de la Etapa 1.6: métodos de pago administrables.
# COLLATE NOCASE en el UNIQUE evita duplicados tipo "QR" vs "qr".
ESQUEMA_V3_SQL = """
CREATE TABLE IF NOT EXISTS metodos_pago (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL COLLATE NOCASE UNIQUE,
    creado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# Tabla nueva de la Etapa 1.7: clientes. El CELULAR es la clave única
# (identifica al cliente en las estadísticas del reporte). El mail es
# opcional. COLLATE NOCASE en el UNIQUE por si lo escriben distinto.
ESQUEMA_V4_SQL = """
CREATE TABLE IF NOT EXISTS clientes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre     TEXT NOT NULL,
    apellido   TEXT NOT NULL,
    celular    TEXT NOT NULL COLLATE NOCASE UNIQUE,
    mail       TEXT NOT NULL DEFAULT '',
    creado_en  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# El índice sobre ventas.cliente_id se crea DESPUÉS del ALTER que agrega
# la columna (en inicializar), no en el script de la tabla.
INDICE_CLIENTE_V4_SQL = \
    "CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id)"

# Tabla nueva de la Etapa 1.8: adelantos del dueño a los barberos.
# Mismo patrón que gastos (uuid para la sincronización de la Etapa 2),
# pero vinculado a un barbero: se descuenta de su liquidación.
ESQUEMA_V5_SQL = """
CREATE TABLE IF NOT EXISTS adelantos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    uuid         TEXT NOT NULL UNIQUE,
    fecha_hora   TEXT NOT NULL,
    barbero_id   INTEGER NOT NULL REFERENCES barberos(id),
    monto        REAL NOT NULL CHECK (monto > 0),
    nota         TEXT NOT NULL DEFAULT '',
    sincronizado INTEGER NOT NULL DEFAULT 0,
    creado_en    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_adelantos_fecha   ON adelantos(fecha_hora);
CREATE INDEX IF NOT EXISTS idx_adelantos_barbero ON adelantos(barbero_id);
"""

# Columna que la Etapa 1.8 agrega a clientes (ALTER TABLE idempotente).
# Opcional (puede quedar vacía): fecha de nacimiento "DD/MM/AAAA".
COLUMNA_NACIMIENTO_V5 = ("fecha_nacimiento", "TEXT NOT NULL DEFAULT ''")

# Columnas que la Etapa 1.5 agrega a ventas (ALTER TABLE idempotente).
COLUMNAS_VENTAS_V2 = (
    ("barbero_id", "INTEGER REFERENCES barberos(id)"),
    ("cliente", "TEXT"),
    ("metodo_pago", "TEXT"),
    ("propina", "REAL NOT NULL DEFAULT 0 CHECK (propina >= 0)"),
)

# Columna que la Etapa 1.6 agrega a barberos (ALTER TABLE idempotente).
COLUMNA_COMISION_V3 = (
    "comision",
    "REAL NOT NULL DEFAULT 50.0 CHECK (comision >= 0 AND comision <= 100)",
)

# Columna que la Etapa 1.7 agrega a ventas (ALTER TABLE idempotente).
COLUMNA_CLIENTE_V4 = ("cliente_id", "INTEGER REFERENCES clientes(id)")

SEMILLA_CATALOGO = [
    ("Corte Caballero", "SERVICIO", 8000.00),
    ("Perfilado de Barba", "SERVICIO", 5000.00),
    ("Corte + Barba", "SERVICIO", 11000.00),
    ("Coloración", "SERVICIO", 15000.00),
    ("Pomada", "PRODUCTO", 6500.00),
    ("Champú", "PRODUCTO", 5500.00),
    ("Aceite para Barba", "PRODUCTO", 7000.00),
]

# Semilla de barberos: SOLO el dueño (Juliano). Los empleados (como
# Alexander) se cargan desde Administración → BARBEROS. En bases ya
# existentes la semilla no se vuelve a aplicar: el equipo cargado se
# conserva tal cual.
SEMILLA_BARBEROS = ["Juliano"]

# Métodos de pago de fábrica. Se conserva la escritura original
# ("QR / Mercado Pago") para que las ventas históricas sigan agrupándose
# con las nuevas en los reportes.
SEMILLA_METODOS = ["EFECTIVO", "TRANSFERENCIA", "TARJETA", "QR / Mercado Pago"]

# SELECT canónico de ventas con el nombre del barbero resuelto.
# CONTRATO: devuelve 12 columnas en este orden — la interfaz y el
# exportador dependen de él; agregar columnas solo AL FINAL.
SELECT_VENTAS = """
SELECT v.id, v.fecha_hora, COALESCE(b.nombre, '—') AS barbero,
       v.tipo, v.descripcion, COALESCE(v.cliente, '') AS cliente,
       COALESCE(v.metodo_pago, 'EFECTIVO') AS metodo_pago,
       v.precio_unitario, v.cantidad, v.subtotal, COALESCE(v.propina, 0) AS propina,
       ROUND(v.subtotal + COALESCE(v.propina, 0), 2) AS total
FROM ventas v LEFT JOIN barberos b ON b.id = v.barbero_id
"""


class ConexionDB:
    """Única puerta de entrada a viking.db. Activa claves foráneas y WAL."""

    def __init__(self, ruta: Path):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def abrir(self) -> sqlite3.Connection:
        """Devuelve una conexión NUEVA. Quien la abre, la cierra:
        usar siempre dentro de ``contextlib.closing`` (ver repositorios)."""
        con = sqlite3.connect(self.ruta)
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("PRAGMA journal_mode = WAL")
        return con

    def inicializar(self) -> None:
        """Crea/migra el esquema. Idempotente: segura de correr en cada
        arranque sobre una base nueva (Etapa 1.8 pura) o heredada
        (v1/v2/v3/v4)."""
        with closing(self.abrir()) as con:
            with con:
                con.executescript(ESQUEMA_BASE_SQL)
                con.executescript(ESQUEMA_V2_SQL)
                con.executescript(ESQUEMA_V3_SQL)
                con.executescript(ESQUEMA_V4_SQL)
                con.executescript(ESQUEMA_V5_SQL)
                existentes = {f[1] for f in con.execute("PRAGMA table_info(ventas)")}
                for nombre, definicion in COLUMNAS_VENTAS_V2:
                    if nombre not in existentes:
                        con.execute(f"ALTER TABLE ventas ADD COLUMN {nombre} {definicion}")
                nombre_col, definicion_col = COLUMNA_CLIENTE_V4
                if nombre_col not in existentes:
                    con.execute(
                        f"ALTER TABLE ventas ADD COLUMN {nombre_col} {definicion_col}")
                con.execute(INDICE_CLIENTE_V4_SQL)
                cols_barberos = {f[1] for f in con.execute("PRAGMA table_info(barberos)")}
                nombre_col, definicion_col = COLUMNA_COMISION_V3
                if nombre_col not in cols_barberos:
                    con.execute(
                        f"ALTER TABLE barberos ADD COLUMN {nombre_col} {definicion_col}")
                cols_clientes = {f[1] for f in con.execute("PRAGMA table_info(clientes)")}
                nombre_col, definicion_col = COLUMNA_NACIMIENTO_V5
                if nombre_col not in cols_clientes:
                    con.execute(
                        f"ALTER TABLE clientes ADD COLUMN {nombre_col} {definicion_col}")
                con.execute(f"PRAGMA user_version = {VERSION_ESQUEMA}")


class ConfigRepository:
    """Configuración interna (clave de administración, moneda, tema)."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()

    def obtener(self, clave: str, defecto: str = "") -> str:
        with closing(self.db.abrir()) as con:
            fila = con.execute("SELECT valor FROM config WHERE clave = ?", (clave,)).fetchone()
        return fila[0] if fila else defecto

    def establecer(self, clave: str, valor: str) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("INSERT INTO config (clave, valor) VALUES (?, ?) "
                            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
                            (clave, valor))

    def verificar_clave_admin(self, clave_plana: str) -> bool:
        esperado = self.obtener("clave_admin", sha256(b"vikingos").hexdigest())
        return sha256(clave_plana.encode("utf-8")).hexdigest() == esperado

    def cambiar_clave_admin(self, clave_nueva: str) -> None:
        self.establecer("clave_admin", sha256(clave_nueva.encode("utf-8")).hexdigest())


class BarberoRepository:
    """Gestión del equipo. Baja lógica: un barbero con ventas históricas
    se desactiva, nunca se borra. La comisión (0–100) viaja en la fila."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()
        self._cargar_semilla()

    def _cargar_semilla(self) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                vacio = con.execute("SELECT COUNT(*) FROM barberos").fetchone()[0] == 0
                if vacio:
                    con.executemany("INSERT INTO barberos (nombre) VALUES (?)",
                                    [(n,) for n in SEMILLA_BARBEROS])

    def _a_barbero(self, fila) -> Barbero:
        return Barbero(id=fila[0], nombre=fila[1], activo=bool(fila[2]),
                       comision=float(fila[3]) if fila[3] is not None else 50.0)

    def listar(self, solo_activos: bool = True) -> list[Barbero]:
        sql = "SELECT id, nombre, activo, comision FROM barberos"
        if solo_activos:
            sql += " WHERE activo = 1"
        sql += " ORDER BY nombre"
        with closing(self.db.abrir()) as con:
            return [self._a_barbero(f) for f in con.execute(sql).fetchall()]

    def obtener(self, barbero_id: int) -> Barbero | None:
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT id, nombre, activo, comision FROM barberos WHERE id = ?",
                (barbero_id,)).fetchone()
        return self._a_barbero(fila) if fila else None

    def buscar_por_nombre(self, nombre: str) -> Barbero | None:
        """Coincidencia exacta sin distinguir mayúsculas (para reportes)."""
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT id, nombre, activo, comision FROM barberos "
                "WHERE nombre = ? COLLATE NOCASE", (nombre,)).fetchone()
        return self._a_barbero(fila) if fila else None

    def agregar(self, nombre: str, comision: float = 50.0) -> int:
        with closing(self.db.abrir()) as con:
            with con:
                cur = con.execute(
                    "INSERT INTO barberos (nombre, comision) VALUES (?, ?)",
                    (nombre.strip(), round(float(comision), 2)))
                return cur.lastrowid

    def renombrar(self, barbero_id: int, nombre: str) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("UPDATE barberos SET nombre = ? WHERE id = ?",
                            (nombre.strip(), barbero_id))

    def set_activo(self, barbero_id: int, activo: bool) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("UPDATE barberos SET activo = ? WHERE id = ?",
                            (1 if activo else 0, barbero_id))

    def set_comision(self, barbero_id: int, comision: float) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("UPDATE barberos SET comision = ? WHERE id = ?",
                            (round(float(comision), 2), barbero_id))

    def tiene_ventas(self, barbero_id: int) -> bool:
        with closing(self.db.abrir()) as con:
            return con.execute("SELECT COUNT(*) FROM ventas WHERE barbero_id = ?",
                               (barbero_id,)).fetchone()[0] > 0

    def eliminar(self, barbero_id: int) -> None:
        """Borrado físico: solo si jamás registró una venta."""
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM barberos WHERE id = ?", (barbero_id,))


class MetodoPagoRepository:
    """Medios de cobro administrables (Etapa 1.6). Sin baja lógica: las
    ventas históricas guardan el nombre como texto, así que eliminar un
    método no rompe ningún registro anterior."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()
        self._cargar_semilla()

    def _cargar_semilla(self) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                vacio = con.execute("SELECT COUNT(*) FROM metodos_pago").fetchone()[0] == 0
                if vacio:
                    con.executemany("INSERT INTO metodos_pago (nombre) VALUES (?)",
                                    [(n,) for n in SEMILLA_METODOS])

    def listar(self) -> list[tuple]:
        """(id, nombre) en orden de alta — el orden en que los ve la caja."""
        with closing(self.db.abrir()) as con:
            return con.execute("SELECT id, nombre FROM metodos_pago ORDER BY id").fetchall()

    def listar_nombres(self) -> list[str]:
        return [nombre for _id, nombre in self.listar()]

    def contar(self) -> int:
        with closing(self.db.abrir()) as con:
            return con.execute("SELECT COUNT(*) FROM metodos_pago").fetchone()[0]

    def obtener(self, metodo_id: int) -> tuple | None:
        """(id, nombre) o None."""
        with closing(self.db.abrir()) as con:
            return con.execute("SELECT id, nombre FROM metodos_pago WHERE id = ?",
                               (metodo_id,)).fetchone()

    def buscar_por_nombre(self, nombre: str) -> str | None:
        """Devuelve la escritura CANÓNICA registrada (o None si no existe).
        Coincidencia sin distinguir mayúsculas: 'qr / mercado pago' encuentra
        'QR / Mercado Pago'."""
        nombre = (nombre or "").strip()
        if not nombre:
            return None
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT nombre FROM metodos_pago WHERE nombre = ? COLLATE NOCASE",
                (nombre,)).fetchone()
        return fila[0] if fila else None

    def agregar(self, nombre: str) -> int:
        with closing(self.db.abrir()) as con:
            with con:
                cur = con.execute("INSERT INTO metodos_pago (nombre) VALUES (?)",
                                  (nombre.strip(),))
                return cur.lastrowid

    def eliminar(self, metodo_id: int) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM metodos_pago WHERE id = ?", (metodo_id,))


class ClienteRepository:
    """Base de clientes (Etapa 1.7). El CELULAR es la clave única:
    identifica al cliente en las estadísticas del reporte. Eliminar un
    cliente NO toca el historial: las ventas conservan su nombre como
    texto y su cliente_id pasa a NULL."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()

    # CONTRATO de columnas: toda lectura de clientes devuelve estas 6
    # columnas en este orden (agregar columnas solo AL FINAL).
    _COLUMNAS = "id, nombre, apellido, celular, mail, fecha_nacimiento"

    def _a_cliente(self, fila) -> Cliente:
        return Cliente(id=fila[0], nombre=fila[1], apellido=fila[2],
                       celular=fila[3], mail=fila[4] or "",
                       fecha_nacimiento=(fila[5] or "") if len(fila) > 5 else "")

    def listar(self) -> list[Cliente]:
        """Todos los clientes, ordenados por apellido y nombre."""
        with closing(self.db.abrir()) as con:
            return [self._a_cliente(f) for f in con.execute(
                f"SELECT {self._COLUMNAS} FROM clientes "
                "ORDER BY apellido, nombre").fetchall()]

    def obtener(self, cliente_id: int) -> Cliente | None:
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                f"SELECT {self._COLUMNAS} FROM clientes "
                "WHERE id = ?", (cliente_id,)).fetchone()
        return self._a_cliente(fila) if fila else None

    def buscar_por_celular(self, celular: str) -> Cliente | None:
        """Coincidencia sin distinguir mayúsculas/minúsculas."""
        celular = (celular or "").strip()
        if not celular:
            return None
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                f"SELECT {self._COLUMNAS} FROM clientes "
                "WHERE celular = ? COLLATE NOCASE", (celular,)).fetchone()
        return self._a_cliente(fila) if fila else None

    def buscar(self, texto: str, limite: int = 8) -> list[Cliente]:
        """Búsqueda PARCIAL para el autocompletado de la caja: coincide con
        nombre, apellido, celular, mail o las combinaciones
        'nombre apellido' / 'apellido nombre' (sin distinguir mayúsculas
        en ASCII). Ej.: tipeando 'rich' aparecen todos los Richard.
        Los comodines LIKE (% y _) del texto tipeado se escapan."""
        texto = (texto or "").strip()
        if not texto:
            return self.listar()[:max(int(limite), 1)]
        patron = ("%" + texto.replace("\\", "\\\\").replace("%", "\\%")
                             .replace("_", "\\_") + "%")
        sql = f"""
        SELECT {self._COLUMNAS} FROM clientes
        WHERE nombre LIKE ? ESCAPE '\\' OR apellido LIKE ? ESCAPE '\\'
           OR celular LIKE ? ESCAPE '\\' OR mail LIKE ? ESCAPE '\\'
           OR (nombre || ' ' || apellido) LIKE ? ESCAPE '\\'
           OR (apellido || ' ' || nombre) LIKE ? ESCAPE '\\'
        ORDER BY apellido, nombre LIMIT ?
        """
        with closing(self.db.abrir()) as con:
            return [self._a_cliente(f) for f in con.execute(
                sql, (patron,) * 6 + (max(int(limite), 1),)).fetchall()]

    def buscar_por_nombre_y_mail(self, nombre: str, mail: str,
                                 excluir_id: int | None = None) -> Cliente | None:
        """Coincidencia EXACTA de nombre + mail (sin distinguir mayúsculas):
        la usa el detector de errores de tipeo del alta/edición — si coincide
        nombre + mail pero el celular es otro, probablemente se tipeó mal.
        ``excluir_id`` ignora una ficha (la que se está editando)."""
        nombre = (nombre or "").strip()
        mail = (mail or "").strip()
        if not nombre or not mail:
            return None
        sql = (f"SELECT {self._COLUMNAS} FROM clientes "
               "WHERE nombre = ? COLLATE NOCASE AND mail = ? COLLATE NOCASE")
        params: tuple = (nombre, mail)
        if excluir_id is not None:
            sql += " AND id <> ?"
            params = (nombre, mail, int(excluir_id))
        with closing(self.db.abrir()) as con:
            fila = con.execute(sql, params).fetchone()
        return self._a_cliente(fila) if fila else None

    def agregar(self, nombre: str, apellido: str, celular: str,
                mail: str = "", fecha_nacimiento: str = "") -> int:
        with closing(self.db.abrir()) as con:
            with con:
                cur = con.execute(
                    "INSERT INTO clientes (nombre, apellido, celular, mail, "
                    "fecha_nacimiento) VALUES (?, ?, ?, ?, ?)",
                    (nombre.strip(), apellido.strip(), celular.strip(),
                     (mail or "").strip(), (fecha_nacimiento or "").strip()))
                return cur.lastrowid

    def actualizar(self, cliente_id: int, nombre: str, apellido: str,
                   celular: str, mail: str = "",
                   fecha_nacimiento: str = "") -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute(
                    "UPDATE clientes SET nombre = ?, apellido = ?, celular = ?, "
                    "mail = ?, fecha_nacimiento = ? WHERE id = ?",
                    (nombre.strip(), apellido.strip(), celular.strip(),
                     (mail or "").strip(), (fecha_nacimiento or "").strip(),
                     cliente_id))

    def eliminar(self, cliente_id: int) -> None:
        """Baja física. Antes desvincula las ventas (cliente_id → NULL):
        el texto del nombre queda guardado en cada venta, así el historial
        y los reportes anteriores no cambian."""
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("UPDATE ventas SET cliente_id = NULL WHERE cliente_id = ?",
                            (cliente_id,))
                con.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))


class CatalogoRepository:
    """Gestiona el catálogo de servicios y productos (ABM completo)."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()
        self._cargar_semilla()

    def _cargar_semilla(self) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                vacio = con.execute("SELECT COUNT(*) FROM items_catalogo").fetchone()[0] == 0
                if vacio:
                    con.executemany(
                        "INSERT INTO items_catalogo (nombre, tipo, precio_unitario) VALUES (?, ?, ?)",
                        SEMILLA_CATALOGO,
                    )

    def listar_activos(self, tipo: TipoItem | None = None) -> list[ItemCatalogo]:
        sql = "SELECT nombre, tipo, precio_unitario, activo FROM items_catalogo WHERE activo = 1"
        params: tuple = ()
        if tipo is not None:
            sql += " AND tipo = ?"
            params = (tipo.value,)
        sql += " ORDER BY nombre"
        with closing(self.db.abrir()) as con:
            filas = con.execute(sql, params).fetchall()
        return [ItemCatalogo(nombre=f[0], tipo=TipoItem(f[1]),
                             precio_unitario=f[2], activo=bool(f[3])) for f in filas]

    def listar_todos(self) -> list[tuple]:
        """(id, nombre, tipo, precio_unitario, activo) para el panel admin."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT id, nombre, tipo, precio_unitario, activo "
                "FROM items_catalogo ORDER BY tipo, nombre").fetchall()

    def buscar_por_nombre(self, nombre: str) -> ItemCatalogo | None:
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT nombre, tipo, precio_unitario, activo FROM items_catalogo WHERE nombre = ?",
                (nombre,)).fetchone()
        if fila is None:
            return None
        return ItemCatalogo(nombre=fila[0], tipo=TipoItem(fila[1]),
                            precio_unitario=fila[2], activo=bool(fila[3]))

    def obtener(self, item_id: int) -> tuple | None:
        """(id, nombre, tipo, precio_unitario, activo) o None."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT id, nombre, tipo, precio_unitario, activo "
                "FROM items_catalogo WHERE id = ?", (item_id,)).fetchone()

    def agregar(self, nombre: str, tipo: TipoItem, precio: float) -> int:
        with closing(self.db.abrir()) as con:
            with con:
                cur = con.execute(
                    "INSERT INTO items_catalogo (nombre, tipo, precio_unitario) VALUES (?, ?, ?)",
                    (nombre.strip(), tipo.value, round(float(precio), 2)))
                return cur.lastrowid

    def actualizar(self, item_id: int, nombre: str, tipo: TipoItem, precio: float) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute(
                    "UPDATE items_catalogo SET nombre = ?, tipo = ?, precio_unitario = ? WHERE id = ?",
                    (nombre.strip(), tipo.value, round(float(precio), 2), item_id))

    def set_activo(self, item_id: int, activo: bool) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("UPDATE items_catalogo SET activo = ? WHERE id = ?",
                            (1 if activo else 0, item_id))

    def eliminar(self, item_id: int) -> None:
        """Borrado físico del catálogo. Las ventas históricas no se tocan:
        guardan la descripción como texto propio."""
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM items_catalogo WHERE id = ?", (item_id,))


class VentaRepository:
    """Persiste y consulta ventas. Toda escritura es transacción ACID.

    VERIFICACIÓN DE CORRECCIÓN — guardar
        Pre-condición:  venta válida (pasó RegistroVentaService); db accesible.
        Post-condición: la fila existe en disco y total_del_dia aumentó
                        exactamente en venta.total; conexión cerrada.
        Caso límite:    uuid duplicado → sqlite3.IntegrityError → se propaga;
                        nunca se escribe una fila a medias.
    """

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()

    def guardar(self, venta: Venta) -> None:
        sql = """INSERT INTO ventas (uuid, fecha_hora, tipo, descripcion,
                                     precio_unitario, cantidad, subtotal,
                                     barbero_id, cliente, cliente_id,
                                     metodo_pago, propina)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        with closing(self.db.abrir()) as con:
            with con:  # COMMIT o ROLLBACK automático
                con.execute(sql, (venta.uuid, venta.fecha_hora, venta.tipo.value,
                                  venta.descripcion, venta.precio_unitario,
                                  venta.cantidad, venta.subtotal, venta.barbero_id,
                                  venta.cliente or None, venta.cliente_id,
                                  venta.metodo_pago or None, venta.propina))

    def ventas_del_dia(self, fecha: str) -> list[tuple]:
        """Filas del día con barbero, cliente, método de pago y propina."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                SELECT_VENTAS + " WHERE date(v.fecha_hora) = ? ORDER BY v.fecha_hora",
                (fecha,)).fetchall()

    def ventas_entre_fechas(self, fecha_desde: str, fecha_hasta: str) -> list[tuple]:
        """Filas del rango inclusive, para la exportación .xlsx (canal BAT-03)."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                SELECT_VENTAS + " WHERE date(v.fecha_hora) BETWEEN ? AND ? "
                                "ORDER BY v.fecha_hora",
                (fecha_desde, fecha_hasta)).fetchall()

    def total_del_dia(self, fecha: str) -> float:
        """SUMA de (subtotal + propina) del día, recalculada SIEMPRE desde
        disco: el tarjetero nunca acumula en memoria."""
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT COALESCE(SUM(subtotal + COALESCE(propina, 0)), 0) "
                "FROM ventas WHERE date(fecha_hora) = ?", (fecha,)).fetchone()
        return float(fila[0])

    def obtener(self, venta_id: int) -> tuple | None:
        with closing(self.db.abrir()) as con:
            return con.execute(SELECT_VENTAS + " WHERE v.id = ?", (venta_id,)).fetchone()

    def actualizar(self, venta_id: int, *, barbero_id: int, tipo: TipoItem,
                   descripcion: str, precio_unitario: float, cantidad: int,
                   cliente: str, metodo_pago: str, propina: float,
                   cliente_id: int | None = None) -> None:
        """Corrección administrativa de un movimiento (con barbero nuevo,
        importes nuevos, cliente nuevo, etc.). El subtotal se recalcula;
        uuid y fecha se conservan para no romper la trazabilidad."""
        subtotal = round(float(precio_unitario) * int(cantidad), 2)
        with closing(self.db.abrir()) as con:
            with con:
                con.execute(
                    """UPDATE ventas SET barbero_id = ?, tipo = ?, descripcion = ?,
                           precio_unitario = ?, cantidad = ?, subtotal = ?,
                           cliente = ?, cliente_id = ?, metodo_pago = ?, propina = ?,
                           actualizado_en = datetime('now')
                       WHERE id = ?""",
                    (barbero_id, tipo.value, descripcion.strip(),
                     round(float(precio_unitario), 2), int(cantidad), subtotal,
                     cliente or None, cliente_id, metodo_pago,
                     round(float(propina), 2), venta_id))

    def eliminar(self, venta_id: int) -> None:
        """Baja física de un movimiento cargado por error (solo desde Admin)."""
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM ventas WHERE id = ?", (venta_id,))

    def estadisticas_clientes(self, fecha_desde: str,
                              fecha_hasta: str) -> list[tuple]:
        """Estadísticas por cliente dentro del rango (hoja CLIENTES).

        Agrupa por cliente registrado (cliente_id) y, aparte, por el texto
        libre de las ventas sin vínculo (mostrador o clientes históricos).
        Devuelve tuplas:
            (grupo, nombre, apellido, celular, mail, texto_original,
             operaciones, gastado, propinas, ultima_visita, fecha_nacimiento)
        ``grupo`` es el id del cliente (int) o "T:<TEXTO>" para las ventas
        sin vínculo; en ese caso nombre/apellido/celular/mail/nacimiento van
        vacíos y el nombre a mostrar es ``texto_original`` ("" = mostrador
        puro). Orden: de mayor a menor gastado.
        """
        sql = """
        SELECT COALESCE(v.cliente_id,
                        'T:' || UPPER(TRIM(COALESCE(v.cliente, '')))) AS grupo,
               COALESCE(c.nombre, ''), COALESCE(c.apellido, ''),
               COALESCE(c.celular, ''), COALESCE(c.mail, ''),
               COALESCE(MAX(v.cliente), '') AS texto_original,
               COUNT(*) AS operaciones,
               ROUND(SUM(v.subtotal), 2) AS gastado,
               ROUND(SUM(COALESCE(v.propina, 0)), 2) AS propinas,
               MAX(v.fecha_hora) AS ultima,
               COALESCE(c.fecha_nacimiento, '') AS nacimiento
        FROM ventas v LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE date(v.fecha_hora) BETWEEN ? AND ?
        GROUP BY grupo
        ORDER BY gastado DESC, ultima DESC
        """
        with closing(self.db.abrir()) as con:
            return con.execute(sql, (fecha_desde, fecha_hasta)).fetchall()


class GastoRepository:
    """Salidas de caja. Mismo patrón que VentaRepository."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()

    def guardar(self, gasto: Gasto) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute(
                    "INSERT INTO gastos (uuid, fecha_hora, categoria, descripcion, monto) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (gasto.uuid, gasto.fecha_hora, gasto.categoria,
                     gasto.descripcion, gasto.monto))

    def listar_entre_fechas(self, fecha_desde: str, fecha_hasta: str) -> list[tuple]:
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT id, fecha_hora, categoria, descripcion, monto FROM gastos "
                "WHERE date(fecha_hora) BETWEEN ? AND ? ORDER BY fecha_hora",
                (fecha_desde, fecha_hasta)).fetchall()

    def total_entre_fechas(self, fecha_desde: str, fecha_hasta: str) -> float:
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT COALESCE(SUM(monto), 0) FROM gastos "
                "WHERE date(fecha_hora) BETWEEN ? AND ?",
                (fecha_desde, fecha_hasta)).fetchone()
        return float(fila[0])

    def eliminar(self, gasto_id: int) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM gastos WHERE id = ?", (gasto_id,))


class AdelantoRepository:
    """Adelantos del dueño a los barberos (Etapa 1.8). Mismo patrón que
    GastoRepository: toda escritura es transacción ACID y la fecha la
    asigna el servicio. El barbero se guarda como ID (referencia viva):
    si se renombra, el historial de adelantos sigue al barbero."""

    def __init__(self, db: ConexionDB):
        self.db = db
        self.db.inicializar()

    def guardar(self, adelanto: Adelanto) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute(
                    "INSERT INTO adelantos (uuid, fecha_hora, barbero_id, "
                    "monto, nota) VALUES (?, ?, ?, ?, ?)",
                    (adelanto.uuid, adelanto.fecha_hora, adelanto.barbero_id,
                     adelanto.monto, adelanto.nota))

    def obtener(self, adelanto_id: int) -> tuple | None:
        """(id, fecha_hora, barbero, monto, nota) o None."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT a.id, a.fecha_hora, b.nombre, a.monto, a.nota "
                "FROM adelantos a JOIN barberos b ON b.id = a.barbero_id "
                "WHERE a.id = ?", (adelanto_id,)).fetchone()

    def listar_por_barbero(self, barbero_id: int, limite: int = 50) -> list[tuple]:
        """Últimos adelantos del barbero (más recientes primero), para la
        pestaña BARBEROS. Tuplas (id, fecha_hora, barbero, monto, nota).
        El desempate por id garantiza orden aunque dos adelantos caigan
        en el MISMO segundo (el reloj se guarda con precisión de segundos)."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT a.id, a.fecha_hora, b.nombre, a.monto, a.nota "
                "FROM adelantos a JOIN barberos b ON b.id = a.barbero_id "
                "WHERE a.barbero_id = ? "
                "ORDER BY a.fecha_hora DESC, a.id DESC LIMIT ?",
                (barbero_id, max(int(limite), 1))).fetchall()

    def listar_entre_fechas(self, fecha_desde: str,
                            fecha_hasta: str) -> list[tuple]:
        """Adelantos del rango inclusive (cronológicos), para el reporte
        Excel. Tuplas (id, fecha_hora, barbero, monto, nota)."""
        with closing(self.db.abrir()) as con:
            return con.execute(
                "SELECT a.id, a.fecha_hora, b.nombre, a.monto, a.nota "
                "FROM adelantos a JOIN barberos b ON b.id = a.barbero_id "
                "WHERE date(a.fecha_hora) BETWEEN ? AND ? "
                "ORDER BY a.fecha_hora, a.id",
                (fecha_desde, fecha_hasta)).fetchall()

    def total_entre_fechas(self, fecha_desde: str, fecha_hasta: str) -> float:
        with closing(self.db.abrir()) as con:
            fila = con.execute(
                "SELECT COALESCE(SUM(monto), 0) FROM adelantos "
                "WHERE date(fecha_hora) BETWEEN ? AND ?",
                (fecha_desde, fecha_hasta)).fetchone()
        return float(fila[0])

    def eliminar(self, adelanto_id: int) -> None:
        with closing(self.db.abrir()) as con:
            with con:
                con.execute("DELETE FROM adelantos WHERE id = ?", (adelanto_id,))
