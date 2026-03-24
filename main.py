import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3
import pandas as pd
import time

# ------------------ CONFIGURACIÓN ------------------

st.set_page_config(page_title="Corte Champlitte", layout="centered", page_icon="🥐")

zona_mx = pytz.timezone("America/Mexico_City")

# ------------------ BASE DE DATOS ------------------

conn = sqlite3.connect("corte_champlitte.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS ventas (
id INTEGER PRIMARY KEY AUTOINCREMENT,
categoria TEXT,
monto REAL,
hora TEXT)
""")
conn.commit()

# ------------------ CSS ------------------

st.markdown("""
<style>
/* Header visible para que en celular aparezca el botón del menú lateral (sidebar) */
footer {visibility:hidden;}
.stApp { background:#121212; color:white; }

/* Input numérico gigante (solo aplica a la caja de monto, evita dañar el desplegable) */
div[data-testid="stNumberInput"] input {
    background:#000!important; color:#90ee90!important;
    font-size:2rem!important; text-align:center!important;
    border-radius:12px!important; border:2px solid #444!important;
}

/* FIX: Asegurar que el desplegable y sus opciones sean oscuros y visibles */
div[data-baseweb="select"] > div {
    background-color: #1e1e1e !important;
    color: white !important;
    border: 1px solid #444 !important;
}
div[data-baseweb="popover"], ul[data-baseweb="menu"] {
    background-color: #1e1e1e !important;
}
li[role="option"] {
    color: white !important;
}

/* Diseño general de botones y tarjetas */
.stButton>button{
    width:100%; border-radius:10px; padding:16px;
    background:#1e1e1e!important; color:white!important;
    font-size:0.9rem!important; border:1px solid #333!important;
}
.stButton>button:hover{ border-color:#90ee90!important; background:#262626!important; }
.confirm{
    background:#1e1e1e; padding:15px; border-radius:10px;
    border-left:5px solid #90ee90; margin-top:15px;
}
.total-card{
    background:#1b1b1b; padding:20px; border-radius:14px;
    border-left:5px solid #90ee90; margin-bottom:20px; text-align:center;
}
.total-card h1{ font-size:2.5rem; margin:0; color:#90ee90; }
</style>
""", unsafe_allow_html=True)

# ------------------ ORDEN Y CATEGORÍAS ------------------

ORDEN_CATEGORIAS = [
    "Crédito", 
    "Débito", 
    "Uber", 
    "Didi", 
    "Rappi", 
    "Transferencia Liga"
]

# ------------------ LÓGICA DE VARIABLES ------------------

if "calc_historial" not in st.session_state: st.session_state.calc_historial = []

def op_calc(tipo, accion):
    monto = st.session_state.monto_calculadora
    if monto and monto > 0:
        tipo_str = "Crédito" if tipo == "cre" else "Débito"
        accion_str = "Suma" if accion == "base" else "Resta"
        
        st.session_state.calc_historial.append({
            "Tarjeta": tipo_str,
            "Operación": accion_str,
            "Monto": float(monto)
        })
        
        # Guardar confirmación verde para la calculadora
        st.session_state.confirmacion_calc = f"""
        <div class="confirm">
        ✅ <b>{tipo_str} ({accion_str}):</b> ${monto:.2f}
        </div>
        """
        
        st.session_state.monto_calculadora = None

def limpiar_calc():
    st.session_state.calc_historial = [] 
    if "confirmacion_calc" in st.session_state:
        del st.session_state["confirmacion_calc"]

def registrar_pago(cat):
    monto = st.session_state.monto_actual
    if monto and monto > 0:
        hora = datetime.now(zona_mx).strftime("%H:%M:%S")
        c.execute("INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)", (cat,monto,hora))
        conn.commit()
        st.session_state.confirmacion = f"""
        <div class="confirm">
        ✅ <b>{cat}:</b> ${monto:.2f} | 🕒 {hora}
        </div>
        """
        st.session_state.monto_actual = None


# ------------------ SIDEBAR (MENÚ LATERAL) ------------------

st.sidebar.header("⚙️ Configuración")

# Lista desplegable para números de WhatsApp
opciones_wa = {
    "Contacto Principal": "522283530069",
    "Contacto Secundario": "522299359597",
    "Contacto 3": "520987654321" 
}
seleccion_wa = st.sidebar.selectbox("📱 Selecciona el WhatsApp destino", list(opciones_wa.keys()))
numero_whatsapp = opciones_wa[seleccion_wa]

st.sidebar.divider()

# Espacio para adjuntar CSV y restaurar datos
st.sidebar.subheader("💾 Respaldo de Base de Datos")
st.sidebar.info("Sube tu archivo CSV de respaldo para restaurar los movimientos de ventas.")
archivo_csv = st.sidebar.file_uploader("⬆️ Subir Respaldo CSV", type=["csv"])

if archivo_csv is not None:
    if st.sidebar.button("🔄 Cargar y Restaurar Ventas", use_container_width=True):
        try:
            df_restaurar = pd.read_csv(archivo_csv)
            c.execute("DELETE FROM ventas")
            for _, fila in df_restaurar.iterrows():
                c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?, ?, ?)", 
                          (str(fila['categoria']), float(fila['monto']), str(fila['hora'])))
            conn.commit()
            st.sidebar.success("✅ Base de datos restaurada correctamente")
            time.sleep(1.5)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"⚠️ Error al restaurar: {e}")

st.sidebar.divider()

with st.sidebar.expander("🚨 Zona de Peligro"):
    confirmar_reset = st.checkbox("Confirmar que deseo borrar todo", key="check_reset")
    if st.button("⚠️ EJECUTAR RESET TOTAL", use_container_width=True):
        if confirmar_reset:
            c.execute("DELETE FROM ventas")
            conn.commit()
            st.session_state.calc_historial = []
            st.sidebar.success("✅ Base de datos limpiada por completo")
            time.sleep(1)
            st.rerun()
        else:
            st.sidebar.error("Debes confirmar primero")


# ------------------ INTERFAZ (TABS) ------------------

tab1, tab2, tab3, tab4 = st.tabs(["📝 REGISTRO", "📊 RESUMEN", "🧮 CALCULADORA", "📈 RESULTADOS"])

# --- TAB 1: REGISTRO ---
with tab1:
    st.number_input("Monto", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_actual", placeholder="0.00")
    
    with st.expander("💳 Tarjetas y Transferencia", expanded=True):
        # Crédito y Débito en la primera fila
        col1, col2 = st.columns(2)
        with col1:
            st.button("💳 Crédito", on_click=registrar_pago, args=("Crédito",), key="btn_cre")
        with col2:
            st.button("💵 Débito", on_click=registrar_pago, args=("Débito",), key="btn_deb")
        
        # Transferencia Liga abarcando todo el ancho abajo de los dos anteriores
        st.button("🔗 Transferencia Liga", on_click=registrar_pago, args=("Transferencia Liga",), key="btn_transf")

    with st.expander("🛵 Plataformas Delivery", expanded=False):
        col3, col4 = st.columns(2)
        with col3:
            st.button("🚗 Uber", on_click=registrar_pago, args=("Uber",), key="btn_uber")
            st.button("📦 Rappi", on_click=registrar_pago, args=("Rappi",), key="btn_rappi")
        with col4:
            st.button("🛵 Didi", on_click=registrar_pago, args=("Didi",), key="btn_didi")

    if "confirmacion" in st.session_state:
        st.markdown(st.session_state.confirmacion, unsafe_allow_html=True)


# --- TAB 2: RESUMEN ---
with tab2:
    datos = c.execute("SELECT categoria, monto, hora FROM ventas").fetchall()
    
    if not datos:
        st.info("Sin registros")
    else:
        df = pd.DataFrame(datos, columns=["categoria", "monto", "hora"])
        
        # --- DESPLEGABLE EN RESUMEN ---
        with st.expander("📂 Ver y Editar Todos los Movimientos"):
            edited_df = st.data_editor(df, use_container_width=True, hide_index=True, num_rows="dynamic", key="editor_tab2")

            c1, c2 = st.columns(2)
            if c1.button("💾 Guardar Cambios", use_container_width=True):
                c.execute("DELETE FROM ventas")
                for _, row in edited_df.iterrows():
                    if pd.notna(row["categoria"]): # Evita guardar filas vacías
                        c.execute("INSERT INTO ventas (categoria, monto, hora) VALUES (?,?,?)", 
                                 (row["categoria"], row["monto"], row["hora"]))
                conn.commit()
                st.success("Cambios guardados.")
                time.sleep(1)
                st.rerun()
                
            if c2.button("🗑️ Borrar Todo", use_container_width=True):
                c.execute("DELETE FROM ventas")
                conn.commit()
                st.rerun()

        st.divider()

        st.write("### Totales por Categoría")
        
        mensaje = f"💰 *CORTE CHAMPLITTE* ({datetime.now(zona_mx).strftime('%d/%m/%Y')})\n\n"
        total_general = 0

        for cat in ORDEN_CATEGORIAS:
            monto_cat = edited_df[edited_df["categoria"] == cat]["monto"].sum()
            if monto_cat > 0:
                st.write(f"**{cat}:** ${monto_cat:.2f}")
                mensaje += f"• *{cat}:* ${monto_cat:.2f}\n"
                total_general += monto_cat
        
        t_deb = edited_df[edited_df["categoria"] == "Débito"]["monto"].sum()
        t_cre = edited_df[edited_df["categoria"] == "Crédito"]["monto"].sum()
        
        st.markdown(f"""
        <div class="total-card">
        <p>"🏦 TOTAL TARJETAS"</p>
        <h1>${(t_deb + t_cre):.2f}</h1>
        </div>
        """, unsafe_allow_html=True)

        # Botón para enviar EL RESUMEN TOTAL por WhatsApp
        url_wa_resumen = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje)}"
        st.link_button("📲 Enviar al WhatsApp", url_wa_resumen, use_container_width=True)


# --- TAB 3: CALCULADORA ---
with tab3:
    st.number_input("Monto a ingresar", min_value=0.0, step=0.01, value=None, format="%.2f", key="monto_calculadora", placeholder="0.00")
    
    with st.expander("➕ Suma (Ingresos)", expanded=True):
        c1, c2 = st.columns(2)
        c1.button("➕ Crédito", on_click=op_calc, args=("cre", "base"), key="btn_base_cre")
        c2.button("➕ Débito", on_click=op_calc, args=("deb", "base"), key="btn_base_deb")
        
    with st.expander("➖ Resta (Devoluciones / Retiros)", expanded=False):
        c3, c4 = st.columns(2)
        c3.button("➖ Crédito", on_click=op_calc, args=("cre", "resta"), key="btn_resta_cre")
        c4.button("➖ Débito", on_click=op_calc, args=("deb", "resta"), key="btn_resta_deb")

    # Mostrar confirmación verde de la calculadora si existe
    if "confirmacion_calc" in st.session_state:
        st.markdown(st.session_state.confirmacion_calc, unsafe_allow_html=True)


# --- TAB 4: RESULTADOS ---
with tab4:
    # --- DESPLEGABLE EN RESULTADOS ---
    with st.expander("🧮 Ver y Editar Historial de Calculadora"):
        df_calc = pd.DataFrame(columns=["Tarjeta", "Operación", "Monto"]) # Default vacío
        if st.session_state.calc_historial:
            df_calc = pd.DataFrame(st.session_state.calc_historial)
            
        edited_calc = st.data_editor(df_calc, use_container_width=True, hide_index=True, num_rows="dynamic", key="editor_calc")
        
        if st.button("💾 Guardar Cambios en Calculadora", use_container_width=True):
            st.session_state.calc_historial = edited_calc.to_dict('records')
            st.success("Cálculos actualizados.")
            time.sleep(1)
            st.rerun()
        
    st.divider()
    
    # Recalculamos basándonos en la tabla editada
    base_cre = edited_calc[(edited_calc["Tarjeta"] == "Crédito") & (edited_calc["Operación"] == "Suma")]["Monto"].sum()
    resta_cre = edited_calc[(edited_calc["Tarjeta"] == "Crédito") & (edited_calc["Operación"] == "Resta")]["Monto"].sum()
    
    base_deb = edited_calc[(edited_calc["Tarjeta"] == "Débito") & (edited_calc["Operación"] == "Suma")]["Monto"].sum()
    resta_deb = edited_calc[(edited_calc["Tarjeta"] == "Débito") & (edited_calc["Operación"] == "Resta")]["Monto"].sum()

    res_cre = base_cre - resta_cre
    res_deb = base_deb - resta_deb
    
    st.markdown(f"""
    <div class="confirm" style="border-left:5px solid #ffcc00;">
        <p style="margin:0; font-size:14px; color:#aaa;">💳 Crédito (Sumado: ${base_cre:.2f} | Restado: ${resta_cre:.2f})</p>
        <h2 style="margin:0; color:#ffcc00;">${res_cre:.2f}</h2>
    </div>
    <div class="confirm" style="border-left:5px solid #00ccff;">
        <p style="margin:0; font-size:14px; color:#aaa;">💵 Débito (Sumado: ${base_deb:.2f} | Restado: ${resta_deb:.2f})</p>
        <h2 style="margin:0; color:#00ccff;">${res_deb:.2f}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    
    col_calc_1, col_calc_2 = st.columns(2)
    with col_calc_1:
        st.button("🧹 Limpiar Calculadora", on_click=limpiar_calc, use_container_width=True)
    
    with col_calc_2:
        mensaje_calc = f"🧮 *CALCULADORA CHAMPLITTE* ({datetime.now(zona_mx).strftime('%d/%m/%Y')})\n\n"
        mensaje_calc += f"💳 *Crédito:*\nSumado: ${base_cre:.2f}\nRestado: ${resta_cre:.2f}\n*Total: ${res_cre:.2f}*\n\n"
        mensaje_calc += f"💵 *Débito:*\nSumado: ${base_deb:.2f}\nRestado: ${resta_deb:.2f}\n*Total: ${res_deb:.2f}*"
        
        url_wa_calc = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje_calc)}"
        st.link_button("📲 Enviar al WhatsApp", url_wa_calc, use_container_width=True)
