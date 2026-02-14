# Guide de déploiement BLIZZ sur Sevalla

Ce guide décrit les étapes pour héberger l'application BLIZZ sur [Sevalla](https://sevalla.com/).

---

## Prérequis

- Compte Sevalla ([app.sevalla.com](https://app.sevalla.com))
- Méthode de paiement configurée
- Repository Git (GitHub, GitLab ou Bitbucket) avec le code BLIZZ

---

## Étape 1 : Créer la base PostgreSQL

1. Va dans **Databases** → **Create database**
2. Configure :
   - **Type** : PostgreSQL (version 15 ou 16 recommandée)
   - **Database name** : `blizz_db` (ou laisser le nom suggéré)
   - **Database user** : laisser générer
   - **Database password** : laisser générer
   - **Location** : choisir la même région que l'application (ex. Europe West)
3. Clique sur **Create database**
4. **Note** : tu récupéreras `DATABASE_URL` plus tard via la connexion interne

---

## Étape 2 : Créer Redis

1. Va dans **Databases** → **Create database**
2. Configure :
   - **Type** : Redis (version 7.x)
   - **Name** : `blizz-redis`
   - **Location** : **MÊME RÉGION** que PostgreSQL et l'application
3. Clique sur **Create database**

> ⚠️ **Important** : PostgreSQL, Redis et l'application doivent être dans la **même région** pour activer les connexions internes (réseau privé, sans frais de trafic).

---

## Étape 3 : Créer l'application

1. Va dans **Applications** → **Create** → **Application**
2. Source :
   - **Repository URL** : `https://github.com/TON_USERNAME/cuddly-bassoon` (ton repo)
   - **Branch** : `main` (ou ta branche principale)
   - Active **Auto-deploy** si tu veux un déploiement à chaque push
3. Nom : `blizz` (ou `blizzgame`)
4. **Location** : même région que PostgreSQL et Redis
5. **Resource** : au minimum S1 (0.5 CPU / 1 GB RAM) ; pour la prod, S2 ou plus
6. Clique sur **Create application**

---

## Étape 4 : Configurer le Build

1. Dans l'application → **Settings** → **Build**
2. **Build strategy** : Nixpacks (défaut) ou Dockerfile
3. **Build path** : `.` (racine du dépôt)
4. Si tu utilises un **Dockerfile** (recommandé pour plus de contrôle) :
   - **Dockerfile path** : `Dockerfile`
   - **Context** : `.`

### Option A : Utiliser Nixpacks (sans Dockerfile)

Ajoute un fichier `nixpacks.toml` à la racine (optionnel) pour personnaliser le build.

### Option B : Créer un Dockerfile (recommandé)

Crée un fichier `Dockerfile` à la racine du projet (voir section ci-dessous).

---

## Étape 5 : Commande de démarrage (Web Process)

1. Va dans **Processes** → **Web process** → **Update process**
2. **Custom start command** :
   ```bash
   python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
   Ou plus simple (si collectstatic est fait au build) :
   ```bash
   gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

> Le port est fourni par Sevalla via `$PORT` (généralement 8080).

---

## Étape 6 : Connexions internes (PostgreSQL + Redis)

1. Dans l'application → **Settings** → **Networking** (ou **Connections**)
2. Ajoute une **connexion privée** vers la base PostgreSQL
3. Ajoute une **connexion privée** vers Redis
4. Sevalla va automatiquement injecter `DATABASE_URL` et `REDIS_URL` (ou variables équivalentes) dans les variables d'environnement

Si les noms de variables diffèrent, configure-les manuellement dans **Environment variables**.

---

## Étape 7 : Variables d'environnement

1. Va dans **Environment variables**
2. Ajoute les variables suivantes :

| Variable | Valeur | Notes |
|----------|--------|-------|
| `SECRET_KEY` | *(générer une clé Django)* | `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `False` | |
| `ALLOWED_HOSTS` | `*` ou `.sevalla.com,ton-domaine.com` | |
| `CINETPAY_API_KEY` | *(ta clé CinetPay)* | |
| `CINETPAY_SITE_ID` | *(ton site ID)* | |
| `CINETPAY_SECRET_KEY` | *(ton secret)* | |
| `EMAIL_HOST_USER` | *(ton email Gmail)* | |
| `EMAIL_HOST_PASSWORD` | *(mot de passe d'application Gmail)* | |
| `CLOUDINARY_URL` | *(ton URL Cloudinary)* | Ex: `cloudinary://api_key:api_secret@cloud_name` |
| `BASE_URL` | `https://ton-app-xxx.sevalla.com` | URL finale de ton app |
| `ENVIRONMENT` | `production` | |
| `WEBHOOK_SECRET` | *(clé secrète pour le webhook cleanup)* | |

`DATABASE_URL` et `REDIS_URL` sont normalement fournis automatiquement par les connexions internes.

---

## Étape 8 : Job de migration (recommandé)

Pour exécuter les migrations **avant** le démarrage du web process :

1. Va dans **Processes** → **Create new process** → **Job**
2. **Name** : `migrate`
3. **Custom start command** : `python manage.py migrate --noinput`
4. **Start policy** : **Before deployment**
5. Clique sur **Create process**

Ainsi, les migrations s’exécutent avant chaque déploiement.

---

## Étape 9 : Domaine personnalisé (optionnel)

1. Va dans **Domains**
2. Ajoute ton domaine (ex. `blizz.tondomaine.com`)
3. Configure les enregistrements DNS (CNAME ou A) selon les instructions Sevalla
4. Mets à jour `ALLOWED_HOSTS` et `BASE_URL` en conséquence

---

## Étape 10 : GitHub Actions (nettoyage des transactions)

1. Dans GitHub → **Settings** → **Secrets and variables** → **Actions**
2. Modifie ou ajoute :
   - `RENDER_APP_URL` → remplace par l’URL Sevalla : `https://ton-app-xxx.sevalla.com`
   - `WEBHOOK_SECRET` → même valeur que dans les variables d’environnement Sevalla

Le workflow `.github/workflows/cleanup-transactions.yml` continuera d’appeler `/api/cleanup-transactions/` sur ta nouvelle URL.

---

## Dockerfile recommandé

Si tu choisis d’utiliser un Dockerfile pour un build plus prévisible, crée ce fichier à la racine :

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dépendances système pour psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Collecte des statiques au build
RUN python manage.py collectstatic --noinput || true

# Port exposé
ENV PORT=8080
EXPOSE $PORT

# Démarrage
CMD gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

Puis dans Sevalla :
- **Settings** → **Build** → **Update build strategy**
- Choisis **Dockerfile**
- **Dockerfile path** : `Dockerfile`
- **Context** : `.`

---

## Récapitulatif des services Sevalla

| Service | Statut |
|---------|--------|
| 1 Application (Python/Django) | À créer |
| 1 PostgreSQL | À créer |
| 1 Redis | À créer |
| Connexions internes | À configurer |
| Variables d'environnement | À renseigner |
| Job migrate (optionnel) | Recommandé |
| Domaine personnalisé | Optionnel |

---

## Ressources utiles

- [Documentation Sevalla](https://docs.sevalla.com/)
- [Django sur Sevalla](https://docs.sevalla.com/quick-starts/python/django)
- [Ajouter une base de données](https://docs.sevalla.com/databases/get-started/add-a-database)
- [Connexions internes](https://docs.sevalla.com/applications/networking)
