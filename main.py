import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import urllib.parse

# ------------------ CONFIGURACIÓN DE PÁGINA ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# --- CSS MEJORADO (Basado en tu diseño oscuro) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    /* Botones verde claro tipo Champlitte */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: auto; 
        padding: 12px; background-color: #90ee90 !important; 
        color: #121212 !important; font-weight: bold;
        border: none; font-size: 16px;
    }

    /* Inputs negros con texto blanco */
    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
        font-size: 18px !important;
    }

    /* Estilo de métricas */
    [data-testid="stMetricValue"] { color: #90ee90 !important; font-size: 32px; }
    [data-testid="stMetricLabel"] { color: #aaaaaa !important; }

    /* Compactar espacios */
    .block-container {padding-top: 1rem;}
    div.stExpander { border: 1px solid #333; background-color: #1e1e1e; border-radius: 10px; margin-bottom: 10px;}
    </style>
    """, unsafe_allow_html=True)

# ------------------ BASE DE DATOS (Persistencia) ------------------
conn = sqlite3.connect('corte_caja.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, monto REAL, fecha TEXT)''')
conn.commit()

# ------------------ LÓGICA DE FUNCIONES ------------------
def agregar_monto(categoria):
    key = f"input_{categoria}"
    monto = st.session_state.get(key)
    if monto and monto > 0:
        fecha_act = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO ventas (categoria, monto, fecha) VALUES (?, ?, ?)", (categoria, monto, fecha_act))
        conn.commit()
        st.session_state[key] = 0.0 # Resetear input

def eliminar_pago(id_pago):
    c.execute("DELETE FROM ventas WHERE id = ?", (id_pago,))
    conn.commit()

def reset_total():
    c.execute("DELETE FROM ventas")
    conn.commit()

# ------------------ INTERFAZ DE USUARIO ------------------
st.title("💰 Corte de Caja")

categorias = ["Efectivo", "Retiros", "Transferencia Liga", "Tarjeta Débito", 
              "Tarjeta Crédito", "Uber", "Didi", "Rappi"]

suma_santander = 0
total_general = 0

# Iterar por categorías
for cat in categorias:
    # Obtener datos de la BD para esta categoría
    df_cat = pd.read_sql(f"SELECT id, monto FROM ventas WHERE categoria = '{cat}'", conn)
    subtotal = df_cat['monto'].sum()
    
    # Calcular suma para Ficha Santander (Efectivo - Retiros)
    if cat == "Efectivo": suma_santander += subtotal
    if cat == "Retiros": suma_santander -= subtotal # Los retiros restan al efectivo físico
    
    total_general += subtotal

    with st.expander(f"📊 {cat.upper()} - ${subtotal:.2f}", expanded=(subtotal > 0)):
        col_inp, col_btn = st.columns([2, 1])
        
        with col_inp:
            st.number_input("Cantidad:", min_value=0.0, step=0.01, key=f"input_{cat}", format="%.2f")
        
        with col_btn:
            st.write("##") # Espaciador
            st.button("AÑADIR", key=f"btn_{cat}", on_click=agregar_monto, args=(cat,))

        # Mostrar lista de pagos individuales
        if not df_cat.empty:
            st.markdown("---")
            for _, fila in df_cat.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"💵 ${fila['monto']:.2f}")
                if c2.button("🗑️", key=f"del_{fila['id']}"):
                    eliminar_pago(fila['id'])
                    st.rerun()

# ------------------ RESUMEN FINAL ------------------
st.markdown("---")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Ficha Santander (Efectivo)", value=f"${suma_santander:.2f}")
with col_m2:
    st.metric(label="Total Venta Turno", value=f"${total_general:.2f}")

# --- BOTONES DE ACCIÓN ---
st.markdown("---")
col_wa, col_res = st.columns(2)

# Lógica de Reporte WhatsApp
with col_wa:
    if st.button("📲 ENVIAR REPORTE"):
        resumen_msg = "💰 *CORTE DE CAJA CHAMPLITTE*\n\n"
        for cat in categorias:
            sub = pd.read_sql(f"SELECT SUM(monto) FROM ventas WHERE categoria = '{cat}'", conn).iloc[0,0] or 0
            if sub > 0: resumen_msg += f"• *{cat}:* ${sub:.2f}\n"
        resumen_msg += f"\n🏦 *Ficha Santander:* ${suma_santander:.2f}"
        resumen_msg += f"\n📈 *Total General:* ${total_general:.2f}"
        
        # Reemplaza con tu número
        numero = "522283530069"
        link = f"https://wa.me/{numero}?text={urllib.parse.quote(resumen_msg)}"
        st.markdown(f'<meta http-equiv="refresh" content="0;URL={link}">', unsafe_allow_html=True)

with col_res:
    if st.button("🗑️ LIMPIAR TODO", type="secondary"):
        reset_total()
        st.rerun()

st.markdown('<p style="color: #666; font-size: 0.8rem;">v1.1 - Champlitte Internal System</p>', unsafe_allow_html=True)
