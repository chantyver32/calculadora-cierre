import streamlit as st

# Configuración de estilo Champlitte
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    
    .stButton>button { 
        width: 100%; border-radius: 8px; height: auto; 
        padding: 10px; background-color: #90ee90; 
        color: #121212 !important; font-weight: bold;
        border: none; display: block; white-space: normal;
    }
    
    /* Fondo negro en los campos de dinero */
    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }
    
    /* Color verde para el Total */
    [data-testid="stMetricValue"] {
        color: #90ee90 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Cierre de Ventas - Champlitte")

# Inicializar ventas
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], "Transferencia Liga": [], "Tarjeta Débito": [], 
        "Tarjeta Crédito": [], "Anticipos": [], "Pedido Liberado": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }

# Función para añadir y limpiar el campo automáticamente
def guardar_y_limpiar(categoria):
    key = f"input_{categoria}"
    monto = st.session_state[key]
    if monto is not None and monto > 0:
        st.session_state.ventas[categoria].append(monto)
        st.session_state[key] = None 

total_general = 0

# Interfaz por categoría
for cat, montos in st.session_state.ventas.items():
    with st.expander(f"📊 {cat} - Subtotal: ${sum(montos):.2f}", expanded=True):
        
        # Campo de entrada vinculado al session_state
        st.number_input(
            f"Ingresar cantidad para {cat}:", 
            min_value=0.0, 
            step=0.01, 
            value=None, 
            placeholder="Escribe aquí...",
            key=f"input_{cat}"
        )
        
        # Botón con la lógica de guardado corregida
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
    
    total_general += sum(montos)

st.markdown("---")
st.metric(label="TOTAL FINAL DEL DÍA", value=f"${total_general:.2f}")

# Botón de reset general
if st.button("🔴 REINICIAR TODO EL CIERRE", key="reset_all"):
    for cat in st.session_state.ventas:
        st.session_state.ventas[cat] = []
    st.rerun()
