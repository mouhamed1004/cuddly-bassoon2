# 🚂 Configuration Railway - Guide complet

## ❌ PROBLÈME ACTUEL
```
decouple.UndefinedValueError: SECRET_KEY not found
```

**Cause** : Les variables d'environnement ne sont pas configurées dans Railway.

---

## ✅ SOLUTION : Configurer les variables d'environnement

### **Étape 1 : Accéder aux variables Railway**

1. Allez sur **Railway Dashboard** : https://railway.app/
2. Sélectionnez votre projet **Blizz**
3. Cliquez sur votre service web
4. Allez dans l'onglet **"Variables"**

---

### **Étape 2 : Ajouter TOUTES les variables requises**

Copiez-collez ces variables dans Railway (remplacez les valeurs par les vôtres) :

#### **🔐 Variables Django essentielles**

```bash
# Django Secret Key (OBLIGATOIRE)
SECRET_KEY=votre-secret-key-ici-changez-moi

# Debug Mode (IMPORTANT : False en production)
DEBUG=False

# Hosts autorisés (Railway génère un domaine automatiquement)
ALLOWED_HOSTS=.railway.app,blizz.boutique

# Database URL (Railway PostgreSQL - sera auto-configuré)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis URL (Railway Redis - sera auto-configuré)
REDIS_URL=${{Redis.REDIS_URL}}
```

#### **☁️ Variables Cloudinary (Stockage images)**

```bash
CLOUDINARY_CLOUD_NAME=votre-cloud-name
CLOUDINARY_API_KEY=votre-api-key
CLOUDINARY_API_SECRET=votre-api-secret
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
```

#### **💳 Variables CinetPay (Paiements)**

```bash
CINETPAY_API_KEY=votre-cinetpay-api-key
CINETPAY_SITE_ID=votre-site-id
CINETPAY_SECRET_KEY=votre-cinetpay-secret
```

#### **📧 Variables Email (Optionnel mais recommandé)**

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-mot-de-passe-app
DEFAULT_FROM_EMAIL=noreply@blizz.boutique
```

#### **🌐 Variables Shopify (DÉSACTIVÉ - mais gardez-les vides)**

```bash
# Shopify désactivé - laisser vide
SHOPIFY_SHOP_NAME=
SHOPIFY_ACCESS_TOKEN=
SHOPIFY_SHOP_URL=
```

---

### **Étape 3 : Variables Railway automatiques**

Railway configure automatiquement ces variables si vous avez ajouté PostgreSQL et Redis :

```bash
# PostgreSQL (ajouté automatiquement par Railway)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (ajouté automatiquement par Railway)
REDIS_URL=${{Redis.REDIS_URL}}
```

**Comment ajouter PostgreSQL et Redis :**
1. Dans votre projet Railway
2. Cliquez sur **"+ New"**
3. Sélectionnez **"Database" → "PostgreSQL"**
4. Répétez pour **"Redis"**
5. Railway créera automatiquement les variables `DATABASE_URL` et `REDIS_URL`

---

## 🔑 Générer une SECRET_KEY sécurisée

### **Option 1 : Utiliser Python (Recommandé)**

Exécutez cette commande localement :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copiez le résultat et collez-le dans Railway comme valeur de `SECRET_KEY`.

### **Option 2 : Utiliser un générateur en ligne**

1. Allez sur : https://djecrety.ir/
2. Copiez la clé générée
3. Collez-la dans Railway

---

## 📋 CHECKLIST COMPLÈTE

### **Variables OBLIGATOIRES** ✅

- [ ] `SECRET_KEY` - Clé secrète Django
- [ ] `DEBUG` - False en production
- [ ] `ALLOWED_HOSTS` - .railway.app,blizz.boutique
- [ ] `DATABASE_URL` - ${{Postgres.DATABASE_URL}}
- [ ] `REDIS_URL` - ${{Redis.REDIS_URL}}

### **Variables Cloudinary** ✅

- [ ] `CLOUDINARY_CLOUD_NAME`
- [ ] `CLOUDINARY_API_KEY`
- [ ] `CLOUDINARY_API_SECRET`
- [ ] `CLOUDINARY_URL`

### **Variables CinetPay** ✅

- [ ] `CINETPAY_API_KEY`
- [ ] `CINETPAY_SITE_ID`
- [ ] `CINETPAY_SECRET_KEY`

### **Variables Email (Optionnel)** 📧

- [ ] `EMAIL_HOST`
- [ ] `EMAIL_PORT`
- [ ] `EMAIL_USE_TLS`
- [ ] `EMAIL_HOST_USER`
- [ ] `EMAIL_HOST_PASSWORD`
- [ ] `DEFAULT_FROM_EMAIL`

---

## 🚀 Après avoir configuré les variables

### **1. Redéployer**

Railway redéploiera automatiquement après avoir ajouté les variables.

### **2. Exécuter les migrations**

Dans Railway, allez dans l'onglet **"Settings"** → **"Deploy"** et ajoutez :

**Build Command :**
```bash
pip install -r requirements.txt
```

**Start Command :**
```bash
python manage.py migrate && gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT
```

### **3. Créer un superuser**

Dans Railway CLI ou via l'interface :

```bash
railway run python manage.py createsuperuser
```

---

## 🔍 Vérifier que tout fonctionne

### **1. Vérifier les logs**

Dans Railway Dashboard → **"Deployments"** → Cliquez sur le dernier déploiement → **"View Logs"**

Vous devriez voir :
```
✅ Starting gunicorn
✅ Listening at: http://0.0.0.0:8080
✅ Booting worker with pid: X
```

### **2. Tester le site**

Ouvrez l'URL Railway (ex: `https://votre-app.railway.app`)

---

## 📝 Exemple de configuration complète

Voici à quoi devrait ressembler votre section Variables dans Railway :

```
SECRET_KEY = django-insecure-abc123xyz789...
DEBUG = False
ALLOWED_HOSTS = .railway.app,blizz.boutique
DATABASE_URL = ${{Postgres.DATABASE_URL}}
REDIS_URL = ${{Redis.REDIS_URL}}
CLOUDINARY_CLOUD_NAME = blizz-gaming
CLOUDINARY_API_KEY = 123456789012345
CLOUDINARY_API_SECRET = abcdefghijklmnopqrstuvwxyz
CLOUDINARY_URL = cloudinary://123456789012345:abcdefghijklmnopqrstuvwxyz@blizz-gaming
CINETPAY_API_KEY = 12345678901234567890
CINETPAY_SITE_ID = 123456
CINETPAY_SECRET_KEY = abcdefghijklmnopqrstuvwxyz123456
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = contact@blizz.boutique
EMAIL_HOST_PASSWORD = votre-mot-de-passe-app
DEFAULT_FROM_EMAIL = noreply@blizz.boutique
```

---

## ⚠️ IMPORTANT : Sécurité

### **NE JAMAIS** :
- ❌ Committer le fichier `.env` dans Git
- ❌ Partager vos clés API publiquement
- ❌ Utiliser `DEBUG=True` en production
- ❌ Utiliser la même `SECRET_KEY` qu'en local

### **TOUJOURS** :
- ✅ Utiliser des variables d'environnement
- ✅ Générer une nouvelle `SECRET_KEY` pour la production
- ✅ Activer HTTPS (Railway le fait automatiquement)
- ✅ Limiter `ALLOWED_HOSTS` aux domaines autorisés

---

## 🆘 Dépannage

### **Erreur : SECRET_KEY not found**
➡️ Ajoutez `SECRET_KEY` dans les variables Railway

### **Erreur : Database connection failed**
➡️ Vérifiez que PostgreSQL est ajouté et que `DATABASE_URL` est configuré

### **Erreur : Redis connection failed**
➡️ Vérifiez que Redis est ajouté et que `REDIS_URL` est configuré

### **Erreur : Worker failed to boot**
➡️ Vérifiez les logs pour voir quelle variable manque

### **Site inaccessible**
➡️ Vérifiez que `ALLOWED_HOSTS` inclut `.railway.app`

---

## 📞 Support

Si vous avez des problèmes :

1. **Vérifiez les logs** Railway
2. **Vérifiez toutes les variables** sont configurées
3. **Redéployez** manuellement si nécessaire
4. **Contactez le support** Railway si le problème persiste

---

## ✅ Prochaines étapes

Une fois les variables configurées :

1. ✅ Railway redéploiera automatiquement
2. ✅ Exécutez les migrations
3. ✅ Créez un superuser
4. ✅ Testez le site
5. ✅ Configurez votre domaine custom (blizz.boutique)

**Bon déploiement sur Railway !** 🚂🚀
