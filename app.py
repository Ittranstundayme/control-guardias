from datetime import date, datetime
from io import BytesIO
import json
import os
from zoneinfo import ZoneInfo

import pandas as pd
from reportlab.lib import colors

# Importaciones para generar PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
import streamlit as st

# --- CONFIGURACIÓN DE ZONA HORARIA ---
ZONA_HORARIA = ZoneInfo("America/Guayaquil")

# Configuración de página optimizada para celular
st.set_page_config(
    page_title="Control de Guardias y Bodega", page_icon="🛡️", layout="centered"
)

# Archivos JSON para almacenamiento de datos
ARCHIVO_GUARDIAS = "guardias_registrados.json"
ARCHIVO_PROGRAMACION = "programacion_mensual.json"
ARCHIVO_JORNADAS = "jornadas.json"
ARCHIVO_ACTIVIDADES = "actividades.json"
ARCHIVO_BODEGA = "inventario_bodega.json"
ARCHIVO_MOVIMIENTOS = "movimientos_bodega.json"


# --- FUNCIONES DE ALMACENAMIENTO Y TIEMPO ---
def cargar_json(archivo, por_defecto):
  if os.path.exists(archivo):
    with open(archivo, "r", encoding="utf-8") as f:
      try:
        return json.load(f)
      except json.JSONDecodeError:
        return por_defecto
  return por_defecto


def guardar_json(archivo, datos):
  with open(archivo, "w", encoding="utf-8") as f:
    json.dump(datos, f, indent=4, ensure_ascii=False)


def agregar_registro(archivo, registro):
  datos = cargar_json(archivo, [])
  datos.append(registro)
  guardar_json(archivo, datos)


def obtener_fecha_hora():
  return datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d %H:%M:%S")


# --- FUNCIÓN GENERADORA DE PDF ---
def generar_pdf_jornada(jornada, actividades, movimientos):
  buffer = BytesIO()
  doc = SimpleDocTemplate(
      buffer,
      pagesize=letter,
      rightMargin=30,
      leftMargin=30,
      topMargin=30,
      bottomMargin=30,
  )
  story = []

  styles = getSampleStyleSheet()
  title_style = ParagraphStyle(
      "TitleStyle",
      parent=styles["Heading1"],
      fontSize=18,
      textColor=colors.HexColor("#1E3A8A"),
      spaceAfter=12,
      alignment=1,  # Centrado
  )
  subtitle_style = ParagraphStyle(
      "SubTitleStyle",
      parent=styles["Heading2"],
      fontSize=13,
      textColor=colors.HexColor("#1E3A8A"),
      spaceBefore=12,
      spaceAfter=6,
  )
  text_style = styles["Normal"]

  # Encabezado
  story.append(
      Paragraph("<b>REPORTE OFICIAL DE TURNO DE SEGURIDAD</b>", title_style)
  )
  story.append(Spacer(1, 10))

  # Datos Principales del Turno
  datos_turno = [
      [
          Paragraph("<b>Guardia a Cargo:</b>", text_style),
          Paragraph(jornada.get("guardia", "N/A"), text_style),
      ],
      [
          Paragraph("<b>Turno:</b>", text_style),
          Paragraph(jornada.get("turno", "N/A"), text_style),
      ],
      [
          Paragraph("<b>Inicio de Jornada:</b>", text_style),
          Paragraph(jornada.get("inicio", "N/A"), text_style),
      ],
      [
          Paragraph("<b>Fin de Jornada:</b>", text_style),
          Paragraph(jornada.get("fin", "En curso"), text_style),
      ],
      [
          Paragraph("<b>Observaciones de Cierre:</b>", text_style),
          Paragraph(
              jornada.get("observaciones_cierre", "Sin observaciones"), text_style
          ),
      ],
  ]
  t_info = Table(datos_turno, colWidths=[150, 380])
  t_info.setStyle(
      TableStyle([
          ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F4F6")),
          ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
          ("PADDING", (0, 0), (-1, -1), 6),
      ])
  )
  story.append(t_info)

  # Novedades / Actividades
  story.append(
      Paragraph("<b>1. Bitácora de Novedades y Recorridos</b>", subtitle_style)
  )
  if actividades:
    tabla_act = [["Hora / Fecha", "Descripción de la Novedad"]]
    for a in actividades:
      tabla_act.append([
          Paragraph(a.get("fecha_hora", ""), text_style),
          Paragraph(a.get("actividad", ""), text_style),
      ])

    t_act = Table(tabla_act, colWidths=[130, 400])
    t_act.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(t_act)
  else:
    story.append(
        Paragraph(
            "No se registraron novedades durante esta jornada.", text_style
        )
    )

  # Movimientos de Bodega
  story.append(
      Paragraph(
          "<b>2. Movimientos e Insumos Retirados de Bodega</b>", subtitle_style
      )
  )
  if movimientos:
    tabla_mov = [
        ["Fecha / Hora", "Artículo", "Cant.", "Lugar / Destino Designado"]
    ]
    for m in movimientos:
      destino = f"{m.get('area_destino', '')} ({m.get('detalle_destino', '')})"
      tabla_mov.append([
          Paragraph(m.get("fecha_hora", ""), text_style),
          Paragraph(m.get("articulo", ""), text_style),
          Paragraph(str(m.get("cantidad", 1)), text_style),
          Paragraph(destino, text_style),
      ])

    t_mov = Table(tabla_mov, colWidths=[110, 140, 50, 230])
    t_mov.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("PADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(t_mov)
  else:
    story.append(
        Paragraph(
            "No se registraron retiradas de bodega durante esta jornada.",
            text_style,
        )
    )

  doc.build(story)
  buffer.seek(0)
  return buffer


# Cargar inventario
bodega_inicial = {
    "Linterna": {"cantidad": 5, "unidad": "uds"},
    "Radio Transmisor": {"cantidad": 4, "unidad": "uds"},
    "Baterías AA": {"cantidad": 20, "unidad": "uds"},
    "Chaleco Reflectivo": {"cantidad": 6, "unidad": "uds"},
    "Cuaderno de Bitácora": {"cantidad": 3, "unidad": "uds"},
}
st.session_state.bodega = cargar_json(ARCHIVO_BODEGA, bodega_inicial)

if "jornada_activa" not in st.session_state:
  st.session_state.jornada_activa = cargar_json("jornada_activa.json", None)

# --- ENCABEZADO ---
st.title("🛡️ Control de Seguridad")

if st.session_state.jornada_activa:
  ja = st.session_state.jornada_activa
  st.success(
      f"🟢 **TURNO ACTIVO:** {ja['guardia']} | **Turno:** {ja['turno']} |"
      f" **Inicio:** {ja['inicio']}"
  )
else:
  st.warning(
      "🔴 **NO HAY JORNADA ACTIVA.** Por favor, inicie jornada a continuación."
  )

st.divider()

# --- PESTAÑAS DE NAVEGACIÓN ---
tab_jornada, tab_actividades, tab_bodega, tab_reportes, tab_admin = st.tabs(
    ["👤 Jornada", "📝 Actividades", "📦 Bodega", "📊 Reportes", "⚙️ Admin"]
)

# ==========================================
# 1. GESTIÓN DE JORNADA (PIN OBLIGATORIO)
# ==========================================
with tab_jornada:
  st.header("Gestión de Jornada")
  guardias_db = cargar_json(ARCHIVO_GUARDIAS, [])
  programaciones_db = cargar_json(ARCHIVO_PROGRAMACION, [])
  hoy_str = datetime.now(ZONA_HORARIA).strftime("%Y-%m-%d")

  if not st.session_state.jornada_activa:
    st.subheader("Iniciar Jornada de Hoy")

    if not guardias_db:
      st.error(
          "⚠️ No hay guardias registrados. El Administrador debe agregarlos en"
          " la pestaña **⚙️ Admin**."
      )
    else:
      programados_hoy = [
          p
          for p in programaciones_db
          if p["fecha_inicio"] <= hoy_str <= p["fecha_fin"]
      ]

      if programados_hoy:
        st.info("📅 **Programación para el día de hoy:**")
        for p in programados_hoy:
          st.write(f"• **{p['guardia']}**: Turno **{p['turno']}**")

      with st.form("form_inicio_jornada", clear_on_submit=False):
        guardia_dict = {g["nombre"]: g for g in guardias_db}
        guardia_sel_nombre = st.selectbox(
            "Seleccione su Nombre", list(guardia_dict.keys())
        )
        pin_ingresado = st.text_input(
            "Ingrese su Código PIN (Obligatorio - 3 dígitos)",
            type="password",
            max_chars=3,
        )
        turno_sel = st.selectbox(
            "Seleccione el Turno a Iniciar", ["Día", "Noche"]
        )

        btn_inicio = st.form_submit_button("🔑 Validar PIN e Iniciar Jornada")

        if btn_inicio:
          datos_g = guardia_dict[guardia_sel_nombre]
          pin_real = str(datos_g.get("pin", "")).strip()
          pin_limpio = pin_ingresado.strip()

          if not pin_limpio:
            st.error(
                "⚠️ DEBE INGRESAR SU PIN DE 3 DÍGITOS PARA INICIAR LA JORNADA."
            )
          elif not pin_real or pin_real == "N/A":
            st.error(
                "❌ Este guardia no tiene un PIN registrado en la base de datos."
                " Contacte al Administrador."
            )
          elif pin_limpio != pin_real:
            st.error("❌ PIN INCORRECTO. Acceso denegado.")
          else:
            jornada = {
                "id": datetime.now(ZONA_HORARIA).strftime("%Y%m%d_%H%M%S"),
                "guardia": datos_g["nombre"],
                "pin": pin_real,
                "turno": turno_sel,
                "inicio": obtener_fecha_hora(),
                "fin": None,
                "estado": "Activa",
            }
            st.session_state.jornada_activa = jornada
            guardar_json("jornada_activa.json", jornada)
            st.success(
                f"✅ PIN verificado con éxito. Jornada iniciada para"
                f" {datos_g['nombre']} ({turno_sel})."
            )
            st.rerun()
  else:
    st.subheader("Finalizar Jornada Actual")
    st.info(
        f"Guardia activo: **{st.session_state.jornada_activa['guardia']}**"
        f" ({st.session_state.jornada_activa['turno']})"
    )
    obs = st.text_area("Observaciones de entrega de turno")

    if st.button("🔴 Cerrar y Finalizar Jornada"):
      jornada = st.session_state.jornada_activa
      jornada["fin"] = obtener_fecha_hora()
      jornada["estado"] = "Finalizada"
      jornada["observaciones_cierre"] = obs

      agregar_registro(ARCHIVO_JORNADAS, jornada)
      st.session_state.jornada_activa = None
      if os.path.exists("jornada_activa.json"):
        os.remove("jornada_activa.json")

      st.success("✅ Jornada finalizada con éxito.")
      st.rerun()

# ==========================================
# 2. ACTIVIDADES Y NOVEDADES
# ==========================================
with tab_actividades:
  st.header("Bitácora de Novedades")
  if not st.session_state.jornada_activa:
    st.info("⚠️ Debe **Iniciar Jornada** para registrar actividades.")
  else:
    with st.form("form_actividad", clear_on_submit=True):
      actividad = st.text_area("Descripción de la novedad o recorrido")
      btn_actividad = st.form_submit_button("Guardar Actividad")

      if btn_actividad and actividad.strip():
        registro = {
            "jornada_id": st.session_state.jornada_activa["id"],
            "fecha_hora": obtener_fecha_hora(),
            "guardia": st.session_state.jornada_activa["guardia"],
            "turno": st.session_state.jornada_activa["turno"],
            "actividad": actividad,
        }
        agregar_registro(ARCHIVO_ACTIVIDADES, registro)
        st.success("✅ Novedad registrada.")

# ==========================================
# 3. SALIDA DE INVENTARIO
# ==========================================
with tab_bodega:
  st.header("📦 Salida de Insumos de Bodega")

  if not st.session_state.jornada_activa:
    st.info("⚠️ Debe **Iniciar Jornada** para registrar salidas de bodega.")
  elif not st.session_state.bodega:
    st.warning("⚠️ No hay productos disponibles en bodega.")
  else:
    with st.form("form_salida_guardia", clear_on_submit=True):
      item_seleccionado = st.selectbox(
          "Seleccione el Artículo a retirar:",
          list(st.session_state.bodega.keys()),
      )
      prod_info = st.session_state.bodega[item_seleccionado]

      st.write(
          f"Disponible en bodega: **{prod_info.get('cantidad', 0)}"
          f" {prod_info.get('unidad', 'uds')}**"
      )

      cant_retirar = st.number_input(
          "Cantidad a retirar", min_value=1, step=1
      )
      area_destino = st.selectbox(
          "Área / Lugar Designado para el uso:",
          [
              "Garita Principal",
              "Bodega Central",
              "Parqueadero / Vehículos",
              "Perímetro Norte",
              "Perímetro Sur",
              "Oficinas Administrativas",
              "Otro (Especificar en detalle)",
          ],
      )
      observacion_destino = st.text_input("Detalle específico del uso o motivo")

      pin_confirmacion = st.text_input(
          "Confirme su PIN de 3 dígitos para autorizar",
          type="password",
          max_chars=3,
      )

      btn_retirar = st.form_submit_button("Confirmar Salida de Insumo")

      if btn_retirar:
        pin_guardia_activo = str(
            st.session_state.jornada_activa.get("pin", "")
        ).strip()

        if not pin_confirmacion.strip():
          st.error("⚠️ Debe ingresar su PIN para autorizar el retiro.")
        elif pin_confirmacion.strip() != pin_guardia_activo:
          st.error("❌ PIN de confirmación incorrecto.")
        elif cant_retirar > prod_info["cantidad"]:
          st.error(
              f"❌ Stock insuficiente. Solo quedan {prod_info['cantidad']}"
              f" {prod_info['unidad']}."
          )
        else:
          st.session_state.bodega[item_seleccionado][
              "cantidad"
          ] -= cant_retirar
          guardar_json(ARCHIVO_BODEGA, st.session_state.bodega)

          mov = {
              "jornada_id": st.session_state.jornada_activa["id"],
              "fecha_hora": obtener_fecha_hora(),
              "tipo": "Salida",
              "guardia": st.session_state.jornada_activa["guardia"],
              "articulo": item_seleccionado,
              "cantidad": cant_retirar,
              "area_destino": area_destino,
              "detalle_destino": observacion_destino,
          }
          agregar_registro(ARCHIVO_MOVIMIENTOS, mov)
          st.success(
              f"✅ Autenticación correcta. Registrada salida de {cant_retirar}"
              f" {prod_info['unidad']} de {item_seleccionado}."
          )
          st.rerun()

# ==========================================
# 4. REPORTES Y GENERACIÓN DE PDF (PRIVADO ADMIN)
# ==========================================
with tab_reportes:
  st.header("📊 Reportes de Jornadas (Privado)")
  st.info("🔒 Esta sección es de uso exclusivo de la Administración.")

  clave_rep = st.text_input(
      "Ingrese la clave de Administrador para ver reportes",
      type="password",
      key="pwd_rep",
  )

  if clave_rep == "admin123":
    jornadas_guardadas = cargar_json(ARCHIVO_JORNADAS, [])
    if not jornadas_guardadas:
      st.info("No hay reportes de jornadas finalizadas.")
    else:
      opciones_jornadas = {}
      for j in reversed(jornadas_guardadas):
        fecha = j.get("inicio", "Sin fecha")
        texto_opcion = f"{fecha} - Guardia: {j['guardia']} ({j['turno']})"
        opciones_jornadas[texto_opcion] = j

      j_sel_str = st.selectbox(
          "Seleccione la Jornada:", list(opciones_jornadas.keys())
      )
      j_sel = opciones_jornadas[j_sel_str]

      acts = [
          a
          for a in cargar_json(ARCHIVO_ACTIVIDADES, [])
          if a.get("jornada_id") == j_sel["id"]
      ]
      movs = [
          m
          for m in cargar_json(ARCHIVO_MOVIMIENTOS, [])
          if m.get("jornada_id") == j_sel["id"]
      ]

      st.markdown("---")
      pdf_bytes = generar_pdf_jornada(j_sel, acts, movs)

      st.download_button(
          label="📄 Descargar Reporte en PDF",
          data=pdf_bytes,
          file_name=f"Reporte_Turno_{j_sel['guardia']}_{j_sel['id']}.pdf",
          mime="application/pdf",
      )
      st.markdown("---")

      st.markdown("### 📄 Vista Previa en Pantalla")
      st.write(f"* **Guardia:** {j_sel['guardia']}")
      st.write(f"* **Turno:** {j_sel['turno']}")
      st.write(f"* **Inicio:** {j_sel['inicio']} | **Fin:** {j_sel['fin']}")
      st.write(
          f"* **Observaciones Cierre:**"
          f" {j_sel.get('observaciones_cierre', 'Sin observaciones')}"
      )

      st.subheader("📝 Novedades Registradas")
      for a in acts:
        st.write(f"⏱️ **{a['fecha_hora']}**: {a['actividad']}")

      st.subheader("📦 Insumos Retirados en el Turno")
      for m in movs:
        st.write(
            f"• **{m['articulo']}** - Cant: {m['cantidad']} ➔"
            f" **Destino:** {m.get('area_destino')} ({m.get('detalle_destino', '')})"
        )

# ==========================================
# 5. PANEL DE ADMINISTRACIÓN
# ==========================================
with tab_admin:
  st.header("⚙️ Panel de Administración")
  clave_admin = st.text_input(
      "Ingrese la Contraseña de Administrador", type="password", key="pwd_adm"
  )

  if clave_admin == "admin123":
    st.success("🔓 Acceso de Administrador Confirmado")

    admin_subtab1, admin_subtab2, admin_subtab3 = st.tabs([
        "📦 Gestión de Bodega",
        "👥 Gestor de Guardias y PINs",
        "📅 Programación de Turnos",
    ])

    # --- GESTIÓN DE BODEGA ---
    with admin_subtab1:
      st.subheader("➕ 1. Registrar o Reabastecer Producto")
      with st.form("form_alta_bodega", clear_on_submit=True):
        nombre_prod = st.text_input("Nombre del Producto")
        cant_prod = st.number_input(
            "Cantidad a Ingresar", min_value=1, step=1
        )
        unidad_prod = st.text_input("Unidad de Medida", value="uds")

        btn_alta = st.form_submit_button("Guardar / Reabastecer en Bodega")

        if btn_alta:
          if nombre_prod.strip():
            nom = nombre_prod.strip().title()
            if nom in st.session_state.bodega:
              st.session_state.bodega[nom]["cantidad"] += cant_prod
            else:
              st.session_state.bodega[nom] = {
                  "cantidad": cant_prod,
                  "unidad": unidad_prod,
              }
            guardar_json(ARCHIVO_BODEGA, st.session_state.bodega)

            mov_admin = {
                "jornada_id": "ADMIN",
                "fecha_hora": obtener_fecha_hora(),
                "tipo": "Ingreso / Reabastecimiento",
                "guardia": "Administrador",
                "articulo": nom,
                "cantidad": cant_prod,
                "area_destino": "Bodega Central",
                "detalle_destino": "Reabastecimiento por Administración",
            }
            agregar_registro(ARCHIVO_MOVIMIENTOS, mov_admin)

            st.success(
                f"✅ Registradas {cant_prod} {unidad_prod} de **{nom}** en"
                " bodega."
            )
            st.rerun()
          else:
            st.error("❌ El nombre del producto es obligatorio.")

      st.divider()

      st.subheader("🔻 2. Dar de Baja Stock (Daño, Pérdida o Merma)")
      if st.session_state.bodega:
        with st.form("form_baja_bodega", clear_on_submit=True):
          prod_baja = st.selectbox(
              "Seleccione Producto para dar de baja:",
              list(st.session_state.bodega.keys()),
              key="sel_prod_baja",
          )
          stock_actual = st.session_state.bodega[prod_baja]["cantidad"]
          unit_actual = st.session_state.bodega[prod_baja]["unidad"]

          st.caption(
              f"Stock actual disponible: **{stock_actual} {unit_actual}**"
          )

          cant_baja = st.number_input(
              "Cantidad a dar de baja",
              min_value=1,
              max_value=max(1, stock_actual),
              step=1,
          )
          motivo_baja = st.text_input(
              "Motivo de la baja (Ej. Deterioro, Pérdida, Caducidad)"
          )

          btn_baja = st.form_submit_button("Descontar Stock")

          if btn_baja:
            if cant_baja > stock_actual:
              st.error("❌ La cantidad supera el stock actual disponible.")
            elif not motivo_baja.strip():
              st.error(
                  "⚠️ Debe ingresar un motivo justificado para dar de baja el"
                  " producto."
              )
            else:
              st.session_state.bodega[prod_baja]["cantidad"] -= cant_baja
              guardar_json(ARCHIVO_BODEGA, st.session_state.bodega)

              mov_baja = {
                  "jornada_id": "ADMIN_BAJA",
                  "fecha_hora": obtener_fecha_hora(),
                  "tipo": "Baja de Stock",
                  "guardia": "Administrador",
                  "articulo": prod_baja,
                  "cantidad": cant_baja,
                  "area_destino": "Baja / Descarte",
                  "detalle_destino": f"Motivo: {motivo_baja.strip()}",
              }
              agregar_registro(ARCHIVO_MOVIMIENTOS, mov_baja)

              st.success(
                  f"✅ Se descontaron {cant_baja} {unit_actual} de **{prod_baja}**."
              )
              st.rerun()
      else:
        st.info("No hay productos en bodega.")

      st.divider()

      st.subheader("🗑️ 3. Eliminar Producto Definitivamente del Catálogo")
      if st.session_state.bodega:
        prod_eliminar = st.selectbox(
            "Seleccione Producto a eliminar del sistema:",
            list(st.session_state.bodega.keys()),
            key="sel_prod_eliminar",
        )

        if st.button("🗑️ Eliminar Producto Definitivamente", type="primary"):
          del st.session_state.bodega[prod_eliminar]
          guardar_json(ARCHIVO_BODEGA, st.session_state.bodega)
          st.success(
              f"🗑️ Producto **{prod_eliminar}** eliminado del catálogo de"
              " bodega."
          )
          st.rerun()
      else:
        st.info("No hay productos para eliminar.")

      st.divider()

      st.subheader("📋 Inventario Actual de Bodega")
      if st.session_state.bodega:
        for prod, info in st.session_state.bodega.items():
          st.write(
              f"• **{prod}**: {info.get('cantidad', 0)}"
              f" {info.get('unidad', 'uds')}"
          )
      else:
        st.info("El inventario está vacío.")

    # --- GESTOR DE GUARDIAS ---
    with admin_subtab2:
      st.subheader("1. Registrar Nuevo Guardia")
      with st.form("form_reg_g", clear_on_submit=True):
        nom_g = st.text_input("Nombre del Guardia")
        ced_g = st.text_input("Cédula")
        pin_g = st.text_input("PIN de Acceso (3 dígitos)", max_chars=3)

        if st.form_submit_button("Guardar Nuevo Guardia"):
          if (
              nom_g.strip()
              and len(pin_g.strip()) == 3
              and pin_g.strip().isdigit()
          ):
            g_db = cargar_json(ARCHIVO_GUARDIAS, [])
            g_db.append({
                "id": len(g_db) + 1,
                "nombre": nom_g.strip().title(),
                "cedula": ced_g.strip(),
                "pin": pin_g.strip(),
            })
            guardar_json(ARCHIVO_GUARDIAS, g_db)
            st.success(
                f"✅ Guardia **{nom_g}** registrado con PIN **{pin_g}**."
            )
            st.rerun()
          else:
            st.error("❌ Ingrese nombre y PIN numérico de 3 dígitos.")

      st.divider()
      st.subheader("2. Editar PIN o Asignar a Guardia Existente")
      g_db_lista = cargar_json(ARCHIVO_GUARDIAS, [])

      if g_db_lista:
        dict_guardias_edit = {g["nombre"]: g for g in g_db_lista}
        g_selec_editar = st.selectbox(
            "Seleccione el Guardia para cambiar/asignar PIN:",
            list(dict_guardias_edit.keys()),
        )
        nuevo_pin = st.text_input(
            "Nuevo PIN de 3 dígitos:", max_chars=3, key="edit_pin_input"
        )

        if st.button("🔄 Actualizar PIN del Guardia"):
          if len(nuevo_pin.strip()) == 3 and nuevo_pin.strip().isdigit():
            for g in g_db_lista:
              if g["nombre"] == g_selec_editar:
                g["pin"] = nuevo_pin.strip()
                break
            guardar_json(ARCHIVO_GUARDIAS, g_db_lista)
            st.success(
                f"✅ ¡PIN actualizado a **{nuevo_pin}** para"
                f" {g_selec_editar}!"
            )
            st.rerun()
          else:
            st.error("❌ El PIN debe tener exactamente 3 números.")

        st.divider()
        st.subheader("3. Eliminar Guardia del Sistema")
        g_selec_eliminar = st.selectbox(
            "Seleccione el Guardia a Eliminar:",
            list(dict_guardias_edit.keys()),
            key="elim_g_sel",
        )

        if st.button(
            "🗑️ Eliminar Guardia Definitivamente", type="primary"
        ):
          nueva_lista = [
              g for g in g_db_lista if g["nombre"] != g_selec_eliminar
          ]
          guardar_json(ARCHIVO_GUARDIAS, nueva_lista)
          st.success(
              f"🗑️ Guardia **{g_selec_eliminar}** eliminado correctamente."
          )
          st.rerun()

      st.divider()
      st.subheader("👥 Lista Actual de Guardias")
      if g_db_lista:
        for g in g_db_lista:
          st.write(
              f"• **{g['nombre']}** | Cédula: {g['cedula']} | PIN Actual:"
              f" **`{g.get('pin', 'Sin PIN')}`**"
          )
      else:
        st.info("No hay guardias registrados.")

    # --- PROGRAMACIÓN MENSUAL Y CARGA EXCEL ---
    with admin_subtab3:
      st.subheader("📅 Programación de Turnos")
      g_db = cargar_json(ARCHIVO_GUARDIAS, [])

      if g_db:
        st.markdown("### 📤 Cargar desde archivo Excel")
        archivo_excel = st.file_uploader(
            "Selecciona un archivo Excel (.xlsx)", type=["xlsx", "xls"]
        )

        if archivo_excel is not None:
          try:
            df = pd.read_excel(archivo_excel)
            columnas_esperadas = {
                "Guardia",
                "Turno",
                "Fecha Inicio",
                "Fecha Fin",
            }
            if not columnas_esperadas.issubset(set(df.columns)):
              st.error(
                  "❌ El Excel debe contener las columnas: Guardia, Turno,"
                  " Fecha Inicio, Fecha Fin"
              )
            else:
              st.write("📋 **Vista previa de los datos a cargar:**")
              st.dataframe(df)

              modo_carga = st.radio(
                  "Modo de carga:",
                  [
                      "Añadir a la programación existente",
                      "Reemplazar toda la programación actual",
                  ],
              )

              if st.button("🚀 Cargar Programación desde Excel"):
                registros_nuevos = []
                for _, row in df.iterrows():
                  registros_nuevos.append({
                      "guardia": str(row["Guardia"]).strip(),
                      "turno": str(row["Turno"]).strip().title(),
                      "fecha_inicio": pd.to_datetime(
                          row["Fecha Inicio"]
                      ).strftime("%Y-%m-%d"),
                      "fecha_fin": pd.to_datetime(row["Fecha Fin"]).strftime(
                          "%Y-%m-%d"
                      ),
                  })

                if modo_carga == "Reemplazar toda la programación actual":
                  p_db = registros_nuevos
                else:
                  p_db = cargar_json(ARCHIVO_PROGRAMACION, [])
                  p_db.extend(registros_nuevos)

                guardar_json(ARCHIVO_PROGRAMACION, p_db)
                st.success(
                    f"✅ Se cargaron correctamente {len(registros_nuevos)}"
                    " registros."
                )
                st.rerun()

          except Exception as e:
            st.error(f"❌ Error al procesar Excel: {e}")

        st.divider()

        st.markdown("### ✍️ Registro Manual Individual")
        with st.form("form_prog_m", clear_on_submit=True):
          g_sel_prog = st.selectbox("Guardia", [g["nombre"] for g in g_db])
          t_sel_prog = st.selectbox("Turno", ["Día", "Noche", "Descanso"])
          fecha_local_hoy = datetime.now(ZONA_HORARIA).date()
          f_i = st.date_input("Fecha Inicio", value=fecha_local_hoy)
          f_f = st.date_input("Fecha Fin", value=fecha_local_hoy)

          if st.form_submit_button("Guardar Programación Individual"):
            p_db = cargar_json(ARCHIVO_PROGRAMACION, [])
            p_db.append({
                "guardia": g_sel_prog,
                "turno": t_sel_prog,
                "fecha_inicio": f_i.strftime("%Y-%m-%d"),
                "fecha_fin": f_f.strftime("%Y-%m-%d"),
            })
            guardar_json(ARCHIVO_PROGRAMACION, p_db)
            st.success("✅ Programación guardada correctamente.")
            st.rerun()
      else:
        st.warning(
            "⚠️ Primero debe registrar guardias en la pestaña **👥 Gestor de"
            " Guardias y PINs**."
        )

      st.divider()
      st.subheader("📅 Turnos y Descansos Programados Actualmente")
      progs = cargar_json(ARCHIVO_PROGRAMACION, [])

      if progs:
        for idx, p in enumerate(progs):
          icono_turno = "🟢" if p["turno"] in ["Día", "Noche"] else "🟡"

          col_info, col_btn = st.columns([4, 1])

          with col_info:
            st.write(
                f"• {icono_turno} **{p['guardia']}** | Turno: **{p['turno']}** |"
                f" Desde: `{p['fecha_inicio']}` hasta `{p['fecha_fin']}`"
            )

          with col_btn:
            if st.button("🗑️ Eliminar", key=f"btn_elim_prog_{idx}"):
              progs.pop(idx)
              guardar_json(ARCHIVO_PROGRAMACION, progs)
              st.success("✅ Asignación eliminada.")
              st.rerun()

        st.divider()
        if st.button(
            "🗑️ Borrar TODO el Historial de Programación", type="secondary"
        ):
          guardar_json(ARCHIVO_PROGRAMACION, [])
          st.success("Historial de programación limpiado.")
          st.rerun()
      else:
        st.info("No hay programaciones registradas aún.")
