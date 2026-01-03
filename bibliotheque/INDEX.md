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
├── help/            → Guides bibliothèques externes
├── ajouts/          → Historique chronologique des modifications
├── walkthroughs/    → Sessions de développement détaillées
└── erreurs/         → Rapports d'erreurs détaillés
```

---

## 🗂️ Table des matières

### 📘 Guides généraux

| Document | Description | Quand consulter |
|----------|-------------|-----------------|
| [IMPLEMENTATION_GUIDE.md](guides/IMPLEMENTATION_GUIDE.md) | Règles strictes d'implémentation | Avant d'ajouter du code |
| [COMMON_ERRORS.md](erreurs/COMMON_ERRORS.md) | Erreurs courantes + solutions | Quand tu rencontres une erreur |

### 🔧 Règles par module

| Module | Document | Description |
|--------|----------|-------------|
| Database | [database-rules.md](modules/database-rules.md) | Repositories, migrations, SQL |
| Services | [services-rules.md](modules/services-rules.md) | Logique métier, patterns |
| UI | [ui-rules.md](modules/ui-rules.md) | Pages Streamlit, composants |
| OCR | [ocr-rules.md](modules/ocr-rules.md) | Extraction texte, parsers |
| Utils | [utils-rules.md](modules/utils-rules.md) | Fonctions helpers globales |

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
| 04 | Amélioration OCR | OCR 100% success rate | 17 déc 2024 |
| 05 | Phase 1 Production Readiness | Logging + Exceptions + Tests | 19 déc 2024 |
| 06 | Phase 2 OCR Finalisation | Infrastructure OCR + Apprentissage auto | 19 déc 2024 |
| 07 | Tour Contrôle Refactorisation | Refactorisation Tour de Contrôle OCR | 20 déc 2024 |
| 08 | Phase 3 Build Installation | Build multi-OS + Installation bulletproof | 22 déc 2024 |
| 09 | Phase 4 Amélioration Site | Design, SEO, Performance | 22 déc 2024 |
| 10 | Phase 5 Release Feedback | Release 1.0 publiée | 22 déc 2024 |

📂 **Archive V3** : Les anciens documents V3 sont dans [_archive_v3/](ajouts/_archive_v3/)
📂 **Archive** : Fichier 04 archivé (contenu inclus dans 08) → [_archives/](ajouts/_archives/)

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
   - Documentation technique : `v4/modules/{module}/README.md`
3. **En cas d'erreur** → Chercher dans `erreurs/COMMON_ERRORS.md` puis `erreurs/`
4. **Pour comprendre l'historique** → Parcourir `ajouts/`
5. **Guides bibliothèques** → Consulter `help/`

### Pour les IA

**Workflow recommandé** :
1. **Commencer par** `INDEX.md` (ce fichier)
2. **Lire** `guides/IMPLEMENTATION_GUIDE.md` pour les règles générales
3. **Consulter** le module concerné :
   - Règles dans `modules/{module}-rules.md`
   - Doc technique dans `v4/modules/{module}/README.md`
4. **Vérifier** si l'erreur existe dans `erreurs/COMMON_ERRORS.md`
5. **Documenter** nouvelle feature dans `ajouts/YYYY-MM-DD_feature.md`

### 🤖 Pour l'Agent BIBLIOTHÉCAIRE

**Fichiers clés pour l'indexation** :
- `INDEX.md` - Point d'entrée principal (ce fichier)
- `GLOSSAIRE.md` - Définitions techniques centralisées
- `MAPPING.json` - Index rapide par catégorie
- `modules/INVENTAIRE_LIBRAIRIES.md` - Liste des 30 librairies Python
- `ARCHITECTURE.md` - Vue d'ensemble technique du projet

**Workflow de recherche recommandé** :
1. **Localiser** : Consulter `MAPPING.json` pour trouver le bon fichier
2. **Filtrer** : Lire le frontmatter YAML pour vérifier la pertinence
3. **Définir** : Utiliser `GLOSSAIRE.md` pour les termes techniques
4. **Chercher** : Utiliser ChromaDB pour la recherche sémantique

**Catégories de documents** :
- `guides/` - Règles générales d'implémentation (IMPLEMENTATION_GUIDE, BUILD)
- `modules/` - Règles spécifiques par module (database, services, UI, OCR, utils)
- `help/` - Guides des bibliothèques externes (pandas, plotly, streamlit, etc.)
- `ajouts/` - Historique chronologique des modifications (01-10)
- `erreurs/` - Catalogue des erreurs et solutions
- `walkthroughs/` - Sessions de développement détaillées

**Priorités de consultation** :
1. **Architecture** → `ARCHITECTURE.md` (vue d'ensemble)
2. **Règles** → `guides/IMPLEMENTATION_GUIDE.md` (règles strictes)
3. **Erreurs** → `erreurs/COMMON_ERRORS.md` (pièges à éviter)
4. **Contexte** → `ajouts/` (historique des décisions)

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
- 🔴 [Erreurs courantes](erreurs/COMMON_ERRORS.md)
- 📚 [Guides bibliothèques](help/)
- 📝 [Historique ajouts](ajouts/)

---

## 📊 Statistiques

| Catégorie | Nombre |
|-----------|--------|
| Guides généraux | 2 |
| Règles modules | 7 |
| Guides bibliothèques | 15 |
| Ajouts historiques | 10 (+ 6 archivés V3) |
| Erreurs documentées | 7 |
| Walkthroughs | 1 |
| **Total documents** | **56** |

---

**Dernière mise à jour** : 2 janvier 2026  
**Version bibliothèque** : 1.3
