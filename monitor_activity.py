#!/usr/bin/env python3
"""
Script de monitoring de l'activité utilisateur sur Blizz Gaming
Affiche les dernières connexions, inscriptions et activités
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.contrib.auth.models import User
from blizzgame.models import Post, Transaction, Profile, Notification, Message, Chat


def print_header(title):
    """Affiche un en-tête formaté"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")


def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{'─'*80}")
    print(f"  {title}")
    print(f"{'─'*80}")


def get_user_last_activity(user):
    """
    Détermine la dernière activité d'un utilisateur
    """
    activities = []
    
    # Dernière annonce créée
    last_post = Post.objects.filter(author=user).order_by('-created_at').first()
    if last_post:
        activities.append(('Annonce créée', last_post.created_at))
    
    # Dernier message envoyé
    last_message = Message.objects.filter(sender=user).order_by('-created_at').first()
    if last_message:
        activities.append(('Message envoyé', last_message.created_at))
    
    # Dernière transaction
    last_transaction = Transaction.objects.filter(
        models.Q(buyer=user) | models.Q(seller=user)
    ).order_by('-created_at').first()
    if last_transaction:
        activities.append(('Transaction', last_transaction.created_at))
    
    # Dernière notification lue
    last_notif = Notification.objects.filter(user=user, is_read=True).order_by('-created_at').first()
    if last_notif:
        activities.append(('Notification lue', last_notif.created_at))
    
    # Retourner l'activité la plus récente
    if activities:
        activities.sort(key=lambda x: x[1], reverse=True)
        return activities[0]
    
    return ('Aucune activité', user.date_joined)


def format_time_ago(dt):
    """
    Formate un datetime en temps relatif (il y a X minutes/heures/jours)
    """
    if not dt:
        return "Jamais"
    
    now = timezone.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"Il y a {int(seconds)}s"
    elif seconds < 3600:
        return f"Il y a {int(seconds/60)}min"
    elif seconds < 86400:
        return f"Il y a {int(seconds/3600)}h"
    elif seconds < 604800:
        return f"Il y a {int(seconds/86400)}j"
    else:
        return dt.strftime("%d/%m/%Y %H:%M")


def monitor_recent_signups(hours=24):
    """
    Affiche les inscriptions récentes
    """
    print_section(f"📝 INSCRIPTIONS DES DERNIÈRES {hours}H")
    
    cutoff = timezone.now() - timedelta(hours=hours)
    recent_users = User.objects.filter(date_joined__gte=cutoff).order_by('-date_joined')
    
    if not recent_users:
        print(f"❌ Aucune inscription dans les dernières {hours}h")
        return
    
    print(f"✅ {recent_users.count()} inscription(s) récente(s):\n")
    
    for i, user in enumerate(recent_users, 1):
        profile = Profile.objects.filter(user=user).first()
        
        print(f"{i}. {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Inscrit: {format_time_ago(user.date_joined)} ({user.date_joined.strftime('%d/%m/%Y %H:%M')})")
        print(f"   Email vérifié: {'✅ Oui' if user.emailaddress_set.filter(verified=True).exists() else '❌ Non'}")
        
        if profile:
            print(f"   Score: {profile.score}")
            badge = profile.badge if hasattr(profile, 'badge') else 'N/A'
            print(f"   Badge: {badge}")
        
        # Activité
        activity_type, activity_time = get_user_last_activity(user)
        print(f"   Dernière activité: {activity_type} - {format_time_ago(activity_time)}")
        print()


def monitor_active_users(hours=24):
    """
    Affiche les utilisateurs actifs récemment
    """
    print_section(f"👥 UTILISATEURS ACTIFS ({hours}H)")
    
    cutoff = timezone.now() - timedelta(hours=hours)
    
    # Récupérer les IDs des utilisateurs actifs
    active_poster_ids = set(Post.objects.filter(created_at__gte=cutoff).values_list('author_id', flat=True))
    active_chatter_ids = set(Message.objects.filter(created_at__gte=cutoff).values_list('sender_id', flat=True))
    active_buyer_ids = set(Transaction.objects.filter(created_at__gte=cutoff).values_list('buyer_id', flat=True))
    active_seller_ids = set(Transaction.objects.filter(created_at__gte=cutoff).values_list('seller_id', flat=True))
    
    # Combiner tous les IDs
    all_active_ids = active_poster_ids | active_chatter_ids | active_buyer_ids | active_seller_ids
    
    # Récupérer les objets User
    all_active = User.objects.filter(id__in=all_active_ids)
    
    if not all_active:
        print(f"❌ Aucun utilisateur actif dans les dernières {hours}h")
        return
    
    print(f"✅ {len(all_active)} utilisateur(s) actif(s):\n")
    
    # Trier par dernière activité
    active_list = []
    for user in all_active:
        activity_type, activity_time = get_user_last_activity(user)
        active_list.append((user, activity_type, activity_time))
    
    active_list.sort(key=lambda x: x[2], reverse=True)
    
    for i, (user, activity_type, activity_time) in enumerate(active_list, 1):
        print(f"{i}. {user.username}")
        print(f"   Dernière activité: {activity_type}")
        print(f"   Quand: {format_time_ago(activity_time)} ({activity_time.strftime('%d/%m/%Y %H:%M')})")
        print()


def monitor_recent_posts(hours=24):
    """
    Affiche les annonces récentes
    """
    print_section(f"🎮 ANNONCES CRÉÉES ({hours}H)")
    
    cutoff = timezone.now() - timedelta(hours=hours)
    recent_posts = Post.objects.filter(created_at__gte=cutoff).order_by('-created_at')
    
    if not recent_posts:
        print(f"❌ Aucune annonce créée dans les dernières {hours}h")
        return
    
    print(f"✅ {recent_posts.count()} annonce(s) créée(s):\n")
    
    for i, post in enumerate(recent_posts, 1):
        print(f"{i}. {post.title}")
        print(f"   Vendeur: {post.author.username}")
        print(f"   Jeu: {post.get_game_type_display()}")
        print(f"   Prix: {post.price}€")
        print(f"   Créée: {format_time_ago(post.created_at)} ({post.created_at.strftime('%d/%m/%Y %H:%M')})")
        print(f"   Statut: {'✅ En vente' if post.is_on_sale else '❌ Indisponible'}")
        print()


def monitor_recent_transactions(hours=24):
    """
    Affiche les transactions récentes
    """
    print_section(f"💰 TRANSACTIONS ({hours}H)")
    
    cutoff = timezone.now() - timedelta(hours=hours)
    recent_transactions = Transaction.objects.filter(created_at__gte=cutoff).order_by('-created_at')
    
    if not recent_transactions:
        print(f"❌ Aucune transaction dans les dernières {hours}h")
        return
    
    print(f"✅ {recent_transactions.count()} transaction(s):\n")
    
    for i, transaction in enumerate(recent_transactions, 1):
        print(f"{i}. Transaction #{transaction.id}")
        print(f"   Acheteur: {transaction.buyer.username}")
        print(f"   Vendeur: {transaction.seller.username}")
        print(f"   Produit: {transaction.post.title if transaction.post else 'N/A'}")
        print(f"   Montant: {transaction.amount}€")
        print(f"   Statut: {transaction.get_status_display()}")
        print(f"   Créée: {format_time_ago(transaction.created_at)} ({transaction.created_at.strftime('%d/%m/%Y %H:%M')})")
        print()


def monitor_statistics():
    """
    Affiche les statistiques globales
    """
    print_section("📊 STATISTIQUES GLOBALES")
    
    total_users = User.objects.count()
    total_posts = Post.objects.count()
    total_transactions = Transaction.objects.count()
    
    # Utilisateurs avec email vérifié
    verified_users = User.objects.filter(emailaddress__verified=True).distinct().count()
    
    # Annonces en vente
    posts_on_sale = Post.objects.filter(is_on_sale=True).count()
    
    # Transactions complétées
    completed_transactions = Transaction.objects.filter(status='completed').count()
    
    # Utilisateurs actifs (dernières 24h)
    cutoff_24h = timezone.now() - timedelta(hours=24)
    
    # Compter séparément puis combiner
    users_with_posts = set(Post.objects.filter(created_at__gte=cutoff_24h).values_list('author_id', flat=True))
    users_with_messages = set(Message.objects.filter(created_at__gte=cutoff_24h).values_list('sender_id', flat=True))
    users_as_buyers = set(Transaction.objects.filter(created_at__gte=cutoff_24h).values_list('buyer_id', flat=True))
    users_as_sellers = set(Transaction.objects.filter(created_at__gte=cutoff_24h).values_list('seller_id', flat=True))
    
    active_24h = len(users_with_posts | users_with_messages | users_as_buyers | users_as_sellers)
    
    # Utilisateurs actifs (derniers 7 jours)
    cutoff_7d = timezone.now() - timedelta(days=7)
    
    users_with_posts_7d = set(Post.objects.filter(created_at__gte=cutoff_7d).values_list('author_id', flat=True))
    users_with_messages_7d = set(Message.objects.filter(created_at__gte=cutoff_7d).values_list('sender_id', flat=True))
    users_as_buyers_7d = set(Transaction.objects.filter(created_at__gte=cutoff_7d).values_list('buyer_id', flat=True))
    users_as_sellers_7d = set(Transaction.objects.filter(created_at__gte=cutoff_7d).values_list('seller_id', flat=True))
    
    active_7d = len(users_with_posts_7d | users_with_messages_7d | users_as_buyers_7d | users_as_sellers_7d)
    
    print(f"👥 Utilisateurs:")
    print(f"   Total: {total_users}")
    print(f"   Email vérifié: {verified_users} ({verified_users/total_users*100:.1f}%)" if total_users > 0 else "   Email vérifié: 0")
    print(f"   Actifs 24h: {active_24h}")
    print(f"   Actifs 7j: {active_7d}")
    
    print(f"\n🎮 Annonces:")
    print(f"   Total: {total_posts}")
    print(f"   En vente: {posts_on_sale} ({posts_on_sale/total_posts*100:.1f}%)" if total_posts > 0 else "   En vente: 0")
    
    print(f"\n💰 Transactions:")
    print(f"   Total: {total_transactions}")
    print(f"   Complétées: {completed_transactions} ({completed_transactions/total_transactions*100:.1f}%)" if total_transactions > 0 else "   Complétées: 0")
    
    print()


def main():
    """
    Fonction principale
    """
    print_header("🔍 MONITORING ACTIVITÉ BLIZZ GAMING")
    print(f"📅 Date: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Statistiques globales
    monitor_statistics()
    
    # Inscriptions récentes (24h)
    monitor_recent_signups(hours=24)
    
    # Utilisateurs actifs (24h)
    monitor_active_users(hours=24)
    
    # Annonces récentes (24h)
    monitor_recent_posts(hours=24)
    
    # Transactions récentes (24h)
    monitor_recent_transactions(hours=24)
    
    # Inscriptions dernière semaine
    print_section("📊 INSCRIPTIONS DERNIÈRE SEMAINE")
    cutoff_7d = timezone.now() - timedelta(days=7)
    signups_7d = User.objects.filter(date_joined__gte=cutoff_7d).count()
    print(f"Total: {signups_7d} inscription(s)")
    
    # Répartition par jour
    for i in range(7):
        day_start = timezone.now() - timedelta(days=i+1)
        day_end = timezone.now() - timedelta(days=i)
        day_signups = User.objects.filter(date_joined__gte=day_start, date_joined__lt=day_end).count()
        print(f"  {day_start.strftime('%d/%m')}: {day_signups} inscription(s)")
    
    print("\n" + "="*80)
    print("✅ Monitoring terminé")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Import models.Q pour les requêtes complexes
    from django.db import models
    
    main()
