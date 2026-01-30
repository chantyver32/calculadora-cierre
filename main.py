import streamlit as st

# Configuración de estilo Champlitte
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    
    .stButton>button { 
        width: 100%; border-radius: 8px; height: auto; 
        padding: 10px; background-color: #90ee90 !important; 
        color: #121212 !important; font-weight: bold;
        border: none; display: block; white-space: normal;
    }
    
    .stButton>button:hover, .stButton>button:active, .stButton>button:focus {
        background-color: #90ee90 !important;
        color: #121212 !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #90ee90 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Cierre de Ventas - Champlitte")

# Inicializar ventas con el nuevo orden: Efectivo seguido de Retiros
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], 
        "Retiros": [], 
        "Transferencia Liga": [], 
        "Tarjeta Débito": [], 
        "Tarjeta Crédito": [], 
        "Anticipos": [], 
        "Pedido Liberado": [], 
        "Uber": [], 
        "Didi": [], 
        "Rappi": []
    }

def guardar_y_limpiar(categoria):
    key = f"input_{categoria}"
    monto = st.session_state[key]
    if monto is not None and monto > 0:
        st.session_state.ventas[categoria].append(monto)
        st.session_state[key] = None 

total_general = 0
suma_santander = 0

for cat, montos in st.session_state.ventas.items():
    subtotal = sum(montos)
    with st.expander(f"📊 {cat} - Subtotal: ${subtotal:.2f}", expanded=True):
        
        st.number_input(
            f"Ingresar cantidad para {cat}:", 
            min_value=0.0, 
            step=0.01, 
            value=None, 
            placeholder="Escribe aquí...",
            key=f"input_{cat}"
        )
        
        st.button(
            f"Añadir a {cat}", 
            key=f"btn_{cat}", 
            on_click=guardar_y_limpiar, 
            args=(cat,)
        )

        for i, m in enumerate(montos):
            col1, col2 = st.columns([4, 1])
            col1.write(f"Pago {i+1}: **${m:.2f}**")
            if col2.button("🗑️", key=f"del_{cat}_{i}"):
                st.session_state.ventas[cat].pop(i)
                st.rerun()
    
    # Sumatoria para el total de la Ficha Santander (Solo Efectivo y Retiros)
    if cat in ["Efectivo", "Retiros"]:
        suma_santander += subtotal
        
    total_general += subtotal

st.markdown("---")

# Métricas finales
col_a, col_b = st.columns(2)
with col_a:
    st.metric(label="Total Ficha Santander del turno", value=f"${suma_santander:.2f}")
with col_b:
    st.metric(label="TOTAL GENERAL (Todas las fuentes)", value=f"${total_general:.2f}")

st.markdown("---")

if st.button("🔴 REINICIAR TODO EL CIERRE", key="reset_all"):
    for cat in st.session_state.ventas:
        st.session_state.ventas[cat] = []
    st.rerun()
