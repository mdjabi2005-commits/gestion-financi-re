# -*- coding: utf-8 -*-
"""
Module components - Partie de l'application gestiov4
Généré automatiquement par migrate_to_modular.py
"""

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from services.file_manager import trouver_fichiers_associes


def show_toast(message: str, toast_type="success", duration=3000):
    """
    Affiche une notification toast professionnelle.
    
    Args:
        message (str): Message à afficher
        toast_type (str): Type de toast - 'success', 'warning', 'error'
        duration (int): Durée en millisecondes (défaut: 3000ms)
    """
    # Définir couleur et icône selon le type
    toast_config = {
        "success": {"color": "#10b981", "icon": "✅", "bg_light": "#d1fae5"},
        "warning": {"color": "#f59e0b", "icon": "⚠️", "bg_light": "#fef3c7"},
        "error": {"color": "#ef4444", "icon": "❌", "bg_light": "#fee2e2"}
    }
    
    config = toast_config.get(toast_type, toast_config["success"])
    
    components.html(f"""
        <div style="
            position:fixed;
            bottom:30px;right:30px;
            background:linear-gradient(135deg, {config['color']} 0%, {config['bg_light']} 100%);
            color:#1f2937;
            padding:12px 24px;
            border-radius:12px;
            font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
            font-weight:600;
            box-shadow:0 4px 20px rgba(0,0,0,0.15);
            border-left:4px solid {config['color']};
            z-index:9999;
            animation:slideIn 0.3s ease-out, fadeOut {duration/1000}s {(duration-1000)/1000}s forwards;">
            <span style="font-size:18px;margin-right:8px;">{config['icon']}</span>
            {message}
        </div>
        <style>
        @keyframes slideIn {{
          from {{
            transform: translateX(400px);
            opacity: 0;
          }}
          to {{
            transform: translateX(0);
            opacity: 1;
          }}
        }}
        @keyframes fadeOut {{
          0% {{opacity:1;}}
          100% {{opacity:0;visibility:hidden;}}
        }}
        </style>
    """, height=80)


def toast_success(message: str, duration=3000):
    """Toast de succès rapide"""
    show_toast(message, "success", duration)


def toast_warning(message: str, duration=3000):
    """Toast d'avertissement rapide"""
    show_toast(message, "warning", duration)


def toast_error(message: str, duration=3000):
    """Toast d'erreur rapide"""
    show_toast(message, "error", duration)


def get_badge_html(transaction):
    """Retourne le badge HTML pour une transaction"""
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")
    
    if source == "OCR":
        badge = "🧾 Ticket"
        couleur = "#1f77b4"
        emoji = "🧾"
    elif source == "PDF":
        if type_transaction == "revenu":
            badge = "💼 Bulletin"
            couleur = "#2ca02c"
            emoji = "💼"
        else:
            badge = "📄 Facture"
            couleur = "#ff7f0e"
            emoji = "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        badge = "📝 Manuel"
        couleur = "#7f7f7f"
        emoji = "📝"
    else:
        badge = "📎 Autre"
        couleur = "#9467bd"
        emoji = "📎"
    
    return f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{emoji} {badge}</span>"


def get_badge_icon(transaction):
    """Retourne juste l'emoji du badge"""
    source = transaction.get("source", "")
    type_transaction = transaction.get("type", "")
    
    if source == "OCR":
        return "🧾"
    elif source == "PDF":
        return "💼" if type_transaction == "revenu" else "📄"
    elif source in ["manuel", "récurrente", "récurrente_auto"]:
        return "📝"
    else:
        return "📎"


def afficher_carte_transaction(transaction, idx):
    """Affiche une carte détaillée pour la vue rapide"""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"**Catégorie :** {transaction['categorie']}")
        st.write(f"**Sous-catégorie :** {transaction['sous_categorie']}")
        st.write(f"**Date :** {transaction['date']}")
        
        if transaction.get('description'):
            st.write(f"**Description :** {transaction['description']}")
            
        if transaction.get('recurrence'):
            st.write(f"**Récurrence :** {transaction['recurrence']}")
    
    with col2:
        montant_color = "green" if transaction['type'] == 'revenu' else "red"
        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
        st.markdown(f"<h2 style='color: {montant_color}; text-align: center;'>{montant_prefix}{transaction['montant']:.2f} €</h2>", unsafe_allow_html=True)
        
        # Afficher automatiquement les documents si disponibles
        if transaction['source'] in ['OCR', 'PDF']:
            st.markdown("---")
            st.markdown("**📎 Documents :**")
            afficher_documents_associes(transaction.to_dict())


def afficher_documents_associes(transaction):
    """Affiche les documents associés à une transaction de façon améliorée"""
    fichiers = trouver_fichiers_associes(transaction)
    
    if not fichiers:
        source = transaction.get("source", "")
        type_transaction = transaction.get("type", "")
        
        if source == "OCR":
            st.warning("🧾 Aucun ticket de caisse trouvé dans les dossiers")
        elif source == "PDF":
            if type_transaction == "revenu":
                st.warning("💼 Aucun bulletin de paie trouvé")
            else:
                st.warning("📄 Aucune facture trouvée")
        else:
            st.info("📝 Aucun document associé")
        return

    # Afficher chaque fichier dans des onglets
    tabs = st.tabs([f"Document {i+1}" for i in range(len(fichiers))])
    
    for i, (tab, fichier) in enumerate(zip(tabs, fichiers)):
        with tab:
            nom_fichier = os.path.basename(fichier)
            
            if fichier.lower().endswith(('.jpg', '.jpeg', '.png')):
                # Afficher l'image
                try:
                    image = Image.open(fichier)
                    st.image(image, caption=f"🧾 {nom_fichier}", use_column_width=True)
                    
                    # Option: ré-OCR
                    with st.expander("🔍 Analyser le texte"):
                        texte_ocr = full_ocr(fichier, show_ticket=False)
                        st.text_area("Texte du ticket:", texte_ocr, height=150)
                        
                except Exception as e:
                    toast_error(f"Impossible d'afficher l'image: {e}")
                    
            elif fichier.lower().endswith('.pdf'):
                # Afficher les infos du PDF
                st.success(f"📄 **{nom_fichier}**")
                
                # Extraire le texte automatiquement
                try:
                    texte_pdf = extract_text_from_pdf(fichier)
                    if texte_pdf.strip():
                        with st.expander("📖 Contenu du document"):
                            apercu = texte_pdf[:2000] + "..." if len(texte_pdf) > 2000 else texte_pdf
                            st.text_area("Extrait:", apercu, height=200)
                except:
                    st.info("📄 Document PDF (contenu non extrait)")
                
                # Téléchargement
                with open(fichier, "rb") as f:
                    st.download_button(
                        label="⬇️ Télécharger le document",
                        data=f.read(),
                        file_name=nom_fichier,
                        mime="application/pdf",
                        use_container_width=True
                    )


def refresh_and_rerun():
    """
    Vide le cache des données et recharge la page.
    À utiliser après toute modification de données (ajout, suppression, modification).
    """
    st.cache_data.clear()
    st.rerun()


