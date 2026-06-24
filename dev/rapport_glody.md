# Rapport de progression GLODY

Ce fichier suit le travail du developpeur DEV2 charge de l'interface PySide6 de SALMOSPHARM 133.

## Regle de suivi

- Lire les rapports disponibles dans `dev/` avant chaque implementation :
  - `rapport_pistis.md` pour le developpeur principal.
  - `rapport_junior.md` pour le troisieme developpeur, s'il existe.
  - `rapport_glody.md` pour l'historique DEV2.
- Ajouter une entree apres chaque evolution UI importante.
- Indiquer la date, la phase concernee, les fichiers modifies, les validations effectuees et les limites restantes.
- Ne jamais stocker de secret, mot de passe, token ou code de recuperation dans ce fichier.
- Respecter strictement le perimetre DEV2 : interface PySide6, layouts, composants, messages utilisateur et integration propre avec les services.

## 2026-06-24 - Initialisation du rapport DEV2

### Contexte lu

- `AGENTS.md`
- `CODEX_PHASES.md`
- `dev2.md`
- `docs/01_CONTEXTE_ET_OBJECTIFS.md`
- `docs/02_ARCHITECTURE_ET_STACK.md`
- `docs/03_REGLES_METIER_ET_SECURITE.md`
- `docs/05_MODULES_UI_LIVRAISON.md`
- `dev/rapport_pistis.md`

### Etat UI constate

- L'ecran de premier lancement existe dans `app/ui/first_run/manager_account_window.py`.
- `app/main.py` affiche actuellement l'ecran de creation du gerant si aucun utilisateur n'existe.
- Si un utilisateur existe deja, `app/main.py` affiche encore une fenetre principale minimale.
- Le dossier `app/ui/login/` ne contient pas encore d'ecran de connexion.
- Les dossiers `app/ui/layouts/`, `app/ui/components/`, `app/ui/gerant/` et `app/ui/vendeur/` sont encore vides hors `__init__.py`.
- `AuthService` ne contient pas encore de methode de connexion utilisateur.

### Phase cible

- Phase 9 - Connexion et session utilisateur, cote interface PySide6.

### Plan DEV2 retenu

- Creer l'ecran de connexion dans `app/ui/login/login_window.py`.
- Prevoir les champs identifiant et mot de passe.
- Ajouter l'affichage/masquage du mot de passe.
- Ajouter le bouton `Connexion`.
- Ajouter un lien ou bouton `Mot de passe oublie` sans implementer la recuperation complete tant que le service n'est pas pret.
- Brancher l'ecran au service seulement si une methode de connexion existe.
- Si la methode de connexion n'existe pas, ne pas coder la logique metier dans l'UI et documenter le contrat attendu.
- Modifier `app/main.py` pour afficher l'ecran de connexion apres le premier lancement et quand un utilisateur existe.

### Limites actuelles

- La logique metier de connexion doit etre implementee cote service par le developpeur responsable de l'authentification.
- DEV2 ne doit pas creer de session SQLAlchemy dans l'UI.
- DEV2 ne doit pas modifier directement SQLite.
- La Phase 10 sera abordee seulement apres validation de la connexion.

