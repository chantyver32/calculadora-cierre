import streamlit as st
import urllib.parse
from datetime import datetime
import pytz
import sqlite3

# ------------------ CONFIGURACIÓN ------------------
st.set_page_config(page_title="Cierre Champlitte", layout="centered")

zona_mx = pytz.timezone('America/Mexico_City')

# --- BASE DE DATOS ---
conn = sqlite3.connect('corte_champlitte.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS ventas 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, categoria TEXT, monto REAL, hora TEXT)''')
conn.commit()

# ------------------ CSS ------------------
st.markdown("""
<style>

header {visibility: hidden;}
footer {visibility: hidden;}

.stApp { background-color:#121212; color:white;}

input{
background:#000!important;
color:#90ee90!important;
font-size:2rem!important;
text-align:center!important;
border-radius:15px!important;
border:2px solid #444!important;
}

/* GRID */
[data-testid="column"]{
width:calc(50% - 1rem)!important;
flex:1 1 calc(50% - 1rem)!important;
min-width:calc(50% - 1rem)!important;
}

/* BOTONES */
.stButton>button{
width:100%;
border-radius:10px;
padding:15px 5px;
background:#1e1e1e!important;
color:white!important;
font-size:0.85rem!important;
border:1px solid #333!important;
margin-bottom:2px;
}

.stButton>button:hover{
border-color:#90ee90!important;
background:#262626!important;
}

/* TARJETA TOTAL */
.total-card{
background:#1b1b1b;
padding:20px;
border-radius:14px;
border-left:5px solid #90ee90;
margin-bottom:20px;
text-align:center;
}

.total-card h1{
font-size:2.4rem;
margin:0;
color:#90ee90;
}

.total-card p{
margin:0;
color:#aaa;
}

.footer-text{
color:#666;
font-size:0.8rem;
margin-top:30px;
text-align:center;
}

</style>
""", unsafe_allow_html=True)

# ------------------ CATEGORIAS ------------------

categorias = [
("💳 T. Débito","Tarjeta Débito"),
("💳 T. Crédito","Tarjeta Crédito"),
("🚗 Uber","Uber"),
("🛵 Didi","Didi"),
("📦 Rappi","Rappi"),
("🔗 Transf. Liga","Transferencia Liga")
]

# ------------------ FUNCIONES ------------------

def registrar_pago(cat_key):

    monto = st.session_state.monto_actual

    if monto and monto > 0:

        hora = datetime.now(zona_mx).strftime("%H:%M:%S")

        c.execute(
        "INSERT INTO ventas (categoria,monto,hora) VALUES (?,?,?)",
        (cat_key,monto,hora)
        )

        conn.commit()

        st.session_state.monto_actual=None

        st.toast(f"✅ {cat_key} ${monto:.2f}")

    else:

        st.error("⚠️ Monto inválido")


def borrar_ultimo(cat_key):

    c.execute(
    "DELETE FROM ventas WHERE id=(SELECT MAX(id) FROM ventas WHERE categoria=?)",
    (cat_key,)
    )

    conn.commit()


# ------------------ TABS ------------------

tab1,tab2=st.tabs(["📝 REGISTRO","📊 RESUMEN"])


# ------------------ TAB REGISTRO ------------------

with tab1:

    st.title("💰 Corte Champlitte")

    st.number_input(
    "Monto:",
    min_value=0.0,
    step=0.01,
    value=None,
    format="%.2f",
    key="monto_actual",
    placeholder="0.00"
    )

    st.write("### Clasificar:")

    for i in range(0,len(categorias),2):

        col1,col2=st.columns(2)

        with col1:

            label,key=categorias[i]

            st.button(
            label,
            key=f"btn_{key}",
            on_click=registrar_pago,
            args=(key,)
            )

        with col2:

            if i+1<len(categorias):

                label,key=categorias[i+1]

                st.button(
                label,
                key=f"btn_{key}",
                on_click=registrar_pago,
                args=(key,)
                )

# ------------------ TAB RESUMEN ------------------

with tab2:

    st.header("📊 Resumen")

    datos=c.execute(
    "SELECT id,categoria,monto,hora FROM ventas"
    ).fetchall()

    if not datos:

        st.info("Sin registros.")

    else:

        # -------- SUMATORIA TARJETAS --------

        total_debito=sum(d[2] for d in datos if d[1]=="Tarjeta Débito")
        total_credito=sum(d[2] for d in datos if d[1]=="Tarjeta Crédito")

        total_tarjetas=total_debito+total_credito

        st.markdown(f"""
        <div class="total-card">
        <p>💳 TOTAL TARJETAS</p>
        <h1>${total_tarjetas:.2f}</h1>
        <p>Débito ${total_debito:.2f} • Crédito ${total_credito:.2f}</p>
        </div>
        """,unsafe_allow_html=True)

        # -------- LISTA NORMAL --------

        for label,key in categorias:

            pagos_cat=[d for d in datos if d[1]==key]

            subtotal=sum(p[2] for p in pagos_cat)

            if pagos_cat:

                with st.expander(f"{label}: ${subtotal:.2f}"):

                    for p in pagos_cat:

                        c1,c2=st.columns(2)

                        c1.write(f"Hora: {p[3]}")

                        c2.write(f"**${p[2]:.2f}**")

                    st.button(
                    f"Deshacer {key}",
                    key=f"undo_{key}",
                    on_click=borrar_ultimo,
                    args=(key,)
                    )

        st.divider()

        # -------- WHATSAPP --------

        fecha=datetime.now(zona_mx).strftime("%d/%m/%Y")

        mensaje=f"💰 *CORTE CHAMPLITTE* ({fecha})\n\n"

        for label,key in categorias:

            total=sum(d[2] for d in datos if d[1]==key)

            if total>0:

                mensaje+=f"• *{key}:* ${total:.2f}\n"

        num="522283530069"

        url=f"https://wa.me/{num}?text={urllib.parse.quote(mensaje)}"

        st.link_button(
        "📲 ENVIAR REPORTE",
        url,
        use_container_width=True,
        type="primary"
        )

        if st.button("🚨 REINICIAR TURNO",use_container_width=True):

            c.execute("DELETE FROM ventas")

            conn.commit()

            st.rerun()


st.markdown(
'<p class="footer-text">v2.5 - Champlitte CDMX</p>',
unsafe_allow_html=True
)
