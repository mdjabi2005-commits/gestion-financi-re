# 📚 Documentation Modules v4

Ce dossier contient la **documentation technique détaillée** de chaque module de l'application.

---

## 📋 Fichiers Disponibles

### Modules Domains

- **[ocr-rules.md](./ocr-rules.md)** - Module OCR (extraction tickets/factures)
  - Règles extraction/parsing
  - 4 méthodes détection montants
  - Système apprentissage auto
  - Leçons critiques (patterns, normalisation)

### Modules Shared

- **[database-rules.md](./database-rules.md)** - Gestion base de données SQLite
  - Règles connexions/transactions
  - Schéma et migrations
  - Bonnes pratiques SQL

- **[services-rules.md](./services-rules.md)** - Services partagés
  - Récurrences financières
  - Gestion fichiers associés
  - Services fractals

- **[ui-rules.md](./ui-rules.md)** - Composants UI Streamlit
  - Règles composants réutilisables
  - Styles et thèmes
  - Gestion erreurs UI

- **[utils-rules.md](./utils-rules.md)** - Fonctions utilitaires
  - Conversions sécurisées
  - Validation données
  - Formatage

---

## 🔗 Liens Rapides

### README Complets Modules

Pour la documentation complète de chaque module (architecture, exemples, API) :

- [domains/ocr/README.md](../../v4/domains/ocr/README.md) - OCR complet
- [domains/home/README.md](../../v4/domains/home/README.md) - Dashboard
- [domains/portfolio/README.md](../../v4/domains/portfolio/README.md) - Portefeuille
- [domains/transactions/README.md](../../v4/domains/transactions/README.md) - Transactions
- [domains/revenues/README.md](../../v4/domains/revenues/README.md) - Revenus

### Documentation Architecture

- [ARCHITECTURE.md](../ARCHITECTURE.md) - Vue d'ensemble complète
- [BUILD.md](../guides/BUILD.md) - Guide de build
- [INDEX.md](../INDEX.md) - Navigation principale

---

## 📖 Comment Utiliser

**Pour implémenter une fonctionnalité** :
1. Lire le fichier `-rules.md` du module concerné
2. Suivre les règles strictes définies
3. Consulter le README complet pour exemples
4. Référer aux leçons critiques pour éviter les pièges

**Pour débugger** :
1. Vérifier les règles du module
2. Consulter les erreurs courantes listées
3. Utiliser les checklists fournies

---

**Organisation** : 
- `*-rules.md` = Règles techniques strictes + leçons apprises
- `v4/*/README.md` = Documentation complète + exemples code
