from datetime import datetime, timedelta
import json
import os
import shutil
import sqlite3
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FastFood POS Pro Web")

os.makedirs("imagenes", exist_ok=True)
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

DB_NAME = "restaurante.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# INICIALIZACIÓN Y MIGRACIÓN DE LA BASE DE DATOS
# ==========================================
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            clave TEXT NOT NULL,
            nombre TEXT NOT NULL,
            rol TEXT NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        usuarios_base = [
            ("mesero1", "1234", "Carlos Gómez", "mesero"),
            ("cocina1", "1234", "Chef Mario", "cocina"),
            ("caja1", "1234", "Ana Cajera", "caja"),
            ("admin", "admin", "Administrador", "admin"),
        ]
        cursor.executemany(
            "INSERT INTO usuarios (usuario, clave, nombre, rol) VALUES (?, ?, ?, ?)",
            usuarios_base,
        )

    # 2. Categorías / Secciones
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM categorias")
    if cursor.fetchone()[0] == 0:
        cats_base = [("Hamburguesas",), ("Bebidas",), ("Acompañamientos",), ("Postres",)]
        cursor.executemany("INSERT INTO categorias (nombre) VALUES (?)", cats_base)

    # 3. Productos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            precio REAL NOT NULL,
            categoria TEXT DEFAULT 'General',
            icono TEXT DEFAULT '🍔',
            imagen_path TEXT DEFAULT ''
        )
    """)

    # 4. Pedidos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            mesero TEXT DEFAULT 'Sistema',
            fecha_hora TEXT DEFAULT '',
            metodo_pago TEXT DEFAULT 'efectivo',
            requiere_factura INTEGER DEFAULT 0
        )
    """)

    # Migraciones en pedidos si existía la BD previa
    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN metodo_pago TEXT DEFAULT 'efectivo'")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE pedidos ADD COLUMN requiere_factura INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    # 5. Tabla para Datos de Facturación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER UNIQUE NOT NULL,
            ruc_cedula TEXT NOT NULL,
            razon_social TEXT NOT NULL,
            email TEXT NOT NULL,
            direccion TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            fecha_emision TEXT NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id)
        )
    """)

    # 6. Cajas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cajero TEXT NOT NULL,
            monto_apertura REAL NOT NULL,
            monto_cierre REAL DEFAULT 0.0,
            ventas_efectivo REAL DEFAULT 0.0,
            ventas_transferencia_loja REAL DEFAULT 0.0,
            ventas_transferencia_pichincha REAL DEFAULT 0.0,
            fecha_apertura TEXT NOT NULL,
            fecha_cierre TEXT DEFAULT '',
            estado TEXT DEFAULT 'abierta'
        )
    """)

    try:
        cursor.execute("ALTER TABLE cajas ADD COLUMN ventas_transferencia_loja REAL DEFAULT 0.0")
        cursor.execute("ALTER TABLE cajas ADD COLUMN ventas_transferencia_pichincha REAL DEFAULT 0.0")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()


init_db()


# ==========================================
# RUTAS DE AUTENTICACIÓN Y VISTA
# ==========================================
@app.get("/", response_class=FileResponse)
def index():
    return FileResponse("templates/index.html")


@app.post("/api/login")
def login(usuario: str = Form(...), clave: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nombre, rol FROM usuarios WHERE usuario=? AND clave=?",
        (usuario, clave),
    )
    res = cursor.fetchone()
    conn.close()

    if res:
        return {
            "success": True,
            "user_id": res["id"],
            "nombre": res["nombre"],
            "rol": res["rol"],
        }
    raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")


# ==========================================
# RUTAS DE CATEGORÍAS (SECCIONES DEL MENÚ)
# ==========================================
@app.get("/api/categorias")
def listar_categorias():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categorias ORDER BY nombre ASC")
    cats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return cats


@app.post("/api/categorias")
def crear_categoria(data: dict):
    nombre = data.get("nombre")
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre requerido")

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categorias (nombre) VALUES (?)", (nombre.strip(),))
        conn.commit()
        conn.close()
        return {"success": True}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="La categoría ya existe")


@app.delete("/api/categorias/{cat_id}")
def eliminar_categoria(cat_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM categorias WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ==========================================
# RUTAS DE PRODUCTOS / MENÚ
# ==========================================
@app.get("/api/productos")
def listar_productos():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos ORDER BY id DESC")
    prods = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return prods


@app.post("/api/productos")
async def guardar_producto(
    nombre: str = Form(...),
    precio: float = Form(...),
    categoria: str = Form("General"),
    imagen: Optional[UploadFile] = File(None),
):
    path_relativo = ""
    if imagen and imagen.filename:
        ext = os.path.splitext(imagen.filename)[1]
        nom_limpio = "".join(
            c for c in nombre if c.isalnum() or c in (" ", "_")
        ).rstrip()
        filename = f"prod_{nom_limpio.replace(' ', '_')}{ext}"
        filepath = os.path.join("imagenes", filename)

        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)
        path_relativo = f"/imagenes/{filename}"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO productos (nombre, precio, categoria, icono, imagen_path) VALUES (?, ?, ?, '🍔', ?)",
        (nombre, precio, categoria, path_relativo),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.delete("/api/productos/{prod_id}")
def eliminar_producto(prod_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM productos WHERE id = ?", (prod_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ==========================================
# RUTAS DE PEDIDOS Y FACTURACIÓN
# ==========================================
@app.post("/api/pedidos")
def crear_pedido(data: dict):
    cliente = data.get("cliente")
    items = data.get("items")
    mesero = data.get("mesero")

    if not cliente or not items:
        raise HTTPException(status_code=400, detail="Datos incompletos")

    total = sum(item["precio"] for item in items)
    items_json = json.dumps(items)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO pedidos (cliente, items, total, mesero, fecha_hora, estado) VALUES (?, ?, ?, ?, ?, 'pendiente')",
        (cliente, items_json, total, mesero, fecha_actual),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.get("/api/pedidos")
def obtener_pedidos(
    filtro_fecha: Optional[str] = None, estado_not: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM pedidos WHERE 1=1"
    params = []

    if filtro_fecha:
        hoy = datetime.now()
        if filtro_fecha == "Hoy":
            fecha_str = hoy.strftime("%Y-%m-%d")
            query += " AND fecha_hora LIKE ?"
            params.append(f"{fecha_str}%")
        elif filtro_fecha == "Ayer":
            ayer_str = (hoy - timedelta(days=1)).strftime("%Y-%m-%d")
            query += " AND fecha_hora LIKE ?"
            params.append(f"{ayer_str}%")
        elif filtro_fecha == "Últimos 7 días":
            hace_7 = (hoy - timedelta(days=7)).strftime("%Y-%m-%d")
            query += " AND fecha_hora >= ?"
            params.append(hace_7)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    for r in rows:
        r["items"] = json.loads(r["items"])
    return rows


@app.put("/api/pedidos/{pedido_id}/estado")
def cambiar_estado_pedido(pedido_id: int, data: dict):
    nuevo_estado = data.get("estado")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE pedidos SET estado = ? WHERE id = ?", (nuevo_estado, pedido_id)
    )
    conn.commit()
    conn.close()
    return {"success": True}


# COBRO CON MÉTODOS DE PAGO Y FACTURA
@app.put("/api/pedidos/{pedido_id}/cobrar")
def cobrar_pedido(pedido_id: int, data: dict):
    metodo_pago = data.get("metodo_pago", "efectivo")
    requiere_factura = 1 if data.get("requiere_factura") else 0
    datos_factura = data.get("datos_factura", {})

    conn = get_db()
    cursor = conn.cursor()

    # Actualizar pedido
    cursor.execute(
        "UPDATE pedidos SET estado = 'cobrado', metodo_pago = ?, requiere_factura = ? WHERE id = ?",
        (metodo_pago, requiere_factura, pedido_id),
    )

    # Si se solicita factura, registrar datos fiscales
    if requiere_factura:
        ruc_cedula = datos_factura.get("ruc_cedula")
        razon_social = datos_factura.get("razon_social")
        email = datos_factura.get("email")

        if not ruc_cedula or not razon_social or not email:
            conn.rollback()
            conn.close()
            raise HTTPException(status_code=400, detail="Faltan datos obligatorios para la factura (Cédula/RUC, Nombre, Email)")

        fecha_emision = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """INSERT OR REPLACE INTO facturas 
               (pedido_id, ruc_cedula, razon_social, email, direccion, telefono, fecha_emision)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                pedido_id,
                ruc_cedula,
                razon_social,
                email,
                datos_factura.get("direccion", ""),
                datos_factura.get("telefono", ""),
                fecha_emision,
            ),
        )

    conn.commit()
    conn.close()
    return {"success": True, "metodo_pago": metodo_pago, "facturado": bool(requiere_factura)}


# Obtener factura emitida para un pedido
@app.get("/api/pedidos/{pedido_id}/factura")
def obtener_factura(pedido_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM facturas WHERE pedido_id = ?", (pedido_id,))
    res = cursor.fetchone()
    conn.close()

    if not res:
        raise HTTPException(status_code=404, detail="Factura no encontrada para este pedido")
    return dict(res)


# ==========================================
# RUTAS DE RESUMEN DE VENTAS Y CAJA
# ==========================================
# RESUMEN EN TIEMPO REAL (Para cajero, admin o multiusuario)
@app.get("/api/caja/resumen-ventas")
def resumen_ventas_tiempo_real(cajero: Optional[str] = None):
    conn = get_db()
    cursor = conn.cursor()

    hoy_inicio = datetime.now().strftime("%Y-%m-%d 00:00:00")

    base_monto = 0.0
    if cajero:
        cursor.execute(
            "SELECT monto_apertura FROM cajas WHERE cajero=? AND estado='abierta' ORDER BY id DESC LIMIT 1",
            (cajero,),
        )
        caja = cursor.fetchone()
        if caja:
            base_monto = caja["monto_apertura"]

    # Ventas en Efectivo
    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND (metodo_pago='efectivo' OR metodo_pago IS NULL) AND fecha_hora >= ?",
        (hoy_inicio,),
    )
    ventas_efectivo = cursor.fetchone()[0] or 0.0

    # Ventas Banco de Loja
    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND metodo_pago='transferencia_loja' AND fecha_hora >= ?",
        (hoy_inicio,),
    )
    ventas_loja = cursor.fetchone()[0] or 0.0

    # Ventas Banco Pichincha
    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND metodo_pago='transferencia_pichincha' AND fecha_hora >= ?",
        (hoy_inicio,),
    )
    ventas_pichincha = cursor.fetchone()[0] or 0.0

    total_ventas = ventas_efectivo + ventas_loja + ventas_pichincha
    efectivo_en_caja = base_monto + ventas_efectivo

    conn.close()

    return {
        "base_inicial_caja": base_monto,
        "ventas_efectivo": ventas_efectivo,
        "ventas_banco_loja": ventas_loja,
        "ventas_banco_pichincha": ventas_pichincha,
        "total_ventas": total_ventas,
        "debe_haber_en_efectivo": efectivo_en_caja,
    }


@app.get("/api/caja/estado")
def estado_caja(cajero: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, monto_apertura FROM cajas WHERE cajero=? AND estado='abierta'",
        (cajero,),
    )
    res = cursor.fetchone()
    conn.close()

    if res:
        return {"abierta": True, "id": res["id"], "base": res["monto_apertura"]}
    return {"abierta": False}


@app.post("/api/caja/abrir")
def abrir_caja(data: dict):
    cajero = data.get("cajero")
    monto = float(data.get("monto", 0))
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cajas (cajero, monto_apertura, fecha_apertura, estado) VALUES (?, ?, ?, 'abierta')",
        (cajero, monto, fecha),
    )
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/api/caja/cerrar")
def cerrar_caja(data: dict):
    caja_id = data.get("caja_id")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT monto_apertura, fecha_apertura FROM cajas WHERE id=?", (caja_id,))
    caja = cursor.fetchone()
    if not caja:
        conn.close()
        raise HTTPException(status_code=404, detail="Caja no encontrada")

    base = caja["monto_apertura"]
    fecha_apertura = caja["fecha_apertura"]

    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND (metodo_pago='efectivo' OR metodo_pago IS NULL) AND fecha_hora >= ?",
        (fecha_apertura,),
    )
    ventas_efectivo = cursor.fetchone()[0] or 0.0

    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND metodo_pago='transferencia_loja' AND fecha_hora >= ?",
        (fecha_apertura,),
    )
    ventas_loja = cursor.fetchone()[0] or 0.0

    cursor.execute(
        "SELECT SUM(total) FROM pedidos WHERE estado='cobrado' AND metodo_pago='transferencia_pichincha' AND fecha_hora >= ?",
        (fecha_apertura,),
    )
    ventas_pichincha = cursor.fetchone()[0] or 0.0

    total_ventas = ventas_efectivo + ventas_loja + ventas_pichincha
    esperado_efectivo_en_caja = base + ventas_efectivo

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """UPDATE cajas SET 
            monto_cierre=?, 
            ventas_efectivo=?, 
            ventas_transferencia_loja=?, 
            ventas_transferencia_pichincha=?, 
            fecha_cierre=?, 
            estado='cerrada' 
           WHERE id=?""",
        (esperado_efectivo_en_caja, ventas_efectivo, ventas_loja, ventas_pichincha, fecha, caja_id),
    )
    conn.commit()
    conn.close()

    return {
        "success": True,
        "base_inicial": base,
        "ventas_efectivo": ventas_efectivo,
        "ventas_banco_loja": ventas_loja,
        "ventas_banco_pichincha": ventas_pichincha,
        "total_ventas": total_ventas,
        "efectivo_esperado_en_caja": esperado_efectivo_en_caja,
    }


# ==========================================
# RUTAS DE USUARIOS
# ==========================================
@app.get("/api/usuarios")
def listar_usuarios():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nombre, usuario, clave, rol FROM usuarios")
    users = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return users


@app.post("/api/usuarios")
def guardar_usuario(data: dict):
    u_id = data.get("id")
    nombre = data.get("nombre")
    usuario = data.get("usuario")
    clave = data.get("clave")
    rol = data.get("rol")

    conn = get_db()
    cursor = conn.cursor()

    try:
        if u_id:
            cursor.execute(
                "UPDATE usuarios SET nombre=?, usuario=?, clave=?, rol=? WHERE id=?",
                (nombre, usuario, clave, rol, u_id),
            )
        else:
            cursor.execute(
                "INSERT INTO usuarios (nombre, usuario, clave, rol) VALUES (?, ?, ?, ?)",
                (nombre, usuario, clave, rol),
            )
        conn.commit()
        conn.close()
        return {"success": True}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(
            status_code=400, detail="El nombre de usuario ya existe"
        )


@app.delete("/api/usuarios/{u_id}")
def eliminar_usuario(u_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (u_id,))
    conn.commit()
    conn.close()
    return {"success": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
