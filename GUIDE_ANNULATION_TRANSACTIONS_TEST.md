# 🧹 Guide d'annulation des transactions de test

**Date:** 2025-10-02  
**Problème:** Transactions de test CinetPay à nettoyer + Bug d'accès après paiement

---

## 🎯 Objectifs

1. ✅ Annuler toutes les transactions de test
2. ✅ Remettre les produits en vente
3. ✅ Corriger le bug "vous n'avez pas accès à cette transaction"

---

## 📋 Étape 1: Annuler les transactions de test

### **Méthode automatique (Recommandée)**

**Script créé:** `cancel_test_transactions.py`

**Utilisation:**
```bash
# Depuis le dossier du projet
python cancel_test_transactions.py
```

**Ce que fait le script:**
1. 🔍 Identifie les transactions de test (dernières 24h)
2. 📊 Affiche la liste avec détails
3. ❓ Demande confirmation
4. 🔄 Annule les transactions
5. 📦 Remet les produits en vente
6. ✅ Affiche le résumé

**Critères de détection des transactions de test:**
- Montants suspects: 1€, 10€, 100€, 1099 FCFA
- Acheteur = Vendeur (même utilisateur)
- Nom d'utilisateur contient "test"
- Transactions récentes (< 24h)

---

### **Méthode manuelle (Via Django Admin)**

**Si tu préfères faire manuellement:**

1. **Connexion à l'admin Django:**
   ```
   https://blizz.boutique/admin/
   ```

2. **Aller dans "Transactions"**

3. **Pour chaque transaction de test:**
   - Ouvrir la transaction
   - Changer le statut → "cancelled"
   - Sauvegarder

4. **Remettre les produits en vente:**
   - Aller dans "Posts"
   - Pour chaque produit concerné:
     - `is_in_transaction` → False
     - `is_sold` → False
     - `is_on_sale` → True
     - Sauvegarder

---

## 🐛 Étape 2: Corriger le bug d'accès

### **Le problème**

**Message d'erreur:**
```
"Vous n'avez pas accès à cette transaction"
```

**Cause:**
Après le paiement CinetPay, l'utilisateur est redirigé mais la session peut être perdue.

**Code problématique** (`views.py` ligne 1185-1187):
```python
if request.user != transaction.buyer and request.user != transaction.seller:
    messages.error(request, "Vous n'avez pas accès à cette transaction.")
    return redirect('index')
```

---

### **Solution 1: Vérifier l'authentification** ⭐ RECOMMANDÉ

Le problème vient souvent du fait que l'utilisateur n'est pas authentifié après le retour de CinetPay.

**Correction à apporter:**

```python
@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier si l'utilisateur est authentifié
    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour accéder à cette transaction.")
        return redirect(f'/signin/?next=/transaction/{transaction_id}/')
    
    # Vérifier si l'utilisateur est impliqué dans cette transaction
    if request.user != transaction.buyer and request.user != transaction.seller:
        messages.error(request, "Vous n'avez pas accès à cette transaction.")
        return redirect('index')
    
    # ... reste du code
```

---

### **Solution 2: Améliorer le retour CinetPay**

**Le problème:** CinetPay redirige vers une URL sans préserver la session.

**Vérifier la configuration CinetPay:**

```python
# Dans cinetpay_utils.py ou views.py
return_url = f"{settings.SITE_URL}/payment/cinetpay/success/{transaction.id}/"
notify_url = f"{settings.SITE_URL}/payment/cinetpay/notify/{transaction.id}/"
```

**S'assurer que:**
- ✅ `SITE_URL` est correct: `https://blizz.boutique`
- ✅ Les URLs incluent bien l'ID de la transaction
- ✅ Les cookies de session sont préservés

---

### **Solution 3: Ajouter un token de sécurité**

**Pour éviter les problèmes de session:**

```python
import secrets

# Lors de la création de la transaction
transaction.access_token = secrets.token_urlsafe(32)
transaction.save()

# Dans l'URL de retour CinetPay
return_url = f"{settings.SITE_URL}/payment/cinetpay/success/{transaction.id}/?token={transaction.access_token}"

# Dans la vue transaction_detail
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Vérifier le token si fourni
    token = request.GET.get('token')
    if token and token == transaction.access_token:
        # Accès autorisé via token
        pass
    elif request.user.is_authenticated and (request.user == transaction.buyer or request.user == transaction.seller):
        # Accès autorisé via authentification
        pass
    else:
        messages.error(request, "Vous n'avez pas accès à cette transaction.")
        return redirect('index')
```

---

## 🔧 Étape 3: Appliquer les corrections

### **Correction immédiate (Sans code)**

**Pour la transaction de 1099 FCFA qui pose problème:**

1. **Se connecter avec le compte acheteur**
2. **Aller sur:** `https://blizz.boutique/transactions/`
3. **Cliquer sur la transaction concernée**
4. **Si ça ne marche toujours pas:**
   - Copier l'URL de la transaction
   - Se déconnecter
   - Se reconnecter
   - Coller l'URL et accéder

---

### **Correction permanente (Avec code)**

**Fichier à modifier:** `blizzgame/views.py`

**Ligne 1181-1187:**

```python
# AVANT (problématique)
@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    if request.user != transaction.buyer and request.user != transaction.seller:
        messages.error(request, "Vous n'avez pas accès à cette transaction.")
        return redirect('index')

# APRÈS (corrigé)
@login_required
def transaction_detail(request, transaction_id):
    transaction = get_object_or_404(Transaction, id=transaction_id)
    
    # Log pour debug
    logger.info(f"Accès transaction {transaction_id} par {request.user.username if request.user.is_authenticated else 'Anonymous'}")
    logger.info(f"Acheteur: {transaction.buyer.username}, Vendeur: {transaction.seller.username}")
    
    # Vérifier l'authentification
    if not request.user.is_authenticated:
        messages.warning(request, "Veuillez vous connecter pour accéder à cette transaction.")
        return redirect(f'/signin/?next=/transaction/{transaction_id}/')
    
    # Vérifier l'accès
    if request.user != transaction.buyer and request.user != transaction.seller and not request.user.is_staff:
        logger.warning(f"Accès refusé à la transaction {transaction_id} pour {request.user.username}")
        messages.error(request, "Vous n'avez pas accès à cette transaction.")
        return redirect('index')
```

---

## 📊 Résumé des actions

### **À faire maintenant:**

1. **Annuler les transactions de test:**
   ```bash
   python cancel_test_transactions.py
   ```

2. **Vérifier la transaction de 1099 FCFA:**
   - Se reconnecter
   - Accéder via `/transactions/`
   - Vérifier que le chat fonctionne

3. **Appliquer la correction du code:**
   - Modifier `views.py` ligne 1181-1187
   - Ajouter les logs de debug
   - Déployer sur Render

---

## ✅ Checklist de vérification

Après les corrections:

- [ ] Toutes les transactions de test sont annulées
- [ ] Les produits sont remis en vente
- [ ] La transaction de 1099 FCFA est accessible
- [ ] Le chat de la transaction fonctionne
- [ ] Les logs montrent les accès correctement
- [ ] Pas de message d'erreur "vous n'avez pas accès"

---

## 🆘 Si le problème persiste

**Vérifier dans cet ordre:**

1. **Session Django:**
   ```python
   # Dans settings.py
   SESSION_COOKIE_AGE = 1209600  # 2 semaines
   SESSION_COOKIE_SECURE = True  # HTTPS only
   SESSION_COOKIE_SAMESITE = 'Lax'  # Permet les redirections externes
   ```

2. **Configuration CinetPay:**
   - URL de retour correcte
   - URL de notification correcte
   - Domaine autorisé dans CinetPay dashboard

3. **Logs Render:**
   ```bash
   # Voir les logs en temps réel
   render logs --tail
   ```

---

## 📞 Support

**Si tu as besoin d'aide:**
- Envoie-moi les logs de la console (F12)
- Copie l'URL exacte qui pose problème
- Indique le nom d'utilisateur concerné

---

**Généré le:** 2025-10-02 01:19  
**Script créé:** `cancel_test_transactions.py`  
**Fichier à modifier:** `blizzgame/views.py` (ligne 1181-1187)
