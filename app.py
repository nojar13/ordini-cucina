import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Sistema Ordini Cucina", layout="wide")

PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA", "ADMIN"]
CATEGORIE = ["UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONI DATI ---
def get_users():
    return conn.read(worksheet="utenti", ttl="0")

def get_orders():
    return conn.read(worksheet="ordini", ttl="0")

# --- GESTIONE SESSIONE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- AUTENTICAZIONE ---
if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Login", "Registrati"])
    
    with tab1:
        with st.form("login"):
            u = st.text_input("Username").upper()
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Entra"):
                users_df = get_users()
                user_data = users_df[(users_df['Username'] == u) & (users_df['Password'] == p)]
                if not user_data.empty:
                    st.session_state.user = u
                    st.session_state.role = user_data.iloc[0]['Partita']
                    st.rerun()
                else:
                    st.error("Credenziali errate")
    
    with tab2:
        with st.form("register"):
            new_u = st.text_input("Scegli Username").upper()
            new_p = st.text_input("Scegli Password", type="password")
            new_partita = st.selectbox("Seleziona la tua Partita", PARTITE[:-1]) # Esclude ADMIN dalla registrazione pubblica
            if st.form_submit_button("Crea Account"):
                users_df = get_users()
                if new_u in users_df['Username'].values:
                    st.error("Username già esistente")
                else:
                    new_user = pd.DataFrame([{"Username": new_u, "Password": new_p, "Partita": new_partita}])
                    updated_users = pd.concat([users_df, new_user], ignore_index=True)
                    conn.update(worksheet="utenti", data=updated_users)
                    st.success("Account creato! Ora fai il Login.")
    st.stop()

# --- APP DOPO IL LOGIN ---
st.sidebar.title(f"Chef: {st.session_state.user}")
st.sidebar.write(f"Partita: {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

menu_options = ["Nuovo Ordine", "Mio Storico"]
if st.session_state.role == "ADMIN":
    menu_options.append("DASHBOARD EXECUTIVE")

menu = st.sidebar.radio("Navigazione", menu_options)

# --- LOGICA PAGINE ---
if menu == "Nuovo Ordine":
    st.header("🛒 Invia Ordine Interno")
    with st.form("ordine_form", clear_on_submit=True):
        cat = st.selectbox("Categoria", CATEGORIE)
        prod = st.text_input("Prodotto")
        col1, col2 = st.columns(2)
        qta = col1.number_input("Quantità", min_value=0.1)
        uni = col2.selectbox("Unità", UNITA)
        
        if st.form_submit_button("Invia"):
            df_ordini = get_orders()
            nuovo = pd.DataFrame([{
                "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "Chef": st.session_state.user,
                "Partita": st.session_state.role,
                "Categoria": cat,
                "Prodotto": prod.upper(),
                "Quantita": qta,
                "Unita": uni,
                "Stato": "INVIATO"
            }])
            conn.update(worksheet="ordini", data=pd.concat([df_ordini, nuovo], ignore_index=True))
            st.success("Ordine registrato!")

elif menu == "Mio Storico":
    st.header("📋 I tuoi ordini")
    df = get_orders()
    st.dataframe(df[df['Chef'] == st.session_state.user])

elif menu == "DASHBOARD EXECUTIVE":
    st.header("👨‍🍳 Pannello Chef Executive")
    df = get_orders()
    if not df.empty:
        df['Quantita'] = pd.to_numeric(df['Quantita'])
        riepilogo = df.groupby(['Categoria', 'Prodotto', 'Unita'])['Quantita'].sum().reset_index()
        st.subheader("Riepilogo Totale Fabbisogno")
        st.dataframe(riepilogo, use_container_width=True)
        
        if st.button("Svuota Ordini del Giorno"):
            conn.update(worksheet="ordini", data=pd.DataFrame(columns=df.columns))
            st.rerun()
