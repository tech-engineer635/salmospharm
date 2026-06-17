# AGENTS.md — Instructions principales pour Codex

## Projet

Nom du projet : **SALMOSPHARM 133**

Type : application desktop locale de gestion de pharmacie.

Version cible : **1.0 — Offre 2 Professionnelle**

Stack officielle :

```txt
Python
PySide6
SQLite
SQLAlchemy
Alembic
passlib[bcrypt]
pywin32
python-escpos
ReportLab
openpyxl
pytest
PyInstaller
Inno Setup
```

L’application doit fonctionner localement sur Windows, sans dépendance obligatoire à Internet.

---

# 1. Rôle de ce fichier

Ce fichier indique à Codex comment travailler sur ce projet.

Avant de modifier ou générer du code, Codex doit lire et respecter les documents suivants :

```txt
docs/01_CONTEXTE_ET_OBJECTIFS.md
docs/02_ARCHITECTURE_ET_STACK.md
docs/03_REGLES_METIER_ET_SECURITE.md
docs/04_BASE_DE_DONNEES_SQLITE.md
docs/05_MODULES_UI_LIVRAISON.md
CODEX_PHASES.md
```

Ces documents sont prioritaires sur toute suggestion automatique.

Si une demande utilisateur contredit les documents du projet, Codex doit signaler clairement la contradiction avant de coder.

---


# 2. Règles absolues à ne jamais violer

Codex ne doit jamais ajouter, proposer ou implémenter :

```txt
- paiement mobile ;
- carte bancaire ;
- paiement mixte ;
- multi-devise ;
- USD ;
- EUR ;
- annulation de vente ;
- suppression de vente validée ;
- modification de vente validée ;
- table modes_paiement ;
- table paiements ;
- table factures ;
- table rapports ;
- synchronisation cloud obligatoire ;
- application web ;
- API distante obligatoire ;
- serveur obligatoire ;
- multi-pharmacie ;
- gestion fournisseur avancée ;
- crédit client ;
- retour produit ;
- intelligence artificielle ;
- compte admin/admin ;
- mot de passe stocké en clair ;
- code de récupération stocké en clair.
```

La version 1.0 est strictement :

```txt
Desktop Windows
Offline-first
SQLite locale
CDF uniquement
Espèces uniquement
Gérant / Vendeur
Vente définitive
FEFO obligatoire
Lots expirés interdits à la vente
Impression thermique
Backup/restauration locale
```

---

# 3. Architecture obligatoire

L’architecture à respecter est :

```txt
UI PySide6
↓
Services métier
↓
Repositories
↓
SQLAlchemy / SQLite
```

Règle obligatoire :

```txt
L’interface ne doit jamais modifier directement la base de données.
```

Un écran PySide6 peut :

```txt
- afficher des données ;
- recevoir une saisie utilisateur ;
- appeler un service ;
- afficher un message de succès ou d’erreur.
```

Un écran PySide6 ne doit pas :

```txt
- créer directement une session SQLAlchemy ;
- faire session.add(...) directement ;
- décrémenter le stock ;
- appliquer FEFO ;
- créer une vente directement ;
- créer une ligne de vente directement ;
- écrire dans journaux_activite directement ;
- décider des permissions métier.
```

La logique métier doit rester dans :

```txt
app/services/
```

L’accès base doit rester dans :

```txt
app/repositories/
```

---

# 4. Structure recommandée du projet

Codex doit respecter cette structure :

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
│   │   └── styles.qss
│   │
│   └── utils/
│       ├── dates.py
│       ├── money.py
│       ├── validators.py
│       ├── formatters.py
│       └── file_utils.py
│
├── docs/
├── tests/
├── installer/
├── requirements.txt
├── build.bat
├── README.md
├── AGENTS.md
└── CODEX_PHASES.md
```

Si un fichier existe déjà, Codex doit le modifier avec prudence, sans écraser inutilement le travail existant.

---

# 5. Tables SQLite officielles

Codex doit utiliser uniquement les tables principales suivantes pour la version 1.0 :

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

Ne jamais créer ces tables en version 1.0 :

```txt
modes_paiement
paiements
factures
rapports
statistiques_dashboard
sessions_utilisateur
clients
fournisseurs
commandes_fournisseurs
multi_pharmacies
```

Les noms de tables doivent rester en français.

---

# 6. Règles sur les montants

Tous les montants sont en CDF.

Les montants doivent être stockés en `INTEGER`.

Exemples :

```txt
1500 CDF -> 1500
25000 CDF -> 25000
```

Ne jamais utiliser `FLOAT` ou `REAL` pour les montants.

Ne jamais ajouter de conversion de devise.

---

# 7. Règles d’authentification

Codex doit respecter ces règles :

```txt
- aucun module métier accessible sans authentification ;
- premier lancement : création du compte gérant si aucun utilisateur n’existe ;
- aucun compte admin/admin ;
- mot de passe hashé avec passlib[bcrypt] ;
- code de récupération généré automatiquement ;
- code de récupération affiché une seule fois ;
- code de récupération stocké uniquement sous forme de hash ;
- après récupération, générer un nouveau code ;
- vendeur désactivé interdit de connexion ;
- connexion réussie ou échouée journalisée.
```

---

# 8. Règles de permissions

Rôles officiels :

```txt
GERANT
VENDEUR
```

Le gérant peut accéder à tout.

Le vendeur peut uniquement :

```txt
- se connecter ;
- voir son tableau de bord ;
- rechercher des produits ;
- consulter le stock vendable ;
- créer une vente ;
- imprimer le ticket de ses ventes ;
- réimprimer ses propres tickets ;
- consulter son historique personnel.
```

Le vendeur ne peut jamais :

```txt
- créer un vendeur ;
- modifier un utilisateur ;
- créer un produit ;
- modifier un produit ;
- modifier le stock ;
- faire une entrée de stock ;
- faire un ajustement de stock ;
- accéder aux paramètres ;
- exporter les données ;
- importer les données ;
- voir les rapports globaux ;
- consulter toutes les ventes ;
- consulter tout l’historique système.
```

Les permissions doivent être vérifiées dans les services, pas seulement dans l’interface.

---

# 9. Règles de stock et FEFO

Le stock disponible est calculé depuis `lots_produits`.

Un lot est vendable seulement si :

```txt
- le produit est actif ;
- la quantité du lot est supérieure à 0 ;
- le lot n’est pas expiré ;
- la date d’expiration est absente ou supérieure/égale à la date du jour.
```

FEFO est obligatoire :

```txt
First Expired, First Out
```

Lors d’une vente :

```txt
1. récupérer les lots disponibles du produit ;
2. exclure les lots expirés ;
3. exclure les lots à quantité 0 ;
4. trier par date d’expiration croissante ;
5. sortir d’abord le lot qui expire le plus tôt ;
6. répartir la sortie sur plusieurs lots si nécessaire ;
7. créer les lignes de vente ;
8. créer les mouvements de stock ;
9. décrémenter les bons lots.
```

Codex ne doit jamais laisser l’UI choisir manuellement le lot à sortir lors d’une vente standard.

---

# 10. Règles de vente

Une vente validée est définitive.

La fonction de validation de vente doit vérifier :

```txt
- utilisateur connecté ;
- utilisateur autorisé à vendre ;
- panier non vide ;
- produits actifs ;
- lots disponibles ;
- lots non expirés ;
- stock suffisant ;
- prix unitaires valides ;
- total cohérent ;
- montant reçu supérieur ou égal au total ;
- devise CDF ;
- paiement espèces.
```

La validation de vente doit être atomique.

Tout doit réussir ensemble :

```txt
- création vente ;
- création lignes_vente ;
- décrémentation lots ;
- création mouvements_stock ;
- création alertes si nécessaire ;
- journalisation VENTE_VALIDEE.
```

Si une étape échoue, rien ne doit rester en base.

Codex doit utiliser une transaction SQLAlchemy pour cela.

---

# 11. Tickets et impression

L’impression quotidienne doit être thermique.

Bibliothèques recommandées :

```txt
pywin32
python-escpos
```

Le ticket doit supporter :

```txt
58 mm
80 mm
```

Le ticket doit afficher :

```txt
- nom de la pharmacie ;
- téléphone si configuré ;
- adresse si configurée ;
- numéro de vente ;
- date et heure ;
- vendeur ;
- produits ;
- quantités ;
- prix unitaires ;
- sous-totaux ;
- total ;
- montant reçu ;
- monnaie rendue ;
- CDF ;
- paiement espèces ;
- message de remerciement.
```

Si l’impression échoue, la vente ne doit pas être annulée.

L’erreur doit être affichée proprement et journalisée.

---

# 12. Backup et restauration

L’export/import est réservé au gérant.

Extension officielle :

```txt
.spharm
```

Le fichier `.spharm` peut être une archive ZIP renommée contenant :

```txt
database/salmospharm.sqlite3
assets/
factures/
manifest.json
```

Règles obligatoires :

```txt
- utiliser l’API SQLite backup() pour copier la base ;
- ne pas copier brutalement la base pendant utilisation ;
- valider manifest.json avant import ;
- créer une sauvegarde de sécurité avant import ;
- remplacer les données seulement après validation ;
- journaliser BACKUP_EXPORTE et BACKUP_IMPORTE ;
- redémarrer l’application après import si nécessaire.
```

---

# 13. Gestion des erreurs

Codex doit créer des exceptions applicatives propres dans :

```txt
app/core/exceptions.py
```

Exemples :

```txt
PermissionRefuseeError
StockInsuffisantError
ProduitExpireError
UtilisateurInactifError
BackupInvalideError
ImprimanteIndisponibleError
ValidationError
```

L’interface ne doit jamais afficher :

```txt
Traceback
sqlite3.OperationalError
Foreign key constraint failed
NoneType has no attribute
PermissionError brut
```

Les messages utilisateur doivent être simples.

Exemples :

```txt
Stock insuffisant pour ce produit.
Ce produit est expiré et ne peut pas être vendu.
Vous n’avez pas l’autorisation d’effectuer cette action.
Impossible d’imprimer le ticket. Vérifiez l’imprimante.
Ce fichier de sauvegarde n’est pas valide.
```

---

# 14. Tests obligatoires

Codex doit ajouter ou mettre à jour des tests quand il modifie une logique métier.

Framework :

```txt
pytest
```

Tests prioritaires :

```txt
tests/test_auth_service.py
tests/test_permissions.py
tests/test_stock_service.py
tests/test_vente_service.py
tests/test_backup_service.py
tests/test_ticket_service.py
```

Cas à tester obligatoirement :

```txt
- création gérant ;
- mot de passe hashé ;
- code récupération hashé ;
- connexion gérant ;
- connexion vendeur ;
- vendeur désactivé refusé ;
- vendeur interdit d’accès aux paramètres ;
- création produit ;
- entrée stock ;
- lot expiré exclu ;
- FEFO respecté ;
- vente stock suffisant ;
- vente stock insuffisant refusée ;
- panier vide refusé ;
- montant reçu insuffisant refusé ;
- vente validée non annulable ;
- mouvements stock créés ;
- journal vente créé ;
- backup exporté ;
- backup invalide refusé.
```

---

# 15. Tests progressifs obligatoires

Codex doit respecter la stratégie :

```txt
Build early, test often
```

À chaque phase, le projet doit rester lançable.

Ne jamais casser volontairement le lancement de l’application.

Codex doit régulièrement vérifier ou proposer de vérifier :

```txt
python app/main.py
pytest
build.bat
dist/SALMOSPHARM/SALMOSPHARM.exe
```

Quand une phase touche au packaging, Codex doit vérifier :

```txt
- PyInstaller fonctionne ;
- l’exe se lance ;
- les assets sont inclus ;
- les données sont stockées dans AppData ;
- le client n’a pas besoin de Python.
```

---

# 16. Packaging

Le client doit recevoir :

```txt
SALMOSPHARM_Setup.exe
```

Codex doit préparer le build avec :

```txt
PyInstaller --onedir
Inno Setup
```

Le client ne doit pas recevoir :

```txt
- code source ;
- fichiers .py ;
- environnement virtuel ;
- requirements.txt seul ;
- base SQLite à placer manuellement.
```

Les données utilisateur doivent être dans :

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\
```

Pas dans :

```txt
C:\Program Files\SALMOSPHARM\
```

---

# 17. Méthode de travail demandée à Codex

Pour chaque demande de modification ou d’implémentation, Codex doit :

```txt
1. identifier la phase concernée dans CODEX_PHASES.md ;
2. lire les documents projet nécessaires ;
3. expliquer brièvement les fichiers qu’il va toucher ;
4. créer ou modifier uniquement les fichiers nécessaires ;
5. préserver l’architecture UI → Services → Repositories → SQLite ;
6. ajouter les tests pertinents si la logique métier change ;
7. donner les commandes à lancer ;
8. donner les tests manuels à faire ;
9. signaler clairement les limites ou points non terminés.
```

Codex ne doit pas :

```txt
- faire des changements massifs sans justification ;
- réorganiser tout le projet sans demande explicite ;
- supprimer des fichiers sans prévenir ;
- introduire une nouvelle stack ;
- modifier les règles métier validées ;
- ignorer les tests.
```

---

# 18. Quand Codex ne sait pas

Si Codex n’est pas sûr, il doit :

```txt
- ne pas inventer ;
- expliquer l’incertitude ;
- proposer une solution prudente ;
- demander validation humaine si la décision change le périmètre ;
- chercher dans les fichiers docs du projet avant de proposer une règle.
```

Pour une question de bibliothèque ou de syntaxe, Codex peut suggérer quoi rechercher.

Exemples :

```txt
Documentation officielle SQLAlchemy Session transaction
Documentation officielle PySide6 signal slot
Documentation officielle PyInstaller add-data Windows
Documentation python-escpos Windows printer
Documentation passlib bcrypt verify
```

---

# 19. Résumé opérationnel pour Codex

Toujours retenir :

```txt
SALMOSPHARM 133 est une application desktop locale.
La stack est Python + PySide6 + SQLite.
L’architecture est UI → Services → Repositories → SQLite.
Le paiement est espèces uniquement.
La devise est CDF uniquement.
Une vente validée est définitive.
FEFO est obligatoire.
Les lots expirés sont interdits à la vente.
Les permissions doivent être vérifiées côté service.
Les actions sensibles doivent être journalisées.
Les tests progressifs commencent dès la mini application.
Le client reçoit SALMOSPHARM_Setup.exe, pas le code source.
```
