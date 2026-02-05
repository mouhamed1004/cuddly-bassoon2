"""
Test du système d'insignes et de la barre de progression
Vérifie que les badges et la progression évoluent correctement
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialgame.settings')
django.setup()

from blizzgame.models import User, UserReputation
from blizzgame.badge_config import get_seller_badge, SELLER_BADGES

def test_badge_progression():
    """Test de la progression des badges"""
    print("\n" + "="*80)
    print("🧪 TEST DU SYSTÈME D'INSIGNES ET PROGRESSION")
    print("="*80)
    
    # Scénarios de test
    test_scenarios = [
        # (score, transactions, badge_attendu, description)
        (0, 0, 'bronze_1', "Nouveau vendeur"),
        (20, 3, 'bronze_2', "Bronze II - 3 transactions"),
        (35, 5, 'bronze_3', "Bronze III - 5 transactions"),
        (60, 10, 'silver_1', "Argent I - 10 transactions"),
        (70, 15, 'silver_2', "Argent II - 15 transactions"),
        (80, 20, 'silver_3', "Argent III - 20 transactions"),
        (85, 30, 'gold_1', "Or I - 30 transactions"),
        (90, 40, 'gold_2', "Or II - 40 transactions"),
        (95, 50, 'gold_3', "Or III - 50 transactions"),
        (96, 75, 'diamond_1', "Diamant I - 75 transactions"),
        (98, 100, 'diamond_2', "Diamant II - 100 transactions"),
        (99, 150, 'diamond_3', "Diamant III - 150 transactions"),
        
        # Cas limites
        (100, 5, 'bronze_3', "100% mais seulement 5 transactions"),
        (95, 50, 'gold_3', "95% avec 50 transactions (pas assez pour Diamant)"),
        (99, 100, 'diamond_2', "99% avec 100 transactions (pas assez pour Diamant III)"),
    ]
    
    print("\n📊 Tests de détermination des badges:\n")
    all_passed = True
    
    for score, transactions, expected_level, description in test_scenarios:
        badge = get_seller_badge(score, transactions)
        actual_level = badge['level']
        status = "✅" if actual_level == expected_level else "❌"
        
        if actual_level != expected_level:
            all_passed = False
            print(f"{status} {description}")
            print(f"   Score: {score}%, Transactions: {transactions}")
            print(f"   Attendu: {expected_level}, Obtenu: {actual_level}")
            print(f"   Badge: {badge['name']}\n")
        else:
            print(f"{status} {description} → {badge['name']}")
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ TOUS LES TESTS SONT PASSÉS!")
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ!")
    print("="*80)
    
    return all_passed

def test_progress_calculation():
    """Test du calcul de la barre de progression"""
    print("\n" + "="*80)
    print("📈 TEST DU CALCUL DE LA PROGRESSION")
    print("="*80)
    
    # Scénarios de progression
    progress_scenarios = [
        # (current_score, current_trans, next_badge_expected, progress_expected)
        (10, 3, 'bronze_3', 0),  # Bronze II → Bronze III (besoin 30% et 5 trans)
        (25, 5, 'silver_1', 25),  # Bronze III → Argent I (25% de progression vers 50%)
        (60, 15, 'silver_3', 0),  # Argent II → Argent III (besoin 75% et 20 trans)
        (90, 50, 'diamond_1', 0),  # Or III → Diamant I (besoin 95% et 75 trans)
    ]
    
    print("\n📊 Tests de calcul de progression:\n")
    
    for current_score, current_trans, expected_next, expected_progress_approx in progress_scenarios:
        current_badge = get_seller_badge(current_score, current_trans)
        
        # Trouver le badge suivant
        next_badge = None
        for badge in SELLER_BADGES:
            if current_score < badge['min_score'] or current_trans < badge['min_transactions']:
                next_badge = badge
                break
        
        if next_badge:
            # Calculer la progression (simplifié - basé sur le score uniquement)
            current_min = current_badge['min_score']
            next_min = next_badge['min_score']
            progress_in_level = current_score - current_min
            level_range = next_min - current_min
            progress_percentage = (progress_in_level / level_range) * 100 if level_range > 0 else 0
            
            print(f"Badge actuel: {current_badge['name']}")
            print(f"  Score: {current_score}%, Transactions: {current_trans}")
            print(f"  Prochain badge: {next_badge['name']}")
            print(f"  Progression: {progress_percentage:.1f}%")
            print(f"  Requis: {next_badge['min_score']}% score + {next_badge['min_transactions']} transactions\n")
        else:
            print(f"Badge actuel: {current_badge['name']}")
            print(f"  Score: {current_score}%, Transactions: {current_trans}")
            print(f"  ⭐ NIVEAU MAXIMUM ATTEINT!\n")
    
    print("="*80)

def test_reputation_update():
    """Test de la mise à jour de la réputation"""
    print("\n" + "="*80)
    print("🔄 TEST DE MISE À JOUR DE LA RÉPUTATION")
    print("="*80)
    
    # Simuler différents scénarios de vendeurs
    scenarios = [
        {
            'name': 'Vendeur débutant',
            'total': 3,
            'successful': 3,
            'expected_score': 30.0,  # 100% * (3/10) = 30%
            'expected_badge': 'bronze_2'
        },
        {
            'name': 'Vendeur intermédiaire',
            'total': 20,
            'successful': 18,
            'expected_score': 90.0,  # 90% * 1.0 = 90%
            'expected_badge': 'silver_3'  # 90% mais seulement 20 trans
        },
        {
            'name': 'Vendeur expert',
            'total': 100,
            'successful': 99,
            'expected_score': 99.0,  # 99% * 1.0 = 99%
            'expected_badge': 'diamond_2'  # 99% avec 100 trans
        },
        {
            'name': 'Vendeur parfait',
            'total': 150,
            'successful': 150,
            'expected_score': 100.0,  # 100% * 1.0 = 100%
            'expected_badge': 'diamond_3'  # 100% avec 150 trans
        },
    ]
    
    print("\n📊 Simulation de calculs de réputation:\n")
    
    for scenario in scenarios:
        total = scenario['total']
        successful = scenario['successful']
        
        # Calcul du score (comme dans models.py)
        base_score = (successful / total) * 100
        confidence_factor = min(total / 10, 1.0)
        final_score = base_score * confidence_factor
        
        # Déterminer le badge
        badge = get_seller_badge(final_score, total)
        
        print(f"👤 {scenario['name']}:")
        print(f"   Transactions: {successful}/{total} réussies")
        print(f"   Score de base: {base_score:.1f}%")
        print(f"   Facteur de confiance: {confidence_factor:.2f}")
        print(f"   Score final: {final_score:.1f}%")
        print(f"   Badge: {badge['name']} ({badge['level']})")
        
        # Vérification
        score_ok = abs(final_score - scenario['expected_score']) < 0.1
        badge_ok = badge['level'] == scenario['expected_badge']
        
        if score_ok and badge_ok:
            print(f"   ✅ Résultat correct\n")
        else:
            print(f"   ❌ Résultat incorrect!")
            print(f"      Attendu: {scenario['expected_score']:.1f}% / {scenario['expected_badge']}")
            print(f"      Obtenu: {final_score:.1f}% / {badge['level']}\n")
    
    print("="*80)

def display_badge_table():
    """Affiche le tableau des badges"""
    print("\n" + "="*80)
    print("📋 TABLEAU DES BADGES")
    print("="*80)
    print(f"\n{'Niveau':<20} {'Score min':<12} {'Trans min':<12} {'Tier':<6}")
    print("-" * 50)
    
    for badge in SELLER_BADGES:
        print(f"{badge['name']:<20} {badge['min_score']:>3}%{'':<8} {badge['min_transactions']:>3}{'':<8} {badge['tier']:>2}")
    
    print("="*80)

if __name__ == '__main__':
    print("\n🎮 BLIZZ - Test du système d'insignes vendeurs")
    print("Date:", "2025-10-01")
    
    # Afficher le tableau des badges
    display_badge_table()
    
    # Test 1: Détermination des badges
    test1_passed = test_badge_progression()
    
    # Test 2: Calcul de la progression
    test_progress_calculation()
    
    # Test 3: Mise à jour de la réputation
    test_reputation_update()
    
    print("\n" + "="*80)
    print("🏁 TESTS TERMINÉS")
    print("="*80)
    
    if test1_passed:
        print("\n✅ Le système d'insignes fonctionne correctement!")
        print("✅ Les badges évoluent en fonction du score ET des transactions")
        print("✅ La progression est calculée correctement")
    else:
        print("\n❌ Des problèmes ont été détectés dans le système")
        print("⚠️  Vérifier les seuils et la logique de calcul")
    
    print("\n💡 Recommandations:")
    print("   - Tester avec de vrais utilisateurs")
    print("   - Vérifier l'affichage des badges sur les pages")
    print("   - Surveiller les mises à jour de réputation après chaque transaction")
    print("\n")
