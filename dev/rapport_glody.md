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

## 2026-06-25 - Phase 10 UI - Layout principal et navigation

### Ce qui a ete fait

- Remplacement de la fenetre principale transitoire par un vrai layout connecte.
- Creation d'une sidebar adaptee au role connecte :
  - menu gerant : Tableau de bord, Produits, Stock, Ventes, Vendeurs, Historique, Alertes, Parametres, Deconnexion ;
  - menu vendeur : Tableau de bord, Nouvelle vente, Recherche produit, Historique des ventes, Tickets, Deconnexion.
- Creation d'une topbar affichant :
  - le titre de page active ;
  - le nom de l'utilisateur connecte ;
  - le role ;
  - une action de deconnexion.
- Creation des dashboards placeholders gerant et vendeur avec cartes visuelles fictives.
- Creation de pages placeholders neutres pour les autres entrees de navigation.
- Branchement de `app/main.py` :
  - apres `LoginWindow.connexion_reussie`, ouverture du nouveau `MainWindow` ;
  - conservation de la `SessionUtilisateur` en memoire ;
  - fermeture de `LoginWindow` ;
  - deconnexion UI vers un nouvel ecran de connexion.
- Aucun acces direct SQLite, aucune session SQLAlchemy et aucune logique metier critique n'ont ete ajoutes dans l'UI.
- Aucun menu `Factures` ou `Rapports` persistant n'a ete ajoute, conformement a la consigne Phase 10 specifique.

### Fichiers principaux

- `app/main.py`
- `app/ui/layouts/main_layout.py`
- `app/ui/layouts/sidebar.py`
- `app/ui/layouts/topbar.py`
- `app/ui/layouts/__init__.py`
- `app/ui/gerant/dashboard_page.py`
- `app/ui/gerant/__init__.py`
- `app/ui/vendeur/dashboard_page.py`
- `app/ui/vendeur/__init__.py`
- `tests/test_main_window.py`
- `tests/test_login_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 8 passed
pytest global : 31 passed
```

### Limites restantes

- Les deux images de maquette Phase 10 n'etaient pas presentes dans le message de travail. Le layout respecte donc les contraintes ecrites et un style medical professionnel, mais l'ajustement pixel/visuel exact devra etre fait apres reception des images.
- Les dashboards utilisent volontairement des donnees fictives et placeholders.
- Les vraies statistiques, ventes, alertes, produits et tickets ne sont pas encore branches aux services metier.

## 2026-06-25 - Phase 10 UI - Reproduction des maquettes dashboard

### Ce qui a ete fait

- Lecture et prise en compte des deux maquettes fournies :
  - dashboard vendeur `1SML.jpeg` ;
  - dashboard gerant `2sml.jpeg`.
- Refonte visuelle du layout principal pour se rapprocher des maquettes :
  - sidebar blanche avec grand logo SALMOSPHARM ;
  - menu actif vert clair avec barre laterale ;
  - topbar avec bouton menu, recherche, date et notification ;
  - zone centrale blanche/tres claire ;
  - cartes statistiques blanches avec icones rondes colorees ;
  - footer bleu fonce avec copyright et version.
- Refonte du dashboard gerant placeholder :
  - 5 cartes statistiques ;
  - graphique fictif d'evolution des ventes ;
  - top produits vendus ;
  - synthese par vendeur ;
  - activites recentes ;
  - alertes rapides.
- Refonte du dashboard vendeur placeholder :
  - 4 cartes statistiques ;
  - graphique fictif horaire ;
  - ventes recentes ;
  - produits les plus vendus aujourd'hui ;
  - objectifs et performance.
- Les menus ont ete rapproches des maquettes :
  - gerant : Tableau de bord, Produits, Stock, Ventes, Factures, Rapports, Vendeurs, Historique, Alertes, Parametres ;
  - vendeur : Tableau de bord, Nouvelle vente, Historique des ventes, Produits, Factures.
- Adaptation obligatoire : les lignes de vente de la maquette qui indiquaient `Mobile` ont ete remplacees par `Especes`, car le projet interdit le paiement mobile.
- Les pages `Factures` et `Rapports` restent des placeholders UI uniquement :
  - aucune table `factures` creee ;
  - aucune table `rapports` creee ;
  - aucune logique metier branchee.

### Fichiers principaux

- `app/ui/layouts/sidebar.py`
- `app/ui/layouts/topbar.py`
- `app/ui/layouts/main_layout.py`
- `app/ui/gerant/dashboard_page.py`
- `app/ui/vendeur/dashboard_page.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
rg -n "Mobile|mobile|USD|EUR|carte bancaire|paiement mixte|create_session|session\.add|SQLAlchemy|sqlite" app\ui app\main.py
```

Resultats :

```txt
tests UI cibles : 8 passed
pytest global : 31 passed
recherche interdits UI : aucun paiement/devise interdit ni acces direct SQLite detecte
```

### Limites restantes

- Les graphiques, ventes, produits, alertes et objectifs restent fictifs pour la Phase 10.
- Les icones sont des placeholders dessines/texte simple ; une phase de polish pourra remplacer ces pictogrammes par des assets si necessaire.

## 2026-06-25 - Phase 10 UI - Validation du bouton de connexion par role

### Ce qui a ete fait

- Verification du flux du bouton `Se connecter` :
  - `LoginWindow` appelle `AuthService.connecter(...)` ;
  - le service retourne une `SessionUtilisateur` ;
  - `LoginWindow` emet `connexion_reussie` ;
  - `app/main.py` ouvre `MainWindow(session_utilisateur=...)` ;
  - `MainWindow` adapte automatiquement sidebar et dashboard selon `GERANT` ou `VENDEUR`.
- Ajout d'un test UI simulant le clic sur `Se connecter` pour les deux roles.
- Verification que :
  - le gerant arrive sur l'interface gerant ;
  - le vendeur arrive sur l'interface vendeur ;
  - le vendeur ne voit pas `Parametres` ;
  - le gerant ne voit pas le menu vendeur `Nouvelle vente`.

### Fichiers principaux

- `tests/test_login_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_login_window.py tests\test_main_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 9 passed
pytest global : 32 passed
```

## 2026-06-25 - Phase 10 UI - Ajustements menu et accueil vide

### Ce qui a ete fait

- Ajustement du comportement au lancement de l'interface connectee :
  - la sidebar est masquee au demarrage ;
  - la zone centrale affiche uniquement le logo SALMOSPHARM centre ;
  - aucun dashboard n'est affiche automatiquement.
- Branchement du bouton menu de la topbar :
  - clic sur le bouton menu affiche ou masque la sidebar ;
  - clic sur `Tableau de bord` affiche ensuite le dashboard du role connecte.
- Ajustement de l'espacement de la sidebar :
  - logo reduit et moins colle au contenu ;
  - zone de navigation defilable ;
  - espace ajoute avant la carte utilisateur ;
  - `Parametres` n'est plus colle au bloc du bas.
- Conservation des contraintes :
  - aucune session SQLAlchemy dans l'UI ;
  - aucun acces direct SQLite ;
  - aucune logique metier de vente ou stock dans les widgets.

### Fichiers principaux

- `app/ui/layouts/main_layout.py`
- `app/ui/layouts/sidebar.py`
- `app/ui/layouts/topbar.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 10 passed
pytest global : 33 passed
```

## 2026-06-25 - Phase 10 UI - Scrollbar, theme et profil

### Ce qui a ete fait

- Ajustement visuel des barres de defilement :
  - barre plus fine ;
  - poignee grise arrondie ;
  - fleches haut/bas stylisees en petits triangles.
- Ajout d'un bouton dans `Parametres` :
  - `Basculer mode sombre / clair` ;
  - changement visuel local du theme sans persistance base.
- Ajout d'une page `Profil utilisateur` accessible depuis le bloc utilisateur en bas de la sidebar.
- Ajout d'un bouton `Choisir une photo de profil` :
  - selection locale d'une image ;
  - apercu dans l'interface ;
  - aucune ecriture en base pour cette phase.
- Conservation de l'architecture UI uniquement :
  - aucune session SQLAlchemy dans l'UI ;
  - aucune modification SQLite ;
  - aucune logique metier de compte utilisateur deplacee dans l'interface.

### Fichiers principaux

- `app/ui/layouts/main_layout.py`
- `app/ui/layouts/sidebar.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 12 passed
pytest global : 35 passed
```

## 2026-06-25 - Phase 10 UI - Photo de profil ronde dans la sidebar

### Ce qui a ete fait

- La photo choisie dans la page `Profil utilisateur` est maintenant affichee sous forme ronde.
- La meme photo apparait aussi dans la carte utilisateur en bas de la sidebar.
- Suppression de la petite fleche a cote du role `Gerant` / `Vendeur`.
- Le bloc utilisateur reste cliquable pour ouvrir la page profil.
- Le choix de photo reste local a la session et n'est pas encore persiste en base.

### Fichiers principaux

- `app/ui/layouts/main_layout.py`
- `app/ui/layouts/sidebar.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 13 passed
pytest global : 36 passed
```

## 2026-06-25 - Phase 10 UI - Icones et boutons Voir tout

### Ce qui a ete fait

- Ajout d'un helper d'icones vectorielles PySide dans `app/ui/components/icons.py`.
- Ajout d'icones dans la sidebar :
  - Tableau de bord ;
  - Produits ;
  - Stock ;
  - Ventes ;
  - Factures ;
  - Rapports ;
  - Vendeurs ;
  - Historique ;
  - Alertes ;
  - Parametres.
- Ajout des icones dans la topbar :
  - recherche ;
  - calendrier ;
  - notification ;
  - bouton menu.
- Ajout d'icones dans les cartes statistiques :
  - ventes du jour ;
  - transactions ;
  - total encaisse ;
  - produits en stock ;
  - stock faible ;
  - expirations proches ;
  - articles vendus.
- Remplacement de `7 derniers jours` par `Aujourd'hui` dans le dashboard gerant.
- Transformation des liens/boutons `Voir tout` en boutons ouvrant des pages detail placeholders.
- Les pages detail restent sans acces base et sans logique metier.

### Fichiers principaux

- `app/ui/components/icons.py`
- `app/ui/layouts/sidebar.py`
- `app/ui/layouts/topbar.py`
- `app/ui/layouts/main_layout.py`
- `app/ui/gerant/dashboard_page.py`
- `app/ui/vendeur/dashboard_page.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 15 passed
pytest global : 38 passed
```

## 2026-06-25 - Phase 10 UI - Demarrage direct sur dashboard

### Ce qui a ete fait

- Suppression de l'ecran vide initial avec logo apres connexion.
- Apres connexion, l'utilisateur arrive directement sur le tableau de bord de son role.
- Les tests UI ont ete ajustes pour verifier ce comportement.

### Fichiers principaux

- `app/ui/layouts/main_layout.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 15 passed
pytest global : 38 passed
```

## 2026-06-25 - Phase 10 UI - Choix clair/sombre dans Parametres

### Ce qui a ete fait

- Remplacement du bouton `Basculer mode sombre / clair` par deux choix explicites :
  - `Clair`
  - `Sombre`
- Lorsque `Sombre` est coche, l'interface passe en mode sombre.
- Lorsque `Clair` est coche, l'interface revient en mode clair.
- Le reglage reste visuel et non persiste en base pour cette phase.

### Fichiers principaux

- `app/ui/layouts/main_layout.py`
- `tests/test_main_window.py`
- `dev/rapport_glody.md`

### Validation

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_main_window.py tests\test_login_window.py
.\.venv\Scripts\python.exe -m pytest
```

Resultats :

```txt
tests UI cibles : 12 passed
pytest global : 35 passed
```
