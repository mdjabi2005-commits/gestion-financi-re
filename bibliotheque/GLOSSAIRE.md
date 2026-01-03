# 📚 Glossaire Technique - Gestio V4

**Dernière mise à jour** : 2 janvier 2026

---

## A

### Agent IA
Programme d'intelligence artificielle capable de raisonner et d'utiliser des outils pour accomplir des tâches de manière autonome.

### Architecture en couches
Organisation du code en couches distinctes (UI, Services, Database, Config) avec dépendances unidirectionnelles.

---

## C

### ChromaDB
Base de données vectorielle pour stocker et rechercher des embeddings de texte. Utilisée pour la recherche sémantique.

---

## D

### DataClass
Décorateur Python (`@dataclass`) qui génère automatiquement `__init__`, `__repr__`, `__eq__`, etc. Utilisé pour les modèles de données comme `Transaction`.

### Domain-Driven Design (DDD)
Architecture qui organise le code par domaine métier (transactions, OCR, etc.) plutôt que par type technique.

---

## E

### Embeddings
Représentation vectorielle (numérique) d'un texte permettant la recherche sémantique. Chaque texte est converti en vecteur de nombres.

---

## L

### LangChain
Framework Python pour créer des applications utilisant des LLM avec outils et mémoire.

### LangGraph
Extension de LangChain pour créer des agents avec état et mémoire conversationnelle. Permet de gérer des workflows complexes.

---

## O

### OCR (Optical Character Recognition)
Reconnaissance optique de caractères - extraction de texte depuis des images de tickets/factures.

---

## R

### RAG (Retrieval-Augmented Generation)
Technique où l'agent cherche dans une base de connaissances avant de générer une réponse. Combine recherche et génération.

### Repository Pattern
Pattern qui sépare la logique métier de l'accès aux données.  
**Exemple** : `TransactionRepository.get_all()` au lieu de SQL direct.

### Récurrence
Transaction qui se répète automatiquement (mensuelle, hebdomadaire, etc.). Gérée par le système de récurrence.

---

## S

### Streamlit
Framework Python pour créer des interfaces web interactives. Utilisé pour l'UI de Gestio V4.

---

## T

### Tool (Outil)
Fonction Python décorée avec `@tool` que l'agent peut utiliser. L'agent choisit quel outil utiliser selon le contexte.

---

## V

### Vectorisation
Transformation de texte en vecteurs numériques pour recherche sémantique. Permet de trouver des documents similaires.

---

**Total termes** : 15+

**Pour ajouter un terme** : Créer une Pull Request ou modifier ce fichier directement.
