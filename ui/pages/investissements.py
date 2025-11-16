# -*- coding: utf-8 -*-
"""
Module investissements - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
from ui.components import toast_success, toast_error


def interface_voir_investissements_alpha():
    st.subheader("📊 Performances de ton portefeuille (Trade Republic + Alpha Vantage) V2")

    api_key = st.text_input("🔑 Entre ta clé API Alpha Vantage :", type="password")
    if not api_key:
        st.info("Entre ta clé API Alpha Vantage pour continuer.")
        return
    ts = TimeSeries(key=api_key, output_format='pandas')

    uploaded_file = st.file_uploader("📥 Importer ton fichier CSV Trade Republic", type=["csv"])
    if uploaded_file is None:
        st.info("Importe ton CSV pour analyser ton portefeuille.")
        return

    df_tr = pd.read_csv(uploaded_file)
    st.markdown("### 💼 Données importées depuis Trade Republic")
    st.dataframe(df_tr, use_container_width=True, height=250)

    required_cols = {"Ticker", "Quantité", "Prix d'achat (€)"}
    if not required_cols.issubset(df_tr.columns):
        toast_error(f"Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        return

    tickers = df_tr["Ticker"].dropna().unique().tolist()

    st.markdown("### 📈 Données de marché en direct (Alpha Vantage)")
    data = {}
    for t in tickers:
        try:
            df, meta = ts.get_daily(symbol=t, outputsize='compact')
            df = df.rename(columns={
                '1. open': 'Open', '2. high': 'High',
                '3. low': 'Low', '4. close': 'Close', 
                '5. volume': 'Volume'
            })
            data[t] = df
        except Exception as e:
            logger.error(f"Alpha Vantage failed for {t}: {e}")
            toast_warning(f"Impossible de récupérer {t} ({e})")

    if not data:
        st.warning("Aucune donnée récupérée depuis Alpha Vantage.")
        return

    results = []
    for _, row in df_tr.iterrows():
        t = row["Ticker"]
        qte = safe_convert(row["Quantité"], float, 0.0)
        prix_achat = safe_convert(row["Prix d'achat (€)"], float, 0.0)
        if t not in data or data[t].empty:
            continue
        prix_actuel = data[t]['Close'].iloc[-1]
        perf = ((prix_actuel - prix_achat) / prix_achat) * 100
        valeur_totale = prix_actuel * qte
        results.append({
            "Symbole": t,
            "Quantité": qte,
            "Prix d'achat (€)": prix_achat,
            "Cours actuel (€)": round(prix_actuel, 2),
            "Performance (%)": round(perf, 2),
            "Valeur totale (€)": round(valeur_totale, 2)
        })

    df_results = pd.DataFrame(results)
    st.markdown("### 💹 Performance actuelle de ton portefeuille")
    st.dataframe(df_results, use_container_width=True, height=300)

    valeur_totale_portefeuille = df_results["Valeur totale (€)"].sum()
    perf_moyenne = df_results["Performance (%)"].mean()
    st.metric("💰 Valeur totale du portefeuille", f"{valeur_totale_portefeuille:,.2f} €", f"{perf_moyenne:.2f}%")

    premier_titre = df_results["Symbole"].iloc[0] if not df_results.empty else None
    if premier_titre and premier_titre in data:
        st.markdown(f"### 📊 Évolution récente de {premier_titre}")
        fig, ax = plt.subplots()
        ax.plot(data[premier_titre].index, data[premier_titre]["Close"], label=premier_titre)
        ax.set_title(f"Historique de {premier_titre}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Cours (€)")
        ax.legend()
        st.pyplot(fig)

    toast_success("Portefeuille analysé avec succès !")


