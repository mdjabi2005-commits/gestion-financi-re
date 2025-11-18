# 📦 Guide d'Export des Logs OCR pour le Support

## 🎯 Objectif

Ce guide explique comment exporter et envoyer vos logs OCR au support pour améliorer continuellement la détection automatique de montants dans l'application Gestio.

---

## 📋 Contenu de l'Export

Lorsque vous créez un export de logs OCR, le fichier ZIP contient :

### 1. **Dossier `ocr_logs/`**

| Fichier | Description | Utilité |
|---------|-------------|---------|
| `scan_history.jsonl` | Historique complet de tous les scans | Identifier les taux de succès par période |
| `potential_patterns.jsonl` | Patterns potentiels détectés automatiquement | Découvrir de nouveaux formats de tickets |
| `performance_stats.json` | Statistiques globales de performance | Mesurer l'efficacité par type de document |
| `pattern_stats.json` | Fiabilité de chaque pattern | Optimiser les patterns existants |
| `pattern_log.json` | Occurrences des patterns | Comprendre la fréquence d'utilisation |

### 2. **Dossier `problematic_metadata/`**

Métadonnées (JSON uniquement, pas d'images) des tickets où la détection a échoué ou était peu fiable.

Chaque fichier contient :
- Nom du fichier original
- Montant détecté
- Méthode de détection utilisée
- Patterns potentiels trouvés
- Date du déplacement

### 3. **Fichier `SUMMARY.json`**

Résumé de l'export avec :
- Date d'export
- Nombre total de scans
- Nombre de patterns potentiels
- Performance par type de document
- Liste des fichiers inclus

### 4. **Fichier `README.txt`**

Instructions et informations sur le contenu de l'export.

---

## 🔒 Confidentialité et Sécurité

### ✅ Ce qui EST inclus :
- Métadonnées techniques (montants, méthodes, patterns)
- Statistiques de performance
- Patterns détectés
- Dates et timestamps

### ❌ Ce qui N'EST PAS inclus :
- **Aucune image** de ticket ou facture
- **Aucune donnée personnelle** (nom, adresse, numéro de carte)
- **Aucun texte OCR complet** (seulement les patterns extraits)
- **Aucune information bancaire**

**Verdict : 100% sûr pour l'envoi au support**

---

## 📧 Comment Envoyer les Logs au Support

### Option 1 : Email (Recommandé)

```
À : support@gestio.app (à remplacer par votre email de support)
Sujet : Logs OCR pour amélioration - [Votre Nom/ID Utilisateur]
```

**Corps du message :**
```
Bonjour,

Je vous envoie mes logs OCR pour vous aider à améliorer la détection.

Informations complémentaires :
- Nombre de scans : [voir SUMMARY.json]
- Types de tickets principaux : [Supermarché, Restaurant, etc.]
- Problèmes rencontrés : [Optionnel - décrire les types de tickets qui posent problème]

Merci,
[Votre Nom]
```

### Option 2 : Cloud Storage

1. **Uploader le fichier :**
   - Google Drive
   - Dropbox
   - OneDrive
   - WeTransfer (pour fichiers > 10MB)

2. **Générer un lien de partage**

3. **Envoyer le lien par email** (modèle ci-dessus)

### Option 3 : GitHub Issue

Pour les développeurs ou utilisateurs avancés :

1. Créer une issue sur le repo GitHub
2. Label : `enhancement`, `ocr-improvement`
3. Attacher le fichier ZIP ou lien cloud
4. Décrire les problèmes rencontrés

---

## 🔍 Analyser les Logs (Pour le Support)

### Structure des Logs JSONL

Chaque ligne est un objet JSON :

```json
{
  "timestamp": "2025-11-18T10:30:00",
  "document_type": "ticket",
  "filename": "ticket_123.jpg",
  "montants_detectes": [12.50, 10.00],
  "montant_choisi": 12.50,
  "categorie": "alimentation",
  "sous_categorie": "supermarche",
  "patterns_detectes": ["TOTAL", "TTC"],
  "success_level": "exact",
  "methode_detection": "A-PATTERNS"
}
```

### Méthodes de Détection

| Code | Description | Fiabilité |
|------|-------------|-----------|
| `A-PATTERNS` | Patterns directs (TOTAL, MONTANT) | ⭐⭐⭐⭐⭐ Excellente |
| `B-PAIEMENT` | Somme des paiements (CB, CARTE) | ⭐⭐⭐⭐ Très bonne |
| `C-HT+TVA` | Calcul HT + TVA | ⭐⭐⭐⭐ Très bonne |
| `D-FALLBACK` | Plus grand montant trouvé | ⭐⭐ Faible |
| `AUCUNE` | Aucun montant détecté | ❌ Échec |

### Niveaux de Succès

- `exact` : Montant détecté en premier = montant choisi
- `partial` : Montant dans la liste mais pas en premier
- `failed` : Montant choisi absent de la liste (correction manuelle)

### Patterns Potentiels

Format dans `potential_patterns.jsonl` :

```json
{
  "timestamp": "2025-11-18T10:30:00",
  "filename": "ticket_carrefour.jpg",
  "montant_final": 12.50,
  "methode_detection": "D-FALLBACK",
  "patterns": [
    {
      "pattern": "PAYÉ",
      "line": "PAYÉ : 12,50€",
      "amount": "12,50",
      "raw_label": "Payé"
    }
  ]
}
```

---

## 🚀 Amélioration Continue

### Workflow d'Amélioration

```
1. Utilisateur scanne des tickets
   ↓
2. Système détecte et logue tout
   ↓
3. Utilisateur exporte les logs
   ↓
4. Support analyse les logs
   ↓
5. Identification de nouveaux patterns
   ↓
6. Ajout aux patterns connus
   ↓
7. Mise à jour de l'application
   ↓
8. Meilleure détection pour tous !
```

### Exemples de Patterns Découverts

Grâce aux logs utilisateurs, nous avons ajouté :

- ✅ `MONTANT EUR` (Leclerc)
- ✅ `NET A PAYER` (Auchan)
- ✅ `À PAYER` (Lidl)
- ✅ `TOTAL TTC` (Carrefour)

### Métriques Clés

Le support analyse :

1. **Taux de succès global**
   - Cible : > 85% de détection exacte
   - Actuel : Varie selon les utilisateurs

2. **Patterns manquants**
   - Combien de fois D-FALLBACK est utilisé
   - Patterns potentiels les plus fréquents

3. **Types de documents problématiques**
   - Quels types ont le pire taux de réussite
   - Formats spécifiques à ajouter

4. **Performance temporelle**
   - Amélioration au fil du temps
   - Régression potentielle

---

## 💡 FAQ

### Combien de fois dois-je envoyer mes logs ?

**Recommandation :** Une fois par mois ou après ~50 scans

### Les logs sont-ils supprimés après envoi ?

Non, ils restent sur votre machine. Le fichier ZIP peut être supprimé manuellement.

### Puis-je voir ce qu'il y a dans le ZIP avant d'envoyer ?

Oui ! Ouvrez le fichier ZIP et consultez `README.txt` et `SUMMARY.json`

### Que se passe-t-il avec mes logs après envoi ?

1. Analyse automatisée des patterns
2. Identification des améliorations possibles
3. Ajout aux patterns connus
4. Suppression après traitement (conformité RGPD)

### Les logs contiennent-ils des informations sensibles ?

Non. Uniquement des métadonnées techniques (montants, méthodes). Aucune image, aucun texte complet.

---

## 📞 Contact Support

**Email :** support@gestio.app (à remplacer)
**GitHub :** https://github.com/your-repo/gestio
**Documentation :** https://docs.gestio.app

---

## 🙏 Remerciements

Merci d'aider à améliorer Gestio ! Chaque export de logs contribue à créer une meilleure expérience pour tous les utilisateurs.

**Impact de votre contribution :**
- ✨ Meilleure détection pour vous
- 🌍 Meilleure détection pour la communauté
- 🚀 Application plus intelligente et performante
- 💡 Découverte de nouveaux formats automatiquement

---

*Document généré le 18/11/2025*
*Version 1.0*
