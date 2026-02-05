#!/usr/bin/env python3
"""
Test script to verify badge display fix
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from blizzgame.models import UserReputation

def test_badge_display_fix():
    """Test badge display fix"""
    print("🧪 Testing badge display fix...")
    
    client = Client()
    
    # Test 1: Check index page badge display
    print("\n1. Testing index page badge display...")
    try:
        response = client.get('/')
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check if badge data is being used correctly
            has_seller_badge_data = 'seller_badge_data' in content
            has_badge_names = any(badge in content for badge in ['Bronze I', 'Argent I', 'Or I', 'Diamant I'])
            
            print(f"   Index page loads: ✅")
            print(f"   Uses seller_badge_data: {'✅' if has_seller_badge_data else '❌'}")
            print(f"   Shows badge names: {'✅' if has_badge_names else '❌'}")
            
            if has_seller_badge_data and has_badge_names:
                print("   ✅ Index page badge display working correctly")
            else:
                print("   ❌ Index page badge display has issues")
        else:
            print(f"   ❌ Index page failed to load: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing index page: {e}")
    
    # Test 2: Check product detail page badge display
    print("\n2. Testing product detail page badge display...")
    try:
        # Get a product to test
        from blizzgame.models import Post
        post = Post.objects.first()
        if post:
            response = client.get(f'/product/{post.id}/')
            if response.status_code == 200:
                content = response.content.decode('utf-8')
                
                has_seller_badge = 'seller_badge' in content
                has_badge_names = any(badge in content for badge in ['Bronze I', 'Argent I', 'Or I', 'Diamant I'])
                
                print(f"   Product detail page loads: ✅")
                print(f"   Has seller_badge context: {'✅' if has_seller_badge else '❌'}")
                print(f"   Shows badge names: {'✅' if has_badge_names else '❌'}")
                
                if has_seller_badge and has_badge_names:
                    print("   ✅ Product detail page badge display working correctly")
                else:
                    print("   ❌ Product detail page badge display has issues")
            else:
                print(f"   ❌ Product detail page failed to load: {response.status_code}")
        else:
            print("   ⚠️  No products found to test")
    except Exception as e:
        print(f"   ❌ Error testing product detail page: {e}")
    
    # Test 3: Check specific user badge data
    print("\n3. Testing specific user badge data...")
    try:
        user = User.objects.first()
        if user and hasattr(user, 'userreputation'):
            reputation = user.userreputation
            badge_data = reputation.seller_badge_data
            badge_method = reputation.get_seller_badge()
            
            print(f"   User: {user.username}")
            print(f"   Badge from property: {badge_data['name']}")
            print(f"   Badge from method: {badge_method['name']}")
            print(f"   Match: {'✅' if badge_data['name'] == badge_method['name'] else '❌'}")
            
            if badge_data['name'] == badge_method['name']:
                print("   ✅ Property and method return same badge")
            else:
                print("   ❌ Property and method return different badges")
        else:
            print("   ⚠️  No user with reputation found")
    except Exception as e:
        print(f"   ❌ Error testing user badge data: {e}")
    
    # Test 4: Check for users with different badge levels
    print("\n4. Checking users with different badge levels...")
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT seller_badge, COUNT(*) FROM blizzgame_userreputation GROUP BY seller_badge ORDER BY COUNT(*) DESC")
            badge_counts = cursor.fetchall()
            
            print("   Badge distribution:")
            for badge, count in badge_counts:
                print(f"     {badge}: {count} users")
            
            # Test a few users with different badges
            users_to_test = User.objects.filter(userreputation__isnull=False)[:3]
            for user in users_to_test:
                reputation = user.userreputation
                badge = reputation.seller_badge_data
                print(f"   {user.username}: {badge['name']} (score: {reputation.seller_score})")
                
    except Exception as e:
        print(f"   ❌ Error checking badge levels: {e}")

if __name__ == "__main__":
    print("🚀 Starting badge display fix test...")
    test_badge_display_fix()
    print("\n✅ Badge display fix test completed!")


