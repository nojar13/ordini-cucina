import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="Ordini Interni Chef", layout="wide")

PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA"]
CATEGORIE = [
    "UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", 
    "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", 
    "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", 
    "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", 
    "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"
]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

# Connessione al foglio Google
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FUNZIONI ---
def get_data():
    return conn.read(worksheet="ordini", ttl="0")

# --- LOGIN SEMPLICE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    pw = st.text_input("Password Cucina", type="password")
    if pw == "Chef2026": # Puoi cambiare la password qui
        st.session_state.authenticated = True
        st.rerun()
    st.stop()

# --- NAVIGAZIONE ---
menu = st.sidebar.radio("Menu", ["Fai un Ordine", "Storico Personale", "Dashboard Executive"])

# --- 1. AREA ORDINE ---
if menu == "Fai un Ordine":
    st.header("🛒 Nuovo Ordine Interno")
    
    with st.form("ordine_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Tuo Nome")
            partita = st.selectbox("Tua Partita", PARTITE)
        with col2:
            categoria = st.selectbox("Categoria", CATEGORIE)
            prodotto = st.text_input("Ingrediente (es. Pomodori)")
            
        col3, col4 = st.columns(2)
        with col3:
            qta = st.number_input("Quantità", min_value=0.1, step=0.1)
        with col4:
            misura = st.selectbox("Unità", UNITA)
            
        submit = st.form_submit_button("INVIA ORDINE")
        
        if submit:
            if nome and prodotto:
                # Carica dati esistenti
                df_esistente = get_data()
                # Crea nuovo record
                nuovo_row = pd.DataFrame([{
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Chef": nome.upper(),
                    "Partita": partita,
                    "Categoria": categoria,
                    "Prodotto": prodotto.upper(),
                    "Quantita": qta,
                    "Unita": misura,
                    "Stato": "INVIATO"
                }])
                # Unisci e salva
                updated_df = pd.concat([df_esistente, nuovo_row], ignore_index=True)
                conn.update(worksheet="ordini", data=updated_df)
                st.success(f"Ordine per {prodotto} inviato!")
            else:
                st.error("Inserisci nome e prodotto!")

# --- 2. STORICO PERSONALE ---
elif menu == "Storico Personale":
    st.header("📋 I tuoi ordini di oggi")
    nome_cerca = st.text_input("Inserisci il tuo nome per filtrare")
    df = get_data()
    if not df.empty and nome_cerca:
        risultato = df[df['Chef'] == nome_cerca.upper()]
        st.dataframe(risultato, use_container_width=True)

# --- 3. DASHBOARD EXECUTIVE (IL TUO PANNELLO) ---
elif menu == "Dashboard Executive":
    st.header("👨‍🍳 Riepilogo Magazzino")
    df = get_data()
    
    if not df.empty:
        # Trasformiamo la colonna Quantità in numero per sicurezza
        df['Quantita'] = pd.to_numeric(df['Quantita'])
        
        st.subheader("Totali da ordinare ai fornitori")
        # Raggruppa per Categoria e Prodotto sommando le quantità
        riepilogo = df.groupby(['Categoria', 'Prodotto', 'Unita'])['Quantita'].sum().reset_index()
        st.dataframe(riepilogo, use_container_width=True)
        
        if st.button("Pulisci Lista Ordini (Svuota Tutto)"):
            header_only = pd.DataFrame(columns=df.columns)
            conn.update(worksheet="ordini", data=header_only)
            st.warning("Lista svuotata!")
            st.rerun()
    else:
        st.info("Nessun ordine presente.")
