# 02 — Architecture et stack technique

## 1. Rôle du document

Ce document définit l’architecture technique officielle de l’application **SALMOSPHARM 133**.

Il doit servir de référence pendant l’implémentation pour :

- le développeur principal ;
- les autres développeurs du projet ;
- Codex ;
- ChatGPT ;
- tout autre LLM utilisé pour générer, corriger ou refactoriser le code.

Ce fichier ne décrit pas les règles métier détaillées. Les règles métier sont centralisées dans :

```txt
03_REGLES_METIER_ET_SECURITE.md
```

Ce document répond surtout aux questions suivantes :

```txt
Quelle stack utiliser ?
Comment organiser le projet ?
Où placer chaque responsabilité ?
Quelles bibliothèques sont autorisées ?
Comment gérer les chemins locaux ?
Comment préparer l’application pour être livrée en exécutable Windows ?
```

---

## 2. Vision technique globale

SALMOSPHARM 133 est une application desktop locale destinée à fonctionner principalement sur Windows.

L’application doit être :

- simple à installer ;
- utilisable sans connexion Internet ;
- stable pour une utilisation quotidienne en pharmacie ;
- maintenable par un développeur Python ;
- compatible avec une base locale SQLite ;
- capable d’imprimer sur imprimante thermique ;
- capable d’exporter et de restaurer toutes ses données ;
- livrable sous forme d’installateur Windows.

La stack technique retenue est volontairement classique et raisonnable. Le but n’est pas de sur-complexifier le projet, mais de construire un logiciel fiable, clair et évolutif.

---

## 3. Stack technique officielle

### 3.1 Langage principal

```txt
Python
```

Python est utilisé pour :

- la logique métier ;
- l’interface desktop ;
- la gestion de la base SQLite ;
- la génération des tickets/factures ;
- la sauvegarde/restauration ;
- le packaging applicatif ;
- les tests automatisés.

Python doit rester le langage central du projet.

---

### 3.2 Interface graphique

```txt
PySide6
```

PySide6 est retenu pour l’interface desktop.

Il est préféré à Tkinter parce qu’il permet :

- une interface plus moderne ;
- des tableaux plus puissants ;
- une meilleure séparation des composants ;
- une meilleure apparence desktop ;
- une meilleure compatibilité avec une application professionnelle ;
- une personnalisation visuelle via QSS.

L’interface doit rester claire, simple et adaptée à des utilisateurs non techniques.

---

### 3.3 Base de données

```txt
SQLite
```

SQLite est retenu comme base de données locale.

Raisons :

- pas besoin de serveur ;
- installation simple ;
- très adapté à une application desktop locale ;
- bon choix pour une pharmacie unique ;
- compatible avec l’approche offline-first ;
- facile à sauvegarder et restaurer.

La base SQLite doit être stockée dans le dossier de données utilisateur, pas dans le dossier d’installation de l’application.

---

### 3.4 ORM

```txt
SQLAlchemy
```

SQLAlchemy est retenu pour organiser l’accès aux données.

Il permet :

- de structurer les modèles ;
- d’éviter de disperser des requêtes SQL partout ;
- de faciliter les tests ;
- de clarifier les relations entre entités ;
- de séparer la logique métier de la persistance.

Le SQL brut reste autorisé uniquement dans certains cas justifiés :

- vues SQLite ;
- rapports ;
- requêtes analytiques ;
- opérations très spécifiques ;
- optimisation nécessaire.

---

### 3.5 Migrations

```txt
Alembic
```

Alembic est utilisé pour gérer les évolutions du schéma SQLite.

Même si SQLite est simple, il faut éviter de modifier manuellement la base du client.

Toute modification structurelle importante doit passer par une migration :

- ajout de colonne ;
- ajout de table ;
- ajout d’index ;
- modification d’une contrainte lorsque possible ;
- ajout de données initiales techniques.

---

### 3.6 Sécurité des mots de passe

```txt
passlib[bcrypt]
```

Les mots de passe ne doivent jamais être stockés en clair.

À hasher :

- mot de passe utilisateur ;
- code de récupération du gérant.

À ne jamais stocker en clair :

- mot de passe ;
- code de récupération ;
- secret sensible.

---

### 3.7 Impression thermique

Bibliothèques retenues :

```txt
pywin32
python-escpos
```

Rôle :

- détecter les imprimantes Windows ;
- envoyer les tickets à l’imprimante thermique ;
- gérer l’impression directe ;
- supporter les tickets 58 mm et 80 mm ;
- permettre la réimpression.

L’impression quotidienne ne doit pas dépendre d’un PDF ouvert manuellement.

Flux attendu :

```txt
Vente validée
→ ticket généré
→ impression directe
→ journalisation
```

---

### 3.8 Génération de documents PDF

```txt
ReportLab
```

ReportLab peut être utilisé pour générer une version PDF d’une facture ou d’un reçu pour :

- archivage ;
- export ;
- réimpression éventuelle ;
- conservation documentaire.

Cependant, pour l’usage quotidien en caisse, l’impression thermique directe est prioritaire.

---

### 3.9 Export Excel

```txt
openpyxl
```

openpyxl est utilisé pour exporter :

- liste des produits ;
- stock ;
- ventes ;
- rapports journaliers ;
- rapports mensuels ;
- rapports par vendeur.

Les exports Excel sont utiles pour le gérant, mais ils ne remplacent pas les rapports internes de l’application.

---

### 3.10 Tests

```txt
pytest
```

pytest est utilisé pour tester :

- les services métier ;
- la logique de vente ;
- la logique de stock ;
- les permissions ;
- le backup/restauration ;
- la génération des numéros de vente ;
- les cas d’erreurs.

Les tests d’interface complète peuvent être limités au départ, mais les règles métier critiques doivent être testées.

---

### 3.11 Packaging Windows

```txt
PyInstaller
Inno Setup
```

PyInstaller sert à produire l’exécutable.

Inno Setup sert à produire l’installateur final.

Le client ne doit pas recevoir le code source.

Le livrable client doit être :

```txt
SALMOSPHARM_Setup.exe
```

---

## 4. Technologies interdites ou non retenues en version 1.0

Sauf décision explicite ultérieure, ne pas utiliser :

```txt
Django
FastAPI
Flask
PostgreSQL
MySQL
MongoDB
Electron
Tauri
React
Node.js
API web obligatoire
Serveur distant obligatoire
Cloud obligatoire
```

Ces technologies ne sont pas mauvaises, mais elles ne correspondent pas au choix actuel de l’implémentation.

SALMOSPHARM 133 version 1.0 doit rester une application desktop Python locale.

---

## 5. Architecture générale du projet

Structure recommandée :

```txt
salmospharm/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── paths.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   └── exceptions.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   ├── models.py
│   │   ├── init_db.py
│   │   ├── seed.py
│   │   ├── schema.sql
│   │   └── migrations/
│   │
│   ├── repositories/
│   │   ├── utilisateur_repository.py
│   │   ├── categorie_repository.py
│   │   ├── produit_repository.py
│   │   ├── lot_produit_repository.py
│   │   ├── stock_repository.py
│   │   ├── vente_repository.py
│   │   ├── alerte_repository.py
│   │   ├── journal_repository.py
│   │   └── parametre_repository.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── recuperation_service.py
│   │   ├── utilisateur_service.py
│   │   ├── produit_service.py
│   │   ├── stock_service.py
│   │   ├── vente_service.py
│   │   ├── facture_service.py
│   │   ├── ticket_service.py
│   │   ├── impression_service.py
│   │   ├── rapport_service.py
│   │   ├── alerte_service.py
│   │   ├── backup_service.py
│   │   └── journal_service.py
│   │
│   ├── ui/
│   │   ├── login/
│   │   ├── first_run/
│   │   ├── layouts/
│   │   ├── components/
│   │   ├── gerant/
│   │   └── vendeur/
│   │
│   ├── assets/
│   │   ├── logo.png
│   │   ├── logo.ico
│   │   ├── styles.qss
│   │   └── fonts/
│   │
│   └── utils/
│       ├── dates.py
│       ├── money.py
│       ├── validators.py
│       ├── formatters.py
│       └── file_utils.py
│
├── docs/
│   ├── 01_CONTEXTE_ET_OBJECTIFS.md
│   ├── 02_ARCHITECTURE_ET_STACK.md
│   ├── 03_REGLES_METIER_ET_SECURITE.md
│   ├── 04_BASE_DE_DONNEES_SQLITE.md
│   └── 05_MODULES_UI_LIVRAISON.md
│
├── tests/
│   ├── test_auth_service.py
│   ├── test_permissions.py
│   ├── test_stock_service.py
│   ├── test_vente_service.py
│   ├── test_backup_service.py
│   └── test_ticket_service.py
│
├── installer/
│   └── salmospharm.iss
│
├── requirements.txt
├── build.bat
├── README.md
└── pyproject.toml
```

Cette structure peut évoluer légèrement, mais la séparation des responsabilités doit rester respectée.

---

## 6. Rôle des dossiers principaux

### 6.1 `app/`

Contient le code source principal de l’application.

Tout code applicatif doit être placé dans ce dossier.

---

### 6.2 `app/main.py`

Point d’entrée de l’application.

Responsabilités :

- initialiser l’application PySide6 ;
- charger la configuration ;
- vérifier les chemins nécessaires ;
- initialiser la base si nécessaire ;
- lancer l’écran de premier démarrage ou l’écran de connexion ;
- appliquer le thème visuel ;
- gérer les erreurs critiques au démarrage.

`main.py` ne doit pas contenir de logique métier lourde.

---

### 6.3 `app/core/`

Contient les éléments transversaux.

#### `config.py`

Gère la configuration générale :

- nom de l’application ;
- version ;
- environnement ;
- paramètres techniques ;
- constantes globales.

#### `constants.py`

Contient les constantes métier et techniques :

```txt
ROLES
STATUTS
TYPES_MOUVEMENT_STOCK
TYPES_ALERTES
ACTIONS_JOURNAL
LARGEURS_TICKET
```

Aucune constante métier importante ne doit être dupliquée dans plusieurs fichiers.

#### `paths.py`

Gère les chemins locaux :

- chemin des assets embarqués ;
- chemin du dossier AppData ;
- chemin de la base SQLite ;
- chemin des sauvegardes ;
- chemin des logs ;
- chemin des factures archivées.

#### `security.py`

Gère :

- hash des mots de passe ;
- vérification des mots de passe ;
- génération du code de récupération ;
- hash du code de récupération ;
- validation du code de récupération.

#### `permissions.py`

Centralise les permissions par rôle.

L’interface peut masquer les boutons, mais la couche service doit aussi vérifier les permissions.

#### `exceptions.py`

Contient les exceptions applicatives propres :

```txt
PermissionRefuseeError
StockInsuffisantError
ProduitExpireError
UtilisateurInactifError
BackupInvalideError
ImprimanteIndisponibleError
ValidationError
```

L’objectif est d’éviter d’afficher des erreurs techniques brutes à l’utilisateur.

---

### 6.4 `app/database/`

Contient tout ce qui concerne la base de données.

#### `connection.py`

Responsabilités :

- créer la connexion SQLAlchemy ;
- activer `PRAGMA foreign_keys = ON` ;
- configurer la session ;
- fournir une session aux repositories/services.

Règle obligatoire :

```txt
PRAGMA foreign_keys = ON doit être activé à chaque connexion SQLite.
```

#### `models.py`

Contient les modèles SQLAlchemy.

Les modèles doivent correspondre aux tables françaises retenues :

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

Ne pas créer de modèle pour :

```txt
modes_paiement
factures
rapports
statistiques_dashboard
```

#### `init_db.py`

Responsabilités :

- vérifier si la base existe ;
- créer les tables au premier lancement ;
- lancer les migrations si nécessaire ;
- insérer les données initiales obligatoires.

#### `seed.py`

Contient les données initiales :

- catégories de base ;
- paramètres initiaux ;
- éventuellement valeurs par défaut nécessaires à l’application.

Le compte gérant ne doit pas être créé automatiquement avec un identifiant par défaut. Il est créé au premier lancement via l’écran dédié.

#### `schema.sql`

Peut contenir le schéma SQL initial ou les vues SQL.

Il peut être utilisé pour :

- créer les vues ;
- documenter la structure ;
- initialiser certaines parties spécifiques.

---

### 6.5 `app/repositories/`

Les repositories sont responsables de l’accès direct à la base.

Ils ne doivent pas contenir de logique métier complexe.

Exemples de responsabilités :

```txt
chercher un produit par ID
lister les produits actifs
récupérer les lots disponibles
insérer une vente
insérer une ligne de vente
récupérer les ventes d’un vendeur
```

Ils peuvent contenir des requêtes SQLAlchemy ou du SQL brut justifié.

Règle :

```txt
Les repositories manipulent les données.
Les services décident quoi faire avec ces données.
```

---

### 6.6 `app/services/`

Les services contiennent la logique métier.

C’est la couche la plus importante.

Exemples :

- vérifier qu’un vendeur peut vendre ;
- vérifier qu’un produit est actif ;
- vérifier le stock disponible ;
- appliquer FEFO ;
- bloquer les lots expirés ;
- créer une vente définitive ;
- générer le ticket ;
- journaliser une action ;
- exporter les données ;
- importer une sauvegarde.

Règle absolue :

```txt
La logique métier ne doit pas être codée directement dans les écrans PySide6.
```

L’interface appelle les services.

Les services appellent les repositories.

---

### 6.7 `app/ui/`

Contient l’interface utilisateur.

Organisation :

```txt
ui/
├── login/
├── first_run/
├── layouts/
├── components/
├── gerant/
└── vendeur/
```

#### `login/`

Écran de connexion et éventuels écrans liés à l’authentification.

#### `first_run/`

Écran de création du compte gérant au premier lancement.

#### `layouts/`

Layouts globaux :

- layout gérant ;
- layout vendeur ;
- sidebar ;
- topbar ;
- footer éventuel.

#### `components/`

Composants réutilisables :

```txt
Button
Input
SearchInput
DataTable
StatCard
BadgeStatus
ConfirmDialog
TicketPreview
DateFilter
EmptyState
ErrorBox
```

#### `gerant/`

Écrans réservés au gérant.

#### `vendeur/`

Écrans réservés au vendeur.

Règle :

```txt
Un écran vendeur ne doit jamais exposer une action réservée au gérant.
```

---

### 6.8 `app/assets/`

Contient les ressources embarquées :

- logo ;
- icône `.ico` ;
- fichier QSS ;
- éventuelles polices ;
- images statiques.

Ces fichiers doivent être inclus dans PyInstaller via `--add-data`.

---

### 6.9 `app/utils/`

Contient les fonctions utilitaires non métier.

Exemples :

- formatage des dates ;
- formatage des montants CDF ;
- validations simples ;
- manipulation de fichiers ;
- helpers de chaînes de caractères.

Attention : `utils/` ne doit pas devenir un dossier fourre-tout contenant de la logique métier.

---

### 6.10 `tests/`

Contient les tests automatisés.

Les tests prioritaires concernent :

- authentification ;
- permissions ;
- ventes ;
- stock ;
- FEFO ;
- lots expirés ;
- sauvegarde/restauration ;
- impression/ticket ;
- journalisation.

---

### 6.11 `installer/`

Contient les fichiers nécessaires à la création de l’installateur Windows.

Exemple :

```txt
installer/salmospharm.iss
```

---

## 7. Architecture en couches

L’application doit suivre cette logique :

```txt
UI PySide6
   ↓
Services métier
   ↓
Repositories
   ↓
SQLAlchemy / SQLite
```

La communication inverse ne doit pas exister.

Interdit :

```txt
Repository qui appelle l’UI
Service qui dépend d’un widget PySide6
Base de données modifiée directement depuis un bouton
Logique FEFO codée dans un écran
```

Autorisé :

```txt
Un bouton appelle un service.
Le service applique les règles.
Le service appelle les repositories.
Le repository écrit ou lit la base.
Le service retourne un résultat clair à l’UI.
```

---

## 8. Exemple de flux technique : validation d’une vente

Flux attendu :

```txt
Écran Nouvelle vente
→ vente_service.valider_vente()
→ vérification permission utilisateur
→ vérification panier
→ vérification produits actifs
→ vérification lots non expirés
→ application FEFO
→ création vente
→ création lignes_vente
→ décrément lots_produits
→ création mouvements_stock
→ génération alertes si nécessaire
→ journalisation VENTE_VALIDEE
→ génération ticket
→ impression si activée
→ retour résultat à l’interface
```

L’écran ne doit pas lui-même :

- calculer la sortie FEFO ;
- modifier les lots ;
- insérer directement dans `ventes` ;
- insérer directement dans `lignes_vente` ;
- décider des alertes ;
- écrire dans le journal.

---

## 9. Exemple de flux technique : export des données

Flux attendu :

```txt
Écran Paramètres
→ backup_service.exporter_donnees()
→ vérification rôle gérant
→ création copie cohérente SQLite
→ ajout assets/factures si présents
→ génération manifest.json
→ compression en .spharm
→ journalisation BACKUP_EXPORTE
→ message succès à l’utilisateur
```

L’interface ne doit pas faire elle-même la compression ni copier la base.

---

## 10. Gestion des chemins locaux

### 10.1 Principe général

L’application installée ne doit pas écrire dans son dossier d’installation.

Le dossier d’installation peut être :

```txt
C:\Program Files\SALMOSPHARM\
```

Les données utilisateur doivent être stockées dans :

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\
```

---

### 10.2 Structure du dossier de données utilisateur

```txt
AppData/Local/SALMOSPHARM/
│
├── data/
│   └── salmospharm.sqlite3
│
├── backups/
│   ├── auto_backup_2026-06-15.sqlite3
│   └── avant_import_2026-06-15_18-20.sqlite3
│
├── factures/
│   └── VTE-2026-000001.pdf
│
├── logs/
│   └── salmospharm.log
│
├── exports/
│   └── produits_2026-06-15.xlsx
│
└── assets/
    └── logo_personnalise.png
```

---

### 10.3 Chemins à centraliser

Tous les chemins doivent être centralisés dans :

```txt
app/core/paths.py
```

Aucun chemin absolu personnel ne doit être codé dans l’application.

Interdit :

```python
"C:/Users/Pistis/Desktop/logo.png"
"C:/Users/Admin/Documents/salmospharm.sqlite3"
```

Obligatoire :

```python
get_user_data_dir()
get_database_path()
get_backups_dir()
get_factures_dir()
get_logs_dir()
get_assets_dir()
```

---

## 11. Gestion des assets avec PyInstaller

Quand l’application est lancée en mode développement, les assets viennent du dossier projet.

Quand elle est packagée, les assets sont embarqués par PyInstaller.

Il faut gérer les deux cas.

Exemple conceptuel :

```python
import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parents[1]

    return base_path / relative_path
```

À utiliser pour :

- logo ;
- icône ;
- fichier QSS ;
- templates ;
- schema SQL embarqué.

---

## 12. Gestion de la configuration

La configuration applicative se divise en deux types.

### 12.1 Configuration technique

Stockée côté code ou fichier local technique :

```txt
nom application
version
chemins
mode debug
nom du fichier SQLite
```

### 12.2 Configuration métier

Stockée dans la table `parametres` :

```txt
nom pharmacie
téléphone
adresse
chemin logo
devise CDF
seuil expiration jours
nom imprimante
largeur ticket
impression automatique
sauvegarde automatique
fréquence sauvegarde
```

La devise est fixe :

```txt
CDF uniquement
```

Le mode de paiement est fixe :

```txt
Espèces uniquement
```

Ces deux éléments ne doivent pas être transformés en choix configurables.

---

## 13. Conventions de nommage

### 13.1 Langue

Le projet utilise principalement le français pour :

- tables ;
- modules métier ;
- services ;
- repositories ;
- messages utilisateur ;
- documentation.

Les noms techniques Python peuvent rester simples et cohérents.

Exemples :

```txt
vente_service.py
stock_service.py
produit_repository.py
journal_service.py
```

---

### 13.2 Tables SQLite

Les tables doivent rester en français :

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

Ne pas mélanger avec des noms anglais comme :

```txt
users
products
sales
invoices
payments
```

---

### 13.3 Classes Python

Les classes peuvent utiliser PascalCase.

Exemples :

```python
Utilisateur
Produit
LotProduit
Vente
LigneVente
Alerte
JournalActivite
Parametre
```

---

### 13.4 Fonctions Python

Les fonctions utilisent `snake_case`.

Exemples :

```python
creer_vente()
rechercher_produit()
verifier_stock_disponible()
generer_numero_vente()
exporter_donnees()
```

---

### 13.5 Constantes

Les constantes utilisent `UPPER_SNAKE_CASE`.

Exemples :

```python
ROLE_GERANT = "GERANT"
ROLE_VENDEUR = "VENDEUR"
DEVISE_UNIQUE = "CDF"
MODE_PAIEMENT_UNIQUE = "ESPECES"
```

---

## 14. Gestion des erreurs

L’application doit afficher des erreurs lisibles.

Exemples de messages acceptables :

```txt
Stock insuffisant pour ce produit.
Ce produit est expiré et ne peut pas être vendu.
Cette action est réservée au gérant.
Impossible de se connecter : identifiant ou mot de passe incorrect.
L’imprimante configurée est indisponible.
Le fichier de sauvegarde est invalide.
```

Messages interdits côté utilisateur :

```txt
sqlite3.OperationalError
NoneType has no attribute
Traceback
Foreign key constraint failed
PermissionError: [WinError 5]
```

Les erreurs techniques peuvent être journalisées dans les logs, mais pas affichées brutalement.

---

## 15. Logging technique

En plus de `journaux_activite`, l’application peut avoir un fichier log technique.

Différence :

```txt
journaux_activite = historique métier visible par le gérant
logs techniques = erreurs internes pour diagnostic développeur
```

Emplacement recommandé :

```txt
AppData/Local/SALMOSPHARM/logs/salmospharm.log
```

À journaliser techniquement :

- erreurs d’impression ;
- erreurs SQLite ;
- erreurs d’import/export ;
- exceptions non prévues ;
- problèmes de fichiers ;
- erreurs de démarrage.

---

## 16. Gestion des transactions SQLite

Les opérations critiques doivent être atomiques.

Exemple : validation d’une vente.

Toutes les actions suivantes doivent réussir ensemble :

- création vente ;
- création lignes ;
- diminution stock ;
- création mouvements stock ;
- création alertes ;
- journalisation.

Si une étape échoue, tout doit être annulé.

Règle :

```txt
Une vente ne doit jamais être partiellement enregistrée.
```

Utiliser les transactions SQLAlchemy pour les opérations critiques.

---

## 17. Gestion du premier lancement

Au premier lancement, l’application doit :

```txt
1. Créer les dossiers locaux nécessaires.
2. Créer ou initialiser la base SQLite si elle n’existe pas.
3. Vérifier s’il existe au moins un utilisateur gérant.
4. Si aucun gérant n’existe, afficher l’écran de création du compte gérant.
5. Générer un code de récupération.
6. Afficher le code une seule fois au gérant.
7. Demander au gérant de conserver ou imprimer ce code.
8. Rediriger ensuite vers l’écran de connexion.
```

Interdit :

```txt
Créer automatiquement admin/admin.
Créer un compte gérant avec un mot de passe par défaut.
Stocker le code de récupération en clair.
```

---

## 18. Gestion des sessions utilisateur

Pour la version 1.0, il n’est pas obligatoire de créer une table `sessions_utilisateur`.

La session active peut être gérée en mémoire pendant l’exécution de l’application.

À conserver en mémoire :

```txt
utilisateur connecté
rôle
permissions
heure de connexion
```

À journaliser :

```txt
CONNEXION_REUSSIE
CONNEXION_ECHOUEE
DECONNEXION si nécessaire
```

---

## 19. Packaging avec PyInstaller

### 19.1 Mode recommandé

Utiliser :

```txt
--onedir
```

`--onedir` est préféré à `--onefile` parce que :

- PySide6 a beaucoup de dépendances ;
- les assets sont plus simples à gérer ;
- les problèmes d’exécution sont plus faciles à diagnostiquer ;
- le build est souvent plus stable.

---

### 19.2 Exemple de commande

```bat
pyinstaller app/main.py ^
  --name SALMOSPHARM ^
  --windowed ^
  --onedir ^
  --icon app/assets/logo.ico ^
  --add-data "app/assets;assets" ^
  --add-data "app/database/schema.sql;database"
```

Résultat attendu :

```txt
dist/SALMOSPHARM/SALMOSPHARM.exe
```

---

### 19.3 Fichiers à inclure dans le build

À inclure :

```txt
logo.png
logo.ico
styles.qss
schema.sql si utilisé
templates de tickets/factures si utilisés
polices si utilisées
```

À ne pas inclure comme base de production écrasable :

```txt
salmospharm.sqlite3 rempli avec les données client
```

La base du client doit être créée ou stockée dans AppData.

---

## 20. Installateur Windows avec Inno Setup

Le client doit recevoir un installateur :

```txt
SALMOSPHARM_Setup.exe
```

L’installateur doit :

- installer l’application dans `Program Files` ;
- créer un raccourci bureau ;
- créer une entrée dans le menu démarrer ;
- permettre le lancement après installation ;
- ne pas écraser les données utilisateur existantes.

Les données utilisateur restent dans :

```txt
AppData/Local/SALMOSPHARM
```

---

## 21. Dépendances recommandées dans `requirements.txt`

Exemple :

```txt
PySide6
SQLAlchemy
alembic
passlib[bcrypt]
pywin32
python-escpos
reportlab
openpyxl
pytest
pyinstaller
```

Les versions exactes pourront être figées au moment du développement pour garantir la stabilité.

Exemple après stabilisation :

```bash
pip freeze > requirements.txt
```

---

## 22. Fichier `build.bat`

Créer un fichier `build.bat` à la racine.

Rôle : automatiser la génération du build.

Exemple :

```bat
@echo off

echo Nettoyage des anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Création de l'exécutable SALMOSPHARM...
pyinstaller app/main.py ^
  --name SALMOSPHARM ^
  --windowed ^
  --onedir ^
  --icon app/assets/logo.ico ^
  --add-data "app/assets;assets" ^
  --add-data "app/database/schema.sql;database"

echo Build terminé.
pause
```

Ce script peut être amélioré plus tard.

---

## 23. Environnements recommandés

### 23.1 Développement

```txt
Windows 10 ou Windows 11
Python 3.11 ou 3.12
Virtualenv
SQLite local
VS Code / Cursor / Codex
```

### 23.2 Client

```txt
Windows 10 ou Windows 11
Aucune installation Python requise
Imprimante thermique installée dans Windows
Droits suffisants pour installer l’application
```

---

## 24. Règles pour Codex ou LLM pendant l’implémentation

Lorsqu’un LLM travaille sur le projet, il doit respecter ces règles :

```txt
1. Ne pas changer la stack validée sans demande explicite.
2. Ne pas transformer l’application en application web.
3. Ne pas ajouter de serveur obligatoire.
4. Ne pas ajouter de paiement mobile ou carte bancaire.
5. Ne pas créer de table modes_paiement.
6. Ne pas créer de table factures.
7. Ne pas créer de possibilité d’annuler une vente.
8. Ne pas coder la logique métier directement dans les écrans.
9. Toujours passer par les services pour les règles métier.
10. Toujours passer par les repositories pour l’accès base.
11. Toujours stocker les montants CDF en INTEGER.
12. Toujours vérifier les permissions côté service.
13. Toujours journaliser les actions sensibles.
14. Toujours gérer les erreurs avec des messages lisibles.
15. Toujours respecter les noms de tables en français.
```

---

## 25. Ordre recommandé d’implémentation

Ordre logique :

```txt
1. Structure du projet
2. Gestion des chemins AppData
3. Connexion SQLite
4. Modèles SQLAlchemy
5. Initialisation base et données de départ
6. Création compte gérant au premier lancement
7. Authentification
8. Permissions
9. Layout principal PySide6
10. Gestion produits
11. Gestion lots/stock
12. Vente avec FEFO
13. Ticket thermique
14. Historique des ventes
15. Rapports
16. Alertes
17. Backup/restauration
18. Packaging Windows
19. Tests finaux
```

Ne pas commencer par les écrans complexes avant d’avoir stabilisé :

- la base ;
- l’authentification ;
- les permissions ;
- les services métier.

---

## 26. Critères de validation technique

L’architecture est considérée correcte si :

```txt
- l’application démarre sans serveur ;
- la base SQLite est créée automatiquement au bon endroit ;
- le compte gérant est créé au premier lancement ;
- les services contiennent la logique métier ;
- l’UI ne manipule pas directement la base ;
- les permissions sont vérifiées côté service ;
- une vente est enregistrée de manière atomique ;
- le stock est décrémenté correctement ;
- les lots expirés sont bloqués ;
- l’impression thermique peut être configurée ;
- les données peuvent être exportées/restaurées ;
- l’application peut être packagée en installateur Windows.
```

---

## 27. Résumé final

La base technique officielle de SALMOSPHARM 133 est :

```txt
Python
PySide6
SQLite
SQLAlchemy
Alembic
passlib/bcrypt
pywin32
python-escpos
ReportLab
openpyxl
pytest
PyInstaller
Inno Setup
```

L’architecture officielle est :

```txt
UI → Services → Repositories → SQLite
```

Les données client doivent être stockées dans :

```txt
AppData/Local/SALMOSPHARM
```

Le client doit recevoir :

```txt
SALMOSPHARM_Setup.exe
```

Ce document doit rester la référence pour toute décision technique d’architecture pendant l’implémentation.
