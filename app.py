import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="App Ordini Interni", layout="wide")

PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA", "ADMIN"]
CATEGORIE = ["UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

conn = st.connection("gsheets", type=GSheetsConnection)

if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if st.session_state.user is None:
    t1, t2 = st.tabs(["Login", "Registrati"])
    with t1:
        with st.form("L"):
            u = st.text_input("Username").upper()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ENTRA"):
                df_u = conn.read(worksheet="utenti", ttl=0)
                user_row = df_u[(df_u['Username'] == u) & (df_u['Password'] == p)]
                if not user_row.empty:
                    st.session_state.user = u
                    st.session_state.role = user_row.iloc[0]['Partita']
                    st.rerun()
                else:
                    st.error("Credenziali errate")
    with t2:
        with st.form("R"):
            nu = st.text_input("Nuovo Username").upper()
            np = st.text_input("Nuova Password", type="password")
            npart = st.selectbox("Partita", PARTITE[:-1])
            if st.form_submit_button("CREA ACCOUNT"):
                try:
                    df_u = conn.read(worksheet="utenti", ttl=0)
                    if nu in df_u['Username'].values:
                        st.error("Username già esistente")
                    else:
                        new_u = pd.DataFrame([{"Username": nu, "Password": np, "Partita": npart}])
                        conn.update(worksheet="utenti", data=pd.concat([df_u, new_u], ignore_index=True))
                        st.success("Account creato! Fai il login")
                except Exception as e:
                    st.error(f"Errore: {e}. Controlla i permessi Editor del foglio.")
    st.stop()

st.sidebar.title(f"Chef: {st.session_state.user}")
opzioni = ["Nuovo Ordine", "Storico Ordini"]
if st.session_state.role == "ADMIN":
    opzioni.append("DASHBOARD EXECUTIVE")

scelta = st.sidebar.radio("Menu", opzioni)

if scelta == "Nuovo Ordine":
    st.header("🛒 Nuovo Ordine")
    with st.form("O", clear_on_submit=True):
        cat = st.selectbox("Categoria", CATEGORIE)
        prod = st.text_input("Prodotto").upper()
        c1, c2 = st.columns(2)
        qta = c1.number_input("Quantità", min_value=0.1, step=0.1)
        uni = c2.selectbox("Unità", UNITA)
        if st.form_submit_button("INVIA ORDINE"):
            try:
                df_o = conn.read(worksheet="ordini", ttl=0)
                nuovo_o = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Chef": st.session_state.user,
                    "Partita": st.session_state.role,
                    "Categoria": cat,
                    "Prodotto": prod,
                    "Quantita": qta,
                    "Unita": uni,
                    "Stato": "IN CARICO"
                }])
                conn.update(worksheet="ordini", data=pd.concat([df_o, nuovo_o], ignore_index=True))
                st.success(f"Ordine inviato: {prod}")
            except Exception as e:
                st.error(f"Errore invio: {e}")

elif scelta == "Storico Ordini":
    st.header("📋 I tuoi ordini (Ultime 24h)")
    df_o = conn.read(worksheet="ordini", ttl=0)
    st.dataframe(df_o[df_o['Chef'] == st.session_state.user], use_container_width=True)

elif scelta == "DASHBOARD EXECUTIVE":
    st.header("👨‍🍳 Riepilogo Fornitori")
    df_o = conn.read(worksheet="ordini", ttl=0)
    if not df_o.empty:
        df_o['Quantita'] = pd.to_numeric(df_o['Quantita'])
        st.subheader("Somma totale prodotti")
        riepilogo = df_o.groupby(['Categoria', 'Prodotto', 'Unita'])['Quantita'].sum().reset_index()
        st.table(riepilogo)
        
        st.divider()
        if st.button("SVUOTA TUTTI GLI ORDINI"):
            conn.update(worksheet="ordini", data=pd.DataFrame(columns=df_o.columns))
            st.rerun()
    else:
        st.info("Nessun ordine presente")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()
