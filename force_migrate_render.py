#!/usr/bin/env python3
"""
Script pour forcer l'application des migrations sur Render
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.core.management import execute_from_command_line

def force_migrate():
    """Force l'application de toutes les migrations"""
    print("🚀 FORÇAGE DES MIGRATIONS SUR RENDER")
    print("=" * 60)
    
    try:
        # Appliquer toutes les migrations
        print("📋 Application de toutes les migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=2'])
        
        print("✅ Migrations appliquées avec succès")
        
        # Vérifier l'état des migrations
        print("\n📊 État des migrations:")
        execute_from_command_line(['manage.py', 'showmigrations', 'blizzgame'])
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application des migrations: {e}")
        return False

def check_notification_model():
    """Vérifie le modèle Notification"""
    print("\n🔍 VÉRIFICATION DU MODÈLE NOTIFICATION")
    print("=" * 60)
    
    try:
        from blizzgame.models import Notification
        from django.db import connection
        
        # Vérifier la structure de la table
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA table_info(blizzgame_notification)")
            columns = cursor.fetchall()
            
            print("📋 Colonnes de la table blizzgame_notification:")
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                print(f"   - {col_name}: {col_type}")
        
        # Tester la création d'une notification
        print("\n🧪 Test de création de notification...")
        from django.contrib.auth.models import User
        from blizzgame.models import Order
        
        user = User.objects.first()
        order = Order.objects.filter(user=user).first()
        
        if user and order:
            # Créer une notification simple
            notification = Notification.objects.create(
                user=user,
                title="Test Migration",
                notification_type="order_confirmation",
                order=order
            )
            print(f"✅ Notification créée: {notification.id}")
            notification.delete()
            print("✅ Notification supprimée")
        else:
            print("⚠️  Utilisateur ou commande non trouvé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 SCRIPT DE FORÇAGE DES MIGRATIONS RENDER")
    print("=" * 60)
    
    success = True
    
    # Forcer les migrations
    if not force_migrate():
        success = False
    
    # Vérifier le modèle
    if not check_notification_model():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 MIGRATIONS FORCÉES AVEC SUCCÈS !")
        print("✅ Le problème devrait être résolu")
    else:
        print("❌ PROBLÈME LORS DU FORÇAGE")
        print("⚠️  Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
