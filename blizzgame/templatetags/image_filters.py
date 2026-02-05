from django import template
from django.templatetags.static import static
from django.conf import settings
import os

register = template.Library()

DEFAULT_MEDIA_PLACEHOLDERS = {
    'default_profile.png',
    'default_banner.png',
    'def_img.png',
}


@register.filter
def safe_media_or_static(image_field, fallback_static_path):
    """Return media URL if valid and not a placeholder default; else return static fallback.

    Usage in templates:
        {{ user_profile.profileimg|safe_media_or_static:'images/default_profile.png' }}
    """
    try:
        if image_field and getattr(image_field, 'name', None):
            image_name = image_field.name.split('/')[-1]
            if image_name and image_name not in DEFAULT_MEDIA_PLACEHOLDERS:
                # For Cloudinary, get the full URL which includes the Cloudinary domain
                url = image_field.url
                
                # If URL doesn't start with http, try to construct Cloudinary URL manually
                if not url.startswith('http') and hasattr(settings, 'CLOUDINARY_URL') and settings.CLOUDINARY_URL:
                    # Parse CLOUDINARY_URL to get cloud name
                    try:
                        import re
                        cloudinary_url = os.environ.get('CLOUDINARY_URL', '')
                        if cloudinary_url:
                            # Extract cloud name from cloudinary://api_key:api_secret@cloud_name
                            match = re.search(r'@([^/]+)', cloudinary_url)
                            if match:
                                cloud_name = match.group(1)
                                # Construct full Cloudinary URL
                                cloudinary_full_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/{image_field.name}"
                                return cloudinary_full_url
                    except Exception:
                        pass
                
                return url
    except Exception:
        pass
    return static(fallback_static_path)


@register.filter
def cloudinary_or_static(profile, field_type):
    """
    Nouveau filter qui prioritise les URLs Cloudinary directes
    
    Usage:
        {{ user_profile|cloudinary_or_static:'profileimg' }}
        {{ user_profile|cloudinary_or_static:'banner' }}
    """
    try:
        if field_type == 'profileimg':
            # Priorité 1: URL Cloudinary directe (seulement si le champ existe)
            if hasattr(profile, 'profileimg_url') and getattr(profile, 'profileimg_url', None):
                return profile.profileimg_url
            # Priorité 2: ImageField avec fallback
            return safe_media_or_static(profile.profileimg, 'images/default.png')
            
        elif field_type == 'banner':
            # Priorité 1: URL Cloudinary directe (seulement si le champ existe)
            if hasattr(profile, 'banner_url') and getattr(profile, 'banner_url', None):
                return profile.banner_url
            # Priorité 2: ImageField avec fallback
            return safe_media_or_static(profile.banner, 'images/default.png')
            
    except Exception:
        # En cas d'erreur (champ n'existe pas encore), utiliser l'ancien système
        if field_type == 'profileimg':
            return safe_media_or_static(profile.profileimg, 'images/default.png')
        elif field_type == 'banner':
            return safe_media_or_static(profile.banner, 'images/default.png')
    
    # Fallback final
    return static('images/default.png')


@register.filter
def post_media_or_static(post_or_image, field_type):
    """
    Filter pour les médias des posts (banner, images, vidéos)
    
    Usage:
        {{ post|post_media_or_static:'banner' }}
        {{ post_image|post_media_or_static:'image' }}
        {{ post_video|post_media_or_static:'video' }}
    """
    try:
        if field_type == 'banner':
            # Priorité 1: URL Cloudinary directe
            if hasattr(post_or_image, 'banner_url') and getattr(post_or_image, 'banner_url', None):
                return post_or_image.banner_url
            # Priorité 2: ImageField avec fallback
            return safe_media_or_static(post_or_image.banner, 'images/def_img.png')
            
        elif field_type == 'image':
            # Pour PostImage
            if hasattr(post_or_image, 'image_url') and getattr(post_or_image, 'image_url', None):
                return post_or_image.image_url
            return safe_media_or_static(post_or_image.image, 'images/def_img.png')
            
        elif field_type == 'video':
            # Pour PostVideo
            if hasattr(post_or_image, 'video_url') and getattr(post_or_image, 'video_url', None):
                return post_or_image.video_url
            return post_or_image.video.url if post_or_image.video else ''
            
    except Exception:
        # En cas d'erreur, utiliser l'ancien système
        if field_type == 'banner':
            return safe_media_or_static(post_or_image.banner, 'images/def_img.png')
        elif field_type == 'image':
            return safe_media_or_static(post_or_image.image, 'images/def_img.png')
        elif field_type == 'video':
            return post_or_image.video.url if post_or_image.video else ''
    
    # Fallback final
    return static('images/def_img.png')


@register.filter
def shopify_media_or_static(product_or_image, field_type):
    """
    Filter pour les médias des produits Shopify
    
    Usage:
        {{ product|shopify_media_or_static:'featured' }}
        {{ product_image|shopify_media_or_static:'image' }}
    """
    try:
        if field_type == 'featured':
            # Pour Product.featured_image
            if hasattr(product_or_image, 'featured_image_url') and getattr(product_or_image, 'featured_image_url', None):
                return product_or_image.featured_image_url
            return safe_media_or_static(product_or_image.featured_image, 'images/def_img.png')
            
        elif field_type == 'image':
            # Pour ProductImage
            if hasattr(product_or_image, 'image_url') and getattr(product_or_image, 'image_url', None):
                return product_or_image.image_url
            return safe_media_or_static(product_or_image.image, 'images/def_img.png')
            
    except Exception:
        # En cas d'erreur, utiliser l'ancien système
        if field_type == 'featured':
            return safe_media_or_static(product_or_image.featured_image, 'images/def_img.png')
        elif field_type == 'image':
            return safe_media_or_static(product_or_image.image, 'images/def_img.png')
    
    # Fallback final
    return static('images/def_img.png')


