#!/usr/bin/env python3
"""
Script pour créer/modifier une annonce de test à 110 FCFA
"""
import os
import sys
import django
from decimal import Decimal

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import Post, User
from django.utils import timezone

def list_available_posts():
    """Liste les annonces disponibles à la vente"""
    print("\n" + "="*80)
    print("📦 ANNONCES DISPONIBLES")
    print("="*80 + "\n")
    
    posts = Post.objects.filter(
        is_on_sale=True,
        is_sold=False,
        is_in_transaction=False
    ).order_by('-created_at')[:10]
    
    if not posts:
        print("❌ Aucune annonce disponible!")
        return None
    
    print(f"✅ {posts.count()} annonce(s) disponible(s):\n")
    
    for i, post in enumerate(posts, 1):
        print(f"{i}. {post.title}")
        print(f"   ID: {post.id}")
        print(f"   Prix actuel: {post.price} EUR")
        print(f"   Vendeur: {post.author.username}")
        print(f"   Jeu: {post.get_game_display_name()}")
        print(f"   Date: {post.created_at.strftime('%Y-%m-%d %H:%M')}")
        print()
    
    return list(posts)

def change_post_price(post, new_price_fcfa):
    """Change le prix d'une annonce"""
    # Convertir FCFA en EUR
    new_price_eur = round(new_price_fcfa / 655.957, 2)
    
    print(f"\n{'='*80}")
    print(f"💰 MODIFICATION DU PRIX")
    print(f"{'='*80}")
    print(f"Annonce: {post.title}")
    print(f"Prix actuel: {post.price} EUR")
    print(f"Nouveau prix: {new_price_eur} EUR ({new_price_fcfa} FCFA)")
    print(f"Vendeur: {post.author.username}")
    
    # Demander confirmation
    response = input("\n❓ Confirmer la modification? (oui/non): ").strip().lower()
    
    if response not in ['oui', 'yes', 'y', 'o']:
        print("\n❌ Modification annulée.")
        return False
    
    # Modifier le prix
    old_price = post.price
    post.price = Decimal(str(new_price_eur))
    post.save()
    
    print(f"\n✅ Prix modifié: {old_price} EUR → {new_price_eur} EUR ({new_price_fcfa} FCFA)")
    print(f"✅ Annonce prête pour les tests!")
    
    return True

def create_test_post():
    """Crée une nouvelle annonce de test"""
    print("\n" + "="*80)
    print("🆕 CRÉATION D'UNE NOUVELLE ANNONCE DE TEST")
    print("="*80 + "\n")
    
    # Trouver un utilisateur pour être le vendeur
    users = User.objects.filter(is_active=True).exclude(is_staff=True)[:5]
    
    if not users:
        print("❌ Aucun utilisateur trouvé!")
        return False
    
    print("👥 Utilisateurs disponibles:")
    for i, user in enumerate(users, 1):
        print(f"{i}. {user.username} ({user.email})")
    
    choice = input("\n❓ Choisir un utilisateur (1-5): ").strip()
    
    try:
        user_index = int(choice) - 1
        if user_index < 0 or user_index >= len(users):
            print("❌ Choix invalide!")
            return False
        
        seller = users[user_index]
    except ValueError:
        print("❌ Choix invalide!")
        return False
    
    # Convertir 110 FCFA en EUR
    price_fcfa = 110
    price_eur = round(price_fcfa / 655.957, 2)
    
    # Créer l'annonce
    post = Post.objects.create(
        author=seller,
        user=seller,
        title="🧪 TEST - Compte Free Fire",
        description="Annonce de test pour vérifier le système de paiement CinetPay.\n\n⚠️ CECI EST UN TEST - NE PAS ACHETER",
        game='FreeFire',
        price=Decimal(str(price_eur)),
        coins='1000 Diamants',
        level='10',
        is_on_sale=True,
        is_sold=False,
        is_in_transaction=False
    )
    
    print(f"\n✅ Annonce créée avec succès!")
    print(f"   ID: {post.id}")
    print(f"   Titre: {post.title}")
    print(f"   Prix: {post.price} EUR ({price_fcfa} FCFA)")
    print(f"   Vendeur: {seller.username}")
    print(f"   URL: https://blizz.boutique/product/{post.id}/")
    
    return True

def main():
    print("\n" + "="*80)
    print("🎮 CRÉATION D'ANNONCE DE TEST - 110 FCFA")
    print("="*80)
    
    print("\n💡 Options:")
    print("1. Modifier le prix d'une annonce existante")
    print("2. Créer une nouvelle annonce de test")
    
    choice = input("\n❓ Votre choix (1 ou 2): ").strip()
    
    if choice == '1':
        # Modifier une annonce existante
        posts = list_available_posts()
        
        if not posts:
            print("\n💡 Aucune annonce disponible. Création d'une nouvelle annonce...")
            create_test_post()
            return
        
        post_choice = input("\n❓ Choisir une annonce (numéro): ").strip()
        
        try:
            post_index = int(post_choice) - 1
            if post_index < 0 or post_index >= len(posts):
                print("❌ Choix invalide!")
                return
            
            selected_post = posts[post_index]
            change_post_price(selected_post, 110)
            
        except ValueError:
            print("❌ Choix invalide!")
            return
    
    elif choice == '2':
        # Créer une nouvelle annonce
        create_test_post()
    
    else:
        print("❌ Choix invalide!")
        return
    
    print("\n" + "="*80)
    print("🎉 TERMINÉ!")
    print("="*80)
    print("\n📝 Prochaines étapes:")
    print("   1. Aller sur https://blizz.boutique/")
    print("   2. Trouver l'annonce de test")
    print("   3. Cliquer sur 'Acheter'")
    print("   4. Payer avec CinetPay (110 FCFA)")
    print("   5. Vérifier que tout fonctionne!")
    print("\n💡 Pour annuler après le test:")
    print("   python3 cancel_test_transactions.py")
    print("\n💸 Pour rembourser:")
    print("   python3 refund_transaction.py")

if __name__ == '__main__':
    main()
