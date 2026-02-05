# 📊 GUIDE DE MONITORING - BLIZZ GAMING

## 🎯 Objectif

Le script `monitor_activity.py` permet de surveiller l'activité de votre plateforme en temps réel.

---

## 🚀 UTILISATION SUR RENDER

### **Méthode 1 : Via le Shell Render (RECOMMANDÉ)**

1. **Aller sur le dashboard Render**
   - https://dashboard.render.com
   - Sélectionner votre service "blizz-web-service"

2. **Ouvrir le Shell**
   - Cliquer sur "Shell" dans le menu de gauche
   - Attendre que le terminal s'ouvre

3. **Lancer le script**
   ```bash
   python3 monitor_activity.py
   ```

4. **Voir les résultats**
   - Le script affiche toutes les statistiques
   - Scroll pour voir toutes les sections

---

### **Méthode 2 : Via SSH (si configuré)**

```bash
# Se connecter à Render
render ssh

# Lancer le script
python3 monitor_activity.py
```

---

### **Méthode 3 : Via les logs (automatique)**

Vous pouvez aussi créer une commande Django pour l'exécuter automatiquement.

---

## 📊 INFORMATIONS AFFICHÉES

### **1. Statistiques globales**
- Nombre total d'utilisateurs
- Utilisateurs avec email vérifié
- Utilisateurs actifs (24h et 7 jours)
- Nombre d'annonces (total et en vente)
- Nombre de transactions (total et complétées)

### **2. Inscriptions récentes (24h)**
- Liste des nouveaux utilisateurs
- Email et date d'inscription
- Statut de vérification email
- Dernière activité

### **3. Utilisateurs actifs (24h)**
- Qui a été actif récemment
- Type d'activité (annonce, message, transaction)
- Quand (il y a X minutes/heures)

### **4. Annonces créées (24h)**
- Nouvelles annonces
- Vendeur, jeu, prix
- Statut (en vente ou non)

### **5. Transactions (24h)**
- Nouvelles transactions
- Acheteur, vendeur, montant
- Statut de la transaction

### **6. Tendances (7 jours)**
- Inscriptions par jour
- Évolution sur la semaine

---

## 🔄 FRÉQUENCE D'UTILISATION

### **Première semaine (post-lancement)**
- ✅ Toutes les 2-3 heures
- ✅ Vérifier s'il y a de nouveaux utilisateurs
- ✅ Surveiller les premières transactions

### **Après la première semaine**
- ✅ 2-3 fois par jour
- ✅ Matin, midi, soir

### **En régime de croisière**
- ✅ 1 fois par jour
- ✅ Ou quand vous voulez vérifier l'activité

---

## 📈 INTERPRÉTATION DES RÉSULTATS

### **Scénario 1 : Aucune inscription**
```
❌ Aucune inscription dans les dernières 24h
```

**Actions :**
- Intensifier le marketing
- Vérifier que le site est accessible
- Partager plus sur les réseaux sociaux

---

### **Scénario 2 : Inscriptions mais pas d'activité**
```
✅ 5 inscription(s) récente(s)
❌ Aucun utilisateur actif dans les dernières 24h
```

**Actions :**
- Les gens s'inscrivent mais ne font rien
- Améliorer l'onboarding
- Envoyer un email de bienvenue
- Créer plus d'annonces vous-même (pour remplir le site)

---

### **Scénario 3 : Activité mais pas de transactions**
```
✅ 10 utilisateur(s) actif(s)
✅ 5 annonce(s) créée(s)
❌ Aucune transaction dans les dernières 24h
```

**Actions :**
- Les gens créent des annonces mais n'achètent pas
- Vérifier les prix (trop élevés ?)
- Améliorer la confiance (ajouter des témoignages)
- Créer des annonces attractives

---

### **Scénario 4 : Tout fonctionne ! 🎉**
```
✅ 15 inscription(s) récente(s)
✅ 20 utilisateur(s) actif(s)
✅ 12 annonce(s) créée(s)
✅ 3 transaction(s)
```

**Actions :**
- Continuer le marketing
- Engager avec la communauté
- Optimiser ce qui fonctionne

---

## 🎯 OBJECTIFS PAR PÉRIODE

### **Semaine 1 (Lancement)**
- 🎯 10-20 inscriptions
- 🎯 5-10 annonces créées
- 🎯 1-3 transactions

### **Semaine 2-4**
- 🎯 50-100 inscriptions
- 🎯 30-50 annonces
- 🎯 10-20 transactions

### **Mois 2-3**
- 🎯 200-500 inscriptions
- 🎯 100-200 annonces
- 🎯 50-100 transactions

---

## 💡 ASTUCES

### **1. Comparer avec hier**
Lancez le script tous les jours à la même heure pour voir l'évolution.

### **2. Noter les tendances**
Créez un fichier Excel/Google Sheets pour tracker :
- Inscriptions par jour
- Transactions par jour
- Utilisateurs actifs

### **3. Corréler avec le marketing**
- Jour où vous avez posté sur Facebook → Pic d'inscriptions ?
- Jour où vous avez contacté des influenceurs → Plus d'activité ?

---

## 🔧 PERSONNALISATION

### **Changer la période (ex: 48h au lieu de 24h)**

Éditez le fichier `monitor_activity.py` :

```python
# Ligne ~250
monitor_recent_signups(hours=48)  # Au lieu de 24
monitor_active_users(hours=48)    # Au lieu de 24
monitor_recent_posts(hours=48)    # Au lieu de 24
```

---

### **Ajouter des filtres**

Vous pouvez modifier le script pour :
- Voir uniquement les utilisateurs d'un pays
- Voir uniquement les annonces d'un jeu spécifique
- Voir uniquement les transactions au-dessus d'un montant

---

## 📱 NOTIFICATIONS AUTOMATIQUES (AVANCÉ)

### **Option 1 : Email quotidien**

Créer un cron job sur Render qui envoie un email avec les stats :

```bash
# Tous les jours à 9h
0 9 * * * python3 monitor_activity.py | mail -s "Stats Blizz" votre@email.com
```

### **Option 2 : Webhook Discord/Slack**

Modifier le script pour envoyer les stats sur Discord/Slack automatiquement.

---

## 🐛 DÉPANNAGE

### **Erreur : "No module named 'django'"**
```bash
# Installer les dépendances
pip install -r requirements.txt
```

### **Erreur : "Settings not configured"**
```bash
# Vérifier que vous êtes dans le bon dossier
cd /opt/render/project/src
python3 monitor_activity.py
```

### **Rien ne s'affiche**
C'est normal si vous n'avez pas encore d'utilisateurs ! Le script affichera :
```
❌ Aucune inscription dans les dernières 24h
❌ Aucun utilisateur actif dans les dernières 24h
```

---

## 📊 EXEMPLE DE SORTIE

```
================================================================================
  🔍 MONITORING ACTIVITÉ BLIZZ GAMING
================================================================================

📅 Date: 02/10/2025 19:30:00

────────────────────────────────────────────────────────────────────────────────
  📊 STATISTIQUES GLOBALES
────────────────────────────────────────────────────────────────────────────────

👥 Utilisateurs:
   Total: 25
   Email vérifié: 18 (72.0%)
   Actifs 24h: 5
   Actifs 7j: 12

🎮 Annonces:
   Total: 15
   En vente: 12 (80.0%)

💰 Transactions:
   Total: 3
   Complétées: 2 (66.7%)

────────────────────────────────────────────────────────────────────────────────
  📝 INSCRIPTIONS DES DERNIÈRES 24H
────────────────────────────────────────────────────────────────────────────────

✅ 3 inscription(s) récente(s):

1. gamer123
   Email: gamer123@gmail.com
   Inscrit: Il y a 2h (02/10/2025 17:30)
   Email vérifié: ✅ Oui
   Score: 0
   Badge: Bronze
   Dernière activité: Annonce créée - Il y a 1h

2. player456
   Email: player456@gmail.com
   Inscrit: Il y a 5h (02/10/2025 14:30)
   Email vérifié: ❌ Non
   Score: 0
   Badge: Bronze
   Dernière activité: Aucune activité - Il y a 5h

[...]
```

---

## 🎯 PROCHAINES ÉTAPES

1. **Lancer le script maintenant** pour voir l'état actuel
2. **Le relancer dans 24h** pour voir l'évolution
3. **Ajuster votre stratégie marketing** selon les résultats
4. **Célébrer les premiers utilisateurs** ! 🎉

---

**Bon monitoring ! 📊🚀**
