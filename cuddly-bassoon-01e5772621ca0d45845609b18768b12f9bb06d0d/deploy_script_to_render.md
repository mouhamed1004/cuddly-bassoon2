# 🚀 SUPPRIMER LES ANNONCES SUR RENDER

## 📋 **MÉTHODE 1 : Via l'interface Render (Recommandée)**

### **Étapes :**
1. **Aller sur** [render.com](https://render.com)
2. **Se connecter** à votre compte
3. **Sélectionner** votre service `blizz-web-service`
4. **Cliquer sur** "Shell" ou "Console"
5. **Exécuter** les commandes suivantes :

```bash
# Naviguer vers le répertoire du projet
cd /opt/render/project/src

# Exécuter le script de suppression
python delete_all_posts_render.py
```

## 📋 **MÉTHODE 2 : Via Git (Alternative)**

### **Étapes :**
1. **Pousser le script** sur GitHub :
```bash
git add delete_all_posts_render.py
git commit -m "Add script to delete all posts on Render"
git push
```

2. **Attendre le déploiement** automatique sur Render

3. **Se connecter** à Render via SSH

4. **Exécuter** le script :
```bash
python delete_all_posts_render.py
```

## ⚠️ **ATTENTION :**

- **Ce script supprime TOUTES les annonces de PRODUCTION**
- **Action IRRÉVERSIBLE**
- **Les utilisateurs verront immédiatement la différence**
- **Sauvegardez d'abord si nécessaire**

## 🔍 **VÉRIFICATION :**

Après exécution, vérifiez sur :
- `https://blizz-web-service.onrender.com/`
- La page d'accueil devrait être vide d'annonces
- L'admin Django devrait montrer 0 annonces

## 📞 **EN CAS DE PROBLÈME :**

Si le script ne fonctionne pas :
1. Vérifiez les logs Render
2. Vérifiez la connexion à la base de données
3. Contactez le support Render si nécessaire

