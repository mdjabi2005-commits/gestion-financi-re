from difflib import get_close_matches
import os
import shutil
import sqlite3
import pandas as pd
import pytesseract 
from PIL import Image
import re
import streamlit as st
from datetime import datetime, date, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
import cv2
import numpy as np
from io import BytesIO
from pathlib import Path
from chardet import detect

# ==============================
# 📄 Configuration Streamlit
# ==============================
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# 📂 CONFIGURATION DES DOSSIERS
# ==============================
from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES

def get_db_connection():
    """Retourne une connexion SQLite cohérente avec DB_PATH."""
    return sqlite3.connect(DB_PATH)

# ==============================
# 💾 BASE DE DONNÉES SQLITE
# ==============================

def init_db():
    """Initialise ou met à jour la base de données SQLite avec la table 'transactions'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Créer la table avec le bon schéma
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            categorie TEXT,
            sous_categorie TEXT,
            description TEXT,
            montant REAL,
            date TEXT,
            source TEXT,
            recurrence TEXT,
            date_fin TEXT
        )
    """)
    
    # 🔄 Mettre à jour la table si elle existe avec l'ancien schéma
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN source TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # La colonne existe déjà
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN recurrence TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE transactions ADD COLUMN date_fin TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass
    
    conn.commit()
    conn.close()


def migrate_database_schema():
    """Migre le schéma de la base de données vers les nouveaux noms de colonnes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier si la table existe avec l'ancien schéma
        cursor.execute("PRAGMA table_info(transactions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Si les anciennes colonnes existent, on migre
        if "Catégorie" in columns or "Sous-catégorie" in columns:
            print("🔄 Migration du schéma de la base de données...")
            
            # Créer une nouvelle table avec le bon schéma
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    categorie TEXT,
                    sous_categorie TEXT,
                    description TEXT,
                    montant REAL,
                    date TEXT,
                    source TEXT,
                    recurrence TEXT,
                    date_fin TEXT
                )
            """)
            
            # Copier les données en mappant les anciens noms vers les nouveaux
            cursor.execute("""
                INSERT INTO transactions_new 
                (id, type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                SELECT 
                id, 
                type, 
                "Catégorie" AS categorie, 
                "Sous-catégorie" AS sous_categorie, 
                description, 
                montant, 
                "Date" AS date, 
                "Source" AS source, 
                "Récurrence" AS recurrence, 
                date_fin
                FROM transactions
            """)
            
            # Supprimer l'ancienne table
            cursor.execute("DROP TABLE transactions")
            
            # Renommer la nouvelle table
            cursor.execute("ALTER TABLE transactions_new RENAME TO transactions")
            
            print("✅ Migration terminée avec succès!")
        else:
            print("✅ Le schéma est déjà à jour")
            
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
    finally:
        conn.commit()
        conn.close()

# Appeler la migration au démarrage
init_db()
migrate_database_schema()



# ==============================
# 📁 Dictionnaire des mois
# ==============================
mois_dict = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12"
}

def numero_to_mois(num: str) -> str:
    for mois, numero in mois_dict.items():
        if numero == num:
            return mois
    return "inconnu"

# ==============================
# 🧠 OCR ET TRAITEMENT DE TICKET ET REVENU
# ==============================
def full_ocr(image_path: str, show_ticket: bool = False) -> str:
    """
    Effectue un OCR complet sur une image de ticket.
    Version robuste + option d'affichage du ticket dans Streamlit.
    """
    try:
        # --- Lecture robuste du fichier image ---
        image_data = np.fromfile(image_path, dtype=np.uint8)
        image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Impossible de lire ou décoder l'image : {image_path}")

        # --- Prétraitement pour OCR ---
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        pil_img = Image.fromarray(thresh)

        # --- OCR ---
        text = pytesseract.image_to_string(pil_img, lang="fra")
        text = text.replace("\x0c", "").strip()

        # --- Option : affichage dans Streamlit ---
        if show_ticket:
            with st.expander(f"🧾 Aperçu du ticket : {os.path.basename(image_path)}", expanded=False):
                st.image(cv2.cvtColor(image, cv2.COLOR_BGR2RGB), caption=os.path.basename(image_path))
                if text:
                    st.text_area("Texte OCR détecté :", text, height=200)
                else:
                    st.warning("⚠️ Aucun texte détecté par l'OCR.")

        return text

    except Exception as e:
        st.error(f"❌ Erreur OCR sur {os.path.basename(image_path)} : {e}")
        return ""


def nettoyer_montant(montant_str):
    """
    Nettoie et convertit un montant en float
    Gère les virgules, espaces, symboles monétaires
    """
    try:
        # Convertir en string si ce n'est pas déjà le cas
        montant = str(montant_str).strip()
        
        # Enlever les guillemets, espaces et symboles monétaires
        montant = montant.replace('"', '').replace('€', '').replace(' ', '')
        
        # Remplacer la virgule par un point (format français → format Python)
        montant = montant.replace(',', '.')
        
        # Convertir en float
        return float(montant)
    except (ValueError, TypeError):
        return 0.0

# 🔥 FONCTIONS UTILITAIRES AMÉLIORÉES

def trouver_fichiers_associes(transaction, base_dirs=[SORTED_DIR, REVENUS_TRAITES]):
    """
    Trouve les fichiers (images/PDF) associés à une transaction basée sur:
    - Catégorie et sous-catégorie
    - Date (approximative)
    - Montant (approximatif)
    """
    fichiers_trouves = []
    
    categorie = transaction.get("categorie", "").strip()
    sous_categorie = transaction.get("sous_categorie", "").strip()
    date_transaction = transaction.get("date", "")
    montant = transaction.get("montant", 0.0)
    source = transaction.get("source", "")
    
    # Déterminer le dossier de recherche selon la source
    if source in ["OCR", "import_csv"] and "dépense" in transaction.get("type", ""):
        dossiers_recherche = [SORTED_DIR]
    elif source in ["PDF", "import_csv"] and "revenu" in transaction.get("type", ""):
        dossiers_recherche = [REVENUS_TRAITES]
    else:
        dossiers_recherche = base_dirs
    
    for base_dir in dossiers_recherche:
        if not os.path.exists(base_dir):
            continue
            
        # Construire le chemin attendu : base/categorie/sous_categorie/
        chemin_attendu = os.path.join(base_dir, categorie, sous_categorie)
        
        if os.path.exists(chemin_attendu):
            # Rechercher tous les fichiers dans le dossier
            for fichier in os.listdir(chemin_attendu):
                if fichier.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                    chemin_complet = os.path.join(chemin_attendu, fichier)
                    
                    # Vérification supplémentaire par date (optionnelle)
                    if date_transaction:
                        try:
                            # Extraire la date du nom de fichier si possible
                            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', fichier)
                            if date_match:
                                date_fichier = date_match.group(1)
                                if date_fichier in date_transaction:
                                    fichiers_trouves.append(chemin_complet)
                                    continue
                        except:
                            pass
                    
                    # Si pas de correspondance par date, on l'ajoute quand même
                    fichiers_trouves.append(chemin_complet)
    
    return fichiers_trouves[:5]  # Limiter à 5 fichiers maximum


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
                    st.error(f"❌ Impossible d'afficher l'image: {e}")
                    
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


def normaliser_date(date_str):
    """
    Convertit une date (JJ/MM/AAAA, JJ/MM/AA, AAAA-MM-JJ, etc.)
    en format ISO (AAAA-MM-JJ) pour la base SQLite.
    """
    if not isinstance(date_str, str) or not date_str.strip():
        return ""

    date_str = date_str.strip()

    # Formats possibles (on peut en rajouter si besoin)
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y", "%Y/%m/%d", "%d-%m-%Y", "%d-%m-%y"]
    
    for fmt in formats:
        try:
            d = datetime.strptime(date_str, fmt)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # Si aucun format reconnu
    print(f"[WARN] Format de date non reconnu : {date_str}")
    return ""


def insert_transaction(transaction):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO transactions
        (type, categorie, sous_categorie, description, montant, date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        transaction['type'],
        transaction["categorie"],
        transaction["sous_categorie"],
        transaction.get("description", ''),
        transaction['montant'],
        transaction["date"],
        transaction.get("source", '')
    ))
    
    conn.commit()
    conn.close()


def insert_transaction_batch(transactions):
    """
    Insère plusieurs transactions dans la base SQLite.
    Évite les doublons basés sur (type, categorie, sous_categorie, montant, date).
    """
    if not transactions:
        return
    conn = get_db_connection()
    cur = conn.cursor()

    inserted, skipped = 0, 0

    for t in transactions:
        try:
            cur.execute("""
                SELECT COUNT(*) FROM transactions
                WHERE type = ? AND categorie = ? AND sous_categorie = ?
                      AND montant = ? AND date = ?
            """, (
                t["type"],
                t.get("categorie", ""),
                t.get("sous_categorie", ""),
                float(t["montant"]),
                t["date"]
            ))

            if cur.fetchone()[0] > 0:
                skipped += 1
                continue

            cur.execute("""
                INSERT INTO transactions
                (type, categorie, sous_categorie, description, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t["type"],
                t.get("categorie", ""),
                t.get("sous_categorie", ""),
                t.get("description", ""),
                float(t["montant"]),
                t["date"],
                t.get("source", "manuel"),
                t.get("recurrence", ""),
                t.get("date_fin", "")
            ))
            inserted += 1

        except Exception as e:
            print(f"Erreur lors de l'insertion de {t}: {e}")

    conn.commit()
    conn.close()
    st.success(f"✅ {inserted} transaction(s) insérée(s).")
    if skipped > 0:
        st.info(f"ℹ️ {skipped} doublon(s) détecté(s) et ignoré(s).")


def get_montant_from_line(label_pattern, all_lines, allow_next_line=True):
    """
    Recherche un montant à partir d'un label (ex: 'TOTAL', 'MONTANT RÉEL', etc.)
    Corrigée pour être plus robuste face aux erreurs d'OCR et aux formats de tickets variés.
    """
    montant_regex = r"(\d{1,5}[.,]?\d{0,2})\s*(?:€|eur|euros?)?"

    def clean_ocr_text(txt):
        """Corrige les erreurs courantes de lecture OCR (O/0, I/1, etc.)."""
        txt = txt.replace("O", "0").replace("o", "0")
        txt = txt.replace("I", "1").replace("l", "1")
        txt = re.sub(r"[\u200b\s]+", " ", txt)
        return txt.strip()

    for i, l in enumerate(all_lines):
        l_clean = clean_ocr_text(l)

        # Recherche du label (ex: 'TOTAL', 'MONTANT', etc.)
        if re.search(label_pattern, l_clean, re.IGNORECASE):
            found_same = re.findall(montant_regex, l_clean, re.IGNORECASE)
            if found_same:
                # Prend le montant le plus grand sur la ligne (souvent le total TTC)
                return float(max(found_same, key=lambda x: float(x.replace(",", "."))).replace(",", "."))

            # Ligne suivante possible
            if allow_next_line and i + 1 < len(all_lines):
                next_line = clean_ocr_text(all_lines[i + 1])
                found_next = re.findall(montant_regex, next_line, re.IGNORECASE)
                if found_next:
                    return float(max(found_next, key=lambda x: float(x.replace(",", "."))).replace(",", "."))

    # Si rien trouvé, essaie de repérer un montant seul sur une ligne typique de paiement
    for l in all_lines:
        l_clean = clean_ocr_text(l)
        match = re.search(r"(\d+[.,]\d{2})", l_clean)
        if match:
            try:
                return float(match.group(1).replace(",", "."))
            except ValueError:
                continue

    return 0.0


def parse_ticket_metadata(ocr_text: str):
    """
    Analyse un texte OCR de ticket pour extraire les montants (total, paiements, TVA),
    et choisit le montant final par validation croisée.
    """
    lines = [l.strip() for l in ocr_text.split("\n") if l.strip()]

    def normalize_line(l):
        return l.replace("O", "0").replace("o", "0").replace("I", "1").replace("l", "1").strip()

    lines = [normalize_line(l) for l in lines]

    montant_regex = r"(\d{1,5}[.,]\d{1,2})"

    # === MÉTHODE A : Totaux directs (comme avant)
    total_patterns = [
        r"TOTAL\s*TTC", r"TOTAL\s*(A\s*PAYER)?", r"MONTANT\s*(R[EÉ]EL|TTC)?",
        r"NET\s*A\s*PAYER", r"À\s*PAYER", r"TOTAL$", r"TTC"
    ]
    montants_A = []
    for pattern in total_patterns:
        m = get_montant_from_line(pattern, lines)
        if m > 0:
            montants_A.append(round(m, 2))

    # === MÉTHODE B : Somme des paiements (CB, espèces, web, etc.)
    paiement_patterns = [r"CB", r"CARTE", r"ESPECES", r"WEB", r"PAYPAL", r"CHEQUE"]
    montants_B = []
    for l in lines:
        if any(re.search(p, l, re.IGNORECASE) for p in paiement_patterns):
            found = re.findall(montant_regex, l)
            for val in found:
                try:
                    montants_B.append(float(val.replace(",", ".")))
                except:
                    pass
    somme_B = round(sum(montants_B), 2) if montants_B else 0.0

    # === MÉTHODE C : Net + TVA
    net_lines = [l for l in lines if re.search(r"HT|NET", l, re.IGNORECASE)]
    tva_lines = [l for l in lines if re.search(r"TVA|T\.V\.A", l, re.IGNORECASE)]
    total_HT = 0.0
    total_TVA = 0.0
    for l in net_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_HT += float(v.replace(",", "."))
    for l in tva_lines:
        vals = re.findall(montant_regex, l)
        for v in vals:
            total_TVA += float(v.replace(",", "."))
    somme_C = round(total_HT + total_TVA, 2) if total_HT > 0 else 0.0

    # === MÉTHODE D : fallback global (si rien trouvé)
    all_amounts = [float(m.replace(",", ".")) for m in re.findall(montant_regex, ocr_text)]
    montant_fallback = max(all_amounts) if all_amounts else 0.0

    # === VALIDATION CROISÉE
    candidats = [x for x in montants_A + [somme_B, somme_C, montant_fallback] if x > 0]
    freq = {}
    for m in candidats:
        m_rond = round(m, 2)
        freq[m_rond] = freq.get(m_rond, 0) + 1
    if not freq:
        montant_final = 0.0
    else:
        montant_final = max(freq, key=freq.get)  # prend le montant le plus récurrent

    # === Détection de la date (inchangée)
    date_patterns = [
        r"\b\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}\b",
        r"\b\d{1,2}\s*(janv|févr|mars|avr|mai|juin|juil|août|sept|oct|nov|déc)\.?\s*\d{2,4}\b"
    ]
    detected_date = None
    for p in date_patterns:
        match = re.search(p, ocr_text, re.IGNORECASE)
        if match:
            try:
                detected_date = parser.parse(match.group(0), dayfirst=True, fuzzy=True).date().isoformat()
                break
            except:
                continue
    if not detected_date:
        detected_date = datetime.now().date().isoformat()

    # === Lignes clés (pour affichage dans interface)
    key_lines = [
        l for l in lines if any(re.search(p, l, re.IGNORECASE) for p in total_patterns + paiement_patterns)
    ]

    # === Résultat final
    montants_possibles = sorted(set(candidats), reverse=True)
    return {
        "montants_possibles": montants_possibles if montants_possibles else [montant_final],
        "montant": montant_final,
        "date": detected_date,
        "infos": "\n".join(key_lines)
    }


def move_ticket_to_sorted(ticket_path, categorie, sous_categorie):
    """Déplace un ticket traité vers le dossier 'tickets_scannes' classé par catégorie/sous-catégorie.
       Gère automatiquement les doublons en renommant les fichiers si nécessaire."""
    cat_dir = os.path.join(SORTED_DIR, categorie.strip())
    souscat_dir = os.path.join(cat_dir, sous_categorie.strip())
    os.makedirs(souscat_dir, exist_ok=True)

    base_name = os.path.basename(ticket_path)
    dest_path = os.path.join(souscat_dir, base_name)

    # 🔁 Si un fichier du même nom existe déjà, on crée un nom unique
    if os.path.exists(dest_path):
        name, ext = os.path.splitext(base_name)
        counter = 1
        while os.path.exists(dest_path):
            new_name = f"{name}_{counter}{ext}"
            dest_path = os.path.join(souscat_dir, new_name)
            counter += 1

    shutil.move(ticket_path, dest_path)
    st.success(f"✅ Ticket déplacé vers : {dest_path}")


def extract_text_from_pdf(pdf_path):
    """Lit un PDF et renvoie le texte brut."""
    from pdfminer.high_level import extract_text
    try:
        return extract_text(pdf_path)
    except Exception as e:
        st.warning(f"⚠️ Impossible de lire le PDF {pdf_path} ({e})")
        return ""


def parse_uber_pdf(pdf_path: str) -> dict:
    """
    Parseur spécifique pour les PDF Uber.
    Objectif : extraire le montant net (net earnings) et la date de fin de période de facturation.
    Renvoie dict avec clés : montant (float), date (datetime.date), categorie, sous_categorie, source.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {
            "montant": 0.0,
            "date": datetime.now().date(),
            "categorie": "Revenu",
            "sous_categorie": "Uber",
            "source": "PDF Uber"
        }

    # Cherche une période de facturation sous forme "Période de facturation : 01/07/2025 - 31/07/2025"
    date_fin = None
    periode_match = re.search(
        r"P[eé]riode de facturation\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})\s*[\-–]\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
        text,
        re.IGNORECASE
    )
    if periode_match:
        debut_str, fin_str = periode_match.groups()
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_fin = datetime.strptime(fin_str, fmt).date()
                break
            except Exception:
                continue

    # Si non trouvé par pattern, on tente de trouver une date "Période terminée le : 31/07/2025" ou "Period ending 31/07/2025"
    if not date_fin:
        m2 = re.search(
            r"(period ending|p[eé]riode termin[eé]e le|Date de fin)\s*[:\-]?\s*([0-3]?\d[\/\-\.][01]?\d[\/\-\.]\d{2,4})",
            text,
            re.IGNORECASE
        )
        if m2:
            date_str = m2.group(2)
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
                try:
                    date_fin = datetime.strptime(date_str, fmt).date()
                    break
                except Exception:
                    continue

    if not date_fin:
        date_fin = datetime.now().date()

    # Montant net : varie selon le PDF Uber (Net earnings, Total to be paid, etc.)
    # On cherche d'abord des expressions anglaises ou françaises communes
    montant = 0.0
    montant_patterns = [
        r"(?:Net earnings|Net to driver|Total net|Montant net|Net earnings \(driver\))\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})\s*€?",
        r"([\d]{1,3}(?:[ .,]\d{3})*[.,]\d{2})\s*€\s*(?:net|netto|net earnings|to driver)?"
    ]
    for p in montant_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            s = m.group(1).replace(" ", "").replace(".", "").replace(",", ".") if "," in m.group(1) and "." in m.group(1) else m.group(1).replace(",", ".").replace(" ", "")
            try:
                montant = float(s)
                break
            except Exception:
                continue

    # fallback: chercher le dernier montant présent dans le texte (souvent utile si formats variés)
    if montant == 0.0:
        all_amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if all_amounts:
            # souvent le montant net est parmi les derniers montants, on prend le dernier non nul
            for a in reversed(all_amounts):
                try:
                    candidate = float(a.replace(",", "."))
                    if candidate > 0:
                        montant = candidate
                        break
                except:
                    continue

    return {
        "montant": round(montant, 2),
        "date": date_fin,
        "categorie": "Revenu",
        "sous_categorie": "Uber Eats",
        "source": "PDF Uber"
    }


def parse_fiche_paie(pdf_path: str) -> dict:
    """
    Parseur spécifique pour fiche de paie.
    Objectif : trouver la période (ou la date concernée) et le net à payer.
    Renvoie dict similaire à parse_uber_pdf.
    """
    text = extract_text_from_pdf(pdf_path)
    if not text:
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Salaire", "source": "PDF Fiche de paie"}

    # 1) Trouver le net à payer (patterns : NET A PAYER, Net à payer, Net pay, Net salary)
    montant = 0.0
    net_patterns = [
        r"NET\s*A\s*PAYER\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net à payer \(à vous\)\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})",
        r"Net\s*[:\-\–]?\s*([0-9]+[.,][0-9]{2})"  # fallback
    ]
    for p in net_patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                montant = float(m.group(1).replace(",", "."))
                break
            except:
                continue

    # fallback : prendre le dernier montant trouvé, mais prudence
    if montant == 0.0:
        amounts = re.findall(r"(\d+[.,]\d{2})\s*€?", text)
        if amounts:
            # on peut prioriser montants > 100 (supposés être net), sinon prendre le dernier
            candidates = [float(a.replace(",", ".")) for a in amounts]
            bigs = [c for c in candidates if c > 100]  # heuristique : salaire > 100€
            montant = bigs[-1] if bigs else candidates[-1]

    # 2) Trouver la période ou la date : recherche de "période" ou intervalle "01/07/2025 - 31/07/2025"
    date_found = None
    periode_match = re.search(r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\s*[\-–]\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})", text)
    if periode_match:
        # on prend la date de fin comme date du revenu
        fin_str = periode_match.groups()[1]
        for fmt in ("%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"):
            try:
                date_found = datetime.strptime(fin_str, fmt).date()
                break
            except:
                pass

    # autre pattern : "Période du : 01/07/2025 au 31/07/2025" ou "Pour le mois de juillet 2025"
    if not date_found:
        m2 = re.search(r"Pour le mois de\s+([A-Za-zéûà]+)\s+(\d{4})", text, re.IGNORECASE)
        if m2:
            mois_str, annee_str = m2.groups()
            # mapping simple des mois FR (on peut étendre si besoin)
            mois_map = {
                "janvier":1,"février":2,"fevrier":2,"mars":3,"avril":4,"mai":5,"juin":6,
                "juillet":7,"août":8,"aout":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12,"decembre":12
            }
            mois_key = mois_str.lower()
            mois_num = mois_map.get(mois_key)
            if mois_num:
                # on choisit la fin du mois comme date
                from calendar import monthrange
                last_day = monthrange(int(annee_str), mois_num)[1]
                date_found = date(int(annee_str), mois_num, last_day)

    if not date_found:
        # fallback : date d'aujourd'hui
        date_found = datetime.now().date()

    return {
        "montant": round(float(montant), 2),
        "date": date_found,
        "categorie": "Revenu",
        "sous_categorie": "Salaire",
        "source": "PDF Fiche de paie"
    }


def parse_pdf_dispatcher(pdf_path: str, source_type: str) -> dict:
    """
    Dispatcher simple pour choisir le parseur adapté.
    source_type attendu : 'uber', 'fiche_paie', 'ticket' (ou 'auto' pour tentative heuristique).
    """
    stype = source_type.lower().strip()
    if stype in ("uber", "uber_pdf", "uber eats"):
        return parse_uber_pdf(pdf_path)
    elif stype in ("fiche_paie", "fiche de paie", "paye", "salaire"):
        return parse_fiche_paie(pdf_path)
    elif stype in ("ticket", "receipt", "ticket_ocr"):
        # si tu veux parser un PDF ticket (rare), tu peux appeler parse_ticket_metadata en lui passant le texte
        text = extract_text_from_pdf(pdf_path)
        # parse_ticket_metadata attend du texte OCR ; si elle attend un path, adapte
        return parse_ticket_metadata(text)
    elif stype == "auto":
        # heuristique : essaye d'identifier le type en recherchant des mots-clés dans le PDF
        text = extract_text_from_pdf(pdf_path).lower()
        if "uber" in text or "net to driver" in text or "period" in text:
            return parse_uber_pdf(pdf_path)
        if "net a payer" in text or "fiche de paie" in text or "bulletin" in text:
            return parse_fiche_paie(pdf_path)
        # fallback : on renvoie quelque chose générique
        return {"montant": 0.0, "date": datetime.now().date(), "categorie": "Revenu", "sous_categorie": "Inconnu", "source": "PDF Auto"}
    else:
        raise ValueError(f"Source_type inconnu pour parse_pdf_dispatcher: {source_type}")


def _inc(d, recurrence):
    if recurrence == "hebdomadaire":
        return d + relativedelta(weeks=1)
    if recurrence == "mensuelle":
        return d + relativedelta(months=1)
    if recurrence == "annuelle":
        return d + relativedelta(years=1)
    return d  # fallback


def backfill_recurrences_to_today(db_path):
    """
    Pour chaque modèle 'récurrente', génère toutes les occurrences manquantes
    (source='récurrente_auto') jusqu'à aujourd'hui (ou date_fin si elle existe).
    """
    today = date.today()

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) Récupère tous les modèles
    cur.execute("""
       SELECT id, type, categorie, sous_categorie, montant, date, source, recurrence, date_fin
       FROM transactions
       WHERE source='récurrente'
    """)
    models = cur.fetchall()

    for m in models:
        cat = (m["categorie"] or "").strip()
        sous = (m["sous_categorie"] or "").strip()
        rec = (m["recurrence"] or "").strip()
        if not rec:
            continue

        # bornes
        try:
            start = date.fromisoformat(m["date"])
        except Exception:
            continue
        end_limit = None
        if m["date_fin"]:
            try:
                end_limit = date.fromisoformat(m["date_fin"])
            except Exception:
                end_limit = None
        limit = min(today, end_limit) if end_limit else today

        if start > limit:
            continue  # rien à générer encore

        # 2) Dernière occurrence déjà existante
        cur.execute("""
            SELECT MAX(date) as last_date
            FROM transactions
            WHERE source='récurrente_auto'
              AND categorie=? AND sous_categorie=?
              AND recurrence=?
              AND type=?
        """, (cat, sous, rec, m["type"]))
        row = cur.fetchone()
        last = date.fromisoformat(row["last_date"]) if row and row["last_date"] else None

        # 3) Calcule la prochaine date à générer
        if last:
            next_d = _inc(last, rec)
        else:
            # première occurrence = start (et on l'ajoute si <= limit)
            next_d = start

        # 4) Génère tout ce qui manque jusqu'à 'limit'
        to_insert = []
        while next_d <= limit:
            to_insert.append((
                m["type"], cat, sous, float(m["montant"]), next_d.isoformat(),
                "récurrente_auto", rec, m["date_fin"]
            ))
            next_d = _inc(next_d, rec)

        if to_insert:
            cur.executemany("""
                INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source, recurrence, date_fin)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, to_insert)

    conn.commit()
    conn.close()
    
# ==============================
#  🏠 ACCUEIL
# ============================== 
def interface_accueil():
    st.title("🏠 Tableau de Bord Financier")
    
    # Charger les données
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("💰 Aucune transaction enregistrée. Commencez par ajouter vos premières transactions !")
        return
    
    # 🔥 CORRECTION : Conversion des montants et dates
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # 🔥 DÉTERMINER LA PREMIÈRE TRANSACTION
    premiere_date = df["date"].min().date()
    derniere_date = df["date"].max().date()
    
    st.markdown("---")
    st.subheader("🎯 Période d'analyse")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        # Options de période avec date de début automatique
        periode_options = {
            "Depuis le début": "debut",
            "6 derniers mois": 6,
            "3 derniers mois": 3, 
            "12 derniers mois": 12,
            "Personnalisée": "custom"
        }
        periode_choice = st.selectbox("Choisir la période", list(periode_options.keys()))
    
    with col2:
        if periode_choice == "Personnalisée":
            date_debut = st.date_input("Date de début", value=premiere_date)
            date_fin = st.date_input("Date de fin", value=derniere_date)
        elif periode_choice == "Depuis le début":
            date_debut = premiere_date
            date_fin = derniere_date
            st.info(f"📅 Depuis le début\n{date_debut.strftime('%d/%m/%Y')}")
        else:
            mois_retour = periode_options[periode_choice]
            date_debut = max(premiere_date, date.today() - relativedelta(months=mois_retour))
            date_fin = derniere_date
            st.info(f"📅 {date_debut.strftime('%d/%m/%Y')} → {date_fin.strftime('%d/%m/%Y')}")
    
    with col3:
        # 🔥 STATISTIQUES DE PÉRIODE
        duree_mois = max(1, ((date_fin - date_debut).days // 30))
        st.metric(
            "📅 Couverture", 
            f"{duree_mois} mois",
            delta=f"Depuis {premiere_date.strftime('%d/%m/%y')}"
        )
    
    with col4:
        if st.button("🔄 Actualiser"):
            st.rerun()
    
    # Filtrer les données selon la période
    df_periode = df[(df["date"] >= pd.Timestamp(date_debut)) & (df["date"] <= pd.Timestamp(date_fin))]
    
    if df_periode.empty:
        st.warning("📊 Aucune transaction dans la période sélectionnée.")
        return
    
    # 🔥 STATISTIQUES PAR MOIS
    df_mensuel = df_periode.copy()
    df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
    df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")
    
    # Transactions par mois
    transactions_par_mois = df_mensuel.groupby("mois_str").agg({
        "montant": "count",
        "type": lambda x: (x == "revenu").sum()
    }).rename(columns={"montant": "total_transactions", "type": "nb_revenus"})
    
    transactions_par_mois["nb_depenses"] = transactions_par_mois["total_transactions"] - transactions_par_mois["nb_revenus"]
    
    # 🔥 MÉTRIQUES PRINCIPALES AMÉLIORÉES
    st.markdown("---")
    st.subheader("📈 Vue d'Ensemble")
    
    # Calculs des métriques
    total_revenus = df_periode[df_periode["type"] == "revenu"]["montant"].sum()
    total_depenses = df_periode[df_periode["type"] == "dépense"]["montant"].sum()
    solde_periode = total_revenus - total_depenses
    nb_transactions = len(df_periode)
    
    # Métriques avancées
    df_depenses = df_periode[df_periode["type"] == "dépense"]
    df_revenus = df_periode[df_periode["type"] == "revenu"]
    
    nb_depenses = len(df_depenses)
    nb_revenus = len(df_revenus)
    mois_couverts = max(1, ((date_fin - date_debut).days // 30))
    
    # Calculs mensuels
    depenses_mensuelles = total_depenses / mois_couverts
    revenus_mensuels = total_revenus / mois_couverts
    moyenne_depense = df_depenses["montant"].median() if not df_depenses.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        solde_color = "green" if solde_periode >= 0 else "red"
        solde_icon = "📈" if solde_periode >= 0 else "📉"
        st.metric(
            f"{solde_icon} Solde période", 
            f"{solde_periode:+.2f} €",
            delta=f"{solde_periode/mois_couverts:+.0f} €/mois"
        )
    
    with col2:
        st.metric(
            "💸 Dépenses totales", 
            f"{total_depenses:.2f} €",
            delta=f"~{depenses_mensuelles:.0f} €/mois • {nb_depenses} transactions"
        )
    
    with col3:
        st.metric(
            "💹 Revenus totaux", 
            f"{total_revenus:.2f} €",
            delta=f"~{revenus_mensuels:.0f} €/mois • {nb_revenus} transactions"
        )
    
    with col4:
        # 🔥 NOUVEAU : ACTIVITÉ MOYENNE
        transactions_mensuelles = nb_transactions / mois_couverts
        st.metric(
            "📊 Activité moyenne", 
            f"{transactions_mensuelles:.1f}/mois",
            delta=f"{nb_transactions} transactions total"
        )
    
    # 🔥 TABLEAU DES TRANSACTIONS PAR MOIS
    st.markdown("---")
    st.subheader("📅 Activité Mensuelle")
    
    if not transactions_par_mois.empty:
        # Trier par date
        transactions_par_mois = transactions_par_mois.sort_index(
            key=lambda x: pd.to_datetime(x, format='%b %Y')
        )
        
        # Préparer l'affichage
        df_display = transactions_par_mois.reset_index()
        df_display = df_display.rename(columns={
            "mois_str": "Mois",
            "total_transactions": "Total",
            "nb_revenus": "Revenus",
            "nb_depenses": "Dépenses"
        })
        
        # Afficher le tableau
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mois": st.column_config.TextColumn("📅 Mois"),
                "Total": st.column_config.NumberColumn("📊 Total", format="%d"),
                "Revenus": st.column_config.NumberColumn("💹 Revenus", format="%d"),
                "Dépenses": st.column_config.NumberColumn("💸 Dépenses", format="%d")
            }
        )
        
        # 🔥 GRAPHIQUE DE L'ACTIVITÉ MENSUELLE
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Évolution du nombre de transactions**")
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            # Appliquer le thème
            try:
                theme = st.get_option("theme.base")
                is_dark_theme = theme == "dark"
            except:
                is_dark_theme = False
                
            bg_color = "#0E1117" if is_dark_theme else "white"
            text_color = "white" if is_dark_theme else "black"
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            ax.tick_params(colors=text_color)
            ax.xaxis.label.set_color(text_color)
            ax.yaxis.label.set_color(text_color)
            ax.title.set_color(text_color)
            
            # Graphique en barres
            x_pos = np.arange(len(transactions_par_mois.index))
            bar_width = 0.6
            
            bars_total = ax.bar(x_pos, transactions_par_mois["total_transactions"], 
                               bar_width, label="Total", alpha=0.7, color="#4A90E2")
            
            ax.set_ylabel("Nombre de transactions", color=text_color, fontweight='bold')
            ax.set_xlabel("Mois", color=text_color, fontweight='bold')
            ax.set_title("Évolution de l'activité mensuelle", color=text_color, fontweight='bold')
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(transactions_par_mois.index, rotation=45, ha='right', color=text_color)
            ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
        
        with col2:
            st.markdown("**🥧 Répartition Revenus/Dépenses**")
            
            # Calculer les totaux
            total_revenus_count = transactions_par_mois["nb_revenus"].sum()
            total_depenses_count = transactions_par_mois["nb_depenses"].sum()
            
            if total_revenus_count + total_depenses_count > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                
                # Appliquer le thème
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                data = [total_revenus_count, total_depenses_count]
                labels = [f"Revenus\n{total_revenus_count}", f"Dépenses\n{total_depenses_count}"]
                colors = ["#00D4AA", "#FF6B6B"]
                
                wedges, texts, autotexts = ax.pie(
                    data, 
                    labels=labels, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                # Texte adapté au thème
                for text in texts:
                    text.set_color(text_color)
                    text.set_fontweight('bold')
                for autotext in autotexts:
                    autotext.set_color('white')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title("Répartition des transactions", color=text_color, fontweight='bold')
                st.pyplot(fig)
            else:
                st.info("📊 Pas assez de données pour le graphique")
    
    else:
        st.info("📅 Pas assez de données pour l'analyse mensuelle")
    
    # 🔥 INDICATEURS DE SANTÉ FINANCIÈRE
    st.markdown("---")
    st.subheader("💰 Santé Financière")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if total_revenus > 0:
            taux_epargne = (solde_periode / total_revenus) * 100
            
            if taux_epargne >= 20:
                message = "🎉 Excellent"
                couleur = "normal"
            elif taux_epargne >= 10:
                message = "👍 Très bien" 
                couleur = "normal"
            elif taux_epargne >= 0:
                message = "✅ Correct"
                couleur = "off"
            else:
                message = "🚨 Découvert"
                couleur = "inverse"
                
            st.metric(
                "🎯 Taux d'épargne", 
                f"{taux_epargne:.1f}%",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("🎯 Taux d'épargne", "N/A", delta="Aucun revenu")
    
    with col2:
        if total_revenus > 0:
            ratio_depenses = (total_depenses / total_revenus) * 100
            
            if ratio_depenses <= 80:
                message = "✅ Maîtrisé"
                couleur = "normal"
            elif ratio_depenses <= 100:
                message = "⚠️ Limite"
                couleur = "off" 
            else:
                message = "🚨 Dangereux"
                couleur = "inverse"
                
            st.metric(
                "📊 Ratio dépenses", 
                f"{ratio_depenses:.1f}%",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("📊 Ratio dépenses", "N/A", delta="Aucun revenu")
    
    with col3:
        if not df_depenses.empty:
            depense_max = df_depenses["montant"].max()
            
            if total_revenus > 0:
                ratio_max = (depense_max / (total_revenus/mois_couverts)) * 100
                if ratio_max > 50:
                    message = "🚨 Important"
                    couleur = "inverse"
                elif ratio_max > 25:
                    message = "⚠️ Notable"
                    couleur = "off"
                else:
                    message = "✅ Normal"
                    couleur = "normal"
            else:
                message = "💰 Dépense"
                couleur = "normal"
                
            st.metric(
                "🔥 Plus grosse dépense", 
                f"{depense_max:.0f} €",
                delta=message,
                delta_color=couleur
            )
        else:
            st.metric("🔥 Plus grosse dépense", "0 €")
    
    with col4:
        # 🔥 NOUVEAU : TRANSACTIONS PAR MOIS MOYEN
        tx_par_mois = nb_transactions / mois_couverts
        if tx_par_mois > 20:
            message = "📈 Actif"
            couleur = "normal"
        elif tx_par_mois > 10:
            message = "📊 Moyen"
            couleur = "normal"
        else:
            message = "📉 Faible"
            couleur = "off"
            
        st.metric(
            "🔄 Activité moyenne", 
            f"{tx_par_mois:.1f}/mois",
            delta=message,
            delta_color=couleur
        )
    
    # ... (le reste du code avec les graphiques financiers et transactions reste similaire)
    # 🔥 DÉTECTION DU THÈME STREAMLIT
    try:
        theme = st.get_option("theme.base")
        is_dark_theme = theme == "dark"
    except:
        is_dark_theme = False
    
    # 🔥 COULEURS ADAPTATIVES AU THÈME
    if is_dark_theme:
        bg_color = "#0E1117"
        text_color = "white"
        grid_color = "#2E2E2E"
        face_color = "#0E1117"
    else:
        bg_color = "white"
        text_color = "black"
        grid_color = "#E0E0E0"
        face_color = "white"
    
    # Couleurs des données
    couleur_revenus = "#00D4AA"
    couleur_depenses = "#FF6B6B"
    couleur_solde = "#4A90E2"
    
    # 🔥 GRAPHIQUE PRINCIPAL ADAPTÉ AU THÈME
    st.markdown("---")
    st.subheader("📊 Évolution Financière")
    
    # Préparer les données mensuelles
    df_mensuel = df_periode.copy()
    df_mensuel["mois"] = df_mensuel["date"].dt.to_period("M")
    df_mensuel["mois_str"] = df_mensuel["date"].dt.strftime("%b %Y")
    
    # Agréger par mois et type
    df_evolution = df_mensuel.groupby(["mois_str", "type"])["montant"].sum().unstack(fill_value=0)
    df_evolution = df_evolution.reindex(sorted(df_evolution.index, key=lambda x: pd.to_datetime(x, format='%b %Y')))
    
    # Créer le graphique adapté au thème
    if not df_evolution.empty:
        plt.style.use('default')
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Appliquer les couleurs du thème
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        ax.tick_params(colors=text_color)
        ax.xaxis.label.set_color(text_color)
        ax.yaxis.label.set_color(text_color)
        ax.title.set_color(text_color)
        
        bar_width = 0.6
        x_pos = np.arange(len(df_evolution.index))
        
        # Barres de revenus (positives)
        if "revenu" in df_evolution.columns:
            bars_revenus = ax.bar(x_pos, df_evolution["revenu"], bar_width, 
                                  label="Revenus", color=couleur_revenus, alpha=0.9,
                                  edgecolor=text_color, linewidth=0.5)
        
        # Barres de dépenses (négatives)
        if "dépense" in df_evolution.columns:
            bars_depenses = ax.bar(x_pos, -df_evolution["dépense"], bar_width, 
                                   label="Dépenses", color=couleur_depenses, alpha=0.9,
                                   edgecolor=text_color, linewidth=0.5)
        
        # Ligne de tendance du solde
        if "revenu" in df_evolution.columns and "dépense" in df_evolution.columns:
            solde_mensuel = df_evolution.get("revenu", 0) - df_evolution.get("dépense", 0)
            line_solde = ax.plot(x_pos, solde_mensuel, label="Solde", color=couleur_solde, 
                                 marker='o', linewidth=3, markersize=6, markerfacecolor=bg_color,
                                 markeredgecolor=couleur_solde, markeredgewidth=2)
        
        # Personnalisation
        ax.axhline(0, color=text_color, linewidth=1, alpha=0.5)
        ax.set_ylabel("Montant (€)", fontsize=12, fontweight='bold', color=text_color)
        ax.set_xlabel("Mois", fontsize=12, fontweight='bold', color=text_color)
        ax.set_title("Évolution des Revenus et Dépenses", fontsize=14, fontweight='bold', pad=20, color=text_color)
        
        # Légende adaptée
        legend = ax.legend(loc='upper left', frameon=True, fancybox=True, 
                          facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
        
        # Grille adaptée
        ax.grid(True, alpha=0.2, color=grid_color)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(df_evolution.index, rotation=45, ha='right', color=text_color)
        
        # Ajouter les valeurs sur les barres
        def add_value_labels(ax, bars):
            for bar in bars:
                height = bar.get_height()
                if abs(height) > 0:
                    label_color = text_color if abs(height) > max(ax.get_ylim())*0.1 else text_color
                    va = 'bottom' if height > 0 else 'top'
                    y_offset = 10 if height > 0 else -20
                    
                    ax.text(bar.get_x() + bar.get_width()/2., height + y_offset,
                           f'{abs(height):.0f}€', ha='center', va=va,
                           fontweight='bold', fontsize=9, color=label_color)
        
        if "revenu" in df_evolution.columns:
            add_value_labels(ax, bars_revenus)
        if "dépense" in df_evolution.columns:
            add_value_labels(ax, bars_depenses)
        
        # Style des bordures
        for spine in ax.spines.values():
            spine.set_color(text_color)
            spine.set_alpha(0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        
    else:
        st.info("📈 Pas assez de données pour afficher l'évolution mensuelle")
    
    
    # 🔥 RÉPARTITION DES CATÉGORIES ADAPTÉE
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🥧 Dépenses par Catégorie")
        
        depenses_df = df_periode[df_periode["type"] == "dépense"]
        if not depenses_df.empty:
            categories_depenses = depenses_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)
            total_depenses_calc = categories_depenses.sum()
            
            # Filtrer les catégories < 3%
            seuil_minimum = 0.03
            categories_principales = categories_depenses[categories_depenses / total_depenses_calc >= seuil_minimum]
            categories_autres = categories_depenses[categories_depenses / total_depenses_calc < seuil_minimum]
            
            if not categories_autres.empty:
                categories_principales = categories_principales.copy()
                categories_principales["Autres"] = categories_autres.sum()
            
            if not categories_principales.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Appliquer le thème
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                colors = plt.cm.Set3(np.linspace(0, 1, len(categories_principales)))
                wedges, texts, autotexts = ax.pie(
                    categories_principales.values, 
                    labels=categories_principales.index, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                # Texte adapté au thème
                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('white' if is_dark_theme else 'black')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title(f"Dépenses ({len(categories_principales)} catégories)", 
                           color=text_color, fontweight='bold')
                st.pyplot(fig)
                
    with col2:
        st.subheader("📊 Revenus par Catégorie")
        
        revenus_df = df_periode[df_periode["type"] == "revenu"]
        if not revenus_df.empty:
            categories_revenus = revenus_df.groupby("categorie")["montant"].sum().sort_values(ascending=False)
            total_revenus_calc = categories_revenus.sum()
            
            seuil_minimum = 0.03
            categories_principales = categories_revenus[categories_revenus / total_revenus_calc >= seuil_minimum]
            categories_autres = categories_revenus[categories_revenus / total_revenus_calc < seuil_minimum]
            
            if not categories_autres.empty:
                categories_principales = categories_principales.copy()
                categories_principales["Autres"] = categories_autres.sum()
            
            if not categories_principales.empty:
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Appliquer le thème
                fig.patch.set_facecolor(bg_color)
                ax.set_facecolor(bg_color)
                
                colors = plt.cm.Pastel1(np.linspace(0, 1, len(categories_principales)))
                wedges, texts, autotexts = ax.pie(
                    categories_principales.values, 
                    labels=categories_principales.index, 
                    autopct='%1.1f%%', 
                    startangle=90,
                    colors=colors,
                    wedgeprops={'edgecolor': bg_color, 'linewidth': 2}
                )
                
                # Texte adapté au thème
                for text in texts:
                    text.set_color(text_color)
                for autotext in autotexts:
                    autotext.set_color('black')
                    autotext.set_fontweight('bold')
                
                ax.axis('equal')
                ax.set_title(f"Revenus ({len(categories_principales)} catégories)", 
                           color=text_color, fontweight='bold')
                st.pyplot(fig)
    
    # 🔥 PLUS GROSSES TRANSACTIONS (REVENUS ET DÉPENSES)
    st.markdown("---")
    st.subheader("🎯 Transactions Importantes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**💸 Top 5 Dépenses**")
        top_depenses = df_periode[df_periode["type"] == "dépense"].nlargest(5, "montant")
        
        if not top_depenses.empty:
            for idx, trans in top_depenses.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                        if trans.get('description'):
                            st.caption(f"📝 {trans['description']}")
                    with col_b:
                        st.markdown(f"<h4 style='color: #FF6B6B; text-align: right;'>-{trans['montant']:.2f} €</h4>", 
                                  unsafe_allow_html=True)
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                    st.markdown("---")
        else:
            st.info("Aucune dépense significative")
    
    with col2:
        st.markdown("**💹 Top 5 Revenus**")
        top_revenus = df_periode[df_periode["type"] == "revenu"].nlargest(5, "montant")
        
        if not top_revenus.empty:
            for idx, trans in top_revenus.iterrows():
                with st.container():
                    col_a, col_b = st.columns([3, 2])
                    with col_a:
                        st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                        if trans.get('description'):
                            st.caption(f"📝 {trans['description']}")
                    with col_b:
                        st.markdown(f"<h4 style='color: #00D4AA; text-align: right;'>+{trans['montant']:.2f} €</h4>", 
                                  unsafe_allow_html=True)
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                    st.markdown("---")
        else:
            st.info("Aucun revenu significatif")
    
    # 🔥 10 DERNIÈRES TRANSACTIONS
    st.markdown("---")
    st.subheader("🕒 10 Dernières Transactions")
    
    dernieres = df_periode.head(5)
    
    if not dernieres.empty:
        for idx, trans in dernieres.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 2])
                
                with col1:
                    icon = "🟢" if trans["type"] == "revenu" else "🔴"
                    st.write(icon)
                
                with col2:
                    st.write(f"**{trans['categorie']}** → {trans['sous_categorie']}")
                    if trans.get('description'):
                        st.caption(f"📝 {trans['description']}")
                    st.caption(f"📅 {trans['date'].strftime('%d/%m/%Y')}")
                
                with col3:
                    montant_color = "#00D4AA" if trans["type"] == "revenu" else "#FF6B6B"
                    montant_prefix = "+" if trans["type"] == "revenu" else "-"
                    st.markdown(f"<h4 style='color: {montant_color}; text-align: right;'>{montant_prefix}{trans['montant']:.2f} €</h4>", 
                              unsafe_allow_html=True)
                
                st.markdown("---")
    else:
        st.info("Aucune transaction récente")   
# ==============================
# ⚙️ TRAITEMENT DES TICKETS ET REVENUS
# ==============================
def process_all_tickets_in_folder():
    """
    Traite tous les tickets du dossier TO_SCAN_DIR :
    - OCR
    - extraction montants / date / infos clés
    - confirmation utilisateur
    - insertion en base + déplacement
    """
    st.subheader("🧾 Traitement des tickets à scanner")

    tickets = [f for f in os.listdir(TO_SCAN_DIR) if f.lower().endswith((".jpg", ".png", ".jpeg", ".pdf"))]
    if not tickets:
        st.info("📂 Aucun ticket à scanner pour le moment.")
        return

    st.write(f"🧮 {len(tickets)} ticket(s) détecté(s) dans le dossier à scanner.")

    for ticket_file in tickets:
        ticket_path = os.path.join(TO_SCAN_DIR, ticket_file)
        st.markdown("---")
        st.markdown(f"### 🧾 {ticket_file}")

        # --- OCR selon format ---
        try:
            if ticket_file.lower().endswith(".pdf"):
                text = extract_text_from_pdf(ticket_path)
                # 👉 Affichage PDF : on montre juste le texte OCR
                with st.expander(f"📄 Texte OCR extrait du PDF : {ticket_file}", expanded=False):
                    st.text_area("Contenu OCR :", text, height=200)
            else:
                # 👉 Affichage image : on montre l'image + texte OCR
                text = full_ocr(ticket_path, show_ticket=True)
        except Exception as e:
            st.error(f"❌ Erreur OCR sur {ticket_file} : {e}")
            continue

        # --- Analyse du texte OCR ---
        data = parse_ticket_metadata(text)

        montant_final = data.get("montant", 0.0)
        montants_possibles = data.get("montants_possibles", [montant_final])
        detected_date = data.get("date", datetime.now().date().isoformat())
        key_info = data.get("infos", "")
        
        # --- Déduction de la catégorie et sous-catégorie à partir du nom de fichier ---
        name = os.path.splitext(ticket_file)[0]
        parts = name.split(".")[1:]  # Ignore la première partie (ex: le2)

        if len(parts) >= 2:
            categorie_auto = parts[1].capitalize()
            sous_categorie_auto = parts[0].capitalize()
        elif len(parts) == 1:
            categorie_auto = parts[0].capitalize()
            sous_categorie_auto = "Autre"
        else:
            categorie_auto = "Divers"
            sous_categorie_auto = "Autre"

        # --- Affichage automatique ---
        st.markdown(f"🧠 **Catégorie auto-détectée :** {categorie_auto} → {sous_categorie_auto}")

        # --- Affichage des infos clés OCR ---
        with st.expander("📜 Aperçu OCR (lignes clés)"):
            st.text(key_info)

        # --- Interface de validation du ticket ---
        with st.form(f"form_{ticket_file}"):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale", categorie_auto)
                sous_categorie = st.text_input("Sous-catégorie (ex: supermarché, restaurant...)", sous_categorie_auto)
            with col2:
                montant_select = st.selectbox(
                    "Montant détecté",
                    options=[round(m, 2) for m in montants_possibles],
                    index=0 if montants_possibles else 0
                )
                montant_corrige = st.number_input(
                    "💶 Corriger le montant si besoin (€)",
                    value=float(montant_select) if montant_select else 0.0,
                    min_value=0.0,
                    step=0.01
                )
                date_ticket = st.date_input("📅 Date du ticket", datetime.fromisoformat(detected_date))

            valider = st.form_submit_button("✅ Valider et enregistrer ce ticket")

        # --- Validation / sauvegarde ---
        if valider:
            if not categorie or montant_corrige <= 0:
                st.error("⚠️ Catégorie ou montant invalide.")
                continue

            # Ajout à la base de données
            insert_transaction_batch([{
                "type": "dépense",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant_corrige,
                "date": date_ticket.isoformat(),
                "source": "OCR"
            }])

            # Déplacement du ticket classé
            move_ticket_to_sorted(ticket_path, categorie, sous_categorie)

            st.success(f"💾 Ticket {ticket_file} enregistré avec succès ({montant_corrige:.2f} €).")


def interface_process_all_revenues_in_folder():
    st.subheader("📥 Scanner et enregistrer tous les revenus depuis le dossier")

    src_folder = REVENUS_A_TRAITER 

    # --- Étape 1 : scanner les fichiers une seule fois ---
    if "revenus_data" not in st.session_state:
        st.session_state["revenus_data"] = []

    if st.button("🚀 Scanner tous les revenus") and not st.session_state["revenus_data"]:
        pdfs = [os.path.join(root, f)
                for root, _, files in os.walk(src_folder)
                for f in files if f.lower().endswith(".pdf")]

        if not pdfs:
            st.warning("📂 Aucun PDF de revenu trouvé dans le dossier.")
            return

        data_list = []
        for pdf_path in pdfs:
            # Identifier le sous-dossier utile
            parent_folder = os.path.basename(os.path.dirname(pdf_path))

            # Si le parent est "revenus_a_traiter", on ignore
            if parent_folder.lower() in ["revenus_a_traiter", "revenus_traité", "revenus_traités"]:
                sous_dossier = "Revenus"
            else:
                sous_dossier = parent_folder

            # Parsing selon type
            try:
                if sous_dossier.lower() == "uber":
                    parsed = parse_uber_pdf(pdf_path)
                else:
                    parsed = parse_fiche_paie(pdf_path)
            except Exception:
                parsed = {"montant": 0.0, "date": datetime.today().date(), "source": "PDF Auto"}

            # Calcul du mois en français
            date_val = parsed.get("date", datetime.today().date())
            if isinstance(date_val, str):
                date_val = datetime.fromisoformat(date_val).date()
            mois_nom = numero_to_mois(f"{date_val.month:02d}")

            data_list.append({
                "file": os.path.basename(pdf_path),
                "path": pdf_path,
                "categorie": sous_dossier,
                "sous_categorie": mois_nom,
                "montant": parsed.get("montant", 0.0),
                "date": date_val,
                "source":"PDF"
            })

        st.session_state["revenus_data"] = data_list
        st.success("✅ Revenus scannés avec succès. Tu peux maintenant les modifier avant validation.")

    # --- Étape 2 : affichage et édition persistante ---
    if st.session_state.get("revenus_data"):
        updated_list = []
        for idx, data in enumerate(st.session_state["revenus_data"]):
            st.markdown("---")
            st.write(f"📄 {data['file']}")
            col1, col2 = st.columns(2)
            with col1:
                cat = st.text_input(f"Catégorie ({data['file']})", value=data["categorie"], key=f"rev_cat_{idx}")
                souscat = st.text_input(f"Sous-catégorie ({data['file']})", value=data["sous_categorie"], key=f"rev_souscat_{idx}")
            with col2:
                montant_str = f"{data['montant']:.2f}" if data["montant"] else ""
                montant_edit = st.text_input(f"Montant (€) ({data['file']})", value=montant_str, key=f"rev_montant_{idx}")
                date_edit = st.date_input(f"Date ({data['file']})", value=data["date"], key=f"rev_date_{idx}")

            try:
                montant_val = float(montant_edit.replace(",", "."))
            except ValueError:
                montant_val = 0.0

            updated_list.append({
                "file": data["file"],
                "path": data["path"],
                "categorie": cat.strip(),
                "sous_categorie": souscat.strip(),
                "montant": montant_val,
                "date": date_edit,
                "source": data["source"]
            })

        st.session_state["revenus_data"] = updated_list

        st.markdown("---")
        st.warning("⚠️ Vérifie bien les informations avant de confirmer l'enregistrement.")

        # --- Étape 3 : validation et insertion ---
        if st.button("✅ Confirmer et enregistrer tous les revenus"):
            conn = get_db_connection()
            cursor = conn.cursor()

            for data in st.session_state["revenus_data"]:
                cursor.execute("""
                    INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "revenu",
                    data["categorie"],
                    data["sous_categorie"],
                    data["montant"],
                    data["date"].isoformat(),
                    data["source"]
                ))

                # Déplacement du fichier — tout reste centralisé dans /data
                target_dir = os.path.join(REVENUS_TRAITES, data["categorie"], data["sous_categorie"])
                os.makedirs(target_dir, exist_ok=True)

                # On déplace depuis /data/revenus_a_traiter → /data/revenus_traités/...
                shutil.move(data["path"], os.path.join(target_dir, data["file"]))

            conn.commit()
            conn.close()
            st.success("🎉 Tous les revenus ont été enregistrés et rangés avec succès !")
            st.session_state.pop("revenus_data")

# =============================
#   TRANSACTION MANUELLE
# ✍️ AJOUTER UNE TRANSACTION MANUELLE
# =============================
TRANSACTIONS_CSV = Path(BASE_DIR)/Path(DATA_DIR)/"transactions.csv"
COLUMNS = ["date", "categorie", "sous_categorie", "description", "montant", "type"]

# ==========================
# 🧩 Fonction principale
# ==========================
def interface_transactions_unifiee():
    st.subheader("📊 Gestion des transactions (manuel + CSV)")

    # --- Vérification / création du fichier principal ---
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(TRANSACTIONS_CSV):
        pd.DataFrame(columns=COLUMNS).to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")
        st.info("🆕 Fichier `transactions.csv` créé automatiquement.")

    # --- Charger la base CSV existante ---
    try:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    except UnicodeDecodeError:
        df_base = pd.read_csv(TRANSACTIONS_CSV, encoding="ISO-8859-1")

    # --- Charger les transactions déjà présentes dans la base SQLite ---
    conn = get_db_connection()
    df_sqlite = pd.read_sql_query("""
        SELECT date, categorie, sous_categorie, description, montant, type, source, recurrence
        FROM transactions
    """, conn)
    conn.close()

    st.markdown("#### 📥 Importer un ou plusieurs fichiers CSV de transactions")
    st.info("Les colonnes doivent être écrites sous ce format : `date`, `categorie`, `sous_categorie`, `description`, `montant`, `type`")
    st.info("💡 La colonne `description` peut être vide.")

    uploaded_files = st.file_uploader(
        "Glissez un ou plusieurs fichiers CSV ici",
        type=["csv"],
        accept_multiple_files=True
    )

    all_new_rows = []

    if uploaded_files:
        for uploaded in uploaded_files:
            raw_data = uploaded.read()
            encoding = detect(raw_data)["encoding"] or "utf-8"
            uploaded.seek(0)

            try:
                df_new = pd.read_csv(uploaded, encoding=encoding)
                if "date" in df_new.columns:
                    df_new["date"] = df_new["date"].apply(normaliser_date)
                if "montant" in df_new.columns:
                    df_new["montant"] = df_new["montant"].apply(nettoyer_montant)
            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture de {uploaded.name} : {e}")
                continue

            # Vérifier que les colonnes essentielles sont présentes
            required_cols = ["date", "categorie", "sous_categorie", "description", "montant"]
            missing = [c for c in required_cols if c not in df_new.columns]
            if missing:
                st.error(f"❌ {uploaded.name} : colonnes manquantes ({', '.join(missing)})")
                st.error("Vérifiez bien l'orthographe des colonnes.")
                continue

            all_new_rows.append(df_new)
            st.success(f"✅ {uploaded.name} importé avec succès ({len(df_new)} lignes).")

        if all_new_rows:
            # Fusion de tous les fichiers importés
            df_new_total = pd.concat(all_new_rows, ignore_index=True)

            # 🔹 Nettoyage texte
            for df in [df_base, df_new_total, df_sqlite]:
                for col in ["categorie", "sous_categorie", "description"]:
                    if col in df.columns:
                        df[col] = df[col].fillna("").astype(str).str.strip().str.lower()

            # 🔹 Harmoniser les types de la colonne 'montant'
            for df in [df_new_total, df_sqlite]:
                if "montant" in df.columns:
                    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)

            # 🔹 Supprimer doublons internes (dans fichiers importés)
            df_new_total = df_new_total.drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            )

            # 🔹 Fusion avec CSV existant
            df_combined = pd.concat([df_base, df_new_total], ignore_index=True)

            # 🔹 Détection doublons internes
            duplicates_internal = df_combined.duplicated(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep=False
            )
            df_dupes_internal = df_combined[duplicates_internal]

            # 🔹 Détection doublons externes (déjà dans SQLite)
            df_merged = df_new_total.merge(
                df_sqlite,
                on=["date", "montant", "categorie", "sous_categorie", "description"],
                how="left",
                indicator=True
            )
            df_dupes_sqlite = df_merged[df_merged["_merge"] != "left_only"]

            # 🔹 On garde uniquement les vraies nouvelles transactions
            df_new_clean = df_merged[df_merged["_merge"] == "left_only"].drop(columns=["_merge"])

            # 🔹 Affichage des doublons détectés
            if not df_dupes_internal.empty or not df_dupes_sqlite.empty:
                st.warning("⚠️ Doublons détectés :")
                if not df_dupes_internal.empty:
                    st.caption("🔁 Dans les fichiers importés / CSV local :")
                    st.dataframe(df_dupes_internal)
                if not df_dupes_sqlite.empty:
                    st.caption("🗄️ Déjà présents dans la base SQLite :")
                    st.dataframe(df_dupes_sqlite)

                keep_dupes = st.radio(
                    "Souhaitez-vous quand même conserver les doublons internes ?",
                    ["Non", "Oui"],
                    horizontal=True,
                    key="keep_dupes_choice"
                )
            else:
                keep_dupes = "Non"

            # 🔹 Nettoyage final selon choix
            if keep_dupes == "Non":
                df_final = df_combined.drop_duplicates(
                    subset=["date", "montant", "categorie", "sous_categorie", "description"],
                    keep="first"
                )
            else:
                df_final = df_combined

            # --- Sauvegarde CSV ---
            df_final.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            # --- Insertion SQLite ---
            if not df_new_clean.empty:
                if "type" not in df_new_clean.columns:
                    st.warning("⚠️ Colonne 'type' absente — les lignes seront marquées comme 'dépense'.")
                    df_new_clean["type"] = "dépense"

                for _, row in df_new_clean.iterrows():
                    insert_transaction({
                        "type": str(row.get("type", "dépense")).strip().lower(),
                        "categorie": str(row["categorie"]).strip().lower(),
                        "sous_categorie": str(row.get("sous_categorie", "")).strip().lower(),
                        "description": str(row.get("description", "")).strip(),
                        "montant": float(row["montant"]),
                        "date": row["date"],
                        "source": "import_csv"
                    })
                st.success(f"✅ {len(df_new_clean)} nouvelle(s) transaction(s) ajoutée(s) à la base.")
            else:
                st.info("ℹ️ Aucune nouvelle transaction à insérer (toutes déjà présentes).")

    # ==========================
    # ✍️ Ajout manuel
    # ==========================
    st.markdown("---")
    st.markdown("#### ✍️ Ajouter manuellement une transaction")

    with st.form("add_manual"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date_tr = st.date_input("Date", value=date.today())
            type_tr = st.selectbox("Type", ["dépense", "revenu"])
        with col2:
            cat = st.text_input("Catégorie principale")
            sous_cat = st.text_input("Sous-catégorie")
        with col3:
            montant = st.number_input("Montant (€)", min_value=0.0, step=0.01, format="%.2f")
            desc = st.text_input("Description")

        valider = st.form_submit_button("💾 Ajouter la transaction")

    if valider:
        if not cat or montant <= 0:
            st.error("⚠️ Veuillez entrer au moins une catégorie et un montant valide.")
        else:
            new_line = pd.DataFrame([{
                "date": date_tr.isoformat(),
                "categorie": cat.strip().lower(),
                "sous_categorie": sous_cat.strip().lower(),
                "description": desc.strip(),
                "montant": float(montant),
                "type": type_tr,
                "source": "manuel"
            }])

            df_updated = pd.concat([df_base, new_line], ignore_index=True).drop_duplicates(
                subset=["date", "montant", "categorie", "sous_categorie", "description"],
                keep="first"
            ).reset_index(drop=True)

            df_updated.to_csv(TRANSACTIONS_CSV, index=False, encoding="utf-8")

            insert_transaction({
                "type": type_tr,
                "categorie": cat.strip().lower(),
                "sous_categorie": sous_cat.strip().lower(),
                "description": desc.strip(),
                "montant": float(montant),
                "date": date_tr.isoformat(),
                "source": "import_csv"
            })

            st.success(f"✅ Transaction ajoutée ({type_tr}) : {cat} — {montant:.2f} €")

    # ==========================
    # 📥 Téléchargement du CSV
    # ==========================
    df_latest = pd.read_csv(TRANSACTIONS_CSV, encoding="utf-8")
    csv_buf = BytesIO()
    csv_buf.write(df_latest.to_csv(index=False).encode("utf-8"))

    st.download_button(
        label="⬇️ Télécharger le fichier CSV complet",
        data=csv_buf.getvalue(),
        file_name="transactions.csv",
        mime="text/csv"
    )


# =============================
# 🔁 AJOUTER UNE TRANSACTION RÉCURRENTE
# =============================
def interface_transaction_recurrente():
    st.subheader("🔁 Ajouter une dépense récurrente")

    with st.form("ajouter_transaction_recurrente", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            categorie = st.text_input("Catégorie principale (ex: logement, assurance, abonnement)")
            sous_categorie = st.text_input("Sous-catégorie (ex: EDF, Netflix, Loyer)")
            montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
        with col2:
            recurrence = st.selectbox("Fréquence", ["hebdomadaire", "mensuelle", "annuelle"])
            date_debut = st.date_input("Date de début", date.today())
            date_fin = st.date_input("Date de fin (facultatif)", None)
        submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

    if submit_btn:
        if not categorie or montant <= 0:
            st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
            return

        safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
        safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

        # Enregistrement modèle + occurrences
        today = date.today()
        occurrences = []
        current_date = date_debut
        while current_date <= today:
            occurrences.append(current_date)
            if recurrence == "hebdomadaire":
                current_date += timedelta(weeks=1)
            elif recurrence == "mensuelle":
                current_date += relativedelta(months=1)
            elif recurrence == "annuelle":
                current_date += relativedelta(years=1)
            if date_fin and current_date > date_fin:
                break

        transactions = [
            # modèle
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": date_debut.isoformat(),
                "source": "récurrente",
                "recurrence": recurrence,
                "date_fin": date_fin.isoformat() if date_fin else ""
            }
        ] + [
            # occurrences passées
            {
                "type": "dépense",
                "categorie": safe_categorie,
                "sous_categorie": safe_sous_categorie,
                "montant": montant,
                "date": d.isoformat(),
                "source": "récurrente_auto",
                "recurrence": recurrence
            } for d in occurrences
        ]

        insert_transaction_batch(transactions)
        st.success(f"✅ Transaction récurrente ({recurrence}) enregistrée.")
        st.info(f"{len(occurrences)} occurrence(s) passée(s) ajoutée(s).")


# ==============================
# 💼 INTERFACE AJOUTER UN REVENU
# ==============================
def interface_ajouter_revenu():
    st.subheader("💼 Ajouter un revenu")

    mode = st.selectbox(
        "Choisir le mode d'ajout du revenu :",
        ["Sélectionner...", "Scanner depuis le dossier", "Ajouter manuellement", "Revenu récurrent"]
    )

    # =============================
    # 1️⃣ Scanner depuis le dossier
    # =============================
    if mode == "Scanner depuis le dossier":
        interface_process_all_revenues_in_folder()

    # =============================
    # 2️⃣ Ajouter un revenu manuel
    # =============================
    elif mode == "Ajouter manuellement":
        with st.form("ajouter_revenu_manuel", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Uber, Animation, Salaire)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
            with col2:
                montant = st.number_input("Montant (€)", min_value=0.0, format="%.2f", step=0.01)
                date_revenu = st.date_input("Date du revenu", date.today())

            submit_btn = st.form_submit_button("💾 Enregistrer le revenu")

        if submit_btn:
            if not categorie or montant <= 0:
                st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
                return

            insert_transaction_batch([{
                "type": "revenu",
                "categorie": categorie.strip(),
                "sous_categorie": sous_categorie.strip(),
                "montant": montant,
                "date": date_revenu.isoformat(),
                "source": "manuel"
            }])
            st.success("✅ Revenu manuel ajouté avec succès !")

    # =============================
    # 3️⃣ Revenu récurrent
    # =============================
    elif mode == "Revenu récurrent":
        with st.form("ajouter_revenu_recurrent", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                categorie = st.text_input("Catégorie principale (ex: Salaire, Bourse, CAF)")
                sous_categorie = st.text_input("Sous-catégorie (ex: septembre, octobre, etc.)")
                montant = st.number_input("Montant du revenu (€)", min_value=0.0, format="%.2f", step=0.01)
            with col2:
                recurrence = st.selectbox("Fréquence", ["mensuelle", "hebdomadaire", "annuelle"])
                date_debut = st.date_input("Date de début", date.today())
                date_fin = st.date_input("Date de fin (facultatif)", None)

            submit_btn = st.form_submit_button("💾 Enregistrer la récurrence")

        if submit_btn:
            if not categorie or montant <= 0:
                st.error("⚠️ Veuillez entrer une catégorie et un montant valide.")
                return

            safe_categorie = re.sub(r'[<>:"/\\|?*]', "_", categorie.strip())
            safe_sous_categorie = re.sub(r'[<>:"/\\|?*]', "_", sous_categorie.strip()) if sous_categorie else ""

            today = date.today()
            occurrences = []
            current_date = date_debut
            while current_date <= today:
                occurrences.append(current_date)
                if recurrence == "hebdomadaire":
                    current_date += timedelta(weeks=1)
                elif recurrence == "mensuelle":
                    current_date += relativedelta(months=1)
                elif recurrence == "annuelle":
                    current_date += relativedelta(years=1)
                if date_fin and current_date > date_fin:
                    break

            transactions = [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": date_debut.isoformat(), "source": "récurrente", "recurrence": recurrence,
                 "date_fin": date_fin.isoformat() if date_fin else ""}
            ] + [
                {"type": "revenu", "categorie": safe_categorie, "sous_categorie": safe_sous_categorie,
                 "montant": montant, "date": d.isoformat(), "source": "récurrente_auto", "recurrence": recurrence}
                for d in occurrences
            ]
            insert_transaction_batch(transactions)
            st.success(f"✅ Revenu récurrent ({recurrence}) ajouté avec succès.")
            st.info(f"{len(occurrences)} versement(s) passé(s) ajouté(s).")


# =============================
# 🔁 GERER LES RECURRENCES
# =============================
def interface_gerer_recurrences():
    st.subheader("🔁 Gérer les transactions récurrentes")
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE source='récurrente_auto' ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("Aucune transaction récurrente trouvée.")
        return

    st.dataframe(df, use_container_width=True)
    selected_id = st.selectbox("Sélectionner une récurrence à modifier :", df["id"].tolist())

    if selected_id:
        selected = df[df["id"] == selected_id].iloc[0]
        st.markdown(f"### 🧾 {selected['categorie']} → {selected['sous_categorie']}")
        new_montant = st.number_input("Montant", value=float(selected["montant"]), step=0.01)
        new_recurrence = st.selectbox("Récurrence", ["hebdomadaire", "mensuelle", "annuelle"], 
                                     index=["hebdomadaire","mensuelle","annuelle"].index(selected["recurrence"]))
        new_date_fin = st.date_input("Date de fin", value=date.today() if not selected["date_fin"] else datetime.fromisoformat(selected["date_fin"]).date())
        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Enregistrer les modifications"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE transactions SET montant=?, recurrence=?, date_fin=? WHERE id=?", 
                             (new_montant, new_recurrence, new_date_fin.isoformat(), selected_id))
                conn.commit()
                conn.close()
                st.success("✅ Récurrence mise à jour avec succès.")

        with col2:
            if st.button("🗑️ Supprimer cette récurrence et toutes ses occurrences"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM transactions WHERE (source LIKE 'récurrente%' AND categorie=? AND sous_categorie=?)", 
                             (selected["categorie"], selected["sous_categorie"]))
                conn.commit()
                conn.close()
                st.success("🗑️ Récurrence supprimée entièrement.")


# =============================
# 🛠️ GERER LES TRANSACTIONS
# =============================
def interface_gerer_transactions():
    st.subheader("🛠️ Gérer les transactions (modifier ou supprimer)")

    conn = get_db_connection()
    df_all = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df_all.empty:
        st.info("Aucune transaction à gérer pour le moment.")
        return

    # 🔥 CORRECTION : Convertir la colonne date en datetime pour l'édition
    df_all['date'] = pd.to_datetime(df_all['date']).dt.date

    # 🔥 CORRECTION : Utiliser des clés uniques pour les filtres
    type_filter = st.selectbox("Type", ["Toutes", "revenu", "dépense"], key="type_filtre_gerer_unique")
    
    # Filtrer les catégories disponibles selon le type sélectionné
    df_for_cat = df_all.copy()
    if type_filter != "Toutes":
        df_for_cat = df_for_cat[df_for_cat["type"] == type_filter]
    
    cat_filter = st.selectbox("Catégorie", ["Toutes"] + sorted(df_for_cat["categorie"].dropna().unique().tolist()), key="cat_filtre_gerer_unique")
    
    # Filtrer les sous-catégories disponibles selon la catégorie sélectionnée
    df_for_souscat = df_for_cat.copy()
    if cat_filter != "Toutes":
        df_for_souscat = df_for_souscat[df_for_souscat["categorie"] == cat_filter]
    
    souscat_filter = st.selectbox("Sous-catégorie", ["Toutes"] + sorted(df_for_souscat["sous_categorie"].dropna().unique().tolist()), key="souscat_filtre_gerer_unique")

    # Appliquer les filtres pour l'affichage
    df = df_all.copy()
    if type_filter != "Toutes": 
        df = df[df["type"] == type_filter]
    if cat_filter != "Toutes": 
        df = df[df["categorie"] == cat_filter]
    if souscat_filter != "Toutes": 
        df = df[df["sous_categorie"] == souscat_filter]

    if df.empty:
        st.warning("Aucune transaction trouvée avec ces filtres.")
        return

    # 🔥 CORRECTION : Ajouter un message clair
    st.markdown("---")
    st.info(f"💡 **{len(df)} transaction(s) trouvée(s)** - Modifie les valeurs directement ou coche les lignes à supprimer.")
    
    # Ajouter colonne de suppression
    df["🗑️ Supprimer"] = False
    
    # 🔥 CORRECTION : Configuration sans DateColumn pour éviter l'erreur de type
    df_edit = st.data_editor(
        df, 
        use_container_width=True, 
        num_rows="fixed", 
        key="editor_transactions_unique",
        hide_index=True,
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "type": st.column_config.SelectboxColumn("Type", options=["dépense", "revenu"]),
            "categorie": st.column_config.TextColumn("Catégorie"),
            "sous_categorie": st.column_config.TextColumn("Sous-catégorie"),
            "description": st.column_config.TextColumn("Description"),
            "montant": st.column_config.NumberColumn("Montant (€)", format="%.2f"),
            "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
            "source": st.column_config.TextColumn("Source", disabled=True),
            "recurrence": st.column_config.TextColumn("Récurrence", disabled=True),
            "date_fin": st.column_config.TextColumn("Date fin", disabled=True),
            "🗑️ Supprimer": st.column_config.CheckboxColumn("🗑️ Supprimer")
        }
    )

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Enregistrer les modifications", type="primary"):
            conn = get_db_connection()
            cursor = conn.cursor()
            modified_count = 0
            
            # 🔥 CORRECTION : Comparer avec le DataFrame original pour détecter les changements
            for idx, row in df_edit.iterrows():
                original_row = df[df["id"] == row["id"]].iloc[0]
                
                # Vérifier si des changements ont été faits (sauf la colonne de suppression)
                has_changes = False
                for col in ["categorie", "sous_categorie", "description", "montant", "date", "type"]:
                    if str(row[col]) != str(original_row[col]):
                        has_changes = True
                        break
                
                if has_changes:
                    # 🔥 CORRECTION : Convertir la date en string ISO pour SQLite
                    date_str = row["date"].isoformat() if hasattr(row["date"], 'isoformat') else str(row["date"])
                    
                    cursor.execute("""
                        UPDATE transactions
                        SET type=?, categorie=?, sous_categorie=?, description=?, montant=?, date=?
                        WHERE id=?
                    """, (
                        row["type"],
                        row["categorie"], 
                        row["sous_categorie"], 
                        row["description"], 
                        float(row["montant"]), 
                        date_str, 
                        row["id"]
                    ))
                    modified_count += 1

            conn.commit()
            conn.close()
            
            if modified_count > 0:
                st.success(f"✅ {modified_count} transaction(s) modifiée(s) avec succès.")
                st.rerun()
            else:
                st.info("ℹ️ Aucune modification détectée.")

    with col2:
        if st.button("🚮 Supprimer les transactions cochées", type="secondary"):
            # 🔥 CORRECTION : Vérifier que la colonne existe avant de filtrer
            if "🗑️ Supprimer" in df_edit.columns:
                to_delete = df_edit[df_edit["🗑️ Supprimer"] == True]
            else:
                to_delete = pd.DataFrame()
            
            if not to_delete.empty:
                conn = get_db_connection()
                cursor = conn.cursor()
                for _, row in to_delete.iterrows():
                    cursor.execute("DELETE FROM transactions WHERE id=?", (row["id"],))
                conn.commit()
                conn.close()
                st.success(f"🗑️ {len(to_delete)} transaction(s) supprimée(s) avec succès.")
                st.rerun()
            else:
                st.warning("⚠️ Coche au moins une transaction avant de supprimer.")



# =============================
# 📊 VOIR TOUTES LES TRANSACTIONS
# =============================
def interface_voir_transactions():
    st.subheader("📊 Voir toutes les transactions")
    
    # ✅ Backfill automatique avant de charger le tableau
    backfill_recurrences_to_today(DB_PATH)

    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()

    if df.empty:
        st.info("Aucune transaction enregistrée pour le moment.")
        return

    # 🔥 CORRECTION : CONVERTIR LES MONTANTS EN NUMÉRIQUE
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)

    # 🔥 FILTRES SIMPLIFIÉS EN HAUT
    st.markdown("### 🎯 Filtres rapides")
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
    
    with col1:
        type_filter = st.selectbox("**Type**", ["Toutes", "revenu", "dépense"])
        
    with col2:
        categories = ["Toutes"] + sorted(df["categorie"].dropna().unique().tolist())
        cat_filter = st.selectbox("**Catégorie**", categories)
        
    with col3:
        filtre_documents = st.selectbox(
            "**Documents**",
            ["Tous", "🧾 Tickets", "💼 Bulletins", "📄 Factures", "📝 Sans docs"]
        )
    
    with col4:
        # Option pour limiter l'affichage
        limit_display = st.checkbox("📋 5 dernières seulement", value=True)

    # Appliquer les filtres de base
    df_filtered = df.copy()
    if type_filter != "Toutes": 
        df_filtered = df_filtered[df_filtered["type"] == type_filter]
    if cat_filter != "Toutes": 
        df_filtered = df_filtered[df_filtered["categorie"] == cat_filter]

    # 🔥 APPLIQUER LE FILTRE DOCUMENTS
    if filtre_documents == "🧾 Tickets":
        df_filtered = df_filtered[df_filtered["source"] == "OCR"]
    elif filtre_documents == "💼 Bulletins":
        df_filtered = df_filtered[(df_filtered["source"] == "PDF") & (df_filtered["type"] == "revenu")]
    elif filtre_documents == "📄 Factures":
        df_filtered = df_filtered[(df_filtered["source"] == "PDF") & (df_filtered["type"] == "dépense")]
    elif filtre_documents == "📝 Sans docs":
        df_filtered = df_filtered[~df_filtered["source"].isin(["OCR", "PDF"])]

    # 🔥 LIMITER AUX 5 DERNIÈRES SI OPTION ACTIVÉE
    if limit_display and len(df_filtered) > 5:
        df_display = df_filtered.head(5)
        st.info(f"📋 Affichage des 5 dernières transactions sur {len(df_filtered)} trouvées")
    else:
        df_display = df_filtered

    if df_display.empty:
        st.warning("🎯 Aucune transaction trouvée avec ces filtres.")
        return

    # 🔥 TABLEAU PRINCIPAL EN PREMIER - AMÉLIORÉ
    st.markdown("---")
    st.markdown("### 📋 Transactions récentes")
    
    # Préparer le DataFrame pour l'affichage
    df_table = df_display.copy()
    
    # 🔥 CORRECTION : S'ASSURER QUE LES MONTANTS SONT NUMÉRIQUES
    df_table["montant"] = pd.to_numeric(df_table["montant"], errors="coerce").fillna(0.0)
    
    # Ajouter une colonne visuelle pour le type
    def get_type_icon(row_type):
        return "🟢" if row_type == "revenu" else "🔴"
    
    df_table["Type"] = df_table["type"].apply(get_type_icon)
    
    # Ajouter une colonne visuelle pour les documents
    def get_doc_icon(source):
        if source == "OCR":
            return "🧾"
        elif source == "PDF":
            return "📄"
        else:
            return "📝"
    
    df_table["Doc"] = df_table["source"].apply(get_doc_icon)
    
    # 🔥 CORRECTION : FORMATAGE DES MONTANTS AVEC VÉRIFICATION DU TYPE
    def format_montant(row):
        montant = float(row["montant"]) if pd.notna(row["montant"]) else 0.0
        prefix = "+" if row["type"] == "revenu" else "-"
        return f"{prefix}{montant:.2f} €"
    
    df_table["Montant"] = df_table.apply(format_montant, axis=1)
    df_table["Date"] = pd.to_datetime(df_table["date"]).dt.strftime("%d/%m/%Y")
    
    # Sélection des colonnes à afficher
    display_columns = {
        "Type": "Type",
        "Doc": "Doc",
        "Date": "Date", 
        "categorie": "Catégorie",
        "sous_categorie": "Sous-catégorie",
        "Montant": "Montant",
        "description": "Description"
    }
    
    # Afficher le tableau principal
    st.dataframe(
        df_table[list(display_columns.keys())].rename(columns=display_columns),
        use_container_width=True,
        height=400,
        hide_index=True
    )

    # 🔥 STATISTIQUES RAPIDES SOUS LE TABLEAU - AVEC CONVERSION NUMÉRIQUE
    st.markdown("---")
    
    # 🔥 CORRECTION : S'ASSURER QUE LES CALCULS SONT FAITS SUR DES NUMÉRIQUES
    df_display["montant"] = pd.to_numeric(df_display["montant"], errors="coerce").fillna(0.0)
    
    total_revenus = df_display[df_display["type"]=="revenu"]["montant"].sum()
    total_depenses = df_display[df_display["type"]=="dépense"]["montant"].sum()
    solde = total_revenus - total_depenses
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Transactions", len(df_display))
    
    with col2:
        avec_docs = len(df_display[df_display["source"].isin(["OCR", "PDF"])])
        st.metric("📎 Avec documents", avec_docs)
    
    with col3:
        st.metric("💸 Revenus", f"{total_revenus:.2f} €")
    
    with col4:
        st.metric("💳 Dépenses", f"{total_depenses:.2f} €")

    # 🔥 SOLDE VISUEL
    solde_color = "green" if solde >= 0 else "red"
    solde_icon = "📈" if solde >= 0 else "📉"
    
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin: 20px 0;'>
        <h2 style='color: {solde_color}; margin: 0;'>
            {solde_icon} Solde : {solde:+.2f} €
        </h2>
    </div>
    """, unsafe_allow_html=True)

    # 🔥 VUE DÉTAILLÉE OPTIONNELLE (SI BESOIN DE PLUS)
    if len(df_display) > 0:
        with st.expander("🔍 Voir les détails et documents", expanded=False):
            st.markdown("### 📋 Détails des transactions")
            
            for idx, transaction in df_display.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        # Badge du type de document
                        source = transaction['source']
                        if source == "OCR":
                            badge = "🧾 Ticket de caisse"
                            couleur = "#1f77b4"
                        elif source == "PDF":
                            if transaction['type'] == "revenu":
                                badge = "💼 Bulletin de paie"
                                couleur = "#2ca02c"
                            else:
                                badge = "📄 Facture"
                                couleur = "#ff7f0e"
                        else:
                            badge = "📝 Transaction manuelle"
                            couleur = "#7f7f7f"
                        
                        st.markdown(f"<span style='background-color: {couleur}; color: white; padding: 4px 12px; border-radius: 16px; font-size: 0.8em; font-weight: bold;'>{badge}</span>", 
                                   unsafe_allow_html=True)
                        
                        st.write(f"**{transaction['categorie']}** → {transaction['sous_categorie']}")
                        if transaction.get('description'):
                            st.caption(f"📝 {transaction['description']}")
                            
                    with col2:
                        st.write(f"📅 {transaction['date']}")
                        if transaction.get('recurrence'):
                            st.caption(f"🔁 {transaction['recurrence']}")
                            
                    with col3:
                        # 🔥 CORRECTION : CONVERSION NUMÉRIQUE POUR L'AFFICHAGE
                        montant_val = float(transaction['montant']) if pd.notna(transaction['montant']) else 0.0
                        montant_color = "green" if transaction['type'] == 'revenu' else "red"
                        montant_prefix = "+" if transaction['type'] == 'revenu' else "-"
                        st.markdown(f"<h4 style='color: {montant_color}; text-align: right;'>{montant_prefix}{montant_val:.2f} €</h4>", unsafe_allow_html=True)
                    
                    # 🔥 AFFICHAGE DES DOCUMENTS SI DISPONIBLES
                    if transaction['source'] in ['OCR', 'PDF']:
                        if st.button("👀 Voir les documents", key=f"view_{idx}", type="secondary"):
                            st.session_state[f'selected_transaction_{idx}'] = transaction.to_dict()
                    
                    # Afficher les documents si sélectionnés
                    if f'selected_transaction_{idx}' in st.session_state:
                        st.markdown("---")
                        st.markdown("#### 📎 Documents associés")
                        afficher_documents_associes(st.session_state[f'selected_transaction_{idx}'])
                        
                        if st.button("❌ Fermer", key=f"close_{idx}"):
                            del st.session_state[f'selected_transaction_{idx}']
                            st.rerun()
                    
                    st.markdown("---")

    # 🔥 BOUTON POUR VOIR TOUTES LES TRANSACTIONS
    if limit_display and len(df_filtered) > 5:
        st.markdown("---")
        if st.button("📊 Voir toutes les transactions", use_container_width=True):
            st.session_state['show_all_transactions'] = True
            st.rerun()

# 🔥 FONCTION POUR AFFICHER TOUTES LES TRANSACTIONS (si besoin)
def interface_toutes_les_transactions():
    """Version étendue pour voir toutes les transactions"""
    st.subheader("📊 Toutes les transactions")
    
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("Aucune transaction enregistrée.")
        return
    
    # 🔥 CORRECTION : CONVERTIR LES MONTANTS DÈS LE DÉBUT
    df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)
    
    # Filtres étendus
    col1, col2, col3 = st.columns(3)
    with col1:
        date_debut = st.date_input("Date début", value=date(2025,1,1))
    with col2:
        date_fin = st.date_input("Date fin", value=date.today())
    with col3:
        souscat_filter = st.selectbox("Sous-catégorie", ["Toutes"] + sorted(df["sous_categorie"].dropna().unique().tolist()))
    
    # Appliquer filtres
    df = df[(df["date"] >= date_debut.isoformat()) & (df["date"] <= date_fin.isoformat())]
    if souscat_filter != "Toutes": 
        df = df[df["sous_categorie"] == souscat_filter]
    
    st.dataframe(
        df,
        use_container_width=True,
        height=600,
        hide_index=True,
        column_config={
            "id": "ID",
            "type": "Type",
            "categorie": "Catégorie", 
            "sous_categorie": "Sous-catégorie",
            "montant": st.column_config.NumberColumn("Montant (€)", format="%.2f €"),
            "date": "Date",
            "source": "Source",
            "recurrence": "Récurrence"
        }
    )
    if st.button("⬅️ Retour à la vue simplifiée"):
        st.session_state['show_all_transactions'] = False
        st.rerun()
  
    
def main_interface_voir_transactions():
    """Gère l'affichage des transactions selon le mode"""
    if st.session_state.get('show_all_transactions', False):
        interface_toutes_les_transactions()
    else:
        interface_voir_transactions()
        

# =============================
# 💹 Solde prévisionnel
# =============================
def interface_solde_previsionnel():
    st.header("💹 Solde prévisionnel")

    # --- Onglets internes
    tab1, tab2, tab3 = st.tabs([
        "📈 Analyse prévisionnelle",
        "🧮 Ajouter des prévisions",
        "📊 Suivi du portefeuille"
    ])

    # =======================
    # ONGLET 1 : ANALYSE PRÉVISIONNELLE
    # =======================
    with tab1:
        st.subheader("📊 Analyse prévisionnelle")

        conn = get_db_connection()
        df = pd.read_sql_query("SELECT * FROM transactions ORDER BY date ASC", conn)
        conn.close()

        if df.empty:
            st.info("Aucune transaction enregistrée pour le moment.")
        else:
            # --- Nettoyage de base ---
            df["montant"] = pd.to_numeric(df["montant"], errors="coerce").fillna(0.0)
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

            # --- Calcul du solde actuel ---
            revenus = df[df["type"] == "revenu"]["montant"].sum()
            depenses = df[df["type"] == "dépense"]["montant"].sum()
            solde_actuel = revenus - depenses

            st.metric("💰 Solde actuel", f"{solde_actuel:,.2f} €")

            # --- Date de projection ---
            date_projection = st.date_input(
                "Date de projection", 
                value=date.today() + timedelta(days=90)
            )
            proj_ts = pd.Timestamp(date_projection)
            today_ts = pd.Timestamp(datetime.now().date())

            # --- Sélection uniquement des transactions récurrentes automatiques ---
            rec_df = df[
                (df["recurrence"].notna()) &
                (df["source"].isin(["récurrence_auto", "récurrente_auto"]))
            ]

            occurrences = []

            for _, row in rec_df.iterrows():
                start_date = row["date"]
                recurrence = row["recurrence"]
                current_date = pd.Timestamp(start_date)

                # Générer les occurrences futures jusqu'à la date de projection
                while current_date <= proj_ts:
                    if current_date >= today_ts:
                        occurrences.append({
                            "date": current_date,
                            "type": row["type"],
                            "categorie": row["categorie"],
                            "sous_categorie": row["sous_categorie"],
                            "montant": row["montant"],
                            "description": row.get("description", "")
                        })

                    # Avancer selon la fréquence
                    if recurrence == "hebdomadaire":
                        current_date += pd.Timedelta(weeks=1)
                    elif recurrence == "mensuelle":
                        current_date += pd.DateOffset(months=1)
                    elif recurrence == "annuelle":
                        current_date += pd.DateOffset(years=1)
                    else:
                        break

            if occurrences:
                occ_df = pd.DataFrame(occurrences)

                # ✅ Éliminer les doublons (même date, type, catégorie, montant)
                occ_df = occ_df.drop_duplicates(
                    subset=["date", "type", "categorie", "sous_categorie", "montant"]
                )

                # --- Calcul du solde prévisionnel ---
                occ_df = occ_df.sort_values("date").reset_index(drop=True)
                solde_cum = [solde_actuel]
                for _, row in occ_df.iterrows():
                    dernier_solde = solde_cum[-1]
                    if row["type"] == "revenu":
                        solde_cum.append(dernier_solde + row["montant"])
                    else:
                        solde_cum.append(dernier_solde - row["montant"])
                occ_df["solde_previsionnel"] = solde_cum[1:]

                # --- Affichage du tableau ---
                st.subheader("📅 Occurrences futures des transactions récurrentes")
                st.dataframe(
                    occ_df[["date", "type", "categorie", "sous_categorie", "montant", "solde_previsionnel"]],
                    use_container_width=True
                )

                # --- Affichage du solde final ---
                st.metric(
                    "💹 Solde prévisionnel au " + date_projection.strftime("%d/%m/%Y"),
                    f"{solde_cum[-1]:,.2f} €"
                )

                # --- Graphique de l'évolution du solde ---
                st.subheader("📈 Évolution du solde prévisionnel")
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(occ_df["date"], occ_df["solde_previsionnel"], marker="o", linestyle="-")
                ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
                ax.set_xlabel("Date")
                ax.set_ylabel("Solde (€)")
                ax.set_title("Variation du solde prévisionnel dans le temps")
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)

            else:
                st.info("Aucune transaction récurrente à venir trouvée jusqu'à la date de projection.")

    # =======================
    # ONGLET 2 : AJOUTER DES PRÉVISIONS
    # =======================
    with tab2:
        st.subheader("🧮 Ajouter des prévisions temporaires")
        with st.form("form_prevision"):
            type_prevision = st.selectbox("Type de prévision", ["revenu","dépense"])
            categorie = st.text_input("Catégorie")
            sous_categorie = st.text_input("Sous-catégorie")
            montant = st.number_input("Montant (€)", min_value=0.0, step=10.0)
            date_prevision = st.date_input("Date de la prévision", value=date.today()+timedelta(days=30))
            submit_prevision = st.form_submit_button("Ajouter la prévision")
        
        if submit_prevision:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""INSERT INTO transactions (type, categorie, sous_categorie, montant, date, source) VALUES (?,?,?,?,?,?)""",
                         (type_prevision, categorie, sous_categorie, montant, date_prevision.isoformat(), "prévision_temp"))
            conn.commit()
            conn.close()
            st.success(f"✅ Prévision {type_prevision} ajoutée pour le {date_prevision.strftime('%d/%m/%Y')}")

    # =======================
    # ONGLET 3 : SUIVI DU PORTEFEUILLE
    # =======================
    with tab3:
        st.subheader("💹 Suivi du portefeuille")

        # --- Création / connexion à la base de données ---
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portefeuille (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                valeur_reelle REAL
            )
        """)
        conn.commit()

        # Lecture des valeurs réelles existantes
        df_portefeuille = pd.read_sql_query("SELECT * FROM portefeuille ORDER BY date ASC", conn)
        if not df_portefeuille.empty:
            df_portefeuille["date"] = pd.to_datetime(df_portefeuille["date"]).dt.date

        # --- 3 sous-onglets ---
        sous_tab1, sous_tab2, sous_tab3 = st.tabs([
            "📈 Simulation théorique",
            "💰 Valeur actuelle du portefeuille",
            "🚀 Stratégie de rattrapage"
        ])

        # =======================
        # 1️⃣ SIMULATION THÉORIQUE
        # =======================
        with sous_tab1:
            st.markdown("### 📈 Simulation de l'évolution théorique")
            capital_depart_theo = st.number_input("💵 Capital de départ (€)", value=1625.0, step=100.0, key="capital_depart_theo")
            rendement_cible_theo = st.number_input("🎯 Rendement cible annuel (%)", value=8.0, step=0.1, key="rendement_theo")
            versement_mensuel_theo = st.number_input("📆 Versement mensuel (€)", value=430.0, step=10.0, key="versement_theo")
            duree_annees_theo = st.slider("Durée de la simulation (années)", 1, 10, 2, key="duree_theo")

            taux_mensuel = rendement_cible_theo / 100 / 12
            dates_sim = pd.date_range(start=date.today(), periods=duree_annees_theo * 12, freq='MS')

            valeurs_theoriques = []
            valeur = capital_depart_theo
            for _ in dates_sim:
                valeurs_theoriques.append(round(valeur, 2))
                valeur = valeur * (1 + taux_mensuel) + versement_mensuel_theo

            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(dates_sim, valeurs_theoriques, label="Courbe théorique", color="blue", linewidth=2)
            ax.set_title("Simulation théorique de l'évolution du portefeuille")
            ax.set_xlabel("Date")
            ax.set_ylabel("Valeur (€)")
            ax.grid(True, linestyle="--", alpha=0.5)
            ax.legend()
            st.pyplot(fig)

            st.info(f"Valeur projetée après {duree_annees_theo} ans : **{valeurs_theoriques[-1]:,.2f} €**")

        # =======================
        # 2️⃣ VALEUR ACTUELLE DU PORTEFEUILLE
        # =======================
        with sous_tab2:
            st.markdown("### 💰 Enregistrement de la valeur réelle du portefeuille")

            # Choix du mode d'ajout
            mode_saisie = st.radio(
                "Choisir le type d'enregistrement :",
                ["📅 Ajouter une valeur pour aujourd'hui", "🕒 Ajouter une valeur pour une autre date"],
                horizontal=True,
                key="mode_saisie"
            )

            if mode_saisie == "📅 Ajouter une valeur pour aujourd'hui":
                date_saisie = datetime.now().date()
            else:
                date_saisie = st.date_input("📆 Sélectionner la date", value=datetime.now().date(), key="date_saisie")

            valeur_actuelle = st.number_input("💶 Valeur réelle (€)", value=0.0, step=10.0, key="valeur_actuelle")

            btn_valider = st.button("💾 Enregistrer cette valeur", key="btn_valider")

            if btn_valider:
                if valeur_actuelle <= 0:
                    st.warning("⚠️ Merci d'entrer une valeur supérieure à 0.")
                else:
                    # Vérifier si une valeur existe déjà pour cette date
                    cursor.execute("SELECT valeur_reelle FROM portefeuille WHERE date = ?", (date_saisie.isoformat(),))
                    existing = cursor.fetchone()

                    if existing:
                        st.warning(f"⚠️ Une valeur existe déjà pour le {date_saisie.strftime('%d/%m/%Y')} ({existing[0]:,.2f} €)")
                        if st.button("📝 Remplacer la valeur existante"):
                            cursor.execute(
                                "UPDATE portefeuille SET valeur_reelle = ? WHERE date = ?",
                                (valeur_actuelle, date_saisie.isoformat())
                            )
                            conn.commit()
                            st.success(f"✅ Valeur mise à jour pour le {date_saisie.strftime('%d/%m/%Y')} ({valeur_actuelle:,.2f} €)")
                    else:
                        cursor.execute(
                            "INSERT INTO portefeuille (date, valeur_reelle) VALUES (?, ?)",
                            (date_saisie.isoformat(), valeur_actuelle)
                        )
                        conn.commit()
                        st.success(f"✅ Valeur enregistrée ({valeur_actuelle:,.2f} €) le {date_saisie.strftime('%d/%m/%Y')}")

                # Rafraîchir les données
                df_portefeuille = pd.read_sql_query("SELECT * FROM portefeuille ORDER BY date ASC", conn)
                if not df_portefeuille.empty:
                    df_portefeuille["date"] = pd.to_datetime(df_portefeuille["date"]).dt.date

            # Affichage du graphique
            if df_portefeuille.empty:
                st.info("Aucune valeur réelle enregistrée pour le moment.")
            else:
                st.line_chart(df_portefeuille.set_index("date")["valeur_reelle"])

        # =======================
        # 3️⃣ STRATÉGIE DE RATTRAPAGE
        # =======================
        with sous_tab3:
            st.markdown("### 🚀 Stratégie de rattrapage (deux modes)")

            if df_portefeuille.empty:
                st.warning("⚠️ Enregistre d'abord au moins une valeur réelle dans l'onglet précédent.")
            else:
                # point de départ réel
                montant_depart = df_portefeuille["valeur_reelle"].iloc[-1]
                date_depart = df_portefeuille["date"].iloc[-1]
                st.info(f"Dernière valeur enregistrée : {montant_depart:,.2f} € ({date_depart.strftime('%d/%m/%Y')})")

                # Choix du mode
                mode = st.radio("Choisir le mode :", 
                                ("Entrer un montant → calculer la date (mode montant→date)",
                                 "Entrer une date → calculer le montant (mode date→montant)"),
                                key="rattrap_mode")

                # Paramètres communs
                capital_theo = st.number_input("💵 Capital théorique actuel (€)", value=2800.0, step=100.0, key="r_capital_theo")
                rendement_cible = st.number_input("🎯 Rendement cible annuel (%)", value=8.0, step=0.1, key="r_rendement")
                versement_mensuel = st.number_input("📆 Versement mensuel (€)", value=430.0, step=10.0, key="r_versement_mensuel")
                freq_common = st.selectbox("📅 Fréquence du versement supplémentaire", 
                                           ["Journalière", "Hebdomadaire", "Mensuelle", "Annuelle"], key="r_freq_common")

                # paramètres internes
                taux_journalier = (1 + rendement_cible / 100) ** (1 / 365) - 1
                freq_to_days = {"Journalière": 1, "Hebdomadaire": 7, "Mensuelle": 30, "Annuelle": 365}
                pas_days_common = freq_to_days[freq_common]

                # ============= MODE A : Entrer un montant -> calculer la date =============
                if mode.startswith("Entrer un montant"):
                    st.subheader("Mode : montant → date (combien de temps pour rattraper ?)")

                    montant_suppl = st.number_input("💸 Montant supplémentaire par période (selon la fréquence choisie)", 
                                                    value=10.0, step=1.0, key="r_montant_suppl_modeA")
                    max_days = st.number_input("Limite maximale de simulation (jours)", value=2000, step=1, key="r_max_days")

                    if st.button("⚡ Calculer la date de rattrapage", key="btn_calc_date_rattrap"):
                        # initialisation
                        montant_reel = montant_depart
                        montant_theo = capital_theo
                        montant_rattrap = montant_depart
                        jours = 0
                        dates, theo_series, reel_series, rattrap_series = [], [], [], []

                        # cas déjà rattrapé
                        if montant_rattrap >= montant_theo:
                            st.success("✅ Tu es déjà au-dessus de la courbe théorique.")
                        else:
                            # boucle journalière
                            while montant_rattrap < montant_theo and jours < int(max_days):
                                current_date = date.today() + timedelta(days=jours)
                                dates.append(current_date)

                                # intérêt journalier
                                montant_reel *= (1 + taux_journalier)
                                montant_theo *= (1 + taux_journalier)
                                montant_rattrap *= (1 + taux_journalier)

                                # versement mensuel (tous les 30 jours, à partir du jour 30)
                                if jours % 30 == 0 and jours > 0:
                                    montant_reel += versement_mensuel
                                    montant_theo += versement_mensuel
                                    montant_rattrap += versement_mensuel

                                # versement supplémentaire selon fréquence
                                if jours % pas_days_common == 0:
                                    montant_rattrap += montant_suppl

                                # sauvegarde
                                theo_series.append(montant_theo)
                                reel_series.append(montant_reel)
                                rattrap_series.append(montant_rattrap)
                                jours += 1

                            if montant_rattrap >= montant_theo:
                                date_rattrap = date.today() + timedelta(days=jours-1)
                                delta = date_rattrap - date.today()
                                jours_tot = delta.days
                                mois = jours_tot // 30
                                semaines = jours_tot // 7
                                st.success(f"🎯 Rattrapage atteint en environ {mois} mois ({semaines} semaines / {jours_tot} jours) — le {date_rattrap.strftime('%d/%m/%Y')}.")
                            else:
                                st.warning("⚠️ Rattrapage non atteint dans la limite de jours spécifiée.")

                            # affichage du graphique (toujours)
                            fig, ax = plt.subplots(figsize=(10,5))
                            ax.plot(dates, theo_series, label="Simulation théorique", color="blue", linewidth=2)
                            ax.plot(dates, reel_series, label="Valeur réelle (sans supplément)", color="orange", linewidth=2)
                            ax.plot(dates, rattrap_series, label=f"Rattrapage ({freq_common.lower()})", color="red", linestyle="--", linewidth=2)
                            ax.set_xlabel("Date")
                            ax.set_ylabel("Valeur (€)")
                            ax.set_title("📊 Simulation : rattrapage (montant → date)")
                            ax.grid(True, linestyle="--", alpha=0.5)
                            ax.legend()
                            st.pyplot(fig)

                # ============= MODE B : Entrer une date -> calculer le montant =============
                else:
                    st.subheader("Mode : date → montant (quel montant par période pour rattraper ?)")

                    date_cible = st.date_input("📅 Date cible de rattrapage", value=date.today() + timedelta(days=120), key="r_date_cible")
                    nb_jours = (date_cible - date.today()).days
                    if nb_jours <= 0:
                        st.warning("Choisis une date cible dans le futur.")
                    else:
                        # calculs sans boucle d'essais : détermination analytique
                        # 1) futur théorique (sans supplément)
                        montant_theo_future = capital_theo
                        for j in range(nb_jours):
                            montant_theo_future *= (1 + taux_journalier)
                            if j % 30 == 0 and j > 0:
                                montant_theo_future += versement_mensuel

                        # 2) futur réel (sans supplément)
                        montant_reel_future = montant_depart
                        for j in range(nb_jours):
                            montant_reel_future *= (1 + taux_journalier)
                            if j % 30 == 0 and j > 0:
                                montant_reel_future += versement_mensuel

                        # 3) déterminer nombre de périodes et taux par période
                        per_days = pas_days_common
                        # ceil division for periods
                        n_periodes = (nb_jours + per_days - 1) // per_days
                        # taux par période (approx multiplicatif)
                        r_periode = (1 + taux_journalier) ** per_days - 1

                        # 4) facteur capitalisant pour versements périodiques
                        if r_periode == 0:
                            facteur = n_periodes
                        else:
                            facteur = ((1 + r_periode) ** n_periodes - 1) / r_periode

                        # 5) montant par période nécessaire (analytique)
                        denom = facteur
                        numer = montant_theo_future - montant_reel_future
                        versement_par_periode = numer / denom if denom != 0 else float('inf')

                        if versement_par_periode <= 0:
                            st.success("✅ Tu es déjà au-dessus ou égal à la courbe théorique à la date choisie.")
                        else:
                            total_verse = versement_par_periode * n_periodes
                            st.success(f"💡 Il faut verser **{versement_par_periode:.2f} € par {freq_common.lower()}** pour rattraper la courbe le {date_cible.strftime('%d/%m/%Y')}.")
                            st.info(f"🔢 Nombre de versements : {n_periodes} → Total versé ~ {total_verse:,.2f} €")

                        # Simulation des 3 courbes (affichage)
                        dates_sim, theo_series, reel_series, rattrap_series = [], [], [], []
                        montant_theo = capital_theo
                        montant_reel = montant_depart
                        montant_rattrap = montant_depart

                        for j in range(nb_jours):
                            current_date = date.today() + timedelta(days=j)
                            dates_sim.append(current_date)

                            montant_theo *= (1 + taux_journalier)
                            montant_reel *= (1 + taux_journalier)
                            montant_rattrap *= (1 + taux_journalier)

                            if j % 30 == 0 and j > 0:
                                montant_theo += versement_mensuel
                                montant_reel += versement_mensuel
                                montant_rattrap += versement_mensuel

                            # ajout du versement périodique à la bonne fréquence
                            if (freq_common == "Journalière") or \
                               (freq_common == "Hebdomadaire" and j % 7 == 0) or \
                               (freq_common == "Mensuelle" and j % 30 == 0) or \
                               (freq_common == "Annuelle" and j % 365 == 0):
                                montant_rattrap += max(0, versement_par_periode)

                            theo_series.append(montant_theo)
                            reel_series.append(montant_reel)
                            rattrap_series.append(montant_rattrap)

                        fig, ax = plt.subplots(figsize=(10,5))
                        ax.plot(dates_sim, theo_series, label="Simulation théorique", color="blue", linewidth=2)
                        ax.plot(dates_sim, reel_series, label="Valeur réelle (sans supplément)", color="orange", linewidth=2)
                        ax.plot(dates_sim, rattrap_series, label=f"Rattrapage ({freq_common.lower()})", color="red", linestyle="--", linewidth=2)
                        ax.set_xlabel("Date")
                        ax.set_ylabel("Valeur (€)")
                        ax.set_title("📊 Simulation : date → montant")
                        ax.grid(True, linestyle="--", alpha=0.5)
                        ax.legend()
                        st.pyplot(fig)

        conn.close()


# ==============================
# 💹 Sous onglet voir les investissement
# ==============================
def interface_voir_investissements_alpha():
    st.subheader("📊 Performances de ton portefeuille (Trade Republic + Alpha Vantage)")

    # --- Clé API Alpha Vantage
    api_key = st.text_input("🔑 Entre ta clé API Alpha Vantage :", type="password")
    if not api_key:
        st.info("Entre ta clé API Alpha Vantage pour continuer.")
        return
    ts = TimeSeries(key=api_key, output_format='pandas')

    # --- Import du CSV Trade Republic
    uploaded_file = st.file_uploader("📥 Importer ton fichier CSV Trade Republic", type=["csv"])
    if uploaded_file is None:
        st.info("Importe ton CSV pour analyser ton portefeuille.")
        return

    df_tr = pd.read_csv(uploaded_file)
    st.markdown("### 💼 Données importées depuis Trade Republic")
    st.dataframe(df_tr, use_container_width=True, height=250)

    # Vérification des colonnes minimales
    required_cols = {"Ticker", "Quantité", "Prix d'achat (€)"}
    if not required_cols.issubset(df_tr.columns):
        st.error(f"⚠️ Le fichier doit contenir les colonnes : {', '.join(required_cols)}")
        return

    tickers = df_tr["Ticker"].dropna().unique().tolist()

    # --- Téléchargement des données de marché actuelles
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
            st.warning(f"❌ Impossible de récupérer {t} ({e})")

    if not data:
        st.warning("Aucune donnée récupérée depuis Alpha Vantage.")
        return

    # --- Calculs de performance
    results = []
    for _, row in df_tr.iterrows():
        t = row["Ticker"]
        qte = float(row["Quantité"])
        prix_achat = float(row["Prix d'achat (€)"])
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

    # --- Valeur totale
    valeur_totale_portefeuille = df_results["Valeur totale (€)"].sum()
    perf_moyenne = df_results["Performance (%)"].mean()
    st.metric("💰 Valeur totale du portefeuille", f"{valeur_totale_portefeuille:,.2f} €", f"{perf_moyenne:.2f}%")

    # --- Graphique d'évolution du premier actif
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

    st.success("✅ Portefeuille analysé avec succès !")

# Liste de catégories valides connues (tu peux l'étendre à volonté)
KNOWN_CATEGORIES = [
    "essence", "alimentation", "supermarché", "carrefour", "auchan",
    "restaurant", "boulangerie", "loisirs", "santé", "logement", "transport"
]

def correct_category_name(name):
    """Corrige les fautes simples dans les noms de catégorie/sous-catégorie."""
    if not name:
        return name
    name = name.lower().strip()
    matches = get_close_matches(name, KNOWN_CATEGORIES, n=1, cutoff=0.8)
    return matches[0] if matches else name

# ==============================
# 📋 MENU LATÉRAL
# ==============================
with st.sidebar:
    st.title("📂 Menu principal")
    page = st.radio(
        "Navigation",
        ["🏠 Accueil","💸 Transactions", "📊 Voir Transactions", "📈 Solde prévisionnel"]
    )
# ==============================
# 🏠 PAGE ACCUEIL
# ==============================    
if page == "🏠 Accueil":
    interface_accueil()

# ==============================
# 💸 PAGE TRANSACTIONS
# ==============================
if page == "💸 Transactions":
    st.header("💸 Transactions")

    # Onglets pour les sous-parties
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧾 Ajouter un ticket",
        "✍️ Ajouter une dépense manuelle",
        "🔁 Dépense récurrente",
        "💰 Ajouter un revenu"
    ])

    with tab1:
        st.header("📸 Scanner les tickets automatiquement")
        st.info(f"Dépose tes tickets à scanner dans : `{TO_SCAN_DIR}`")
        process_all_tickets_in_folder()
    
    with tab2:
        interface_transactions_unifiee()

    with tab3:
        interface_transaction_recurrente()
    
    with tab4:
        interface_ajouter_revenu()

# ==============================
# 📊 PAGE VOIR / GÉRER TRANSACTIONS
# ==============================
elif page == "📊 Voir Transactions":
    st.header("📊 Voir Transactions")

    # --- Onglets pour les sous-parties ---
    tab1, tab2, tab3 = st.tabs([
        "📋 Transactions",
        "🗑️ Gérer les transactions",
        "🔁 Gérer les récurrences"
    ])

    # === Onglet 1 : Visualisation ===
    with tab1:
        main_interface_voir_transactions()

    # === Onglet 2 : Suppression et gestion ===
    with tab2:
        interface_gerer_transactions()

    # === Onglet 3 : Gestion des récurrences ===
    with tab3:
        interface_gerer_recurrences()


# ==============================
# 📈 Solde prévisionnel
# ==============================
elif page == "📈 Solde prévisionnel": 
    interface_solde_previsionnel()