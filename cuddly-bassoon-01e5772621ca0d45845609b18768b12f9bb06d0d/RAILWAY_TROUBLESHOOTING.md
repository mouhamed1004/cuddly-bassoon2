# 🚂 Railway - Dépannage des erreurs courantes

## ✅ PROBLÈMES RÉSOLUS

### 1. ❌ `SECRET_KEY not found`
**Erreur** :
```
decouple.UndefinedValueError: SECRET_KEY not found
```

**Solution** : Ajouter les variables d'environnement dans Railway
- Railway Dashboard → Votre service → Variables
- Ajouter `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, etc.
- Voir `RAILWAY_SETUP.md` pour la liste complète

---

### 2. ❌ `FileNotFoundError: /app/logs/django.log`
**Erreur** :
```
FileNotFoundError: [Errno 2] No such file or directory: '/app/logs/django.log'
ValueError: Unable to configure handler 'file'
```

**Cause** : Django essaie d'écrire dans un fichier log mais le dossier `logs/` n'existe pas sur Railway

**Solution** : ✅ **CORRIGÉ** dans `settings.py`
- Suppression du handler `file` du LOGGING
- Utilisation uniquement de `console` (StreamHandler)
- Railway capture automatiquement les logs console

**Commit** : `fix: Suppression logging fichier pour Railway - Console uniquement`

---

## 📋 CHECKLIST DE DÉPLOIEMENT RAILWAY

### **Avant de déployer** ✅

- [ ] Code poussé sur GitHub
- [ ] PostgreSQL ajouté dans Railway
- [ ] Redis ajouté dans Railway
- [ ] Variables d'environnement configurées

### **Variables OBLIGATOIRES** ✅

```bash
SECRET_KEY=<votre-secret-key>
DEBUG=False
ALLOWED_HOSTS=.railway.app,votre-domaine.com
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
```

### **Variables Cloudinary** ☁️

```bash
CLOUDINARY_CLOUD_NAME=<votre-cloud-name>
CLOUDINARY_API_KEY=<votre-api-key>
CLOUDINARY_API_SECRET=<votre-api-secret>
CLOUDINARY_URL=cloudinary://...
```

### **Variables CinetPay** 💳

```bash
CINETPAY_API_KEY=<votre-api-key>
CINETPAY_SITE_ID=<votre-site-id>
CINETPAY_SECRET_KEY=<votre-secret>
```

---

## 🔍 VÉRIFIER LE DÉPLOIEMENT

### **Logs de succès** ✅

```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
[INFO] Booting worker with pid: 2
```

**Pas d'erreur** = Déploiement réussi ! 🎉

### **Logs d'erreur** ❌

#### Erreur : Variable manquante
```
decouple.UndefinedValueError: XXX not found
```
➡️ Ajouter la variable `XXX` dans Railway Variables

#### Erreur : Database connection
```
django.db.utils.OperationalError: could not connect to server
```
➡️ Vérifier que PostgreSQL est ajouté et `DATABASE_URL` configuré

#### Erreur : Redis connection
```
redis.exceptions.ConnectionError
```
➡️ Vérifier que Redis est ajouté et `REDIS_URL` configuré

---

## 🚀 APRÈS LE DÉPLOIEMENT

### **1. Exécuter les migrations**

Dans Railway CLI ou via l'interface :

```bash
railway run python manage.py migrate
```

Ou ajoutez dans **Settings → Deploy** :

**Start Command** :
```bash
python manage.py migrate && gunicorn socialgame.wsgi:application --bind 0.0.0.0:$PORT
```

### **2. Créer un superuser**

```bash
railway run python manage.py createsuperuser
```

### **3. Collecter les fichiers statiques (si nécessaire)**

```bash
railway run python manage.py collectstatic --noinput
```

---

## 📊 MONITORING

### **Vérifier les logs en temps réel**

Railway Dashboard → Deployments → Cliquez sur le dernier → View Logs

### **Métriques**

Railway Dashboard → Votre service → Metrics
- CPU usage
- Memory usage
- Network traffic

---

## 💰 COÛTS RAILWAY

### **Plan gratuit** (Hobby)
- $5 de crédit/mois
- 500h de runtime
- PostgreSQL inclus
- Redis inclus

### **Plan Pro**
- $20/mois
- Runtime illimité
- Plus de ressources

### **Estimation pour Blizz**
- **Démarrage** : $0-5/mois (gratuit)
- **Croissance** : $20-30/mois

---

## 🆘 SUPPORT

### **Documentation Railway**
- https://docs.railway.app/

### **Discord Railway**
- https://discord.gg/railway

### **Support**
- support@railway.app

---

## 📝 NOTES IMPORTANTES

### **Logging**
- ✅ Railway capture automatiquement les logs console
- ✅ Pas besoin de fichiers logs
- ✅ Logs disponibles dans le dashboard

### **Fichiers statiques**
- Railway peut servir les fichiers statiques
- Ou utiliser Cloudinary (recommandé pour les images)
- Ou utiliser un CDN externe

### **Base de données**
- PostgreSQL géré par Railway
- Backups automatiques
- Pas besoin de maintenance

### **Redis**
- Redis géré par Railway
- Pas de configuration nécessaire
- Juste utiliser `${{Redis.REDIS_URL}}`

---

## ✅ RÉSUMÉ

### **Problèmes résolus** ✅
1. ✅ SECRET_KEY manquante → Variables ajoutées
2. ✅ Logs fichier erreur → Console uniquement

### **Configuration actuelle** ✅
- ✅ Logging console uniquement
- ✅ PostgreSQL configuré
- ✅ Redis configuré
- ✅ Variables d'environnement prêtes

### **Prochaines étapes** 🚀
1. Railway redéploie automatiquement (2-3 min)
2. Vérifier les logs (pas d'erreur)
3. Exécuter les migrations
4. Créer un superuser
5. Tester le site

**Votre site devrait être en ligne maintenant !** 🎉
