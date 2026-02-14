
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator
from django.utils import timezone
import json
import uuid
from .encrypted_fields import EncryptedCharField, EncryptedEmailField
from cloudinary.models import CloudinaryField

# Modèles Highlights
class Highlight(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlights')
    video = models.FileField(upload_to='highlights_videos/')
    caption = models.TextField(max_length=500, blank=True)
    hashtags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    views_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=48)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def time_remaining(self):
        if self.is_expired:
            return None
        return self.expires_at - timezone.now()
    
    @property
    def appreciations_count(self):
        return self.appreciations.count()
    
    @property
    def comments_count(self):
        return self.comments.count()
    
    def get_appreciation_counts_by_level(self):
        """Retourne un dictionnaire avec le nombre d'appréciations par niveau"""
        counts = {}
        for level in range(1, 7):
            counts[level] = self.appreciations.filter(appreciation_level=level).count()
        return counts
    
    def __str__(self):
        return f"Highlight by {self.author.username} - {self.created_at}"

class HighlightAppreciation(models.Model):
    """Système d'appréciation avec 6 niveaux d'émotions"""
    APPRECIATION_CHOICES = [
        (1, 'Extrêmement nul'),
        (2, 'Pas terrible'),
        (3, 'Moyen'),
        (4, 'Bien'),
        (5, 'Très bien'),
        (6, 'Extraordinaire'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='appreciations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlight_appreciations')
    appreciation_level = models.IntegerField(choices=APPRECIATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['highlight', 'user']
    
    def __str__(self):
        return f"{self.user.username} - Niveau {self.appreciation_level} sur {self.highlight.id}"
    
    @property
    def score_impact(self):
        """Retourne l'impact sur le score de l'auteur"""
        score_impacts = {
            1: -10,  # Extrêmement nul
            2: -4,   # Pas terrible
            3: 2,    # Moyen
            4: 4,    # Bien
            5: 6,    # Très bien
            6: 10,   # Extraordinaire
        }
        return score_impacts.get(self.appreciation_level, 0)

class HighlightComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlight_comments')
    content = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.highlight.id}"

class HighlightView(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlight_views', null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    view_duration = models.FloatField(default=0.0, help_text="View duration in seconds")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['highlight', 'user']
    
    def __str__(self):
        return f"View on {self.highlight.id} by {self.user.username if self.user else 'Anonymous'} ({self.view_duration}s)"

class HighlightShare(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    highlight = models.ForeignKey(Highlight, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='highlight_shares')
    shared_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_highlight_shares', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} shared {self.highlight.id}"

class UserSubscription(models.Model):
    """Système d'abonnement pour les Highlights (remplace les demandes d'amis)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscribed_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['subscriber', 'subscribed_to']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(subscriber=models.F('subscribed_to')),
                name='no_self_subscription'
            )
        ]
    
    def __str__(self):
        return f"{self.subscriber.username} subscribed to {self.subscribed_to.username}"

# Modèles existants
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    profileimg = models.ImageField(upload_to='profile_images', default='default_profile.png', blank=True, null=True)
    profileimg_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de l'image de profil")
    location = models.CharField(max_length=100, blank=True)
    banner = models.ImageField(upload_to='banner_images', default='default_banner.png', blank=True, null=True)
    banner_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de la bannière")
    favorite_games = models.JSONField(default=list, blank=True, help_text="Liste des jeux favoris de l'utilisateur")
    
    # Champs pour le système de réputation
    score = models.IntegerField(default=0, help_text="Score basé sur les appréciations des Highlights")
    appreciation_count = models.IntegerField(default=0, help_text="Nombre total d'appréciations reçues")
    
    # Champ pour le délai de modification de pseudo
    last_username_change = models.DateTimeField(null=True, blank=True, help_text="Date du dernier changement de pseudo")
    
    # Champs pour les informations de payout
    payout_phone = models.CharField(max_length=20, blank=True, help_text="Numéro de téléphone pour les payouts")
    payout_country = models.CharField(max_length=2, blank=True, help_text="Code pays pour les payouts (ex: CI, SN, ML)")
    payout_operator = models.CharField(max_length=50, blank=True, help_text="Opérateur mobile pour les payouts")
    payout_verified = models.BooleanField(default=False, help_text="Informations de payout vérifiées")

    @property
    def friends_count(self):
        """Compte le nombre d'amis (abonnements mutuels)"""
        user_subscriptions = set(self.user.subscriptions.values_list('subscribed_to_id', flat=True))
        user_subscribers = set(self.user.subscribers.values_list('subscriber_id', flat=True))
        return len(user_subscriptions.intersection(user_subscribers))
    
    @property
    def subscribers_count(self):
        """Compte le nombre d'abonnés"""
        return self.user.subscribers.count()
    
    @property
    def subscriptions_count(self):
        """Compte le nombre d'abonnements"""
        return self.user.subscriptions.count()

    GAME_CHOICES = [
        ('FreeFire', 'FreeFire'),
        ('PUBG', 'PUBG Mobile'),
        ('COD', 'Call of Duty Mobile'),
        ('efootball', 'eFootball Mobile'),
        ('fc25', 'FC25 Mobile'),
        ('bloodstrike', 'Bloodstrike'),
        ('other', 'Autre'),
    ]

    def __str__(self):
        return self.user.username

    @property
    def can_change_username(self):
        """Vérifie si l'utilisateur peut changer son pseudo (délai de 2 mois)"""
        if not self.last_username_change:
            return True
        
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        now = timezone.now()
        two_months_ago = now - timedelta(days=60)  # 2 mois = 60 jours
        
        return self.last_username_change <= two_months_ago
    
    @property
    def next_username_change_date(self):
        """Retourne la date du prochain changement de pseudo possible"""
        if not self.last_username_change:
            return None
        
        from datetime import timedelta
        from django.utils import timezone
        
        return self.last_username_change + timedelta(days=60)

    @property
    def appreciation_percentage(self):
        """Calcule le pourcentage d'appréciations positives (niveaux 4-6)"""
        if self.appreciation_count == 0:
            return 0.0
        
        # Compter les appréciations positives (niveaux 4-6)
        positive_appreciations = HighlightAppreciation.objects.filter(
            highlight__author=self.user
        ).filter(appreciation_level__gte=4).count()
        
        return round((positive_appreciations / self.appreciation_count) * 100, 1)
    
    def update_score_from_appreciation(self, appreciation_level):
        """Met à jour le score basé sur une nouvelle appréciation"""
        score_impacts = {
            1: -10,  # Extrêmement nul
            2: -4,   # Pas terrible
            3: 2,    # Moyen
            4: 4,    # Bien
            5: 6,    # Très bien
            6: 10,   # Extraordinaire
        }
        
        impact = score_impacts.get(appreciation_level, 0)
        self.score += impact
        self.appreciation_count += 1
        self.save()

    @property
    def appreciation_level_counts(self):
        """Retourne un dict {1..6: count} des appréciations reçues par niveau pour tous les highlights de l'utilisateur."""
        counts = {level: 0 for level in range(1, 7)}
        qs = HighlightAppreciation.objects.filter(highlight__author=self.user)
        for level in range(1, 7):
            counts[level] = qs.filter(appreciation_level=level).count()
        return counts

    @property
    def appreciation_level_percentages(self):
        """Retourne un dict {1..6: percent} basé sur appreciation_count (0 si aucun)."""
        total = self.appreciation_count or 0
        counts = self.appreciation_level_counts
        if total == 0:
            return {level: 0.0 for level in range(1, 7)}
        return {level: round((counts[level] / total) * 100, 1) for level in counts}

class Post(models.Model):
    GAME_CHOICES = [
        ('FreeFire', 'FreeFire'),
        ('PUBG', 'PUBG Mobile'),
        ('COD', 'Call of Duty Mobile'),
        ('efootball', 'eFootball Mobile'),
        ('fc25', 'FC25 Mobile'),
        ('bloodstrike', 'Bloodstrike'),
        ('other', 'Autre'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200, default='sans nom')
    banner = models.ImageField(upload_to='post_banners', default='def_img.png')
    banner_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de la bannière du post")
    caption = models.TextField(max_length=200, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    no_of_likes = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MaxValueValidator(999999.99)])
    email = models.EmailField(default='sans email')
    password = models.CharField(max_length=254, default='sans password')
    is_sold = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=True)
    is_in_transaction = models.BooleanField(default=False)
    game_type = models.CharField(max_length=50, choices=GAME_CHOICES, default='other')
    custom_game_name = models.CharField(max_length=100, blank=True, null=True)
    coins = models.CharField(max_length=100, default='')
    level = models.CharField(max_length=50, default='')

    def get_game_display_name(self):
        if self.game_type == 'other' and self.custom_game_name:
            return self.custom_game_name
        else:
            return dict(self.GAME_CHOICES).get(self.game_type, 'Autre')

    @property
    def main_image(self):
        return self.banner

    @property
    def has_banner(self):
        return bool(self.banner and self.banner.name != 'def_img.png')

    @property
    def time_since_created(self):
        from django.utils.timesince import timesince
        return timesince(self.created_at)

    
    @property
    def is_fake_demo(self):
        """Indique si c'est une fausse annonce pour demo"""
        return hasattr(self, '_is_fake_demo') and self._is_fake_demo

    def __str__(self):
        return self.title

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images')
    image_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de l'image")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(fields=['post', 'order'], name='unique_image_order'),
            models.CheckConstraint(check=models.Q(order__lt=10), name='max_images_per_post'),
        ]

class PostVideo(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='post_videos')
    video_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de la vidéo")

# Modèles de transaction existants
class Transaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('disputed', 'Litigieuse'),
        ('refunded', 'Remboursée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    security_period_end = models.DateTimeField(null=True, blank=True)
    account_verified_before = models.BooleanField(default=False)
    account_verified_after = models.BooleanField(default=False)

    def __str__(self):
        return f"Transaction {self.id} - {self.buyer.username} -> {self.seller.username}"

# Modèles CinetPay existants
class CinetPayTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending_payment', 'Paiement en attente'),
        ('payment_received', 'Paiement reçu'),
        ('in_escrow', 'En séquestre'),
        ('escrow_released', 'Séquestre libéré'),
        ('escrow_refunded', 'Séquestre remboursé'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='cinetpay_transaction')
    customer_id = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    customer_surname = models.CharField(max_length=100)
    customer_phone_number = models.CharField(max_length=20)
    customer_email = models.EmailField()
    customer_address = models.CharField(max_length=200)
    customer_city = models.CharField(max_length=100)
    customer_country = models.CharField(max_length=2)
    customer_state = models.CharField(max_length=2)
    customer_zip_code = models.CharField(max_length=10)
    seller_phone_number = models.CharField(max_length=20)
    seller_country = models.CharField(max_length=2)
    seller_operator = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)
    seller_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_payment')
    cinetpay_transaction_id = models.CharField(max_length=100, unique=True)
    payment_url = models.URLField(null=True, blank=True)
    payment_token = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payment_received_at = models.DateTimeField(null=True, blank=True)
    escrow_released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"CinetPay {self.cinetpay_transaction_id} - {self.status}"

# Modèles Shopify corrigés
class ShopifyIntegration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    shop_name = models.CharField(max_length=100)
    shop_url = models.URLField()
    access_token = models.CharField(max_length=255)
    webhook_secret = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Shopify - {self.shop_name}"

class ProductCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Product Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('out_of_stock', 'Rupture de stock'),
        ('discontinued', 'Arrêté'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tags = models.JSONField(default=list, blank=True)
    featured_image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    featured_image_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de l'image principale")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_featured = models.BooleanField(default=False)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Champs Shopify
    shopify_product_id = models.CharField(max_length=100, null=True, blank=True)
    shopify_variant_id = models.CharField(max_length=100, null=True, blank=True)
    shopify_handle = models.CharField(max_length=200, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return self.name

    def get_main_image(self):
        if self.featured_image:
            return self.featured_image
        first_image = self.images.first()
        return first_image.image if first_image else None

class ProductImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    image_url = models.URLField(blank=True, null=True, help_text="URL Cloudinary de l'image")
    alt_text = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

class ProductVariant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=100)  # Ex: "Couleur", "Taille"
    value = models.CharField(max_length=100)  # Ex: "Rouge", "L"
    price_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shopify_variant_id = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['product', 'name', 'value']

    def __str__(self):
        return f"{self.product.name} - {self.name}: {self.value}"

    def get_final_price(self):
        return self.product.price + self.price_adjustment

# Modèles de panier et commande
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items.all())

    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def is_empty(self):
        return not self.items.exists()

    def __str__(self):
        return f"Cart {self.id} - {self.user.username if self.user else 'Anonymous'}"

class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']

    def get_current_price(self):
        """Retourne le prix actuel du produit (pas le prix stocké)"""
        return self.variant.get_final_price() if self.variant else self.product.price
    
    def get_total_price(self):
        # Utiliser le prix actuel du produit au lieu du prix stocké
        # pour éviter les problèmes de devise obsolète
        return self.get_current_price() * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours de traitement'),
        ('shipped', 'Expédiée'),
        ('delivered', 'Livrée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('paid', 'Payée'),
        ('failed', 'Échouée'),
        ('refunded', 'Remboursée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_orders', null=True, blank=True)
    order_number = models.CharField(max_length=20, unique=True)
    
    # Informations client
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=20)
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    
    # Adresse de livraison
    shipping_address_line1 = models.CharField(max_length=200)
    shipping_address_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=2)
    
    # Montants
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Statuts
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Intégration Shopify
    shopify_order_id = models.CharField(max_length=100, null=True, blank=True)
    shopify_order_number = models.CharField(max_length=50, null=True, blank=True)
    shopify_fulfillment_status = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.order_number}"

    def generate_order_number(self):
        """Génère un numéro de commande unique"""
        import random
        import string
        while True:
            number = 'BLZ' + ''.join(random.choices(string.digits, k=8))
            if not Order.objects.filter(order_number=number).exists():
                return number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shopify_line_item_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.product_name}"

# Transaction CinetPay pour la boutique (dropshipping)
class ShopCinetPayTransaction(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
        ('cancelled', 'Annulée'),
        ('refunded', 'Remboursée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='cinetpay_transaction')
    
    # ID de transaction CinetPay
    cinetpay_transaction_id = models.CharField(max_length=100, unique=True)
    payment_url = models.URLField(null=True, blank=True)
    payment_token = models.CharField(max_length=255, null=True, blank=True)
    
    # Informations client pour CinetPay
    customer_name = models.CharField(max_length=100)
    customer_surname = models.CharField(max_length=100)
    customer_phone_number = models.CharField(max_length=20)
    customer_email = models.EmailField()
    customer_country = models.CharField(max_length=2)
    
    # Montants
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    
    # Statut et timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Shop CinetPay {self.cinetpay_transaction_id} - {self.order.order_number}"

# Modèles de réputation et autres (existants)
class UserReputation(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userreputation')
    
    # Métriques vendeur
    seller_total_transactions = models.IntegerField(default=0)
    seller_successful_transactions = models.IntegerField(default=0)
    seller_failed_transactions = models.IntegerField(default=0)
    seller_fraudulent_transactions = models.IntegerField(default=0)
    seller_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    seller_badge = models.CharField(max_length=50, default='novice')
    
    # Métriques acheteur
    buyer_total_transactions = models.IntegerField(default=0)
    buyer_successful_transactions = models.IntegerField(default=0)
    buyer_failed_transactions = models.IntegerField(default=0)
    buyer_disputed_transactions = models.IntegerField(default=0)
    buyer_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    buyer_badge = models.CharField(max_length=50, default='novice')
    
    # Timestamps
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_seller_badge(self):
        from .badge_config import get_seller_badge
        return get_seller_badge(float(self.seller_score), self.seller_total_transactions)
    
    @property
    def seller_badge_data(self):
        """Propriété pour les templates Django"""
        return self.get_seller_badge()

    def update_reputation(self):
        from .badge_config import get_seller_badge
        
        # Calcul du score vendeur avec facteur de confiance basé sur le volume
        if self.seller_total_transactions > 0:
            # Score de base: taux de réussite (0-100%)
            base_score = (self.seller_successful_transactions / self.seller_total_transactions) * 100
            
            # Facteur de confiance: augmente progressivement avec le volume
            # Atteint 100% à partir de 10 transactions
            confidence_factor = min(self.seller_total_transactions / 10, 1.0)
            
            # Score final ajusté par le volume
            self.seller_score = base_score * confidence_factor
            
            # Déterminer le badge selon le score ET le nombre de transactions
            final_badge = get_seller_badge(self.seller_score, self.seller_total_transactions)
            self.seller_badge = final_badge['level'] if final_badge else 'bronze_1'
        else:
            # Aucune transaction: Bronze I par défaut
            self.seller_score = 0.0
            self.seller_badge = 'bronze_1'
        
        self.save()

    def __str__(self):
        return f"Reputation for {self.user.username}"

class UserRating(models.Model):
    RATING_TYPE_CHOICES = [
        ('seller', 'Vendeur'),
        ('buyer', 'Acheteur'),
    ]

    OUTCOME_CHOICES = [
        ('success', 'Réussi'),
        ('failed', 'Échoué'),
        ('disputed', 'Litigieux'),
        ('fraudulent', 'Frauduleux'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='ratings')
    rating_type = models.CharField(max_length=10, choices=RATING_TYPE_CHOICES)
    outcome = models.CharField(max_length=15, choices=OUTCOME_CHOICES)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'transaction', 'rating_type']

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"

# Modèle pour la gestion des devises utilisateur
class UserCurrency(models.Model):
    CURRENCY_CHOICES = [
        # Afrique de l'Ouest et Centrale (PRIORITÉ)
        ('XOF', 'Franc CFA Ouest (FCFA)'),
        ('XAF', 'Franc CFA Central (FCFA)'),
        ('NGN', 'Naira Nigérian (₦)'),
        ('GHS', 'Cedi Ghanéen (₵)'),
        ('GNF', 'Franc Guinéen (GNF)'),
        
        # Maghreb
        ('MAD', 'Dirham Marocain (د.م.)'),
        ('DZD', 'Dinar Algérien (د.ج)'),
        ('TND', 'Dinar Tunisien (د.ت)'),
        ('EGP', 'Livre Égyptienne (ج.م)'),
        
        # Afrique de l'Est et Australe
        ('KES', 'Shilling Kenyan (KSh)'),
        ('TZS', 'Shilling Tanzanien (TSh)'),
        ('UGX', 'Shilling Ougandais (USh)'),
        ('ZAR', 'Rand Sud-Africain (R)'),
        ('MUR', 'Roupie Mauricienne (₨)'),
        
        # Devises principales internationales
        ('EUR', 'Euro (€)'),
        ('USD', 'Dollar Américain ($)'),
        ('GBP', 'Livre Sterling (£)'),
        
        # Asie
        ('JPY', 'Yen Japonais (¥)'),
        ('CNY', 'Yuan Chinois (¥)'),
        ('INR', 'Roupie Indienne (₹)'),
        ('KRW', 'Won Sud-Coréen (₩)'),
        ('THB', 'Baht Thaïlandais (฿)'),
        ('VND', 'Dong Vietnamien (₫)'),
        ('IDR', 'Roupie Indonésienne (Rp)'),
        ('PHP', 'Peso Philippin (₱)'),
        ('MYR', 'Ringgit Malaisien (RM)'),
        ('SGD', 'Dollar Singapourien (S$)'),
        
        # Amérique latine
        ('BRL', 'Real Brésilien (R$)'),
        ('MXN', 'Peso Mexicain ($)'),
        ('ARS', 'Peso Argentin ($)'),
        ('CLP', 'Peso Chilien ($)'),
        ('COP', 'Peso Colombien ($)'),
        ('PEN', 'Sol Péruvien (S/)'),
        ('UYU', 'Peso Uruguayen ($)'),
        ('VES', 'Bolívar Vénézuélien (Bs)'),
        
        # Amérique du Nord
        ('CAD', 'Dollar Canadien (CAD)'),
        ('AUD', 'Dollar Australien (A$)'),
        ('NZD', 'Dollar Néo-Zélandais (NZ$)'),
        
        # Europe
        ('CHF', 'Franc Suisse (CHF)'),
        ('SEK', 'Couronne Suédoise (kr)'),
        ('NOK', 'Couronne Norvégienne (kr)'),
        ('DKK', 'Couronne Danoise (kr)'),
        ('PLN', 'Zloty Polonais (zł)'),
        ('CZK', 'Couronne Tchèque (Kč)'),
        ('HUF', 'Forint Hongrois (Ft)'),
        ('RON', 'Leu Roumain (lei)'),
        ('BGN', 'Lev Bulgare (лв)'),
        ('HRK', 'Kuna Croate (kn)'),
        ('RSD', 'Dinar Serbe (дин)'),
        ('UAH', 'Hryvnia Ukrainienne (₴)'),
        ('RUB', 'Rouble Russe (₽)'),
        ('TRY', 'Livre Turque (₺)'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='currency_preference')
    preferred_currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='EUR')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.preferred_currency}"

# Modèle pour le cache des taux de change
class ExchangeRate(models.Model):
    base_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['base_currency', 'target_currency']
        indexes = [
            models.Index(fields=['base_currency', 'target_currency']),
            models.Index(fields=['last_updated']),
        ]
    
    def __str__(self):
        return f"{self.base_currency} → {self.target_currency}: {self.rate}"
    
    @property
    def is_fresh(self):
        """Vérifie si le taux est récent (moins de 1 heure)"""
        from datetime import timedelta
        return timezone.now() - self.last_updated < timedelta(hours=1)

# Modèles de chat et notifications (existants)
class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='chat', null=True, blank=True)
    dispute = models.OneToOneField('Dispute', on_delete=models.CASCADE, related_name='chat', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(transaction__isnull=False, dispute__isnull=True) |
                    models.Q(transaction__isnull=True, dispute__isnull=False)
                ),
                name='chat_has_transaction_or_dispute'
            )
        ]

    def __str__(self):
        if self.transaction:
            return f"Chat for transaction {self.transaction.id}"
        elif self.dispute:
            return f"Chat for dispute {self.dispute.id}"
        return f"Chat {self.id}"

    def has_access(self, user):
        """Vérifie si l'utilisateur a accès à ce chat"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[HAS_ACCESS DEBUG] Chat ID: {self.id}, User: {user.username} (ID: {user.id})")
        logger.info(f"[HAS_ACCESS DEBUG] Transaction: {self.transaction.id if self.transaction else None}")
        logger.info(f"[HAS_ACCESS DEBUG] Dispute: {self.dispute.id if self.dispute else None}")
        
        if self.transaction:
            buyer_match = user == self.transaction.buyer
            seller_match = user == self.transaction.seller
            logger.info(f"[HAS_ACCESS DEBUG] Buyer: {self.transaction.buyer.username} (ID: {self.transaction.buyer.id})")
            logger.info(f"[HAS_ACCESS DEBUG] Seller: {self.transaction.seller.username} (ID: {self.transaction.seller.id})")
            logger.info(f"[HAS_ACCESS DEBUG] Buyer match: {buyer_match}, Seller match: {seller_match}")
            result = buyer_match or seller_match
            logger.info(f"[HAS_ACCESS DEBUG] Result: {result}")
            return result
        elif self.dispute:
            result = (user == self.dispute.transaction.buyer or 
                   user == self.dispute.transaction.seller or 
                   user.is_staff)
            logger.info(f"[HAS_ACCESS DEBUG] Dispute access result: {result}")
            return result
        
        logger.info(f"[HAS_ACCESS DEBUG] No transaction or dispute - returning False")
        return False

    def get_other_users(self, user):
        """Retourne les autres utilisateurs du chat"""
        if self.transaction:
            if user == self.transaction.buyer:
                return [self.transaction.seller]
            elif user == self.transaction.seller:
                return [self.transaction.buyer]
        elif self.dispute:
            users = [self.dispute.transaction.buyer, self.dispute.transaction.seller]
            if self.dispute.assigned_admin:
                users.append(self.dispute.assigned_admin)
            return [u for u in users if u != user]
        return []

    def get_other_user(self, user):
        """Retourne l'autre utilisateur principal du chat (pour les chats de transaction)"""
        if self.transaction:
            if user == self.transaction.buyer:
                return self.transaction.seller
            elif user == self.transaction.seller:
                return self.transaction.buyer
        return None

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Message texte'),
        ('image', 'Image'),
        ('file', 'Fichier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message {self.id.hex[:8]}"
    
    def mark_as_read(self, user):
        """Marquer le message comme lu par un utilisateur spécifique"""
        if self.sender != user and not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class PendingEmailNotification(models.Model):
    """
    Suivi des vendeurs qui n'ont pas répondu et doivent être notifiés manuellement
    """
    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE, related_name='pending_notifications')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pending_seller_notifications')
    last_buyer_message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notification_trigger')
    created_at = models.DateTimeField(auto_now_add=True)
    notified_manually = models.BooleanField(default=False)
    notified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['transaction', 'last_buyer_message']
    
    def __str__(self):
        return f"Notification pour {self.seller.username} - Transaction {self.transaction.id}"

class Notification(models.Model):
    TYPE_CHOICES = [
        ('purchase_intent', "Intention d'achat"),
        ('new_message', 'Nouveau message'),
        ('transaction_update', 'Mise à jour de transaction'),
        ('system', 'Notification système'),
        ('private_message', 'Message privé'),
        ('group_message', 'Message de groupe'),
        ('group_invite', 'Invitation de groupe'),
        ('friend_request', "Demande d'ami"),
        ('friend_accept', 'Amitié acceptée'),
        ('dispute_created', 'Litige créé'),
        ('dispute_resolved', 'Litige résolu'),
        ('dispute_message', 'Message de litige'),
        ('new_report', 'Nouveau signalement'),
        ('marketing', 'Notification marketing'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    # Champs pour le groupement des messages
    message_count = models.PositiveIntegerField(default=1, help_text="Nombre de messages groupés")
    sender_username = models.CharField(max_length=150, blank=True, help_text="Nom d'utilisateur de l'expéditeur des messages groupés")
    
    # Relations optionnelles
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    dispute = models.ForeignKey('Dispute', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    report = models.ForeignKey('Report', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)

    class Meta:
        ordering = ['is_read', '-created_at']  # Non lues en premier, puis par date décroissante

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

# Modèles pour les informations de paiement vendeur
class SellerPaymentInfo(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Virement Bancaire'),
        ('card', 'Carte Bancaire'),
    ]

    OPERATOR_CHOICES = [
        ('orange_money', 'Orange Money'),
        ('mtn_momo', 'MTN Mobile Money'),
        ('moov_money', 'Moov Money'),
        ('wave', 'Wave'),
        ('free_money', 'Free Money'),
        ('emoney', 'E-Money'),
        ('airtel_money', 'Airtel Money'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='payment_info')
    
    # Méthode de paiement préférée
    preferred_payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='mobile_money')
    
    # Informations Mobile Money
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES, null=True, blank=True)
    country = models.CharField(max_length=2, default='SN')
    
    # Informations bancaires
    bank_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=50, null=True, blank=True)
    account_holder_name = models.CharField(max_length=100, null=True, blank=True)
    swift_code = models.CharField(max_length=20, null=True, blank=True)
    iban = models.CharField(max_length=50, null=True, blank=True)
    
    # Informations carte
    card_number = models.CharField(max_length=20, null=True, blank=True)
    card_holder_name = models.CharField(max_length=100, null=True, blank=True)
    
    # Vérification
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_attempts = models.IntegerField(default=0)
    last_verification_attempt = models.DateTimeField(null=True, blank=True)
    verification_failed_reason = models.TextField(null=True, blank=True)
    
    # Champs encryptés pour la sécurité (Phase 2)
    encrypted_phone_number = EncryptedCharField(max_length=20, null=True, blank=True)
    encrypted_account_number = EncryptedCharField(max_length=50, null=True, blank=True)
    encrypted_card_number = EncryptedCharField(max_length=20, null=True, blank=True)
    encrypted_account_holder_name = EncryptedCharField(max_length=100, null=True, blank=True)
    encrypted_card_holder_name = EncryptedCharField(max_length=100, null=True, blank=True)
    encrypted_bank_name = EncryptedCharField(max_length=100, null=True, blank=True)
    encrypted_swift_code = EncryptedCharField(max_length=20, null=True, blank=True)
    encrypted_iban = EncryptedCharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment info for {self.user.username}"

# Modèles pour les groupes et messages privés
class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    avatar = models.ImageField(upload_to='group_avatars/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    max_members = models.IntegerField(default=100)

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return self.name
    
    @property
    def members(self):
        """Retourne les utilisateurs membres actifs du groupe"""
        return User.objects.filter(
            group_memberships__group=self,
            group_memberships__is_active=True
        )

class GroupMembership(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_members')

    class Meta:
        unique_together = ['user', 'group']
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"

class GroupMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_messages')
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Group message from {self.sender.username} in {self.group.name}"

class GroupMessageRead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='read_group_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['message', 'user']

class PrivateConversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='private_chats_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['user1', 'user2']
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation between {self.user1.username} and {self.user2.username}"

class PrivateMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    conversation = models.ForeignKey(PrivateConversation, on_delete=models.CASCADE, related_name='private_messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_private_messages')
    content = models.TextField()
    image = models.ImageField(upload_to='chat_images/', null=True, blank=True)
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    def mark_as_read(self, user):
        """Marquer le message comme lu par un utilisateur spécifique"""
        if self.sender != user and not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Private message from {self.sender.username}"

# Modèles d'amitié
class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('accepted', 'Acceptée'),
        ('declined', 'Refusée'),
        ('cancelled', 'Annulée'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Friend request from {self.from_user.username} to {self.to_user.username}"

class Friendship(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friendships_as_user2')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user1', 'user2']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user1=models.F('user2')),
                name='no_self_friendship'
            )
        ]

    def __str__(self):
        return f"Friendship between {self.user1.username} and {self.user2.username}"

# Modèles d'escrow et payout (existants)
class EscrowTransaction(models.Model):
    STATUS_CHOICES = [
        ('in_escrow', 'En séquestre'),
        ('released', 'Libéré'),
        ('refunded', 'Remboursé'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cinetpay_transaction = models.OneToOneField(CinetPayTransaction, on_delete=models.CASCADE, related_name='escrow')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_escrow')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Escrow {self.id} - {self.status}"

class PayoutRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
    ]
    
    PAYOUT_TYPE_CHOICES = [
        ('seller_payout', 'Paiement Vendeur'),
        ('buyer_refund', 'Remboursement Acheteur'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    escrow_transaction = models.ForeignKey(EscrowTransaction, on_delete=models.CASCADE, related_name='payout_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text='Montant à payer (90% pour vendeur, 100% pour remboursement)')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text='Montant original de la transaction')
    currency = models.CharField(max_length=3, default='XOF')
    payout_type = models.CharField(max_length=20, choices=PAYOUT_TYPE_CHOICES, default='seller_payout', help_text='Type de payout')
    recipient_phone = models.CharField(max_length=20)
    recipient_country = models.CharField(max_length=2)
    recipient_operator = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    cinetpay_payout_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payout {self.id} - {self.status}"


class Dispute(models.Model):
    """
    Modèle pour gérer les litiges entre acheteurs et vendeurs
    """
    REASON_CHOICES = [
        ('invalid_account', 'Compte gaming invalide'),
        ('wrong_data', 'Données incorrectes'),
        ('no_response', 'Vendeur ne répond pas'),
        ('account_recovered', 'Compte récupéré par le propriétaire original'),
        ('fake_screenshots', 'Captures d\'écran falsifiées'),
        ('other', 'Autre motif'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente d\'examen'),
        ('investigating', 'Enquête en cours'),
        ('awaiting_evidence', 'En attente de preuves'),
        ('resolved_buyer', 'Résolu en faveur de l\'acheteur'),
        ('resolved_seller', 'Résolu en faveur du vendeur'),
        ('closed', 'Fermé sans suite'),
    ]
    
    RESOLUTION_CHOICES = [
        ('refund', 'Remboursement acheteur'),
        ('payout', 'Paiement vendeur'),
        ('partial_refund', 'Remboursement partiel'),
        ('no_action', 'Aucune action'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Faible'),
        ('medium', 'Moyenne'),
        ('high', 'Élevée'),
        ('urgent', 'Urgente'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    transaction = models.OneToOneField(Transaction, on_delete=models.CASCADE, related_name='dispute')
    
    # Informations du litige
    opened_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='opened_disputes')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    description = models.TextField(help_text="Description détaillée du problème")
    
    # Preuves et documents
    evidence = models.JSONField(default=dict, help_text="Preuves uploadées (screenshots, logs, etc.)")
    chat_logs = models.TextField(blank=True, help_text="Logs de chat sauvegardés automatiquement")
    
    # Gestion administrative
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assigned_admin = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='assigned_disputes',
        limit_choices_to={'is_staff': True}
    )
    
    # Notes et résolution
    admin_notes = models.TextField(blank=True, help_text="Notes internes pour les administrateurs")
    resolution = models.CharField(max_length=20, choices=RESOLUTION_CHOICES, blank=True)
    resolution_details = models.TextField(blank=True, help_text="Détails de la résolution")
    
    # Montants financiers
    disputed_amount = models.DecimalField(max_digits=10, decimal_places=2)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Délais et timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True, help_text="Délai limite pour résolution (72h par défaut)")
    
    # Métriques
    response_time_hours = models.IntegerField(null=True, blank=True, help_text="Temps de première réponse en heures")
    resolution_time_hours = models.IntegerField(null=True, blank=True, help_text="Temps total de résolution en heures")
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_admin', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Litige #{self.id.hex[:8]} - {self.get_status_display()}"
    
    def save(self, *args, **kwargs):
        # Définir le délai par défaut (72h)
        if not self.deadline:
            from django.utils import timezone
            self.deadline = timezone.now() + timezone.timedelta(hours=72)
        
        # Calculer le temps de résolution si résolu
        if self.status in ['resolved_buyer', 'resolved_seller', 'closed'] and not self.resolved_at:
            from django.utils import timezone
            self.resolved_at = timezone.now()
            if self.created_at:
                time_diff = self.resolved_at - self.created_at
                self.resolution_time_hours = int(time_diff.total_seconds() / 3600)
        
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Vérifie si le litige dépasse le délai limite"""
        from django.utils import timezone
        return timezone.now() > self.deadline and self.status not in ['resolved_buyer', 'resolved_seller', 'closed']
    
    @property
    def time_remaining(self):
        """Temps restant avant le délai limite"""
        from django.utils import timezone
        if self.is_overdue:
            return None
        return self.deadline - timezone.now()
    
    def get_involved_users(self):
        """Retourne tous les utilisateurs impliqués dans le litige"""
        return [self.transaction.buyer, self.transaction.seller, self.assigned_admin]
    
    def add_evidence(self, evidence_type, evidence_data, uploaded_by):
        """Ajoute une preuve au litige"""
        if not self.evidence:
            self.evidence = {}
        
        evidence_entry = {
            'type': evidence_type,
            'data': evidence_data,
            'uploaded_by': uploaded_by.id,
            'uploaded_at': timezone.now().isoformat(),
        }
        
        if evidence_type not in self.evidence:
            self.evidence[evidence_type] = []
        
        self.evidence[evidence_type].append(evidence_entry)
        self.save()


class DisputeMessage(models.Model):
    """
    Messages échangés dans le cadre d'un litige
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Message visible seulement par les admins")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message de {self.sender.username} - {self.created_at}"

class DisputeInformationRequest(models.Model):
    REQUEST_TYPES = [
        ('text_response', 'Réponse textuelle'),
        ('screenshot', 'Capture d\'écran'),
        ('document', 'Document/Preuve'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('responded', 'Répondu'),
        ('expired', 'Expiré'),
    ]
    
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, related_name='information_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    requested_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    question = models.TextField(help_text="Question ou demande d'information")
    response_text = models.TextField(blank=True, help_text="Réponse textuelle de l'utilisateur")
    response_file = CloudinaryField('dispute_response', blank=True, null=True, help_text="Fichier uploadé en réponse")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    deadline = models.DateTimeField(help_text="Délai de réponse (24h par défaut)")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Demande à {self.requested_to.username} - {self.get_request_type_display()}"
    
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.deadline

# Modèles de signalement
class Report(models.Model):
    """
    Modèle pour gérer les signalements de contenu
    """
    REPORT_TYPES = [
        ('highlight', 'Highlight'),
        ('gaming_post', 'Vente Gaming'),
        ('chat_message', 'Message Chat'),
        ('user_profile', 'Profil Utilisateur'),
    ]
    
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('inappropriate', 'Contenu inapproprié'),
        ('harassment', 'Harcèlement'),
        ('fake', 'Faux contenu/Arnaque'),
        ('violence', 'Violence'),
        ('hate_speech', 'Discours de haine'),
        ('copyright', 'Violation de droits d\'auteur'),
        ('other', 'Autre'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('under_review', 'En cours d\'examen'),
        ('resolved', 'Résolu'),
        ('dismissed', 'Rejeté'),
    ]
    
    ACTION_CHOICES = [
        ('none', 'Aucune action'),
        ('warning', 'Avertissement'),
        ('content_removal', 'Suppression du contenu'),
        ('temporary_ban', 'Bannissement temporaire'),
        ('permanent_ban', 'Bannissement permanent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(help_text="Description détaillée du signalement")
    
    # Références vers le contenu signalé
    highlight = models.ForeignKey('Highlight', on_delete=models.CASCADE, null=True, blank=True)
    gaming_post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    chat_message = models.ForeignKey('Message', on_delete=models.CASCADE, null=True, blank=True)
    
    # Gestion administrative
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_reports')
    admin_notes = models.TextField(blank=True, help_text="Notes internes de l'admin")
    action_taken = models.CharField(max_length=20, choices=ACTION_CHOICES, default='none')
    
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = [
            ['reporter', 'highlight'],
            ['reporter', 'gaming_post'],
            ['reporter', 'chat_message'],
        ]
    
    def __str__(self):
        return f"Signalement de {self.reporter.username} - {self.get_reason_display()}"

# Modèle pour la vérification email
class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    verification_code = models.CharField(max_length=6, unique=True, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    last_email_sent = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Vérification Email"
        verbose_name_plural = "Vérifications Email"

    def __str__(self):
        return f"Vérification email pour {self.user.username}"

    def generate_verification_code(self):
        """Génère un code de vérification à 6 chiffres"""
        import random
        code = str(random.randint(100000, 999999))
        self.verification_code = code
        self.save()
        return code

    @property
    def is_expired(self):
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(hours=24)
        return timezone.now() > expiry_time

    @property
    def can_resend_email(self):
        """Vérifie si l'utilisateur peut renvoyer un email (délai de 5 minutes)"""
        if not self.last_email_sent:
            return True
        from datetime import timedelta
        cooldown_time = self.last_email_sent + timedelta(minutes=5)
        return timezone.now() > cooldown_time

    @property
    def time_until_next_resend(self):
        """Retourne le temps restant avant de pouvoir renvoyer un email"""
        if not self.last_email_sent:
            return None
        from datetime import timedelta
        cooldown_time = self.last_email_sent + timedelta(minutes=5)
        remaining = cooldown_time - timezone.now()
        return remaining if remaining.total_seconds() > 0 else None

    def send_verification_email(self):
        try:
            from django.conf import settings
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.utils.html import strip_tags
            
            # Générer le code de vérification
            verification_code = self.generate_verification_code()
            
            subject = '🎮 Code de vérification - BLIZZ Gaming'
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Code de vérification - BLIZZ Gaming</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #6c5ce7, #a29bfe); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ padding: 20px; background: #f9f9f9; border-radius: 0 0 10px 10px; }}
                    .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                    .verification-code {{ 
                        background: linear-gradient(135deg, #6c5ce7, #a29bfe); 
                        color: white; 
                        padding: 20px; 
                        border-radius: 10px; 
                        font-family: 'Courier New', monospace; 
                        font-size: 32px; 
                        text-align: center; 
                        margin: 20px 0; 
                        font-weight: bold;
                        letter-spacing: 5px;
                        box-shadow: 0 4px 15px rgba(108, 92, 231, 0.3);
                    }}
                    .instructions {{ 
                        background: #fff; 
                        padding: 15px; 
                        border-radius: 8px; 
                        border-left: 4px solid #6c5ce7; 
                        margin: 15px 0; 
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 BLIZZ Gaming</h1>
                        <p>Code de vérification de votre compte</p>
                    </div>
                    <div class="content">
                        <h2>Bonjour {self.user.username} !</h2>
                        <p>Merci de vous être inscrit sur <strong>BLIZZ Gaming</strong> ! Pour activer votre compte, utilisez le code de vérification ci-dessous :</p>
                        
                        <div class="verification-code">
                            {verification_code}
                        </div>
                        
                        <div class="instructions">
                            <h3>📋 Instructions :</h3>
                            <ol>
                                <li>Retournez sur la page de votre profil</li>
                                <li>Entrez le code <strong>{verification_code}</strong> dans le champ de vérification</li>
                                <li>Cliquez sur "Vérifier"</li>
                            </ol>
                        </div>
                        
                        <p><strong>⏰ Ce code expire dans 24 heures.</strong></p>
                        <p>Si vous n'avez pas créé de compte sur BLIZZ Gaming, ignorez cet email.</p>
                        <p>Bonne partie ! 🎮</p>
                    </div>
                    <div class="footer">
                        <p>BLIZZ Gaming - Votre marketplace gaming de confiance</p>
                        <p>Si vous ne voyez pas cet email, vérifiez vos spams.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            plain_message = f"""
            Bonjour {self.user.username} !
            Merci de vous être inscrit sur BLIZZ Gaming !
            
            Votre code de vérification est : {verification_code}
            
            Instructions :
            1. Retournez sur la page de votre profil
            2. Entrez le code {verification_code} dans le champ de vérification
            3. Cliquez sur "Vérifier"
            
            Ce code expire dans 24 heures.
            Si vous n'avez pas créé de compte, ignorez cet email.
            
            L'équipe BLIZZ Gaming
            """
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Mettre à jour la date du dernier envoi
            from django.utils import timezone
            self.last_email_sent = timezone.now()
            self.save()
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'envoi de l'email de vérification: {e}")
            if 'console' in str(e) or 'BadCredentials' in str(e):
                print("Mode développement : Email simulé dans la console")
                return True
            return False


class PasswordReset(models.Model):
    """Modèle pour la réinitialisation de mot de passe"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_resets')
    token = models.UUIDField(default=uuid.uuid4, unique=True)
    reset_code = models.CharField(max_length=6, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token valide pendant 1 heure
            self.expires_at = timezone.now() + timezone.timedelta(hours=1)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    @property
    def time_remaining(self):
        if self.is_expired:
            return None
        return self.expires_at - timezone.now()
    
    def mark_as_used(self):
        """Marque le token comme utilisé"""
        self.is_used = True
        self.save()
    
    def generate_reset_code(self):
        """Génère un code de réinitialisation à 6 chiffres"""
        import random
        while True:
            code = str(random.randint(100000, 999999))
            if not PasswordReset.objects.filter(reset_code=code, is_used=False).exists():
                self.reset_code = code
                self.save()
                return code
    
    def send_reset_email(self, request=None):
        """Envoie l'email de réinitialisation"""
        try:
            print("[DEBUG] Début de send_reset_email")
            from django.core.mail import send_mail
            from django.conf import settings
            
            print(f"[DEBUG] Settings EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Non défini')}")
            print(f"[DEBUG] Settings EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Non défini')}")
            print(f"[DEBUG] Settings BASE_URL: {getattr(settings, 'BASE_URL', 'Non défini')}")
            
            # Générer le code de réinitialisation
            reset_code = self.generate_reset_code()
            print(f"[DEBUG] Code de réinitialisation généré: {reset_code}")
            
            # Contenu de l'email
            subject = "🔒 Code de réinitialisation de votre mot de passe BLIZZ"
            print(f"[DEBUG] Sujet de l'email: {subject}")
            print(f"[DEBUG] Destinataire: {self.user.email}")
            
            plain_message = f"""
Bonjour {self.user.first_name or self.user.username},

Vous avez demandé la réinitialisation de votre mot de passe sur BLIZZ.

Votre code de réinitialisation est : {reset_code}

Ce code est valide pendant 1 heure.

Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.

L'équipe BLIZZ
            """.strip()
            
            html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Réinitialisation de mot de passe</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0f1729 0%, #1e293b 100%);
            margin: 0;
            padding: 20px;
            color: #ffffff;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background: rgba(15, 23, 41, 0.95);
            border-radius: 15px;
            padding: 30px;
            border: 1px solid #6c5ce7;
            box-shadow: 0 0 30px rgba(108, 92, 231, 0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-family: 'RussoOne', sans-serif;
            font-size: 2.5rem;
            color: #6c5ce7;
            text-shadow: 0 0 15px #6c5ce7;
            margin-bottom: 10px;
        }}
        .title {{
            color: #6c5ce7;
            font-size: 1.5rem;
            margin-bottom: 20px;
        }}
        .content {{
            line-height: 1.6;
            margin-bottom: 30px;
        }}
        .reset-button {{
            display: inline-block;
            background: linear-gradient(45deg, #6c5ce7, #a29bfe);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 8px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
            transition: all 0.3s ease;
        }}
        .reset-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(108, 92, 231, 0.3);
        }}
        .warning {{
            background: rgba(255, 193, 7, 0.1);
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            color: #ffc107;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(108, 92, 231, 0.3);
            color: rgba(255, 255, 255, 0.6);
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">BLIZZ</div>
            <div class="title">🔒 Code de réinitialisation</div>
        </div>
        
        <div class="content">
            <p>Bonjour <strong>{self.user.first_name or self.user.username}</strong>,</p>
            
            <p>Vous avez demandé la réinitialisation de votre mot de passe sur BLIZZ.</p>
            
            <p>Votre code de réinitialisation est :</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <div style="background: linear-gradient(45deg, #6c5ce7, #a29bfe); 
                           color: white; 
                           font-size: 2.5rem; 
                           font-weight: bold; 
                           padding: 20px 40px; 
                           border-radius: 10px; 
                           display: inline-block;
                           letter-spacing: 5px;
                           text-shadow: 0 2px 4px rgba(0,0,0,0.3);">
                    {reset_code}
                </div>
            </div>
            
            <div class="warning">
                <strong>⚠️ Important :</strong>
                <ul>
                    <li>Ce code est valide pendant <strong>1 heure</strong></li>
                    <li>Il ne peut être utilisé qu'<strong>une seule fois</strong></li>
                    <li>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email</li>
                </ul>
            </div>
            
            <p>Retournez sur la page de réinitialisation et entrez ce code pour continuer.</p>
        </div>
        
        <div class="footer">
            <p>L'équipe BLIZZ</p>
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
            """.strip()
            
            # Envoyer l'email
            print("[DEBUG] Tentative d'envoi via send_mail...")
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[self.user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            print("[DEBUG] Email envoyé avec succès!")
            return True
        except Exception as e:
            print(f"[DEBUG] Erreur lors de l'envoi de l'email de réinitialisation: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
            if 'console' in str(e) or 'BadCredentials' in str(e):
                print("[DEBUG] Mode développement : Email simulé dans la console")
                return True
            return False


# Modèles pour la gestion des sanctions (avertissements et bannissements)
class UserWarning(models.Model):
    """
    Modèle pour gérer les avertissements des utilisateurs
    """
    WARNING_TYPES = [
        ('content_violation', 'Violation de contenu'),
        ('behavior_violation', 'Violation de comportement'),
        ('dispute_lost', 'Litige perdu'),
        ('inappropriate_behavior', 'Comportement inapproprié'),
        ('fake_account', 'Compte falsifié'),
        ('spam', 'Spam'),
        ('other', 'Autre'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warnings_given', limit_choices_to={'is_staff': True})
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, null=True, blank=True, related_name='warnings')
    related_report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    
    warning_type = models.CharField(max_length=30, choices=WARNING_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='medium')
    reason = models.TextField(help_text="Raison de l'avertissement")
    details = models.TextField(blank=True, help_text="Détails supplémentaires")
    
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Date d'expiration de l'avertissement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['admin', 'created_at']),
        ]
    
    def __str__(self):
        return f"Avertissement {self.id.hex[:8]} - {self.user.username} ({self.get_severity_display()})"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at


class UserBan(models.Model):
    """
    Modèle pour gérer les bannissements des utilisateurs
    """
    BAN_TYPES = [
        ('temporary', 'Temporaire'),
        ('permanent', 'Permanent'),
    ]
    
    BAN_REASONS = [
        ('multiple_disputes', 'Multiples litiges perdus'),
        ('fraud', 'Fraude'),
        ('inappropriate_behavior', 'Comportement inapproprié'),
        ('fake_accounts', 'Comptes falsifiés'),
        ('spam', 'Spam'),
        ('other', 'Autre'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans')
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans_given', limit_choices_to={'is_staff': True})
    dispute = models.ForeignKey(Dispute, on_delete=models.CASCADE, null=True, blank=True, related_name='bans')
    related_report = models.ForeignKey(Report, on_delete=models.SET_NULL, null=True, blank=True)
    
    ban_type = models.CharField(max_length=20, choices=BAN_TYPES)
    reason = models.CharField(max_length=30, choices=BAN_REASONS, default='other')
    details = models.TextField(help_text="Détails du bannissement", blank=True)
    
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(auto_now_add=True)
    ends_at = models.DateTimeField(null=True, blank=True, help_text="Date de fin du bannissement (pour les bannissements temporaires)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['admin', 'created_at']),
        ]
    
    def __str__(self):
        return f"Bannissement {self.id.hex[:8]} - {self.user.username} ({self.get_ban_type_display()})"
    
    @property
    def is_expired(self):
        if not self.ends_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.ends_at
    
    @property
    def is_permanent(self):
        return self.ban_type == 'permanent'


class MarketingNotification(models.Model):
    """
    Modèle pour gérer les notifications marketing quotidiennes de la boutique dropshipping
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marketing_notifications')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='marketing_notifications')
    shown_date = models.DateField(default=timezone.now)
    is_dismissed = models.BooleanField(default=False)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'shown_date']  # Un utilisateur ne peut avoir qu'une notification par jour
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'shown_date']),
            models.Index(fields=['is_dismissed', 'shown_date']),
        ]
    
    def __str__(self):
        return f"Marketing notification - {self.user.username} - {self.product.name} - {self.shown_date}"
    
    def dismiss(self):
        """Marque la notification comme fermée"""
        self.is_dismissed = True
        self.dismissed_at = timezone.now()
        self.save()