# 🚨 URGENT: Perte de données sur Render - Solution immédiate

## 🎯 PROBLÈME CRITIQUE

**Tes données disparaissent à chaque déploiement car tu utilises SQLite au lieu de PostgreSQL !**

### Symptômes observés :
- ✅ Utilisateur `tami24` créé → ❌ Disparu après déploiement
- ✅ Images produits synchronisées → ❌ Perdues après déploiement
- ✅ Toutes les données → ❌ Réinitialisées à chaque push

### Cause :
```python
# Dans settings.py ligne 166
config('DATABASE_URL', default='sqlite:///db.sqlite3')
```
**SQLite = fichier local = disparaît à chaque redéploiement Render !**

## 🔧 SOLUTION IMMÉDIATE

### ÉTAPE 1: Créer une base PostgreSQL sur Render

1. **Va sur ton dashboard Render**
2. **Clique "New +" → "PostgreSQL"**
3. **Configure :**
   - **Name**: `blizz-database`
   - **Database**: `blizz_db`
   - **User**: `blizz_user`
   - **Region**: Même que ton web service
   - **Plan**: Starter (gratuit)

4. **Clique "Create Database"**

### ÉTAPE 2: Récupérer l'URL de connexion

1. **Clique sur ta base créée**
2. **Onglet "Connect"**
3. **Copie l'URL "External Database URL"**
   - Format: `postgresql://user:password@host:port/database`

### ÉTAPE 3: Configurer ton Web Service

1. **Va sur ton web service** (`blizz-web-service`)
2. **Onglet "Environment"**
3. **Ajoute la variable :**
   - **Key**: `DATABASE_URL`
   - **Value**: L'URL PostgreSQL copiée

### ÉTAPE 4: Redéployer

1. **Déclenche un redéploiement** (Manual Deploy)
2. **Attends la fin du déploiement**
3. **Tes données seront maintenant persistantes !**

## 🎮 RÉCUPÉRATION DES DONNÉES

### Malheureusement, les données perdues ne sont pas récupérables :
- ❌ Utilisateur `tami24` → À recréer
- ❌ Images produits → À re-synchroniser
- ❌ Toutes les données utilisateurs → Perdues

### Mais maintenant, avec PostgreSQL :
- ✅ **Données persistantes** entre déploiements
- ✅ **Sauvegardes automatiques** Render
- ✅ **Performances améliorées**
- ✅ **Prêt pour la production**

## ⚠️ ACTIONS URGENTES

1. **Configure PostgreSQL MAINTENANT** (5 minutes)
2. **Redéploie ton app**
3. **Teste la persistance** en créant un utilisateur test
4. **Re-synchronise tes produits Shopify**

## 🔍 VÉRIFICATION

Après configuration, teste :
```bash
# Sur Render, dans les logs, tu devrais voir :
"Using database: postgresql://..."
# Au lieu de :
"Using database: sqlite:///db.sqlite3"
```

---

**⏰ TEMPS ESTIMÉ : 5-10 minutes**
**🎯 PRIORITÉ : CRITIQUE - À faire immédiatement !**
