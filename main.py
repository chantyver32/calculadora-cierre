import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# Zona horaria CDMX
zona_mx = pytz.timezone('America/Mexico_City')

# --- BASE DE DATOS (Para que no se borre al refrescar) ---
conn = sqlite3.connect('corte_champlitte.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, monto REAL, hora TEXT)''')
conn.commit()

# CSS: Diseño Oscuro Pro
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    input { 
        background-color: #000000 !important; 
        color: #90ee90 !important; 
        font-size: 2.2rem !important;
        text-align: center !important;
        border: 2px solid #444 !important;
        border-radius: 15px !important;
    }

    .stButton>button { 
        width: 100%; border-radius: 12px; padding: 18px;
        background-color: #1e1e1e !important; color: white !important;
        font-size: 1.1rem !important; border: 1px solid #333 !important;
        margin-bottom: 5px;
    }
    
    .stButton>button:hover { border-color: #90ee90 !important; background-color: #262626 !important; }
    [data-testid="stMetricValue"] { color: #90ee90 !important; font-size: 2.5rem !important; }
    .footer-text { color: #666; font-size: 0.8rem; margin-top: 30px; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# Categorías solicitadas
categorias = {
    "💳 Tarjeta Débito": "Tarjeta Débito",
    "💳 Tarjeta Crédito": "Tarjeta Crédito",
    "🚗 Uber": "Uber",
    "🛵 Didi": "Didi",
    "📦 Rappi": "Rappi",
    "🔗 Transf. Liga": "Transferencia Liga"
}

# ------------------ FUNCIONES DE LÓGICA ------------------
def registrar_pago(cat_key):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora_cdmx = datetime.now(zona_mx).strftime("%H:%M:%S")
        # Guardar en Base de Datos
        c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?, ?, ?)", 
                  (cat_key, monto, hora_cdmx))
        conn.commit()
        # Reiniciar campo
        st.session_state.monto_actual = None
        st.toast(f"✅ Guardado ${monto:.2f} en {cat_key}")
    else:
        st.error("⚠️ Ingresa un monto válido")

def borrar_ultimo(cat_key):
    c.execute("DELETE FROM ventas WHERE id = (SELECT MAX(id) FROM ventas WHERE categoria = ?)", (cat_key,))
    conn.commit()

def reiniciar_todo():
    c.execute("DELETE FROM ventas")
    conn.commit()

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["📝 REGISTRO", "📊 RESUMEN INDIVIDUAL"])

with tab1:
    st.title("💰 Corte Champlitte")
    
    st.number_input("Monto a registrar:", min_value=0.0, step=0.01, value=None, 
                    format="%.2f", key="monto_actual", placeholder="0.00")

    st.write("### Clasificar pago:")
    
    for label, key in categorias.items():
        st.button(label, key=f"btn_{key}", on_click=registrar_pago, args=(key,), use_container_width=True)

with tab2:
    st.header("📊 Detalle del Turno")
    
    # Consultar datos actuales
    datos = c.execute("SELECT id, categoria, monto, hora FROM ventas").fetchall()
    
    if not datos:
        st.info("No hay registros todavía.")
    else:
        total_turno = sum(d[2] for d in datos)
        st.metric("Venta Total Registrada", f"${total_turno:.2f}")
        st.divider()

        for label, key in categorias.items():
            pagos_cat = [d for d in datos if d[1] == key]
            subtotal = sum(p[2] for p in pagos_cat)
            
            if pagos_cat:
                with st.expander(f"{label} - Total: ${subtotal:.2f}"):
                    for p in pagos_cat:
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"Registro ({p[3]})")
                        c2.write(f"**${p[2]:.2f}**")
                    
                    st.button(f"Deshacer último {key}", key=f"undo_{key}", on_click=borrar_ultimo, args=(key,))

        st.divider()

        # --- ENVÍO A WHATSAPP CORREGIDO ---
        fecha_cdmx = datetime.now(zona_mx).strftime("%d/%m/%Y")
        mensaje = f"💰 *CORTE CHAMPLITTE* ({fecha_cdmx})\n\n"
        for label, key in categorias.items():
            total_cat = sum(d[2] for d in datos if d[1] == key)
            if total_cat > 0:
                mensaje += f"• *{key}:* ${total_cat:.2f}\n"
        mensaje += f"\n📈 *TOTAL:* ${total_turno:.2f}"
        
        # Número y Link corregido
        numero_wa = "522283530069" # Formato internacional correcto
        url_wa = f"https://wa.me/{numero_wa}?text={urllib.parse.quote(mensaje)}"
        
        st.link_button("📲 ENVIAR REPORTE A WHATSAPP", url_wa, use_container_width=True, type="primary")

        # --- REINICIAR ---
        if st.button("🚨 REINICIAR TURNO", use_container_width=True):
            reiniciar_todo()
            st.rerun()

st.markdown('<p class="footer-text">v2.3 - Champlitte CDMX (Base de Datos)</p>', unsafe_allow_html=True)
