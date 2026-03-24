import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3
import pandas as pd

# ------------------ CONFIGURACIÓN ------------------

st.set_page_config(page_title="Corte Champlitte", layout="centered")

zona_mx = pytz.timezone("America/Mexico_City")

# ------------------ BASE DE DATOS ------------------

conn = sqlite3.connect("corte_champlitte.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS ventas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
categoria TEXT,
monto REAL,
hora TEXT)
""")
conn.commit()

# ------------------ CSS ------------------

st.markdown("""
<style>
header {visibility:hidden;}
footer {visibility:hidden;}
.stApp{ background:#121212; color:white; }
input{
    background:#000!important; color:#90ee90!important;
    font-size:2rem!important; text-align:center!important;
    border-radius:12px!important; border:2px solid #444!important;
}
.stButton>button{
    width:100%; border-radius:10px; padding:16px;
    background:#1e1e1e!important; color:white!important;
    font-size:0.9rem!important; border:1px solid #333!important;
}
.stButton>button:hover{ border-color:#90ee90!important; background:#262626!important; }
.confirm{
    background:#1e1e1e; padding:15px; border-radius:10px;
    border-left:5px solid #90ee90; margin-top:15px;
}
.total-card{
    background:#1b1b1b; padding:20px; border-radius:14px;
    border-left:5px solid #90ee90; margin-bottom:20px; text-align:center;
}
.total-card h1{ font-size:2.5rem; margin:0; color:#90ee90; }
</style>
""", unsafe_allow_html=True)

# ------------------ ORDEN Y CATEGORÍAS ------------------

ORDEN_CATEGORIAS = [
    "Tarjeta Débito", 
    "Tarjeta Crédito", 
    "Uber", 
    "Didi", 
    "Rappi", 
    "Transferencia Liga"
]

labels_botones = [
    ("💳 T. Débito", "Tarjeta Débito"),
    ("💳 T. Crédito", "Tarjeta Crédito"),
    ("🚗 Uber", "Uber"),
    ("🛵 Didi", "Didi"),
    ("📦 Rappi", "Rappi"),
    ("🔗 Transf. Liga", "Transferencia Liga")
]

# ------------------ LOGICA ------------------

# --- VARIABLES DE SESIÓN PARA LA CALCULADORA ---
if "calc_base_cre" not in st.session_state: st.session_state.calc_base_cre = 0.0
if "calc_base_deb" not in st.session_state: st.session_state.calc_base_deb = 0.0
if "calc_resta_cre" not in st.session_state: st.session_state.calc_resta_cre = 0.0
if "calc_resta_deb" not in st.session_state: st.session_state.calc_resta_deb = 0.0
# Nuevo: Historial de movimientos de la calculadora
if "calc_historial" not in st.session_state: st.session_state.calc_historial = []

def op_calc(tipo, accion):
    monto = st.session_state.monto_calculadora
    if monto and monto > 0:
        # Lógica de sumas
        if tipo == "cre" and accion == "base": st.session_state.calc_base_cre += monto
        if tipo == "deb" and accion == "base": st.session_state.calc_base_deb += monto
        if tipo == "cre" and accion == "resta": st.session_state.calc_resta_cre += monto
        if tipo == "deb" and accion == "resta": st.session_state.calc_resta_deb += monto
        
        # Lógica de registro para el historial
        tipo_str = "Crédito" if tipo == "cre" else "Débito"
        accion_str = "Suma a Base" if accion == "base" else "Resta"
        simbolo = "+" if accion == "base" else "-"
        
        st.session_state.calc_historial.append({
            "Tarjeta": tipo_str,
            "Operación": accion_str,
            "Monto": f"{simbolo} ${monto:.2f}"
        })
        
        st.session_state.monto_calculadora = None

def limpiar_calc():
    st.session_state.calc_base_cre = 0.0
    st.session_state.calc_base_deb = 0.0
    st.session_state.calc_resta_cre = 0.0
    st.session_state.calc_resta_deb = 0.0
    st.session_state.calc_historial = [] # Limpiar historial
# -------------------------------------------------------

def registrar_pago(cat):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora = datetime.now(zona_mx).strftime("%H:%M:%S")
        c.execute("INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)", (cat,monto,hora))
        conn.commit()
        st.session_state.confirmacion = f"""
        <div class="confirm">
        ✅ <b>{cat}:</b> ${monto:.2f} | 🕒 {hora}
        </div>
        """
        st.session_state.monto_actual = None

# ------------------ INTERFAZ (TABS) ------------------

tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 RESUMEN", "🧮 CALCULADORA"])

with tab1:
    st.number_input("Monto", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_actual", placeholder="0.00")
    
    for i in range(0, len(labels_botones), 2):
        col1, col2 = st.columns(2)
        with col1:
            label, key = labels_botones[i]
            st.button(label, on_click=registrar_pago, args=(key,), key=f"btn_{i}")
        with col2:
            if i+1 < len(labels_botones):
                label, key = labels_botones[i+1]
                st.button(label, on_click=registrar_pago, args=(key,), key=f"btn_{i+1}")

    if "confirmacion" in st.session_state:
        st.markdown(st.session_state.confirmacion, unsafe_allow_html=True)

with tab2:
    datos = c.execute("SELECT categoria, monto, hora FROM ventas").fetchall()
    
    if not datos:
        st.info("Sin registros")
    else:
        df = pd.DataFrame(datos, columns=["categoria", "monto", "hora"])
        
        st.write("### Movimientos")
        edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")

        c1, c2 = st.columns(2)
        if c1.button("💾 Guardar", use_container_width=True):
            c.execute("DELETE FROM ventas")
            for _, row in edited_df.iterrows():
                c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?,?,?)", 
                         (row["categoria"], row["monto"], row["hora"]))
            conn.commit()
            st.rerun()
        if c2.button("🗑️ Borrar Todo", use_container_width=True):
            c.execute("DELETE FROM ventas")
            conn.commit()
            st.rerun()

        st.divider()

        st.write("### Totales por Categoría")
        
        mensaje = f"💰 *CORTE CHAMPLITTE* ({datetime.now(zona_mx).strftime('%d/%m/%Y')})\n\n"
        total_general = 0

        for cat in ORDEN_CATEGORIAS:
            monto_cat = edited_df[edited_df["categoria"] == cat]["monto"].sum()
            if monto_cat > 0:
                st.write(f"**{cat}:** ${monto_cat:.2f}")
                mensaje += f"• *{cat}:* ${monto_cat:.2f}\n"
                total_general += monto_cat
        
        t_deb = edited_df[edited_df["categoria"] == "Tarjeta Débito"]["monto"].sum()
        t_cre = edited_df[edited_df["categoria"] == "Tarjeta Crédito"]["monto"].sum()
        
        st.markdown(f"""
        <div class="total-card">
        <p>💳 TOTAL TARJETAS</p>
        <h1>${(t_deb + t_cre):.2f}</h1>
        </div>
        """, unsafe_allow_html=True)

        url_wa = f"https://wa.me/522283530069?text={urllib.parse.quote(mensaje)}"
        st.link_button("📲 ENVIAR REPORTE", url_wa, use_container_width=True)

# --- TAB: CALCULADORA ---
with tab3:
    st.write("### Calculadora de Tarjetas")
    st.number_input("Monto a ingresar", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_calculadora", placeholder="0.00")
    
    st.write("**1. Sumar Monto Base**")
    c1, c2 = st.columns(2)
    c1.button("➕ Base T. Crédito", on_click=op_calc, args=("cre", "base"), key="btn_base_cre")
    c2.button("➕ Base T. Débito", on_click=op_calc, args=("deb", "base"), key="btn_base_deb")

    st.write("**2. Restar Cantidades**")
    c3, c4 = st.columns(2)
    c3.button("➖ Restar a T. Crédito", on_click=op_calc, args=("cre", "resta"), key="btn_resta_cre")
    c4.button("➖ Restar a T. Débito", on_click=op_calc, args=("deb", "resta"), key="btn_resta_deb")

    st.divider()
    
    # --- NUEVO: TABLA DE DETALLES ---
    st.write("### Detalle de Movimientos")
    if st.session_state.calc_historial:
        df_calc = pd.DataFrame(st.session_state.calc_historial)
        st.dataframe(df_calc, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay movimientos en la calculadora.")
        
    st.divider()
    
    st.write("### Resultados Finales")
    
    res_cre = st.session_state.calc_base_cre - st.session_state.calc_resta_cre
    res_deb = st.session_state.calc_base_deb - st.session_state.calc_resta_deb
    
    st.markdown(f"""
    <div class="confirm" style="border-left:5px solid #ffcc00;">
        <p style="margin:0; font-size:14px; color:#aaa;">💳 T. CRÉDITO (Base: ${st.session_state.calc_base_cre:.2f} | Restado: ${st.session_state.calc_resta_cre:.2f})</p>
        <h2 style="margin:0; color:#ffcc00;">${res_cre:.2f}</h2>
    </div>
    <div class="confirm" style="border-left:5px solid #00ccff;">
        <p style="margin:0; font-size:14px; color:#aaa;">💳 T. DÉBITO (Base: ${st.session_state.calc_base_deb:.2f} | Restado: ${st.session_state.calc_resta_deb:.2f})</p>
        <h2 style="margin:0; color:#00ccff;">${res_deb:.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    st.button("🧹 Limpiar Calculadora", on_click=limpiar_calc)
