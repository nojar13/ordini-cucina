import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Ordini Cucina", layout="wide")

# Liste predefinite
PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA", "ADMIN"]
CATEGORIE = ["UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

# Connessione
conn = st.connection("gsheets", type=GSheetsConnection)

# Gestione Accesso
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Login", "Registrati"])
    
    with tab1:
        with st.form("L"):
            u = st.text_input("Username").upper()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Entra"):
                try:
                    users = conn.read(worksheet="utenti", ttl=0)
                    user = users[(users['Username'] == u) & (users['Password'] == p)]
                    if not user.empty:
                        st.session_state.user, st.session_state.role = u, user.iloc[0]['Partita']
                        st.rerun()
                    else:
                        st.error("Credenziali errate")
                except:
                    st.error("Errore di connessione. Verifica il foglio Google e i Secrets.")

    with tab2:
        with st.form("R"):
            nu = st.text_input("Scegli Username").upper()
            np = st.text_input("Password", type="password")
            npart = st.selectbox("Tua Partita", PARTITE[:-1])
            if st.form_submit_button("Crea Account"):
                try:
                    users = conn.read(worksheet="utenti", ttl=0)
                    if nu in users['Username'].values:
                        st.error("Username già esistente")
                    else:
                        new_user = pd.DataFrame([{"Username": nu, "Password": np, "Partita": npart}])
                        conn.update(worksheet="utenti", data=pd.concat([users, new_user], ignore_index=True))
                        st.success("Fatto! Ora fai il login.")
                except:
                    st.error("Errore nel salvataggio. Verifica i permessi del foglio.")
    st.stop()

# Menu principale
st.sidebar.write(f"Chef: {st.session_state.user} ({st.session_state.role})")
opzioni = ["Nuovo Ordine", "Mio Storico"]
if st.session_state.role == "ADMIN": 
    opzioni.append("DASHBOARD EXECUTIVE")
scelta = st.sidebar.radio("Vai a:", opzioni)

if scelta == "Nuovo Ordine":
    with st.form("O", clear_on_submit=True):
        c = st.selectbox("Categoria", CATEGORIE)
        p = st.text_input("Ingrediente")
        col1, col2 = st.columns(2)
        q = col1.number_input("Quantità", min_value=0.1)
        m = col2.selectbox("Unità", UNITA)
        if st.form_submit_button("INVIA"):
            ordini = conn.read(worksheet="ordini", ttl=0)
            nuovo = pd.DataFrame([{"Data": datetime.now().strftime("%d/%m/%Y"), "Chef": st.session_state.user, "Partita": st.session_state.role, "Categoria": c, "Prodotto": p.upper(), "Quantita": q, "Unita": m}])
            conn.update(worksheet="ordini", data=pd.concat([ordini, nuovo], ignore_index=True))
            st.success("Inviato!")

elif scelta == "Mio Storico":
    df = conn.read(worksheet="ordini", ttl=0)
    st.dataframe(df[df['Chef'] == st.session_state.user], use_container_width=True)

elif scelta == "DASHBOARD EXECUTIVE":
    df = conn.read(worksheet="ordini", ttl=0)
    if not df.empty:
        df['Quantita'] = pd.to_numeric(df['Quantita'])
        st.subheader("Riepilogo Totale per Categoria")
        riepilogo = df.groupby(['Categoria', 'Prodotto', 'Unita'])['Quantita'].sum().reset_index()
        st.table(riepilogo)
        if st.button("Svuota lista ordini"):
            conn.update(worksheet="ordini", data=pd.DataFrame(columns=df.columns))
            st.rerun()
