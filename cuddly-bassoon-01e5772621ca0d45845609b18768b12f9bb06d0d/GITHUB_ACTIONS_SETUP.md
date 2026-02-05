# 🚀 Configuration GitHub Actions - Nettoyage Automatique

## 🎯 OBJECTIF
Automatiser le nettoyage des transactions abandonnées **toutes les 24h** avec GitHub Actions.

## ✅ CE QUI A ÉTÉ FAIT

### 1. 🔧 Code Implémenté
- ✅ Endpoint webhook: `/api/cleanup-transactions/`
- ✅ Workflow GitHub Actions: `.github/workflows/cleanup-transactions.yml`
- ✅ Sécurisation avec clé secrète
- ✅ Gestion d'erreurs et notifications
- ✅ Résumé automatique des résultats

### 2. 📅 Planning
- **Exécution**: Tous les jours à **02:00 UTC** (04:00 heure française)
- **Timeout**: 2 heures par défaut (configurable)
- **Déclenchement manuel**: Possible depuis GitHub

## 🚀 ÉTAPES DE CONFIGURATION

### ÉTAPE 1: Secrets GitHub

1. **Va sur ton repo GitHub**
2. **Settings** → **Secrets and variables** → **Actions**
3. **Ajoute ces secrets** :

   **RENDER_APP_URL**
   ```
   https://ton-app-name.onrender.com
   ```
   *(Remplace par ton URL Render réelle)*

   **WEBHOOK_SECRET**
   ```
   blizz-game-cleanup-2024
   ```

### ÉTAPE 2: Variables d'environnement Render

Ajoute cette variable sur Render :
```bash
WEBHOOK_SECRET=blizz-game-cleanup-2024
```

### ÉTAPE 3: Déployer le code

```bash
git add .
git commit -m "Add GitHub Actions daily cleanup workflow"
git push
```

### ÉTAPE 4: Activer le workflow

1. Va sur **GitHub** → **Actions**
2. Tu devrais voir le workflow "🧹 Nettoyage des Transactions Abandonnées"
3. Il s'exécutera automatiquement à 02:00 UTC chaque jour

## 🧪 TEST MANUEL

### Option 1: Depuis GitHub
1. Va sur **Actions** → **🧹 Nettoyage des Transactions Abandonnées**
2. Clique **Run workflow**
3. Configure le timeout si nécessaire
4. Clique **Run workflow**

### Option 2: Test local (si serveur Django actif)
```powershell
.\test_webhook.ps1
```

## 📊 MONITORING

### Voir les résultats
1. **GitHub Actions** → **Workflow runs**
2. Clique sur une exécution
3. Regarde l'onglet **Summary** pour le résumé

### En cas d'échec
- Une **issue GitHub** sera créée automatiquement
- Tu recevras une notification
- L'issue contiendra les étapes de dépannage

## 🎯 AVANTAGES

### ✅ Automatique
- Pas d'intervention manuelle
- Fonctionne même si tu dors 😴

### ✅ Fiable  
- Redémarrage automatique en cas d'échec
- Notifications d'erreur
- Logs détaillés

### ✅ Sécurisé
- Clé secrète pour authentification
- Pas d'accès non autorisé

### ✅ Gratuit
- GitHub Actions gratuit pour repos publics
- 2000 minutes/mois pour repos privés

## 🔧 PERSONNALISATION

### Changer la fréquence
Modifie dans `.github/workflows/cleanup-transactions.yml` :
```yaml
schedule:
  # Exemple: toutes les 12h
  - cron: '0 */12 * * *'
  
  # Exemple: tous les lundis à 08:00
  - cron: '0 8 * * 1'
```

### Changer le timeout
Modifie la valeur par défaut :
```yaml
default: '2'  # 2 heures
```

## 🎉 RÉSULTAT

**Tes annonces ne seront plus jamais bloquées !**

- 🔄 Nettoyage automatique quotidien
- 📊 Statistiques dans GitHub
- 🚨 Alertes en cas de problème
- 🎮 Plus de frustration pour tes utilisateurs !

---

**Prêt à déployer ? Push ton code et laisse GitHub faire le travail !** 🚀
