# 📁 Dossier `/scripts`

## 🎯 But du dossier

Ce dossier contient des **scripts de maintenance et migration** - utilitaires ponctuels pour réparer, migrer ou transformer les données. Ces scripts ne sont pas appelés par l'application elle-même, mais exécutés manuellement quand nécessaire.

---

## 📄 Fichiers

### 1. `migrate_files_to_id.py`
**Rôle** : Renomme tous les fichiers tickets existants avec l'ID de leur transaction.

**Problème résolu** : Les anciens tickets étaient nommés `ticket.jpg`, `ticket_1.jpg`, etc. Ce script les renomme en `{transaction_id}.jpg` pour correspondre au nouveau système.

**Utilisation** :
```bash
python scripts/migrate_files_to_id.py
```

**Ce qu'il fait** :
1. Parcourt tous les tickets dans `SORTED_DIR`
2. Pour chaque fichier, trouve sa transaction associée en base
3. Renomme le fichier avec l'ID de transaction
4. Met à jour les chemins en base si nécessaire

**Exemple** :
```
Avant : data/tickets_tries/Alimentation/Restaurant/ticket_23.jpg
Après : data/tickets_tries/Alimentation/Restaurant/1234.jpg
```

---

### 2. `normalize_categories.py`
**Rôle** : Normalise toutes les catégories existantes en base de données.

**Problème résolu** : Catégories incohérentes ("alimentation", "Alimentation", "ALIMENTATION")

**Utilisation** :
```bash
python scripts/normalize_categories.py
```

**Ce qu'il fait** :
1. Lit toutes les transactions
2. Applique `normalize_category()` et `normalize_subcategory()`
3. Met à jour en base
4. Déplace les fichiers vers les dossiers normalisés

**Exemple** :
```
Avant : "transport" → Après : "Transport"
Avant : "courses mensuelles" → Après : "Courses Mensuelles"
```

---

### 3. `migrate_recurrences_clean.py`
**Rôle** : Migration propre des transactions récurrentes vers le nouveau système d'échéances.

**Problème résolu** : Ancienne gestion des récurrences à améliorer

**Usage** :
```bash
python scripts/migrate_recurrences_clean.py
```

**Ce qu'il fait** :
1. Supprime les anciennes récurrences auto-générées
2. Reconstruit à partir des définitions de récurrence
3. Génère toutes les échéances futures
4. Nettoie les doublons

---

### 4. `diagnose_recurrences.py`
**Rôle** : Diagnostic des problèmes de récurrences.

**Utilisation** :
```bash
python scripts/diagnose_recurrences.py
```

**Affiche** :
- Nombre de transactions récurrentes définies
- Nombre d'échéances générées
- Transactions en double
- Récurrences manquantes
- Problèmes de dates

---

### 5. `cleanup_id_suffixes.py`
**Rôle** : Nettoie les suffixes "_1", "_2" dans les noms de fichiers.

**Problème résolu** : Doublons de fichiers avec suffixes

**Usage** :
```bash
python scripts/cleanup_id_suffixes.py
```

**Exemple** :
```
1234_1.jpg → 1234.jpg (si pas de conflit)
```

---

### 6. `test_csv_export.py`
**Rôle** : Teste la fonctionnalité d'export CSV.

**Usage** :
```bash
python scripts/test_csv_export.py
```

**Ce qu'il fait** :
- Exporte les transactions sans tickets vers CSV
- Affiche les statistiques
- Vérifie l'intégrité des données exportées

---

## ⚠️ Points d'attention

1. **Scripts ponctuels** : À exécuter manuellement, pas intégrés à l'app
2. **Backup recommandé** : Toujours sauvegarder `finances.db` avant migration
3. **Exécution unique** : La plupart sont conçus pour 1 seule exécution
4. **Logs détaillés** : Tous affichent ce qu'ils font

---

## 🔄 Ordre d'exécution recommandé (migration complète)

Si tu veux tout nettoyer/normaliser :

```bash
# 1. Backup !
cp data/finances.db data/finances.db.backup

# 2. Normaliser les catégories
python scripts/normalize_categories.py

# 3. Nettoyer les noms de fichiers
python scripts/cleanup_id_suffixes.py

# 4. Renommer par ID
python scripts/migrate_files_to_id.py

# 5. Nettoyer les récurrences
python scripts/migrate_recurrences_clean.py

# 6. Vérifier
python scripts/diagnose_recurrences.py
```

---

## 💡 Quand utiliser chaque script

| Script | Quand l'utiliser |
|--------|------------------|
| `migrate_files_to_id.py` | Après migration vers système ID |
| `normalize_categories.py` | Catégories incohérentes |
| `migrate_recurrences_clean.py` | Problèmes de récurrences |
| `diagnose_recurrences.py` | Debug récurrences |
| `cleanup_id_suffixes.py` | Fichiers dupliqués avec suffixes |
| `test_csv_export.py` | Tester l'export CSV |

---

## 🔗 Dépendances

**Internes** :
- `config` - Chemins
- `modules.database` - Accès données
- `modules.services` - Normalisation, file_service

**Externes** :
- `os`, `shutil` - Manipulation fichiers
- `sqlite3` - Base de données
- `pandas` - Analyse données

---

## ✅ Bonnes pratiques

**Avant d'exécuter un script** :
1. ✅ Lire le code pour comprendre ce qu'il fait
2. ✅ Sauvegarder `finances.db`
3. ✅ Vérifier qu'il n'y a pas de processus qui utilise la DB
4. ✅ Lire les logs pendant l'exécution

**Après exécution** :
1. ✅ Vérifier les logs
2. ✅ Tester l'application
3. ✅ Garder le backup quelques jours
