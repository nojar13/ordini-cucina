import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="App Ordini Chef", layout="wide")

# Liste predefinite
PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA", "ADMIN"]
CATEGORIE = ["UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONE DI AGGIORNAMENTO SICURO ---
def safe_update(worksheet_name, new_data):
    try:
        # Legge il foglio esistente
        existing_data = conn.read(worksheet=worksheet_name, ttl=0)
        # Unisce i dati (assicurandosi che le colonne siano le stesse)
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        # Converte tutto in stringa per evitare errori di formato 400
        updated_df = updated_df.astype(str)
        # Invia l'aggiornamento
        conn.update(worksheet=worksheet_name, data=updated_df)
        return True
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return False

# --- GESTIONE ACCESSO ---
if "user" not in st.session_state:
    st.session_state.user = None
    st.session_state.role = None

if st.session_state.user is None:
    t1, t2 = st.tabs(["Login", "Registrati"])
    with t1:
        with st.form("L"):
            u = st.text_input("Username").upper().strip()
            p = st.text_input("Password", type="password").strip()
            if st.form_submit_button("ENTRA"):
                df_u = conn.read(worksheet="utenti", ttl=0)
                user_row = df_u[(df_u['Username'].astype(str) == u) & (df_u['Password'].astype(str) == p)]
                if not user_row.empty:
                    st.session_state.user = u
                    st.session_state.role = user_row.iloc[0]['Partita']
                    st.rerun()
                else:
                    st.error("Credenziali errate")
    with t2:
        with st.form("R"):
            nu = st.text_input("Username").upper().strip()
            np = st.text_input("Password", type="password").strip()
            npart = st.selectbox("Partita", PARTITE[:-1])
            if st.form_submit_button("CREA ACCOUNT"):
                if nu and np:
                    new_u = pd.DataFrame([{"Username": nu, "Password": np, "Partita": npart}])
                    if safe_update("utenti", new_u):
                        st.success("Account creato! Fai il login")
                else:
                    st.warning("Riempi tutti i campi")
    st.stop()

# --- MENU ---
st.sidebar.title(f"Chef: {st.session_state.user}")
opzioni = ["Nuovo Ordine", "Storico"]
if st.session_state.role == "ADMIN": opzioni.append("DASHBOARD")
scelta = st.sidebar.radio("Vai a:", opzioni)

if scelta == "Nuovo Ordine":
    st.header("🛒 Invia Ordine")
    with st.form("O", clear_on_submit=True):
        cat = st.selectbox("Categoria", CATEGORIE)
        prod = st.text_input("Prodotto").upper().strip()
        c1, c2 = st.columns(2)
        qta = c1.number_input("Quantità", min_value=0.1, step=0.1)
        uni = c2.selectbox("Unità", UNITA)
        if st.form_submit_button("INVIA"):
            if prod:
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
                if safe_update("ordini", nuovo_o):
                    st.success(f"Inviato: {prod}")
            else:
                st.warning("Inserisci il nome del prodotto")

elif scelta == "Storico":
    df_o = conn.read(worksheet="ordini", ttl=0)
    st.dataframe(df_o[df_o['Chef'] == st.session_state.user], use_container_width=True)

elif scelta == "DASHBOARD":
    st.header("👨‍🍳 Riepilogo Totale")
    df_o = conn.read(worksheet="ordini", ttl=0)
    if not df_o.empty:
        df_o['Quantita'] = pd.to_numeric(df_o['Quantita'], errors='coerce')
        riepilogo = df_o.groupby(['Categoria', 'Prodotto', 'Unita'])['Quantita'].sum().reset_index()
        st.table(riepilogo)
        if st.button("SVUOTA TUTTO"):
            conn.update(worksheet="ordini", data=pd.DataFrame(columns=df_o.columns))
            st.rerun()

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()
