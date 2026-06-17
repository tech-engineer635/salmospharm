# 01 — CONTEXTE ET OBJECTIFS DU PROJET

## Projet : SALMOSPHARM 133

**Nom du projet :** SALMOSPHARM 133  
**Type de projet :** Application desktop de gestion de pharmacie  
**Version fonctionnelle visée :** Version 1.0  
**Offre retenue :** Offre 2 — Version professionnelle  
**Mode d’utilisation :** Application locale, installée sur ordinateur Windows  
**Base de données :** SQLite locale  
**Mode réseau :** Offline-first  
**Devise unique :** Franc congolais — CDF  
**Paiement :** Espèces uniquement  
**Public cible :** Gérant de pharmacie et vendeurs  

---

# 1. Objectif du document

Ce fichier a pour rôle de donner le contexte général du projet SALMOSPHARM 133 avant toute implémentation.

Il sert de référence principale pour comprendre :

- ce que l’application doit faire ;
- pour qui elle est construite ;
- dans quel contexte elle sera utilisée ;
- quelles décisions fonctionnelles ont déjà été validées ;
- quelles limites ne doivent pas être dépassées ;
- quelles règles générales doivent guider le développement.

Ce document est destiné :

- au développeur principal ;
- aux autres développeurs qui rejoindraient le projet ;
- aux assistants IA utilisés pendant l’implémentation ;
- à Codex ou tout autre outil de génération de code ;
- à toute personne chargée de maintenir ou faire évoluer l’application.

Ce document ne doit pas être traité comme une simple présentation commerciale. Il doit être utilisé comme un document de cadrage technique et fonctionnel.

---

# 2. Résumé du projet

SALMOSPHARM 133 est une application desktop destinée à faciliter la gestion quotidienne d’une pharmacie.

L’application doit permettre au gérant et aux vendeurs de gérer les opérations principales de la pharmacie :

- connexion sécurisée ;
- gestion des utilisateurs ;
- gestion des produits ;
- gestion des stocks ;
- suivi des lots ;
- suivi des dates d’expiration ;
- réalisation des ventes ;
- impression des tickets de vente ;
- consultation des factures/reçus ;
- génération de rapports ;
- gestion des alertes ;
- journalisation des actions sensibles ;
- sauvegarde et restauration complète des données.

L’application est conçue pour fonctionner localement sur un ordinateur Windows, sans nécessiter de connexion internet permanente.

Elle doit être simple à utiliser, stable, rapide et adaptée à des utilisateurs non techniques.

---

# 3. Vision générale du produit

SALMOSPHARM 133 doit être un logiciel de caisse et de gestion interne pour pharmacie.

L’objectif n’est pas de construire une application complexe inutilement, mais un outil clair, fiable et utilisable au quotidien.

La priorité est donnée à :

- la simplicité d’utilisation ;
- la fiabilité des ventes ;
- la bonne gestion du stock ;
- la prévention des ventes de produits expirés ;
- la traçabilité des actions ;
- la possibilité de récupérer les données en cas de changement d’ordinateur ;
- une interface professionnelle adaptée à une pharmacie locale.

L’application doit donner au gérant une vision claire de son activité, tout en permettant aux vendeurs de travailler rapidement sans accéder aux fonctions administratives.

---

# 4. Contexte d’utilisation

## 4.1 Environnement réel

L’application sera utilisée dans une pharmacie physique.

Les utilisateurs ne sont pas forcément techniques. L’interface doit donc éviter :

- les menus trop complexes ;
- les messages techniques ;
- les workflows trop longs ;
- les paramètres inutiles ;
- les écrans surchargés.

Les opérations les plus fréquentes doivent être rapides :

- rechercher un produit ;
- vérifier son stock ;
- ajouter au panier ;
- encaisser ;
- imprimer le ticket.

## 4.2 Contrainte locale

L’application est pensée pour fonctionner localement.

Cela signifie :

- pas de serveur distant obligatoire ;
- pas d’API web obligatoire ;
- pas de dépendance à internet pour vendre ;
- données stockées dans une base SQLite locale ;
- sauvegarde/export possible pour changer de PC.

## 4.3 Contrainte matérielle

Le client utilisera une imprimante thermique pour les tickets de vente.

L’application doit donc prévoir :

- l’impression directe de tickets ;
- le support des formats 58 mm et 80 mm ;
- la sélection de l’imprimante dans les paramètres ;
- la réimpression contrôlée des tickets ;
- des messages clairs en cas d’échec d’impression.

---

# 5. Offre fonctionnelle retenue

L’offre retenue pour le projet est l’**Offre 2 — Version professionnelle**.

Cette version inclut les fonctionnalités essentielles ainsi que des fonctionnalités supplémentaires.

## 5.1 Fonctionnalités de base incluses

L’application doit inclure :

- authentification utilisateur ;
- gestion des rôles ;
- gestion des produits ;
- gestion du stock ;
- gestion des ventes ;
- génération de facture ou reçu ;
- impression des tickets ;
- dashboard vendeur ;
- rapport journalier simple ;
- interface ergonomique.

## 5.2 Fonctionnalités professionnelles incluses

L’application doit également inclure :

- dashboard gérant amélioré ;
- historique détaillé des actions ;
- alertes intelligentes ;
- rapports mensuels consolidés ;
- recherche rapide de produits ;
- interface UX/UI améliorée ;
- statistiques simplifiées.

## 5.3 Positionnement de l’offre 2

L’offre 2 n’est pas une version minimale.

Elle doit être suffisamment professionnelle pour une utilisation réelle en pharmacie, mais elle ne doit pas intégrer des fonctionnalités trop avancées réservées à une version premium.

Elle doit rester :

- robuste ;
- simple ;
- locale ;
- maintenable ;
- livrable sous forme d’exécutable Windows.

---

# 6. Utilisateurs du système

L’application comporte deux profils principaux :

1. le gérant ;
2. le vendeur.

Ces deux profils ne doivent pas avoir les mêmes droits.

---

## 6.1 Gérant

Le gérant est l’utilisateur principal et administrateur du système.

Il possède un accès complet à l’application.

### Responsabilités du gérant

Le gérant peut :

- créer le compte initial de l’application ;
- créer les comptes vendeurs ;
- désactiver un vendeur ;
- gérer les produits ;
- gérer le stock ;
- consulter toutes les ventes ;
- consulter tous les tickets/factures ;
- réimprimer les tickets ;
- consulter les rapports ;
- consulter les alertes ;
- consulter l’historique des actions ;
- modifier les paramètres ;
- configurer l’imprimante thermique ;
- exporter les données ;
- importer une sauvegarde ;
- gérer les sauvegardes.

### Objectif de l’espace gérant

L’espace gérant doit permettre de piloter toute la pharmacie.

Il doit fournir une vision globale sur :

- les ventes du jour ;
- les ventes mensuelles ;
- le stock disponible ;
- les produits en rupture ;
- les produits proches de l’expiration ;
- les vendeurs actifs ;
- les performances par vendeur ;
- les dernières actions effectuées.

---

## 6.2 Vendeur

Le vendeur est un utilisateur opérationnel.

Il a un accès limité aux fonctions nécessaires à son travail quotidien.

### Responsabilités du vendeur

Le vendeur peut :

- se connecter ;
- voir son tableau de bord ;
- rechercher un produit ;
- consulter le stock disponible ;
- créer une vente ;
- encaisser en espèces ;
- imprimer un ticket ;
- réimprimer ses propres tickets si autorisé ;
- consulter son historique personnel de ventes ;
- consulter les factures liées à ses ventes.

### Restrictions du vendeur

Le vendeur ne peut pas :

- créer un autre utilisateur ;
- créer un produit ;
- modifier un produit ;
- modifier le stock ;
- accéder aux paramètres ;
- exporter les données ;
- importer une sauvegarde ;
- consulter les rapports globaux ;
- consulter toutes les ventes de tous les vendeurs ;
- accéder à l’historique complet des actions ;
- modifier les règles de l’application.

### Objectif de l’espace vendeur

L’espace vendeur doit être simple et rapide.

Le vendeur doit pouvoir vendre sans être distrait par les fonctions administratives.

Les actions principales doivent être visibles immédiatement :

- nouvelle vente ;
- recherche produit ;
- historique de mes ventes ;
- factures/reçus.

---

# 7. Contraintes générales validées

Les contraintes suivantes sont définitives pour la version 1.0.

Elles doivent être respectées par tous les développeurs et tous les assistants IA travaillant sur le projet.

---

## 7.1 Application desktop uniquement

SALMOSPHARM 133 est une application desktop.

Elle ne doit pas être conçue comme :

- une application web ;
- une application mobile ;
- une API distante ;
- une plateforme SaaS ;
- un système multi-pharmacie connecté.

La version 1.0 doit fonctionner sur Windows via un exécutable ou un installateur.

---

## 7.2 Fonctionnement offline-first

L’application doit fonctionner sans internet.

La connexion internet ne doit pas être nécessaire pour :

- se connecter ;
- vendre ;
- imprimer ;
- consulter le stock ;
- générer un rapport ;
- sauvegarder localement les données.

Toute dépendance obligatoire à un service cloud est interdite pour la version 1.0.

---

## 7.3 Base de données locale SQLite

La base de données principale est SQLite.

Toutes les données métier doivent être stockées localement.

La base doit contenir notamment :

- les utilisateurs ;
- les catégories ;
- les produits ;
- les lots ;
- les mouvements de stock ;
- les ventes ;
- les lignes de vente ;
- les alertes ;
- les journaux d’activité ;
- les paramètres.

SQLite est retenu parce que :

- l’application est locale ;
- la pharmacie n’a pas besoin d’un serveur dédié ;
- l’installation doit rester simple ;
- la sauvegarde peut être gérée par fichier ;
- le volume de données attendu reste raisonnable.

---

## 7.4 Devise unique : CDF

La seule devise acceptée est le franc congolais : CDF.

L’application ne doit pas gérer :

- USD ;
- EUR ;
- multi-devise ;
- taux de change ;
- conversion automatique.

Tous les montants doivent être affichés en CDF.

Les montants doivent être stockés en entiers, pas en nombres décimaux.

Exemple :

```txt
Prix : 2500 CDF
Stockage : 2500
```

---

## 7.5 Paiement espèces uniquement

Le seul mode de paiement autorisé est le paiement en espèces.

L’application ne doit jamais proposer :

- Orange Money ;
- M-Pesa ;
- Airtel Money ;
- carte bancaire ;
- virement ;
- crédit client ;
- paiement mixte ;
- portefeuille électronique.

Aucun écran ne doit contenir de choix de mode de paiement.

Le ticket peut afficher :

```txt
Paiement : Espèces
```

Mais ce mode n’est pas configurable.

---

## 7.6 Aucune annulation de transaction

Une vente validée est définitive.

Il ne doit pas exister de fonctionnalité permettant :

- d’annuler une vente ;
- de supprimer une vente ;
- de modifier une vente validée ;
- de remettre automatiquement le stock après annulation.

Cette décision simplifie le fonctionnement et limite les manipulations sensibles.

Les ventes sont conservées comme historique définitif.

---

## 7.7 Gestion stricte du stock

L’application doit empêcher les erreurs de stock.

Règles principales :

- impossible de vendre un produit sans stock ;
- impossible de vendre une quantité supérieure au stock disponible ;
- impossible de vendre un lot expiré ;
- le stock est décrémenté automatiquement après validation de la vente ;
- les mouvements de stock doivent être journalisés ;
- les alertes doivent être générées lorsque le stock devient faible.

---

## 7.8 Gestion des lots selon FEFO

La sortie du stock doit suivre la logique FEFO.

FEFO signifie :

```txt
First Expired, First Out
```

Cela veut dire que les lots dont la date d’expiration est la plus proche doivent être vendus en premier.

Exemple :

```txt
Produit : Paracétamol 500mg
Lot A : expire le 2026-08-20, quantité 10
Lot B : expire le 2026-12-10, quantité 50
```

La vente doit utiliser d’abord le Lot A.

Cette règle est obligatoire pour limiter les pertes liées aux produits expirés.

---

## 7.9 Blocage des produits expirés

Un lot expiré ne peut pas être vendu.

Un produit peut apparaître dans la recherche, mais il ne doit être vendable que s’il possède au moins un lot :

- actif ;
- non expiré ;
- avec quantité disponible.

Si tous les lots sont expirés ou vides, le produit ne doit pas pouvoir être ajouté au panier.

---

## 7.10 Imprimante thermique

L’impression principale se fait via une imprimante thermique.

L’application doit prévoir :

- un ticket simple et lisible ;
- une largeur configurable : 58 mm ou 80 mm ;
- une imprimante par défaut configurable ;
- l’impression automatique après validation d’une vente ;
- la réimpression contrôlée ;
- des erreurs claires si l’impression échoue.

Le PDF ne doit pas être le flux principal d’impression quotidienne.

L’impression quotidienne doit être directe vers l’imprimante thermique.

---

## 7.11 Sauvegarde et restauration

Le gérant doit pouvoir exporter toutes les données de l’application dans un fichier de sauvegarde.

Cas d’usage principal : changement d’ordinateur.

Flux attendu :

```txt
Ancien ordinateur
→ Paramètres
→ Exporter les données
→ Génération d’un fichier de sauvegarde
→ Nouveau ordinateur
→ Installation de SALMOSPHARM
→ Importer les données
→ Restauration complète
```

Le fichier de sauvegarde doit permettre de restaurer l’état de l’application à un instant donné.

L’import doit remplacer les données actuelles après confirmation.

Avant tout import, l’application doit créer automatiquement une sauvegarde de sécurité des données existantes.

---

## 7.12 Code de récupération

Lors de la création du compte gérant, l’application doit fournir un code de récupération.

Ce code sert à récupérer l’accès si le gérant oublie son mot de passe.

Règles :

- le code doit être généré automatiquement ;
- le code doit être affiché une seule fois ;
- le gérant doit être invité à le conserver ;
- le code ne doit jamais être stocké en clair ;
- seul le hash du code doit être enregistré ;
- après utilisation du code, un nouveau code doit être généré.

---

# 8. Objectifs fonctionnels détaillés

## 8.1 Authentification

L’application doit s’ouvrir sur un écran de connexion.

L’utilisateur doit saisir :

- son identifiant ;
- son mot de passe.

Après connexion, l’application doit rediriger :

- le gérant vers l’espace gérant ;
- le vendeur vers l’espace vendeur.

Un compte désactivé ne doit pas pouvoir se connecter.

Au premier lancement, si aucun compte n’existe, l’application doit afficher l’écran de création du compte gérant.

---

## 8.2 Gestion des vendeurs

Le gérant doit pouvoir créer et gérer les vendeurs.

Fonctions attendues :

- ajouter un vendeur ;
- modifier les informations d’un vendeur ;
- désactiver un vendeur ;
- réactiver un vendeur ;
- consulter ses performances ;
- voir ses ventes du jour.

Un vendeur désactivé conserve son historique, mais ne peut plus se connecter.

---

## 8.3 Gestion des produits

Le gérant doit pouvoir gérer le catalogue de produits.

Informations attendues :

- nom du produit ;
- catégorie ;
- forme ou description ;
- code-barres éventuel ;
- prix de vente en CDF ;
- seuil de stock faible ;
- statut actif/inactif.

Un produit qui possède déjà un historique de vente ne doit pas être supprimé brutalement.

La désactivation est préférable à la suppression.

---

## 8.4 Gestion du stock

Le gérant doit pouvoir :

- ajouter une entrée de stock ;
- créer ou mettre à jour un lot ;
- ajuster une quantité ;
- consulter les mouvements ;
- consulter les ruptures ;
- consulter les expirations proches.

Chaque mouvement important doit être enregistré.

---

## 8.5 Gestion des ventes

Le vendeur et le gérant peuvent créer une vente.

Une vente contient :

- un numéro unique ;
- un vendeur ;
- une date ;
- plusieurs lignes de vente ;
- un total ;
- un montant reçu ;
- une monnaie rendue calculée.

La vente suit ce processus :

```txt
Recherche produit
→ Ajout au panier
→ Vérification stock
→ Calcul du total
→ Saisie montant reçu
→ Validation
→ Décrémentation stock
→ Enregistrement vente
→ Impression ticket
→ Journalisation
```

La vente validée est définitive.

---

## 8.6 Factures et tickets

L’application doit générer un reçu/ticket après chaque vente.

Le ticket doit contenir :

- nom de la pharmacie ;
- slogan éventuel ;
- numéro de vente ;
- date et heure ;
- vendeur ;
- produits vendus ;
- quantités ;
- prix unitaires ;
- sous-totaux ;
- total ;
- montant reçu ;
- monnaie rendue ;
- devise CDF ;
- mention paiement espèces ;
- message de remerciement.

La réimpression doit être possible selon les règles de permissions.

---

## 8.7 Rapports

L’application doit fournir des rapports simples et utiles.

Rapports attendus :

- ventes du jour ;
- ventes mensuelles ;
- ventes par vendeur ;
- produits les plus vendus ;
- stock faible ;
- expirations proches.

Les rapports ne doivent pas être stockés dans une table dédiée.

Ils doivent être calculés depuis les ventes, lignes de vente, produits, lots et utilisateurs.

---

## 8.8 Alertes

L’application doit générer des alertes pour :

- stock faible ;
- rupture ;
- expiration proche ;
- produit expiré.

Les alertes doivent être visibles sur le tableau de bord gérant et dans l’écran Alertes.

Elles doivent être utiles, mais pas envahissantes.

---

## 8.9 Historique des actions

L’application doit garder une trace des actions sensibles.

Actions à journaliser :

- connexion réussie ;
- connexion échouée ;
- compte gérant créé ;
- vendeur créé ;
- vendeur modifié ;
- vendeur désactivé ;
- produit créé ;
- produit modifié ;
- entrée de stock ;
- ajustement de stock ;
- vente validée ;
- ticket imprimé ;
- ticket réimprimé ;
- sauvegarde exportée ;
- sauvegarde importée ;
- paramètres modifiés ;
- code de récupération généré ;
- mot de passe réinitialisé.

---

## 8.10 Paramètres

L’écran Paramètres est réservé au gérant.

Il doit permettre de configurer :

- nom de la pharmacie ;
- téléphone ;
- adresse ;
- logo ;
- seuil d’expiration ;
- imprimante thermique ;
- largeur ticket ;
- impression automatique ;
- sauvegarde automatique ;
- export des données ;
- import des données.

Le paiement et la devise ne doivent pas être modifiables.

Ils sont fixes :

```txt
Paiement : Espèces
Devise : CDF
```

---

# 9. Objectifs non fonctionnels

## 9.1 Simplicité

L’application doit être facile à comprendre.

Un vendeur doit pouvoir effectuer une vente sans formation longue.

Les libellés doivent être clairs et en français.

---

## 9.2 Fiabilité

L’application doit éviter les erreurs critiques :

- vente sans stock ;
- vente de produit expiré ;
- montant reçu inférieur au total ;
- accès vendeur à des fonctions gérant ;
- perte de données pendant une restauration ;
- impression silencieusement échouée.

---

## 9.3 Rapidité

Les actions courantes doivent être rapides :

- recherche produit ;
- ajout panier ;
- validation vente ;
- impression ticket ;
- consultation historique.

La base SQLite doit être indexée sur les champs importants.

---

## 9.4 Maintenabilité

Le code doit être organisé en couches.

L’interface ne doit pas contenir la logique métier principale.

Les règles doivent être centralisées dans les services.

L’accès à la base doit passer par des repositories ou une couche dédiée.

---

## 9.5 Sécurité locale

Même si l’application est locale, elle doit respecter les principes minimums :

- mot de passe hashé ;
- code de récupération hashé ;
- séparation des rôles ;
- actions sensibles protégées ;
- accès import/export réservé au gérant ;
- sauvegarde avant restauration ;
- journalisation des opérations sensibles.

---

# 10. Limites explicites de la version 1.0

La version 1.0 ne doit pas inclure :

- application mobile ;
- interface web ;
- synchronisation cloud ;
- multi-pharmacie ;
- gestion de plusieurs succursales ;
- paiement mobile ;
- paiement bancaire ;
- gestion multi-devise ;
- crédit client ;
- comptabilité avancée ;
- gestion fournisseur avancée ;
- commande automatique fournisseur ;
- intelligence artificielle ;
- reconnaissance de code-barres obligatoire ;
- annulation de transaction ;
- suppression de ventes validées ;
- accès distant par navigateur ;
- API publique.

Toute proposition de ce type doit être considérée comme hors périmètre pour la version 1.0.

---

# 11. Périmètre fonctionnel retenu

Le périmètre fonctionnel retenu est le suivant :

```txt
Authentification
Gestion des rôles
Création du compte gérant au premier lancement
Code de récupération
Gestion des vendeurs
Gestion des produits
Gestion des catégories
Gestion des lots
Gestion du stock
Gestion des ventes
Impression thermique des tickets
Réimpression contrôlée
Historique des ventes
Rapports simplifiés
Alertes stock/expiration
Historique des actions
Paramètres application
Export/import des données
Sauvegarde automatique
Packaging Windows
```

---

# 12. Décisions définitivement validées

Les décisions suivantes ont été validées et ne doivent pas être remises en cause pendant l’implémentation sans nouvelle instruction explicite.

## 12.1 Décisions métier

```txt
- Application desktop Windows
- Python comme langage principal
- SQLite comme base locale
- Paiement espèces uniquement
- Devise CDF uniquement
- Deux rôles : gérant et vendeur
- Gérant avec accès complet
- Vendeur avec accès limité
- Création du compte gérant au premier lancement
- Code de récupération fourni au gérant
- Aucune annulation de transaction
- Vente définitive après validation
- Stock diminué automatiquement après vente
- Sortie des lots selon FEFO
- Lots expirés interdits à la vente
- Réimpression de ticket autorisée selon rôle
- Backup/export/import des données
- Sauvegarde automatique
- Journalisation des actions sensibles
- Impression thermique 58 mm / 80 mm
```

## 12.2 Décisions techniques

```txt
- Python
- PySide6
- SQLite
- SQLAlchemy
- Alembic
- pywin32
- python-escpos
- PyInstaller
- Inno Setup
- pytest
```

## 12.3 Décisions de livraison

```txt
- Le client reçoit un installateur Windows
- Nom recommandé : SALMOSPHARM_Setup.exe
- Le client ne reçoit pas le code source
- Les données sont stockées dans AppData/Local/SALMOSPHARM
- L’application est installée dans Program Files
```

---

# 13. Vocabulaire de référence

Pour éviter les incohérences, les termes suivants doivent être utilisés dans l’application et dans le code métier.

## 13.1 Utilisateurs

```txt
Gérant
Vendeur
Utilisateur
Compte actif
Compte désactivé
```

## 13.2 Produits et stock

```txt
Produit
Catégorie
Lot
Numéro de lot
Date d’expiration
Stock disponible
Stock faible
Rupture
Entrée de stock
Ajustement de stock
Mouvement de stock
```

## 13.3 Vente

```txt
Vente
Nouvelle vente
Panier
Ligne de vente
Quantité
Prix unitaire
Sous-total
Total
Montant reçu
Monnaie rendue
Ticket
Réimpression
```

## 13.4 Paiement

```txt
Espèces
CDF
```

Ne pas utiliser :

```txt
Mobile Money
Carte bancaire
Virement
Paiement mixte
Mode de paiement configurable
```

## 13.5 Sauvegarde

```txt
Exporter les données
Importer les données
Sauvegarde automatique
Sauvegarde de sécurité
Fichier .spharm
Restauration
```

---

# 14. Principes à respecter par Codex ou tout assistant IA

Tout assistant IA travaillant sur ce projet doit respecter les consignes suivantes :

1. Ne jamais ajouter de fonctionnalité hors périmètre sans demande explicite.
2. Ne jamais ajouter de paiement mobile ou bancaire.
3. Ne jamais introduire de multi-devise.
4. Ne jamais ajouter d’annulation de vente.
5. Ne jamais permettre au vendeur d’accéder aux fonctions du gérant.
6. Ne jamais stocker de mot de passe ou de code de récupération en clair.
7. Ne jamais faire dépendre l’application d’internet pour fonctionner.
8. Ne jamais stocker les rapports dans des tables dédiées.
9. Ne jamais créer une table `modes_paiement`.
10. Ne jamais créer une table `factures` si les données peuvent être générées depuis les ventes.
11. Toujours respecter les noms de tables en français.
12. Toujours stocker les montants CDF en entiers.
13. Toujours passer par la logique métier avant de modifier le stock.
14. Toujours journaliser les actions sensibles.
15. Toujours protéger l’import/export des données par le rôle gérant.

---

# 15. Critères de réussite du projet

Le projet peut être considéré comme réussi si :

- le gérant peut installer et utiliser l’application sur Windows ;
- le premier compte gérant peut être créé au premier lancement ;
- le gérant peut créer des vendeurs ;
- un vendeur peut vendre rapidement ;
- les ventes diminuent correctement le stock ;
- les lots proches de l’expiration sortent en premier ;
- les lots expirés sont bloqués ;
- les tickets thermiques s’impriment correctement ;
- le gérant peut consulter les ventes et rapports ;
- les alertes de stock et expiration sont visibles ;
- les actions sensibles sont journalisées ;
- le gérant peut exporter les données ;
- les données peuvent être restaurées sur un autre PC ;
- l’application reste utilisable sans internet ;
- le client reçoit un installateur propre.

---

# 16. Résumé final

SALMOSPHARM 133 est une application desktop locale pour pharmacie.

Elle doit être simple, fiable et adaptée à une utilisation réelle en caisse.

Les décisions clés sont :

```txt
Desktop Windows
Python + PySide6
SQLite local
Offline-first
Gérant / Vendeur
Espèces uniquement
CDF uniquement
Aucune annulation de vente
FEFO obligatoire
Blocage des lots expirés
Impression thermique
Backup/restauration complète
Journalisation des actions sensibles
Livraison sous installateur Windows
```

Ce fichier constitue la base de contexte du projet.

Les autres documents doivent détailler :

- l’architecture et la stack ;
- les règles métier et sécurité ;
- la base de données SQLite ;
- les modules, l’interface et la livraison.

