# Module OCR - Résumé

> 📖 **README complet** : [v4/domains/ocr/README.md](../../v4/domains/ocr/README.md)

---

## 🎯 Rôle du Module

**Extraction automatique d'informations** depuis tickets/factures via OCR (Optical Character Recognition).

**Fonctionnalité principale** : Scanner un ticket → Extraire montant + date + catégorie

---

## 📁 Architecture

```
domains/ocr/
├── scanner.py              # Extraction texte (Tesseract OCR)
├── parsers.py              # Analyse texte → métadonnées
├── pattern_manager.py      # Gestion patterns détection
├── scanning_service.py     # Orchestration scan complet
├── learning_service.py     # Système apprentissage auto 🧠
├── learning_ui.py          # Interface apprentissage
├── logging.py              # Logs OCR (scan_history, stats)
├── export_logs.py          # Export ZIP support
├── diagnostics.py          # Debug OCR
└── pages/
    ├── scanning.py         # UI scan tickets
    ├── tour_controle_simplifie.py  # Debug & analyse
    └── ...
```

---

## ⚙️ Fonctionnalités Clés

### 1. **Extraction OCR Multi-Format**
- Images (JPG, PNG) → Tesseract OCR
- PDF → PyMuPDF extraction

### 2. **Détection Montants (4 Méthodes)**
- **Méthode A** : Amount patterns (TOTAL, MONTANT)
- **Méthode B** : Payment patterns (CB, CARTE)
- **Méthode C** : HT/TVA calculation
- **Méthode D** : Fallback (dernier montant)

### 3. **Cross-Validation**
- Compare résultats des 4 méthodes
- Fiabilité = 2+ méthodes identiques

### 4. **Système d'Apprentissage Auto** 🧠
- Analyse corrections utilisateur
- Suggère nouveaux patterns
- S'améliore automatiquement

### 5. **Logging Complet**
- `scan_history.jsonl` - Historique scans
- `performance_stats.json` - Stats par type
- `pattern_stats.json` - Fiabilité patterns

---

## 🔗 Fichiers Config

- `config/ocr_patterns.yml` - Patterns détection
- `config/ocr_patterns_learned.yml` - Patterns appris

---

## 📊 Métriques

- **52 patterns actifs** (TOTAL, MONTANT, CB, etc.)
- **4 méthodes détection** en parallèle
- **85-95% taux succès** (selon type document)
- **Système apprentissage** : Amélioration continue

---

## 🧪 Tests

- **20 tests unitaires** (Pattern Manager, Parsers)
- **8 tests intégration** (Learning system)
- **Coverage** : ~85%

**Localisation** : `tests/test_ocr/`

---

## 📝 Documentation Complète

**Pour détails techniques complets, architecture interne, exemples code** :
👉 [v4/domains/ocr/README.md](../../v4/domains/ocr/README.md)

**Guides spécifiques** :
- Patterns : `v4/domains/ocr/PATTERNS.md`
- Debug : `v4/domains/ocr/DEBUG_GUIDE.md`

---

**Dernière mise à jour** : 20 décembre 2024
