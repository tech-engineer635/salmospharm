# DEV — INTERFACE PYSIDE6

## Projet

**Nom du projet :** SALMOSPHARM 133  
**Type :** application desktop Windows de gestion de pharmacie  
**Stack UI :** Python, PySide6, QSS  
**Rôle de ce document :** guider le développeur chargé de l'interface et aider Codex à produire des écrans propres sans casser la logique métier.

Ce document concerne le développeur responsable de l'interface utilisateur.

---

# 1. Mission principale

Tu es responsable de l'interface graphique de SALMOSPHARM 133.

Ton objectif est de créer une application claire, simple, professionnelle et utilisable par des personnes non techniques.

Tu gères principalement :

- les écrans PySide6 ;
- les layouts ;
- les composants réutilisables ;
- la sidebar gérant ;
- la sidebar vendeur ;
- la topbar ;
- le style QSS ;
- les formulaires ;
- les tableaux ;
- les messages d'erreur utilisateur ;
- l'intégration progressive avec les services métier ;
- les tests visuels et fonctionnels de base.

---

# 2. Ce que tu ne dois pas faire

Tu ne dois pas coder la logique métier critique.

Interdit dans l'UI :

```txt
- modifier directement SQLite ;
- écrire des requêtes SQL dans les écrans ;
- appliquer FEFO dans un widget ;
- décrémenter le stock depuis un bouton ;
- créer une vente directement depuis l'UI sans passer par vente_service ;
- vérifier les permissions uniquement par masquage de boutons ;
- importer/exporter les données depuis l'UI sans passer par backup_service ;
- afficher une stack trace Python à l'utilisateur.
```

L'interface appelle les services. Les services font le vrai travail.

---

# 3. Fichiers à lire avant de coder

Lire dans cet ordre :

```txt
AGENTS.md
CODEX_PHASES.md
docs/01_CONTEXTE_ET_OBJECTIFS.md
docs/02_ARCHITECTURE_ET_STACK.md
docs/03_REGLES_METIER_ET_SECURITE.md
docs/05_MODULES_UI_LIVRAISON.md
```

Pour la base de données, lire seulement si nécessaire :

```txt
docs/04_BASE_DE_DONNEES_SQLITE.md
```

Tu dois comprendre les règles métier, mais tu ne dois pas modifier la base directement.

---

# 4. Architecture UI attendue

Structure recommandée :

```txt
app/ui/
├── __init__.py
├── login/
│   ├── __init__.py
│   └── login_window.py
├── first_run/
│   ├── __init__.py
│   └── first_run_window.py
├── layouts/
│   ├── __init__.py
│   ├── main_layout.py
│   ├── gerant_layout.py
│   ├── vendeur_layout.py
│   ├── sidebar.py
│   └── topbar.py
├── components/
│   ├── __init__.py
│   ├── buttons.py
│   ├── inputs.py
│   ├── data_table.py
│   ├── stat_card.py
│   ├── badge_status.py
│   ├── confirm_dialog.py
│   ├── error_box.py
│   ├── empty_state.py
│   └── ticket_preview.py
├── gerant/
│   ├── dashboard_page.py
│   ├── produits_page.py
│   ├── ventes_page.py
│   ├── rapports_page.py
│   ├── vendeurs_page.py
│   ├── historique_page.py
│   ├── alertes_page.py
│   └── parametres_page.py
└── vendeur/
    ├── dashboard_page.py
    ├── nouvelle_vente_page.py
    ├── recherche_produit_page.py
    ├── historique_ventes_page.py
    └── factures_page.py
```

Cette structure peut évoluer légèrement, mais elle doit rester lisible.

---

# 5. Règles d'interface

L'interface doit être :

```txt
- claire ;
- moderne ;
- simple ;
- médicale ;
- professionnelle ;
- lisible ;
- adaptée à des utilisateurs non techniques.
```

Éviter :

```txt
- trop de couleurs ;
- trop de boutons ;
- menus complexes ;
- messages techniques ;
- écrans surchargés ;
- choix de paiement ;
- choix de devise.
```

Règles fixes :

```txt
Paiement : Espèces uniquement
Devise : CDF uniquement
```

L'interface ne doit jamais proposer d'autre mode de paiement.

---

# 6. Étapes de travail

## Étape 1 — Mini fenêtre PySide6

Objectif : vérifier que PySide6 fonctionne.

Dans `app/main.py`, afficher une fenêtre simple :

```txt
SALMOSPHARM 133
Application lancée avec succès
Bouton Quitter
```

Test :

```bash
python app/main.py
```

Critère de validation : la fenêtre s'ouvre sans erreur.

---

## Étape 2 — Layout principal vide

Créer :

```txt
app/ui/layouts/main_layout.py
app/ui/layouts/sidebar.py
app/ui/layouts/topbar.py
```

Le layout doit contenir :

```txt
- sidebar gauche ;
- topbar ;
- zone centrale ;
- indication discrète de version.
```

Ne pas encore connecter la base.

Utiliser de fausses pages simples pour tester la navigation.

---

## Étape 3 — Composants réutilisables

Créer progressivement les composants :

```txt
Button
Input
SearchInput
DataTable
StatCard
BadgeStatus
ConfirmDialog
ErrorBox
EmptyState
TicketPreview
```

Règle : ne pas dupliquer le même style dans chaque écran.

Si tu ne sais pas créer un composant PySide6, chercher :

```txt
PySide6 custom QWidget component example
```

---

## Étape 4 — Écran de premier lancement

Créer :

```txt
app/ui/first_run/first_run_window.py
```

Champs attendus :

```txt
- nom complet ;
- email ou identifiant ;
- mot de passe ;
- confirmation du mot de passe ;
- bouton créer compte gérant.
```

L'écran ne doit pas hasher lui-même le mot de passe. Il doit appeler le service d'authentification.

Exemple conceptuel :

```python
resultat = auth_service.creer_premier_gerant(...)
```

Après création, afficher le code de récupération une seule fois.

---

## Étape 5 — Écran de connexion

Créer :

```txt
app/ui/login/login_window.py
```

Champs :

```txt
- identifiant/email ;
- mot de passe ;
- bouton Connexion ;
- lien Mot de passe oublié.
```

Le bouton Connexion doit appeler :

```python
auth_service.connecter(...)
```

L'UI doit gérer proprement les erreurs :

```txt
Identifiant ou mot de passe incorrect.
Ce compte est désactivé. Veuillez contacter le gérant.
```

Ne jamais afficher :

```txt
Traceback
sqlite3.Error
NoneType error
```

---

## Étape 6 — Layout gérant

Créer :

```txt
app/ui/layouts/gerant_layout.py
```

Sidebar gérant recommandée :

```txt
- Tableau de bord
- Produits
- Ventes
- Factures / Tickets
- Rapports
- Vendeurs
- Historique
- Alertes
- Paramètres
- Déconnexion
```

Le gérant a accès complet, mais les actions dangereuses doivent demander confirmation.

---

## Étape 7 — Layout vendeur

Créer :

```txt
app/ui/layouts/vendeur_layout.py
```

Sidebar vendeur recommandée :

```txt
- Tableau de bord
- Nouvelle vente
- Recherche produit
- Historique des ventes
- Factures / Tickets
- Déconnexion
```

Le vendeur ne doit pas voir :

```txt
- Produits administration ;
- Stock administration ;
- Rapports globaux ;
- Vendeurs ;
- Historique complet ;
- Paramètres ;
- Backup/import/export.
```

---

## Étape 8 — Dashboard gérant

Créer :

```txt
app/ui/gerant/dashboard_page.py
```

Données à afficher plus tard via services :

```txt
- ventes du jour ;
- nombre de transactions ;
- produits en stock faible ;
- produits proches expiration ;
- produits les plus vendus ;
- synthèse par vendeur ;
- activités récentes.
```

Au début, utiliser des données fictives.

Ensuite remplacer par :

```python
rapport_service.get_dashboard_gerant(...)
```

---

## Étape 9 — Dashboard vendeur

Créer :

```txt
app/ui/vendeur/dashboard_page.py
```

Données :

```txt
- ventes du jour du vendeur connecté ;
- nombre de transactions personnelles ;
- total encaissé ;
- dernières ventes personnelles.
```

Le vendeur ne voit pas les chiffres globaux de la pharmacie.

---

## Étape 10 — Écran Produits

Créer :

```txt
app/ui/gerant/produits_page.py
```

Fonctions :

```txt
- lister les produits ;
- rechercher ;
- filtrer par catégorie ;
- ajouter produit ;
- modifier produit ;
- désactiver produit ;
- voir lots ;
- entrée stock ;
- ajustement stock.
```

Règle : toutes les actions appellent les services.

Exemples :

```python
produit_service.creer_produit(...)
stock_service.entrer_stock(...)
stock_service.ajuster_stock(...)
```

---

## Étape 11 — Écran Nouvelle vente

Créer :

```txt
app/ui/vendeur/nouvelle_vente_page.py
```

L'écran doit être rapide :

```txt
- recherche produit ;
- liste des produits disponibles ;
- panier ;
- total ;
- montant reçu ;
- monnaie rendue ;
- bouton Encaisser ;
- aperçu ticket après validation.
```

L'écran ne choisit pas les lots. Le service de vente applique FEFO.

Le bouton Encaisser appelle :

```python
vente_service.valider_vente(...)
```

Si la vente réussit, afficher le ticket et proposer l'impression.

---

## Étape 12 — Historique des ventes

Créer :

```txt
app/ui/vendeur/historique_ventes_page.py
app/ui/gerant/ventes_page.py
```

Règles :

- gérant voit toutes les ventes ;
- vendeur voit seulement ses ventes ;
- aucune vente ne peut être modifiée ;
- aucune vente ne peut être annulée ;
- aucune vente ne peut être supprimée.

---

## Étape 13 — Paramètres

Créer :

```txt
app/ui/gerant/parametres_page.py
```

Sections :

```txt
- Informations pharmacie ;
- Impression ;
- Sauvegarde/restauration ;
- Sécurité.
```

Afficher éventuellement :

```txt
Devise : CDF
Paiement : Espèces uniquement
```

Mais ne pas permettre de modifier ces deux éléments.

---

# 7. Messages utilisateur recommandés

Utiliser des messages simples.

Exemples :

```txt
Stock insuffisant pour ce produit.
Ce produit est en rupture de stock.
Ce produit ne peut pas être vendu car son lot est expiré.
Le montant reçu doit être supérieur ou égal au total.
Vous n'avez pas l'autorisation d'effectuer cette action.
Impossible d'imprimer le ticket. Vérifiez l'imprimante.
```

Ne jamais afficher les erreurs techniques directement.

---

# 8. Tests UI à faire

À chaque écran :

```txt
[ ] l'écran s'ouvre sans erreur ;
[ ] les boutons sont visibles ;
[ ] les champs sont lisibles ;
[ ] les messages d'erreur sont compréhensibles ;
[ ] la navigation fonctionne ;
[ ] le vendeur ne voit pas les menus du gérant ;
[ ] le gérant voit les modules administratifs ;
[ ] l'application reste utilisable en fenêtre normale ;
[ ] aucun écran ne propose un autre mode de paiement ;
[ ] aucun écran ne propose une autre devise.
```

À tester aussi avec l'exécutable généré.

---

# 9. Prompt Codex conseillé pour ce rôle

```txt
Lis AGENTS.md, CODEX_PHASES.md et les fichiers docs/ nécessaires.

Tu travailles uniquement sur l'interface PySide6 de SALMOSPHARM 133.

Avant de coder, explique l'écran ou le composant que tu vas créer, les fichiers concernés et les services qui seront appelés.

Ne modifie pas la base de données.
Ne crée pas de requêtes SQL dans l'UI.
Ne code pas FEFO dans un écran.
Ne décrémente jamais le stock depuis un widget.
Ne crée pas de paiement mobile, multi-devise, annulation de vente ou API web.
Utilise des données fictives au début si les services ne sont pas prêts.
Ensuite, connecte progressivement les vrais services.
À la fin, donne les tests manuels à faire.
```

---

# 10. Critères d'acceptation finaux

Ton travail est acceptable si :

```txt
[ ] l'application a une interface claire ;
[ ] la navigation gérant fonctionne ;
[ ] la navigation vendeur fonctionne ;
[ ] les rôles ont des menus séparés ;
[ ] les écrans principaux existent ;
[ ] les formulaires sont lisibles ;
[ ] les erreurs sont propres ;
[ ] l'UI appelle les services ;
[ ] l'UI ne touche pas directement à SQLite ;
[ ] aucune logique FEFO n'est dans les widgets ;
[ ] aucun écran ne propose un paiement interdit ;
[ ] aucun écran ne propose une devise interdite ;
[ ] l'exe affiche correctement l'interface.
```

---

# 11. Résumé

Tu construis l'expérience utilisateur.

Ton objectif est de rendre le logiciel simple à utiliser, mais sans casser l'architecture.

La règle la plus importante :

```txt
L'interface affiche et déclenche les actions.
Les services décident et modifient les données.
```
