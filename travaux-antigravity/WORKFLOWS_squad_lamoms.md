# 🔄 Workflows Squad Lamoms - Les 3 Scénarios

**Date** : 2 janvier 2026  
**Source** : Workflows manuscrits utilisateur

---

## 🛡️ Workflow 1 : DÉFENSIF (Maintenance & Bugs)

**Objectif** : Détecter et corriger automatiquement les bugs

### Diagramme

```
┌─────────────────────────────────────────────────────────┐
│                    LAMOMS-COACH                         │
│              (Détecte bug ou problème)                  │
└────────────────────────┬────────────────────────────────┘
                         │ Signale bug
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LAMOMS-BIBLIOTHÉCAIRE                      │
│   - Cherche dans base de connaissances                  │
│   - Décide : Bug connu ou nouveau ?                     │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
    Si bug CONNU                  Si problème NOUVEAU
             │                            │
             ↓                            ↓
┌────────────────────────┐    ┌─────────────────────────┐
│ LAMOMS-BIBLIOTHÉCAIRE  │    │ LAMOMS-BIBLIOTHÉCAIRE   │
│ - Donne pistes/        │    │ - Appelle EXPERT        │
│   solutions connues    │    └──────────┬──────────────┘
│ - "Voici comment on a  │               │
│   résolu ce bug avant" │               ↓
└────────────┬───────────┘    ┌─────────────────────────┐
             │                │   LAMOMS-EXPERT         │
             │                │   (Recherche Google)    │
             │                │   - Cherche infos       │
             │                │   - Trouve solutions    │
             │                └──────────┬──────────────┘
             │                           │ Renvoie infos
             │                           ↓
             │              ┌────────────────────────────┐
             │              │ LAMOMS-BIBLIOTHÉCAIRE      │
             │              │ - Enregistre nouvelles     │
             │              │   solutions trouvées       │
             │              └────────────┬───────────────┘
             │                           │
             └───────────────────────────┘
                         │ Top 3 solutions pré-filtrées
                         ↓
             ┌───────────────────────────┐
             │   LAMOMS-MÉCANICIEN       │
             │   (Modèle local - Ollama) │
             │   - Choisit meilleure     │
             │   - Applique la solution  │
             │   - FIXE le code          │
             │   - Teste                 │
             └───────────┬───────────────┘
                         │ Patch appliqué
                         ↓
             ┌───────────────────────────┐
             │     LAMOMS-COACH          │
             │   (Notifié : Bug corrigé) │
             └───────────────────────────┘
```

### Étapes Détaillées

1. **COACH** détecte un bug (erreur dans logs, crash, comportement anormal)

2. **COACH** signale à **BIBLIOTHÉCAIRE**

3. **BIBLIOTHÉCAIRE** analyse :
   - Cherche dans sa base de connaissances (ChromaDB + RAG)
   - **DÉCIDE** : Bug connu ou nouveau ?

4. **Deux chemins possibles** :
   
   **A. Bug CONNU** :
   - **BIBLIOTHÉCAIRE** trouve solutions dans base
   - **BIBLIOTHÉCAIRE** utilise RAG pour scorer les solutions
   - **BIBLIOTHÉCAIRE** pré-filtre : Top 3 meilleures solutions
   - **BIBLIOTHÉCAIRE** : "Voici les 3 meilleures façons de résoudre ce bug"
   
   **B. Problème NOUVEAU** :
   - **BIBLIOTHÉCAIRE** appelle **EXPERT**
   - **EXPERT** recherche sur Google/Stack Overflow/GitHub
   - **EXPERT** renvoie les infos à **BIBLIOTHÉCAIRE**
   - **BIBLIOTHÉCAIRE** enregistre les nouvelles solutions
   - **BIBLIOTHÉCAIRE** pré-filtre : Top 3 solutions trouvées

5. **BIBLIOTHÉCAIRE** envoie **Top 3 solutions pré-filtrées** à **MÉCANICIEN**

6. **MÉCANICIEN** (Modèle local - Ollama + Llama 3) :
   - Reçoit les 3 meilleures solutions
   - **Choisit** la plus adaptée au contexte
   - Applique la solution
   - **FIXE le code**
   - Teste la correction

7. **Patch appliqué** → **COACH** notifié : "✅ Bug corrigé !"

8. **BIBLIOTHÉCAIRE** enregistre :
   - Quelle solution a été choisie
   - Si ça a marché
   - Pour améliorer le scoring futur

---

## 🎨 Workflow 2 : CRÉATIF (Nouvelles Fonctionnalités)

**Objectif** : Développer une nouvelle fonctionnalité demandée par l'utilisateur

### Diagramme

```
┌─────────────────────────────────────────────────────────┐
│                    UTILISATEUR                          │
│   "Créer une nouvelle fonctionnalité"                   │
│   (Contient description + détails pour le codage)       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LAMOMS-PLANIFICATEUR                       │
│   - Entre une tâche                                     │
│   - Répartit et distribue correctement                  │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│               LAMOMS-MÉCANICIEN                         │
│   - Demande des infos sur les modèles                   │
│   - Demande templates de code                           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│             LAMOMS-BIBLIOTHÉCAIRE                       │
│   - Cherche modèles existants dans base                 │
│   - Fournit templates de code                           │
│   - Décide : Info existe ou manquante ?                 │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
    Si info EXISTE              Si info MANQUANTE
             │                            │
             │                            ↓
             │              ┌─────────────────────────────┐
             │              │     LAMOMS-EXPERT           │
             │              │   - Recherche documentation │
             │              │   - Trouve exemples Web     │
             │              └──────────┬──────────────────┘
             │                         │ Renvoie infos
             │                         ↓
             │              ┌─────────────────────────────┐
             │              │   LAMOMS-BIBLIOTHÉCAIRE     │
             │              │   - ENREGISTRE les infos    │
             │              │   - Met à jour base docs    │
             │              │   (NE MODIFIE PAS LE CODE)  │
             │              └──────────┬──────────────────┘
             │                         │
             └─────────────────────────┘
                         │ Renvoie infos et documentation
                         ↓
┌─────────────────────────────────────────────────────────┐
│               LAMOMS-MÉCANICIEN                         │
│   - Reçoit templates et documentation                   │
│   - DÉVELOPPE le code (seul à coder)                    │
│   - Incrémente la fonctionnalité                        │
│   - Teste la nouvelle feature                           │
└────────────────────────┬────────────────────────────────┘
                         │ Feature terminée
                         ↓
             ┌───────────────────────────┐
             │     LAMOMS-COACH          │
             │   (Notifie utilisateur)   │
             │   "✅ Fonctionnalité OK"  │
             └───────────────────────────┘
```

### Étapes Détaillées

1. **UTILISATEUR** demande nouvelle fonctionnalité
   - Fournit description
   - Donne détails pour le codage

2. **PLANIFICATEUR** organise :
   - Crée une tâche
   - Répartit le travail
   - Distribue aux bons agents

3. **MÉCANICIEN** démarre :
   - Demande infos sur les modèles existants
   - Demande templates de code

4. **BIBLIOTHÉCAIRE** cherche :
   - Fouille dans base de connaissances
   - Fournit templates existants
   - **DÉCIDE** : Info existe ou manquante ?

5. **Si info MANQUANTE** :
   - **BIBLIOTHÉCAIRE** appelle **EXPERT**
   - **EXPERT** recherche documentation externe
   - **EXPERT** trouve exemples sur Web
   - **EXPERT** renvoie à **BIBLIOTHÉCAIRE**
   - **BIBLIOTHÉCAIRE** **ENREGISTRE** les nouvelles infos
   - **BIBLIOTHÉCAIRE** met à jour base de docs
   - ⚠️ **BIBLIOTHÉCAIRE NE MODIFIE JAMAIS LE CODE**

6. **BIBLIOTHÉCAIRE** renvoie infos et documentation à **MÉCANICIEN**

7. **MÉCANICIEN** développe (SEUL à coder) :
   - Reçoit templates et documentation
   - **DÉVELOPPE le code**
   - Incrémente la fonctionnalité
   - Teste

8. **COACH** notifie utilisateur : "✅ Fonctionnalité prête !"

---

## 💰 Workflow 3 : SOCIAL (Conseils Financiers)

**Objectif** : Présenter des transactions et demander des conseils pour investissement dans une catégorie

### Diagramme

```
┌─────────────────────────────────────────────────────────┐
│                    UTILISATEUR                          │
│   "Présenter des transactions et demander conseils      │
│    pour investissement dans une catégorie"              │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  LAMOMS-COACH                           │
│   - Enregistre les requêtes                             │
│   - Compile dans la mémoire du portable                 │
└────────────────────────┬────────────────────────────────┘
                         │ Appelle pour des conseils
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 LAMOMS-ANALYSTE                         │
│   - Génère des conseils (si assez appris)               │
│   - Sinon → Envoie l'argument à MENTORE                 │
└────────────┬────────────────────────────┬───────────────┘
             │                            │
    Si ANALYSTE autonome        Si ANALYSTE pas encore prêt
             │                            │
             │                            ↓
             │              ┌─────────────────────────────┐
             │              │    LAMOMS-MENTORE           │
             │              │    - Donne les conseils     │
             │              │    - ANALYSTE observe       │
             │              └──────────┬──────────────────┘
             │                         │
             └─────────────────────────┘
                         │ Conseils générés
                         ↓
             ┌───────────────────────────┐
             │     LAMOMS-COACH          │
             │   - Affiche conseils      │
             │   - Collecte feedback 👍👎│
             └───────────┬───────────────┘
                         │
                         ↓
             ┌───────────────────────────┐
             │  LAMOMS-BIBLIOTHÉCAIRE    │
             │  - Stocke dans Dataset    │
             │    d'Or (si 👍)           │
             └───────────────────────────┘
```

### Étapes Détaillées

1. **UTILISATEUR** demande conseils :
   - Présente transactions
   - Demande conseils pour investissement dans catégorie

2. **COACH** prépare :
   - Enregistre les requêtes
   - Compile dans la mémoire du portable
   - Prépare contexte utilisateur

3. **COACH** appelle **ANALYSTE** pour générer conseils

4. **ANALYSTE** décide :
   
   **A. Si ANALYSTE a assez appris (Phase 4)** :
   - Génère conseils directement
   - Utilise son modèle local (Llama 3)
   - Coût = $0
   
   **B. Si ANALYSTE pas encore prêt (Phases 1-3)** :
   - Envoie l'argument à **MENTORE**
   - **MENTORE** génère conseils (Gemini)
   - **ANALYSTE** observe et apprend
   - Coût = ~$0.001

5. **Conseils générés** → Retour à **COACH**

6. **COACH** affiche à l'utilisateur :
   - Présente les conseils
   - Demande feedback (👍 Utile / 👎 Inutile)

7. **Si 👍** → **BIBLIOTHÉCAIRE** stocke :
   - Ajoute au Dataset d'Or
   - **ANALYSTE** apprend de cet exemple

8. **Si 👎** → Ignoré (pas stocké)

---

## 🎯 Résumé des Workflows

| Workflow | Déclencheur | Agents Principaux | Objectif |
|----------|-------------|-------------------|----------|
| **DÉFENSIF** | Bug détecté | BIBLIOTHÉCAIRE (décide), MÉCANICIEN (fixe) | Corriger automatiquement |
| **CRÉATIF** | Nouvelle fonctionnalité | PLANIFICATEUR, BIBLIOTHÉCAIRE (docs), MÉCANICIEN (code) | Développer feature |
| **SOCIAL** | Demande conseil | COACH, ANALYSTE, MENTORE | Conseiller financièrement |

---

## 💡 Points Clés

### Workflow Défensif
- ✅ **BIBLIOTHÉCAIRE** décide si bug connu ou nouveau
- ✅ **BIBLIOTHÉCAIRE** appelle EXPERT si nouveau
- ✅ **BIBLIOTHÉCAIRE** donne pistes de solution
- ✅ **MÉCANICIEN** applique et FIXE le code (seul à coder)
- ✅ **BIBLIOTHÉCAIRE** enregistre solutions

### Workflow Créatif
- ✅ Organisation par PLANIFICATEUR
- ✅ **BIBLIOTHÉCAIRE** fournit documentation (jamais de code)
- ✅ **BIBLIOTHÉCAIRE** enregistre nouvelles infos trouvées
- ✅ **MÉCANICIEN** développe le code (seul à coder)

### Workflow Social
- ✅ ANALYSTE apprend de MENTORE (teacher-student)
- ✅ Feedback utilisateur (👍/👎)
- ✅ Dataset d'Or pour autonomie future

---

## 🔑 Règles Absolues

### BIBLIOTHÉCAIRE
- ✅ **SAIT** comment résoudre (base de connaissances)
- ✅ **DÉCIDE** si problème connu ou nouveau
- ✅ **APPELLE** EXPERT si besoin
- ✅ **DONNE** pistes et documentation
- ✅ **ENREGISTRE** solutions et infos
- ❌ **NE MODIFIE JAMAIS LE CODE**

### MÉCANICIEN
- ✅ **SEUL** à modifier le code
- ✅ **APPLIQUE** les solutions suggérées
- ✅ **DÉVELOPPE** nouvelles fonctionnalités
- ✅ **TESTE** le code

---

## 🛠️ Choix Technologiques

### Modèles IA par Agent

| Agent | Modèle | Coût | Raison |
|-------|--------|------|--------|
| **COACH** | Gemini 2.0 Flash | ~$1/mois | Interface utilisateur, rapide |
| **MÉCANICIEN** | **Ollama + Llama 3 8B (local)** | **$0/mois** | **Formation, apprentissage, gratuit** |
| **BIBLIOTHÉCAIRE** | ChromaDB + Embeddings | $0 | RAG local, pré-filtrage |
| **ANALYSTE** | Llama 3 8B (local) | $0/mois | Apprentissage, autonomie |
| **MENTORE** | Gemini 1.5 Flash | ~$1/mois | Teacher temporaire |
| **EXPERT** | n8n + Web scraping | $0 | Recherche Web |
| **PLANIFICATEUR** | Python + APIs | $0 | Telegram, Calendar |

### Stratégie Formation → Performance

**Phase 1-2 (Formation - 2-4 mois)** :
- ✅ **MÉCANICIEN** = Ollama + Llama 3 8B (local, gratuit)
- ✅ Vous apprenez LangChain, ChromaDB, RAG
- ✅ Coût total : ~$2/mois (juste COACH + MENTORE)
- ✅ Objectif : **Apprendre**, pas performer

**Phase 3+ (Performance - si besoin)** :
- ⚠️ Si MÉCANICIEN local pas assez bon
- ⚠️ Upgrade vers Claude 3.5 Sonnet (~$10/mois)
- ⚠️ Ou fine-tuner Llama 3 sur votre codebase
- ✅ Décision basée sur résultats réels

### Avantages Modèle Local (Ollama)

**Pour MÉCANICIEN** :
- ✅ **Gratuit** - Parfait pour apprendre
- ✅ **Offline** - Fonctionne sans internet
- ✅ **Privé** - Code reste sur votre PC
- ✅ **Rapide** - Pas de latence API
- ✅ **Évolutif** - Peut fine-tuner plus tard

**Inconvénients** :
- ⚠️ Moins bon que Claude 3.5 Sonnet (au début)
- ⚠️ Nécessite RAM (8GB minimum)
- ⚠️ Peut faire des erreurs

**Solution** :
- ✅ BIBLIOTHÉCAIRE pré-filtre → Aide MÉCANICIEN
- ✅ Vous apprenez à débugger
- ✅ Upgrade si vraiment nécessaire

---

**Évolution** : 
- **Phase 1-2** : Formation avec modèles locaux gratuits
- **Phase 3** : ANALYSTE autonome, MENTORE désactivé
- **Phase 4** : Décision performance (local vs cloud)

**Coût Phase 1-2** : ~$2/mois (quasi gratuit !)

**Vision** : Squad autonome, intelligente et **gratuite** ! 🚀
