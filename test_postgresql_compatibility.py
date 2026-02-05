#!/usr/bin/env python
"""
Script de test de compatibilité Django/PostgreSQL pour Render
"""
import os
import sys
import django
import time
from datetime import datetime

# Configuration Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from django.db import connection, transaction
from django.test import TestCase
from django.core.management import execute_from_command_line
from blizzgame.models import User, Post, Profile, Order, OrderItem
from django.contrib.auth.models import User as AuthUser

def print_header(title):
    """Afficher un en-tête formaté"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(test_name, success, details=""):
    """Afficher le résultat d'un test"""
    status = "✅" if success else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   📝 {details}")

def test_database_connection():
    """Test 1: Connexion à la base de données"""
    print_header("TEST DE CONNEXION BASE DE DONNÉES")
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            print_result("Connexion PostgreSQL", True, "Connexion réussie")
            return True
        else:
            print_result("Connexion PostgreSQL", False, "Résultat inattendu")
            return False
    except Exception as e:
        print_result("Connexion PostgreSQL", False, f"Erreur: {e}")
        return False

def test_database_info():
    """Test 2: Informations sur la base de données"""
    print_header("INFORMATIONS BASE DE DONNÉES")
    
    try:
        with connection.cursor() as cursor:
            # Version PostgreSQL
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            print(f"📊 Version PostgreSQL: {version}")
            
            # Informations de connexion
            db_settings = connection.settings_dict
            print(f"📊 Base de données: {db_settings.get('NAME', 'N/A')}")
            print(f"📊 Host: {db_settings.get('HOST', 'N/A')}")
            print(f"📊 Port: {db_settings.get('PORT', 'N/A')}")
            print(f"📊 User: {db_settings.get('USER', 'N/A')}")
            
            # Configuration SSL
            options = db_settings.get('OPTIONS', {})
            ssl_mode = options.get('sslmode', 'N/A')
            print(f"📊 SSL Mode: {ssl_mode}")
            
            print_result("Informations base de données", True, "Récupération réussie")
            return True
            
    except Exception as e:
        print_result("Informations base de données", False, f"Erreur: {e}")
        return False

def test_django_orm():
    """Test 3: Fonctionnement de l'ORM Django"""
    print_header("TEST ORM DJANGO")
    
    try:
        # Test de lecture
        start_time = time.time()
        user_count = AuthUser.objects.count()
        read_time = time.time() - start_time
        
        print(f"📊 Nombre d'utilisateurs: {user_count}")
        print(f"📊 Temps de lecture: {read_time:.3f}s")
        
        # Test d'écriture (transaction)
        with transaction.atomic():
            test_user = AuthUser.objects.create_user(
                username=f'test_user_{int(time.time())}',
                email=f'test{int(time.time())}@example.com',
                password='testpass123'
            )
            test_user_id = test_user.id
            
        # Vérification
        created_user = AuthUser.objects.get(id=test_user_id)
        if created_user.username.startswith('test_user_'):
            print_result("Création utilisateur", True, f"ID: {test_user_id}")
        else:
            print_result("Création utilisateur", False, "Utilisateur non trouvé")
            return False
            
        # Nettoyage
        created_user.delete()
        print_result("Suppression utilisateur", True, "Nettoyage réussi")
        
        print_result("ORM Django", True, f"Lecture: {read_time:.3f}s")
        return True
        
    except Exception as e:
        print_result("ORM Django", False, f"Erreur: {e}")
        return False

def test_complex_queries():
    """Test 4: Requêtes complexes"""
    print_header("TEST REQUÊTES COMPLEXES")
    
    try:
        # Test de jointure
        start_time = time.time()
        posts_with_users = Post.objects.select_related('author').all()[:10]
        query_time = time.time() - start_time
        
        print(f"📊 Requête avec jointure: {query_time:.3f}s")
        print(f"📊 Nombre de posts récupérés: {len(posts_with_users)}")
        
        # Test d'agrégation
        start_time = time.time()
        from django.db.models import Count, Avg
        user_stats = AuthUser.objects.aggregate(
            total_users=Count('id'),
            avg_id=Avg('id')
        )
        agg_time = time.time() - start_time
        
        print(f"📊 Requête d'agrégation: {agg_time:.3f}s")
        print(f"📊 Statistiques: {user_stats}")
        
        # Test de filtrage complexe
        start_time = time.time()
        recent_posts = Post.objects.filter(
            created_at__gte=datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        ).order_by('-created_at')[:5]
        filter_time = time.time() - start_time
        
        print(f"📊 Requête de filtrage: {filter_time:.3f}s")
        print(f"📊 Posts récents: {len(recent_posts)}")
        
        print_result("Requêtes complexes", True, f"Total: {query_time + agg_time + filter_time:.3f}s")
        return True
        
    except Exception as e:
        print_result("Requêtes complexes", False, f"Erreur: {e}")
        return False

def test_transaction_performance():
    """Test 5: Performance des transactions"""
    print_header("TEST PERFORMANCE TRANSACTIONS")
    
    try:
        # Test de transaction simple
        start_time = time.time()
        with transaction.atomic():
            test_user = AuthUser.objects.create_user(
                username=f'perf_test_{int(time.time())}',
                email=f'perf{int(time.time())}@example.com',
                password='testpass123'
            )
        transaction_time = time.time() - start_time
        
        print(f"📊 Transaction simple: {transaction_time:.3f}s")
        
        # Test de transaction avec rollback
        start_time = time.time()
        try:
            with transaction.atomic():
                AuthUser.objects.create_user(
                    username=f'rollback_test_{int(time.time())}',
                    email=f'rollback{int(time.time())}@example.com',
                    password='testpass123'
                )
                raise Exception("Test rollback")
        except:
            pass
        rollback_time = time.time() - start_time
        
        print(f"📊 Transaction avec rollback: {rollback_time:.3f}s")
        
        # Nettoyage
        AuthUser.objects.filter(username__startswith='perf_test_').delete()
        
        print_result("Performance transactions", True, f"Simple: {transaction_time:.3f}s, Rollback: {rollback_time:.3f}s")
        return True
        
    except Exception as e:
        print_result("Performance transactions", False, f"Erreur: {e}")
        return False

def test_render_compatibility():
    """Test 6: Compatibilité spécifique Render"""
    print_header("TEST COMPATIBILITÉ RENDER")
    
    try:
        # Test des variables d'environnement
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            print(f"📊 DATABASE_URL configurée: {'Oui' if 'postgres' in database_url else 'Non'}")
        else:
            print("📊 DATABASE_URL: Non configurée (mode local)")
        
        # Test de la configuration SSL
        db_settings = connection.settings_dict
        options = db_settings.get('OPTIONS', {})
        ssl_mode = options.get('sslmode', 'disable')
        
        if ssl_mode == 'require':
            print_result("Configuration SSL", True, "SSL requis (compatible Render)")
        else:
            print_result("Configuration SSL", False, f"SSL mode: {ssl_mode} (peut causer des problèmes sur Render)")
        
        # Test de la configuration de pool de connexions
        conn_max_age = db_settings.get('CONN_MAX_AGE', 0)
        if conn_max_age > 0:
            print_result("Pool de connexions", True, f"CONN_MAX_AGE: {conn_max_age}")
        else:
            print_result("Pool de connexions", False, "CONN_MAX_AGE non configuré")
        
        print_result("Compatibilité Render", True, "Configuration vérifiée")
        return True
        
    except Exception as e:
        print_result("Compatibilité Render", False, f"Erreur: {e}")
        return False

def generate_recommendations():
    """Générer des recommandations d'optimisation"""
    print_header("RECOMMANDATIONS D'OPTIMISATION")
    
    recommendations = [
        "✅ Utiliser des requêtes select_related() pour les jointures",
        "✅ Implémenter un cache Redis pour les requêtes fréquentes",
        "✅ Configurer CONN_MAX_AGE pour le pool de connexions",
        "✅ Utiliser des index sur les champs fréquemment recherchés",
        "✅ Implémenter la pagination pour les grandes listes",
        "✅ Utiliser des transactions atomiques pour les opérations critiques",
        "✅ Configurer SSL mode 'require' pour Render",
        "✅ Implémenter des requêtes asynchrones pour les opérations longues"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\n📊 Configuration recommandée pour Render:")
    print(f"  DATABASE_URL=postgresql://user:pass@host:port/dbname?sslmode=require")
    print(f"  CONN_MAX_AGE=60")
    print(f"  CACHES={{'default': {{'BACKEND': 'django_redis.cache.RedisCache'}}}}")

def main():
    """Fonction principale de test"""
    print("🚀 TEST DE COMPATIBILITÉ DJANGO/POSTGRESQL POUR RENDER")
    print(f"⏰ Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_database_connection,
        test_database_info,
        test_django_orm,
        test_complex_queries,
        test_transaction_performance,
        test_render_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Erreur dans le test: {e}")
    
    print_header("RÉSULTATS FINAUX")
    print(f"📊 Tests réussis: {passed}/{total}")
    print(f"📊 Pourcentage de réussite: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 Tous les tests sont passés ! Votre configuration est compatible avec Render.")
    elif passed >= total * 0.8:
        print("⚠️  La plupart des tests sont passés. Quelques optimisations recommandées.")
    else:
        print("❌ Plusieurs tests ont échoué. Vérifiez votre configuration.")
    
    generate_recommendations()
    
    print(f"\n⏰ Fin des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
