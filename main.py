import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3
import pandas as pd

# ------------------ CONFIGURACIÓN ------------------

st.set_page_config(page_title="Corte Champlitte", layout="centered")

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

header {visibility:hidden;}
footer {visibility:hidden;}

.stApp{
background:#121212;
color:white;
}

input{
background:#000!important;
color:#90ee90!important;
font-size:2rem!important;
text-align:center!important;
border-radius:12px!important;
border:2px solid #444!important;
}

[data-testid="column"]{
width:calc(50% - 1rem)!important;
flex:1 1 calc(50% - 1rem)!important;
min-width:calc(50% - 1rem)!important;
}

.stButton>button{
width:100%;
border-radius:10px;
padding:16px;
background:#1e1e1e!important;
color:white!important;
font-size:1rem!important;
border:1px solid #333!important;
margin-bottom:6px;
}

.stButton>button:hover{
border-color:#90ee90!important;
background:#262626!important;
}

.confirm{
background:#1e1e1e;
padding:15px;
border-radius:10px;
border-left:5px solid #90ee90;
margin-top:15px;
}

.total-card{
background:#1b1b1b;
padding:20px;
border-radius:14px;
border-left:5px solid #90ee90;
margin-bottom:20px;
text-align:center;
}

.total-card h1{
font-size:2.5rem;
margin:0;
color:#90ee90;
}

</style>
""", unsafe_allow_html=True)

# ------------------ CATEGORÍAS ------------------

categorias = [
("💳 T. Débito","Tarjeta Débito"),
("💳 T. Crédito","Tarjeta Crédito"),
("🚗 Uber","Uber"),
("🛵 Didi","Didi"),
("📦 Rappi","Rappi"),
("🔗 Transf. Liga","Transferencia Liga")
]

# ------------------ FUNCIÓN REGISTRAR ------------------

def registrar_pago(cat):

    monto = st.session_state.monto_actual

    if monto and monto > 0:

        hora = datetime.now(zona_mx).strftime("%H:%M:%S")

        c.execute(
        "INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)",
        (cat,monto,hora)
        )

        conn.commit()

        st.session_state.confirmacion = f"""
        <div class="confirm">
        ✅ <b>Registrado:</b> ${monto:.2f}<br>
        💳 <b>Método:</b> {cat}<br>
        🕒 <b>Hora:</b> {hora}
        </div>
        """

        st.session_state.monto_actual = None

# ------------------ TABS ------------------

tab1,tab2 = st.tabs(["📝 REGISTRO","📊 RESUMEN"])

# ------------------ REGISTRO ------------------

with tab1:

    st.title("💰 Corte Champlitte")

    st.number_input(
    "Monto",
    min_value=0.0,
    step=0.01,
    value=None,
    format="%.2f",
    key="monto_actual",
    placeholder="0.00"
    )

    st.write("### Seleccionar método")

    for i in range(0,len(categorias),2):

        col1,col2 = st.columns(2)

        with col1:
            label,key = categorias[i]
            st.button(label, on_click=registrar_pago, args=(key,))

        with col2:
            if i+1 < len(categorias):
                label,key = categorias[i+1]
                st.button(label, on_click=registrar_pago, args=(key,))

    if "confirmacion" in st.session_state:
        st.markdown(st.session_state.confirmacion, unsafe_allow_html=True)

# ------------------ RESUMEN ------------------

with tab2:

    st.header("📊 Resumen")

    datos = c.execute(
        "SELECT id,categoria,monto,hora FROM ventas ORDER BY id DESC"
    ).fetchall()

    if not datos:

        st.info("Sin registros")

    else:

        df = pd.DataFrame(datos, columns=["id","categoria","monto","hora"])

        st.subheader("Editar movimientos")

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic"
        )

        col1,col2 = st.columns(2)

        with col1:
            if st.button("💾 Guardar cambios", use_container_width=True):

                c.execute("DELETE FROM ventas")

                for _,row in edited_df.iterrows():

                    c.execute(
                    "INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)",
                    (row["categoria"],row["monto"],row["hora"])
                    )

                conn.commit()

                st.success("Cambios guardados")

                st.rerun()

        with col2:
            if st.button("🗑️ Borrar todo", use_container_width=True):

                c.execute("DELETE FROM ventas")
                conn.commit()
                st.rerun()

        st.divider()

        # -------- TOTALES --------

        total_debito = edited_df[edited_df["categoria"]=="Tarjeta Débito"]["monto"].sum()
        total_credito = edited_df[edited_df["categoria"]=="Tarjeta Crédito"]["monto"].sum()

        total_tarjetas = total_debito + total_credito

        st.markdown(f"""
        <div class="total-card">
        <p>💳 TOTAL TARJETAS</p>
        <h1>${total_tarjetas:.2f}</h1>
        <p>Débito ${total_debito:.2f} • Crédito ${total_credito:.2f}</p>
        </div>
        """, unsafe_allow_html=True)

        # -------- WHATSAPP --------

        fecha = datetime.now(zona_mx).strftime("%d/%m/%Y")

        mensaje = f"💰 *CORTE CHAMPLITTE* ({fecha})\n\n"

        for cat in edited_df["categoria"].unique():

            total = edited_df[edited_df["categoria"]==cat]["monto"].sum()

            if total > 0:
                mensaje += f"• *{cat}:* ${total:.2f}\n"

        numero = "522283530069"

        url = f"https://wa.me/{numero}?text={urllib.parse.quote(mensaje)}"

        st.link_button("📲 ENVIAR REPORTE", url, use_container_width=True)
