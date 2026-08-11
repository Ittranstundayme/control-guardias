import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FastFood POS Pro Web")

# Directorios de estáticos e imágenes
os.makedirs("imagenes", exist_ok=True)
app.mount("/imagenes", StaticFiles(directory="imagenes"), name="imagenes")

DB_NAME = "restaurante.db"


def get_db():
  conn = sqlite3.connect(DB_NAME)
  conn.row_factory = sqlite3.Row
  return conn


# ==========================================
# INICIALIZACIÓN DE LA BASE DE DATOS
# ==========================================
def init_db():
  conn = get_db()
  cursor = conn.cursor()

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
        "INSERT INTO usuarios (usuario, clave, nombre, rol) VALUES (?, ?, ?,"
        " ?)",
        usuarios_base,
    )

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

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            mesero TEXT DEFAULT 'Sistema',
            fecha_hora TEXT DEFAULT ''
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS cajas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cajero TEXT NOT NULL,
            monto_apertura REAL NOT NULL,
            monto_cierre REAL DEFAULT 0.0,
            ventas_efectivo REAL DEFAULT 0.0,
            fecha_apertura TEXT NOT NULL,
            fecha_cierre TEXT DEFAULT '',
            estado TEXT DEFAULT 'abierta'
        )
    """)

  conn.commit()
  conn.close()


init_db()


# ==========================================
# RUTAS DE AUTENTICACIÓN Y VISTA
# ==========================================
@app.get("/", response_class=FileResponse)
def index():
  # Servir directamente el archivo index.html evitando la caché de Jinja2
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
  raise HTTPException(
      status_code=401, detail="Usuario o contraseña incorrectos"
  )


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
      "INSERT INTO productos (nombre, precio, categoria, icono, imagen_path)"
      " VALUES (?, ?, 'General', '🍔', ?)",
      (nombre, precio, path_relativo),
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
# RUTAS DE PEDIDOS Y MESERO
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
      "INSERT INTO pedidos (cliente, items, total, mesero, fecha_hora) VALUES"
      " (?, ?, ?, ?, ?)",
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


@app.post("/api/pedidos/{pedido_id}/adicional")
def agregar_item_adicional(pedido_id: int, data: dict):
  prod_id = data.get("producto_id")
  conn = get_db()
  cursor = conn.cursor()

  cursor.execute("SELECT nombre, precio FROM productos WHERE id = ?", (prod_id,))
  producto = cursor.fetchone()

  cursor.execute("SELECT items, total FROM pedidos WHERE id = ?", (pedido_id,))
  pedido = cursor.fetchone()

  if producto and pedido:
    items = json.loads(pedido["items"])
    items.append({"nombre": producto["nombre"], "precio": producto["precio"]})
    nuevo_total = pedido["total"] + producto["precio"]

    cursor.execute(
        "UPDATE pedidos SET items = ?, total = ? WHERE id = ?",
        (json.dumps(items), nuevo_total, pedido_id),
    )
    conn.commit()

  conn.close()
  return {"success": True}


# ==========================================
# RUTAS DE USUARIOS Y PERSONAL
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
          "INSERT INTO usuarios (nombre, usuario, clave, rol) VALUES (?, ?,"
          " ?, ?)",
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


# ==========================================
# RUTAS DE CAJA (APERTURA, ARQUEO Y CIERRE)
# ==========================================
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
      "INSERT INTO cajas (cajero, monto_apertura, fecha_apertura, estado)"
      " VALUES (?, ?, ?, 'abierta')",
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

  cursor.execute("SELECT SUM(total) FROM pedidos WHERE estado='cobrado'")
  total_ventas = cursor.fetchone()[0] or 0.0

  cursor.execute("SELECT monto_apertura FROM cajas WHERE id=?", (caja_id,))
  caja = cursor.fetchone()
  base = caja["monto_apertura"] if caja else 0.0
  esperado = base + total_ventas

  fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute(
      "UPDATE cajas SET monto_cierre=?, ventas_efectivo=?, fecha_cierre=?,"
      " estado='cerrada' WHERE id=?",
      (esperado, total_ventas, fecha, caja_id),
  )
  conn.commit()
  conn.close()

  return {
      "success": True,
      "base": base,
      "ventas": total_ventas,
      "esperado": esperado,
  }


if __name__ == "__main__":
  import uvicorn

  uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
