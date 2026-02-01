import streamlit as st
import os

# --- 1. INSTALACIÓN AUTOMÁTICA DE LIBRERÍAS ---
try:
    from streamlit_cookies_manager import EncryptedCookieManager
except ImportError:
    os.system("pip install streamlit-cookies-manager")
    from streamlit_cookies_manager import EncryptedCookieManager

# --- 2. CONFIGURACIÓN DE COOKIES (PERSISTENCIA) ---
# Esta es la "memoria" que se queda en tu celular
cookies = EncryptedCookieManager(password="champlitte_clave_segura_123")

if not cookies.ready():
    st.stop()

# --- 3. CONFIGURACIÓN DE PÁGINA Y ESTILOS ---
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    /* Botones verdes */
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #90ee90 !important; 
        color: #121212 !important; font-weight: bold; border: none;
    }
    
    /* Campos de entrada negros */
    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }

    [data-testid="stMetricValue"] { color: #90ee90 !important; }
    .footer-text { color: #666; font-size: 0.8rem; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. INICIALIZACIÓN DE DATOS ---
if "ventas" not in cookies:
    cookies["ventas"] = {
        "Efectivo": [], "Retiros": [], "Transferencia Liga": [], 
        "Tarjeta Débito": [], "Tarjeta Crédito": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }
    cookies.save()

# Traemos los datos de la cookie a una variable de trabajo
datos_ventas = cookies["ventas"]

def guardar_en_celular():
    cookies["ventas"] = datos_ventas
    cookies.save()

# --- 5. INTERFAZ ---
st.title("💰 Corte de Caja")

suma_santander = 0

for cat in datos_ventas.keys():
    montos = datos_ventas[cat]
    subtotal = sum(montos)
    
    if cat in ["Efectivo", "Retiros"]:
        suma_santander += subtotal

    with st.expander(f"📊 {cat} - Subtotal: ${subtotal:.2f}", expanded=False):
        # Campo para ingresar dinero
        nuevo_monto = st.number_input(
            f"Cantidad:", 
            min_value=0.0, step=0.01, value=None, 
            placeholder="0.00", key=f"in_{cat}"
        )
        
        if st.button(f"Añadir a {cat}", key=f"btn_{cat}"):
            if nuevo_monto and nuevo_monto > 0:
                datos_ventas[cat].append(nuevo_monto)
                guardar_en_celular()
                st.rerun()

        # Mostrar lista de pagos guardados
        for i, m in enumerate(montos):
            col1, col2 = st.columns([4, 1])
            col1.write(f"Pago {i+1}: **${m:.2f}**")
            if col2.button("🗑️", key=f"del_{cat}_{i}"):
                datos_ventas[cat].pop(i)
                guardar_en_celular()
                st.rerun()

st.markdown("---")
st.metric(label="Total Ficha Santander", value=f"${suma_santander:.2f}")
st.markdown("---")

# Botón para resetear todo el día
if st.button("LIMPIAR TURNO COMPLETO"):
    for c in datos_ventas:
        datos_ventas[c] = []
    guardar_en_celular()
    st.rerun()

st.markdown('<p class="footer-text">v1.2 - Persistencia Celular Activa</p>', unsafe_allow_html=True)
