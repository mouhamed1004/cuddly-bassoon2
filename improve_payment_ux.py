#!/usr/bin/env python3
"""
Script pour améliorer l'UX des paiements et nettoyer les transactions abandonnées
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Order, ShopCinetPayTransaction
from django.utils import timezone

def improve_payment_ux():
    """Améliore l'UX des paiements et nettoie les transactions abandonnées"""
    print("AMELIORATION UX PAIEMENTS")
    print("=" * 40)
    
    try:
        # 1. Identifier les transactions abandonnées (anciennes)
        print("\n1. NETTOYAGE TRANSACTIONS ABANDONNEES")
        print("-" * 40)
        
        # Transactions de plus de 1 heure en attente = abandonnées
        cutoff_time = timezone.now() - timedelta(hours=1)
        
        old_pending = ShopCinetPayTransaction.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        print(f"Transactions abandonnees (>1h): {old_pending.count()}")
        
        for transaction in old_pending:
            print(f"  - {transaction.cinetpay_transaction_id} (créée {transaction.created_at})")
            
            # Marquer comme échouée
            transaction.status = 'failed'
            transaction.save()
            
            # Mettre à jour la commande
            order = transaction.order
            if order.payment_status == 'pending':
                order.payment_status = 'failed'
                order.status = 'cancelled'
                order.save()
                print(f"    -> Commande #{order.order_number} marquée comme échouée")
        
        # 2. Statistiques après nettoyage
        print("\n2. STATISTIQUES APRES NETTOYAGE")
        print("-" * 40)
        
        current_pending = ShopCinetPayTransaction.objects.filter(status='pending').count()
        failed = ShopCinetPayTransaction.objects.filter(status='failed').count()
        completed = ShopCinetPayTransaction.objects.filter(status='completed').count()
        
        print(f"Transactions en attente (récentes): {current_pending}")
        print(f"Transactions échouées: {failed}")
        print(f"Transactions complétées: {completed}")
        
        # 3. Analyser les commandes
        print("\n3. ANALYSE COMMANDES")
        print("-" * 40)
        
        pending_orders = Order.objects.filter(payment_status='pending').count()
        failed_orders = Order.objects.filter(payment_status='failed').count()
        paid_orders = Order.objects.filter(payment_status='paid').count()
        
        print(f"Commandes en attente: {pending_orders}")
        print(f"Commandes échouées: {failed_orders}")
        print(f"Commandes payées: {paid_orders}")
        
        # 4. Recommandations d'amélioration UX
        print("\n4. RECOMMANDATIONS AMELIORATION UX")
        print("-" * 40)
        
        total_attempts = ShopCinetPayTransaction.objects.count()
        success_rate = (completed / total_attempts * 100) if total_attempts > 0 else 0
        
        print(f"Taux de succès actuel: {success_rate:.1f}%")
        
        if success_rate < 30:
            print("🚨 TAUX DE SUCCES TRES FAIBLE!")
            print("\nActions urgentes recommandées:")
            print("1. Vérifier que les URLs CinetPay fonctionnent")
            print("2. Tester le processus complet manuellement")
            print("3. Simplifier l'interface de paiement")
            print("4. Ajouter des instructions claires")
            print("5. Réduire le nombre d'étapes")
            
        elif success_rate < 60:
            print("⚠️ Taux de succès moyen")
            print("\nAméliorations suggérées:")
            print("1. Optimiser l'interface utilisateur")
            print("2. Ajouter des indicateurs de progression")
            print("3. Améliorer les messages d'erreur")
            
        else:
            print("✅ Taux de succès acceptable")
            print("Continuer à surveiller et optimiser")
        
        # 5. Créer des alertes pour les nouvelles transactions
        print("\n5. SURVEILLANCE CONTINUE")
        print("-" * 40)
        
        recent_transactions = ShopCinetPayTransaction.objects.filter(
            created_at__gte=timezone.now() - timedelta(minutes=30)
        )
        
        print(f"Transactions des 30 dernières minutes: {recent_transactions.count()}")
        
        for transaction in recent_transactions:
            age_minutes = (timezone.now() - transaction.created_at).total_seconds() / 60
            print(f"  - {transaction.cinetpay_transaction_id}: {transaction.status} ({age_minutes:.1f}min)")
        
        # 6. Suggestions d'amélioration technique
        print("\n6. SUGGESTIONS TECHNIQUES")
        print("-" * 40)
        print("1. Implémenter un système de relance automatique")
        print("2. Ajouter un timeout automatique (30min)")
        print("3. Créer une page de suivi de paiement")
        print("4. Envoyer des emails de rappel")
        print("5. Améliorer les messages d'erreur utilisateur")
        print("6. Ajouter un chat support en temps réel")
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    improve_payment_ux()
