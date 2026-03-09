import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import urllib.parse
import time

# ------------------ CONFIGURACIÓN GENERAL ------------------

with st.spinner('Iniciando sistema Champlitte... 🥐'):
    zona_mx = pytz.timezone('America/Mexico_City')
    fecha_hoy_mx = datetime.now(zona_mx).date()
    numero_whatsapp = "522283530069"

st.set_page_config(page_title="Inventario Champlitte MX", page_icon="🥐", layout="wide")

# ------------------ BASE DE DATOS ------------------

conn = sqlite3.connect('inventario_pan.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS captura_actual (nombre TEXT, fecha_cad DATE, cantidad INTEGER)')
c.execute('CREATE TABLE IF NOT EXISTS base_anterior (nombre TEXT, fecha_cad DATE, cantidad INTEGER)')
c.execute('''CREATE TABLE IF NOT EXISTS historial_ventas (
    nombre TEXT, fecha_cad DATE, habia INTEGER, quedan INTEGER, vendidos INTEGER, fecha_corte DATETIME
)''')
conn.commit()

# ------------------ FUNCIONES ------------------

def sonido_click():
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-16.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

def sumar(valor):
    st.session_state.conteo_temp += valor
    sonido_click()

def resetear():
    st.session_state.conteo_temp = 0
    sonido_click()

# ------------------ SIDEBAR RESET ------------------

st.sidebar.header("⚙️ Configuración")
with st.sidebar.expander("🚨 Zona de Peligro"):
    confirmar_reset = st.checkbox("Confirmar borrar todo")
    if st.button("⚠️ RESET TOTAL"):
        if confirmar_reset:
            c.execute("DELETE FROM captura_actual"); c.execute("DELETE FROM base_anterior"); c.execute("DELETE FROM historial_ventas")
            conn.commit()
            st.sidebar.success("✅ Datos borrados"); time.sleep(1); st.rerun()

# ------------------ TABS ------------------

tab1, tab2, tab3, tab4 = st.tabs(["📝 Conteo", "📦 Inventario y Corte", "📊 Análisis", "🧮 Calculadora"])

# ------------------------------------------------------------
# TAB 1: CONTEO
# ------------------------------------------------------------
with tab1:
    if "conteo_temp" not in st.session_state: st.session_state.conteo_temp = 0
    
    col_busq, col_limpiar = st.columns([4,1])
    with col_busq:
        buscar = st.text_input("Buscar", placeholder="🔎 BUSCAR PRODUCTO...", key="buscar_prod", label_visibility="collapsed").upper()
    with col_limpiar:
        if st.button("Sweep", use_container_width=True): st.session_state.buscar_prod = ""; st.rerun()

    nombres_prev = [r[0] for r in c.execute("SELECT nombre FROM base_anterior UNION SELECT nombre FROM captura_actual").fetchall()]
    sugerencias = [p for p in nombres_prev if buscar in p] if buscar else nombres_prev

    col1, col2 = st.columns([2,1])
    with col1:
        nombre_input = st.selectbox("Producto", sugerencias) if sugerencias else buscar
    with col2:
        f_cad = st.date_input("Caducidad", value=fecha_hoy_mx)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.button("+1", use_container_width=True, on_click=sumar, args=(1,))
    with c2: st.button("+5", use_container_width=True, on_click=sumar, args=(5,))
    with c3: st.button("+10", use_container_width=True, on_click=sumar, args=(10,))
    with c4: st.button("Borrar", use_container_width=True, on_click=resetear)

    st.metric("A registrar", st.session_state.conteo_temp)

    if st.button("➕ Registrar en Inventario", use_container_width=True, type="primary"):
        if nombre_input:
            nombre_final = str(nombre_input).strip().upper()
            existe = c.execute("SELECT cantidad FROM captura_actual WHERE nombre=? AND fecha_cad=?", (nombre_final, str(f_cad))).fetchone()
            if existe:
                c.execute("UPDATE captura_actual SET cantidad=cantidad+? WHERE nombre=? AND fecha_cad=?", (int(st.session_state.conteo_temp), nombre_final, str(f_cad)))
            else:
                c.execute("INSERT INTO captura_actual VALUES (?,?,?)", (nombre_final, str(f_cad), int(st.session_state.conteo_temp)))
            conn.commit()
            st.session_state.conteo_temp = 0
            st.success(f"✅ {nombre_final} registrado")
            time.sleep(1); st.rerun()

    st.divider()
    df_hoy = pd.read_sql("SELECT rowid, nombre, fecha_cad, cantidad FROM captura_actual", conn)
    df_editado = st.data_editor(df_hoy, column_config={"rowid": None}, num_rows="dynamic", use_container_width=True, key="ed_conteo")
    
    if st.button("💾 Guardar Cambios"):
        c.execute("DELETE FROM captura_actual")
        for _, f in df_editado.iterrows():
            if pd.notna(f["nombre"]): c.execute("INSERT INTO captura_actual VALUES (?,?,?)", (str(f["nombre"]).upper(), str(f["fecha_cad"]), int(f["cantidad"])))
        conn.commit()
        st.success("✅ Cambios guardados")

# ------------------------------------------------------------
# TAB 2: INVENTARIO Y CORTE (CON SUMA DE TARJETAS)
# ------------------------------------------------------------
with tab2:
    st.header("💳 Finanzas del Día")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        t_credito = st.number_input("Crédito $", min_value=0.0, step=1.0, format="%.2f")
    with col_t2:
        t_debito = st.number_input("Débito $", min_value=0.0, step=1.0, format="%.2f")
    
    total_tarjetas = t_credito + t_debito
    st.subheader(f"Total Tarjetas: ${total_tarjetas:,.2f}")
    if st.button("Confirmar Montos", use_container_width=True):
        st.success(f"✅ Montos confirmados: ${total_tarjetas:,.2f}")

    st.divider()
    st.header("📦 Stock Actual")
    df_stock = pd.read_sql("SELECT nombre, fecha_cad, cantidad FROM base_anterior", conn)
    
    if not df_stock.empty:
        fechas = sorted(df_stock['fecha_cad'].unique())
        filtro = st.multiselect("Filtrar Caducidad:", fechas, default=fechas)
        df_stock_filt = df_stock[df_stock['fecha_cad'].isin(filtro)]
        st.dataframe(df_stock_filt, use_container_width=True)

        # REPORTE WA UNIFICADO
        msg = f"🥐 *REPORTE CHAMPLITTE*\n\n💳 *FINANZAS:*\n- Crédito: ${t_credito}\n- Débito: ${t_debito}\n- *Total Tarjetas: ${total_tarjetas}*\n\n📦 *INVENTARIO:*\n"
        for _, r in df_stock_filt.iterrows(): msg += f"• {r['nombre']} ({r['fecha_cad']}): {r['cantidad']} pza\n"
        
        st.link_button("📲 Enviar Reporte a WhatsApp", f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(msg)}", use_container_width=True, type="primary")

    st.divider()
    if st.button("🚀 PROCESAR CORTE AHORA", use_container_width=True):
        df_act = pd.read_sql("SELECT * FROM captura_actual", conn)
        if df_act.empty: st.warning("⚠️ Sin conteo")
        else:
            ts = datetime.now(zona_mx).strftime("%Y-%m-%d %H:%M:%S")
            # Lógica de comparación simplificada para el ejemplo
            c.execute("DELETE FROM base_anterior")
            c.execute("INSERT INTO base_anterior SELECT * FROM captura_actual")
            c.execute("DELETE FROM captura_actual")
            conn.commit()
            st.balloons(); st.success("✅ Corte realizado"); time.sleep(1); st.rerun()

# ------------------------------------------------------------
# TAB 3: ANÁLISIS
# ------------------------------------------------------------
with tab3:
    df_hist = pd.read_sql("SELECT * FROM historial_ventas", conn)
    if df_hist.empty: st.info("Sin historial")
    else:
        st.dataframe(df_hist, use_container_width=True)
        st.line_chart(df_hist.groupby("fecha_corte")["vendidos"].sum())

# ------------------------------------------------------------
# TAB 4: CALCULADORA (DISEÑO INTEGRADO)
# ------------------------------------------------------------
with tab4:
    st.header("🧮 Calculadora de Venta")
    if "calc_val" not in st.session_state: st.session_state.calc_val = ""

    # Pantalla de la calculadora
    st.code(st.session_state.calc_val if st.session_state.calc_val else "0", language="text")

    def calc_press(char):
        if char == "=":
            try: st.session_state.calc_val = str(eval(st.session_state.calc_val))
            except: st.session_state.calc_val = "Error"
        elif char == "C": st.session_state.calc_val = ""
        else: st.session_state.calc_val += str(char)
        sonido_click()

    # Grid de botones
    cols = st.columns(4)
    botones = ["7","8","9","/", "4","5","6","*", "1","2","3","-", "C","0","=","+"]
    
    for i, b in enumerate(botones):
        with cols[i % 4]:
            if st.button(b, key=f"btn_{b}_{i}", use_container_width=True):
                calc_press(b)
                st.rerun()
    
    st.divider()
    st.success("✅ Calculadora lista para operaciones rápidas")
