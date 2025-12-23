# 📚 Bibliothèque : PyYAML

## 🎯 Qu'est-ce que PyYAML ?

**PyYAML** est LA bibliothèque Python pour **lire et écrire des fichiers YAML** (YAML Ain't Markup Language). YAML est un format de sérialisation de données lisible par l'homme, idéal pour les fichiers de configuration.

**Site officiel** : https://pyyaml.org  
**Documentation** : https://pyyaml.org/wiki/PyYAMLDocumentation

---

## 💡 Pourquoi YAML dans notre projet ?

1. **Configuration OCR** : Patterns de détection dans `/config/ocr_patterns.yml`
2. **Lisibilité** : Format clair et hiérarchique
3. **Commentaires** : Documentation inline possible
4. **Maintenance** : Facile à éditer manuellement
5. **Apprentissage** : Patterns appris sauvegardés dans `ocr_patterns_learned.yml`

---

## 🔧 Concepts de base

### 1. Structure YAML

```yaml
# Commentaire
cle_simple: valeur

# Liste
liste:
  - item1
  - item2
  - item3

# Dictionnaire imbriqué
config:
  database:
    path: "data/finances.db"
    timeout: 30
  ocr:
    enabled: true
```

### 2. Types de données

```yaml
# String
name: "Gestio V4"
titre: Gestion Financière  # Quotes optionnelles

# Number
version: 4.0
max_items: 100

# Boolean
debug_mode: true
production: false

# Null
description: null
```

---

## 📊 Exemples concrets de notre app

### Charger patterns OCR (`pattern_manager.py`)

```python
import yaml
from pathlib import Path

# Chemin du fichier
patterns_file = Path(__file__).parent / "config" / "ocr_patterns.yml"

# Lecture sécurisée
with open(patterns_file, 'r', encoding='utf-8') as f:
    patterns_data = yaml.safe_load(f)

# Accès aux données
amount_patterns = patterns_data.get('amount_patterns', [])
for pattern in amount_patterns:
    regex = pattern['pattern']
    priority = pattern['priority']
    enabled = pattern['enabled']
    
    if enabled:
        print(f"Pattern actif : {regex} (priorité {priority})")
```

### Structure de `ocr_patterns.yml`

```yaml
amount_patterns:
  - pattern: "MONTANT\\s*(REEL|KEEL)"
    priority: 1
    enabled: true
    description: "Tickets essence CB"
  
  - pattern: "TOTAL\\s*(TTC|TIC)"
    priority: 2
    enabled: true
    description: "Total TTC tickets"
  
  - pattern: "CB\\s*(?:DEBIT|CREDIT)?"
    priority: 3
    enabled: true
    description: "Paiement carte bancaire"

payment_patterns:
  - "CB"
  - "CARTE"
  - "PATEMENT"  # Erreur OCR courante
  - "DEBIT"
  - "CREDIT"
```

### Sauvegarder un pattern appris

```python
import yaml

# Nouveau pattern découvert par apprentissage
new_pattern = {
    'pattern': r"SOMME\\s*A\\s*PAYER",
    'priority': 10,
    'enabled': true,
    'description': "Montant à payer (appris)",
    'learned_from': "ticket_12345.jpg",
    'confidence': 0.95
}

# Charger fichier existant
with open('config/ocr_patterns_learned.yml', 'r', encoding='utf-8') as f:
    learned = yaml.safe_load(f) or {'amount_patterns': []}

# Ajouter le nouveau pattern
learned['amount_patterns'].append(new_pattern)

# Sauvegarder
with open('config/ocr_patterns_learned.yml', 'w', encoding='utf-8') as f:
    yaml.safe_dump(learned, f, 
                   default_flow_style=False,  # Format lisible
                   allow_unicode=True,        # Support accents
                   sort_keys=False)           # Garde l'ordre

print("✅ Pattern appris sauvegardé")
```

---

## ⚠️ Pièges courants

### 1. Indentation (espaces uniquement !)

```yaml
# ❌ Erreur : tabulations
config:
	path: "data/db"  # TAB = ERREUR

# ✅ Correct : espaces
config:
  path: "data/db"  # 2 espaces
```

### 2. Quotes pour valeurs spéciales

```yaml
# ❌ Interprété comme boolean
pattern: "true"  

# ✅ String
pattern: "true"

# ❌ Interprété comme nombre
code: 001

# ✅ String
code: "001"
```

### 3. safe_load vs load

```python
# ✅ Toujours utiliser safe_load
data = yaml.safe_load(file)

# ❌ Dangereux ! Peut exécuter du code
data = yaml.load(file)  # INTERDIT

# ✅ Si vraiment nécessaire
data = yaml.load(file, Loader=yaml.FullLoader)
```

### 4. Encodage UTF-8

```python
# ❌ Erreur avec accents
with open('config.yml', 'r') as f:
    data = yaml.safe_load(f)

# ✅ Toujours spécifier encoding
with open('config.yml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
```

---

## 🔥 Opérations avancées

### Valider le schéma YAML

```python
import yaml
from cerberus import Validator

# Définir schéma attendu
schema = {
    'amount_patterns': {
        'type': 'list',
        'schema': {
            'type': 'dict',
            'schema': {
                'pattern': {'type': 'string', 'required': True},
                'priority': {'type': 'integer', 'required': True},
                'enabled': {'type': 'boolean', 'required': True}
            }
        }
    }
}

# Charger et valider
with open('config/ocr_patterns.yml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

v = Validator(schema)
if not v.validate(data):
    print(f"❌ Erreur validation : {v.errors}")
else:
    print("✅ YAML valide")
```

### Merger deux fichiers YAML

```python
import yaml

# Charger patterns de base
with open('ocr_patterns.yml', 'r', encoding='utf-8') as f:
    base_patterns = yaml.safe_load(f)

# Charger patterns appris
with open('ocr_patterns_learned.yml', 'r', encoding='utf-8') as f:
    learned_patterns = yaml.safe_load(f) or {'amount_patterns': []}

# Merger
all_patterns = base_patterns.copy()
all_patterns['amount_patterns'].extend(
    learned_patterns.get('amount_patterns', [])
)

print(f"Total patterns : {len(all_patterns['amount_patterns'])}")
```

---

## 📖 Ressources

- **Documentation** : https://pyyaml.org/wiki/PyYAMLDocumentation
- **Spécification YAML** : https://yaml.org/spec/
- **Validator** : https://docs.python-cerberus.org/

---

## 💡 YAML dans notre projet

| Fichier | Utilisation |
|---------|------------|
| `config/ocr_patterns.yml` | Patterns de détection OCR (52 patterns actifs) |
| `config/ocr_patterns_learned.yml` | Patterns appris automatiquement |
| `pattern_manager.py` | Chargement et gestion des patterns |
| `learning_service.py` | Sauvegarde des patterns appris |

**Commande d'installation** :
```bash
pip install PyYAML
```

**Bonnes pratiques** :
- ✅ Toujours utiliser `yaml.safe_load`
- ✅ Spécifier `encoding='utf-8'`
- ✅ Valider le schéma si données critiques
- ❌ Ne jamais utiliser `yaml.load` sans loader sécurisé
- ❌ Ne pas mélanger espaces et tabulations
