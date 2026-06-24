# Rapport de progression JUNIOR

Ce fichier suit les interventions du developpeur DEV3 sur SALMOSPHARM 133.

## Role DEV3

DEV3 est charge de la qualite, des tests, de l'impression, du backup/restauration, du build `.exe` et de l'installateur Windows.

## Regles de suivi

- Consulter les rapports disponibles dans `dev/` avant chaque implementation.
- Ne pas modifier les rapports des autres developpeurs sauf demande explicite.
- Ajouter une entree apres chaque evolution majeure DEV3.
- Indiquer la date, la phase concernee, les fichiers modifies, les validations effectuees et les limites restantes.
- Ne jamais stocker de secret, de mot de passe, de token ou de code de recuperation.

## Rapports de reference

- `dev/rapport_pistis.md` : rapport du developpeur principal.
- `dev/rapport_glody.md` : rapport du developpeur charge des interfaces, a consulter lorsqu'il existe.
- `dev/rapport_junior.md` : rapport DEV3 courant.

## 2026-06-24 - Audit DEV3 initial - Phase 21 / Packaging

### Ce qui a ete fait

- Lecture des instructions projet et documents obligatoires.
- Audit sans modification du code source.
- Verification du lancement de l'application en developpement.
- Verification de PySide6.
- Verification de la creation AppData dans un dossier temporaire.
- Verification du schema SQLite et absence des tables interdites.
- Verification des dependances de securite `passlib` / `bcrypt`.
- Verification de `build.bat`.
- Test de build PyInstaller via le Python du venv.
- Verification de la presence de `dist/SALMOSPHARM/SALMOSPHARM.exe`.
- Verification de l'inclusion des assets `logo.ico` et `logo.png`.
- Test de demarrage controle de l'executable packagé.
- Verification de `.gitignore` pour les artefacts generes.

### Constats principaux

- L'application demarre en developpement.
- PySide6 fonctionne.
- La base SQLite est creee dans AppData.
- Les 10 tables officielles sont presentes.
- Aucune table interdite n'a ete detectee.
- PyInstaller genere correctement l'executable si lance avec :

```powershell
.\.venv\Scripts\python.exe -m PyInstaller app/main.py --name SALMOSPHARM --windowed --onedir --icon app/assets/logo.ico --add-data "app/assets;assets" --noconfirm
```

### Problemes identifies

- Les tests pytest echouent actuellement a cause de l'environnement :
  - `requirements.txt` demande `bcrypt==4.0.1`
  - le venv contient `bcrypt 5.0.0`
  - `passlib 1.7.4` echoue avec cette version de `bcrypt`
- `build.bat` appelle `pyinstaller` directement au lieu du Python du venv.
- `build.bat` peut afficher un message de succes meme si PyInstaller n'est pas trouve.
- Les services DEV3 suivants ne sont pas encore implementes :
  - `app/services/ticket_service.py`
  - `app/services/impression_service.py`
  - `app/services/backup_service.py`
- L'installateur Inno Setup n'existe pas encore :
  - `installer/salmospharm.iss`

### Validations effectuees

Commandes executees :

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -c "import PySide6, sqlalchemy, passlib, bcrypt; ..."
.\.venv\Scripts\python.exe -m PyInstaller app/main.py --name SALMOSPHARM --windowed --onedir --icon app/assets/logo.ico --add-data "app/assets;assets" --noconfirm
```

Resultats :

```txt
pytest : 5 failed, 11 passed
PySide6 : OK
SQLite AppData : OK
Tables interdites : aucune detectee
Build PyInstaller via venv : OK
Executable dist/SALMOSPHARM/SALMOSPHARM.exe : OK
Assets dans le build : OK
Demarrage controle de l'exe : OK
```

### Limites restantes

- Corriger l'environnement `bcrypt` avant de valider les tests.
- Corriger `build.bat` apres feu vert.
- Ajouter les services et tests ticket/impression/backup dans les phases DEV3 prevues.
- Creer l'installateur Windows dans la phase 22.
