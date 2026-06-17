# 05 — Modules, UI, impression, backup, tests et livraison

## Projet : SALMOSPHARM 133

**Type de projet :** Application desktop de gestion de pharmacie  
**Version cible :** 1.0  
**Offre retenue :** Offre 2 — Version professionnelle  
**Stack principale :** Python, PySide6, SQLite, SQLAlchemy  
**Livraison finale :** exécutable Windows avec installateur `SALMOSPHARM_Setup.exe`

---

# 1. Rôle de ce document

Ce fichier décrit les modules visibles de l’application, l’organisation de l’interface, les règles d’expérience utilisateur, le système d’impression thermique, le système de sauvegarde/restauration, les tests de validation et les exigences de livraison client.

Il complète les fichiers suivants :

- `01_CONTEXTE_ET_OBJECTIFS.md`
- `02_ARCHITECTURE_ET_STACK.md`
- `03_REGLES_METIER_ET_SECURITE.md`
- `04_BASE_DE_DONNEES_SQLITE.md`

Ce document doit être utilisé par tout développeur ou LLM/Codex pour implémenter les écrans et les fonctionnalités sans contredire les décisions validées.

---

# 2. Rappel des règles non négociables

Les règles suivantes doivent être respectées dans tous les modules :

1. L’application est une application desktop locale.
2. La base de données est SQLite.
3. L’application fonctionne offline-first.
4. La devise unique est le CDF.
5. Le paiement se fait uniquement en espèces.
6. Aucun mode de paiement alternatif ne doit apparaître.
7. Aucune vente validée ne peut être annulée.
8. Aucun lot expiré ne peut être vendu.
9. La sortie de stock doit suivre la règle FEFO.
10. Le vendeur n’a pas accès aux fonctions administratives.
11. Le gérant a accès complet au système.
12. Les actions sensibles doivent être journalisées.
13. Les données doivent pouvoir être exportées et restaurées via un fichier `.spharm`.
14. L’impression quotidienne se fait via imprimante thermique.
15. Le client reçoit un installateur Windows, pas le code source.

---

# 3. Modules fonctionnels de l’application

L’application est organisée autour de modules métiers. Chaque module doit avoir une responsabilité claire.

## 3.1 Module Authentification

### Rôle

Permettre l’accès sécurisé à l’application selon le rôle de l’utilisateur.

### Utilisateurs concernés

- Gérant
- Vendeur

### Écrans concernés

- Connexion
- Création du compte gérant au premier lancement
- Récupération du compte via code de récupération
- Changement de mot de passe si nécessaire

### Fonctionnalités

- Connexion par identifiant/email et mot de passe.
- Vérification du mot de passe hashé.
- Refus de connexion si compte désactivé.
- Redirection selon le rôle.
- Création du premier compte gérant si aucun utilisateur n’existe.
- Génération d’un code de récupération pour le gérant.
- Réinitialisation du mot de passe via code de récupération.

### Règles métier

- Le mot de passe ne doit jamais être stocké en clair.
- Le code de récupération ne doit jamais être stocké en clair.
- Le code de récupération doit être affiché une seule fois lors de sa génération.
- Après une récupération, un nouveau code doit être généré.
- Une connexion réussie ou échouée doit être journalisée.

### Erreurs utilisateur à prévoir

- Identifiant ou mot de passe incorrect.
- Compte désactivé.
- Code de récupération invalide.
- Mot de passe trop faible.
- Champs obligatoires manquants.

---

## 3.2 Module Tableau de bord gérant

### Rôle

Donner au gérant une vue globale sur l’état de la pharmacie.

### Utilisateur concerné

- Gérant uniquement

### Données affichées

- Total des ventes du jour.
- Nombre de transactions du jour.
- Produits en stock.
- Produits en stock faible.
- Produits/lots proches de l’expiration.
- Produits les plus vendus.
- Synthèse par vendeur.
- Activités récentes.
- Alertes critiques.

### Actions possibles

- Changer la période d’analyse.
- Consulter les alertes.
- Accéder aux ventes.
- Accéder aux rapports.
- Consulter les activités récentes.

### Règles métier

- Les montants doivent être affichés en CDF.
- Les statistiques du gérant couvrent toute la pharmacie.
- Les alertes critiques doivent être visibles sans recherche complexe.
- Le dashboard ne doit pas permettre d’action dangereuse directe sans confirmation.

---

## 3.3 Module Tableau de bord vendeur

### Rôle

Afficher au vendeur un résumé simple de son activité personnelle.

### Utilisateur concerné

- Vendeur uniquement

### Données affichées

- Ventes du jour du vendeur connecté.
- Nombre de transactions du vendeur connecté.
- Total encaissé en CDF.
- Articles vendus.
- Dernières ventes personnelles.

### Actions possibles

- Démarrer une nouvelle vente.
- Voir son historique.
- Rechercher un produit.
- Réimprimer une facture liée à ses propres ventes.

### Règles métier

- Le vendeur ne voit que ses propres ventes.
- Il ne voit pas les performances globales de la pharmacie.
- Il ne voit pas les ventes des autres vendeurs.
- Il ne doit pas accéder aux paramètres.

---

## 3.4 Module Produits

### Rôle

Gérer le catalogue des médicaments et produits disponibles dans la pharmacie.

### Utilisateur concerné

- Gérant uniquement

### Données principales

- Code produit ou code-barres.
- Nom du produit.
- Catégorie.
- Prix de vente en CDF.
- Stock minimum.
- Description.
- Statut actif/inactif.

### Actions possibles

- Ajouter un produit.
- Modifier un produit.
- Désactiver un produit.
- Rechercher un produit.
- Filtrer par catégorie.
- Exporter la liste des produits.

### Règles métier

- Un produit déjà vendu ne doit pas être supprimé physiquement.
- Il doit être désactivé pour préserver l’historique.
- Le prix est en CDF uniquement.
- Le stock disponible n’est pas stocké dans la table `produits`.
- Le stock disponible est calculé depuis les lots.

### Erreurs utilisateur à prévoir

- Produit sans nom.
- Prix négatif.
- Code-barres déjà utilisé.
- Catégorie invalide.
- Tentative de suppression d’un produit historique.

---

## 3.5 Module Stock

### Rôle

Gérer les entrées, ajustements et suivis de stock par lots.

### Utilisateur concerné

- Gérant uniquement

### Données principales

- Produit.
- Lot.
- Quantité disponible.
- Prix d’achat.
- Date d’expiration.
- Historique des mouvements.

### Actions possibles

- Ajouter une entrée de stock.
- Ajuster une quantité.
- Consulter les mouvements.
- Voir les ruptures.
- Voir les expirations proches.
- Exporter l’état du stock.

### Règles métier

- Chaque entrée de stock doit créer ou mettre à jour un lot.
- Chaque modification de stock doit créer un mouvement dans `mouvements_stock`.
- Les quantités ne peuvent jamais devenir négatives.
- Les lots expirés ne doivent pas être vendus.
- Les alertes de stock faible doivent être générées automatiquement ou recalculées.
- Les alertes d’expiration doivent respecter le seuil défini dans les paramètres.

### Types de mouvements retenus

- `ENTREE`
- `SORTIE`
- `AJUSTEMENT`
- `PERTE`
- `EXPIRATION`

### Note importante

Il n’y a pas de type `RETOUR_VENTE`, car les ventes validées ne peuvent pas être annulées.

---

## 3.6 Module Nouvelle vente

### Rôle

Permettre l’enregistrement rapide d’une vente.

### Utilisateurs concernés

- Gérant
- Vendeur

### Interface attendue

L’écran doit être simple et rapide :

- Champ de recherche produit.
- Liste ou cartes de produits disponibles.
- Panier de vente.
- Récapitulatif à droite.
- Total en CDF.
- Montant reçu.
- Monnaie à rendre.
- Bouton `Encaisser`.
- Bouton `Imprimer ticket` après validation.

### Règles métier

- Paiement uniquement en espèces.
- Devise CDF uniquement.
- Aucun choix de mode de paiement.
- Un panier vide ne peut pas être validé.
- Une quantité supérieure au stock disponible est interdite.
- Un lot expiré est interdit à la vente.
- Le stock doit sortir selon FEFO.
- Une vente validée est définitive.
- Une vente validée diminue automatiquement le stock.
- Une vente validée crée des lignes de vente.
- Une vente validée crée les mouvements de stock correspondants.
- Une vente validée génère un numéro de vente unique.
- Une vente validée peut produire un ticket thermique.

### Format du numéro de vente

Format recommandé :

```txt
VTE-YYYY-000001
```

Exemple :

```txt
VTE-2026-000001
```

### Erreurs utilisateur à prévoir

- Panier vide.
- Montant reçu inférieur au total.
- Produit en rupture.
- Lot expiré.
- Stock insuffisant.
- Échec d’impression.
- Base de données indisponible.

---

## 3.7 Module Historique des ventes

### Rôle

Permettre la consultation des ventes validées.

### Utilisateurs concernés

- Gérant
- Vendeur

### Accès gérant

Le gérant peut voir toutes les ventes.

### Accès vendeur

Le vendeur ne peut voir que ses propres ventes.

### Actions possibles

- Rechercher une vente.
- Filtrer par date.
- Voir le détail d’une vente.
- Réimprimer le ticket si autorisé.

### Règles métier

- Les ventes ne peuvent pas être modifiées.
- Les ventes ne peuvent pas être annulées.
- Les ventes ne peuvent pas être supprimées.
- La réimpression doit être journalisée.

---

## 3.8 Module Factures / Tickets

### Rôle

Afficher, imprimer et réimprimer les reçus de vente.

### Utilisateurs concernés

- Gérant
- Vendeur

### Règles d’accès

- Le vendeur peut réimprimer uniquement les tickets de ses propres ventes.
- Le gérant peut réimprimer tous les tickets.

### Règles métier

- Le ticket affiche uniquement des montants en CDF.
- Le ticket indique que le paiement est en espèces.
- Le ticket contient le nom de la pharmacie.
- Le ticket contient le numéro de vente.
- Le ticket contient la date et l’heure.
- Le ticket contient le vendeur.
- Le ticket contient la liste des produits.
- Le ticket contient le total, le montant reçu et la monnaie rendue.

### Note sur les factures PDF

Le PDF n’est pas le format principal pour l’impression quotidienne. L’impression principale est thermique. Le PDF peut être utilisé uniquement pour :

- archivage ;
- export ;
- consultation ;
- réimpression alternative.

---

## 3.9 Module Rapports

### Rôle

Permettre au gérant d’analyser les ventes et performances.

### Utilisateur concerné

- Gérant uniquement

### Rapports attendus

- Rapport journalier.
- Rapport mensuel.
- Rapport par vendeur.
- Produits les plus vendus.
- Total des ventes sur période.

### Règles métier

- Les rapports sont calculés par requêtes ou vues.
- Il ne faut pas créer de table `rapports`.
- Les montants sont en CDF.
- Les ventes concernées sont uniquement les ventes validées.

---

## 3.10 Module Gestion des vendeurs

### Rôle

Permettre au gérant de créer et gérer les comptes vendeurs.

### Utilisateur concerné

- Gérant uniquement

### Actions possibles

- Créer un vendeur.
- Modifier un vendeur.
- Désactiver un vendeur.
- Réactiver un vendeur.
- Voir ses performances.

### Règles métier

- Seul le gérant peut créer un vendeur.
- Un vendeur désactivé ne peut pas se connecter.
- Un vendeur ne doit pas être supprimé si son compte est lié à des ventes.
- La désactivation préserve l’historique.
- La création, modification ou désactivation d’un vendeur doit être journalisée.

---

## 3.11 Module Alertes

### Rôle

Centraliser les alertes importantes liées au stock et aux expirations.

### Utilisateur concerné

- Gérant principalement

### Types d’alertes

- `STOCK_FAIBLE`
- `EXPIRATION_PROCHE`
- `PRODUIT_EXPIRE`

### Actions possibles

- Consulter les alertes.
- Marquer comme lue.
- Filtrer les alertes.
- Accéder au produit ou lot concerné.

### Règles métier

- Une alerte de stock faible est déclenchée quand le stock disponible est inférieur ou égal au seuil minimum.
- Une alerte d’expiration proche est déclenchée selon le seuil défini dans les paramètres.
- Un produit ou lot expiré ne peut pas être vendu.
- Les alertes critiques doivent apparaître sur le dashboard gérant.

---

## 3.12 Module Historique des actions

### Rôle

Tracer les actions sensibles effectuées dans l’application.

### Utilisateur concerné

- Gérant uniquement

### Actions à journaliser

- `CONNEXION_REUSSIE`
- `CONNEXION_ECHOUEE`
- `COMPTE_GERANT_CREE`
- `CODE_RECUPERATION_GENERE`
- `MOT_DE_PASSE_REINITIALISE`
- `UTILISATEUR_CREE`
- `UTILISATEUR_MODIFIE`
- `UTILISATEUR_DESACTIVE`
- `PRODUIT_CREE`
- `PRODUIT_MODIFIE`
- `STOCK_ENTREE`
- `STOCK_AJUSTE`
- `VENTE_VALIDEE`
- `FACTURE_IMPRIMEE`
- `FACTURE_REIMPRIMEE`
- `BACKUP_EXPORTE`
- `BACKUP_IMPORTE`
- `SAUVEGARDE_AUTO_CREEE`
- `PARAMETRES_MODIFIES`

### Règles métier

- L’historique ne doit pas être modifiable par les vendeurs.
- L’historique ne doit pas être supprimé depuis l’interface standard.
- Les actions critiques doivent contenir l’utilisateur, le module, l’action et la date.

---

## 3.13 Module Paramètres

### Rôle

Permettre au gérant de configurer les informations essentielles de l’application.

### Utilisateur concerné

- Gérant uniquement

### Sections recommandées

1. Informations de la pharmacie
2. Impression
3. Sauvegarde et restauration
4. Sécurité

### Paramètres pharmacie

- Nom de la pharmacie.
- Téléphone.
- Adresse.
- Logo.

### Paramètres impression

- Nom de l’imprimante.
- Largeur du ticket : 58 mm ou 80 mm.
- Impression automatique après vente : oui/non.

### Paramètres sauvegarde

- Sauvegarde automatique : oui/non.
- Fréquence de sauvegarde.
- Dernière sauvegarde.
- Export manuel.
- Import manuel.

### Paramètres sécurité

- Changer le mot de passe.
- Régénérer le code de récupération.

### Règles métier

- Le vendeur ne peut pas accéder aux paramètres.
- Le mode de paiement n’est pas configurable.
- La devise n’est pas configurable.
- Les paramètres sensibles doivent être journalisés.

---

# 4. Organisation générale de l’interface

## 4.1 Direction artistique

L’interface doit être :

- moderne ;
- claire ;
- médicale ;
- professionnelle ;
- lisible ;
- adaptée aux utilisateurs non techniques.

Elle doit s’inspirer d’un tableau de bord SaaS, mais rester simple et utilisable en contexte réel de pharmacie.

## 4.2 Couleurs principales

- Vert principal : actions positives, boutons principaux, badges `En stock`.
- Bleu nuit : titres, footer, éléments institutionnels.
- Gris clair : fonds secondaires, bordures, séparateurs.
- Orange : avertissements, stock faible, expiration proche.
- Rouge : erreurs, ruptures, produits expirés, actions dangereuses.
- Blanc : cartes, formulaires, tableaux.

## 4.3 Typographie

Police recommandée :

- Inter ;
- Segoe UI ;
- Roboto.

Priorité : lisibilité.

## 4.4 Layout général

Chaque écran principal doit respecter cette structure :

```txt
Fenêtre principale
├── Sidebar gauche
├── Topbar
├── Zone de contenu
└── Footer discret ou information version
```

## 4.5 Sidebar gérant

Ordre recommandé :

1. Tableau de bord
2. Produits
3. Stock
4. Ventes
5. Factures
6. Rapports
7. Vendeurs
8. Historique
9. Alertes
10. Paramètres
11. Déconnexion

## 4.6 Sidebar vendeur

Ordre recommandé :

1. Tableau de bord
2. Nouvelle vente
3. Historique des ventes
4. Recherche produit
5. Factures
6. Déconnexion

## 4.7 Composants UI réutilisables

Les composants suivants doivent être factorisés :

- `Sidebar`
- `Topbar`
- `StatCard`
- `DataTable`
- `BadgeStatus`
- `SearchInput`
- `DateFilter`
- `ConfirmDialog`
- `TicketPreview`
- `EmptyState`
- `ErrorMessage`
- `LoadingOverlay`

## 4.8 Règles UX

- Les actions principales doivent être visibles.
- Les formulaires doivent être simples.
- Les erreurs doivent être compréhensibles.
- Les tableaux doivent être filtrables et paginés.
- Les actions sensibles doivent demander confirmation.
- Aucun écran ne doit afficher un choix de mode de paiement.
- L’état de stock doit être visible avant la vente.
- Les produits expirés ou indisponibles doivent être clairement signalés.

---

# 5. Impression thermique

## 5.1 Principe

L’impression quotidienne des tickets doit se faire directement vers une imprimante thermique compatible ESC/POS.

Le flux attendu :

```txt
Vente validée
↓
Génération du ticket texte/ESC-POS
↓
Envoi à l’imprimante thermique
↓
Découpe papier si supportée
```

## 5.2 Technologies recommandées

- `python-escpos`
- `pywin32`

## 5.3 Paramètres nécessaires

Dans la table `parametres`, prévoir :

- `nom_imprimante`
- `largeur_ticket`
- `impression_auto`

## 5.4 Largeurs supportées

L’application doit supporter :

- 58 mm
- 80 mm

La largeur 80 mm est recommandée, mais 58 mm doit rester possible.

## 5.5 Format recommandé du ticket

Exemple :

```txt
================================
        SALMOSPHARM 133
   Votre santé, notre priorité
================================
Facture : VTE-2026-000001
Date    : 15/06/2026 14:33
Vendeur : Jean Mukendi
--------------------------------
Paracétamol 500mg
2 x 2000 = 4000 CDF

Vitamine C
1 x 1500 = 1500 CDF
--------------------------------
TOTAL        : 5500 CDF
Reçu         : 6000 CDF
Monnaie      : 500 CDF
Paiement     : Espèces
--------------------------------
Merci de votre visite
================================
```

## 5.6 Impression automatique

Si `impression_auto = 1`, le ticket est imprimé directement après validation de la vente.

Si `impression_auto = 0`, l’application affiche le ticket et l’utilisateur peut cliquer sur `Imprimer`.

## 5.7 Réimpression

La réimpression est autorisée selon le rôle :

- vendeur : uniquement ses ventes ;
- gérant : toutes les ventes.

Toute réimpression doit créer une entrée dans `journaux_activite`.

## 5.8 Gestion des erreurs d’impression

L’application doit afficher des messages propres pour :

- imprimante non configurée ;
- imprimante introuvable ;
- imprimante hors ligne ;
- papier terminé ;
- échec d’impression ;
- permission Windows insuffisante.

Une vente validée ne doit pas être annulée à cause d’un échec d’impression. Le ticket pourra être réimprimé.

---

# 6. Backup et restauration

## 6.1 Principe

Le gérant doit pouvoir exporter toutes les données de l’application dans un fichier portable, puis restaurer ces données sur un autre ordinateur.

Cas d’usage principal :

```txt
Ancien ordinateur
Paramètres → Exporter les données
↓
Fichier .spharm généré
↓
Nouveau ordinateur
Installer SALMOSPHARM
↓
Paramètres → Importer les données
↓
Toutes les données sont restaurées
```

## 6.2 Format du fichier

Extension recommandée :

```txt
.spharm
```

Exemple :

```txt
salmospharm_backup_2026-06-15_14-30.spharm
```

Techniquement, le fichier peut être une archive ZIP renommée.

## 6.3 Contenu du backup

Le fichier doit contenir :

```txt
backup.spharm
├── database/
│   └── salmospharm.sqlite3
├── assets/
│   └── logo.png
├── factures/
│   └── fichiers éventuels
└── manifest.json
```

## 6.4 Manifest

Le `manifest.json` doit contenir :

- nom de l’application ;
- version de l’application ;
- version du backup ;
- date de création ;
- présence de la base ;
- présence des assets ;
- présence des factures archivées.

## 6.5 Export manuel

L’export manuel est réservé au gérant.

Règles :

- utiliser l’API SQLite `backup()` pour copier la base proprement ;
- ne pas faire un simple copier-coller pendant que l’application est active ;
- inclure les fichiers utiles ;
- journaliser `BACKUP_EXPORTE`.

## 6.6 Import manuel

L’import est réservé au gérant.

Règles :

1. Vérifier que le fichier est valide.
2. Vérifier le `manifest.json`.
3. Vérifier que la base SQLite est présente.
4. Créer une sauvegarde automatique de sécurité avant import.
5. Remplacer les données actuelles.
6. Restaurer les assets et factures si présents.
7. Journaliser `BACKUP_IMPORTE`.
8. Redémarrer l’application.

## 6.7 Sauvegarde automatique

La sauvegarde automatique est validée.

Comportement recommandé :

- sauvegarde quotidienne si l’application est utilisée ;
- sauvegarde à la fermeture de l’application ;
- sauvegarde obligatoire avant import ;
- conservation des 15 dernières sauvegardes.

## 6.8 Messages utilisateur

Avant import :

```txt
L’import remplacera les données actuelles de cette installation.
Une sauvegarde de sécurité sera créée avant le remplacement.
Voulez-vous continuer ?
```

Après import :

```txt
Les données ont été restaurées avec succès.
L’application doit redémarrer pour appliquer les changements.
```

---

# 7. Packaging et livraison Windows

## 7.1 Objectif

Le client doit recevoir un installateur Windows simple à utiliser.

Livrable final :

```txt
SALMOSPHARM_Setup.exe
```

Le client ne doit pas recevoir :

- le code source ;
- les fichiers `.py` ;
- un environnement virtuel ;
- un fichier `requirements.txt` seul ;
- une base SQLite à placer manuellement.

## 7.2 Build recommandé

Utiliser PyInstaller en mode `--onedir`.

Raison :

- plus stable avec PySide6 ;
- meilleure gestion des assets ;
- meilleure compatibilité avec les DLL ;
- plus facile à diagnostiquer en cas d’erreur.

## 7.3 Installateur recommandé

Utiliser Inno Setup.

L’installateur doit :

- installer l’application dans `Program Files` ;
- créer un raccourci bureau ;
- créer une entrée menu démarrer ;
- inclure les assets nécessaires ;
- ne pas écraser les données utilisateur lors d’une mise à jour.

## 7.4 Chemins Windows

Application :

```txt
C:\Program Files\SALMOSPHARM\
```

Données :

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\
```

Sous-dossiers données :

```txt
data\
backups\
logs\
factures\
assets\
config\
```

## 7.5 Premier lancement après installation

Au premier lancement :

1. Créer le dossier AppData si absent.
2. Créer la base SQLite si absente.
3. Appliquer le schéma.
4. Insérer les données initiales.
5. Afficher l’écran de création du compte gérant.
6. Générer le code de récupération.

## 7.6 Mise à jour de l’application

Lors d’une mise à jour :

- ne pas supprimer la base existante ;
- ne pas écraser les backups ;
- ne pas écraser les factures archivées ;
- appliquer les migrations nécessaires ;
- créer une sauvegarde avant migration si possible.

---

# 8. Tests de validation avant livraison

## 8.1 Tests d’installation

- Installer l’application sur un PC Windows propre.
- Vérifier le raccourci bureau.
- Vérifier le lancement depuis le menu démarrer.
- Vérifier que la base est créée dans AppData.
- Vérifier que l’application ne demande pas Python.

## 8.2 Tests premier lancement

- L’écran de création du gérant apparaît si aucun utilisateur n’existe.
- Le compte gérant est créé.
- Le code de récupération est généré.
- Le code est affiché une seule fois.
- Le gérant peut se connecter.

## 8.3 Tests authentification

- Connexion gérant valide.
- Connexion vendeur valide.
- Mauvais mot de passe refusé.
- Compte vendeur désactivé refusé.
- Récupération de mot de passe avec code valide.
- Récupération refusée avec code invalide.

## 8.4 Tests permissions

- Le vendeur ne voit pas les paramètres.
- Le vendeur ne peut pas créer de produit.
- Le vendeur ne peut pas modifier le stock.
- Le vendeur ne peut pas créer de vendeur.
- Le vendeur ne peut pas importer/exporter les données.
- Le gérant accède à tous les modules.

## 8.5 Tests produits et stock

- Création d’une catégorie.
- Création d’un produit.
- Entrée de stock avec lot.
- Ajustement de stock.
- Stock faible détecté.
- Expiration proche détectée.
- Lot expiré bloqué à la vente.

## 8.6 Tests vente

- Vente avec stock suffisant.
- Vente refusée si panier vide.
- Vente refusée si stock insuffisant.
- Vente refusée si lot expiré.
- Montant reçu inférieur au total refusé.
- Stock diminué après vente.
- Mouvement de stock créé.
- Lignes de vente créées.
- Vente journalisée.
- Vente impossible à annuler.

## 8.7 Tests FEFO

Créer deux lots pour le même produit :

- Lot A : expiration plus proche ;
- Lot B : expiration plus lointaine.

Vérifier que la vente sort d’abord du lot A.

## 8.8 Tests impression thermique

- Imprimante configurée.
- Ticket 80 mm imprimé.
- Ticket 58 mm imprimé si sélectionné.
- Impression automatique après vente.
- Réimpression par vendeur de ses tickets.
- Réimpression par gérant de tous les tickets.
- Réimpression refusée pour vente d’un autre vendeur.
- Échec d’impression géré proprement.

## 8.9 Tests backup/restauration

- Export `.spharm` généré.
- Manifest présent.
- Base présente dans le backup.
- Import sur une nouvelle installation.
- Données restaurées correctement.
- Sauvegarde de sécurité créée avant import.
- Fichier invalide refusé.

## 8.10 Tests rapports

- Rapport journalier correct.
- Rapport mensuel correct.
- Rapport par vendeur correct.
- Produits les plus vendus corrects.
- Montants affichés en CDF.

## 8.11 Tests journalisation

Vérifier que les actions suivantes apparaissent dans l’historique :

- connexion ;
- création utilisateur ;
- création produit ;
- entrée stock ;
- vente ;
- impression ;
- réimpression ;
- export backup ;
- import backup ;
- modification paramètres.

---

# 9. Consignes strictes pour LLM/Codex

Lors de l’implémentation, respecter ces consignes :

1. Ne jamais ajouter de paiement mobile.
2. Ne jamais ajouter de carte bancaire.
3. Ne jamais ajouter une table `modes_paiement`.
4. Ne jamais créer de table `factures`.
5. Ne jamais créer de table `rapports`.
6. Ne jamais permettre l’annulation d’une vente validée.
7. Ne jamais vendre un lot expiré.
8. Toujours appliquer FEFO pour la sortie de stock.
9. Toujours stocker les montants en INTEGER CDF.
10. Toujours passer par les services pour la logique métier.
11. Ne jamais mettre la logique métier directement dans les écrans PySide6.
12. Toujours journaliser les actions sensibles.
13. Toujours vérifier les permissions côté service.
14. Toujours garder les tables en français.
15. Toujours stocker les données utilisateur dans AppData, pas dans Program Files.
16. Toujours prévoir les erreurs utilisateur propres.
17. Toujours protéger l’import/export backup par rôle gérant.

---

# 10. Checklist finale de livraison client

Avant d’envoyer le projet au client, vérifier :

```txt
[ ] Application installable via SALMOSPHARM_Setup.exe
[ ] Aucun besoin d’installer Python
[ ] Base SQLite créée automatiquement
[ ] Création du compte gérant au premier lancement
[ ] Code de récupération généré
[ ] Connexion gérant OK
[ ] Connexion vendeur OK
[ ] Permissions vendeur correctes
[ ] Produits OK
[ ] Stock OK
[ ] Vente OK
[ ] Vente non annulable
[ ] FEFO OK
[ ] Lots expirés bloqués
[ ] Ticket thermique OK
[ ] Réimpression OK
[ ] Backup export OK
[ ] Backup import OK
[ ] Sauvegarde automatique OK
[ ] Rapports OK
[ ] Historique des actions OK
[ ] Données dans AppData
[ ] Application testée sur un autre PC Windows
```

---

# 11. Conclusion

Ce fichier sert de référence pour l’implémentation des modules visibles, de l’interface, de l’impression, du backup et de la livraison client.

Il faut toujours le lire avec les autres fichiers de documentation, surtout :

- `03_REGLES_METIER_ET_SECURITE.md` pour les règles métier ;
- `04_BASE_DE_DONNEES_SQLITE.md` pour le schéma ;
- `02_ARCHITECTURE_ET_STACK.md` pour l’organisation du code.

La priorité est de livrer une application simple, stable, locale, utilisable par des non-techniciens et conforme aux décisions validées.
