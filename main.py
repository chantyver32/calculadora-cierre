import streamlit as st
import urllib.parse
from datetime import datetime

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# CSS: Diseño Oscuro Pro
st.markdown("""
    <style>
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stApp { background-color: #121212; color: white; }
    
    /* Input gigante y limpio */
    input { 
        background-color: #000000 !important; 
        color: #90ee90 !important; 
        font-size: 2.2rem !important;
        text-align: center !important;
        border: 2px solid #444 !important;
        border-radius: 15px !important;
    }

    /* Botones de categorías */
    .stButton>button { 
        width: 100%; border-radius: 12px; padding: 18px;
        background-color: #1e1e1e !important; color: white !important;
        font-size: 1.1rem !important; border: 1px solid #333 !important;
        margin-bottom: 5px;
    }
    
    /* Hover de botones */
    .stButton>button:hover { border-color: #90ee90 !important; background-color: #262626 !important; }

    /* Estilo de métricas */
    [data-testid="stMetricValue"] { color: #90ee90 !important; font-size: 2.5rem !important; }
    
    .footer-text { color: #666; font-size: 0.8rem; margin-top: 30px; text-align: center; }
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

# ------------------ FUNCIONES DE LOGICA ------------------
def registrar_pago(cat_key):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        st.session_state.ventas.append({
            "categoria": cat_key,
            "monto": monto,
            "hora": datetime.now().strftime("%H:%M:%S")
        })
        # REINICIO A CERO/VACÍO:
        st.session_state.monto_actual = None
        st.toast(f"✅ Registrado ${monto:.2f} en {cat_key}")
    else:
        st.error("⚠️ Ingresa un monto válido")

# ------------------ TABS ------------------
tab1, tab2 = st.tabs(["📝 REGISTRO", "📊 RESUMEN INDIVIDUAL"])

with tab1:
    st.title("💰 Corte Champlitte")
    
    # CAMPO ÚNICO: Inicia vacío (value=None) para escribir rápido
    st.number_input("Monto a registrar:", min_value=0.0, step=0.01, value=None, 
                    format="%.2f", key="monto_actual", placeholder="0.00")

    st.write("### Clasificar pago:")
    
    # GRILLA DE BOTONES
    cols = st.columns(2)
    for i, (label, key) in enumerate(categorias.items()):
        with cols[i % 2]:
            st.button(label, key=f"btn_{key}", on_click=registrar_pago, args=(key,), use_container_width=True)

with tab2:
    st.header("📊 Detalle del Turno")
    
    if not st.session_state.ventas:
        st.info("No hay registros todavía.")
    else:
        # Cálculos de Totales
        totales_por_cat = {}
        for v in st.session_state.ventas:
            cat = v["categoria"]
            totales_por_cat[cat] = totales_por_cat.get(cat, 0) + v["monto"]
        
        # Ficha Santander
        ficha_s = totales_por_cat.get("Efectivo", 0) - totales_por_cat.get("Retiros", 0)
        
        st.metric("Total Ficha Santander", f"${ficha_s:.2f}")
        st.divider()

        # DESPLIEGUE INDIVIDUAL POR CATEGORÍA
        for label, key in categorias.items():
            pagos_cat = [v for v in st.session_state.ventas if v["categoria"] == key]
            subtotal = sum(p["monto"] for p in pagos_cat)
            
            if pagos_cat:
                with st.expander(f"{label} - Total: ${subtotal:.2f}"):
                    for i, p in enumerate(pagos_cat):
                        c1, c2 = st.columns([3, 1])
                        c1.write(f"Pago {i+1} ({p['hora']})")
                        c2.write(f"**${p['monto']:.2f}**")
                    
                    # Opción para borrar el último de esta categoría si hubo error
                    if st.button(f"Deshacer último {key}", key=f"undo_{key}"):
                        # Buscar el índice del último registro de esta categoría y eliminarlo
                        for idx in reversed(range(len(st.session_state.ventas))):
                            if st.session_state.ventas[idx]["categoria"] == key:
                                st.session_state.ventas.pop(idx)
                                st.rerun()

        st.divider()

        # --- ENVÍO A WHATSAPP ---
        if st.button("📲 ENVIAR REPORTE FINAL", use_container_width=True, type="primary"):
            mensaje = "💰 *CORTE CHAMPLITTE*\n\n"
            for label, key in categorias.items():
                total_cat = sum(v["monto"] for v in st.session_state.ventas if v["categoria"] == key)
                if total_cat > 0:
                    mensaje += f"• *{key}:* ${total_cat:.2f}\n"
            mensaje += f"\n🏦 *Ficha Santander:* ${ficha_s:.2f}"
            
            num = "522283530069"
            url = f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={url}">', unsafe_allow_html=True)

        # --- BORRAR TODO ---
        if st.button("🚨 REINICIAR TODO EL TURNO", use_container_width=True):
            st.session_state.ventas = []
            st.rerun()

st.markdown('<p class="footer-text">v2.1 - Champlitte Registro Rápido</p>', unsafe_allow_html=True)
