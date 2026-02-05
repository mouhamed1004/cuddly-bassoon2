from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q
from blizzgame.models import Highlight, User
from collections import Counter
import json
import re
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Génère des suggestions de hashtags intelligentes pour améliorer la découvrabilité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            default='hashtag_suggestions.json',
            help='Fichier de sortie pour les suggestions (JSON)',
        )
        parser.add_argument(
            '--min-frequency',
            type=int,
            default=3,
            help='Fréquence minimale pour qu\'un hashtag soit suggéré',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Génération des suggestions de hashtags...')
        )
        
        suggestions = self.generate_hashtag_suggestions(options['min_frequency'])
        
        # Sauvegarder les suggestions
        output_file = options['output_file']
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(suggestions, f, ensure_ascii=False, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f'Suggestions sauvegardées dans {output_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la sauvegarde: {e}')
            )
        
        # Afficher un résumé
        self.display_suggestions_summary(suggestions)

    def generate_hashtag_suggestions(self, min_frequency=3):
        """Génère des suggestions de hashtags basées sur l'analyse du contenu"""
        suggestions = {
            'trending': [],
            'popular': [],
            'gaming_related': [],
            'emotion_based': [],
            'time_based': [],
            'combinations': [],
            'categories': {}
        }
        
        try:
            # Analyser les hashtags existants
            recent_highlights = Highlight.objects.filter(
                is_active=True,
                created_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).values_list('hashtags', 'caption', flat=False)
            
            all_hashtags = []
            captions = []
            
            for hashtags, caption in recent_highlights:
                if hashtags:
                    all_hashtags.extend([tag.lower() for tag in hashtags])
                if caption:
                    captions.append(caption.lower())
            
            # Hashtags populaires
            hashtag_counts = Counter(all_hashtags)
            popular_hashtags = [
                {'tag': tag, 'count': count} 
                for tag, count in hashtag_counts.most_common(50)
                if count >= min_frequency
            ]
            suggestions['popular'] = popular_hashtags
            
            # Hashtags tendances (dernières 7 jours)
            trending_hashtags = self.get_trending_hashtags()
            suggestions['trending'] = trending_hashtags
            
            # Hashtags gaming
            gaming_keywords = [
                'gaming', 'game', 'play', 'player', 'win', 'victory', 'defeat',
                'clutch', 'epic', 'pro', 'noob', 'skill', 'combo', 'kill',
                'headshot', 'ace', 'mvp', 'team', 'solo', 'duo', 'squad',
                'battle', 'fight', 'war', 'arena', 'tournament', 'esport',
                'freefire', 'pubg', 'fortnite', 'valorant', 'lol', 'cod',
                'mobile', 'pc', 'console', 'stream', 'live', 'gameplay'
            ]
            
            gaming_hashtags = [
                {'tag': tag, 'count': count}
                for tag, count in hashtag_counts.items()
                if any(keyword in tag for keyword in gaming_keywords) and count >= min_frequency
            ]
            suggestions['gaming_related'] = gaming_hashtags
            
            # Hashtags émotionnels
            emotion_keywords = [
                'happy', 'sad', 'angry', 'excited', 'surprised', 'love',
                'hate', 'fun', 'boring', 'amazing', 'awesome', 'terrible',
                'good', 'bad', 'best', 'worst', 'cool', 'hot', 'fire',
                'lit', 'crazy', 'insane', 'wild', 'chill', 'relax'
            ]
            
            emotion_hashtags = [
                {'tag': tag, 'count': count}
                for tag, count in hashtag_counts.items()
                if any(keyword in tag for keyword in emotion_keywords) and count >= min_frequency
            ]
            suggestions['emotion_based'] = emotion_hashtags
            
            # Hashtags temporels
            time_keywords = [
                'morning', 'afternoon', 'evening', 'night', 'today', 'yesterday',
                'weekend', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                'saturday', 'sunday', 'daily', 'weekly', 'monthly'
            ]
            
            time_hashtags = [
                {'tag': tag, 'count': count}
                for tag, count in hashtag_counts.items()
                if any(keyword in tag for keyword in time_keywords) and count >= min_frequency
            ]
            suggestions['time_based'] = time_hashtags
            
            # Combinaisons populaires
            combinations = self.find_hashtag_combinations(recent_highlights)
            suggestions['combinations'] = combinations
            
            # Catégoriser les hashtags
            categories = self.categorize_hashtags(hashtag_counts, min_frequency)
            suggestions['categories'] = categories
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des suggestions: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {e}')
            )
            return suggestions

    def get_trending_hashtags(self):
        """Récupère les hashtags tendances des 7 derniers jours"""
        try:
            week_ago = timezone.now() - timezone.timedelta(days=7)
            recent_highlights = Highlight.objects.filter(
                is_active=True,
                created_at__gte=week_ago
            ).prefetch_related('appreciations', 'views')
            
            hashtag_scores = {}
            
            for highlight in recent_highlights:
                if not highlight.hashtags:
                    continue
                
                # Score basé sur l'engagement récent
                engagement_score = (
                    highlight.appreciations.count() * 5 +
                    highlight.views.count() * 2 +
                    highlight.comments.count() * 3
                )
                
                for hashtag in highlight.hashtags:
                    hashtag_lower = hashtag.lower()
                    if hashtag_lower not in hashtag_scores:
                        hashtag_scores[hashtag_lower] = 0
                    hashtag_scores[hashtag_lower] += engagement_score + 1
            
            trending = [
                {'tag': tag, 'score': score}
                for tag, score in sorted(hashtag_scores.items(), key=lambda x: x[1], reverse=True)[:20]
            ]
            
            return trending
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tendances: {e}")
            return []

    def find_hashtag_combinations(self, highlights_data):
        """Trouve les combinaisons de hashtags les plus populaires"""
        try:
            combinations = Counter()
            
            for hashtags, caption in highlights_data:
                if hashtags and len(hashtags) >= 2:
                    # Créer toutes les combinaisons de 2 hashtags
                    hashtags_lower = [tag.lower() for tag in hashtags]
                    for i in range(len(hashtags_lower)):
                        for j in range(i + 1, len(hashtags_lower)):
                            combo = tuple(sorted([hashtags_lower[i], hashtags_lower[j]]))
                            combinations[combo] += 1
            
            popular_combinations = [
                {'tags': list(combo), 'count': count}
                for combo, count in combinations.most_common(20)
                if count >= 3
            ]
            
            return popular_combinations
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de combinaisons: {e}")
            return []

    def categorize_hashtags(self, hashtag_counts, min_frequency):
        """Catégorise les hashtags par thème"""
        categories = {
            'Gaming': [],
            'Emotions': [],
            'Actions': [],
            'Time': [],
            'Social': [],
            'Performance': [],
            'Other': []
        }
        
        category_keywords = {
            'Gaming': ['game', 'play', 'gaming', 'gamer', 'esport', 'tournament', 'battle', 'fight', 'war', 'arena', 'freefire', 'pubg', 'fortnite', 'valorant', 'lol', 'cod', 'mobile', 'pc', 'console'],
            'Emotions': ['happy', 'sad', 'angry', 'excited', 'love', 'hate', 'fun', 'amazing', 'awesome', 'cool', 'fire', 'lit', 'crazy', 'insane', 'wild', 'chill'],
            'Actions': ['kill', 'headshot', 'clutch', 'ace', 'win', 'victory', 'defeat', 'combo', 'skill', 'pro', 'mvp', 'stream', 'live', 'gameplay'],
            'Time': ['morning', 'afternoon', 'evening', 'night', 'today', 'weekend', 'daily', 'weekly'],
            'Social': ['team', 'solo', 'duo', 'squad', 'friend', 'together', 'vs', 'challenge', 'competition'],
            'Performance': ['best', 'worst', 'good', 'bad', 'epic', 'fail', 'success', 'record', 'new', 'first']
        }
        
        try:
            for hashtag, count in hashtag_counts.items():
                if count < min_frequency:
                    continue
                
                categorized = False
                for category, keywords in category_keywords.items():
                    if any(keyword in hashtag.lower() for keyword in keywords):
                        categories[category].append({'tag': hashtag, 'count': count})
                        categorized = True
                        break
                
                if not categorized:
                    categories['Other'].append({'tag': hashtag, 'count': count})
            
            # Trier chaque catégorie par popularité
            for category in categories:
                categories[category].sort(key=lambda x: x['count'], reverse=True)
            
            return categories
            
        except Exception as e:
            logger.error(f"Erreur lors de la catégorisation: {e}")
            return categories

    def display_suggestions_summary(self, suggestions):
        """Affiche un résumé des suggestions générées"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('RÉSUMÉ DES SUGGESTIONS DE HASHTAGS'))
        self.stdout.write('='*50)
        
        # Hashtags tendances
        if suggestions['trending']:
            self.stdout.write('\n🔥 TOP 5 HASHTAGS TENDANCES:')
            for i, item in enumerate(suggestions['trending'][:5], 1):
                self.stdout.write(f'{i}. #{item["tag"]} (score: {item["score"]})')
        
        # Hashtags populaires
        if suggestions['popular']:
            self.stdout.write('\n📈 TOP 5 HASHTAGS POPULAIRES:')
            for i, item in enumerate(suggestions['popular'][:5], 1):
                self.stdout.write(f'{i}. #{item["tag"]} ({item["count"]} utilisations)')
        
        # Combinaisons populaires
        if suggestions['combinations']:
            self.stdout.write('\n🔗 TOP 3 COMBINAISONS POPULAIRES:')
            for i, combo in enumerate(suggestions['combinations'][:3], 1):
                tags = ' + '.join([f'#{tag}' for tag in combo['tags']])
                self.stdout.write(f'{i}. {tags} ({combo["count"]} fois)')
        
        # Statistiques par catégorie
        self.stdout.write('\n📊 STATISTIQUES PAR CATÉGORIE:')
        for category, hashtags in suggestions['categories'].items():
            if hashtags:
                self.stdout.write(f'{category}: {len(hashtags)} hashtags')
        
        self.stdout.write('\n' + '='*50)
