import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

# --- CONFIGURACIÓN DE COOKIES ---
# Importante: La contraseña debe tener al menos 16 caracteres para ser segura
cookies = EncryptedCookieManager(password="champlitte_clave_maestra_2026_segura")

if not cookies.ready():
    # Mientras la cookie carga, mostramos un mensaje amigable
    st.info("Cargando memoria del dispositivo...")
    st.stop()

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# Estilos CSS
st.markdown("""
    <style>
    header, footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    .stButton>button { 
        width: 100%; border-radius: 8px; background-color: #90ee90 !important; 
        color: #121212 !important; font-weight: bold; border: none;
    }
    input { background-color: #000000 !important; color: #ffffff !important; border: 1px solid #444 !important; }
    [data-testid="stMetricValue"] { color: #90ee90 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE DATOS ---
# Si es la primera vez que abres la app, creamos la estructura
if "ventas_v2" not in cookies:
    cookies["ventas_v2"] = {
        "Efectivo": [], "Retiros": [], "Transferencia Liga": [], 
        "Tarjeta Débito": [], "Tarjeta Crédito": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }
    cookies.save()

# Variable de trabajo vinculada a la cookie
datos_ventas = cookies["ventas_v2"]

# --- INTERFAZ ---
st.title("💰 Corte de Caja")

suma_santander = 0

for cat in list(datos_ventas.keys()):
    montos = datos_ventas[cat]
    subtotal = sum(montos)
    
    if cat in ["Efectivo", "Retiros"]:
        suma_santander += subtotal

    with st.expander(f"📊 {cat} - Subtotal: ${subtotal:.2f}"):
        nuevo_monto = st.number_input(f"Cantidad:", min_value=0.0, step=0.01, key=f"in_{cat}")
        
        if st.button(f"Añadir a {cat}", key=f"btn_{cat}"):
            if nuevo_monto > 0:
                datos_ventas[cat].append(nuevo_monto)
                cookies["ventas_v2"] = datos_ventas # Actualizamos la cookie
                cookies.save()
                st.rerun()

        for i, m in enumerate(montos):
            c1, c2 = st.columns([4, 1])
            c1.write(f"Pago {i+1}: **${m:.2f}**")
            if c2.button("🗑️", key=f"del_{cat}_{i}"):
                datos_ventas[cat].pop(i)
                cookies["ventas_v2"] = datos_ventas
                cookies.save()
                st.rerun()

st.markdown("---")
st.metric(label="Total Ficha Santander", value=f"${suma_santander:.2f}")

if st.button("LIMPIAR TURNO COMPLETO"):
    cookies["ventas_v2"] = {c: [] for c in datos_ventas}
    cookies.save()
    st.rerun()
