import streamlit as st
import pandas as pd
from datetime import datetime

# Configurazione Categorie e Unità
PARTITE = ["ANTIPASTI", "PRIMI", "SECONDI", "PIZZERIA", "FRITTI", "PASTICCERIA"]
CATEGORIE = [
    "UOVA", "ANIMALI/VOLATILI", "PESCI/ANFIBI", "CROSTACEI", "MOLLUSCHI", 
    "LEGUMI", "CEREALI", "VEGETALI", "FRUTTI", "FRUTTI SECCHI", "ERBE", 
    "SPEZIE", "FIORI", "SEMI", "INSACCATI", "LATTICINI", "FORMAGGI ITALIA", 
    "FORMAGGI MONDO", "PASTA", "PASTA RIPIENA", "CONDIMENTI", 
    "SOTTOLIO/ACETO/SALAMOIA", "SALSE", "FARINE", "VARIE", "ALCOLICI"
]
UNITA = ["kg", "Lt", "Pz", "Cs", "Vs"]

# Simulazione Database (In produzione si usa un file CSV o SQL)
if 'ordini' not in st.session_state:
    st.session_state.ordini = []

# --- INTERFACCIA ---
st.title("Sistema Ordini Interni")

menu = st.sidebar.radio("Navigazione", ["Area Chef (Ordini)", "Dashboard Executive (Riepilogo)"])

# --- AREA CHEF ---
if menu == "Area Chef (Ordini)":
    st.header("Nuovo Ordine")
    
    with st.form("form_ordine"):
        nome_chef = st.text_input("Nome Chef")
        partita = st.selectbox("Tua Partita", PARTITE)
        categoria = st.selectbox("Categoria Ingrediente", CATEGORIE)
        prodotto = st.text_input("Nome Prodotto (es. Farina 00)")
        quantita = st.number_input("Quantità", min_value=0.1, step=0.1)
        u_misura = st.selectbox("Unità", UNITA)
        
        submit = st.form_submit_button("Invia Ordine")
        
        if submit:
            nuovo_ordine = {
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Chef": nome_chef,
                "Partita": partita,
                "Categoria": categoria,
                "Prodotto": prodotto,
                "Quantità": quantita,
                "Unità": u_misura,
                "Stato": "Preso in carico"
            }
            st.session_state.ordini.append(nuovo_ordine)
            st.success("Ordine inviato con successo!")

    st.subheader("Il tuo storico ordini (Oggi)")
    df = pd.DataFrame(st.session_state.ordini)
    if not df.empty:
        st.write(df[df['Chef'] == nome_chef])

# --- DASHBOARD EXECUTIVE ---
elif menu == "Dashboard Executive (Riepilogo)":
    st.header("Riepilogo Totale per Fornitori")
    
    if st.session_state.ordini:
        df_totale = pd.DataFrame(st.session_state.ordini)
        
        # Aggregazione per categoria e prodotto per il fornitore
        riepilogo = df_totale.groupby(['Categoria', 'Prodotto', 'Unità'])['Quantità'].sum().reset_index()
        
        st.table(riepilogo)
        
        if st.button("Esporta per Fornitori (CSV)"):
            st.write("File pronto per l'invio.")
    else:
        st.info("Nessun ordine presente al momento.")
