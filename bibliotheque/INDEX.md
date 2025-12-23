# 📚 Bibliothèque de Connaissances - Gestio V4

## 🎯 Bienvenue

Cette bibliothèque centralise toute la documentation, les règles d'implémentation, l'historique des ajouts et les erreurs rencontrées sur le projet Gestio V4.

**Public cible** : Développeurs, IA assistantes, contributeurs externes

---

## 📖 Structure

```
bibliotheque/
├── INDEX.md         → Ce fichier (navigation)
├── guides/          → Règles générales et standards
├── modules/         → Règles spécifiques par module
├── readmes/         → Documentation technique modules (copies)
├── help/            → Guides bibliothèques externes
├── ajouts/          → Walkthroughs chronologiques
└── erreurs/         → Rapports d'erreurs détaillés
```

---

## 🗂️ Table des matières

### 📘 Guides généraux

| Document | Description | Quand consulter |
|----------|-------------|-----------------|
| [IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md) | Règles strictes d'implémentation | Avant d'ajouter du code |
| [COMMON_ERRORS.md](guides/COMMON_ERRORS.md) | Erreurs courantes + solutions | Quand tu rencontres une erreur |

### 🔧 Règles par module

| Module | Document | Description |
|--------|----------|-------------|
| Database | [database-rules.md](modules/database-rules.md) | Repositories, migrations, SQL |
| Services | [services-rules.md](modules/services-rules.md) | Logique métier, patterns |
| UI | [ui-rules.md](modules/ui-rules.md) | Pages Streamlit, composants |
| OCR | [ocr-rules.md](modules/ocr-rules.md) | Extraction texte, parsers |
| Utils | [utils-rules.md](modules/utils-rules.md) | Fonctions helpers globales |

### 📖 Documentation technique (Copies README)

*Copies des README modules pour consultation centralisée*

| Module | Document | Contenu |
|--------|----------|---------|
| Config | [config.md](readmes/config.md) | Configuration, chemins, constantes |
| Database | [database.md](readmes/database.md) | Tables, repositories, modèles |

*Note : Les README originaux restent dans `v4/modules/{module}/README.md`*

### 📚 Guides bibliothèques externes

| Bibliothèque | Document | Description |
|--------------|----------|-------------|
| Streamlit | [streamlit.md](help/streamlit.md) | Framework UI - Concepts & exemples |
| Pandas | [pandas.md](help/pandas.md) | Manipulation données |
| Plotly | [plotly.md](help/plotly.md) | Graphiques interactifs |
| SQLite3 | [sqlite3.md](help/sqlite3.md) | Base de données |

### 📝 Historique des ajouts

**Format** : `NN_nom_modification.md` (numérotation séquentielle)

| # | Nom | Description | Date |
|---|-----|-------------|------|
| 01 | Refactoring Transactions | Refactoring de `transactions.py` en 3 modules | 14 déc 2024 |
| 02 | Création Documentation | Création documentation complète projet | 14 déc 2024 |
| 03 | Refactoring Architecture | Migration modules/ → domains/shared/ | 16 déc 2024 |
| 04 | Installation Bulletproof | Système d'installation robuste v4.0.0 | 21 déc 2024 |

📂 **Archive V3** : Les anciens documents V3 sont dans [_archive_v3/](ajouts/_archive_v3/)

📖 **Template** : Voir [ajouts/README.md](ajouts/README.md) pour ajouter un nouveau document

### 🔴 Erreurs documentées

**Format** : `YYYY-MM-DD_type-erreur.md`

| Date | Erreur | Lien |
|------|--------|------|
| - | (Erreurs individuelles à documenter) | - |

*Les 7 erreurs courantes sont déjà dans [COMMON_ERRORS.md](erreurs/COMMON_ERRORS.md)*

---

## 🚀 Comment utiliser cette bibliothèque

### Pour les développeurs

1. **Avant d'ajouter du code** → Consulter `guides/IMPLEMENTATION_GUIDE.md`
2. **Pour un module spécifique** :
   - Règles : `modules/{module}-rules.md`
   - Documentation technique : `readmes/{module}.md` ou `v4/modules/{module}/README.md`
3. **En cas d'erreur** → Chercher dans `guides/COMMON_ERRORS.md` puis `erreurs/`
4. **Pour comprendre l'historique** → Parcourir `ajouts/`
5. **Guides bibliothèques** → Consulter `help/`

### Pour les IA

**Workflow recommandé** :
1. **Commencer par** `INDEX.md` (ce fichier)
2. **Lire** `guides/IMPLEMENTATION_GUIDE.md` pour les règles générales
3. **Consulter** le module concerné :
   - Règles dans `modules/{module}-rules.md`
   - Doc technique dans `readmes/{module}.md`
4. **Vérifier** si l'erreur existe dans `guides/COMMON_ERRORS.md`
5. **Documenter** nouvelle feature dans `ajouts/YYYY-MM-DD_feature.md`

---

## 📝 Template de documentation

### Ajouter un walkthrough

```bash
# Créer fichier avec date
bibliotheque/ajouts/2024-12-XX_nouvelle-feature.md
```

**Contenu** :
```markdown
# [Titre Feature]

## Objectif
[Description]

## Modifications apportées
[Fichiers modifiés]

## Tests effectués
[Validation]

## Notes
[Points importants]
```

### Documenter une erreur

```bash
# Créer fichier avec date
bibliotheque/erreurs/2024-12-XX_type-erreur.md
```

**Contenu** :
```markdown
# [Titre Erreur]

## Symptôme
[Message d'erreur]

## Solution
[Code corrigé]

## Prévention
[Comment éviter]
```

---

## 🔄 Mise à jour de la bibliothèque

**Responsabilité** : Développeur qui fait la modification

**Quand** :
- ✅ Après chaque ajout de feature → Créer walkthrough dans `ajouts/`
- ✅ Après résolution d'erreur → Documenter dans `erreurs/`
- ✅ Ajout de règle générale → Mettre à jour `guides/`
- ✅ Ajout de règle module → Mettre à jour `modules/`

**Comment** :
1. Créer fichier avec date `YYYY-MM-DD_` (ou titre descriptif)
2. Mettre à jour ce fichier `INDEX.md`
3. Commit avec message clair

---

## 🎓 Principes

1. **Documentation = Code** - Aussi important que le code
2. **Chronologie claire** - Toujours dater les nouveaux fichiers
3. **Concision** - Aller droit au but
4. **Exemples** - Toujours illustrer avec du code
5. **Prévention** - Expliquer comment éviter le problème

---

## 📞 Navigation rapide

- 🏠 [Retour au projet](../v4/README.md)
- 📖 [Guide implémentation](guides/IMPLEMENTATION_GUIDE.md)
- 🔴 [Erreurs courantes](guides/COMMON_ERRORS.md)
- 📚 [Guides bibliothèques](help/)
- 📝 [Historique ajouts](ajouts/)

---

## 📊 Statistiques

| Catégorie | Nombre |
|-----------|--------|
| Guides généraux | 2 |
| Règles modules | 5 |
| Guides bibliothèques | 4 |
| Ajouts historiques | 4 (+ 5 archivés V3) |
| Erreurs documentées | 7 (dans COMMON_ERRORS) |
| **Total documents** | **21+** |

---

**Dernière mise à jour** : 21 décembre 2024  
**Version bibliothèque** : 1.2
