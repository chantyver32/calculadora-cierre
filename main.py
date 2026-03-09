import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3
import time

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Sistema Champlitte", layout="centered")

# Zona horaria CDMX
zona_mx = pytz.timezone('America/Mexico_City')
numero_whatsapp = "522283530069"

# --- BASE DE DATOS ---
conn = sqlite3.connect('corte_champlitte.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, monto REAL, hora TEXT)''')
conn.commit()

# --- ESTILO CSS (Interfaz Oscura / Botones Grandes) ---
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    /* Input gigante */
    input { 
        background-color: #000000 !important; 
        color: #90ee90 !important; 
        font-size: 2.2rem !important;
        text-align: center !important;
        border: 2px solid #444 !important;
        border-radius: 15px !important;
    }

    /* Botones de categorías y calculadora */
    .stButton>button { 
        width: 100%; border-radius: 12px; padding: 20px 10px;
        background-color: #1e1e1e !important; color: white !important;
        font-size: 1rem !important; border: 1px solid #333 !important;
        font-weight: bold;
    }
    
    .stButton>button:hover { border-color: #90ee90 !important; background-color: #262626 !important; }
    
    /* Estilo especial para el resultado de la calculadora */
    .calc-display {
        background-color: #000;
        color: #ff9f0a;
        padding: 15px;
        font-size: 2.5rem;
        text-align: right;
        border-radius: 10px;
        border: 1px solid #444;
        margin-bottom: 10px;
        font-family: monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# Categorías
categorias = [
    ("💳 T. Débito", "Tarjeta Débito"),
    ("💳 T. Crédito", "Tarjeta Crédito"),
    ("🚗 Uber", "Uber"),
    ("🛵 Didi", "Didi"),
    ("📦 Rappi", "Rappi"),
    ("🔗 Transf. Liga", "Transferencia Liga")
]

# ------------------ FUNCIONES ------------------
def registrar_pago(cat_key):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora_cdmx = datetime.now(zona_mx).strftime("%H:%M:%S")
        c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?, ?, ?)", (cat_key, monto, hora_cdmx))
        conn.commit()
        st.session_state.monto_actual = None
        st.success(f"✅ {cat_key} guardado")
        time.sleep(0.5)
    else:
        st.error("⚠️ Ingrese un monto")

def calculadora_func(tecla):
    if "calc_val" not in st.session_state: st.session_state.calc_val = ""
    
    if tecla == "=":
        try:
            # Evaluar la expresión matemática
            res = eval(st.session_state.calc_val.replace('x', '*').replace('÷', '/'))
            st.session_state.calc_val = str(res)
        except:
            st.session_state.calc_val = "Error"
    elif tecla == "C":
        st.session_state.calc_val = ""
    else:
        st.session_state.calc_val += str(tecla)

# ------------------ TABS ------------------
tab1, tab2, tab3 = st.tabs(["📝 REGISTRO", "📊 CORTE TARJETAS", "🧮 CALCULADORA"])

# TAB 1: REGISTRO DE VENTAS
with tab1:
    st.title("💰 Cierre Champlitte")
    st.number_input("Monto:", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_actual", placeholder="0.00")

    st.write("### Clasificar:")
    for i in range(0, len(categorias), 2):
        col1, col2 = st.columns(2)
        with col1:
            label, key = categorias[i]
            st.button(label, key=f"btn_{key}", on_click=registrar_pago, args=(key,))
        with col2:
            if i + 1 < len(categorias):
                label, key = categorias[i+1]
                st.button(label, key=f"btn_{key}", on_click=registrar_pago, args=(key,))

# TAB 2: RESUMEN Y ENVÍO WA
with tab2:
    st.header("📊 Resumen de Tarjetas")
    datos = c.execute("SELECT categoria, monto FROM ventas").fetchall()
    
    # Calcular sumas
    debito = sum(d[1] for d in datos if d[0] == "Tarjeta Débito")
    credito = sum(d[1] for d in datos if d[0] == "Tarjeta Crédito")
    total_tarjetas = debito + credito
    
    # Mostrar resultados estilo "Card"
    st.markdown(f"""
        <div style="background-color:#1e1e1e; padding:20px; border-radius:15px; border-left: 5px solid #90ee90;">
            <p style="margin:0; font-size:1.2rem;">Total Tarjetas</p>
            <h1 style="margin:0; color:#90ee90;">${total_tarjetas:.2f}</h1>
            <hr>
            <p style="margin:0;">💳 Débito: ${debito:.2f}</p>
            <p style="margin:0;">💳 Crédito: ${credito:.2f}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()

    # WhatsApp Reporte
    fecha_cdmx = datetime.now(zona_mx).strftime("%d/%m/%Y")
    txt_wa = f"🥐 *CORTE CHAMPLITTE* ({fecha_cdmx})\n\n"
    txt_wa += f"💳 *TOTAL TARJETAS:* ${total_tarjetas:.2f}\n"
    txt_wa += f"   • Débito: ${debito:.2f}\n"
    txt_wa += f"   • Crédito: ${credito:.2f}\n\n"
    
    # Agregar otras categorías si tienen monto
    for label, key in categorias[2:]: # Uber, Didi, etc
        total_cat = sum(d[1] for d in datos if d[0] == key)
        if total_cat > 0:
            txt_wa += f"• *{key}:* ${total_cat:.2f}\n"

    url_wa = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(txt_wa)}"
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.link_button("📲 ENVIAR A WA", url_wa, use_container_width=True, type="primary")
    with col_b:
        if st.button("🚨 BORRAR TODO"):
            c.execute("DELETE FROM ventas")
            conn.commit()
            st.rerun()

# TAB 3: CALCULADORA BÁSICA
with tab3:
    if "calc_val" not in st.session_state: st.session_state.calc_val = ""
    
    st.markdown(f'<div class="calc-display">{st.session_state.calc_val if st.session_state.calc_val else "0"}</div>', unsafe_allow_html=True)
    
    # Grilla de la calculadora
    botones_calc = [
        ['7', '8', '9', '/'],
        ['4', '5', '6', 'x'],
        ['1', '2', '3', '-'],
        ['C', '0', '=', '+']
    ]
    
    for fila in botones_calc:
        cols = st.columns(4)
        for i, tecla in enumerate(fila):
            with cols[i]:
                if st.button(tecla, key=f"calc_{tecla}"):
                    calculadora_func(tecla)
                    st.rerun()

st.markdown('<p style="color:#444; text-align:center; margin-top:50px;">Champlitte Pro v3.0</p>', unsafe_allow_html=True)
