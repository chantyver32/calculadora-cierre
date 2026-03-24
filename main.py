import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3
import pandas as pd
import time

# ------------------ CONFIGURACIÓN ------------------

st.set_page_config(page_title="Corte Champlitte", layout="centered", page_icon="🥐")

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

# ------------------ CSS MEJORADO ------------------

st.markdown("""
<style>
header {visibility:hidden;}
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

# ------------------ SIDEBAR (CORREGIDO) ------------------

st.sidebar.title("⚙️ Panel de Control")

opciones_wa = {
    "Contacto Principal": "522283530069",
    "Contacto Secundario": "522299359597"
}
seleccion_wa = st.sidebar.selectbox("📱 Enviar Reporte a:", list(opciones_wa.keys()))
numero_whatsapp = opciones_wa[seleccion_wa]

st.sidebar.divider()

# Herramienta de Restauración
with st.sidebar.expander("📂 Restaurar Respaldo"):
    archivo_csv = st.file_uploader("Subir archivo .csv", type=["csv"])
    if archivo_csv and st.button("Restaurar Datos Ahora"):
        try:
            df_restaurar = pd.read_csv(archivo_csv)
            c.execute("DELETE FROM ventas")
            for _, fila in df_restaurar.iterrows():
                c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?, ?, ?)", 
                          (str(fila['categoria']), float(fila['monto']), str(fila['hora'])))
            conn.commit()
            st.success("✅ Restaurado")
            time.sleep(1)
            st.rerun()
        except:
            st.error("Error en formato")

# Reset Total
with st.sidebar.expander("🚨 Borrado Total"):
    if st.button("Confirmar Limpieza de Base"):
        c.execute("DELETE FROM ventas")
        conn.commit()
        st.rerun()

# ------------------ LÓGICA ------------------

ORDEN_CATEGORIAS = ["Tarjeta Débito", "Tarjeta Crédito", "Uber", "Didi", "Rappi", "Transferencia Liga"]

labels_botones = [
    ("💳 T. Débito", "Tarjeta Débito"), ("💳 T. Crédito", "Tarjeta Crédito"),
    ("🚗 Uber", "Uber"), ("🛵 Didi", "Didi"),
    ("📦 Rappi", "Rappi"), ("🔗 Transf. Liga", "Transferencia Liga")
]

def registrar_pago(cat):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora = datetime.now(zona_mx).strftime("%H:%M:%S")
        c.execute("INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)", (cat,monto,hora))
        conn.commit()
        st.session_state.confirmacion = f"✅ {cat}: ${monto:.2f}"
        st.session_state.monto_actual = None

# ------------------ INTERFAZ (TABS) ------------------

tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 RESUMEN", "🧮 CALCULADORA"])

# --- TAB 1: REGISTRO (SIN TABLAS NI CSV) ---
with tab1:
    st.number_input("Monto de Venta", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_actual", placeholder="0.00")
    
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
        st.info(st.session_state.confirmacion)

# --- TAB 2: RESUMEN ---
with tab2:
    datos = c.execute("SELECT categoria, monto, hora FROM ventas").fetchall()
    if not datos:
        st.info("No hay ventas registradas hoy.")
    else:
        df = pd.DataFrame(datos, columns=["categoria", "monto", "hora"])
        
        st.write("### 📂 Listado de Movimientos")
        # Tabla solo para visualización y edición rápida de errores
        edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic")

        if st.button("💾 Guardar Cambios en Lista", use_container_width=True):
            c.execute("DELETE FROM ventas")
            for _, row in edited_df.iterrows():
                if pd.notna(row["categoria"]):
                    c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?,?,?)", 
                             (row["categoria"], row["monto"], row["hora"]))
            conn.commit()
            st.rerun()
            
        st.divider()

        # Cálculo de Totales
        mensaje_wa = f"💰 *CORTE CHAMPLITTE* ({datetime.now(zona_mx).strftime('%d/%m/%Y')})\n\n"
        total_acumulado = 0

        for cat in ORDEN_CATEGORIAS:
            monto_cat = edited_df[edited_df["categoria"] == cat]["monto"].sum()
            if monto_cat > 0:
                st.write(f"**{cat}:** ${monto_cat:.2f}")
                mensaje_wa += f"• *{cat}:* ${monto_cat:.2f}\n"
                total_acumulado += monto_cat
        
        t_deb = edited_df[edited_df["categoria"] == "Tarjeta Débito"]["monto"].sum()
        t_cre = edited_df[edited_df["categoria"] == "Tarjeta Crédito"]["monto"].sum()
        
        st.markdown(f"""
        <div class="total-card">
        <p>💳 TOTAL TARJETAS (D+C)</p>
        <h1>${(t_deb + t_cre):.2f}</h1>
        </div>
        """, unsafe_allow_html=True)

        url_wa = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje_wa)}"
        st.link_button("📲 ENVIAR CORTE AL WHATSAPP", url_wa, use_container_width=True)

# --- TAB 3: CALCULADORA ---
with tab3:
    if "calc_historial" not in st.session_state: st.session_state.calc_historial = []

    st.write("### Desglose de Tarjetas")
    monto_c = st.number_input("Monto para calcular", min_value=0.0, step=0.01, value=None, key="monto_calc", placeholder="0.00")
    
    c1, c2 = st.columns(2)
    if c1.button("➕ Base Crédito"):
        if monto_c: st.session_state.calc_historial.append({"Tarjeta": "Crédito", "Op": "Base", "Monto": monto_c})
    if c2.button("➕ Base Débito"):
        if monto_c: st.session_state.calc_historial.append({"Tarjeta": "Débito", "Op": "Base", "Monto": monto_c})

    c3, c4 = st.columns(2)
    if c3.button("➖ Restar Crédito"):
        if monto_c: st.session_state.calc_historial.append({"Tarjeta": "Crédito", "Op": "Resta", "Monto": monto_c})
    if c4.button("➖ Restar Débito"):
        if monto_c: st.session_state.calc_historial.append({"Tarjeta": "Débito", "Op": "Resta", "Monto": monto_c})

    if st.session_state.calc_historial:
        df_calc = pd.DataFrame(st.session_state.calc_historial)
        
        # Totales rápidos
        res_cre = df_calc[(df_calc["Tarjeta"]=="Crédito") & (df_calc["Op"]=="Base")]["Monto"].sum() - \
                  df_calc[(df_calc["Tarjeta"]=="Crédito") & (df_calc["Op"]=="Resta")]["Monto"].sum()
        
        res_deb = df_calc[(df_calc["Tarjeta"]=="Débito") & (df_calc["Op"]=="Base")]["Monto"].sum() - \
                  df_calc[(df_calc["Tarjeta"]=="Débito") & (df_calc["Op"]=="Resta")]["Monto"].sum()

        st.markdown(f"""
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; border-left:5px solid #ffcc00; margin-bottom:10px;">
            <small>RESULTADO CRÉDITO</small><br><b>${res_cre:.2f}</b>
        </div>
        <div style="background:#1e1e1e; padding:15px; border-radius:10px; border-left:5px solid #00ccff;">
            <small>RESULTADO DÉBITO</small><br><b>${res_deb:.2f}</b>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🧹 Limpiar Calculadora"):
            st.session_state.calc_historial = []
            st.rerun()
