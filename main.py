import streamlit as st

# Configuración de estilo Champlitte (Modo Oscuro con Verde Claro)
st.markdown("""
    <style>
    .stApp { background-color: #121212; color: white; }
    
    /* Estilo de los botones */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: auto; 
        padding-top: 10px;
        padding-bottom: 10px;
        background-color: #90ee90; /* Verde claro */
        color: #121212 !important; /* Texto oscuro para contraste */
        font-weight: bold;
        border: none;
        display: block;
        white-space: normal; /* Evita que el texto se oculte o corte */
        word-wrap: break-word;
    }
    
    .stButton>button:hover {
        background-color: #77dd77; /* Verde un poco más oscuro al pasar el mouse */
        color: #000000 !important;
    }

    /* Estilo de los inputs */
    input { color: white !important; }
    
    /* Estilo de las métricas */
    [data-testid="stMetricValue"] {
        color: #90ee90 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Cierre de Ventas - Champlitte")

# Inicializar el estado de la aplicación
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], "Transferencia Liga": [], "Tarjeta Débito": [], 
        "Tarjeta Crédito": [], "Anticipos": [], "Pedido Liberado": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }

total_general = 0

# Generar interfaz por categoría
for cat, montos in st.session_state.ventas.items():
    with st.expander(f"📊 {cat} - Subtotal: ${sum(montos):.2f}", expanded=True):
        
        nuevo_monto = st.number_input(
            f"Ingresar monto:", 
            min_value=0.0, 
            step=0.01, 
            value=None, 
            placeholder="0.00",
            key=f"input_{cat}"
        )
        
        # Botón con texto multilínea si es necesario
        if st.button(f"Añadir a {cat}", key=f"btn_{cat}"):
            if nuevo_monto is not None and nuevo_monto > 0:
                st.session_state.ventas[cat].append(nuevo_monto)
                st.rerun()

        # Listado de montos con borrado individual
        for i, m in enumerate(montos):
            col1, col2 = st.columns([4, 1])
            col1.write(f"Pago {i+1}: **${m:.2f}**")
            if col2.button("🗑️", key=f"del_{cat}_{i}"):
                st.session_state.ventas[cat].pop(i)
                st.rerun()
    
    total_general += sum(montos)

st.markdown("---")
st.metric(label="TOTAL FINAL DEL DÍA", value=f"${total_general:.2f}")

# Botón de reset general con un color distinto para precaución
if st.button("🔴 REINICIAR TODO EL CIERRE", key="reset_all"):
    for cat in st.session_state.ventas:
        st.session_state.ventas[cat] = []
    st.rerun()
