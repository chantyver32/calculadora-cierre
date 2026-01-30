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
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Cierre de Ventas - Champlitte")

# Inicializar ventas y un rastreador de limpieza
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], "Transferencia Liga": [], "Tarjeta Débito": [], 
        "Tarjeta Crédito": [], "Anticipos": [], "Pedido Liberado": [], 
        "Uber": [], "Didi": [], "Rappi": []
    }

total_general = 0

# Función para añadir y limpiar el campo automáticamente
def guardar_y_limpiar(categoria):
    key = f"input_{categoria}"
    monto = st.session_state[key]
    if monto is not None and monto > 0:
        st.session_state.ventas[categoria].append(monto)
        # Esta es la clave: reseteamos el valor en el session_state
        st.session_state[key] = None 

# Interfaz
for cat, montos in st.session_state.ventas.items():
    with st.expander(f"📊 {cat} - Subtotal: ${sum(montos):.2f}", expanded=True):
        
        # El campo ahora está vinculado directamente al session_state
        st.number_input(
            f"Ingresar cantidad:", 
            min_value=0.0, 
            step=0.01, 
            value=None, 
            placeholder="Escribe aquí...",
            key=f"input_{cat}",
            on_change=None # El cambio se procesa al picar el botón
        )
        
        # Al pulsar el botón, se ejecuta la lógica de guardado y limpieza
        if st.button(
