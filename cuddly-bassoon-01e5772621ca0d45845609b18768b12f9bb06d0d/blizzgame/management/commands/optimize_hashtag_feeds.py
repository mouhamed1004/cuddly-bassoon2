from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q, F
from blizzgame.models import Highlight, HighlightAppreciation, HighlightView, User
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimise les feeds basés sur les hashtags et met à jour les scores de pertinence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID utilisateur spécifique pour optimiser son feed personnalisé',
        )
        parser.add_argument(
            '--update-trending',
            action='store_true',
            help='Met à jour les hashtags tendances',
        )
        parser.add_argument(
            '--analyze-engagement',
            action='store_true',
            help='Analyse l\'engagement par hashtag',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Démarrage de l\'optimisation des feeds hashtags...')
        )
        
        if options['user_id']:
            self.optimize_user_feed(options['user_id'])
        
        if options['update_trending']:
            self.update_trending_hashtags()
        
        if options['analyze_engagement']:
            self.analyze_hashtag_engagement()
        
        if not any([options['user_id'], options['update_trending'], options['analyze_engagement']]):
            # Par défaut, exécuter toutes les optimisations
            self.update_trending_hashtags()
            self.analyze_hashtag_engagement()
            self.optimize_global_feeds()
        
        self.stdout.write(
            self.style.SUCCESS('Optimisation des feeds terminée avec succès!')
        )

    def optimize_user_feed(self, user_id):
        """Optimise le feed personnalisé d'un utilisateur basé sur ses hashtags préférés"""
        try:
            user = User.objects.get(id=user_id)
            
            # Récupérer les hashtags des highlights appréciés par l'utilisateur
            appreciated_highlights = Highlight.objects.filter(
                appreciations__user=user,
                appreciations__level__gte=4,  # Niveaux 4, 5, 6 (positifs)
                is_active=True
            ).values_list('hashtags', flat=True)
            
            user_hashtags = []
            for hashtag_list in appreciated_highlights:
                if hashtag_list:
                    user_hashtags.extend(hashtag_list)
            
            hashtag_counts = Counter(user_hashtags)
            top_hashtags = [tag for tag, count in hashtag_counts.most_common(15)]
            
            self.stdout.write(f'Hashtags préférés de {user.username}: {", ".join(top_hashtags[:5])}')
            
            # Calculer le score de pertinence pour les nouveaux highlights
            recent_highlights = Highlight.objects.filter(
                is_active=True,
                expires_at__gt=timezone.now(),
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).exclude(author=user)
            
            relevant_highlights = []
            for highlight in recent_highlights:
                score = self.calculate_relevance_score(highlight, top_hashtags)
                if score > 0:
                    relevant_highlights.append((highlight, score))
            
            relevant_highlights.sort(key=lambda x: x[1], reverse=True)
            
            self.stdout.write(f'Trouvé {len(relevant_highlights)} highlights pertinents pour {user.username}')
            
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Utilisateur avec ID {user_id} non trouvé')
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation du feed utilisateur: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {e}')
            )

    def calculate_relevance_score(self, highlight, user_hashtags):
        """Calcule le score de pertinence d'un highlight pour un utilisateur"""
        score = 0
        
        if not highlight.hashtags:
            return score
        
        # Points pour hashtags correspondants
        for hashtag in highlight.hashtags:
            if hashtag.lower() in [tag.lower() for tag in user_hashtags]:
                score += 10
        
        # Bonus pour engagement récent
        recent_appreciations = highlight.appreciations.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=6)
        ).count()
        score += recent_appreciations * 2
        
        # Bonus pour vues récentes
        recent_views = highlight.views.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=6)
        ).count()
        score += recent_views
        
        return score

    def update_trending_hashtags(self):
        """Met à jour la liste des hashtags tendances"""
        try:
            # Hashtags des dernières 24h avec pondération par engagement
            recent_highlights = Highlight.objects.filter(
                is_active=True,
                created_at__gte=timezone.now() - timezone.timedelta(hours=24)
            ).prefetch_related('appreciations', 'views')
            
            hashtag_scores = {}
            
            for highlight in recent_highlights:
                if not highlight.hashtags:
                    continue
                
                # Score basé sur l'engagement
                engagement_score = (
                    highlight.appreciations.count() * 3 +
                    highlight.views.count() * 1 +
                    highlight.comments.count() * 2
                )
                
                for hashtag in highlight.hashtags:
                    hashtag_lower = hashtag.lower()
                    if hashtag_lower not in hashtag_scores:
                        hashtag_scores[hashtag_lower] = 0
                    hashtag_scores[hashtag_lower] += engagement_score + 1
            
            # Trier par score
            trending_hashtags = sorted(
                hashtag_scores.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:20]
            
            self.stdout.write('Top 10 hashtags tendances:')
            for i, (hashtag, score) in enumerate(trending_hashtags[:10], 1):
                self.stdout.write(f'{i}. #{hashtag} (score: {score})')
            
            return [hashtag for hashtag, score in trending_hashtags]
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des hashtags tendances: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {e}')
            )
            return []

    def analyze_hashtag_engagement(self):
        """Analyse l'engagement par hashtag pour optimiser les recommandations"""
        try:
            # Analyser les hashtags des 7 derniers jours
            week_ago = timezone.now() - timezone.timedelta(days=7)
            highlights = Highlight.objects.filter(
                is_active=True,
                created_at__gte=week_ago
            ).prefetch_related('appreciations', 'views', 'comments')
            
            hashtag_analytics = {}
            
            for highlight in highlights:
                if not highlight.hashtags:
                    continue
                
                total_appreciations = highlight.appreciations.count()
                total_views = highlight.views.count()
                total_comments = highlight.comments.count()
                
                # Calculer le taux d'engagement
                engagement_rate = 0
                if total_views > 0:
                    engagement_rate = (total_appreciations + total_comments) / total_views * 100
                
                for hashtag in highlight.hashtags:
                    hashtag_lower = hashtag.lower()
                    if hashtag_lower not in hashtag_analytics:
                        hashtag_analytics[hashtag_lower] = {
                            'count': 0,
                            'total_views': 0,
                            'total_appreciations': 0,
                            'total_comments': 0,
                            'engagement_rates': []
                        }
                    
                    stats = hashtag_analytics[hashtag_lower]
                    stats['count'] += 1
                    stats['total_views'] += total_views
                    stats['total_appreciations'] += total_appreciations
                    stats['total_comments'] += total_comments
                    stats['engagement_rates'].append(engagement_rate)
            
            # Calculer les moyennes et trier
            hashtag_performance = []
            for hashtag, stats in hashtag_analytics.items():
                if stats['count'] >= 3:  # Au moins 3 highlights pour être significatif
                    avg_engagement = sum(stats['engagement_rates']) / len(stats['engagement_rates'])
                    avg_views = stats['total_views'] / stats['count']
                    
                    hashtag_performance.append({
                        'hashtag': hashtag,
                        'count': stats['count'],
                        'avg_engagement': avg_engagement,
                        'avg_views': avg_views,
                        'total_appreciations': stats['total_appreciations']
                    })
            
            # Trier par engagement moyen
            hashtag_performance.sort(key=lambda x: x['avg_engagement'], reverse=True)
            
            self.stdout.write('\nTop 10 hashtags par engagement:')
            for i, stats in enumerate(hashtag_performance[:10], 1):
                self.stdout.write(
                    f'{i}. #{stats["hashtag"]} - '
                    f'{stats["avg_engagement"]:.1f}% engagement, '
                    f'{stats["count"]} highlights, '
                    f'{stats["avg_views"]:.0f} vues moy.'
                )
            
            return hashtag_performance
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse d'engagement: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {e}')
            )
            return []

    def optimize_global_feeds(self):
        """Optimise les feeds globaux basés sur les tendances hashtags"""
        try:
            trending_hashtags = self.update_trending_hashtags()
            engagement_data = self.analyze_hashtag_engagement()
            
            # Créer une liste optimisée de hashtags recommandés
            recommended_hashtags = []
            
            # Ajouter les hashtags tendances
            recommended_hashtags.extend(trending_hashtags[:10])
            
            # Ajouter les hashtags avec le meilleur engagement
            if engagement_data:
                top_engagement = [item['hashtag'] for item in engagement_data[:5]]
                for hashtag in top_engagement:
                    if hashtag not in recommended_hashtags:
                        recommended_hashtags.append(hashtag)
            
            self.stdout.write(f'\nHashtags recommandés pour optimisation: {", ".join(recommended_hashtags[:15])}')
            
            return recommended_hashtags
            
        except Exception as e:
            logger.error(f"Erreur lors de l'optimisation globale: {e}")
            self.stdout.write(
                self.style.ERROR(f'Erreur: {e}')
            )
            return []
