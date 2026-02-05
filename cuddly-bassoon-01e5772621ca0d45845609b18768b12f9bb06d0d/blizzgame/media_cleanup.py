"""
Utilitaires pour la suppression des médias des annonces vendues
"""
import os
import logging
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def delete_post_media(post):
    """
    Supprime tous les médias (images et vidéos) d'une annonce vendue
    pour économiser l'espace de stockage
    """
    try:
        deleted_files = []
        
        # Supprimer la bannière si ce n'est pas l'image par défaut
        if post.banner and post.banner.name != 'def_img.png':
            try:
                if default_storage.exists(post.banner.name):
                    default_storage.delete(post.banner.name)
                    deleted_files.append(f"Banner: {post.banner.name}")
                    logger.info(f"Bannière supprimée: {post.banner.name}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de la bannière {post.banner.name}: {e}")
        
        # Supprimer toutes les images supplémentaires
        for image in post.images.all():
            try:
                if default_storage.exists(image.image.name):
                    default_storage.delete(image.image.name)
                    deleted_files.append(f"Image: {image.image.name}")
                    logger.info(f"Image supprimée: {image.image.name}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de l'image {image.image.name}: {e}")
        
        # Supprimer toutes les vidéos
        for video in post.videos.all():
            try:
                if default_storage.exists(video.video.name):
                    default_storage.delete(video.video.name)
                    deleted_files.append(f"Video: {video.video.name}")
                    logger.info(f"Vidéo supprimée: {video.video.name}")
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de la vidéo {video.video.name}: {e}")
        
        # Supprimer les enregistrements de la base de données
        post.images.all().delete()
        post.videos.all().delete()
        
        # Réinitialiser la bannière à l'image par défaut
        post.banner = 'def_img.png'
        post.save()
        
        logger.info(f"Suppression des médias terminée pour l'annonce {post.id}. Fichiers supprimés: {len(deleted_files)}")
        return {
            'success': True,
            'deleted_files': deleted_files,
            'count': len(deleted_files)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des médias pour l'annonce {post.id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'deleted_files': []
        }


def cleanup_sold_posts_media():
    """
    Fonction de maintenance pour nettoyer les médias de toutes les annonces vendues
    qui n'ont pas encore été nettoyées
    """
    try:
        from .models import Post
        
        sold_posts = Post.objects.filter(is_sold=True)
        cleaned_count = 0
        
        for post in sold_posts:
            # Vérifier si l'annonce a encore des médias (pas encore nettoyée)
            has_media = (
                (post.banner and post.banner.name != 'def_img.png') or
                post.images.exists() or
                post.videos.exists()
            )
            
            if has_media:
                result = delete_post_media(post)
                if result['success']:
                    cleaned_count += 1
                    logger.info(f"Annonce {post.id} nettoyée: {result['count']} fichiers supprimés")
        
        logger.info(f"Nettoyage terminé: {cleaned_count} annonces nettoyées")
        return {
            'success': True,
            'cleaned_posts': cleaned_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage des médias des annonces vendues: {e}")
        return {
            'success': False,
            'error': str(e),
            'cleaned_posts': 0
        }
