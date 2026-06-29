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

## 2026-06-22 - Correction transversale - Journalisation du premier lancement

### Ce qui a ete fait

- Creation du service `app/services/journal_service.py`.
- Ajout d'une methode `journaliser` qui ecrit dans `journaux_activite` via `JournalRepository`.
- Validation des actions de journalisation contre `ACTIONS_JOURNAL`.
- Branchement de la journalisation dans `AuthService.creer_premier_gerant`.
- Journalisation des actions sensibles du premier lancement :
  - `COMPTE_GERANT_CREE`
  - `CODE_RECUPERATION_GENERE`
- Les journaux sont crees dans la meme transaction que le compte gerant.
- Le code de recuperation en clair n'est jamais stocke dans les details du journal.

### Fichiers principaux

- `app/services/journal_service.py`
- `app/services/auth_service.py`
- `tests/test_auth_service.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
13 passed
```

### Limites restantes

- La connexion n'est pas encore journalisee, car la phase 9 n'est pas encore implementee.
- Les autres actions sensibles seront branchees au fur et a mesure des services metier : produits, stock, vente, impression, backup et parametres.

## 2026-06-22 - Correction securite - Passlib bcrypt officiel

### Ce qui a ete fait

- Remplacement de l'utilisation directe du paquet `bcrypt` par `passlib.context.CryptContext`.
- Alignement du code avec la stack officielle `passlib[bcrypt]`.
- Pinning des dependances de securite dans `requirements.txt` :
  - `passlib[bcrypt]==1.7.4`
  - `bcrypt==4.0.1`
- Correction du conflit local entre `passlib 1.7.4` et `bcrypt 5.0.0`.
- Activation de `bcrypt__truncate_error=True` pour refuser la troncature silencieuse des secrets trop longs.
- Conservation du comportement attendu :
  - mot de passe hashe
  - code de recuperation hashe
  - verification des secrets via passlib
  - aucun secret en clair stocke
- Ajout d'un test pour refuser un secret trop long.

### Fichiers principaux

- `app/core/security.py`
- `requirements.txt`
- `tests/test_auth_service.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pip install bcrypt==4.0.1
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
14 passed
passlib 1.7.4
bcrypt 4.0.1
```

### Limites restantes

- Les dependances devront etre reinstallees depuis `requirements.txt` sur tout nouvel environnement pour eviter de revenir a `bcrypt 5.0.0`.

## 2026-06-24 - Ajustement securite - Regle de mot de passe gerant

### Ce qui a ete fait

- Ajustement de la validation du mot de passe du premier gerant.
- Le minimum est maintenant de 5 caracteres.
- Suppression de l'obligation de melanger lettres et chiffres.
- L'interdiction du compte `admin/admin` reste active.
- Le hash passlib/bcrypt reste obligatoire.

### Fichiers principaux

- `app/services/auth_service.py`
- `tests/test_auth_service.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
16 passed
```

## 2026-06-25 - Phase 9 - Connexion utilisateur cote service

### Ce qui a ete fait

- Ajout de la connexion metier dans `AuthService.connecter`.
- Conservation du contrat attendu par l'ecran DEV2 :
  - `connecter(identifiant=..., mot_de_passe=...)`
- Normalisation de l'identifiant en minuscules.
- Verification du mot de passe avec passlib/bcrypt.
- Refus d'un identifiant inconnu avec message generique.
- Refus d'un mot de passe incorrect avec message generique.
- Refus d'un compte desactive avec message utilisateur propre.
- Ajout d'une session memoire `SessionUtilisateur` sans hash de mot de passe ni hash de code de recuperation.
- Journalisation des connexions reussies avec `CONNEXION_REUSSIE`.
- Journalisation des connexions echouees avec `CONNEXION_ECHOUEE`.
- Aucun mot de passe saisi n'est stocke dans les journaux.

### Fichiers principaux

- `app/services/auth_service.py`
- `tests/test_auth_service.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
22 passed
```

### Limites restantes

- La redirection apres connexion vers les layouts GERANT/VENDEUR attend la Phase 10.
- La recuperation complete de mot de passe reste a implementer dans une phase suivante.

## 2026-06-25 - Phase 10 - Preparation session et jonction apres connexion

### Ce qui a ete fait

- Validation explicite du role utilisateur dans `AuthService.connecter` avant creation de la session memoire.
- Passage de la `SessionUtilisateur` a la fenetre principale transitoire apres connexion.
- Conservation de la session connectee dans `MainWindow.session_utilisateur`.
- Affichage du nom et du role de l'utilisateur connecte dans la fenetre principale minimale.
- Ajout d'un test de jonction pour verifier que la fenetre principale recoit et affiche la session.
- Ajout d'un test garantissant que `SessionUtilisateur` ne contient aucun hash ni donnee sensible.
- Ajout d'un test garantissant qu'un role non officiel est refuse avant creation de la session memoire.

### Fichiers principaux

- `app/services/auth_service.py`
- `app/main.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation

Commande executee :

```powershell
.\.venv\Scripts\python.exe -m pytest
```

Resultat :

```txt
25 passed
```

### Limites restantes

- Le layout complet, la sidebar, la topbar et les pages placeholder restent du ressort DEV2 pour la suite de la Phase 10.
- La deconnexion graphique sera finalisee avec le layout principal.

## 2026-06-26 - Phase 11 - Produits et categories

### Ce qui a ete fait

- Creation du service metier `ProduitService` pour la gestion du catalogue :
  - creation de categories ;
  - creation de produits ;
  - modification de produits ;
  - desactivation de produits au lieu d'une suppression physique ;
  - recherche par nom ou code-barres ;
  - filtre par categorie et statut actif.
- Ajout d'un payload `ProduitPayload` pour centraliser les donnees de fiche produit.
- Application des validations Phase 11 cote service :
  - gerant obligatoire pour creer, modifier et desactiver ;
  - recherche produit limitee aux roles autorises ;
  - prix en entier CDF ;
  - prix negatif refuse ;
  - stock minimum negatif refuse ;
  - code-barres unique ;
  - categorie invalide refusee.
- Journalisation des actions sensibles :
  - `PRODUIT_CREE` ;
  - `PRODUIT_MODIFIE` ;
  - `PRODUIT_DESACTIVE`.
- Extension de `ProduitRepository` avec une recherche combinee et une mise a jour explicite.
- Remplacement du placeholder gerant `Produits` par une page PySide6 fonctionnelle :
  - formulaire categorie ;
  - formulaire produit ;
  - filtres catalogue ;
  - tableau produits ;
  - modification et desactivation via le service.
- Reprise visuelle de la maquette `gerant_gestion_produit.png` :
  - titre et recherche en haut de page ;
  - cartes de synthese ;
  - barre d'actions catalogue ;
  - tableau dense ;
  - colonne droite avec filtres rapides et formulaire produit.
- Ajout d'un `PRODUCT.md` minimal pour documenter le registre produit de l'interface.

### Fichiers principaux

- `PRODUCT.md`
- `app/services/produit_service.py`
- `app/repositories/produit_repository.py`
- `app/ui/gerant/produits/produits_page.py`
- `app/ui/gerant/produits/__init__.py`
- `app/ui/layouts/main_layout.py`
- `tests/test_produit_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest
$env:QT_QPA_PLATFORM='offscreen'; $env:LOCALAPPDATA=(New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP 'salmospharm-products-design-smoke')).FullName; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from app.core.paths import ensure_app_directories; from app.database.init_db import init_database; from app.services.auth_service import SessionUtilisateur; from app.ui.gerant.produits import ProduitsPage; ensure_app_directories(); init_database(); app=QApplication([]); page=ProduitsPage(SessionUtilisateur(1,'Gerant','gerant','GERANT')); assert page.products_table.columnCount()==7; assert page.total_metric.value_label.text() == '0'; print('products_design_ok')"
```

Resultats :

```txt
45 passed
products_design_ok
```

### Limites restantes

- La Phase 11 ne gere pas encore les lots, les entrees de stock, FEFO ou les ventes.
- Le stock affiche dans la fiche produit reste limite au seuil minimum ; le stock disponible sera calcule depuis `lots_produits` en Phase 12.
- La page produits affiche et modifie les champs principaux, mais les workflows d'export catalogue et de consultation avancee restent a traiter plus tard.

### Correctif accessibilite - Reactivation produit

- Ajout d'une action explicite `Reactiver ce produit` quand un produit desactive est selectionne.
- Ajout d'un texte d'aide visible dans le formulaire pour expliquer l'etat actif/desactive.
- Ajout de `ProduitService.reactiver_produit()` pour garder la reactivation cote service.
- Journalisation de la reactivation via `PRODUIT_MODIFIE`.
- Ajout de tests service et UI pour eviter qu'un produit desactive reste difficile a reactiver.

Validation :

```powershell
.\.venv\Scripts\python.exe -m pytest
$env:QT_QPA_PLATFORM='offscreen'; $env:LOCALAPPDATA=(New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP 'salmospharm-access-reactivate-smoke')).FullName; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from app.core.paths import ensure_app_directories; from app.database.init_db import init_database; from app.services.auth_service import SessionUtilisateur; from app.ui.gerant.produits import ProduitsPage; ensure_app_directories(); init_database(); app=QApplication([]); page=ProduitsPage(SessionUtilisateur(1,'Gerant','gerant','GERANT')); assert page.disable_button.text() == 'Desactiver'; print('access_reactivation_ui_ok')"
```

Resultats :

```txt
48 passed
access_reactivation_ui_ok
```

### Correctif UI - Spacing plein ecran produits

- Resserrement du spacing vertical de l'ecran produits pour se rapprocher de la maquette fournie.
- Reduction des marges propres a la page produits dans le layout principal.
- Compression des cartes de synthese et des champs du panneau lateral.
- Retrait du champ visible `Description` dans le formulaire principal pour eviter un formulaire trop haut ; le champ reste gere en interne par le service.
- Masquage des controles de statut tant qu'aucun produit n'est selectionne.
- Ajout d'un test anti-regression : en 1450x900, la page produits ne doit pas activer le scroll vertical et le bouton `Enregistrer` doit rester visible.

Validation :

```powershell
.\.venv\Scripts\python.exe -m pytest
$env:QT_QPA_PLATFORM='offscreen'; $env:LOCALAPPDATA=(New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP 'salmospharm-products-fit-check')).FullName; .\.venv\Scripts\python.exe -c "from PySide6.QtWidgets import QApplication; from app.core.paths import ensure_app_directories; from app.database.init_db import init_database; from app.services.auth_service import SessionUtilisateur; from app.ui.layouts.main_layout import MainWindow; ensure_app_directories(); init_database(); app=QApplication([]); w=MainWindow(SessionUtilisateur(1,'Gerant','gerant','GERANT')); w.resize(1450,900); w.show(); w.navigate('produits'); app.processEvents(); scroll=w.content_stack.currentWidget(); p=w._page_widgets['produits']; button_bottom=p.save_button.mapTo(scroll.viewport(), p.save_button.rect().bottomRight()).y(); assert scroll.verticalScrollBar().maximum()==0; assert button_bottom <= scroll.viewport().height(); print('products_fullscreen_no_scroll_ok')"
```

Resultats :

```txt
49 passed
products_fullscreen_no_scroll_ok
```

## Phase 12 - Lots et stock

### Perimetre implemente

- Ajout du service `StockService` pour les entrees de stock, les ajustements et la consultation des lots/mouvements.
- Ajout du service `AlerteService` pour creer les alertes `STOCK_FAIBLE` et `EXPIRATION_PROCHE` sans doublons ouverts.
- Extension des repositories lots et mouvements stock, en conservant l'acces base hors UI.
- Ajout de l'ecran gerant `StockPage` : cartes de synthese, table des lots, historique recent, formulaire d'entree et formulaire d'ajustement.
- Integration de la page stock dans le layout principal du gerant.
- Ajout des tests metier et UI : entree, mise a jour lot, ajustement motive, refus quantite negative, refus vendeur, mouvements, journaux, alertes et absence de scroll plein ecran.

### Fichiers principaux

- `app/services/stock_service.py`
- `app/services/alerte_service.py`
- `app/repositories/lot_produit_repository.py`
- `app/repositories/stock_repository.py`
- `app/ui/gerant/stock/stock_page.py`
- `app/ui/gerant/stock/__init__.py`
- `app/ui/layouts/main_layout.py`
- `app/ui/components/icons.py`
- `tests/test_stock_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest
$env:QT_QPA_PLATFORM='offscreen'; $unique = 'salmospharm-phase12-stock-smoke-' + [guid]::NewGuid().ToString('N'); $env:LOCALAPPDATA=(New-Item -ItemType Directory -Force -Path (Join-Path $env:TEMP $unique)).FullName; .\.venv\Scripts\python.exe -
```

Resultats :

```txt
56 passed
stock_page_ok
```

### Limites restantes

- La sortie de stock par vente FEFO reste reservee a la phase vente.
- L'import/export global de sauvegarde n'est pas modifie ici.
- Les alertes sont creees au moment des entrees et ajustements ; un traitement global de recalcul pourra etre ajoute plus tard si la feuille de route le demande.

### Correctif UI - Espacement du panneau stock

- Augmentation controlee de la largeur du panneau lateral stock pour eviter les champs trop serres.
- Separation claire de la ligne `Quantite / Prix achat` et du controle d'expiration.
- Placement de `Date d'expiration connue` et du champ date sur une meme ligne lisible, sans chevauchement.
- Ajustement des hauteurs des panneaux pour conserver l'absence de scroll en plein ecran.
- Ajout d'assertions UI pour verifier que les controles ne se chevauchent pas et que le bouton d'enregistrement reste visible.
- Reprise finale du formulaire avec des groupes `label + champ` non compressibles.
- Passage du panneau de droite dans un scroll interne : si la hauteur manque, la colonne formulaire defile sans ecraser les champs ni faire scroller toute la page.
- Ajout de `dev/stock_spacing_*.png` dans `.gitignore` pour ignorer les captures de diagnostic UI.

Validation :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_main_window.py::test_page_stock_ne_scrolle_pas_en_plein_ecran
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
1 passed
56 passed
```

## Phase 13 - FEFO

### Perimetre implemente

- Ajout de `StockService.choisir_lots_fefo()` pour selectionner les lots vendables sans decrementer le stock.
- Ajout du resultat `LotFefoSelection`, detache de SQLAlchemy, pour preparer la future validation de vente.
- Exclusion des lots expires, des lots a quantite 0 et des produits inactifs.
- Tri FEFO par date d'expiration croissante, avec les lots sans date places apres les lots dates.
- Repartition automatique de la quantite demandee sur plusieurs lots si necessaire.
- Refus propre avec `StockInsuffisantError` quand le stock vendable ne couvre pas la demande.
- Validation de la quantite demandee avant toute selection.

### Fichiers principaux

- `app/services/stock_service.py`
- `tests/test_stock_service.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_stock_service.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
10 passed
61 passed
```

### Limites restantes

- La methode FEFO ne decremente pas encore les lots ; la sortie effective sera faite dans la phase vente.
- Les mouvements `SORTIE`, les lignes de vente et la transaction complete restent reserves a la Phase 14.

## Phases 14 et 15 - Vente definitive et interface nouvelle vente

### Perimetre implemente

- Ajout de `VenteService.valider_vente()` pour valider une vente definitive en especes et en CDF.
- Validation cote service : permission de vente, panier non vide, quantites positives, produits actifs, prix coherents, stock vendable suffisant et montant recu suffisant.
- Application FEFO dans la transaction de vente, avec exclusion des lots expires ou vides.
- Creation atomique de `ventes`, `lignes_vente`, mouvements `SORTIE`, alertes de stock/expiration si necessaire et journal `VENTE_VALIDEE`.
- Ajout de `VenteService.lister_produits_vendables()` pour alimenter l'interface sans exposer les lots a l'UI.
- Remplacement du placeholder vendeur `Nouvelle vente` par une page PySide6 connectee aux services : recherche, filtres categories, cartes produits, panier, total, montant recu, monnaie et encaissement.
- Conservation visible mais desactivee de la remise du mockup, car aucune regle metier de remise n'est validee pour la version 1.0.
- Bouton d'impression laisse visible mais desactive tant que la phase ticket/impression n'est pas branchee.
- Ajout d'un test UI pour garantir qu'en plein ecran l'encaissement reste accessible sans scroll global.

### Fichiers principaux

- `app/services/vente_service.py`
- `app/ui/vendeur/nouvelle_vente/nouvelle_vente_page.py`
- `app/ui/layouts/main_layout.py`
- `tests/test_vente_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_vente_service.py
.\.venv\Scripts\python.exe -m pytest tests/test_vente_service.py tests/test_main_window.py
.\.venv\Scripts\python.exe -m pytest tests/test_main_window.py::test_page_nouvelle_vente_ne_scrolle_pas_en_plein_ecran
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
7 passed
26 passed
1 passed
71 passed
```

### Limites restantes

- L'impression ticket/facture n'est pas encore activee ; elle depend de la phase ticket/impression.
- La remise n'est pas appliquee, car elle n'existe pas dans les regles metier validees.
- L'historique des ventes et la reimpression restent a brancher dans les phases suivantes.

## Gestion des vendeurs - Ecran gerant

### Perimetre implemente

- Ajout de `UtilisateurService` pour gerer les comptes vendeurs sans acces direct de l'UI a SQLAlchemy.
- Creation vendeur reservee au gerant, avec mot de passe hashé, code de recuperation hashé et journalisation.
- Liste des vendeurs avec recherche, statut actif/inactif, derniere connexion connue et ventes du jour.
- Desactivation et reactivation de vendeur via le service, avec journalisation.
- Remplacement du placeholder `Vendeurs` par une page PySide6 dans `app/ui/gerant/vendeurs/`.
- Reprise du design fourni : en-tete, cartes metriques, tableau, panneau d'ajout a droite et actions visibles.
- Suppression du champ `Role` du formulaire, car cette interface cree uniquement des vendeurs.
- Omission du champ telephone persistant : la table officielle `utilisateurs` ne contient pas de colonne telephone.
- Ajout d'un test UI garantissant que le bouton de creation reste accessible sans scroll global en plein ecran.

### Fichiers principaux

- `app/services/utilisateur_service.py`
- `app/repositories/utilisateur_repository.py`
- `app/ui/gerant/vendeurs/vendeurs_page.py`
- `app/ui/layouts/main_layout.py`
- `tests/test_utilisateur_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_utilisateur_service.py
.\.venv\Scripts\python.exe -m pytest tests/test_utilisateur_service.py tests/test_main_window.py
.\.venv\Scripts\python.exe -m pytest tests/test_main_window.py::test_page_vendeurs_formulaire_sans_champ_role_et_accessible_plein_ecran
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
4 passed
25 passed puis correction spacing
1 passed
77 passed
```

### Limites restantes

- Aucun envoi d'email n'est implemente : l'application doit fonctionner sans Internet obligatoire.
- Le telephone vendeur necessiterait une evolution validee du schema officiel avant persistance.

## Correctif UX - Encaissement nouvelle vente

### Perimetre corrige

- Le bouton `Encaisser` n'est plus percu comme inactif apres ajout au panier.
- Le champ `Montant recu` est pre-rempli avec le total du panier pour permettre un encaissement exact rapide.
- Ajout d'un message d'aide sous le montant recu :
  - panier vide ;
  - montant recu inferieur au total ;
  - pret a encaisser.
- Le bouton reste accessible des qu'un panier existe ; si le montant est insuffisant, l'interface affiche un message clair au lieu de rester silencieuse.
- Message de produit vendable vide clarifie : il faut un produit actif avec un lot non expire et du stock.
- Le test de non-scroll plein ecran de `Nouvelle vente` reste valide apres ajout du message d'aide.

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_main_window.py::test_page_nouvelle_vente_panier_total_et_accessibilite_encaissement tests/test_main_window.py::test_page_nouvelle_vente_ne_scrolle_pas_en_plein_ecran
.\.venv\Scripts\python.exe -m pytest tests/test_main_window.py::test_page_nouvelle_vente_ne_scrolle_pas_en_plein_ecran
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
1 passed, puis correction spacing
1 passed
77 passed
```

## Stabilisation phases 10 a 15

### Perimetre corrige

- Alignement du menu vendeur avec la documentation : l'entree `Produits` devient `Recherche produit` pour le vendeur, sans changer la navigation `Produits` du gerant.
- Le titre de page vendeur suit le meme libelle `Recherche produit`.
- Renforcement de `VenteService.valider_vente()` : le service confirme en base que l'utilisateur connecte est encore actif avant de creer la vente, les lignes, les mouvements de stock ou le journal.
- Ajout d'un test de vente pour refuser un vendeur desactive et verifier que la tentative reste atomique.
- Decision de stabilisation initiale : l'apercu et l'impression du ticket etaient reportes a la Phase 16. La section Phase 16 ci-dessous leve ce report.

### Validation executee

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_vente_service.py tests/test_main_window.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\pyinstaller.exe app/main.py --name SALMOSPHARM --windowed --onedir --icon app/assets/logo.ico --add-data "app/assets;assets" --noconfirm
```

Resultats :

```txt
30 passed
78 passed
Build PyInstaller reussi, executable genere : dist\SALMOSPHARM\SALMOSPHARM.exe
```

### Test manuel recommande

1. Lancer `python app/main.py`.
2. Se connecter avec un vendeur actif.
3. Verifier que le menu affiche `Recherche produit`.
4. Aller dans `Nouvelle vente`, ajouter un produit actif avec lot non expire et stock disponible.
5. Cliquer sur `Encaisser`.
6. Verifier que la vente est validee, que le stock diminue et que le ticket s'affiche apres encaissement.

## Phase 16 - Tickets et impression thermique

### Perimetre implemente

- Ajout de `TicketService` pour generer un ticket depuis une vente validee, sans creer de table `factures`.
- Les donnees du recu viennent de `ventes`, `lignes_vente`, `produits`, `utilisateurs` et `parametres`.
- Respect des permissions de consultation : le gerant peut generer un ticket de toute vente, le vendeur uniquement de ses ventes.
- Ajout de l'export PDF local via ReportLab.
- Ajout de `ImpressionService` pour formater un ticket thermique 58 mm ou 80 mm et envoyer le flux texte a une imprimante Windows configuree.
- Gestion propre des erreurs d'impression : absence d'imprimante ou echec pilote retourne un message utilisateur et journalise `ERREUR_IMPRESSION` sans annuler la vente.
- Branchement de `Nouvelle vente` : apres encaissement, le ticket est genere, l'impression automatique est tentee si activee, puis l'ecran `Facture / Recu` est affiche.
- Remplacement du placeholder `Factures` par une page d'apercu avec actions `Imprimer`, `Telecharger (PDF)` et `Fermer`.

### Fichiers principaux

- `app/services/ticket_service.py`
- `app/services/impression_service.py`
- `app/repositories/vente_repository.py`
- `app/ui/components/ticket_preview.py`
- `app/ui/vendeur/nouvelle_vente/nouvelle_vente_page.py`
- `app/ui/layouts/main_layout.py`
- `tests/test_ticket_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation executee

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ticket_service.py tests/test_main_window.py tests/test_vente_service.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\pyinstaller.exe app/main.py --name SALMOSPHARM --windowed --onedir --icon app/assets/logo.ico --add-data "app/assets;assets" --noconfirm
```

Resultats :

```txt
35 passed
83 passed
Build PyInstaller reussi, executable genere : dist\SALMOSPHARM\SALMOSPHARM.exe
```

### Limites restantes

- L'impression reelle 58 mm / 80 mm doit etre testee avec une imprimante thermique Windows configuree dans les parametres.
- La reimpression depuis un historique de ventes sera finalisee avec la Phase 17, quand les ecrans d'historique existeront.
- L'impression ESC/POS avancee reste limitee au flux texte brut Windows pour garder l'application locale et testable sans imprimante pendant le developpement.

## Phase 17 - Historique des ventes, rapports et alertes

### Perimetre implemente

- Ajout de `RapportService` pour calculer les historiques et rapports depuis les tables existantes, sans table `rapports`.
- Historique gerant : consultation de toutes les ventes validees, recherche par numero ou vendeur, ouverture du ticket associe.
- Historique vendeur : consultation limitee a ses propres ventes par verification service.
- Rapports gerant : ventes du jour, ventes du mois, panier moyen, rapport par vendeur et produits les plus vendus.
- Alertes gerant : liste des alertes stock/expiration et marquage comme lue.
- Remplacement des placeholders `Rapports`, `Alertes`, `Historique`, `Ventes` et `Historique des ventes` par des pages connectees.
- Les tickets restent generes depuis les ventes via `TicketService`, jamais depuis une table `factures`.

### Fichiers principaux

- `app/services/rapport_service.py`
- `app/services/alerte_service.py`
- `app/repositories/alerte_repository.py`
- `app/ui/gerant/historique/`
- `app/ui/vendeur/historique_ventes/`
- `app/ui/gerant/rapports/`
- `app/ui/gerant/alertes/`
- `app/ui/layouts/main_layout.py`
- `tests/test_rapport_service.py`
- `tests/test_main_window.py`
- `dev/rapport_pistis.md`

### Validation executee

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rapport_service.py tests/test_main_window.py tests/test_ticket_service.py tests/test_vente_service.py
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\pyinstaller.exe app/main.py --name SALMOSPHARM --windowed --onedir --icon app/assets/logo.ico --add-data "app/assets;assets" --noconfirm
```

Resultats :

```txt
40 passed
88 passed
Build PyInstaller reussi, executable genere : dist\SALMOSPHARM\SALMOSPHARM.exe
```

### Limites restantes

- Les filtres date avances restent minimalistes cote UI ; la couche service les supporte deja.
- Les graphiques visuels ne sont pas ajoutes : la phase valide des rapports calcules sous forme de tableaux denses et lisibles.

## Correction UI Phase 17 - Alignement maquettes rapports/historiques

### Perimetre corrige

- `Rapports` adopte une structure proche de la maquette fournie : titre `Rapports et statistiques`, actions de periode/export, cartes metriques, graphique en barres, graphique donut et tableau de performance vendeurs.
- Les graphiques sont dessines en PySide natif avec `QPainter`; aucune dependance graphique supplementaire n'a ete ajoutee.
- Le menu gerant `Historique` affiche maintenant le journal des actions systeme, avec filtres visuels, table d'actions et resume lateral.
- Le menu gerant `Ventes` conserve l'historique des ventes validees et l'ouverture des tickets.
- Ajout d'un test service pour verifier que le gerant peut consulter le journal d'actions et que le vendeur est refuse.

### Validation executee

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_rapport_service.py tests/test_main_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
28 passed
89 passed
```
## Migration graphique et iconographique

- Les graphiques des tableaux de bord gerant et vendeur ainsi que ceux des rapports utilisent desormais `PySide6.QtCharts`.
- Les courbes, histogrammes, diagrammes annulaires et anneaux de progression sont centralises dans `app/ui/components/charts.py`.
- Les icones des ecrans sont harmonisees avec `QtAwesome 1.4.2` via le composant semantique `ui_icon`.
- Les dessins `QPainter` conserves concernent uniquement les illustrations, fonds et recadrages d'images, pas les graphiques de donnees.

## Refonte fonctionnelle de l'ecran Rapports

- Ajout de `RapportRepository` pour isoler toutes les requetes SQL des rapports et historiques.
- Calcul sur une periode inclusive : chronologie journaliere, categories, performances vendeurs et comparaison avec la periode precedente.
- Modes Journalier, Mensuel et Par vendeur relies a des donnees reelles sans table `rapports`.
- Reproduction de la maquette avec cartes alternees, histogramme annote, donut avec legende complete et tableau vendeur totalise.
- Deux filtres de date accessibles, etat vide explicite et absence de defilement a 1450 x 900.
- Export du rapport affiche en classeur Excel reserve au gerant.

## Phase 18 - Backup et restauration

- Ajout du format `.spharm` avec base SQLite coherente, manifeste JSON, assets et factures.
- Export SQLite realise avec l'API `backup()` et journalise par `BACKUP_EXPORTE`.
- Validation du checksum SHA-256, du schema, de `integrity_check`, des cles et des chemins ZIP.
- Import reserve au gerant avec sauvegarde `.spharm` obligatoire avant remplacement.
- Remplacement de la base et des fichiers avec rollback automatique en cas d'echec.
- Finalisation de `BACKUP_IMPORTE` dans la base restauree au redemarrage.
- Ajout du panneau Sauvegarde et restauration dans les Parametres gerant.

## Phase 19 - Sauvegarde automatique

- Sauvegarde quotidienne au premier usage authentifie, sans doublon le meme jour.
- Sauvegarde a la fermeture uniquement lorsque les donnees ont change depuis la connexion.
- Modes `QUOTIDIENNE`, `FERMETURE` et `MANUELLE`, avec activation persistante dans `parametres`.
- Empreinte SHA-256 de la base, des assets et des factures pour detecter les modifications reelles.
- Journalisation `SAUVEGARDE_AUTO_CREEE` et mise a jour de `derniere_sauvegarde`.
- Conservation des 15 dernieres archives internes sans supprimer les exports manuels.
- Sauvegarde pre-import de la phase 18 conservee et incluse dans la retention.
- Reglages accessibles dans le panneau Parametres reserve au gerant.
- Echec automatique non bloquant, consigne dans `AppData\Local\SALMOSPHARM\logs\salmospharm.log`.

### Validation executee

```txt
104 tests pytest reussis
Build PyInstaller reussi
Executable dist\SALMOSPHARM\SALMOSPHARM.exe lance avec succes
Controle visuel Parametres a 1450 x 900 sans defilement
```

## Phase 20 - Exports Excel

- Export du catalogue produits avec recherche, categorie, statut et filtre de stock minimum.
- Export des lots de stock avec quantites, prix d'achat CDF, expirations et etat explicite.
- Export complet des ventes validees, sans la limite d'affichage de 100 lignes.
- Export des rapports journalier, mensuel et par vendeur avec synthese, evolution, categories, vendeurs et produits vendus.
- Generation `.xlsx` centralisee avec filtres, volets figes, largeurs adaptees et formats CDF/date.
- Ecriture atomique et neutralisation des textes pouvant etre interpretes comme formules Excel.
- Permission `EXPORTER_DONNEES` verifiee dans chaque service et journalisation `EXPORT_EXCEL`.
- Boutons QtAwesome accessibles sur Produits, Stock, Ventes et Rapports.

### Validation executee

```txt
108 tests pytest reussis
Classeur produits, stock, ventes et rapports relus avec openpyxl
Controle visuel des quatre ecrans a 1450 x 900
Build PyInstaller reussi
Executable dist\SALMOSPHARM\SALMOSPHARM.exe lance avec succes
```

## Stabilisation fonctionnelle et accessibilite - Phase 21

- Suppression de `Se souvenir de moi`, des placeholders, de l'import catalogue
  inactif, de la remise interdite et de la photo de profil non persistante.
- Validation par Entree sur la connexion, le premier lancement et les formulaires
  principaux, avec noms accessibles, focus visible et messages simples.
- Recuperation de compte complete : code verifie, mot de passe remplace, ancien
  code invalide et nouveau code affiche une seule fois.
- Tableaux de bord gerant et vendeur relies aux ventes reelles avec periodes
  Jour, 7 jours et 30 jours.
- Nouvelle vente disponible pour le gerant, confirmation avant vente definitive,
  historique vendeur sans export global et recherche vendeur en lecture seule.
- Modification, desactivation et reactivation des vendeurs reliees au service.
- Parametres pharmacie, imprimante, ticket 58/80 mm, impression automatique et
  securite du compte ajoutes sans changement de theme.
- Alertes migrees avec etat actif, derniere detection et resolution. Une file Qt
  deduplique les changements, un worker utilise sa propre session SQLAlchemy et
  une reconciliation complete s'execute toutes les 60 secondes.
- Alertes persistantes reactivees au prochain lancement, resolues automatiquement
  et recreees comme nouvelle occurrence en cas de recidive.
- Navigation, filtres d'historique, compteur d'alertes et recherche globale
  branches sur les pages reelles.
- Mise en page verifiee sans depassement horizontal a 1450x900, 1366x768 et
  1080x680; le defilement vertical reste disponible en hauteur reduite.
- Contraste des champs verrouille par palette Qt pour eviter le texte ou les
  placeholders invisibles selon le theme Windows, y compris a l'etat desactive.
- Ecran Factures reconstruit selon la maquette validee : indicateurs du jour,
  recherche, historique a gauche, apercu detaille a droite, badge, pagination,
  icones et actions impression/PDF. Les donnees restent derivees des ventes,
  sans creation d'une table `factures`.
- Sidebar conservee sur les fenetres de bureau a partir de 1180 px afin de
  respecter les proportions de la maquette Factures.

### Validation executee

```txt
115 tests pytest reussis
Compilation de tous les modules app reussie
python app/main.py lance avec succes dans un AppData temporaire
Build PyInstaller reussi
dist\SALMOSPHARM\SALMOSPHARM.exe lance avec succes
git diff --check sans erreur
```
