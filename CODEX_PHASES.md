# CODEX_PHASES.md — Guide d’implémentation phase par phase

## Projet

**SALMOSPHARM 133**  
Application desktop Windows de gestion de pharmacie.

Ce fichier guide Codex dans l’ordre d’implémentation du projet.

Il doit être utilisé avec :

```txt
AGENTS.md
docs/01_CONTEXTE_ET_OBJECTIFS.md
docs/02_ARCHITECTURE_ET_STACK.md
docs/03_REGLES_METIER_ET_SECURITE.md
docs/04_BASE_DE_DONNEES_SQLITE.md
docs/05_MODULES_UI_LIVRAISON.md
```

---

# Principe général

L’application doit être construite progressivement.

À chaque phase :

```txt
- le projet doit rester lançable ;
- les tests doivent être faits progressivement ;
- le .exe doit être testé tôt ;
- l’architecture doit rester propre ;
- la logique métier doit rester dans les services ;
- l’UI ne doit jamais modifier directement la base.
```

Stratégie :

```txt
Build early, test often.
```

En français :

```txt
Construire tôt, tester souvent.
```

---

# Phase 0 — Préparation de l’environnement

## Objectif

Préparer le dossier de projet, l’environnement Python et les dépendances de base.

## À créer

```txt
salmospharm/
requirements.txt
README.md
AGENTS.md
CODEX_PHASES.md
docs/
app/
tests/
installer/
```

## Commandes recommandées

Sur Windows :

```bat
mkdir salmospharm
cd salmospharm
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

Installer les premières dépendances :

```bat
pip install PySide6 SQLAlchemy alembic passlib[bcrypt] pytest pyinstaller
```

Créer `requirements.txt` :

```bat
pip freeze > requirements.txt
```

## À vérifier

```txt
- Python est installé.
- L’environnement virtuel s’active.
- pip fonctionne.
- PySide6 s’installe.
- pytest s’installe.
```

## Si blocage

Chercher :

```txt
python venv windows activate
pip install PySide6 Windows
```

---

# Phase 1 — Créer la structure de base du projet

## Objectif

Créer l’arborescence officielle.

## À créer

```txt
app/main.py
app/core/
app/database/
app/repositories/
app/services/
app/ui/
app/ui/login/
app/ui/first_run/
app/ui/layouts/
app/ui/components/
app/ui/gerant/
app/ui/vendeur/
app/assets/
app/utils/
tests/
installer/
```

## Règles

Ne pas encore coder les modules métier.

Créer une structure propre et vide ou minimale.

## Test manuel

Vérifier que l’arborescence correspond à celle indiquée dans `AGENTS.md`.

---

# Phase 2 — Mini application PySide6

## Objectif

Créer une première fenêtre desktop très simple.

## Fichier principal

```txt
app/main.py
```

## Comportement attendu

L’application affiche une fenêtre avec :

```txt
SALMOSPHARM 133
Application lancée avec succès
```

et un bouton :

```txt
Quitter
```

## Commande de test

```bat
python app/main.py
```

## Critères d’acceptation

```txt
- la fenêtre s’ouvre ;
- le titre de fenêtre est correct ;
- le bouton Quitter ferme l’application ;
- aucune erreur dans le terminal.
```

## Si blocage

Chercher :

```txt
PySide6 QApplication QMainWindow example
PySide6 QPushButton clicked close
```

---

# Phase 3 — Premier build .exe avec PyInstaller

## Objectif

Tester très tôt la génération d’un `.exe`.

## À créer

```txt
build.bat
```

## Commande recommandée

```bat
pyinstaller app/main.py ^
  --name SALMOSPHARM ^
  --windowed ^
  --onedir
```

## Résultat attendu

```txt
dist/SALMOSPHARM/SALMOSPHARM.exe
```

## Test manuel

```txt
1. Lancer build.bat.
2. Ouvrir dist/SALMOSPHARM/SALMOSPHARM.exe.
3. Vérifier que la fenêtre s’ouvre.
4. Vérifier qu’il n’y a pas de terminal noir.
5. Vérifier que Python n’est pas demandé.
```

## Critères d’acceptation

```txt
- l’exe s’ouvre ;
- l’app fonctionne comme en développement ;
- aucun fichier Python externe n’est demandé manuellement.
```

## Si blocage

Chercher :

```txt
PyInstaller PySide6 --onedir Windows
PyInstaller --windowed Windows
```

---

# Phase 4 — Gestion des chemins AppData

## Objectif

Créer automatiquement les dossiers de données utilisateur.

## Fichiers concernés

```txt
app/core/paths.py
app/main.py
```

## Dossiers à créer automatiquement

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\
├── data\
├── backups\
├── logs\
├── factures\
├── exports\
├── assets\
└── config\
```

## Fonctions recommandées

Dans `app/core/paths.py` :

```python
get_user_data_dir()
get_database_path()
get_backups_dir()
get_logs_dir()
get_factures_dir()
get_exports_dir()
get_assets_dir()
ensure_app_dirs()
```

## Test manuel

```txt
1. Fermer l’application.
2. Supprimer temporairement AppData/Local/SALMOSPHARM si c’est un environnement de test.
3. Lancer python app/main.py.
4. Vérifier que les dossiers sont créés.
5. Relancer l’application.
6. Vérifier qu’elle ne recrée pas inutilement ou ne plante pas.
```

## Critères d’acceptation

```txt
- les dossiers sont créés automatiquement ;
- aucune donnée n’est écrite dans Program Files ;
- les chemins sont centralisés dans paths.py.
```

## Si blocage

Chercher :

```txt
Python pathlib AppData LocalAppData Windows
os.environ LOCALAPPDATA Python
```

---

# Phase 5 — SQLite et SQLAlchemy

## Objectif

Mettre en place la connexion SQLite locale.

## Fichiers concernés

```txt
app/database/connection.py
app/database/models.py
app/database/init_db.py
app/database/seed.py
app/database/schema.sql
app/core/paths.py
```

## Règles

La base doit être stockée ici :

```txt
AppData/Local/SALMOSPHARM/data/salmospharm.sqlite3
```

Activer à chaque connexion :

```sql
PRAGMA foreign_keys = ON;
```

## Tables à créer

```txt
utilisateurs
categories
produits
lots_produits
mouvements_stock
ventes
lignes_vente
alertes
journaux_activite
parametres
```

## Interdits

Ne pas créer :

```txt
modes_paiement
paiements
factures
rapports
clients
fournisseurs
```

## Test manuel

```txt
1. Supprimer la base de test si nécessaire.
2. Lancer l’application.
3. Vérifier que salmospharm.sqlite3 est créé.
4. Ouvrir la base avec DB Browser for SQLite.
5. Vérifier que les tables existent.
6. Vérifier que les catégories initiales existent.
7. Vérifier qu’un enregistrement parametres existe.
```

## Test automatisé recommandé

```txt
tests/test_database_init.py
```

Vérifier :

```txt
- base créée ;
- tables créées ;
- foreign_keys activées ;
- données initiales présentes.
```

## Si blocage

Chercher :

```txt
SQLAlchemy SQLite engine sessionmaker example
SQLAlchemy event PRAGMA foreign_keys SQLite
SQLAlchemy declarative base models
```

---

# Phase 6 — Modèles et repositories

## Objectif

Créer les modèles SQLAlchemy et les repositories de base.

## Fichiers à créer

```txt
app/repositories/utilisateur_repository.py
app/repositories/categorie_repository.py
app/repositories/produit_repository.py
app/repositories/lot_produit_repository.py
app/repositories/stock_repository.py
app/repositories/vente_repository.py
app/repositories/alerte_repository.py
app/repositories/journal_repository.py
app/repositories/parametre_repository.py
```

## Règle

Les repositories font l’accès base.

Ils ne doivent pas contenir de logique métier lourde.

## Exemple de responsabilité repository

```txt
- chercher par id ;
- lister ;
- créer ;
- modifier ;
- récupérer les lots disponibles ;
- récupérer les ventes d’un vendeur ;
- insérer une ligne de vente.
```

## Interdit

Ne pas mettre dans les repositories :

```txt
- décision FEFO complète ;
- vérification permission complète ;
- validation de vente complète ;
- logique d’import backup ;
- messages utilisateur.
```

Ces responsabilités vont dans les services.

---

# Phase 7 — Exceptions, constantes et permissions

## Objectif

Centraliser les constantes, exceptions et règles de permissions.

## Fichiers à créer

```txt
app/core/constants.py
app/core/exceptions.py
app/core/permissions.py
```

## Constantes importantes

```txt
ROLE_GERANT
ROLE_VENDEUR
DEVISE_UNIQUE = CDF
MODE_PAIEMENT_UNIQUE = ESPECES
TYPES_MOUVEMENT_STOCK
TYPES_ALERTES
ACTIONS_JOURNAL
LARGEURS_TICKET
```

## Exceptions importantes

```txt
PermissionRefuseeError
StockInsuffisantError
ProduitExpireError
UtilisateurInactifError
BackupInvalideError
ImprimanteIndisponibleError
ValidationError
```

## Tests recommandés

```txt
tests/test_permissions.py
```

Vérifier :

```txt
- gérant autorisé sur actions sensibles ;
- vendeur refusé sur actions gérant ;
- rôle inconnu refusé.
```

---

# Phase 8 — Premier lancement et création du gérant

## Objectif

Créer le compte gérant au premier lancement si aucun utilisateur n’existe.

## Fichiers concernés

```txt
app/services/auth_service.py
app/services/recuperation_service.py
app/services/journal_service.py
app/core/security.py
app/ui/first_run/
app/ui/login/
```

## Règles

```txt
- pas de compte admin/admin ;
- mot de passe hashé ;
- code de récupération généré ;
- code affiché une seule fois ;
- hash du code stocké ;
- création journalisée.
```

## Tests manuels

```txt
1. Supprimer la base de test.
2. Lancer l’application.
3. Vérifier que l’écran création gérant apparaît.
4. Créer le gérant.
5. Vérifier que le code de récupération apparaît.
6. Fermer l’application.
7. Relancer.
8. Vérifier que l’écran de connexion apparaît.
9. Se connecter avec le gérant.
```

## Tests automatisés

```txt
tests/test_auth_service.py
```

Cas :

```txt
- création gérant ;
- mot de passe hashé ;
- code récupération hashé ;
- pas de création double du premier gérant.
```

## Si blocage

Chercher :

```txt
passlib bcrypt hash verify Python
secrets token_urlsafe Python
PySide6 form input password
```

---

# Phase 9 — Connexion et session utilisateur

## Objectif

Permettre aux utilisateurs de se connecter.

## Fichiers concernés

```txt
app/services/auth_service.py
app/core/security.py
app/ui/login/
app/ui/layouts/
```

## Comportement attendu

```txt
- identifiant/email + mot de passe ;
- refus si mauvais mot de passe ;
- refus si compte désactivé ;
- redirection selon rôle ;
- session en mémoire ;
- journalisation connexion réussie/échouée.
```

## Tests manuels

```txt
- connexion gérant valide ;
- mauvais mot de passe refusé ;
- vendeur valide ;
- vendeur désactivé refusé ;
- déconnexion.
```

---

# Phase 10 — Layout principal et navigation

## Objectif

Créer l’interface principale avec sidebar et topbar.

## Fichiers concernés

```txt
app/ui/layouts/
app/ui/components/
app/ui/gerant/
app/ui/vendeur/
```

## Layout attendu

```txt
Fenêtre principale
├── Sidebar gauche
├── Topbar
├── Zone de contenu
└── Footer discret / version
```

## Règle

La sidebar dépend du rôle.

Gérant :

```txt
Tableau de bord
Produits
Stock
Ventes
Factures
Rapports
Vendeurs
Historique
Alertes
Paramètres
Déconnexion
```

Vendeur :

```txt
Tableau de bord
Nouvelle vente
Historique des ventes
Recherche produit
Factures
Déconnexion
```

## Tests manuels

```txt
- gérant voit les menus gérant ;
- vendeur voit seulement les menus vendeur ;
- navigation fonctionnelle ;
- aucun écran gérant visible côté vendeur.
```

---

# Phase 11 — Produits et catégories

## Objectif

Implémenter la gestion des produits et catégories.

## Fichiers concernés

```txt
app/services/produit_service.py
app/repositories/produit_repository.py
app/repositories/categorie_repository.py
app/ui/gerant/produits/
```

## Fonctionnalités

```txt
- ajouter catégorie ;
- ajouter produit ;
- modifier produit ;
- désactiver produit ;
- rechercher produit ;
- filtrer par catégorie.
```

## Règles

```txt
- gérant uniquement ;
- prix en INTEGER CDF ;
- prix négatif refusé ;
- code-barres unique ;
- produit historique désactivé plutôt que supprimé.
```

## Tests

```txt
- créer catégorie ;
- créer produit ;
- prix négatif refusé ;
- code-barres doublon refusé ;
- vendeur interdit de création produit.
```

---

# Phase 12 — Lots et stock

## Objectif

Implémenter la gestion des lots, entrées et ajustements de stock.

## Fichiers concernés

```txt
app/services/stock_service.py
app/repositories/lot_produit_repository.py
app/repositories/stock_repository.py
app/services/alerte_service.py
app/ui/gerant/stock/
```

## Fonctionnalités

```txt
- entrée de stock ;
- création/mise à jour lot ;
- ajustement de quantité ;
- mouvement ENTREE ;
- mouvement AJUSTEMENT ;
- alertes stock faible ;
- alertes expiration proche.
```

## Règles

```txt
- gérant uniquement ;
- quantité jamais négative ;
- chaque modification crée un mouvement ;
- chaque action sensible est journalisée ;
- stock disponible calculé depuis les lots.
```

## Tests

```txt
- entrée stock ;
- ajustement avec motif ;
- quantité négative refusée ;
- mouvement créé ;
- alerte stock faible créée ;
- alerte expiration proche créée.
```

---

# Phase 13 — FEFO

## Objectif

Créer la logique de sélection des lots selon FEFO.

## Fichier principal

```txt
app/services/stock_service.py
```

ou :

```txt
app/services/vente_service.py
```

## Fonction recommandée

```txt
choisir_lots_fefo(produit_id, quantite_demandee)
```

## Logique

```txt
1. récupérer les lots disponibles ;
2. exclure les lots expirés ;
3. exclure les lots quantité 0 ;
4. trier par date d’expiration croissante ;
5. prendre les quantités nécessaires ;
6. retourner la répartition ;
7. lever StockInsuffisantError si stock insuffisant.
```

## Test obligatoire

Créer :

```txt
Lot A : 5 unités, expiration proche
Lot B : 10 unités, expiration lointaine
Vente demandée : 8 unités
```

Résultat attendu :

```txt
Lot A : 5 unités sorties
Lot B : 3 unités sorties
```

## Tests automatisés

```txt
tests/test_stock_service.py
```

Cas :

```txt
- FEFO simple ;
- FEFO sur plusieurs lots ;
- lot expiré ignoré ;
- stock insuffisant refusé ;
- lot quantité 0 ignoré.
```

---

# Phase 14 — Vente complète

## Objectif

Implémenter la validation complète d’une vente.

## Fichier principal

```txt
app/services/vente_service.py
```

## Fonction recommandée

```txt
valider_vente(utilisateur_connecte, panier, montant_recu)
```

## Étapes obligatoires

```txt
1. vérifier utilisateur connecté ;
2. vérifier rôle autorisé ;
3. vérifier panier non vide ;
4. vérifier produits actifs ;
5. vérifier quantités positives ;
6. vérifier stock disponible ;
7. appliquer FEFO ;
8. vérifier montant reçu >= total ;
9. ouvrir transaction SQLAlchemy ;
10. créer vente ;
11. créer lignes_vente ;
12. décrémenter lots ;
13. créer mouvements_stock ;
14. générer alertes si nécessaire ;
15. journaliser VENTE_VALIDEE ;
16. retourner résultat de vente.
```

## Règle importante

Tout doit être atomique.

Si une étape échoue :

```txt
aucune vente ne doit rester partiellement enregistrée.
```

## Tests obligatoires

```txt
tests/test_vente_service.py
```

Cas :

```txt
- vente valide ;
- panier vide refusé ;
- montant insuffisant refusé ;
- stock insuffisant refusé ;
- lot expiré refusé ;
- vendeur autorisé ;
- vendeur désactivé refusé ;
- FEFO appliqué ;
- mouvements créés ;
- journal créé ;
- vente non annulable.
```

---

# Phase 15 — Écran Nouvelle vente

## Objectif

Connecter l’interface de vente au service `vente_service`.

## Fichiers concernés

```txt
app/ui/vendeur/nouvelle_vente/
app/ui/gerant/ventes/
app/services/vente_service.py
```

## Interface attendue

```txt
- recherche produit ;
- liste des produits vendables ;
- panier ;
- quantité ;
- total ;
- montant reçu ;
- monnaie rendue ;
- bouton Encaisser ;
- aperçu ticket après validation.
```

## Règle

L’écran appelle le service.

Il ne décrémente jamais le stock lui-même.

## Tests manuels

```txt
- ajouter produit au panier ;
- modifier quantité ;
- retirer produit du panier ;
- montant reçu insuffisant ;
- vente valide ;
- affichage du ticket ;
- stock mis à jour après vente.
```

---

# Phase 16 — Tickets et impression thermique

## Objectif

Générer et imprimer les tickets.

## Fichiers concernés

```txt
app/services/ticket_service.py
app/services/impression_service.py
app/services/facture_service.py
app/ui/components/TicketPreview
```

## Technologies

```txt
python-escpos
pywin32
ReportLab pour PDF optionnel
```

## Tests manuels

```txt
- générer aperçu ticket ;
- imprimer ticket 80 mm ;
- imprimer ticket 58 mm ;
- impression automatique ;
- réimpression par vendeur de ses ventes ;
- réimpression par gérant de toutes les ventes ;
- erreur imprimante affichée proprement.
```

## Règle

Une erreur d’impression ne doit jamais annuler une vente validée.

---

# Phase 17 — Historique des ventes, rapports et alertes

## Objectif

Ajouter les écrans de consultation et rapports.

## Fichiers concernés

```txt
app/services/rapport_service.py
app/services/alerte_service.py
app/ui/gerant/rapports/
app/ui/gerant/alertes/
app/ui/gerant/historique/
app/ui/vendeur/historique_ventes/
```

## Règles

```txt
- gérant voit toutes les ventes ;
- vendeur voit seulement ses ventes ;
- rapports calculés par requêtes ou vues ;
- pas de table rapports ;
- tickets générés depuis les ventes, pas depuis une table factures.
```

## Tests

```txt
- rapport journalier ;
- rapport mensuel ;
- rapport par vendeur ;
- produits les plus vendus ;
- vendeur limité à ses ventes ;
- gérant voit tout.
```

---

# Phase 18 — Backup et restauration

## Objectif

Implémenter export/import `.spharm`.

## Fichier principal

```txt
app/services/backup_service.py
```

## Contenu du backup

```txt
database/salmospharm.sqlite3
assets/
factures/
manifest.json
```

## Règles

```txt
- gérant uniquement ;
- utiliser SQLite backup() ;
- vérifier manifest.json ;
- sauvegarde de sécurité avant import ;
- remplacement sécurisé ;
- journalisation ;
- redémarrage après import si nécessaire.
```

## Tests manuels

```txt
1. Créer données test.
2. Exporter .spharm.
3. Installer/lancer sur autre PC ou autre profil Windows.
4. Importer.
5. Vérifier que les données sont restaurées.
6. Tester fichier invalide.
7. Vérifier que vendeur est refusé.
```

## Tests automatisés

```txt
tests/test_backup_service.py
```

---

# Phase 19 — Sauvegarde automatique

## Objectif

Ajouter les sauvegardes automatiques.

## Règles

```txt
- sauvegarde quotidienne si l’application est utilisée ;
- sauvegarde à la fermeture si données changées ;
- sauvegarde obligatoire avant import ;
- conservation des 15 dernières sauvegardes.
```

## Tests

```txt
- backup auto créé ;
- anciens backups nettoyés ;
- sauvegarde avant import créée.
```

---

# Phase 20 — Exports Excel

## Objectif

Permettre au gérant d’exporter certaines listes et rapports.

## Technologie

```txt
openpyxl
```

## Exports possibles

```txt
- produits ;
- stock ;
- ventes ;
- rapport journalier ;
- rapport mensuel ;
- rapport vendeur.
```

## Règles

```txt
- gérant uniquement ;
- montants en CDF ;
- fichiers dans AppData/Local/SALMOSPHARM/exports si nécessaire.
```

---

# Phase 21 — Tests complets

## Objectif

Stabiliser l’application avant livraison.

## Commandes

```bat
pytest
python app/main.py
build.bat
```

## Tests manuels prioritaires

```txt
- premier lancement ;
- création gérant ;
- code récupération ;
- connexion gérant ;
- création vendeur ;
- connexion vendeur ;
- permissions vendeur ;
- création produit ;
- entrée stock ;
- lot expiré ;
- vente FEFO ;
- impression ;
- réimpression ;
- rapport ;
- backup export ;
- backup import ;
- application packagée.
```

## Critères d’acceptation

```txt
- aucun test critique échoué ;
- aucun écran bloquant ;
- aucune vente partiellement enregistrée ;
- aucune donnée écrite dans Program Files ;
- l’exe se lance ;
- l’installateur fonctionne.
```

---

# Phase 22 — Installateur Windows

## Objectif

Créer l’installateur final.

## Technologies

```txt
PyInstaller --onedir
Inno Setup
```

## Livrable

```txt
SALMOSPHARM_Setup.exe
```

## Règles

```txt
- installer dans Program Files ;
- créer raccourci bureau ;
- créer menu démarrer ;
- ne pas écraser AppData ;
- ne pas livrer le code source ;
- ne pas demander Python au client.
```

## Tests sur Windows propre

```txt
1. Installer SALMOSPHARM_Setup.exe.
2. Lancer depuis le bureau.
3. Créer gérant.
4. Créer vendeur.
5. Créer produit.
6. Entrer stock.
7. Faire une vente.
8. Tester ticket.
9. Exporter backup.
10. Désinstaller.
11. Réinstaller.
12. Vérifier que les données utilisateur ne sont pas supprimées si c’est le comportement voulu.
```

---

# Phase 23 — Version candidate

## Objectif

Préparer une version presque finale.

## À faire

```txt
- corriger bugs critiques ;
- relire règles métier ;
- vérifier permissions ;
- vérifier messages utilisateur ;
- vérifier backup ;
- vérifier impression ;
- vérifier installateur ;
- faire une démo complète.
```

## Interdit

Ne pas ajouter de nouvelle fonctionnalité majeure à cette étape.

On corrige, on stabilise, on livre.

---

# Phase 24 — Livraison

## Livrables

```txt
SALMOSPHARM_Setup.exe
Guide d’installation simple
Code de récupération généré au premier lancement
Procédure de backup/restauration
```

## Checklist finale

```txt
[ ] L’application s’installe.
[ ] L’application se lance sans Python.
[ ] Le premier compte gérant se crée.
[ ] Le code de récupération s’affiche.
[ ] Le gérant peut créer un vendeur.
[ ] Le vendeur peut vendre.
[ ] Le stock diminue correctement.
[ ] FEFO fonctionne.
[ ] Les lots expirés sont bloqués.
[ ] Les ventes sont non annulables.
[ ] Les tickets s’impriment.
[ ] Les rapports s’affichent.
[ ] Le backup export fonctionne.
[ ] Le backup import fonctionne.
[ ] Le vendeur n’accède pas aux fonctions gérant.
[ ] Les données sont dans AppData.
[ ] Le client reçoit un installateur.
```

---

# Règles de passage entre phases

Ne pas passer à la phase suivante si :

```txt
- l’application ne démarre plus ;
- les tests critiques échouent ;
- l’exe ne se lance plus après une phase de packaging ;
- une règle métier validée est cassée ;
- une fonctionnalité critique est partiellement codée mais non testée.
```

On peut passer à la suite si :

```txt
- la phase fonctionne en développement ;
- les tests prévus sont faits ;
- les fichiers touchés sont cohérents ;
- les règles métier restent respectées ;
- les limites connues sont notées.
```

---

# Comment demander une tâche à Codex

Exemple de prompt à utiliser :

```txt
Tu es dans le projet SALMOSPHARM 133.

Lis d’abord AGENTS.md, CODEX_PHASES.md et les fichiers docs nécessaires.

Nous sommes à la Phase 5 — SQLite et SQLAlchemy.

Objectif : mettre en place la connexion SQLite locale, les modèles SQLAlchemy et l’initialisation de la base.

Respecte l’architecture UI → Services → Repositories → SQLite.
Ne crée aucune table interdite.
Stocke la base dans AppData/Local/SALMOSPHARM/data.
Active PRAGMA foreign_keys = ON.
Ajoute les tests nécessaires.
À la fin, donne les commandes à lancer et les tests manuels à faire.
```

---

# Résumé pour Codex

Toujours travailler ainsi :

```txt
1. Identifier la phase.
2. Lire AGENTS.md.
3. Lire les docs projet nécessaires.
4. Modifier peu de fichiers à la fois.
5. Tester.
6. Garder l’application lançable.
7. Respecter les règles métier.
8. Expliquer ce qui a été fait.
9. Donner les commandes à lancer.
10. Donner les vérifications manuelles.
```
