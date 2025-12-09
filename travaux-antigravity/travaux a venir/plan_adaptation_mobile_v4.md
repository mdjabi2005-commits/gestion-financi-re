# Plan d'Adaptation Mobile - Gestion Financière v4

**Date** : 03 Décembre 2025
**Contexte** : Ce document est une archive du plan d'implémentation technique pour porter l'application `v4` sur mobile (Android/iOS) via Kivy. Il a été établi suite à l'analyse des besoins (fichier Excel `vmobile`) et de la structure du code `v4`.
**Statut** : En attente (À lancer une fois la v4 finalisée).

---

# Plan d'Implémentation - Adaptation Mobile (v4 vers Kivy)

## Objectif
Adapter la version `v4` de l'application "Gestion Financière" pour les appareils mobiles (Android/iOS) en utilisant **Kivy/KivyMD**. L'objectif est de réutiliser la logique backend robuste de `v4` (Services, Base de données, Utilitaires) tout en remplaçant l'interface Streamlit par une interface mobile native.

## Revue Utilisateur Requise
> [!IMPORTANT]
> **Stratégie OCR** : `pytesseract` ne peut pas être utilisé directement sur mobile.
> **Proposition** : Implémenter une **Interface OCR Abstraite**.
> - **Bureau** : Utilise `pytesseract` (existant).
> - **Mobile** : Utilise **Google ML Kit** (via wrapper Kivy) ou une API Cloud (ex: Google Cloud Vision).
> *Décision nécessaire* : Vise-t-on le "offline-first" (ML Kit - plus dur à configurer) ou "online" (API Cloud - plus facile mais payant/nécessite internet) ? *Hypothèse par défaut : Offline-first via ML Kit ou OCR local simplifié si possible.*

> [!WARNING]
> **Graphiques Plotly** : Les graphiques Plotly interactifs sont lourds sur mobile.
> **Stratégie** : Utiliser `kivy.uix.webview` pour afficher les exports HTML de Plotly, ou se replier sur des images statiques (`kaleido`) si la performance est trop faible.

## Alignement avec le Fichier Excel (vmobile)

Ce plan répond point par point aux défis identifiés dans votre analyse Excel :

| Défi Excel | Solution Retenue | Implémentation |
| :--- | :--- | :--- |
| **I. Moteur UI** (Streamlit incompatible) | Migration Kivy/KivyMD | `vmobile/ui/` (Refonte totale de l'interface) |
| **II. Rendu Fractal** (JS incompatible) | Dessin Natif Kivy (Canvas) | `vmobile/ui/components/fractal_widget.py` |
| **V. Graphiques** (Plotly HTML) | Kivy WebView | `kivy.uix.webview` pour afficher les graphiques |
| **VI. Dépendances** (Pandas/Numpy) | Conservation | Supportées par Buildozer (aucun changement de code requis) |
| **VII. Fichiers Système** (Chemins) | Adaptation Dynamique | `v4/config/paths.py` avec détection OS |

## Vue d'Ensemble de l'Architecture

L'application suivra un modèle **Modèle-Vue-Contrôleur (MVC)** :
- **Modèle** : `v4/modules/database` (SQLite) et `v4/modules/services` (Logique Métier) existants. **Réutilisation à 90%**.
- **Vue** : Nouveau `vmobile/ui` utilisant KivyMD (Écrans, Widgets). **Nouveau Code**.
- **Contrôleur** : Classe App Kivy connectant les Vues aux Services. **Nouveau Code**.

## Changements Proposés

### 1. Configuration de la Structure du Projet
#### [NOUVEAU] [vmobile/](file:///c:/Users/djabi/gestion-financière/vmobile/)
- Créer une structure de répertoire propre reflétant `v4` mais pour l'UI mobile.
- `vmobile/main.py` : Point d'entrée de l'application Kivy.
- `vmobile/ui/screens/` : Dossier pour les écrans individuels (Accueil, Transactions, etc.).
- `vmobile/ui/components/` : Widgets Kivy réutilisables (Fractal, Graphiques).

### 2. Adaptation du Cœur (Réutilisation Backend)
#### [MODIFIER] [v4/config/paths.py](file:///c:/Users/djabi/gestion-financière/v4/config/paths.py)
- Mettre à jour la logique `DATA_DIR` pour détecter si l'exécution se fait sur Android/iOS (via `plyer.utils.platform`) et utiliser `app_storage_path` au lieu de `Path.home()`.

### 3. Implémentation UI (KivyMD)
#### [NOUVEAU] [vmobile/ui/screens/home_screen.py](file:///c:/Users/djabi/gestion-financière/vmobile/ui/screens/home_screen.py)
- Implémenter le tableau de bord "Accueil".
- Utiliser `MDCard` pour les métriques sommaires.
- Intégrer **WebView** pour les graphiques Plotly.

#### [NOUVEAU] [vmobile/ui/components/fractal_widget.py](file:///c:/Users/djabi/gestion-financière/vmobile/ui/components/fractal_widget.py)
- **Critique** : Réimplémenter la navigation Triangle Fractal en utilisant `kivy.graphics` (Canvas).
- Traduire la logique de `fractal_service.py` en instructions de dessin (Instructions Vertex, Couleurs).
- Gérer les événements tactiles pour naviguer dans les niveaux hiérarchiques.

### 4. Intégration Matérielle (Caméra & OCR)
#### [NOUVEAU] [vmobile/services/camera_service.py](file:///c:/Users/djabi/gestion-financière/vmobile/services/camera_service.py)
- Utiliser `plyer.camera` ou `kivy-camera` pour capturer des images.
- Sauvegarder les images capturées dans un dossier temporaire pour traitement.

#### [NOUVEAU] [vmobile/services/ocr_service_mobile.py](file:///c:/Users/djabi/gestion-financière/vmobile/services/ocr_service_mobile.py)
- Implémenter la logique OCR spécifique au mobile.
- **Phase 1** : Placeholder simple ou appel API Cloud.
- **Phase 2** : Intégration de l'OCR sur l'appareil (ML Kit).
