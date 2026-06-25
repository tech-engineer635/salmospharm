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

## 2026-06-24 - Phase 9 UI - Ecran de connexion

### Ce qui a ete fait

- Creation de l'ecran de connexion dans `app/ui/login/login_window.py`.
- Reproduction de la maquette fournie :
  - panneau marque a gauche avec logo, nom SALMOSPHARM, badge 133, slogan et benefices;
  - carte de connexion a droite;
  - champs nom d'utilisateur et mot de passe;
  - affichage/masquage du mot de passe;
  - case `Se souvenir de moi`;
  - lien `Mot de passe oublie ?`;
  - bouton principal `Se connecter`;
  - message d'acces reserve;
  - footer bleu avec copyright et version.
- Branchement de l'ecran dans `app/main.py` :
  - si un utilisateur existe, l'application affiche maintenant `LoginWindow`;
  - apres creation du premier gerant, l'application affiche `LoginWindow`.
- Export de `LoginWindow` dans `app/ui/login/__init__.py`.
- Ajout d'un test UI minimal dans `tests/test_login_window.py`.

### Respect du perimetre DEV2

- Aucune session SQLAlchemy n'a ete creee dans l'UI.
- Aucune table n'a ete creee ou modifiee.
- Aucune logique metier de connexion n'a ete inventee dans l'UI.
- Si `AuthService.connecter` n'existe pas, l'ecran affiche un message propre indiquant que le service doit encore etre branche.
- Les erreurs applicatives prevues sont capturees proprement si le service existe plus tard.

### Fichiers principaux

- `app/ui/login/login_window.py`
- `app/ui/login/__init__.py`
- `app/main.py`
- `tests/test_login_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pytest tests\test_login_window.py
.\.venv\Scripts\python.exe -m pip show bcrypt passlib
```

Resultats :

```txt
pytest global : 5 failed, 12 passed
pytest login UI : 1 passed
passlib : 1.7.4
bcrypt : 5.0.0
```

### Limites restantes

- La suite globale echoue encore a cause du conflit d'environnement deja signale par DEV3 : `passlib 1.7.4` avec `bcrypt 5.0.0`.
- `requirements.txt` demande `bcrypt==4.0.1`, mais le venv courant contient `bcrypt 5.0.0`.
- La vraie connexion reste a implementer cote service via un contrat du type `AuthService.connecter(identifiant, mot_de_passe)`.
- La redirection vers les layouts Phase 10 attend la validation de la connexion metier.

## 2026-06-24 - Phase 9 UI - Lien premier lancement vers connexion

### Ce qui a ete fait

- Ajout d'un signal `connexion_demandee` dans `FirstRunWindow`.
- Branchement du lien `J'ai deja un compte` pour emettre ce signal.
- Branchement dans `app/main.py` :
  - clic sur `J'ai deja un compte` depuis l'ecran de creation du gerant;
  - fermeture de l'ecran premier lancement;
  - ouverture directe de `LoginWindow`.
- Ajout d'un test UI minimal pour verifier le signal de demande de connexion.

### Fichiers principaux

- `app/ui/first_run/manager_account_window.py`
- `app/main.py`
- `tests/test_first_run_window.py`
- `dev/rapport_glody.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_first_run_window.py tests\test_login_window.py
```

Resultat :

```txt
2 passed
```

### Limites restantes

- Si aucun compte n'existe encore, l'ecran de connexion peut s'ouvrir via le lien, mais aucune connexion reelle ne pourra aboutir tant que le service `AuthService.connecter` n'est pas implemente et qu'un utilisateur n'existe pas en base.
