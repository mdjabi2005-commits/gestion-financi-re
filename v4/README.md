# 📚 Bibliothèque de Connaissances - Gestio V4

## 🎯 Vue d'ensemble

Cette bibliothèque centralise **toute la documentation, les règles, l'historique et les erreurs** du projet.

**Public** : Développeurs, IA, contributeurs

---

## 📖 Navigation rapide

### Pour les développeurs

- 📘 [Guide d'implémentation](bibliotheque/guides/IMPLEMENTATION_GUIDE.md) - **À lire en premier !**
- 🔴 [Erreurs courantes](bibliotheque/guides/COMMON_ERRORS.md) - Quand tu bloques
- 📋 [Index bibliothèque](bibliotheque/INDEX.md) - Table des matières complète

### Pour les IA

1. Lire [IMPLEMENTATION_GUIDE.md](bibliotheque/guides/IMPLEMENTATION_GUIDE.md)
2. Consulter règles module dans `bibliotheque/modules/{module}-rules.md`
3. Vérifier erreurs connues dans [COMMON_ERRORS.md](bibliotheque/guides/COMMON_ERRORS.md)
4. Documenter ajouts dans `bibliotheque/ajouts/YYYY-MM-DD_description.md`

---

## 📁 Structure du projet

```
gestion-financière/
├── bibliotheque/              ← 📚 Documentation et règles
│   ├── INDEX.md
│   ├── guides/               ← Guides généraux
│   ├── modules/              ← Règles par module
│   ├── ajouts/               ← Historique chronologique
│   └── erreurs/              ← Erreurs documentées
│
└── v4/                       ← 💻 Code de l'application
    ├── README.md             ← Ce fichier
    ├── main.py               ← Point d'entrée Streamlit
    ├── config/               ← Configuration
    ├── modules/
    │   ├── database/         ← Repositories, modèles
    │   ├── services/         ← Logique métier
    │   ├── ui/               ← Interface Streamlit
    │   ├── ocr/              ← Extraction texte
    │   └── utils/            ← Utilitaires globaux
    ├── scripts/              ← Scripts maintenance
    ├── help/                 ← Guides bibliothèques
    └── data/                 ← Base de données
```

---

## 🚀 Démarrage rapide

### Installation

```bash
cd c:\Users\djabi\gestion-financière\v4
pip install -r requirements.txt
```

### Lancement

```bash
streamlit run main.py
```

---

## 📚 Documentation complète

Voir [bibliotheque/INDEX.md](bibliotheque/INDEX.md) pour :
- Guides d'implémentation
- Règles par module
- Historique des ajouts
- Erreurs documentées

---

## 🏗️ Architecture

**Couches** (strictement respectées) :
```
UI → Services → Database → Config
```

Voir [IMPLEMENTATION_GUIDE.md](bibliotheque/guides/IMPLEMENTATION_GUIDE.md) pour les règles détaillées.

---

## 📝 Contribuer

**Avant d'ajouter du code** :
1. Lire [IMPLEMENTATION_GUIDE.md](bibliotheque/guides/IMPLEMENTATION_GUIDE.md)
2. Consulter règles module concerné dans `bibliotheque/modules/`
3. Vérifier [COMMON_ERRORS.md](bibliotheque/guides/COMMON_ERRORS.md)

**Après avoir ajouté une feature** :
1. Créer walkthrough dans `bibliotheque/ajouts/YYYY-MM-DD_feature.md`
2. Mettre à jour [bibliotheque/INDEX.md](bibliotheque/INDEX.md)

---

## 🔗 Liens utiles

- 📖 [Documentation modules](modules/) - README dans chaque module
- 📚 [Guides bibliothèques](help/) - Streamlit, Pandas, Plotly, SQLite
- 📋 [Index complet](bibliotheque/INDEX.md) - Table des matières bibliothèque

---

**Version** : 4.0  
**Dernière mise à jour** : 14 décembre 2024
