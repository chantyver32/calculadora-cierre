import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# CSS optimizado para reducir espacios y mejorar estética
st.markdown("""
    <style>
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    .stApp { background-color: #121212; color: white; }
    
    /* Reducción de espacio superior */
    .block-container { padding-top: 2rem; }

    /* Botones verde claro */
    .stButton>button { 
        width: 100%; border-radius: 8px; height: auto; 
        padding: 5px; background-color: #90ee90 !important; 
        color: #121212 !important; font-weight: bold;
        border: none; display: block;
    }
    
    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }

    [data-testid="stMetricValue"] {
        color: #90ee90 !important;
        font-size: 2.5rem;
    }
    
    .footer-text { text-align: center; color: #666; font-size: 0.7rem; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 1. Inicializar sesión
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], "Retiros": [], "Transferencia Liga": [], 
        "Tarjeta Débito": [], "Tarjeta Crédito": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }

def guardar_y_limpiar(categoria):
    key = f"input_{categoria}"
    monto = st.session_state[key]
    if monto is not None and monto > 0:
        st.session_state.ventas[categoria].append(monto)
        st.session_state[key] = None 

# 2. Cálculos Previos
suma_santander = sum(st.session_state.ventas["Efectivo"]) + sum(st.session_state.ventas["Retiros"])
total_general = sum(sum(m) for m in st.session_state.ventas.values())

# 3. Encabezado y Métrica Principal (AL PRINCIPIO)
st.title("💰 Corte de Caja")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric(label="Ficha Santander", value=f"${suma_santander:.2f}")
with col_m2:
    st.metric(label="Venta Total", value=f"${total_general:.2f}")

st.markdown("---")

# 4. Interfaz de Entrada (Organizada en 2 columnas para reducir espacio)
categorias = list(st.session_state.ventas.keys())
cols = st.columns(2) # Divide la pantalla en dos columnas

for idx, cat in enumerate(categorias):
    # Alternar entre columna 1 y 2
    with cols[idx % 2]:
        subtotal = sum(st.session_state.ventas[cat])
        with st.expander(f"{cat}: ${subtotal:.1f}", expanded=False):
            st.number_input(
                f"Monto {cat}:", 
                min_value=0.0, step=0.01, value=None, 
                placeholder="0.00", key=f"input_{cat}"
            )
            st.button(f"Añadir", key=f"btn_{cat}", on_click=guardar_y_limpiar, args=(cat,))
            
            # Lista de pagos realizados
            for i, m in enumerate(st.session_state.ventas[cat]):
                c1, c2 = st.columns([3, 1])
                c1.caption(f"${m:.2f}")
                if c2.button("🗑️", key=f"del_{cat}_{i}"):
                    st.session_state.ventas[cat].pop(i)
                    st.rerun()

st.markdown("---")

# 5. Botón de Reinicio
if st.button("LIMPIAR TODO EL TURNO", key="reset_all"):
    for cat in st.session_state.ventas:
        st.session_state.ventas[cat] = []
    st.rerun()

st.markdown('<p class="footer-text">v1.1 - Champlitte Compact Mode</p>', unsafe_allow_html=True)
