# 🚀 Lancer la Navigation Fractale

## Méthode 1️⃣ : Script de lancement (Recommandé)

```bash
cd "C:\Users\djabi\gestion-financière\v3"
python run_fractal.py
```

Le script gère automatiquement les chemins Python.

---

## Méthode 2️⃣ : Streamlit direct

```bash
cd "C:\Users\djabi\gestion-financière\v3"
streamlit run pages/fractal_view.py
```

---

## Méthode 3️⃣ : Depuis le répertoire parent

```bash
cd "C:\Users\djabi\gestion-financière"
streamlit run v3/pages/fractal_view.py
```

---

## ✅ Vérification

Une fois lancée, l'application doit:

1. ✅ S'ouvrir automatiquement à `http://localhost:8501`
2. ✅ Afficher le titre "🔺 Navigation Fractale"
3. ✅ Montrer le sidebar avec les options de date
4. ✅ Afficher les statistiques (4 cartes)
5. ✅ Afficher le composant fractal interactif

---

## 🔧 Si vous avez des erreurs

### Erreur: "ModuleNotFoundError: No module named 'modules'"

**Solution:** Utilisez la Méthode 1 ou 2 (pas depuis un autre répertoire)

```bash
cd v3
python run_fractal.py
```

### Erreur: "Cannot find the component"

**Solution:** Le composant personnalisé n'est pas disponible en mode développement. C'est normal.
Les données s'affichent quand même.

### Page vide / qui ne charge pas

**Solutions:**
1. Attendez 5 secondes
2. Rafraîchissez (F5)
3. Vérifiez qu'il y a des données : `sqlite3 ~/analyse/transactions.db "SELECT COUNT(*) FROM transactions;"`
4. Regardez la console pour les messages d'erreur

### Erreur: "No data available"

**Solution:** Vérifiez que vous avez des transactions dans la base de données.

```bash
# Créer quelques données de test
python test_fractal_service.py
```

---

## 🎯 Commandes utiles

### Voir les logs en détail

```bash
streamlit run pages/fractal_view.py --logger.level=debug
```

### Lancer sur un port différent

```bash
streamlit run pages/fractal_view.py --server.port=8502
```

### Désactiver le mode headless (pour le développement)

```bash
streamlit run pages/fractal_view.py --server.headless=false
```

---

## 🚀 Résumé

| Méthode | Commande | Avantages |
|---------|----------|-----------|
| **Script** | `python run_fractal.py` | Gère les chemins automatiquement |
| **Streamlit direct** | `streamlit run pages/fractal_view.py` | Plus simple |
| **Depuis parent** | `streamlit run v3/pages/fractal_view.py` | Flexible |

**Recommandé:** Utilisez le **script de lancement** pour éviter les problèmes de chemin.

```bash
python run_fractal.py
```

---

## 📝 Notes

- La première fois peut prendre 10-15 secondes à se charger
- Streamlit recompile automatiquement si vous modifiez le code
- Les changements aparaissent après le rechargement

---

**Vous êtes prêt!** 🎉

