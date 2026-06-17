# 03 — Règles métier et sécurité

## Projet : SALMOSPHARM 133

**Type de document :** Spécification métier et sécurité pour l’implémentation  
**Version :** 1.0  
**Périmètre :** Offre 2 — Version professionnelle  
**Application :** Desktop Windows, locale, offline-first  
**Stack cible :** Python, PySide6, SQLite, SQLAlchemy  

---

# 1. Rôle de ce document

Ce document définit les règles métier, les contraintes de sécurité et les comportements obligatoires de l’application **SALMOSPHARM 133**.

Il doit être considéré comme une **source de vérité** pendant le développement.

Tout développeur, assistant IA, Codex ou LLM qui implémente une fonctionnalité doit respecter ce fichier avant de produire du code.

Ce fichier répond aux questions suivantes :

- Qui a le droit de faire quoi ?
- Quelles actions sont interdites ?
- Comment une vente doit être validée ?
- Comment le stock doit être diminué ?
- Comment gérer les lots expirés ?
- Comment sécuriser les comptes ?
- Quelles actions doivent être journalisées ?
- Quelles erreurs doivent être bloquées proprement ?

---

# 2. Principes métier fondamentaux

L’application SALMOSPHARM 133 repose sur des principes simples et stricts.

## 2.1 Application locale

SALMOSPHARM est une application desktop locale.

Cela signifie que :

- les données sont stockées localement sur le PC du client ;
- la base principale est SQLite ;
- l’application doit fonctionner sans connexion Internet ;
- aucun serveur distant n’est obligatoire ;
- aucune synchronisation cloud n’est prévue dans cette version.

## 2.2 Utilisation par des non-techniciens

Les utilisateurs finaux peuvent être non techniques.

L’application doit donc :

- afficher des messages simples ;
- éviter les termes techniques dans l’interface ;
- empêcher les erreurs au lieu de les expliquer après coup ;
- proposer des actions claires ;
- ne jamais afficher d’erreur Python, SQL ou stack trace à l’utilisateur.

## 2.3 Paiement unique

Le paiement est uniquement en espèces.

Règles strictes :

- aucun paiement mobile ;
- aucune carte bancaire ;
- aucun Orange Money ;
- aucun M-Pesa ;
- aucun Airtel Money ;
- aucun paiement mixte ;
- aucun choix de mode de paiement dans l’interface.

L’application peut afficher :

```txt
Paiement : Espèces
```

Mais elle ne doit jamais permettre de choisir un autre mode.

## 2.4 Devise unique

La devise unique est le **CDF**.

Règles strictes :

- aucun dollar américain ;
- aucune multi-devise ;
- aucune conversion ;
- aucun taux de change ;
- tous les montants sont affichés en CDF ;
- tous les montants sont stockés comme entiers.

Exemples valides :

```txt
1 500 CDF
25 000 CDF
300 CDF
```

Exemples interdits :

```txt
2.5 USD
1500.75 CDF
CDF/USD
Paiement en dollars
```

## 2.5 Vente définitive

Une vente validée est définitive.

Décision validée : **il n’y a pas de possibilité d’annuler une transaction**.

Cela implique :

- pas de bouton Annuler vente ;
- pas de suppression de vente ;
- pas de modification d’une vente validée ;
- pas de retour automatique de stock après vente ;
- pas de statut `ANNULEE` à gérer dans l’interface ;
- les tickets peuvent être réimprimés mais la vente reste inchangée.

Une fois qu’une vente est validée :

- le stock est diminué ;
- les lignes de vente sont créées ;
- le ticket peut être imprimé ;
- l’action est journalisée ;
- la vente devient non modifiable.

---

# 3. Rôles utilisateurs

L’application possède deux rôles principaux :

1. **Gérant**
2. **Vendeur**

Le rôle détermine :

- les écrans accessibles ;
- les actions autorisées ;
- les données visibles ;
- les opérations sensibles possibles.

---

# 4. Rôle Gérant

## 4.1 Définition

Le gérant est l’utilisateur administrateur principal de la pharmacie.

Il possède l’accès complet au système.

## 4.2 Permissions du gérant

Le gérant peut :

- accéder au tableau de bord global ;
- consulter toutes les ventes ;
- créer une vente si nécessaire ;
- gérer les produits ;
- gérer les catégories ;
- gérer le stock ;
- faire des entrées de stock ;
- ajuster le stock ;
- consulter les alertes ;
- consulter les rapports journaliers et mensuels ;
- consulter les performances des vendeurs ;
- créer des vendeurs ;
- modifier des vendeurs ;
- désactiver des vendeurs ;
- réactiver des vendeurs ;
- accéder aux paramètres ;
- configurer l’imprimante thermique ;
- exporter les données ;
- importer les données ;
- consulter l’historique des actions ;
- réimprimer tous les tickets ;
- sauvegarder/restaurer les données.

## 4.3 Restrictions du gérant

Même le gérant ne peut pas :

- annuler une vente validée ;
- supprimer une vente validée ;
- modifier les lignes d’une vente validée ;
- vendre un produit expiré ;
- vendre une quantité supérieure au stock disponible ;
- vendre un produit désactivé ;
- utiliser une autre devise que CDF ;
- choisir un autre mode de paiement que les espèces.

---

# 5. Rôle Vendeur

## 5.1 Définition

Le vendeur est l’utilisateur chargé des ventes quotidiennes.

Son accès est limité aux opérations nécessaires à la vente et à la consultation simple.

## 5.2 Permissions du vendeur

Le vendeur peut :

- se connecter ;
- voir son tableau de bord personnel ;
- créer une nouvelle vente ;
- rechercher un produit ;
- consulter le prix d’un produit ;
- consulter le stock disponible ;
- ajouter des produits au panier ;
- encaisser une vente en espèces ;
- imprimer le ticket après vente ;
- réimprimer ses propres tickets ;
- consulter son historique personnel de ventes ;
- consulter les factures/tickets liés à ses propres ventes.

## 5.3 Restrictions du vendeur

Le vendeur ne peut pas :

- créer un autre vendeur ;
- modifier un utilisateur ;
- désactiver un utilisateur ;
- accéder aux paramètres ;
- exporter les données ;
- importer les données ;
- modifier les produits ;
- créer un produit ;
- supprimer un produit ;
- modifier le stock ;
- faire une entrée de stock ;
- faire un ajustement de stock ;
- consulter l’historique complet des actions ;
- voir les rapports globaux ;
- voir les ventes des autres vendeurs ;
- modifier une vente validée ;
- annuler une vente ;
- vendre un produit expiré ;
- vendre un produit en rupture.

---

# 6. Authentification

## 6.1 Connexion obligatoire

L’application doit toujours démarrer par un écran de connexion, sauf lors du tout premier lancement si aucun compte n’existe encore.

Aucun module métier ne doit être accessible sans authentification.

## 6.2 Premier lancement

Au premier lancement, si la table `utilisateurs` est vide, l’application doit afficher un écran de création du compte gérant.

Processus :

1. L’application vérifie si aucun utilisateur n’existe.
2. Elle affiche l’écran de création du compte gérant.
3. Le gérant saisit ses informations.
4. Le mot de passe est hashé.
5. Un code de récupération est généré.
6. Le code est affiché une seule fois.
7. Le hash du code de récupération est stocké.
8. Le compte gérant est créé.
9. L’action est journalisée.

## 6.3 Données minimales du compte gérant

Le compte gérant doit contenir :

- nom complet ;
- identifiant ou email ;
- mot de passe ;
- confirmation du mot de passe ;
- rôle `GERANT` ;
- statut actif.

## 6.4 Mot de passe

Les mots de passe doivent être hashés.

Règles :

- ne jamais stocker un mot de passe en clair ;
- ne jamais afficher un mot de passe existant ;
- utiliser un algorithme de hash sécurisé ;
- recommander `bcrypt` ou `argon2` ;
- vérifier le mot de passe via comparaison sécurisée.

## 6.5 Code de récupération

Un code de récupération est fourni au gérant.

Ce code sert à récupérer l’accès si le gérant oublie son mot de passe.

Règles :

- le code est généré automatiquement ;
- le code doit être suffisamment long ;
- le code doit être difficile à deviner ;
- le code est affiché une seule fois ;
- le code doit pouvoir être imprimé ou copié ;
- seul le hash du code est stocké ;
- après utilisation, un nouveau code doit être généré ;
- l’ancien code devient invalide.

Exemple de format :

```txt
SALMOS-7K92-MP41-Q8XZ
```

## 6.6 Récupération de compte

Processus recommandé :

1. Le gérant clique sur « Mot de passe oublié ».
2. Il saisit son identifiant.
3. Il saisit son code de récupération.
4. L’application vérifie le hash du code.
5. Si le code est valide, le gérant crée un nouveau mot de passe.
6. Un nouveau code de récupération est généré.
7. Le nouveau code est affiché une seule fois.
8. L’action est journalisée.

## 6.7 Compte désactivé

Un compte vendeur désactivé ne peut pas se connecter.

Message utilisateur :

```txt
Ce compte est désactivé. Veuillez contacter le gérant.
```

---

# 7. Permissions et contrôle d’accès

## 7.1 Principe général

Les permissions doivent être vérifiées à deux niveaux :

1. dans l’interface ;
2. dans les services métier.

L’interface peut masquer les boutons interdits, mais la logique métier doit aussi bloquer l’action.

Exemple :

- le bouton `Exporter les données` n’apparaît pas pour le vendeur ;
- si un vendeur tente quand même d’appeler la fonction, le service refuse.

## 7.2 Règle stricte

Aucune action sensible ne doit dépendre uniquement de l’interface.

Les services doivent toujours vérifier le rôle courant.

## 7.3 Actions réservées au gérant

Les actions suivantes sont réservées au gérant :

- création de vendeur ;
- modification de vendeur ;
- désactivation de vendeur ;
- réactivation de vendeur ;
- création de produit ;
- modification de produit ;
- désactivation de produit ;
- entrée de stock ;
- ajustement de stock ;
- consultation des rapports globaux ;
- consultation de l’historique complet ;
- configuration des paramètres ;
- configuration de l’imprimante ;
- export des données ;
- import des données ;
- restauration depuis une sauvegarde ;
- réimpression de tous les tickets.

## 7.4 Actions autorisées au vendeur

Les actions suivantes sont autorisées au vendeur :

- nouvelle vente ;
- recherche produit ;
- consultation stock ;
- impression du ticket de ses ventes ;
- réimpression de ses propres tickets ;
- consultation de son historique personnel.

---

# 8. Produits

## 8.1 Définition

Un produit représente un médicament ou un article vendu dans la pharmacie.

Il contient les informations stables :

- nom ;
- code-barres ;
- catégorie ;
- prix de vente ;
- seuil minimum ;
- statut actif/inactif.

## 8.2 Produit actif

Seuls les produits actifs peuvent être vendus.

Un produit inactif :

- peut rester visible dans l’historique ;
- ne doit pas être proposé à la vente ;
- ne doit pas être ajouté au panier.

## 8.3 Suppression de produit

La suppression définitive d’un produit doit être évitée si le produit possède un historique de vente.

Recommandation :

- désactiver le produit au lieu de le supprimer ;
- conserver l’historique des ventes ;
- ne pas casser les références existantes.

## 8.4 Prix de vente

Le prix de vente actuel peut changer.

Cependant, les ventes passées doivent conserver le prix utilisé au moment de la vente grâce au champ `prix_unitaire` dans `lignes_vente`.

---

# 9. Lots de produits

## 9.1 Définition

Un lot représente une quantité physique d’un produit, généralement avec une date d’expiration.

Un même produit peut avoir plusieurs lots.

Exemple :

```txt
Produit : Paracétamol 500 mg
Lot A : 20 unités, expiration 2026-08-31
Lot B : 50 unités, expiration 2026-12-31
```

## 9.2 Quantité du lot

La quantité disponible est stockée au niveau du lot.

Le stock total d’un produit est calculé par la somme des quantités de ses lots valides.

## 9.3 Lot expiré

Un lot expiré ne peut pas être vendu.

Règles :

- si la date d’expiration est passée, le lot est bloqué ;
- le lot ne doit pas être utilisé dans une vente ;
- une alerte doit pouvoir être générée ;
- le vendeur doit voir que le produit est indisponible si aucun lot valide n’existe.

## 9.4 Lot proche de l’expiration

Un lot proche de l’expiration doit déclencher une alerte.

Le nombre de jours avant expiration est configurable dans les paramètres.

Exemple :

```txt
seuil_expiration_jours = 30
```

Si un lot expire dans moins de 30 jours, il doit être signalé.

---

# 10. Stock

## 10.1 Principe général

Le stock doit être fiable.

Toute modification importante du stock doit être traçable.

## 10.2 Stock disponible

Le stock disponible d’un produit est calculé à partir des lots non expirés et ayant une quantité positive.

Formule logique :

```txt
stock_disponible = somme des quantités des lots valides du produit
```

Un lot valide est un lot :

- non expiré ;
- avec quantité supérieure à zéro ;
- lié à un produit actif.

## 10.3 Produit en rupture

Un produit est en rupture si son stock disponible est égal à zéro.

Règles :

- il peut être visible dans la recherche ;
- il ne peut pas être ajouté au panier ;
- le bouton de vente doit être désactivé ;
- une alerte de rupture ou stock faible peut être affichée.

## 10.4 Stock faible

Un produit est en stock faible si son stock disponible est inférieur ou égal à son seuil minimum.

Règle :

```txt
stock_disponible <= stock_minimum
```

Une alerte doit être générée ou affichée.

## 10.5 Entrée de stock

Une entrée de stock est réservée au gérant.

Elle doit :

- créer ou modifier un lot ;
- augmenter la quantité disponible ;
- enregistrer un mouvement de stock ;
- journaliser l’action.

## 10.6 Ajustement de stock

Un ajustement de stock est réservé au gérant.

Il doit être utilisé pour corriger une différence réelle.

Il doit obligatoirement contenir un motif.

Exemples de motifs :

```txt
Correction inventaire
Produit abîmé
Erreur de saisie précédente
Perte constatée
```

## 10.7 Sortie de stock lors d’une vente

La sortie de stock est automatique après validation d’une vente.

Le vendeur ne choisit pas manuellement le lot.

L’application applique la règle FEFO.

---

# 11. Règle FEFO

## 11.1 Définition

FEFO signifie :

```txt
First Expired, First Out
```

Cela veut dire :

```txt
Le lot qui expire le plus tôt sort en premier.
```

## 11.2 Pourquoi FEFO est obligatoire

Dans une pharmacie, il faut éviter de garder les produits proches de l’expiration pendant que des produits plus récents sont vendus.

FEFO permet de réduire :

- les pertes ;
- les expirations inutiles ;
- les erreurs de gestion ;
- les risques de vendre un mauvais lot.

## 11.3 Application pratique

Exemple :

```txt
Produit : Amoxicilline
Lot A : quantité 5, expiration 2026-07-01
Lot B : quantité 20, expiration 2026-12-01
```

Si le vendeur vend 8 unités :

```txt
5 unités sortent du Lot A
3 unités sortent du Lot B
```

## 11.4 Règle stricte

Le service de vente doit toujours trier les lots disponibles par date d’expiration croissante.

Il doit ignorer :

- les lots expirés ;
- les lots avec quantité zéro ;
- les lots liés à un produit inactif.

---

# 12. Vente

## 12.1 Principe général

Une vente est une opération définitive qui diminue le stock et génère un ticket.

## 12.2 Données d’une vente

Une vente doit contenir :

- numéro de vente ;
- vendeur ;
- date et heure ;
- total ;
- montant reçu ;
- monnaie rendue ;
- lignes de vente ;
- devise CDF ;
- paiement espèces.

## 12.3 Numérotation des ventes

Format validé :

```txt
VTE-YYYY-000001
```

Exemples :

```txt
VTE-2026-000001
VTE-2026-000002
VTE-2026-000003
```

Règles :

- le numéro doit être unique ;
- le numéro doit être lisible ;
- le numéro doit apparaître sur le ticket ;
- le numéro ne doit pas être modifié après validation.

## 12.4 Panier

Avant validation, le panier doit respecter les règles suivantes :

- il ne peut pas être vide ;
- chaque quantité doit être supérieure à zéro ;
- chaque produit doit être actif ;
- chaque produit doit avoir un stock disponible suffisant ;
- aucun produit expiré ne peut être ajouté ;
- le total est calculé automatiquement.

## 12.5 Validation de vente

Avant de valider la vente, l’application doit vérifier :

1. utilisateur connecté ;
2. utilisateur autorisé à vendre ;
3. panier non vide ;
4. produits actifs ;
5. lots non expirés ;
6. stock suffisant ;
7. prix unitaires valides ;
8. total cohérent ;
9. montant reçu supérieur ou égal au total ;
10. devise CDF ;
11. paiement espèces.

## 12.6 Après validation

Après validation :

- créer l’en-tête de vente ;
- créer les lignes de vente ;
- diminuer les lots selon FEFO ;
- créer les mouvements de stock ;
- générer les alertes si nécessaire ;
- journaliser la vente ;
- imprimer le ticket si l’impression automatique est activée.

## 12.7 Vente non annulable

Aucune vente validée ne peut être annulée.

Interface interdite :

```txt
Annuler vente
Supprimer vente
Modifier vente
Retour produit
```

Ces fonctions ne doivent pas être implémentées dans cette version.

---

# 13. Facture et ticket

## 13.1 Principe

Dans SALMOSPHARM, la facture est un document généré à partir d’une vente.

Il ne faut pas créer de table `factures`.

Les données viennent de :

- `ventes` ;
- `lignes_vente` ;
- `produits` ;
- `utilisateurs` ;
- `parametres`.

## 13.2 Ticket thermique

L’impression quotidienne se fait via une imprimante thermique.

Règles :

- ticket 58 mm ou 80 mm ;
- imprimante configurable ;
- impression ESC/POS recommandée ;
- impression automatique configurable ;
- réimpression contrôlée ;
- message clair en cas d’échec.

## 13.3 Réimpression

Le vendeur peut réimprimer uniquement ses propres tickets.

Le gérant peut réimprimer tous les tickets.

Toute réimpression doit être journalisée.

Action de journal recommandée :

```txt
FACTURE_REIMPRIMEE
```

## 13.4 Contenu minimum du ticket

Le ticket doit contenir :

- nom de la pharmacie ;
- téléphone si configuré ;
- adresse si configurée ;
- numéro de vente ;
- date et heure ;
- nom du vendeur ;
- liste des produits ;
- quantités ;
- prix unitaires ;
- sous-totaux ;
- total ;
- montant reçu ;
- monnaie rendue ;
- devise CDF ;
- paiement espèces ;
- message de remerciement.

---

# 14. Alertes

## 14.1 Types d’alertes

Alertes principales :

- stock faible ;
- rupture ;
- expiration proche ;
- produit expiré.

## 14.2 Visibilité

Les alertes critiques doivent être visibles pour le gérant.

Elles peuvent être affichées :

- sur le dashboard ;
- dans l’écran Alertes ;
- dans l’écran Stock ;
- dans le détail du produit.

## 14.3 Alertes vendeur

Le vendeur peut voir les informations utiles à la vente :

- en stock ;
- stock faible ;
- rupture ;
- indisponible ;
- expiré.

Mais il ne peut pas gérer ou traiter les alertes administratives.

## 14.4 Génération des alertes

Les alertes peuvent être générées :

- après une vente ;
- après une entrée de stock ;
- au lancement de l’application ;
- lors de la consultation du dashboard ;
- via une tâche interne simple.

---

# 15. Rapports et statistiques

## 15.1 Principe

Les rapports sont calculés depuis les données existantes.

Il ne faut pas créer de table `rapports`.

## 15.2 Rapports du gérant

Le gérant peut consulter :

- ventes du jour ;
- ventes mensuelles ;
- ventes par vendeur ;
- produits les plus vendus ;
- synthèse du stock ;
- alertes critiques ;
- historique des actions.

## 15.3 Rapports du vendeur

Le vendeur peut consulter uniquement ses propres données :

- ventes du jour ;
- nombre de transactions ;
- total encaissé ;
- historique personnel.

## 15.4 Devise dans les rapports

Tous les rapports affichent uniquement le CDF.

---

# 16. Sauvegarde et restauration

## 16.1 Export des données

L’export des données est réservé au gérant.

Il doit générer un fichier contenant l’état des données à un instant donné.

Format recommandé :

```txt
.spharm
```

Exemple :

```txt
salmospharm_backup_2026-06-15_14-30.spharm
```

## 16.2 Contenu du backup

Le backup doit contenir :

- la base SQLite complète ;
- les assets nécessaires ;
- le logo si configuré ;
- les factures archivées si elles existent ;
- un fichier `manifest.json`.

## 16.3 Import des données

L’import est réservé au gérant.

Règles :

- vérifier que le fichier est valide ;
- vérifier le manifeste ;
- créer une sauvegarde automatique avant import ;
- remplacer les données actuelles ;
- restaurer les fichiers liés ;
- journaliser l’action ;
- redémarrer l’application après import.

## 16.4 Message d’avertissement avant import

Avant l’import, afficher un message clair :

```txt
L’importation remplacera les données actuelles de cette installation.
Une sauvegarde de sécurité sera créée avant le remplacement.
Voulez-vous continuer ?
```

## 16.5 Sauvegarde automatique

La sauvegarde automatique est validée.

Règles recommandées :

- sauvegarde quotidienne ;
- sauvegarde avant chaque import ;
- sauvegarde à la fermeture si des données ont changé ;
- conservation limitée des anciennes sauvegardes ;
- accès réservé au gérant dans l’interface.

---

# 17. Paramètres

## 17.1 Accès

Les paramètres sont réservés au gérant.

## 17.2 Paramètres généraux

Les paramètres doivent inclure :

- nom de la pharmacie ;
- téléphone ;
- adresse ;
- logo ;
- seuil d’expiration en jours ;
- thème éventuel ;
- informations d’impression ;
- sauvegarde automatique.

## 17.3 Paramètres fixes

Certains paramètres sont fixes et ne doivent pas être modifiables dans l’interface :

```txt
Devise : CDF
Paiement : Espèces uniquement
```

Ils peuvent être affichés mais pas changés.

## 17.4 Paramètres d’impression

Paramètres validés :

- nom de l’imprimante ;
- largeur ticket : 58 ou 80 mm ;
- impression automatique activée/désactivée.

## 17.5 Paramètres de sauvegarde

Paramètres recommandés :

- sauvegarde automatique activée/désactivée ;
- fréquence de sauvegarde ;
- dernière sauvegarde ;
- dossier de sauvegarde.

---

# 18. Journalisation

## 18.1 Principe

Les actions sensibles doivent être enregistrées dans `journaux_activite`.

Objectif :

- savoir qui a fait quoi ;
- savoir quand l’action a été faite ;
- faciliter le contrôle par le gérant ;
- comprendre les incidents.

## 18.2 Actions à journaliser

Actions obligatoires :

```txt
CONNEXION_REUSSIE
CONNEXION_ECHOUEE
COMPTE_GERANT_CREE
CODE_RECUPERATION_GENERE
MOT_DE_PASSE_REINITIALISE
UTILISATEUR_CREE
UTILISATEUR_MODIFIE
UTILISATEUR_DESACTIVE
UTILISATEUR_REACTIVE
PRODUIT_CREE
PRODUIT_MODIFIE
PRODUIT_DESACTIVE
STOCK_ENTREE
STOCK_AJUSTE
VENTE_VALIDEE
FACTURE_IMPRIMEE
FACTURE_REIMPRIMEE
BACKUP_EXPORTE
BACKUP_IMPORTE
SAUVEGARDE_AUTO_CREEE
PARAMETRES_MODIFIES
ERREUR_IMPRESSION
ERREUR_IMPORT_BACKUP
```

## 18.3 Données d’un journal

Chaque journal doit contenir si possible :

- utilisateur ;
- action ;
- module concerné ;
- identifiant de l’élément concerné ;
- détails lisibles ;
- date et heure.

## 18.4 Journalisation des échecs

Les échecs importants peuvent aussi être journalisés.

Exemples :

- tentative de connexion échouée ;
- import backup invalide ;
- échec d’impression ;
- tentative d’action non autorisée.

---

# 19. Gestion des erreurs

## 19.1 Principe

L’application doit afficher des erreurs simples, non techniques et utiles.

Interdit :

```txt
sqlite3.OperationalError
Traceback Python
KeyError
NullReference
Exception brute
```

Autorisé :

```txt
Impossible d’enregistrer la vente. Le stock disponible est insuffisant.
```

## 19.2 Erreurs métier fréquentes

### Stock insuffisant

```txt
Stock insuffisant pour ce produit.
```

### Produit expiré

```txt
Ce produit ne peut pas être vendu car son lot disponible est expiré.
```

### Produit en rupture

```txt
Ce produit est en rupture de stock.
```

### Panier vide

```txt
Ajoutez au moins un produit avant de valider la vente.
```

### Montant reçu insuffisant

```txt
Le montant reçu doit être supérieur ou égal au total à payer.
```

### Compte désactivé

```txt
Ce compte est désactivé. Veuillez contacter le gérant.
```

### Accès refusé

```txt
Vous n’avez pas l’autorisation d’effectuer cette action.
```

### Imprimante indisponible

```txt
Impossible d’imprimer le ticket. Vérifiez que l’imprimante est connectée et configurée.
```

### Backup invalide

```txt
Ce fichier de sauvegarde n’est pas valide pour SALMOSPHARM.
```

## 19.3 Gestion des erreurs techniques

Les erreurs techniques doivent être :

- capturées ;
- enregistrées dans un fichier de log si nécessaire ;
- transformées en message utilisateur clair ;
- non affichées sous forme brute.

---

# 20. Sécurité locale

## 20.1 Données locales

Les données sont stockées localement dans le dossier utilisateur Windows.

Chemin recommandé :

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\
```

## 20.2 Protection minimale

Même si l’application est locale, elle doit respecter une sécurité minimale :

- mots de passe hashés ;
- code de récupération hashé ;
- rôle vérifié côté service ;
- actions sensibles journalisées ;
- sauvegardes importées uniquement après validation ;
- pas de données sensibles affichées inutilement.

## 20.3 Ce qui n’est pas prévu dans cette version

Non prévu :

- chiffrement complet de la base ;
- synchronisation cloud ;
- authentification biométrique ;
- connexion multi-postes ;
- serveur distant ;
- gestion multi-pharmacies.

---

# 21. Contraintes interdites à ne jamais réintroduire

Les éléments suivants sont explicitement interdits dans cette version :

```txt
- Mode de paiement mobile
- Carte bancaire
- Multi-devise
- Table modes_paiement
- Table factures persistée
- Table rapports persistée
- Annulation de vente
- Suppression de vente validée
- Modification de vente validée
- Vente de lot expiré
- Vente de produit en rupture
- Accès vendeur aux paramètres
- Accès vendeur aux rapports globaux
- Accès vendeur à l’import/export des données
```

---

# 22. Règles pour les assistants IA, Codex et LLM

## 22.1 Respect obligatoire du métier

Avant de générer du code métier, toujours vérifier ce fichier.

Si une demande contredit ce document, il faut signaler la contradiction avant de coder.

## 22.2 Ne pas inventer de fonctionnalités

Ne pas ajouter :

- paiement mobile ;
- annulation de vente ;
- cloud ;
- API web ;
- multi-devise ;
- retours produits ;
- gestion fournisseur avancée ;
- table facture ;
- table mode paiement.

## 22.3 Centraliser la logique métier

La logique métier doit être placée dans les services.

Exemples :

```txt
vente_service.py
stock_service.py
auth_service.py
backup_service.py
impression_service.py
journal_service.py
```

L’interface ne doit pas contenir la logique critique.

## 22.4 Vérifier les permissions dans les services

Chaque action sensible doit vérifier le rôle.

Exemple :

```txt
Seul le gérant peut importer une sauvegarde.
```

Cette règle doit être vérifiée dans le service, pas seulement dans l’écran.

## 22.5 Préserver les décisions validées

Les décisions validées sont prioritaires sur les suggestions automatiques.

Si un LLM propose une meilleure pratique qui contredit les décisions validées, il ne faut pas l’appliquer sans validation humaine.

---

# 23. Résumé opérationnel

Les règles les plus importantes à retenir :

```txt
1. Application desktop locale offline-first.
2. Base SQLite locale.
3. Paiement espèces uniquement.
4. Devise CDF uniquement.
5. Deux rôles : gérant et vendeur.
6. Le gérant a accès complet.
7. Le vendeur a un accès limité.
8. Le compte gérant est créé au premier lancement.
9. Un code de récupération est fourni au gérant.
10. Les mots de passe et codes sont hashés.
11. Une vente validée est définitive.
12. Aucune annulation de transaction.
13. Les lots sortent selon FEFO.
14. Les lots expirés sont interdits à la vente.
15. Les produits en rupture sont interdits à la vente.
16. Les tickets sont imprimés sur imprimante thermique.
17. La réimpression est contrôlée selon le rôle.
18. L’export/import des données est réservé au gérant.
19. Les sauvegardes utilisent un fichier .spharm.
20. Toutes les actions sensibles sont journalisées.
```

---

# 24. Statut du document

Ce document est validé comme référence pour l’implémentation des règles métier et de la sécurité de SALMOSPHARM 133.

Tout code généré doit respecter ce document.

