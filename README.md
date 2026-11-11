# RihlaSahara — Application web + mobile (Android / iOS)

Projet React + Vite, API Python/FastAPI et base SQLite. Le frontend est préparé pour Capacitor. Cette archive contient le code source : elle ne contient pas encore un APK ou un IPA compilé.

## 1. Prérequis Windows
- Node.js LTS (20 ou 22 recommandé) : https://nodejs.org/
- Python 3.11+ : https://www.python.org/downloads/
- VS Code : https://code.visualstudio.com/
- Android Studio : https://developer.android.com/studio

## 2. Démarrer en local (ordinateur)
Dans un terminal, démarrer l'API :
```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```
API : http://127.0.0.1:8000 — documentation : http://127.0.0.1:8000/docs

Dans un deuxième terminal :
```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```
Application web : http://localhost:5173

## 3. Préparer l'API pour les téléphones (indispensable)
Un téléphone ne peut pas utiliser `127.0.0.1:8000` pour joindre le PC. Il faut déployer le dossier `backend/` sur un hébergeur Python avec HTTPS et stockage persistant, puis configurer `VITE_API_URL` dans `frontend/.env` avec l'URL HTTPS réelle, par exemple `https://api.exemple.ma`.

Configurez côté serveur les variables de `backend/.env.example`. N'utilisez jamais les mots de passe de démonstration en production. Le serveur refuse maintenant de démarrer en mode production si les mots de passe ou la clé secrète par défaut sont conservés.

**Base de données :** SQLite est adaptée à une démonstration sur une seule instance avec disque persistant. Si l'hébergeur efface le disque au redémarrage ou si plusieurs instances sont utilisées, migrez vers PostgreSQL avant une mise en production.

## 4. Créer le projet Android sous Windows
La méthode la plus simple : ouvrez PowerShell dans le dossier racine du projet et exécutez :
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\prepare-android.ps1
```
Le script installe les dépendances, construit React, crée le dossier Android s'il n'existe pas, synchronise Capacitor et ouvre Android Studio.

Alternative manuelle depuis `frontend/` :
```powershell
npm install
npm run build
npx cap add android   # une seule fois
npx cap sync android
npx cap open android
```
Dans Android Studio : attendez la synchronisation Gradle, puis **Build > Build Bundle(s) / APK(s) > Build APK(s)**. Le fichier debug se trouve normalement dans `android/app/build/outputs/apk/debug/app-debug.apk`. Pour distribuer publiquement, créez une version signée (AAB recommandé pour Google Play).

## 5. Créer la version iPhone
Depuis un Mac avec Xcode :
```bash
cd frontend
npm install
npm run build
npx cap add ios   # une seule fois
npx cap sync ios
npx cap open ios
```
La signature iOS, les tests sur appareil et l'envoi vers TestFlight/App Store se font avec Xcode et un compte Apple Developer adapté. Windows seul ne compile pas directement une application iOS native.

## 6. Comptes administrateurs
- `ouhemmi.amar` — OUHEMMI AMAR
- `kaoutar.bousbibit` — KAOUTAR BOUSBIBIT

Les mots de passe de démonstration historiques doivent être remplacés via `ADMIN_AMAR_PASSWORD` et `ADMIN_KAOUTAR_PASSWORD` côté backend avant tout déploiement. Ne mettez jamais de secrets dans `frontend/.env` ni dans le code React.

## 7. Mettre à jour l'application
Après toute modification du frontend :
```powershell
cd frontend
npm run build
npx cap sync android
```
Puis reconstruisez l'APK depuis Android Studio. Les changements de données stockées par l'API (par exemple ajout d'une destination dans l'Admin) apparaissent après rechargement, sans réinstaller l'application. Les changements de code nécessitent une nouvelle compilation ou un mécanisme de mise à jour web explicitement configuré.

## 8. Fonctionnalités et limites actuelles
- Navigation, exploration, favoris, carte régionale et formulaire d'itinéraire de démonstration.
- API FastAPI, SQLite, connexion Admin et ajout/suppression de destinations.
- L'assistant n'est pas encore connecté à un vrai modèle IA.
- Pas encore de réservation réelle, comptes visiteurs, géolocalisation détaillée, notifications push ou mode hors ligne complet.
- Les destinations et contenus doivent être vérifiés avant une mise en service touristique.

## Dépannage
- `npm` introuvable : fermez/réouvrez PowerShell après installation de Node.js.
- Erreur Gradle/JDK : utilisez le JDK fourni/recommandé par Android Studio et synchronisez le projet.
- API inaccessible sur téléphone : vérifiez l'URL HTTPS `VITE_API_URL`, le déploiement backend et les journaux serveur.

## 9. Construire l'APK sans Android Studio (GitHub Actions)
1. Créez un dépôt GitHub et envoyez-y tout le contenu de ce dossier.
2. (Recommandé) Dans **Settings > Secrets and variables > Actions > Variables**, ajoutez `VITE_API_URL` = l'URL HTTPS de votre API.
3. Onglet **Actions > Build Android APK > Run workflow**.
4. Après quelques minutes, téléchargez l'artefact **RihlaSahara-apk** (contient `RihlaSahara.apk`).

## 10. Déployer l'API sur Render
Le fichier `render.yaml` est fourni (disque persistant pour SQLite, plan payant `starter`). Renseignez `ADMIN_AMAR_PASSWORD` et `ADMIN_KAOUTAR_PASSWORD` dans Render ; `RIHLASAHARA_SECRET_KEY` est généré automatiquement.
