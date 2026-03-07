import streamlit as st
import urllib.parse
from datetime import datetime

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# CSS: Diseño Oscuro, Botones Verdes e Inputs Negros
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    /* Input principal gigante */
    input { 
        background-color: #000000 !important; 
        color: #90ee90 !important; 
        font-size: 2rem !important;
        text-align: center !important;
        border: 2px solid #444 !important;
    }

    /* Botones de categorías (Iconos) */
    .stButton>button { 
        width: 100%; border-radius: 12px; padding: 15px;
        background-color: #1e1e1e !important; color: white !important;
        font-size: 1.2rem !important; border: 1px solid #333 !important;
    }
    
    /* Botón de Confirmar y Enviar (Verde) */
    div[data-testid="stFormSubmitButton"] > button, .btn-confirm {
        background-color: #90ee90 !important;
        color: #121212 !important;
        font-weight: bold !important;
    }

    .footer-text { color: #666; font-size: 0.8rem; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# ------------------ ESTADO DE SESIÓN ------------------
if 'ventas' not in st.session_state:
    st.session_state.ventas = []

# Categorías con sus iconos
categorias = {
    "💵 Efectivo": "Efectivo",
    "🏧 Retiro": "Retiros",
    "🔗 Transf. Liga": "Transferencia Liga",
    "💳 T. Débito": "Tarjeta Débito",
    "💳 T. Crédito": "Tarjeta Crédito",
    "🚗 Uber": "Uber",
    "🛵 Didi": "Didi",
    "📦 Rappi": "Rappi"
}

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["📝 Registro Rápido", "📊 Resumen y Envío"])

with tab1:
    st.title("💰 Corte de Caja")
    
    # CAMPO ÚNICO DE ENTRADA
    monto_input = st.number_input("Monto a registrar:", min_value=0.0, step=0.01, value=0.0, format="%.2f")

    st.write("Selecciona el tipo de pago:")
    
    # GRILLA DE ICONOS (Botones rápidos)
    cols = st.columns(2)
    for i, (label, key) in enumerate(categorias.items()):
        with cols[i % 2]:
            if st.button(label, use_container_width=True):
                if monto_input > 0:
                    # GUARDAR EN EL HISTORIAL TEMPORAL
                    st.session_state.ventas.append({
                        "categoria": key,
                        "monto": monto_input,
                        "hora": datetime.now().strftime("%H:%M")
                    })
                    st.success(f"✅ Añadido: ${monto_input:.2f} a {key}")
                    st.rerun() # Refresca para limpiar el campo si se desea o marcar éxito
                else:
                    st.warning("Introduce un monto mayor a 0")

with tab2:
    st.header("📊 Resumen del Turno")
    
    if not st.session_state.ventas:
        st.info("No hay registros todavía.")
    else:
        # Procesar datos para el resumen
        df_resumen = {}
        for item in st.session_state.ventas:
            cat = item["categoria"]
            df_resumen[cat] = df_resumen.get(cat, 0) + item["monto"]
        
        # Calcular Ficha Santander
        efectivo = df_resumen.get("Efectivo", 0)
        retiros = df_resumen.get("Retiros", 0)
        ficha_santander = efectivo - retiros
        
        # Mostrar totales
        for cat, total in df_resumen.items():
            st.write(f"**{cat}:** ${total:.2f}")
            
        st.divider()
        st.metric("Total Ficha Santander", f"${ficha_santander:.2f}")

        # --- ENVÍO A WHATSAPP ---
        if st.button("📲 ENVIAR A WHATSAPP", use_container_width=True, type="primary"):
            mensaje = "💰 *CORTE CHAMPLITTE*\n\n"
            for cat, total in df_resumen.items():
                mensaje += f"• *{cat}:* ${total:.2f}\n"
            mensaje += f"\n🏦 *Ficha Santander:* ${ficha_santander:.2f}"
            
            num = "522283530069"
            url = f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)

        # --- BOTÓN PARA BORRAR TODO ---
        if st.button("🗑️ LIMPIAR TODO", use_container_width=True):
            st.session_state.ventas = []
            st.rerun()

st.markdown('<p class="footer-text">v2.0 - Champlitte Registro Rápido</p>', unsafe_allow_html=True)
