import streamlit as st

# Configuración de la página para que se vea más limpia
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

# CSS para ocultar menú de arriba, iconos de código y pie de página de Streamlit
st.markdown("""
    <style>
    /* Ocultar barra superior y menú de Streamlit */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .stApp { background-color: #121212; color: white; }
    
    /* Botones verde claro estables */
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
    }

    /* Sombreado negro en los campos de dinero */
    input { 
        background-color: #000000 !important; 
        color: #ffffff !important; 
        border: 1px solid #444 !important;
    }
    
    /* Estilo para el pie de página personalizado */
    .footer-text {
        text-align: left;
        color: #666;
        font-size: 0.8rem;
        margin-top: 30px;
    }

    [data-testid="stMetricValue"] {
        color: #90ee90 !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Corte de Caja")

# Inicializar ventas
if 'ventas' not in st.session_state:
    st.session_state.ventas = {
        "Efectivo": [], 
        "Retiros": [], 
        "Transferencia Liga": [], 
        "Tarjeta Débito": [], 
        "Tarjeta Crédito": [], 
        "Uber": [], 
        "Didi": [], 
        "Rappi": []
    }

# Función para añadir y limpiar el campo automáticamente
def guardar_y_limpiar(categoria):
    key = f"input_{categoria}"
    monto = st.session_state[key]
    if monto is not None and monto > 0:
        st.session_state.ventas[categoria].append(monto)
        st.session_state[key] = None 

suma_santander = 0

# Interfaz de usuario
for cat, montos in st.session_state.ventas.items():
    subtotal = sum(montos)
    with st.expander(f"📊 {cat} - Subtotal: ${subtotal:.2f}", expanded=True):
        
        st.number_input(
            f"Ingresar cantidad:", 
            min_value=0.0, 
            step=0.01, 
            value=None, 
            placeholder="0.00",
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
    
    # Suma solo Efectivo y Retiros para la Ficha Santander
    if cat in ["Efectivo", "Retiros"]:
        suma_santander += subtotal

st.markdown("---")

# Métrica final
st.metric(label="Total Ficha Santander del turno", value=f"${suma_santander:.2f}")

st.markdown("---")

if st.button("LIMPIAR", key="reset_all"):
    for cat in st.session_state.ventas:
        st.session_state.ventas[cat] = []
    st.rerun()

# Pie de página oficial
st.markdown('<p class="footer-text">v1.0 - Herramienta Interna Champlitte</p>', unsafe_allow_html=True)
