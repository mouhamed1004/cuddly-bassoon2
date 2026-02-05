# 🧪 Guide de Test du Chat CinetPay en Mode Test

## 📋 Vue d'ensemble

Le mode test CinetPay est maintenant activé ! Cela signifie que vous pouvez tester le système de chat entre vendeur et acheteur sans faire de vrais paiements.

## 🔧 Configuration Actuelle

### ✅ Mode Test Activé
- **CINETPAY_TEST_MODE**: `True`
- **Simulation automatique**: Paiement réussi simulé
- **Chat activé**: Immédiatement après simulation

### 🎯 Fonctionnalités Testées
- ✅ Mode test CinetPay activé
- ✅ Simulation de paiement fonctionnelle
- ✅ Activation automatique du chat
- ✅ Création des notifications
- ✅ Mise à jour des statuts de transaction

## 🚀 Comment Tester le Chat

### **Étape 1 : Créer une Annonce Gaming**
1. Allez sur `http://127.0.0.1:8000/`
2. Connectez-vous avec votre compte
3. Cliquez sur "Créer une annonce"
4. Remplissez les informations :
   - **Titre** : "Test Chat CinetPay"
   - **Jeu** : FreeFire (ou autre)
   - **Prix** : 10.00€
   - **Description** : "Compte de test pour le chat"
   - **Email/Password** : test@example.com / test123
5. Cliquez sur "Publier"

### **Étape 2 : Acheter l'Annonce (Compte Acheteur)**
1. **Déconnectez-vous** et connectez-vous avec un **autre compte**
2. Allez sur la page d'accueil
3. Trouvez votre annonce "Test Chat CinetPay"
4. Cliquez sur "Acheter"
5. Vous serez redirigé vers la page de transaction

### **Étape 3 : Tester le Paiement CinetPay**
1. Sur la page de transaction, cliquez sur **"Payer avec CinetPay"**
2. **IMPORTANT** : Le paiement sera **automatiquement simulé** !
3. Vous verrez le message : "🧪 Mode test: Paiement simulé avec succès!"
4. Le chat sera **immédiatement activé**

### **Étape 4 : Tester le Chat**
1. Vous verrez maintenant la section **"Discussion avec [nom du vendeur]"**
2. Tapez un message dans le champ de texte
3. Cliquez sur "Envoyer" (icône avion)
4. Le message apparaîtra dans le chat

### **Étape 5 : Tester du Côté Vendeur**
1. **Déconnectez-vous** et reconnectez-vous avec le **compte vendeur**
2. Allez dans "Mes Ventes" ou "Transactions"
3. Cliquez sur la transaction
4. Vous verrez le chat activé avec les messages de l'acheteur
5. Répondez à l'acheteur

## 🔍 Vérifications Importantes

### **Avant Paiement (Chat Verrouillé)**
- ❌ Section chat avec cadenas
- ❌ Message "Paiement requis"
- ❌ Bouton "Payer maintenant" visible

### **Après Paiement (Chat Activé)**
- ✅ Section chat déverrouillée
- ✅ Interface de messagerie fonctionnelle
- ✅ Messages en temps réel
- ✅ Notifications créées

## 📱 Interface de Chat

### **Éléments Visuels**
- **Header** : "Discussion avec [nom de l'autre utilisateur]"
- **Zone de messages** : Affichage des messages avec timestamps
- **Champ de saisie** : "Tapez votre message..."
- **Bouton d'envoi** : Icône avion

### **Fonctionnalités**
- **Messages différenciés** : Vos messages vs messages de l'autre
- **Timestamps** : Heure d'envoi de chaque message
- **Temps réel** : Pas de rechargement de page nécessaire
- **Notifications** : Alertes pour nouveaux messages

## 🧪 Tests Recommandés

### **Test 1 : Flux Complet**
1. Créer annonce → Acheter → Payer → Chat
2. Vérifier que le chat s'active après paiement
3. Tester l'envoi de messages des deux côtés

### **Test 2 : Notifications**
1. Vérifier les notifications créées
2. Tester l'affichage des alertes
3. Vérifier les emails de notification (si configurés)

### **Test 3 : Statuts de Transaction**
1. Vérifier le passage de "pending" à "processing"
2. Vérifier la création de CinetPayTransaction
3. Vérifier les montants de commission (10% plateforme, 90% vendeur)

## 🔧 Désactiver le Mode Test

Pour désactiver le mode test et utiliser de vrais paiements CinetPay :

```python
# Dans socialgame/settings.py
CINETPAY_TEST_MODE = False  # Mettre à False
```

## 🐛 Dépannage

### **Problème : Chat ne s'active pas**
- Vérifiez que `CINETPAY_TEST_MODE = True`
- Vérifiez les logs Django
- Vérifiez que la transaction a bien un `cinetpay_transaction`

### **Problème : Messages ne s'affichent pas**
- Vérifiez la console JavaScript
- Vérifiez les erreurs réseau
- Vérifiez que les deux utilisateurs sont connectés

### **Problème : Notifications manquantes**
- Vérifiez la création des objets Notification
- Vérifiez les permissions utilisateur
- Vérifiez les templates de notification

## 📊 Logs de Test

Le mode test génère des logs utiles :
- `🧪 Mode test CinetPay activé`
- `✅ Paiement simulé avec succès`
- `✅ Chat activé après paiement`

## 🎉 Résultat Attendu

Après avoir suivi ce guide, vous devriez avoir :
- ✅ Un système de chat fonctionnel
- ✅ Des paiements simulés automatiquement
- ✅ Des notifications créées
- ✅ Une expérience utilisateur fluide

---

**Note** : Ce mode test est parfait pour le développement et les tests. En production, n'oubliez pas de désactiver `CINETPAY_TEST_MODE` et d'utiliser de vraies clés CinetPay.
