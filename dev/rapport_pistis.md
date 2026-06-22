# Rapport de progression PISTIS

Ce fichier doit etre mis a jour a chaque evolution majeure du projet SALMOSPHARM 133.

## Regle de suivi

- Ajouter une entree apres chaque phase importante terminee.
- Indiquer la date, la phase concernee, les fichiers principaux modifies, les validations effectuees et les limites restantes.
- Ne pas y stocker de secret, de mot de passe, de token ou de code de recuperation.

## 2026-06-20 - Phase 5 - Schema SQLAlchemy officiel

### Ce qui a ete fait

- Creation des modeles SQLAlchemy officiels pour les 10 tables validees :
  - utilisateurs
  - categories
  - produits
  - lots_produits
  - mouvements_stock
  - ventes
  - lignes_vente
  - alertes
  - journaux_activite
  - parametres
- Ajout des contraintes principales :
  - roles limites a GERANT et VENDEUR
  - devise limitee a CDF
  - ventes limitees au statut VALIDEE
  - montant recu superieur ou egal au total
  - montants stockes en INTEGER
  - types de mouvements et alertes limites aux valeurs validees
- Ajout des relations SQLAlchemy entre les tables.
- Ajout des index recommandes.
- Ajout du seed initial :
  - parametres par defaut
  - categories de base
- Aucun compte gerant n'est cree automatiquement.
- Aucune table interdite n'a ete creee.

### Fichiers principaux

- `app/database/models.py`
- `app/database/init_db.py`
- `app/database/seed.py`
- `tests/test_database_init.py`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
4 passed
```

### Limites restantes

- Les repositories ne sont pas encore implementes.
- Les services metier ne sont pas encore implementes.
- La creation du compte gerant au premier lancement reste a faire dans une phase suivante.

## 2026-06-21 - Phase 8 - Premier lancement et creation du compte gerant

### Ce qui a ete fait

- Ajout du service de securite local :
  - hash des mots de passe avec bcrypt
  - verification des mots de passe
  - generation du code de recuperation
  - hash et verification du code de recuperation
- Ajout du repository utilisateur minimal pour respecter la separation UI -> Services -> Repositories -> SQLite.
- Ajout du service d'authentification pour le premier lancement :
  - detection de l'existence d'au moins un utilisateur
  - creation du premier compte gerant
  - role force a GERANT
  - compte actif par defaut
  - refus du compte admin/admin
  - refus de double creation du premier gerant
- Ajout du service de recuperation pour generer un code et son hash.
- Ajout de l'ecran PySide6 de creation du compte gerant dans `app/ui/first_run/`.
- Branchement du demarrage dans `app/main.py` :
  - si aucun utilisateur n'existe, afficher l'ecran de creation du gerant
  - sinon, afficher la fenetre minimale actuelle en attendant l'ecran de connexion
- Le code de recuperation est affiche une seule fois apres creation.
- Le mot de passe et le code de recuperation ne sont jamais stockes en clair.

### Fichiers principaux

- `app/core/security.py`
- `app/core/exceptions.py`
- `app/repositories/utilisateur_repository.py`
- `app/services/auth_service.py`
- `app/services/recuperation_service.py`
- `app/ui/first_run/manager_account_window.py`
- `app/main.py`
- `tests/test_auth_service.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest
$env:QT_QPA_PLATFORM='offscreen'; $env:LOCALAPPDATA=(New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP 'salmospharm-first-run-check')).FullName; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from app.core.paths import ensure_app_directories; from app.database.init_db import init_database; from app.services.auth_service import AuthService; from app.ui.first_run.manager_account_window import FirstRunWindow; import sys; ensure_app_directories(); init_database(); app=QApplication([]); service=AuthService(); assert service.existe_utilisateur() is False; window=FirstRunWindow(auth_service=service); assert window.windowTitle() == 'SALMOSPHARM 133'; print('first_run_window_ok')"
```

Resultats :

```txt
7 passed
first_run_window_ok
```

### Limites restantes

- L'ecran de connexion complet n'est pas encore implemente.
- La journalisation metier est preparee conceptuellement mais pas encore branchee dans un service `journal_service.py`.
- La maquette fournie contient un champ telephone et un email optionnel, mais le schema officiel `utilisateurs` ne contient pas ces colonnes. L'ecran garde donc ces elements comme indications visuelles non persistantes, sans modifier la base.
- Le venv actuel contient `passlib 1.7.4` et `bcrypt 5.0.0`, combinaison qui echoue pendant l'auto-detection du backend passlib. Le projet utilise donc bcrypt directement dans `app/core/security.py` tout en conservant le principe de hash bcrypt.

### Correctif UI du premier lancement

- Correction du chevauchement des champs dans l'ecran de creation du compte gerant.
- Ajout d'une hauteur minimale stable pour la carte du formulaire.
- Augmentation de la hauteur du bloc de code de recuperation.
- Ajout d'un conteneur fixe pour les options du formulaire.
- Verification que la zone devient defilable en petite hauteur au lieu de compresser les champs.

### Refonte UI selon la maquette simplifiee

- Retrait des champs visuels `Telephone` et `Email (optionnel)` de l'ecran de creation du compte gerant.
- Retrait du bloc visible `Code de recuperation` avant creation du compte.
- Conservation du code de recuperation dans le flux metier : il est toujours genere et affiche une seule fois apres creation.
- Reduction de la hauteur minimale de la carte pour que tous les elements tiennent dans une fenetre normale.
- Assouplissement de la taille minimale de la fenetre pour activer le scroll uniquement quand la hauteur disponible est reduite.
- Verification : pas de scroll a 1440x900, scroll actif quand la fenetre est reduite.

### Correctif visuel des bandes noires

- Correction du fond du `QScrollArea` et de son viewport pour supprimer les bandes noires autour de la carte.
- Alignement du fond du contenu defilable sur le fond principal `#fbfdff`.
- Masquage du scroll horizontal parasite.
- Verification : pas de scroll vertical en taille normale, scroll vertical actif seulement en hauteur reduite.

## 2026-06-22 - Phase 6 - Repositories de base

### Ce qui a ete fait

- Mise en place des repositories de base pour les tables officielles :
  - utilisateurs
  - categories
  - produits
  - lots_produits
  - mouvements_stock
  - ventes
  - lignes_vente via `VenteRepository`
  - alertes
  - journaux_activite
  - parametres
- Renforcement du repository utilisateur deja existant avec les lectures par id, role et statut actif.
- Ajout de requetes utiles aux prochains services :
  - recherche produit par nom ou code-barres
  - liste des produits actifs
  - liste des lots disponibles pour aider FEFO
  - calcul simple du stock disponible vendable
  - creation de ventes et lignes de vente
  - recuperation des ventes par vendeur
  - creation et lecture des alertes non lues
  - creation et lecture des journaux d'activite
  - lecture de l'enregistrement principal des parametres
- Conservation de la separation des responsabilites :
  - les repositories font l'acces base
  - les decisions metier restent reservees aux services
  - aucune logique de permission complete ni validation de vente complete n'a ete ajoutee dans les repositories

### Fichiers principaux

- `app/repositories/utilisateur_repository.py`
- `app/repositories/__init__.py`
- `app/repositories/categorie_repository.py`
- `app/repositories/produit_repository.py`
- `app/repositories/lot_produit_repository.py`
- `app/repositories/stock_repository.py`
- `app/repositories/vente_repository.py`
- `app/repositories/alerte_repository.py`
- `app/repositories/journal_repository.py`
- `app/repositories/parametre_repository.py`
- `tests/test_repositories.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
8 passed
```

### Limites restantes

- Les repositories ne remplacent pas les services metier : permissions, validation de vente, transactions critiques et FEFO complet seront implementes dans les phases suivantes.
- Le service de journalisation n'est pas encore branche aux actions sensibles existantes.
- Les repositories de rapport/export ne sont pas crees, car les rapports ne doivent pas devenir des tables et seront traites plus tard par requetes ou vues.

## 2026-06-22 - Phase 7 - Constantes, exceptions et permissions

### Ce qui a ete fait

- Creation du fichier `app/core/constants.py` pour centraliser les constantes officielles :
  - roles `GERANT` et `VENDEUR`
  - devise unique `CDF`
  - paiement unique `ESPECES`
  - statut de vente `VALIDEE`
  - types de mouvements de stock
  - types d'alertes
  - largeurs de ticket 58 et 80
  - actions de journalisation obligatoires
- Completion du fichier `app/core/exceptions.py` avec les exceptions applicatives principales :
  - `PermissionRefuseeError`
  - `StockInsuffisantError`
  - `ProduitExpireError`
  - `ProduitInactifError`
  - `UtilisateurInactifError`
  - `BackupInvalideError`
  - `ImprimanteIndisponibleError`
  - `AuthentificationError`
- Creation du fichier `app/core/permissions.py` pour centraliser les permissions par role.
- Definition des permissions vendeur limitees aux actions autorisees :
  - connexion
  - dashboard
  - recherche produit
  - consultation stock
  - creation vente
  - impression/reimpression de ses tickets
  - historique personnel
- Definition des permissions gerant avec acces complet.
- Ajout de fonctions de verification utilisables par les services :
  - `role_valide`
  - `permissions_pour_role`
  - `a_permission`
  - `exiger_permission`
  - `exiger_role_valide`
- Remplacement de la constante locale `ROLE_GERANT` dans `auth_service.py` par la constante officielle.

### Fichiers principaux

- `app/core/constants.py`
- `app/core/exceptions.py`
- `app/core/permissions.py`
- `app/services/auth_service.py`
- `tests/test_permissions.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
12 passed
```

### Limites restantes

- Les services metier des phases suivantes doivent appeler `exiger_permission` pour bloquer les actions sensibles cote service.
- Les permissions ne sont pas encore branchees a une session utilisateur complete, car l'ecran de connexion et la session memoire arrivent en phase 9.
- Les actions de journalisation sont centralisees, mais le service `journal_service.py` reste a creer et brancher.
