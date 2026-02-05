#!/usr/bin/env python3
"""
Script to reset user scores to start with Bronze I
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import UserReputation
from blizzgame.badge_config import get_seller_badge

def reset_user_scores():
    """Reset user scores to start with Bronze I"""
    print("🔄 Resetting user scores to start with Bronze I...")
    
    # Get all users with UserReputation
    users_with_reputation = User.objects.filter(userreputation__isnull=False)
    print(f"Found {users_with_reputation.count()} users with UserReputation")
    
    reset_count = 0
    for user in users_with_reputation:
        try:
            reputation = user.userreputation
            
            # Check current badge
            current_badge = reputation.get_seller_badge()
            print(f"   {user.username}: {current_badge['name']} (score: {reputation.seller_score})")
            
            # Reset to Bronze I (score 0)
            reputation.seller_score = 0.0
            reputation.seller_badge = 'bronze_1'
            reputation.seller_total_transactions = 0
            reputation.seller_successful_transactions = 0
            reputation.seller_failed_transactions = 0
            reputation.seller_fraudulent_transactions = 0
            reputation.save()
            
            # Verify the reset
            new_badge = reputation.get_seller_badge()
            if new_badge['level'] == 'bronze_1':
                print(f"   ✅ Reset to {new_badge['name']}")
                reset_count += 1
            else:
                print(f"   ❌ Failed to reset: {new_badge['name']}")
                
        except Exception as e:
            print(f"   ❌ Error resetting {user.username}: {e}")
    
    print(f"\n✅ Reset {reset_count} users to Bronze I")
    
    # Verify the reset
    print("\nVerifying reset...")
    bronze_users = UserReputation.objects.filter(seller_badge='bronze_1').count()
    print(f"Users with Bronze I: {bronze_users}")

if __name__ == "__main__":
    print("🚀 Starting user score reset...")
    reset_user_scores()
    print("\n✅ User score reset completed!")


