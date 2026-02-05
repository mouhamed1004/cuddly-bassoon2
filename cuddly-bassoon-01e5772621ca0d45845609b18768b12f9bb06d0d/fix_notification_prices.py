#!/usr/bin/env python3
"""
Script pour corriger les prix mal formatés dans les notifications
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Notification
import re

def fix_notification_prices():
    """Corrige les prix mal formatés dans les notifications"""
    print("🔧 CORRECTION DES PRIX DANS LES NOTIFICATIONS")
    print("=" * 60)
    
    try:
        # Chercher les notifications avec des prix mal formatés
        notifications = Notification.objects.filter(
            content__icontains='$'
        ).order_by('-created_at')
        
        total_notifications = notifications.count()
        print(f"📊 Notifications avec $ trouvées: {total_notifications}")
        
        if total_notifications == 0:
            print("✅ Aucune notification à corriger")
            return True
        
        fixed_count = 0
        error_count = 0
        
        for notification in notifications:
            try:
                original_content = notification.content
                print(f"\n📧 Notification {notification.id.hex[:8]}:")
                print(f"   - Titre: {notification.title}")
                print(f"   - Contenu original: {original_content}")
                
                # Chercher les prix mal formatés (ex: "0.$157.95")
                malformed_pattern = r'0\.\$(\d+(?:\.\d{1,2})?)'
                matches = re.findall(malformed_pattern, original_content)
                
                if matches:
                    print(f"   - Prix mal formatés trouvés: {matches}")
                    
                    # Corriger chaque prix mal formaté
                    corrected_content = original_content
                    for amount in matches:
                        # Remplacer "0.$157.95" par "157.95€"
                        malformed_price = f"0.${amount}"
                        corrected_price = f"{amount}€"
                        corrected_content = corrected_content.replace(malformed_price, corrected_price)
                        print(f"   - Corrigé: {malformed_price} → {corrected_price}")
                    
                    # Sauvegarder la correction
                    notification.content = corrected_content
                    notification.save()
                    fixed_count += 1
                    print(f"   - ✅ Corrigé et sauvegardé")
                else:
                    print(f"   - ✅ Aucun prix mal formaté détecté")
                
            except Exception as e:
                error_count += 1
                print(f"   - ❌ Erreur: {e}")
                continue
        
        print(f"\n✅ Correction terminée:")
        print(f"   - Corrigées: {fixed_count}")
        print(f"   - Erreurs: {error_count}")
        print(f"   - Total: {total_notifications}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_fixes():
    """Vérifie que les corrections sont correctes"""
    print(f"\n🔍 VÉRIFICATION DES CORRECTIONS")
    print("=" * 60)
    
    try:
        # Vérifier qu'il n'y a plus de prix mal formatés
        malformed_notifications = Notification.objects.filter(
            content__icontains='0.$'
        )
        
        print(f"📊 Notifications avec prix mal formatés restantes: {malformed_notifications.count()}")
        
        if malformed_notifications.count() == 0:
            print("✅ Aucun prix mal formaté restant")
            return True
        else:
            print("❌ Des prix mal formatés restent:")
            for notification in malformed_notifications:
                print(f"   - {notification.id.hex[:8]}: {notification.content}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🚀 CORRECTION DES PRIX DANS LES NOTIFICATIONS")
    print("=" * 60)
    
    success = True
    
    # Correction
    if not fix_notification_prices():
        success = False
    
    # Vérification
    if not verify_fixes():
        success = False
    
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("🎉 CORRECTION TERMINÉE AVEC SUCCÈS !")
        print("✅ Tous les prix mal formatés ont été corrigés")
        print("✅ Les notifications affichent maintenant les bons prix")
        print("✅ Le filtre a été amélioré pour éviter le problème")
    else:
        print("❌ CERTAINES ERREURS ONT ÉTÉ RENCONTRÉES")
        print("⚠️  Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
