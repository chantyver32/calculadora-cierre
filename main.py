# ---------------- TAB 2: RESUMEN DE PAGOS ----------------
with tab2:

    st.markdown("## 💳 Resumen de Pagos")

    conn = sqlite3.connect("inventario.db")
    c = conn.cursor()

    c.execute("SELECT metodo_pago, monto FROM ventas")
    datos = c.fetchall()

    conn.close()

    if datos:

        # SUMATORIAS
        efectivo = sum(d[1] for d in datos if d[0] == "Efectivo")
        debito = sum(d[1] for d in datos if d[0] == "Tarjeta Débito")
        credito = sum(d[1] for d in datos if d[0] == "Tarjeta Crédito")

        total_tarjetas = debito + credito
        total_general = efectivo + total_tarjetas

        # CSS TARJETAS
        st.markdown("""
        <style>
        .card {
            background-color:#111;
            padding:20px;
            border-radius:12px;
            margin-bottom:15px;
            border-left:5px solid #00ff88;
            box-shadow:0px 2px 10px rgba(0,0,0,0.4);
        }

        .titulo{
            font-size:0.9rem;
            color:#aaa;
            margin-bottom:5px;
        }

        .numero{
            font-size:2.5rem;
            color:#90ee90;
            font-weight:bold;
        }

        .fila{
            display:flex;
            justify-content:space-between;
            font-size:1.1rem;
            margin-top:6px;
        }
        </style>
        """, unsafe_allow_html=True)

        # TOTAL GENERAL
        st.markdown(f"""
        <div class="card">
            <div class="titulo">💰 TOTAL GENERAL</div>
            <div class="numero">${total_general:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

        # TARJETAS
        st.markdown(f"""
        <div class="card">
            <div class="titulo">💳 TOTAL TARJETAS</div>
            <div class="numero">${total_tarjetas:,.2f}</div>
            <hr style="border:0.5px solid #333;">
            <div class="fila">
                <span>💳 Débito</span>
                <b>${debito:,.2f}</b>
            </div>
            <div class="fila">
                <span>💳 Crédito</span>
                <b>${credito:,.2f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # EFECTIVO
        st.markdown(f"""
        <div class="card">
            <div class="titulo">💵 EFECTIVO</div>
            <div class="numero">${efectivo:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("No hay registros de ventas aún.")
