#!/usr/bin/env python3
"""
Script pour rembourser une transaction CinetPay spécifique
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Transaction, Post, CinetPayTransaction, EscrowTransaction, PayoutRequest
from django.contrib.auth.models import User
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def find_transaction_by_amount(amount):
    """Trouve la dernière transaction avec un montant spécifique"""
    print(f"\n🔍 Recherche de la dernière transaction de {amount} EUR...")
    
    # Chercher les transactions récentes avec ce montant
    transactions = Transaction.objects.filter(
        amount=Decimal(str(amount))
    ).order_by('-created_at')[:5]
    
    if not transactions:
        print(f"❌ Aucune transaction trouvée avec le montant {amount} EUR")
        return None
    
    print(f"\n✅ {transactions.count()} transaction(s) trouvée(s):")
    
    for i, transaction in enumerate(transactions, 1):
        print(f"\n{i}. Transaction {transaction.id}")
        print(f"   Montant: {transaction.amount} EUR")
        print(f"   Statut: {transaction.status}")
        print(f"   Acheteur: {transaction.buyer.username}")
        print(f"   Vendeur: {transaction.seller.username}")
        print(f"   Produit: {transaction.post.title if transaction.post else 'N/A'}")
        print(f"   Date: {transaction.created_at}")
        
        # Vérifier le statut CinetPay
        if hasattr(transaction, 'cinetpay_transaction'):
            cpt = transaction.cinetpay_transaction
            print(f"   CinetPay Status: {cpt.status}")
            print(f"   CinetPay ID: {cpt.cinetpay_transaction_id}")
    
    return transactions[0]  # Retourner la plus récente

def refund_transaction(transaction):
    """Rembourse une transaction et crée un PayoutRequest pour l'acheteur"""
    print(f"\n{'='*80}")
    print(f"🔄 REMBOURSEMENT DE LA TRANSACTION {transaction.id}")
    print(f"{'='*80}\n")
    
    try:
        # 1. Vérifier que la transaction peut être remboursée
        if transaction.status == 'refunded':
            print("⚠️  Cette transaction a déjà été remboursée!")
            return False
        
        if transaction.status == 'cancelled':
            print("⚠️  Cette transaction est déjà annulée!")
            return False
        
        # 2. Mettre à jour le statut de la transaction
        old_status = transaction.status
        transaction.status = 'refunded'
        transaction.save()
        print(f"✅ Statut transaction: {old_status} → refunded")
        
        # 3. Remettre le produit en vente
        if transaction.post:
            post = transaction.post
            post.is_in_transaction = False
            post.is_sold = False
            post.is_on_sale = True
            post.save()
            print(f"✅ Produit remis en vente: {post.title}")
        
        # 4. Mettre à jour les transactions CinetPay
        if hasattr(transaction, 'cinetpay_transaction'):
            cpt = transaction.cinetpay_transaction
            old_cpt_status = cpt.status
            cpt.status = 'escrow_refunded'
            cpt.save()
            print(f"✅ CinetPayTransaction: {old_cpt_status} → escrow_refunded")
            
            # 5. Mettre à jour l'escrow
            try:
                escrow = EscrowTransaction.objects.get(cinetpay_transaction=cpt)
                old_escrow_status = escrow.status
                escrow.status = 'refunded'
                escrow.save()
                print(f"✅ EscrowTransaction: {old_escrow_status} → refunded")
                
                # 6. Créer un PayoutRequest pour rembourser l'acheteur
                print(f"\n💰 Création du remboursement pour l'acheteur...")
                
                # Récupérer les infos de paiement de l'acheteur
                buyer = transaction.buyer
                
                # Vérifier si l'acheteur a des infos de paiement
                if hasattr(buyer, 'payment_info') and buyer.payment_info.is_verified:
                    payment_info = buyer.payment_info
                    
                    payout = PayoutRequest.objects.create(
                        escrow_transaction=escrow,
                        amount=transaction.amount,  # Remboursement à 100%
                        original_amount=transaction.amount,
                        currency='EUR',
                        payout_type='buyer_refund',
                        recipient_phone=payment_info.phone_number,
                        recipient_country=payment_info.country,
                        recipient_operator=payment_info.operator,
                        status='pending'
                    )
                    
                    print(f"✅ PayoutRequest créé: {payout.id}")
                    print(f"   Type: Remboursement acheteur")
                    print(f"   Montant: {payout.amount} EUR")
                    print(f"   Destinataire: {payout.recipient_phone}")
                    print(f"   Opérateur: {payout.recipient_operator}")
                    print(f"   Pays: {payout.recipient_country}")
                else:
                    print(f"⚠️  L'acheteur {buyer.username} n'a pas configuré ses infos de paiement!")
                    print(f"   Le remboursement devra être fait manuellement.")
                    print(f"   Montant à rembourser: {transaction.amount} EUR")
                
            except EscrowTransaction.DoesNotExist:
                print("⚠️  Pas d'EscrowTransaction trouvée pour cette transaction")
        
        print(f"\n{'='*80}")
        print(f"✅ REMBOURSEMENT TERMINÉ AVEC SUCCÈS")
        print(f"{'='*80}\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR lors du remboursement: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("💸 REMBOURSEMENT DE TRANSACTION CINETPAY")
    print("="*80 + "\n")
    
    # Convertir 1099 FCFA en EUR (1099 / 655.957 ≈ 1.67 EUR)
    amount_fcfa = 1099
    amount_eur = round(amount_fcfa / 655.957, 2)
    
    print(f"💰 Montant recherché: {amount_fcfa} FCFA ≈ {amount_eur} EUR")
    
    # Trouver la transaction
    transaction = find_transaction_by_amount(amount_eur)
    
    if not transaction:
        print("\n❌ Transaction non trouvée!")
        print("\n💡 Essayez de chercher manuellement:")
        print("   1. Aller sur https://blizz.boutique/admin/")
        print("   2. Section 'Transactions'")
        print("   3. Chercher par montant ou date")
        return
    
    # Afficher les détails
    print(f"\n{'='*80}")
    print(f"📋 DÉTAILS DE LA TRANSACTION À REMBOURSER")
    print(f"{'='*80}")
    print(f"ID: {transaction.id}")
    print(f"Montant: {transaction.amount} EUR ({amount_fcfa} FCFA)")
    print(f"Acheteur: {transaction.buyer.username} ({transaction.buyer.email})")
    print(f"Vendeur: {transaction.seller.username}")
    print(f"Produit: {transaction.post.title if transaction.post else 'N/A'}")
    print(f"Statut actuel: {transaction.status}")
    print(f"Date: {transaction.created_at}")
    
    # Demander confirmation
    print("\n" + "="*80)
    print("⚠️  ATTENTION: Cette action va:")
    print("   1. Marquer la transaction comme 'refunded'")
    print("   2. Remettre le produit en vente")
    print("   3. Créer un PayoutRequest pour rembourser l'acheteur")
    print("   4. L'argent sera remboursé via CinetPay")
    print("="*80)
    
    response = input("\n❓ Confirmer le remboursement? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'yes', 'y', 'o']:
        print("\n❌ Remboursement annulé.")
        return
    
    # Effectuer le remboursement
    success = refund_transaction(transaction)
    
    if success:
        print("\n🎉 REMBOURSEMENT RÉUSSI!")
        print("\n📝 Prochaines étapes:")
        print("   1. Aller sur le dashboard payout: https://blizz.boutique/payouts/list/")
        print("   2. Trouver le PayoutRequest créé")
        print("   3. Traiter le remboursement via CinetPay")
        print("   4. L'acheteur recevra l'argent sur son Mobile Money")
    else:
        print("\n❌ Le remboursement a échoué. Vérifiez les logs ci-dessus.")

if __name__ == '__main__':
    main()
