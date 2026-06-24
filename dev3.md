# DEV — TESTS, IMPRESSION ET PACKAGING

## Projet

**Nom du projet :** SALMOSPHARM 133  
**Type :** application desktop Windows de gestion de pharmacie  
**Responsabilité :** tests, impression thermique, backup/restauration, build `.exe`, installateur Windows  
**Rôle de ce document :** guider le développeur chargé de rendre l'application testable, imprimable et livrable.

Ce document concerne le développeur responsable de la qualité, de l'impression et de la livraison.

---

# 1. Mission principale

Tu dois t'assurer que l'application ne reste pas seulement du code qui marche sur le PC du développeur.

Ton travail est de vérifier que SALMOSPHARM 133 peut réellement être :

```txt
- lancé ;
- testé ;
- transformé en .exe ;
- installé sur Windows ;
- utilisé sans Python ;
- connecté à une imprimante thermique ;
- sauvegardé ;
- restauré ;
- livré au client proprement.
```

Tu travailles sur :

- les tests manuels ;
- les tests pytest ;
- les tickets thermiques ;
- l'aperçu ticket ;
- l'impression 58 mm / 80 mm ;
- les erreurs d'impression ;
- le backup `.spharm` ;
- la restauration ;
- PyInstaller ;
- Inno Setup ;
- les tests sur PC propre ;
- la checklist de livraison.

---

# 2. Fichiers à lire avant de coder

Lire dans cet ordre :

```txt
AGENTS.md
CODEX_PHASES.md
docs/01_CONTEXTE_ET_OBJECTIFS.md
docs/02_ARCHITECTURE_ET_STACK.md
docs/03_REGLES_METIER_ET_SECURITE.md
docs/04_BASE_DE_DONNEES_SQLITE.md
docs/05_MODULES_UI_LIVRAISON.md
```

Tu dois surtout comprendre :

- l'impression thermique ;
- le backup/restauration ;
- les tests progressifs ;
- le packaging Windows ;
- les règles métier critiques à tester.

---

# 3. Ce que tu ne dois pas faire

Tu ne dois pas changer les règles métier.

Interdit :

```txt
- ajouter paiement mobile ;
- ajouter carte bancaire ;
- ajouter multi-devise ;
- ajouter annulation de vente ;
- créer table factures ;
- créer table rapports ;
- créer table modes_paiement ;
- modifier les ventes validées ;
- supprimer des ventes ;
- faire échouer une vente parce que l'imprimante ne marche pas ;
- écraser les données client lors d'une mise à jour.
```

---

# 4. Principe de travail

Tu dois appliquer cette logique :

```txt
Tester tôt, tester souvent.
```

Ne pas attendre la fin pour générer l'exécutable.

Dès la mini fenêtre PySide6, tu dois tester :

```txt
Python → PySide6 → PyInstaller → .exe
```

Ensuite, dès que possible :

```txt
.exe → Inno Setup → installateur → test sur Windows propre
```

---

# 5. Étapes de travail

## Étape 1 — Premier test de lancement

Objectif : vérifier que l'application démarre en mode développement.

Commande :

```bash
python app/main.py
```

À vérifier :

```txt
[ ] la fenêtre s'ouvre ;
[ ] aucun terminal d'erreur ne s'affiche ;
[ ] le bouton Quitter fonctionne ;
[ ] l'application se ferme proprement.
```

Si PySide6 manque :

```bash
pip install PySide6
```

---

## Étape 2 — Premier build `.exe`

Créer ou maintenir :

```txt
build.bat
```

Commande PyInstaller recommandée :

```bat
pyinstaller app/main.py ^
  --name SALMOSPHARM ^
  --windowed ^
  --onedir ^
  --add-data "app/assets;assets"
```

À vérifier :

```txt
[ ] le dossier dist/SALMOSPHARM existe ;
[ ] SALMOSPHARM.exe existe ;
[ ] double-clic sur SALMOSPHARM.exe fonctionne ;
[ ] aucune console noire inutile ne s'ouvre ;
[ ] l'application ne demande pas Python.
```

Si PyInstaller manque :

```bash
pip install pyinstaller
```

Si erreur avec PySide6, chercher :

```txt
PyInstaller PySide6 Windows missing platform plugin qwindows
```

---

## Étape 3 — Vérification des assets dans le build

Objectif : vérifier que les images, icônes et styles sont inclus.

À tester :

```txt
[ ] logo affiché en mode développement ;
[ ] logo affiché dans le .exe ;
[ ] fichier QSS chargé en mode développement ;
[ ] fichier QSS chargé dans le .exe ;
[ ] icône de fenêtre correcte si disponible.
```

Si un asset marche en développement mais pas dans le `.exe`, vérifier la fonction de chemin ressource.

Chercher :

```txt
PyInstaller sys._MEIPASS resource path Python
```

---

## Étape 4 — Installateur Inno Setup minimal

Créer :

```txt
installer/salmospharm.iss
```

Objectif : produire :

```txt
SALMOSPHARM_Setup.exe
```

L'installateur doit :

```txt
- installer l'application dans Program Files ;
- créer un raccourci bureau ;
- créer une entrée menu démarrer ;
- lancer l'application après installation si possible ;
- ne pas écraser AppData.
```

Ne jamais stocker la base client dans Program Files.

Si tu ne connais pas Inno Setup, chercher :

```txt
Inno Setup PyInstaller onedir installer example
```

---

## Étape 5 — Tests AppData

À tester après installation :

```txt
[ ] l'application crée AppData/Local/SALMOSPHARM ;
[ ] le dossier data/ existe ;
[ ] le dossier backups/ existe ;
[ ] le dossier logs/ existe ;
[ ] le dossier factures/ existe ;
[ ] l'application ne tente pas d'écrire dans Program Files ;
[ ] la base SQLite est dans AppData.
```

Test important :

1. installer l'application ;
2. lancer ;
3. créer quelques données ;
4. fermer ;
5. relancer ;
6. vérifier que les données existent encore.

---

## Étape 6 — Tests pytest

Créer ou compléter :

```txt
tests/test_auth_service.py
tests/test_permissions.py
tests/test_stock_service.py
tests/test_vente_service.py
tests/test_backup_service.py
tests/test_ticket_service.py
```

Commande :

```bash
pytest
```

Tests prioritaires :

```txt
[ ] mot de passe hashé ;
[ ] connexion gérant valide ;
[ ] mauvais mot de passe refusé ;
[ ] vendeur désactivé refusé ;
[ ] vendeur ne peut pas accéder aux actions gérant ;
[ ] stock insuffisant refusé ;
[ ] lot expiré refusé ;
[ ] FEFO fonctionne ;
[ ] vente valide décrémente les bons lots ;
[ ] vente non annulable ;
[ ] backup exporté ;
[ ] backup invalide refusé.
```

Si tu ne sais pas utiliser pytest, chercher :

```txt
pytest beginner tutorial Python fixtures tmp_path
```

---

## Étape 7 — Service de ticket

Créer ou compléter :

```txt
app/services/ticket_service.py
```

Objectif : générer le contenu du ticket.

Le ticket doit contenir :

```txt
- nom pharmacie ;
- téléphone si disponible ;
- adresse si disponible ;
- numéro vente ;
- date et heure ;
- vendeur ;
- liste produits ;
- quantité ;
- prix unitaire ;
- sous-total ;
- total ;
- montant reçu ;
- monnaie rendue ;
- devise CDF ;
- paiement Espèces ;
- message de remerciement.
```

Règle : le ticket est généré depuis les données de vente. Il ne faut pas créer une table `factures`.

---

## Étape 8 — Aperçu ticket

Avec le Dev UI, créer ou connecter :

```txt
app/ui/components/ticket_preview.py
```

À tester :

```txt
[ ] ticket lisible ;
[ ] format 58 mm possible ;
[ ] format 80 mm possible ;
[ ] montants affichés en CDF ;
[ ] paiement affiché Espèces ;
[ ] aucun mode de paiement alternatif.
```

---

## Étape 9 — Impression thermique

Créer ou compléter :

```txt
app/services/impression_service.py
```

Bibliothèques possibles :

```txt
pywin32
python-escpos
```

À gérer :

```txt
- imprimante non configurée ;
- imprimante introuvable ;
- imprimante hors ligne ;
- papier terminé ;
- échec d'impression ;
- permission Windows insuffisante.
```

Règle critique :

```txt
Une vente validée ne doit jamais être annulée parce que l'impression échoue.
```

En cas d'échec :

```txt
- afficher un message propre ;
- journaliser ERREUR_IMPRESSION si possible ;
- permettre la réimpression.
```

Si tu ne sais pas imprimer sous Windows, chercher :

```txt
python pywin32 print raw text to Windows printer
python-escpos Windows USB printer example
```

---

## Étape 10 — Réimpression

Règles :

```txt
- le vendeur réimprime seulement ses propres tickets ;
- le gérant réimprime tous les tickets ;
- chaque réimpression est journalisée ;
- la vente reste inchangée.
```

Action de journal recommandée :

```txt
FACTURE_REIMPRIMEE
```

---

## Étape 11 — Backup export

Avec le Dev socle critique, créer ou compléter :

```txt
app/services/backup_service.py
```

Export attendu :

```txt
salmospharm_backup_YYYY-MM-DD_HH-MM.spharm
```

Contenu :

```txt
backup.spharm
├── database/
│   └── salmospharm.sqlite3
├── assets/
├── factures/
└── manifest.json
```

Règles :

- réservé au gérant ;
- utiliser l'API SQLite `backup()` ;
- ne pas copier brutalement la base active ;
- journaliser `BACKUP_EXPORTE`.

Si tu ne sais pas utiliser l'API backup SQLite, chercher :

```txt
Python sqlite3 backup database example
```

---

## Étape 12 — Backup import

Règles :

```txt
1. vérifier que le fichier .spharm est valide ;
2. lire manifest.json ;
3. vérifier que la base est présente ;
4. créer une sauvegarde de sécurité avant import ;
5. remplacer les données ;
6. restaurer assets/factures ;
7. journaliser BACKUP_IMPORTE ;
8. redémarrer l'application.
```

Message avant import :

```txt
L'import remplacera les données actuelles de cette installation.
Une sauvegarde de sécurité sera créée avant le remplacement.
Voulez-vous continuer ?
```

Tests :

```txt
[ ] export depuis une installation ;
[ ] import sur une autre installation ;
[ ] données restaurées ;
[ ] fichier invalide refusé ;
[ ] sauvegarde de sécurité créée avant import ;
[ ] vendeur interdit d'import/export.
```

---

# 6. Checklist de test par version

## Version 0.1 — Mini fenêtre

```txt
[ ] python app/main.py fonctionne ;
[ ] build.bat fonctionne ;
[ ] SALMOSPHARM.exe s'ouvre.
```

## Version 0.2 — AppData

```txt
[ ] dossiers AppData créés ;
[ ] pas d'écriture dans Program Files ;
[ ] exe fonctionne encore.
```

## Version 0.3 — SQLite

```txt
[ ] base créée ;
[ ] tables créées ;
[ ] aucune table interdite ;
[ ] exe fonctionne encore.
```

## Version 0.4 — Auth

```txt
[ ] premier gérant créé ;
[ ] code récupération affiché ;
[ ] connexion OK ;
[ ] mauvais mot de passe refusé.
```

## Version 0.5 — Stock

```txt
[ ] produit créé ;
[ ] lot créé ;
[ ] stock calculé ;
[ ] lot expiré bloqué.
```

## Version 0.6 — Vente FEFO

```txt
[ ] vente valide ;
[ ] stock diminué ;
[ ] FEFO respecté ;
[ ] vente non annulable.
```

## Version 0.7 — Impression

```txt
[ ] ticket généré ;
[ ] aperçu lisible ;
[ ] impression testée ;
[ ] échec impression géré.
```

## Version 0.8 — Backup

```txt
[ ] export .spharm ;
[ ] manifest présent ;
[ ] import OK ;
[ ] fichier invalide refusé.
```

## Version 1.0 — Livraison

```txt
[ ] installateur généré ;
[ ] installation sur PC propre ;
[ ] pas besoin de Python ;
[ ] données conservées après réinstallation ;
[ ] test complet validé.
```

---

# 7. Prompt Codex conseillé pour ce rôle

```txt
Lis AGENTS.md, CODEX_PHASES.md et les fichiers docs/.

Tu travailles sur les tests, l'impression, le backup/restauration, PyInstaller et l'installateur Windows de SALMOSPHARM 133.

Avant de modifier le code, explique ce que tu vas faire, les fichiers concernés, les commandes à lancer et les tests attendus.

Ne change pas les règles métier.
Ne crée pas de table interdite.
Ne fais jamais échouer ou annuler une vente validée parce que l'impression échoue.
Ne stocke pas les données client dans Program Files.
Ne livre jamais le code source au client final.
Travaille par petites étapes testables.
À la fin de chaque étape, donne une checklist de validation.
```

---

# 8. Critères d'acceptation finaux

Ton travail est acceptable si :

```txt
[ ] l'application se lance en développement ;
[ ] le build .exe fonctionne ;
[ ] l'installateur Windows fonctionne ;
[ ] l'application installée ne demande pas Python ;
[ ] les données vont dans AppData ;
[ ] les assets sont inclus dans le build ;
[ ] les tickets sont générés proprement ;
[ ] l'impression thermique est prévue ;
[ ] les erreurs d'impression sont propres ;
[ ] l'échec d'impression n'annule pas une vente ;
[ ] l'export .spharm fonctionne ;
[ ] l'import .spharm fonctionne ;
[ ] une sauvegarde de sécurité est créée avant import ;
[ ] les tests critiques existent ;
[ ] la checklist de livraison est validée sur Windows propre.
```

---

# 9. Résumé

Tu es responsable de la preuve que le logiciel est réellement livrable.

Une fonctionnalité n'est pas terminée seulement parce qu'elle marche dans l'éditeur.

Elle est terminée quand :

```txt
- elle marche en développement ;
- elle marche dans le .exe ;
- elle ne casse pas les données ;
- elle est testable ;
- elle peut être utilisée par le client sans outil technique.
```
