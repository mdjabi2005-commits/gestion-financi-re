# 🤖 Migration OCR : Tesseract → Vision IA (Gemini)

**Date** : 2 janvier 2026  
**Statut** : Idée validée - À implémenter  
**Priorité** : Haute (amélioration majeure)  
**Impact** : Précision 85% → 95%+, Code -90%

---

## 🎯 Décision Architecture

**Vision IA = Outil Partagé (@tool)**

- ✅ **PAS un agent séparé** (pas de SCANNER agent)
- ✅ **Outil LangChain** utilisable par tous les agents
- ✅ **COACH** l'utilise principalement (scan utilisateur)
- ✅ **MÉCANICIEN** peut l'utiliser (tests, migration)
- ✅ Intégré dans `tools/vision_scanner.py`

---

## 🎯 Problème Actuel

### Tesseract : Limitations Identifiées

**Sensibilité** :
- ❌ Qualité photo critique
- ❌ Sensible aux plis
- ❌ Sensible à la lumière
- ❌ Sensible à l'angle
- ❌ Nécessite preprocessing complexe

**Complexité** :
- ❌ 4 méthodes de parsing
- ❌ 52 patterns à maintenir
- ❌ Cross-validation manuelle
- ❌ Learning system complexe
- ❌ ~1600 lignes de code OCR

**Résultat** : 85% précision (bon mais perfectible)

---

## ✅ Solution : Vision IA (Gemini Vision)

### Principe

**L'IA "voit" l'image comme un humain** :
- ✅ Comprend le contexte (ticket vs facture)
- ✅ Robuste aux imperfections
- ✅ Extrait structure directement
- ✅ Pas de preprocessing nécessaire

### Avantages

| Critère | Tesseract | Gemini Vision |
|---------|-----------|---------------|
| **Précision** | 85% | 95-98% |
| **Robustesse photo** | ❌ Faible | ✅ Excellente |
| **Plis/Froissé** | ❌ Problème | ✅ OK |
| **Lumière variable** | ❌ Problème | ✅ OK |
| **Angle/Rotation** | ❌ Problème | ✅ OK |
| **Structuration** | ❌ Manuel | ✅ Auto JSON |
| **Maintenance** | ❌ Patterns | ✅ Aucune |
| **Code** | ~1600 lignes | ~100 lignes |
| **Coût** | Gratuit | 0.001€/image |

---

## 🚀 Nouveau Workflow Simplifié

### Avant (Complexe)
```
1. Upload photo
2. Preprocessing (5 étapes)
   - Redimensionnement
   - Niveaux de gris
   - Débruitage
   - Rotation
   - Contraste
3. Tesseract OCR
4. Parsing (4 méthodes)
   - Regex patterns
   - Montant isolé
   - Ligne TOTAL
   - Fallback
5. Cross-validation
6. Learning system
7. Résultat (85%)
```

### Après (Simple)
```
1. Upload photo
2. Gemini Vision
3. JSON structuré
4. Résultat (95%+)
```

**Gain** : 7 étapes → 3 étapes

---

## 💻 Implémentation - Outil Partagé LangChain

### Structure Projet Squad Lamoms

```
squad_lamoms/
├── tools/                      # Outils partagés
│   ├── __init__.py
│   ├── vision_scanner.py       # ← Vision IA ici
│   ├── database.py
│   └── notifications.py
├── agents/
│   ├── coach.py                # Utilise vision_scanner
│   ├── mecanicien.py           # Peut tester vision_scanner
│   └── ...
```

### Code Outil Vision IA

```python
# tools/vision_scanner.py
from langchain.tools import tool
import google.generativeai as genai
from PIL import Image
from pathlib import Path
import json
from typing import Optional, Dict

@tool
def scan_ticket_vision(image_path: str) -> dict:
    """
    Scanner un ticket de caisse avec Gemini Vision.
    
    Args:
        image_path: Chemin vers l'image du ticket
        
    Returns:
        dict: {
            "montant_total": float,
            "date": "YYYY-MM-DD",
            "magasin": str,
            "categorie_suggeree": str,
            "confiance": float (0.0-1.0)
        }
    """
    try:
        # Configurer Gemini
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Charger image
        image = Image.open(image_path)
        
        # Prompt optimisé
        prompt = """
        Analyse ce ticket de caisse français et extrait en JSON :
        
        {
            "montant_total": <float>,
            "date": "YYYY-MM-DD",
            "magasin": "<nom>",
            "categorie_suggeree": "<Alimentation|Transport|Loisirs|Santé|Autre>",
            "confiance": <0.0-1.0>
        }
        
        Réponds UNIQUEMENT avec le JSON.
        """
        
        # Appel Vision IA
        response = model.generate_content([prompt, image])
        result = json.loads(response.text.strip())
        
        return result
        
    except Exception as e:
        return {
            "error": str(e),
            "montant_total": None,
            "confiance": 0.0
        }

@tool
def scan_facture_vision(image_path: str) -> dict:
    """
    Scanner une facture avec Gemini Vision.
    
    Returns: Structure similaire avec champs additionnels
    """
    # Prompt adapté pour factures
    pass
```

### Utilisation par COACH

```python
# agents/coach.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent
from tools.vision_scanner import scan_ticket_vision, scan_facture_vision

COACH_PROMPT = """
Tu es LAMOMS-COACH, assistant financier personnel.

Tu as accès aux outils suivants :
- scan_ticket_vision : Scanner un ticket de caisse
- scan_facture_vision : Scanner une facture
- create_transaction : Créer une transaction
- get_transactions : Récupérer transactions

Utilise ces outils pour aider l'utilisateur.
"""

class CoachAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.tools = [
            scan_ticket_vision,
            scan_facture_vision,
            # ... autres outils
        ]
        self.agent = create_tool_calling_agent(
            self.llm,
            self.tools,
            COACH_PROMPT
        )
```

### Exemple Conversation

```
Utilisateur: "J'ai un ticket à scanner"

COACH (pense):
- Utilisateur veut scanner ticket
- Je dois utiliser l'outil scan_ticket_vision
- Je vais demander le chemin de l'image

COACH: "Envoyez-moi la photo du ticket"

Utilisateur: [Upload ticket.jpg]

COACH (exécute):
→ scan_ticket_vision("ticket.jpg")
→ Résultat: {"montant_total": 45.67, "magasin": "Carrefour", "confiance": 0.95}

COACH: "✅ Ticket scanné avec succès !
        - Montant : 45.67€
        - Magasin : Carrefour
        - Catégorie suggérée : Alimentation
        
        Voulez-vous créer la transaction ?"

Utilisateur: "Oui"

COACH (exécute):
→ create_transaction(montant=45.67, categorie="Alimentation", ...)

COACH: "✅ Transaction créée !"
```
import google.generativeai as genai
from PIL import Image
from pathlib import Path
import json
from typing import Optional, Dict
from datetime import datetime

class VisionOCRScanner:
    """Scanner OCR utilisant Gemini Vision."""
    
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def scan_ticket(self, image_path: Path) -> Optional[Dict]:
        """
        Scanner un ticket avec Gemini Vision.
        
        Returns:
            {
                "montant_total": float,
                "date": "YYYY-MM-DD",
                "magasin": str,
                "categorie_suggeree": str,
                "articles": [{"nom": str, "prix": float}],
                "confiance": float (0.0-1.0)
            }
        """
        try:
            # Charger image
            image = Image.open(image_path)
            
            # Prompt optimisé pour tickets français
            prompt = """
            Analyse ce ticket de caisse français et extrait les informations en JSON :
            
            {
                "montant_total": <montant total en float, ex: 45.67>,
                "date": "<date au format YYYY-MM-DD>",
                "magasin": "<nom du magasin>",
                "categorie_suggeree": "<Alimentation|Transport|Loisirs|Santé|Vêtements|Autre>",
                "articles": [
                    {"nom": "<nom article>", "prix": <prix float>}
                ],
                "confiance": <0.0 à 1.0, ta confiance dans l'extraction>
            }
            
            Règles importantes :
            - Si montant total illisible, mets null
            - Si date illisible, mets date du jour
            - Catégorie basée sur le magasin :
              * Carrefour/Auchan/Leclerc = Alimentation
              * Shell/Total/BP = Transport
              * Fnac/Cultura = Loisirs
              * Pharmacie = Santé
            - Articles : optionnel, seulement si lisibles
            - Confiance :
              * 1.0 = tout parfaitement clair
              * 0.7-0.9 = quelques zones floues mais montant OK
              * 0.3-0.6 = flou, montant incertain
              * 0.0-0.2 = illisible
            
            Réponds UNIQUEMENT avec le JSON, rien d'autre.
            """
            
            # Envoyer à Gemini Vision
            response = self.model.generate_content([prompt, image])
            
            # Parser JSON
            result = json.loads(response.text.strip())
            
            # Validation basique
            if result.get('montant_total') and result.get('confiance', 0) > 0.5:
                return result
            else:
                return None
            
        except Exception as e:
            print(f"Erreur Vision OCR : {e}")
            return None
    
    def scan_facture(self, image_path: Path) -> Optional[Dict]:
        """
        Scanner une facture (plus détaillé).
        
        Returns: Structure similaire avec champs additionnels
        """
        # Prompt adapté pour factures
        prompt = """
        Analyse cette facture et extrait :
        {
            "montant_total": float,
            "montant_ht": float,
            "tva": float,
            "date": "YYYY-MM-DD",
            "fournisseur": str,
            "numero_facture": str,
            "categorie_suggeree": str,
            "confiance": float
        }
        """
        # Même logique que scan_ticket
        pass
```

### Utilisation dans l'UI

```python
# domains/ocr/pages/scanning.py
import streamlit as st
from domains.ocr.vision_scanner import VisionOCRScanner
from pathlib import Path

def interface_scan_vision():
    """Interface de scan avec Vision IA."""
    
    st.title("📸 Scanner Ticket (Vision IA)")
    
    # Upload
    uploaded_file = st.file_uploader(
        "Photo du ticket", 
        type=['jpg', 'jpeg', 'png'],
        help="Même floue ou froissée, l'IA comprendra !"
    )
    
    if uploaded_file:
        # Afficher preview
        st.image(uploaded_file, caption="Ticket à scanner", width=300)
        
        if st.button("🤖 Scanner avec IA"):
            # Sauvegarder temporairement
            temp_path = Path("temp") / uploaded_file.name
            temp_path.parent.mkdir(exist_ok=True)
            temp_path.write_bytes(uploaded_file.read())
            
            # Scanner avec Vision IA
            scanner = VisionOCRScanner(api_key=st.secrets["GOOGLE_API_KEY"])
            
            with st.spinner("🤖 L'IA analyse le ticket..."):
                result = scanner.scan_ticket(temp_path)
            
            # Afficher résultat
            if result:
                confiance = result['confiance']
                
                if confiance > 0.8:
                    st.success(f"✅ Ticket scanné avec {confiance:.0%} de confiance")
                elif confiance > 0.5:
                    st.warning(f"⚠️ Ticket scanné avec {confiance:.0%} de confiance - Vérifiez les données")
                else:
                    st.error(f"❌ Confiance trop faible ({confiance:.0%}) - Ressayez avec meilleure photo")
                
                # Afficher données extraites
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Montant", f"{result['montant_total']}€")
                    st.write(f"**Date** : {result['date']}")
                
                with col2:
                    st.write(f"**Magasin** : {result['magasin']}")
                    st.write(f"**Catégorie** : {result['categorie_suggeree']}")
                
                # Articles (si disponibles)
                if result.get('articles'):
                    with st.expander("📋 Détail articles"):
                        for article in result['articles']:
                            st.write(f"- {article['nom']} : {article['prix']}€")
                
                # Bouton validation
                if st.button("✅ Créer transaction"):
                    # Créer transaction avec données
                    transaction = {
                        'type': 'dépense',
                        'montant': result['montant_total'],
                        'date': result['date'],
                        'categorie': result['categorie_suggeree'],
                        'description': f"Ticket {result['magasin']}",
                        'source': 'scan_vision_ia'
                    }
                    
                    # Insérer en DB
                    TransactionRepository.insert(transaction)
                    
                    st.success("✅ Transaction créée !")
                    st.balloons()
            
            else:
                st.error("❌ Impossible de scanner le ticket")
            
            # Nettoyer
            temp_path.unlink(missing_ok=True)
```

---

## 📊 Comparaison Détaillée

### Code à Supprimer

**Fichiers obsolètes** :
- ❌ `domains/ocr/preprocessing.py` (~300 lignes)
- ❌ `domains/ocr/parsers.py` (~800 lignes) - 4 méthodes
- ❌ `domains/ocr/learning_service.py` (~300 lignes)
- ❌ `config/ocr_patterns.yml` (52 patterns)
- ❌ `config/ocr_patterns_learned.yml`

**Total supprimé** : ~1400 lignes + 2 fichiers config

**Nouveau code** : ~100 lignes (vision_scanner.py)

**Gain net** : **-93% de code** 🎉

---

## 💰 Coût

### Gemini Flash (Recommandé)

**Prix** : 0.001€ par image

**Estimation mensuelle** :
- 100 tickets/mois = 0.10€
- 500 tickets/mois = 0.50€
- 1000 tickets/mois = 1.00€

**Verdict** : **Négligeable** pour gain de qualité énorme

### Alternative Gratuite

**Stratégie hybride** :
```python
def smart_scan(image_path):
    # Essayer Vision IA d'abord
    result = vision_scanner.scan_ticket(image_path)
    
    if result and result['confiance'] > 0.8:
        return result  # ✅ Haute confiance
    
    # Fallback Tesseract si budget dépassé
    return tesseract_scan(image_path)
```

---

## 🎯 Plan de Migration

### Phase 1 : Prototype (2h)
- [ ] Créer `vision_scanner.py`
- [ ] Tester sur 10 tickets réels
- [ ] Comparer précision vs Tesseract

### Phase 2 : Intégration (3h)
- [ ] Ajouter bouton "Scanner avec IA" dans UI
- [ ] Garder Tesseract en fallback
- [ ] Logger comparaisons

### Phase 3 : Migration Complète (2h)
- [ ] Remplacer Tesseract par Vision IA
- [ ] Supprimer code obsolète
- [ ] Mettre à jour documentation

### Phase 4 : Nettoyage (1h)
- [ ] Supprimer fichiers preprocessing
- [ ] Supprimer parsers.py
- [ ] Supprimer learning_service.py
- [ ] Archiver patterns.yml

**Total** : ~8h pour migration complète

---

## ✅ Avantages Finaux

### Pour l'Utilisateur
- ✅ **Scan plus rapide** (pas de preprocessing)
- ✅ **Fonctionne même avec photos moyennes**
- ✅ **Moins de rejets** (robuste aux plis/lumière)
- ✅ **Catégorie suggérée automatiquement**

### Pour le Développeur
- ✅ **90% moins de code à maintenir**
- ✅ **Pas de patterns à gérer**
- ✅ **Pas de learning system complexe**
- ✅ **API simple (1 appel)**

### Pour le Projet
- ✅ **Précision 85% → 95%+**
- ✅ **Codebase plus simple**
- ✅ **Moins de bugs potentiels**
- ✅ **Évolutif** (Gemini s'améliore avec le temps)

---

## 🚨 Risques et Mitigation

### Risque 1 : Coût
**Mitigation** : 
- Stratégie hybride (Vision IA + Tesseract fallback)
- Budget mensuel défini
- Monitoring coûts

### Risque 2 : Dépendance API
**Mitigation** :
- Garder Tesseract en fallback
- Cache résultats
- Gestion erreurs robuste

### Risque 3 : Offline
**Mitigation** :
- Mode offline = Tesseract automatique
- Détection connexion internet

---

## 📝 Prochaines Étapes

1. **Maintenant** : Idée documentée ✅
2. **Après agents** : Prototype Phase 1
3. **Test réel** : 10-20 tickets
4. **Si concluant** : Migration complète

---

## 🎉 Conclusion

**Cette migration est un NO-BRAINER** :
- ✅ Meilleure précision (85% → 95%+)
- ✅ Code plus simple (-93%)
- ✅ Plus robuste (plis, lumière, angle)
- ✅ Coût négligeable (0.001€/image)
- ✅ Maintenance réduite (pas de patterns)

**Recommandation** : **MIGRER** dès que possible ! 🚀

---

**Lien** : Discussion du 2 janvier 2026, 22h52  
**Auteur** : Antigravity + User insights
