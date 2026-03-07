import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# Zona horaria CDMX
zona_mx = pytz.timezone('America/Mexico_City')

# --- BASE DE DATOS ---
conn = sqlite3.connect('corte_champlitte.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, monto REAL, hora TEXT)''')
conn.commit()

# CSS: Diseño Oscuro Pro y Ajuste de Botones
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    input { 
        background-color: #000000 !important; 
        color: #90ee90 !important; 
        font-size: 2rem !important;
        text-align: center !important;
        border: 2px solid #444 !important;
        border-radius: 15px !important;
    }

    /* Botones más pequeños para 2 columnas */
    .stButton>button { 
        width: 100%; border-radius: 10px; padding: 12px;
        background-color: #1e1e1e !important; color: white !important;
        font-size: 0.9rem !important; border: 1px solid #333 !important;
        margin-bottom: 2px;
    }
    
    .stButton>button:hover { border-color: #90ee90 !important; background-color: #262626 !important; }
    .footer-text { color: #666; font-size: 0.8rem; margin-top: 30px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# Categorías en el orden solicitado
categorias = {
    "💳 T. Débito": "Tarjeta Débito",
    "💳 T. Crédito": "Tarjeta Crédito",
    "🚗 Uber": "Uber",
    "🛵 Didi": "Didi",
    "📦 Rappi": "Rappi",
    "🔗 Transf. Liga": "Transferencia Liga"
}

# ------------------ FUNCIONES ------------------
def registrar_pago(cat_key):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora_cdmx = datetime.now(zona_mx).strftime("%H:%M:%S")
        c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?, ?, ?)", 
                  (cat_key, monto, hora_cdmx))
        conn.commit()
        st.session_state.monto_actual = None
        st.toast(f"✅ {cat_key} ${monto:.2f}")
    else:
        st.error("⚠️ Monto inválido")

def borrar_ultimo(cat_key):
    c.execute("DELETE FROM ventas WHERE id = (SELECT MAX(id) FROM ventas WHERE categoria = ?)", (cat_key,))
    conn.commit()

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["📝 REGISTRO", "📊 RESUMEN"])

with tab1:
    st.title("💰 Corte Champlitte")
    
    st.number_input("Monto:", min_value=0.0, step=0.01, value=None, 
                    format="%.2f", key="monto_actual", placeholder="0.00")

    st.write("### Clasificar:")
    
    # GRILLA DE 2 COLUMNAS
    cols = st.columns(2)
    for i, (label, key) in enumerate(categorias.items()):
        with cols[i % 2]:
            st.button(label, key=f"btn_{key}", on_click=registrar_pago, args=(key,))

with tab2:
    st.header("📊 Resumen")
    datos = c.execute("SELECT id, categoria, monto, hora FROM ventas").fetchall()
    
    if not datos:
        st.info("Sin registros.")
    else:
        # Desglose individual (Sin total general)
        for label, key in categorias.items():
            pagos_cat = [d for d in datos if d[1] == key]
            subtotal = sum(p[2] for p in pagos_cat)
            
            if pagos_cat:
                with st.expander(f"{label}: ${subtotal:.2f}"):
                    for p in pagos_cat:
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"Hora: {p[3]}")
                        c2.write(f"**${p[2]:.2f}**")
                    st.button(f"Deshacer {key}", key=f"undo_{key}", on_click=borrar_ultimo, args=(key,))

        st.divider()

        # WhatsApp (Solo desglose)
        fecha_cdmx = datetime.now(zona_mx).strftime("%d/%m/%Y")
        mensaje = f"💰 *CORTE CHAMPLITTE* ({fecha_cdmx})\n\n"
        hay_datos = False
        for label, key in categorias.items():
            total_cat = sum(d[2] for d in datos if d[1] == key)
            if total_cat > 0:
                mensaje += f"• *{key}:* ${total_cat:.2f}\n"
                hay_datos = True
        
        if hay_datos:
            num_wa = "522283530069" 
            url_wa = f"https://wa.me/{num_wa}?text={urllib.parse.quote(mensaje)}"
            st.link_button("📲 ENVIAR REPORTE", url_wa, use_container_width=True, type="primary")

        if st.button("🚨 REINICIAR TURNO", use_container_width=True):
            c.execute("DELETE FROM ventas")
            conn.commit()
            st.rerun()

st.markdown('<p class="footer-text">v2.4 - Champlitte CDMX</p>', unsafe_allow_html=True)
