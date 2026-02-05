#!/usr/bin/env python3
"""
Script pour annuler les transactions de test CinetPay
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Transaction, Post, CinetPayTransaction, EscrowTransaction
from django.contrib.auth.models import User
from django.utils import timezone

def list_test_transactions():
    """Liste toutes les transactions potentiellement de test"""
    print("=" * 80)
    print("🔍 RECHERCHE DES TRANSACTIONS DE TEST")
    print("=" * 80)
    
    # Critères pour identifier les transactions de test
    test_transactions = []
    
    # 1. Transactions récentes (dernières 24h)
    recent_time = timezone.now() - timezone.timedelta(hours=24)
    recent_transactions = Transaction.objects.filter(created_at__gte=recent_time)
    
    print(f"\n📊 Transactions des dernières 24h: {recent_transactions.count()}")
    
    for transaction in recent_transactions:
        print(f"\n{'='*60}")
        print(f"ID: {transaction.id}")
        print(f"Montant: {transaction.amount} EUR")
        print(f"Statut: {transaction.status}")
        print(f"Acheteur: {transaction.buyer.username}")
        print(f"Vendeur: {transaction.seller.username}")
        print(f"Produit: {transaction.post.title if transaction.post else 'N/A'}")
        print(f"Date: {transaction.created_at}")
        
        # Vérifier si c'est probablement un test
        is_test = False
        reasons = []
        
        # Montants suspects (petits montants ronds ou très petits)
        # 100 FCFA = ~0.15 EUR, 1099 FCFA = ~1.67 EUR
        if transaction.amount <= Decimal('2.00') or transaction.amount in [Decimal('10.00'), Decimal('100.00')]:
            is_test = True
            reasons.append(f"Montant suspect: {transaction.amount} EUR")
        
        # Même utilisateur acheteur/vendeur
        if transaction.buyer == transaction.seller:
            is_test = True
            reasons.append("Acheteur = Vendeur")
        
        # Utilisateur de test dans le nom
        if 'test' in transaction.buyer.username.lower() or 'test' in transaction.seller.username.lower():
            is_test = True
            reasons.append("Nom d'utilisateur contient 'test'")
        
        if is_test:
            print(f"⚠️  TRANSACTION DE TEST DÉTECTÉE:")
            for reason in reasons:
                print(f"   - {reason}")
            test_transactions.append(transaction)
    
    print(f"\n{'='*80}")
    print(f"✅ Total transactions de test trouvées: {len(test_transactions)}")
    print(f"{'='*80}\n")
    
    return test_transactions

def cancel_transaction(transaction):
    """Annule une transaction et remet le produit en vente"""
    print(f"\n🔄 Annulation de la transaction {transaction.id}...")
    
    try:
        # 1. Mettre à jour le statut de la transaction
        old_status = transaction.status
        transaction.status = 'cancelled'
        transaction.save()
        print(f"   ✅ Statut changé: {old_status} → cancelled")
        
        # 2. Remettre le produit en vente
        if transaction.post:
            post = transaction.post
            post.is_in_transaction = False
            post.is_sold = False
            post.is_on_sale = True
            post.save()
            print(f"   ✅ Produit remis en vente: {post.title}")
        
        # 3. Marquer les transactions CinetPay comme annulées
        cinetpay_transactions = CinetPayTransaction.objects.filter(transaction=transaction)
        for cpt in cinetpay_transactions:
            cpt.status = 'cancelled'
            cpt.save()
            print(f"   ✅ CinetPayTransaction {cpt.id} annulée")
        
        # 4. Marquer les escrow comme annulés
        escrow_transactions = EscrowTransaction.objects.filter(cinetpay_transaction__transaction=transaction)
        for escrow in escrow_transactions:
            escrow.status = 'cancelled'
            escrow.save()
            print(f"   ✅ EscrowTransaction {escrow.id} annulée")
        
        print(f"   ✅ Transaction {transaction.id} complètement annulée\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'annulation: {e}\n")
        return False

def main():
    print("\n" + "="*80)
    print("🧹 NETTOYAGE DES TRANSACTIONS DE TEST CINETPAY")
    print("="*80 + "\n")
    
    # Lister les transactions de test
    test_transactions = list_test_transactions()
    
    if not test_transactions:
        print("✅ Aucune transaction de test trouvée!")
        return
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette action va annuler ces transactions!")
    print("Les produits seront remis en vente.")
    print("\nTransactions à annuler:")
    for i, transaction in enumerate(test_transactions, 1):
        print(f"{i}. Transaction {transaction.id} - {transaction.amount} EUR - {transaction.buyer.username}")
    
    # En mode automatique sur serveur, demander confirmation via variable d'environnement
    import os
    auto_confirm = os.environ.get('AUTO_CONFIRM_CANCEL', 'false').lower() == 'true'
    
    if not auto_confirm:
        response = input("\n❓ Voulez-vous continuer? (oui/non): ").strip().lower()
        
        if response not in ['oui', 'yes', 'y', 'o']:
            print("\n❌ Annulation abandonnée.")
            return
    else:
        print("\n✅ Mode automatique activé (AUTO_CONFIRM_CANCEL=true)")
    
    # Annuler les transactions
    print("\n" + "="*80)
    print("🔄 ANNULATION EN COURS...")
    print("="*80)
    
    success_count = 0
    fail_count = 0
    
    for transaction in test_transactions:
        if cancel_transaction(transaction):
            success_count += 1
        else:
            fail_count += 1
    
    # Résumé
    print("\n" + "="*80)
    print("📊 RÉSUMÉ")
    print("="*80)
    print(f"✅ Transactions annulées avec succès: {success_count}")
    print(f"❌ Échecs: {fail_count}")
    print(f"📦 Total traité: {len(test_transactions)}")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
