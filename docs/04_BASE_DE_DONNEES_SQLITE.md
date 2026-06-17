# 04 — Base de données SQLite

## Projet

**Nom du projet :** SALMOSPHARM 133  
**Type :** Application desktop de gestion de pharmacie  
**Base retenue :** SQLite  
**Langage principal :** Python  
**ORM recommandé :** SQLAlchemy  
**Migrations recommandées :** Alembic  
**Devise unique :** CDF  
**Paiement :** Espèces uniquement  
**Mode de fonctionnement :** local, desktop, offline-first

Ce document décrit la base de données SQLite à utiliser pendant l’implémentation de SALMOSPHARM. Il sert de référence pour les développeurs, Codex, les LLM et toute personne qui intervient sur le projet.

La base de données doit rester simple, robuste, locale et adaptée à une pharmacie qui utilise une seule installation de l’application sur un ordinateur Windows.

---

# 1. Objectif de la base de données

La base SQLite doit permettre de gérer :

- les utilisateurs ;
- les rôles ;
- les produits ;
- les catégories ;
- les lots de produits ;
- les mouvements de stock ;
- les ventes ;
- les lignes de vente ;
- les alertes ;
- l’historique des actions ;
- les paramètres de l’application ;
- l’impression thermique ;
- la sauvegarde et la restauration.

La base doit être conçue pour préserver l’historique métier. Une vente validée ne doit pas être modifiée, supprimée ou annulée.

---

# 2. Décisions fondamentales

## 2.1 SQLite est la base officielle de la version 1.0

SQLite est retenu parce que l’application est :

- desktop ;
- locale ;
- offline-first ;
- mono-pharmacie ;
- sans serveur distant obligatoire ;
- destinée à des utilisateurs non techniques.

Il ne faut pas introduire PostgreSQL, MySQL, Supabase ou un serveur distant dans la version 1.0, sauf décision explicite ultérieure.

## 2.2 Les tables doivent être nommées en français

Les noms de tables retenus sont en français pour faciliter la compréhension du projet par tous les développeurs.

Exemples corrects :

```txt
utilisateurs
produits
lots_produits
mouvements_stock
ventes
lignes_vente
alertes
journaux_activite
parametres
```

Exemples interdits :

```txt
users
products
sales
sale_items
settings
```

## 2.3 Les montants sont stockés en INTEGER

Tous les montants en CDF doivent être stockés en `INTEGER`.

Exemples :

```txt
500 CDF   -> 500
1500 CDF  -> 1500
25000 CDF -> 25000
```

Il ne faut pas utiliser `REAL` ou `FLOAT` pour les montants.

Raison : éviter les erreurs d’arrondi et simplifier les calculs.

## 2.4 La devise est fixe

La seule devise autorisée est :

```txt
CDF
```

La base ne doit pas contenir de logique multi-devise.

## 2.5 Le paiement est fixe

Le paiement est uniquement en espèces.

Il ne faut pas créer de table :

```txt
modes_paiement
paiements
transactions_paiement
```

Il ne faut pas stocker Orange Money, M-Pesa, Airtel Money, carte bancaire ou tout autre moyen de paiement.

## 2.6 Les factures ne sont pas une table métier principale

La facture est une représentation imprimable d’une vente.

Elle est générée à partir de :

- `ventes` ;
- `lignes_vente` ;
- `produits` ;
- `utilisateurs` ;
- `parametres`.

Il ne faut pas créer une table `factures` pour dupliquer les données des ventes.

## 2.7 Les rapports ne sont pas des tables persistées

Les rapports sont générés par requêtes SQL ou par vues.

Il ne faut pas créer de tables :

```txt
rapports
statistiques_dashboard
rapports_journaliers
rapports_mensuels
```

Les rapports doivent être calculés depuis les tables existantes.

## 2.8 Une vente validée est définitive

Dans cette version, aucune annulation de transaction n’est autorisée.

Une fois qu’une vente est validée :

- elle reste dans l’historique ;
- elle ne peut pas être supprimée ;
- elle ne peut pas être modifiée ;
- elle ne peut pas être annulée ;
- elle peut seulement être consultée ou réimprimée.

---

# 3. Tables officielles retenues

La base de données doit contenir les tables suivantes :

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

Aucune autre table majeure ne doit être ajoutée sans raison métier claire.

---

# 4. Vue d’ensemble des tables

## 4.1 `utilisateurs`

Rôle : stocker les comptes des personnes qui utilisent l’application.

Utilisateurs possibles :

- gérant ;
- vendeur.

La table permet :

- l’authentification ;
- la séparation des droits ;
- l’attribution des ventes ;
- la journalisation des actions ;
- la désactivation d’un compte sans perte d’historique.

## 4.2 `categories`

Rôle : organiser les produits en familles.

Exemples :

- Antalgiques ;
- Antibiotiques ;
- Antipaludéens ;
- Vitamines ;
- Antiseptiques.

La table permet de filtrer les produits et de produire des statistiques plus lisibles.

## 4.3 `produits`

Rôle : stocker les informations générales des produits vendus.

Cette table ne stocke pas le stock disponible total. Le stock se calcule depuis `lots_produits`.

Elle contient les informations stables :

- nom ;
- code-barres ;
- catégorie ;
- prix de vente ;
- seuil minimum ;
- statut actif/inactif.

## 4.4 `lots_produits`

Rôle : gérer les lots physiques disponibles pour chaque produit.

Un même produit peut avoir plusieurs lots, avec des dates d’expiration différentes.

Cette table est essentielle pour :

- appliquer FEFO ;
- bloquer les lots expirés ;
- suivre les quantités réelles ;
- générer les alertes d’expiration.

## 4.5 `mouvements_stock`

Rôle : tracer toutes les variations de stock.

Exemples :

- entrée de stock ;
- sortie par vente ;
- ajustement ;
- perte ;
- expiration.

Cette table permet de comprendre pourquoi une quantité a changé.

## 4.6 `ventes`

Rôle : stocker l’en-tête d’une vente validée.

Une vente représente une transaction terminée.

Elle contient :

- numéro de vente ;
- vendeur ;
- total ;
- montant reçu ;
- date de vente.

Une vente validée est définitive.

## 4.7 `lignes_vente`

Rôle : stocker les produits vendus dans une vente.

Une vente peut contenir plusieurs lignes.

Chaque ligne contient :

- produit vendu ;
- lot utilisé ;
- quantité ;
- prix unitaire au moment de la vente ;
- sous-total.

Le prix unitaire et le sous-total sont stockés volontairement pour préserver l’historique, même si le prix du produit change plus tard.

## 4.8 `alertes`

Rôle : centraliser les alertes métier.

Types d’alertes :

- stock faible ;
- expiration proche ;
- produit expiré.

Les alertes doivent être visibles dans le tableau de bord et dans l’écran Alertes.

## 4.9 `journaux_activite`

Rôle : tracer les actions importantes effectuées dans l’application.

Exemples :

- connexion réussie ;
- création d’un vendeur ;
- création d’un produit ;
- entrée de stock ;
- vente validée ;
- ticket imprimé ;
- backup exporté ;
- backup importé.

Cette table est obligatoire pour l’offre professionnelle.

## 4.10 `parametres`

Rôle : stocker les paramètres généraux de la pharmacie et de l’application.

Exemples :

- nom de la pharmacie ;
- téléphone ;
- adresse ;
- logo ;
- devise ;
- seuil d’expiration ;
- imprimante thermique ;
- largeur ticket ;
- sauvegarde automatique.

---

# 5. Schéma SQL recommandé

Le schéma ci-dessous constitue la base de référence. Il peut être adapté via SQLAlchemy/Alembic, mais les règles métier et les contraintes doivent être conservées.

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    mot_de_passe_hash TEXT NOT NULL,
    code_recuperation_hash TEXT,
    doit_changer_mot_de_passe INTEGER NOT NULL DEFAULT 0 CHECK(doit_changer_mot_de_passe IN (0, 1)),
    role TEXT NOT NULL CHECK(role IN ('GERANT', 'VENDEUR')),
    actif INTEGER NOT NULL DEFAULT 1 CHECK(actif IN (0, 1)),
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modifie_le TEXT
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL UNIQUE,
    description TEXT,
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modifie_le TEXT
);

CREATE TABLE produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categorie_id INTEGER,
    nom TEXT NOT NULL,
    code_barres TEXT UNIQUE,
    prix_vente INTEGER NOT NULL CHECK(prix_vente >= 0),
    stock_minimum INTEGER NOT NULL DEFAULT 0 CHECK(stock_minimum >= 0),
    description TEXT,
    actif INTEGER NOT NULL DEFAULT 1 CHECK(actif IN (0, 1)),
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modifie_le TEXT,
    FOREIGN KEY (categorie_id) REFERENCES categories(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE lots_produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id INTEGER NOT NULL,
    numero_lot TEXT,
    quantite INTEGER NOT NULL DEFAULT 0 CHECK(quantite >= 0),
    prix_achat INTEGER NOT NULL CHECK(prix_achat >= 0),
    date_expiration TEXT,
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modifie_le TEXT,
    UNIQUE(produit_id, numero_lot),
    FOREIGN KEY (produit_id) REFERENCES produits(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE TABLE mouvements_stock (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id INTEGER NOT NULL,
    lot_id INTEGER,
    utilisateur_id INTEGER,
    type_mouvement TEXT NOT NULL CHECK(type_mouvement IN ('ENTREE','SORTIE','AJUSTEMENT','PERTE','EXPIRATION')),
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    motif TEXT,
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produit_id) REFERENCES produits(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (lot_id) REFERENCES lots_produits(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE ventes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero_vente TEXT NOT NULL UNIQUE,
    vendeur_id INTEGER,
    total INTEGER NOT NULL CHECK(total >= 0),
    montant_recu INTEGER NOT NULL CHECK(montant_recu >= total),
    statut TEXT NOT NULL DEFAULT 'VALIDEE' CHECK(statut = 'VALIDEE'),
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendeur_id) REFERENCES utilisateurs(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE lignes_vente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vente_id INTEGER NOT NULL,
    produit_id INTEGER NOT NULL,
    lot_id INTEGER,
    quantite INTEGER NOT NULL CHECK(quantite > 0),
    prix_unitaire INTEGER NOT NULL CHECK(prix_unitaire >= 0),
    sous_total INTEGER NOT NULL CHECK(sous_total >= 0),
    FOREIGN KEY (vente_id) REFERENCES ventes(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (produit_id) REFERENCES produits(id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    FOREIGN KEY (lot_id) REFERENCES lots_produits(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE alertes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produit_id INTEGER NOT NULL,
    lot_id INTEGER,
    type_alerte TEXT NOT NULL CHECK(type_alerte IN ('STOCK_FAIBLE','EXPIRATION_PROCHE','PRODUIT_EXPIRE')),
    message TEXT,
    est_lue INTEGER NOT NULL DEFAULT 0 CHECK(est_lue IN (0, 1)),
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produit_id) REFERENCES produits(id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (lot_id) REFERENCES lots_produits(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE journaux_activite (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    utilisateur_id INTEGER,
    action TEXT NOT NULL,
    table_cible TEXT,
    element_id INTEGER,
    details TEXT,
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

CREATE TABLE parametres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_pharmacie TEXT NOT NULL,
    telephone TEXT,
    adresse TEXT,
    chemin_logo TEXT,
    devise TEXT NOT NULL DEFAULT 'CDF' CHECK(devise = 'CDF'),
    seuil_expiration_jours INTEGER NOT NULL DEFAULT 30 CHECK(seuil_expiration_jours > 0),
    nom_imprimante TEXT,
    largeur_ticket INTEGER NOT NULL DEFAULT 80 CHECK(largeur_ticket IN (58, 80)),
    impression_auto INTEGER NOT NULL DEFAULT 1 CHECK(impression_auto IN (0, 1)),
    sauvegarde_auto INTEGER NOT NULL DEFAULT 1 CHECK(sauvegarde_auto IN (0, 1)),
    frequence_sauvegarde TEXT NOT NULL DEFAULT 'QUOTIDIENNE' CHECK(frequence_sauvegarde IN ('FERMETURE','QUOTIDIENNE','MANUELLE')),
    derniere_sauvegarde TEXT,
    cree_le TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modifie_le TEXT
);
```

---

# 6. Contraintes métier par table

## 6.1 Contraintes sur `utilisateurs`

### Rôles autorisés

```txt
GERANT
VENDEUR
```

Aucun autre rôle ne doit être créé dans la version 1.0.

### Mot de passe

Le champ `mot_de_passe_hash` doit contenir uniquement un hash sécurisé.

Il est interdit de stocker :

- le mot de passe en clair ;
- un mot de passe encodé en base64 ;
- un mot de passe simplement chiffré sans hash adapté.

### Code de récupération

Le champ `code_recuperation_hash` doit contenir le hash du code de récupération.

Le code en clair doit être affiché une seule fois au gérant, au moment de la création ou de la régénération.

### Désactivation

Le champ `actif` permet de bloquer un utilisateur sans supprimer son historique.

Un vendeur désactivé ne peut pas se connecter.

## 6.2 Contraintes sur `produits`

Un produit peut être actif ou inactif.

Un produit inactif :

- ne doit pas être vendu ;
- peut rester visible dans l’historique ;
- peut être masqué des recherches courantes.

Le stock disponible ne doit pas être stocké dans cette table.

## 6.3 Contraintes sur `lots_produits`

Un lot représente une quantité physique.

Un lot expiré ne peut pas être vendu.

Un lot dont la quantité est `0` ne peut pas être utilisé pour une vente.

La combinaison suivante doit rester unique :

```txt
produit_id + numero_lot
```

## 6.4 Contraintes sur `mouvements_stock`

Types autorisés :

```txt
ENTREE
SORTIE
AJUSTEMENT
PERTE
EXPIRATION
```

Une vente doit générer un mouvement de type :

```txt
SORTIE
```

Une entrée de marchandise doit générer un mouvement de type :

```txt
ENTREE
```

Une correction manuelle de stock doit générer un mouvement de type :

```txt
AJUSTEMENT
```

Il ne faut pas créer de mouvement `RETOUR_VENTE`, car l’annulation de vente n’est pas autorisée.

## 6.5 Contraintes sur `ventes`

Une vente validée est définitive.

Le statut est toujours :

```txt
VALIDEE
```

Le champ est conservé uniquement pour garder une structure évolutive.

Le montant reçu doit être supérieur ou égal au total.

La monnaie rendue n’est pas stockée. Elle est calculée :

```txt
montant_recu - total
```

## 6.6 Contraintes sur `lignes_vente`

Chaque ligne doit conserver :

- le produit vendu ;
- le lot utilisé ;
- la quantité vendue ;
- le prix unitaire au moment de la vente ;
- le sous-total.

Même si le prix du produit change plus tard, les lignes de vente passées ne doivent pas changer.

## 6.7 Contraintes sur `alertes`

Types autorisés :

```txt
STOCK_FAIBLE
EXPIRATION_PROCHE
PRODUIT_EXPIRE
```

Les alertes peuvent être marquées comme lues, mais ne doivent pas forcément être supprimées.

## 6.8 Contraintes sur `journaux_activite`

Toutes les actions sensibles doivent être enregistrées.

La journalisation doit contenir au minimum :

- utilisateur concerné ;
- action ;
- table ou module cible ;
- identifiant de l’élément si disponible ;
- détails lisibles ;
- date et heure.

## 6.9 Contraintes sur `parametres`

Il doit y avoir un seul enregistrement principal de paramètres dans la version 1.0.

La devise doit toujours être :

```txt
CDF
```

La largeur ticket doit être :

```txt
58
```

ou :

```txt
80
```

---

# 7. Index recommandés

Les index sont nécessaires pour garder une application fluide lorsque les données augmentent.

```sql
CREATE INDEX idx_utilisateurs_role ON utilisateurs(role);
CREATE INDEX idx_utilisateurs_actif ON utilisateurs(actif);

CREATE INDEX idx_produits_nom ON produits(nom);
CREATE INDEX idx_produits_code_barres ON produits(code_barres);
CREATE INDEX idx_produits_categorie ON produits(categorie_id);
CREATE INDEX idx_produits_actif ON produits(actif);

CREATE INDEX idx_lots_produits_produit ON lots_produits(produit_id);
CREATE INDEX idx_lots_produits_expiration ON lots_produits(date_expiration);
CREATE INDEX idx_lots_produits_quantite ON lots_produits(quantite);

CREATE INDEX idx_mouvements_stock_produit ON mouvements_stock(produit_id);
CREATE INDEX idx_mouvements_stock_lot ON mouvements_stock(lot_id);
CREATE INDEX idx_mouvements_stock_utilisateur ON mouvements_stock(utilisateur_id);
CREATE INDEX idx_mouvements_stock_date ON mouvements_stock(cree_le);
CREATE INDEX idx_mouvements_stock_type ON mouvements_stock(type_mouvement);

CREATE INDEX idx_ventes_vendeur ON ventes(vendeur_id);
CREATE INDEX idx_ventes_date ON ventes(cree_le);
CREATE INDEX idx_ventes_numero ON ventes(numero_vente);

CREATE INDEX idx_lignes_vente_vente ON lignes_vente(vente_id);
CREATE INDEX idx_lignes_vente_produit ON lignes_vente(produit_id);
CREATE INDEX idx_lignes_vente_lot ON lignes_vente(lot_id);

CREATE INDEX idx_alertes_produit ON alertes(produit_id);
CREATE INDEX idx_alertes_lot ON alertes(lot_id);
CREATE INDEX idx_alertes_est_lue ON alertes(est_lue);
CREATE INDEX idx_alertes_date ON alertes(cree_le);
CREATE INDEX idx_alertes_type ON alertes(type_alerte);

CREATE INDEX idx_journaux_utilisateur ON journaux_activite(utilisateur_id);
CREATE INDEX idx_journaux_date ON journaux_activite(cree_le);
CREATE INDEX idx_journaux_table_cible ON journaux_activite(table_cible);
CREATE INDEX idx_journaux_action ON journaux_activite(action);
```

---

# 8. Vues SQL recommandées

Les vues permettent de simplifier les requêtes de lecture sans dupliquer les données.

## 8.1 Vue du stock par produit

```sql
CREATE VIEW vue_stock_produits AS
SELECT
    p.id AS produit_id,
    p.nom AS produit,
    p.stock_minimum,
    COALESCE(SUM(
        CASE
            WHEN lp.date_expiration IS NULL OR DATE(lp.date_expiration) >= DATE('now')
            THEN lp.quantite
            ELSE 0
        END
    ), 0) AS stock_disponible,
    CASE
        WHEN COALESCE(SUM(
            CASE
                WHEN lp.date_expiration IS NULL OR DATE(lp.date_expiration) >= DATE('now')
                THEN lp.quantite
                ELSE 0
            END
        ), 0) <= p.stock_minimum THEN 1
        ELSE 0
    END AS stock_faible
FROM produits p
LEFT JOIN lots_produits lp ON lp.produit_id = p.id
WHERE p.actif = 1
GROUP BY p.id;
```

Cette vue ignore les quantités des lots expirés.

## 8.2 Vue des lots disponibles

```sql
CREATE VIEW vue_lots_disponibles AS
SELECT
    lp.id AS lot_id,
    p.id AS produit_id,
    p.nom AS produit,
    lp.numero_lot,
    lp.quantite,
    lp.date_expiration,
    lp.prix_achat
FROM lots_produits lp
JOIN produits p ON p.id = lp.produit_id
WHERE p.actif = 1
  AND lp.quantite > 0
  AND (lp.date_expiration IS NULL OR DATE(lp.date_expiration) >= DATE('now'))
ORDER BY DATE(lp.date_expiration) ASC;
```

Cette vue aide à appliquer FEFO.

## 8.3 Vue facture/ticket

```sql
CREATE VIEW vue_facture AS
SELECT
    v.id AS vente_id,
    v.numero_vente,
    v.cree_le AS date_vente,
    u.nom AS vendeur,
    p.nom AS produit,
    lv.quantite,
    lv.prix_unitaire,
    lv.sous_total,
    v.total,
    v.montant_recu,
    (v.montant_recu - v.total) AS monnaie_rendue,
    'CDF' AS devise,
    'Espèces' AS mode_paiement
FROM ventes v
LEFT JOIN utilisateurs u ON u.id = v.vendeur_id
JOIN lignes_vente lv ON lv.vente_id = v.id
JOIN produits p ON p.id = lv.produit_id;
```

Cette vue sert à générer les tickets thermiques et les éventuels PDF d’archivage.

## 8.4 Vue rapport journalier par vendeur

```sql
CREATE VIEW vue_rapport_journalier_vendeur AS
SELECT
    DATE(v.cree_le) AS date_vente,
    u.id AS vendeur_id,
    u.nom AS vendeur,
    COUNT(v.id) AS nombre_ventes,
    SUM(v.total) AS total_ventes,
    'CDF' AS devise
FROM ventes v
LEFT JOIN utilisateurs u ON u.id = v.vendeur_id
WHERE v.statut = 'VALIDEE'
GROUP BY DATE(v.cree_le), u.id;
```

## 8.5 Vue rapport mensuel

```sql
CREATE VIEW vue_rapport_mensuel AS
SELECT
    strftime('%Y-%m', v.cree_le) AS mois,
    COUNT(v.id) AS nombre_ventes,
    SUM(v.total) AS total_ventes,
    'CDF' AS devise
FROM ventes v
WHERE v.statut = 'VALIDEE'
GROUP BY strftime('%Y-%m', v.cree_le);
```

## 8.6 Vue produits les plus vendus

```sql
CREATE VIEW vue_produits_plus_vendus AS
SELECT
    p.id AS produit_id,
    p.nom AS produit,
    SUM(lv.quantite) AS quantite_vendue,
    SUM(lv.sous_total) AS montant_total
FROM lignes_vente lv
JOIN produits p ON p.id = lv.produit_id
JOIN ventes v ON v.id = lv.vente_id
WHERE v.statut = 'VALIDEE'
GROUP BY p.id
ORDER BY quantite_vendue DESC;
```

---

# 9. Données initiales recommandées

## 9.1 Paramètres initiaux

Au premier lancement, après création de la base, insérer un enregistrement dans `parametres`.

```sql
INSERT INTO parametres (
    nom_pharmacie,
    telephone,
    adresse,
    devise,
    seuil_expiration_jours,
    largeur_ticket,
    impression_auto,
    sauvegarde_auto,
    frequence_sauvegarde
) VALUES (
    'SALMOSPHARM 133',
    NULL,
    NULL,
    'CDF',
    30,
    80,
    1,
    1,
    'QUOTIDIENNE'
);
```

## 9.2 Catégories initiales

```sql
INSERT INTO categories (nom, description) VALUES
('Antalgiques', 'Médicaments contre la douleur'),
('Antibiotiques', 'Médicaments contre les infections bactériennes'),
('Antipaludéens', 'Médicaments contre le paludisme'),
('Vitamines', 'Compléments vitaminiques'),
('Antiseptiques', 'Produits de désinfection');
```

## 9.3 Compte gérant initial

Le compte gérant ne doit pas être inséré en dur dans le script SQL.

Au premier lancement :

1. l’application vérifie s’il existe au moins un utilisateur ;
2. si aucun utilisateur n’existe, elle affiche l’écran de création du compte gérant ;
3. le mot de passe est hashé ;
4. un code de récupération est généré ;
5. le code de récupération est hashé ;
6. le code en clair est affiché une seule fois au gérant.

---

# 10. Numérotation des ventes

Le format officiel est :

```txt
VTE-YYYY-000001
```

Exemple :

```txt
VTE-2026-000001
VTE-2026-000002
VTE-2026-000003
```

La numérotation doit être générée par le service de vente, pas directement par l’interface.

Il ne faut pas permettre à l’utilisateur de modifier manuellement un numéro de vente.

La stratégie recommandée :

- récupérer le dernier numéro de vente de l’année en cours ;
- incrémenter la partie numérique ;
- générer le nouveau numéro ;
- vérifier l’unicité avant insertion.

---

# 11. Règle FEFO

FEFO signifie :

```txt
First Expired, First Out
```

En français :

```txt
Le lot qui expire le plus tôt doit sortir en premier.
```

Lors d’une vente, si un produit possède plusieurs lots disponibles :

1. exclure les lots expirés ;
2. exclure les lots avec quantité égale à zéro ;
3. trier les lots par date d’expiration croissante ;
4. retirer la quantité demandée depuis le ou les lots nécessaires.

Exemple :

```txt
Produit : Paracétamol 500 mg
Quantité vendue : 12

Lots disponibles :
Lot A : 5 unités, expire le 2026-07-01
Lot B : 10 unités, expire le 2026-10-01

Sortie :
Lot A : 5 unités
Lot B : 7 unités
```

Le service de vente doit créer les lignes de vente et mouvements de stock correspondants.

---

# 12. Gestion des lots expirés

Un lot est expiré si :

```txt
date_expiration < date du jour
```

Un lot expiré :

- ne doit pas être vendu ;
- ne doit pas contribuer au stock disponible vendable ;
- doit générer une alerte `PRODUIT_EXPIRE` ;
- peut rester dans l’historique.

Un produit peut être affiché dans la recherche même s’il possède des lots expirés, mais il ne doit être vendable que s’il possède au moins un lot valide avec quantité disponible.

---

# 13. Gestion des alertes

Les alertes doivent être générées ou mises à jour dans les cas suivants :

## 13.1 Stock faible

Si le stock disponible vendable d’un produit est inférieur ou égal à son `stock_minimum`, créer une alerte :

```txt
STOCK_FAIBLE
```

## 13.2 Expiration proche

Si un lot expire dans un délai inférieur ou égal à `seuil_expiration_jours`, créer une alerte :

```txt
EXPIRATION_PROCHE
```

## 13.3 Produit expiré

Si un lot est déjà expiré, créer une alerte :

```txt
PRODUIT_EXPIRE
```

## 13.4 Éviter les doublons excessifs

Le système doit éviter de créer plusieurs alertes identiques pour le même produit/lot sans raison.

Approche recommandée :

- vérifier si une alerte non lue du même type existe déjà ;
- si elle existe, ne pas créer de doublon ;
- sinon, créer une nouvelle alerte.

---

# 14. Journalisation obligatoire

Les actions suivantes doivent être enregistrées dans `journaux_activite` :

```txt
CONNEXION_REUSSIE
CONNEXION_ECHOUEE
COMPTE_GERANT_CREE
CODE_RECUPERATION_GENERE
MOT_DE_PASSE_REINITIALISE
UTILISATEUR_CREE
UTILISATEUR_MODIFIE
UTILISATEUR_DESACTIVE
PRODUIT_CREE
PRODUIT_MODIFIE
STOCK_ENTREE
STOCK_AJUSTE
VENTE_VALIDEE
FACTURE_IMPRIMEE
FACTURE_REIMPRIMEE
BACKUP_EXPORTE
BACKUP_IMPORTE
SAUVEGARDE_AUTO_CREEE
PARAMETRES_MODIFIES
```

Chaque entrée doit avoir des détails compréhensibles.

Exemple :

```txt
Action : VENTE_VALIDEE
Table cible : ventes
Element ID : 24
Détails : Vente VTE-2026-000024 validée par le vendeur Jean Mukendi pour un total de 15000 CDF.
```

---

# 15. Transactions SQLite obligatoires

Les opérations critiques doivent être exécutées dans une transaction.

## 15.1 Vente

La validation d’une vente doit être atomique.

Cela signifie que toutes les étapes réussissent ensemble ou échouent ensemble :

1. vérifier le panier ;
2. vérifier le vendeur ;
3. vérifier le stock ;
4. créer la vente ;
5. créer les lignes de vente ;
6. décrémenter les lots ;
7. créer les mouvements de stock ;
8. créer les alertes si nécessaire ;
9. journaliser la vente.

Si une étape échoue, aucune modification ne doit être conservée.

## 15.2 Entrée de stock

L’entrée de stock doit aussi être transactionnelle :

1. créer ou mettre à jour le lot ;
2. enregistrer le mouvement `ENTREE` ;
3. mettre à jour les alertes ;
4. journaliser l’action.

## 15.3 Import de backup

L’import de backup doit suivre un processus sécurisé :

1. vérifier le fichier ;
2. créer une sauvegarde de sécurité ;
3. remplacer la base ;
4. restaurer les fichiers annexes ;
5. journaliser l’import après redémarrage si possible.

---

# 16. Connexion SQLite

À chaque connexion SQLite, il faut activer les clés étrangères.

```sql
PRAGMA foreign_keys = ON;
```

Avec SQLAlchemy, cette règle doit être appliquée automatiquement à l’ouverture de la connexion.

Exemple conceptuel :

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

---

# 17. Chemin de la base SQLite

La base ne doit pas être stockée dans `Program Files`.

Chemin recommandé :

```txt
C:\Users\<Utilisateur>\AppData\Local\SALMOSPHARM\data\salmospharm.sqlite3
```

Raisons :

- éviter les problèmes de permission Windows ;
- permettre les sauvegardes ;
- permettre la restauration ;
- séparer l’application installée des données utilisateur.

---

# 18. Sauvegarde de la base

La base SQLite doit être sauvegardée avec l’API officielle de backup de SQLite, pas par simple copie pendant que l’application tourne.

Approche recommandée :

```python
source.backup(destination)
```

Le fichier exporté `.spharm` doit contenir une copie cohérente de la base.

---

# 19. Restauration de la base

L’import d’un backup `.spharm` remplace la base actuelle.

Avant remplacement, l’application doit créer automatiquement une sauvegarde de sécurité.

Le fichier importé doit être validé :

- présence de `manifest.json` ;
- présence de la base SQLite ;
- nom du projet correct ;
- version de backup compatible.

---

# 20. Règles d’accès aux données par rôle

## 20.1 Gérant

Le gérant peut accéder à toutes les données :

- produits ;
- stock ;
- ventes ;
- vendeurs ;
- rapports ;
- alertes ;
- paramètres ;
- backup ;
- historique.

## 20.2 Vendeur

Le vendeur peut accéder uniquement à :

- son tableau de bord ;
- nouvelle vente ;
- historique de ses ventes ;
- recherche produit ;
- tickets liés à ses ventes.

Le vendeur ne doit pas pouvoir :

- créer un produit ;
- modifier un produit ;
- modifier le stock ;
- créer un vendeur ;
- accéder aux paramètres ;
- exporter les données ;
- importer les données ;
- voir tous les rapports ;
- consulter tout l’historique système.

Ces restrictions doivent être appliquées dans les services, pas seulement dans l’interface.

---

# 21. Ce que la base ne doit pas contenir

Ne pas créer les tables suivantes dans la version 1.0 :

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

Ces tables peuvent être envisagées dans une version future, mais elles ne font pas partie du périmètre validé.

---

# 22. Recommandations SQLAlchemy

Même si le SQL brut est décrit dans ce document, l’implémentation doit idéalement utiliser SQLAlchemy.

Organisation recommandée :

```txt
app/database/models.py
app/database/session.py
app/database/init_db.py
app/repositories/
app/services/
```

Les modèles SQLAlchemy doivent respecter les noms de tables en français.

Exemple :

```python
class Utilisateur(Base):
    __tablename__ = "utilisateurs"
```

Il est interdit de nommer la table SQL :

```python
__tablename__ = "users"
```

---

# 23. Recommandations Alembic

Alembic doit être utilisé pour faire évoluer la base sans tout casser.

Règles :

- toute modification de schéma doit passer par une migration ;
- ne pas supprimer brutalement une colonne contenant des données ;
- prévoir des migrations réversibles quand c’est possible ;
- tester les migrations sur une copie de base avant livraison.

---

# 24. Tests obligatoires liés à la base

Les tests suivants sont obligatoires avant livraison :

## 24.1 Utilisateurs

- créer un gérant ;
- créer un vendeur ;
- refuser un rôle invalide ;
- bloquer un vendeur désactivé ;
- vérifier le hash du mot de passe ;
- vérifier le hash du code de récupération.

## 24.2 Produits et stock

- créer une catégorie ;
- créer un produit ;
- créer plusieurs lots ;
- calculer le stock disponible ;
- exclure les lots expirés ;
- déclencher une alerte stock faible ;
- déclencher une alerte expiration proche.

## 24.3 Vente

- créer une vente valide ;
- refuser une vente avec panier vide ;
- refuser une vente avec stock insuffisant ;
- refuser une vente avec lot expiré ;
- appliquer FEFO ;
- décrémenter les bons lots ;
- créer les lignes de vente ;
- créer les mouvements de stock ;
- créer le journal d’activité ;
- vérifier que la vente ne peut pas être annulée.

## 24.4 Rapports

- vérifier le rapport journalier vendeur ;
- vérifier le rapport mensuel ;
- vérifier les produits les plus vendus ;
- vérifier les montants en CDF.

## 24.5 Backup

- exporter la base ;
- restaurer la base ;
- vérifier que les données restaurées sont identiques ;
- vérifier qu’un fichier invalide est refusé.

---

# 25. Checklist pour Codex ou LLM

Avant de générer du code lié à la base, vérifier :

```txt
- Les noms de tables sont en français.
- SQLite est utilisé.
- Les montants sont en INTEGER.
- La devise reste CDF.
- Aucun mode de paiement multiple n’est ajouté.
- Aucune table modes_paiement n’est créée.
- Aucune table factures n’est créée.
- Aucune table rapports n’est créée.
- Une vente validée est définitive.
- Les lots expirés sont exclus de la vente.
- FEFO est respecté.
- Les actions sensibles sont journalisées.
- Les permissions sont appliquées côté service.
- Les opérations critiques utilisent une transaction.
- PRAGMA foreign_keys = ON est activé.
```

---

# 26. Résumé décisionnel

La base de données officielle de SALMOSPHARM 133 version 1.0 est une base SQLite locale, stockée dans le dossier utilisateur Windows.

Elle repose sur dix tables principales :

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

Les principes non négociables sont :

```txt
SQLite local
Tables en français
Montants en INTEGER CDF
Paiement espèces uniquement
Aucune annulation de vente
Pas de table factures
Pas de table modes_paiement
Pas de table rapports
Stock par lots
FEFO obligatoire
Blocage des lots expirés
Journalisation obligatoire
Backup/restauration sécurisé
```

Ce document doit être respecté strictement pendant l’implémentation.
