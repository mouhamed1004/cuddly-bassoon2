from django.contrib import admin

from blizzgame.models import (
    Post, PostImage, PostVideo, Profile, Product, ProductCategory, 
    ProductImage, ProductVariant, Order, OrderItem, Cart, CartItem,
    ShopCinetPayTransaction, ShopifyIntegration, UserReputation,
    Highlight, HighlightAppreciation, HighlightComment, HighlightView, HighlightShare, UserSubscription,
    Transaction, CinetPayTransaction, Dispute, DisputeMessage, Report, UserWarning, UserBan, Notification,
    PayoutRequest, EscrowTransaction, SellerPaymentInfo
)

# Modèles existants
admin.site.register(Profile)
admin.site.register(Post)
admin.site.register(PostImage)
admin.site.register(PostVideo)
admin.site.register(UserReputation)

# === ADMINISTRATION HIGHLIGHTS ===

@admin.register(Highlight)
class HighlightAdmin(admin.ModelAdmin):
    list_display = ['author', 'caption_preview', 'hashtags_display', 'appreciations_count', 'comments_count', 'views_count', 'created_at', 'expires_at', 'is_active']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['author__username', 'caption', 'hashtags']
    readonly_fields = ['created_at', 'expires_at', 'views_count']
    list_editable = ['is_active']
    
    def caption_preview(self, obj):
        return obj.caption[:50] + '...' if len(obj.caption) > 50 else obj.caption
    caption_preview.short_description = 'Caption'
    
    def hashtags_display(self, obj):
        return ', '.join([f'#{tag}' for tag in obj.hashtags]) if obj.hashtags else 'Aucun'
    hashtags_display.short_description = 'Hashtags'
    
    def appreciations_count(self, obj):
        return obj.appreciations.count()
    appreciations_count.short_description = 'Appréciations'
    
    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = 'Commentaires'
    
    def views_count(self, obj):
        return obj.views.count()
    views_count.short_description = 'Vues'

@admin.register(HighlightAppreciation)
class HighlightAppreciationAdmin(admin.ModelAdmin):
    list_display = ['user', 'highlight_preview', 'appreciation_level', 'created_at']
    list_filter = ['appreciation_level', 'created_at']
    search_fields = ['user__username', 'highlight__caption']
    
    def highlight_preview(self, obj):
        return f"{obj.highlight.author.username} - {obj.highlight.caption[:30]}..."
    highlight_preview.short_description = 'Highlight'

@admin.register(HighlightComment)
class HighlightCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'highlight_preview', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content', 'highlight__caption']
    
    def highlight_preview(self, obj):
        return f"{obj.highlight.author.username} - {obj.highlight.caption[:20]}..."
    highlight_preview.short_description = 'Highlight'
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Commentaire'

@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['subscriber', 'subscribed_to', 'created_at']
    list_filter = ['created_at']
    search_fields = ['subscriber__username', 'subscribed_to__username']

# === ADMINISTRATION BOUTIQUE E-COMMERCE ===

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order']

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ['name', 'value', 'price_adjustment', 'shopify_variant_id', 'is_active']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'status', 'is_featured', 'shopify_product_id', 'created_at']
    list_filter = ['status', 'is_featured', 'category', 'created_at']
    search_fields = ['name', 'description', 'shopify_product_id']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['status', 'is_featured', 'price']
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'slug', 'category', 'description', 'short_description')
        }),
        ('Prix et statut', {
            'fields': ('price', 'compare_price', 'cost_price', 'status', 'is_featured')
        }),
        ('Médias', {
            'fields': ('featured_image',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'tags'),
            'classes': ('collapse',)
        }),
        ('Shopify', {
            'fields': ('shopify_product_id', 'shopify_variant_id', 'shopify_handle'),
            'classes': ('collapse',)
        }),
    )

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_price', 'quantity', 'total_price']
    can_delete = False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_email', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'shipping_country', 'created_at']
    search_fields = ['order_number', 'customer_email', 'customer_first_name', 'customer_last_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations de commande', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Client', {
            'fields': ('customer_first_name', 'customer_last_name', 'customer_email', 'customer_phone')
        }),
        ('Adresse de livraison', {
            'fields': ('shipping_address_line1', 'shipping_address_line2', 'shipping_city', 
                      'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Montants', {
            'fields': ('subtotal', 'shipping_cost', 'tax_amount', 'total_amount')
        }),
        ('Shopify', {
            'fields': ('shopify_order_id', 'shopify_order_number', 'shopify_fulfillment_status'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ShopCinetPayTransaction)
class ShopCinetPayTransactionAdmin(admin.ModelAdmin):
    list_display = ['cinetpay_transaction_id', 'order', 'customer_email', 'amount', 'status', 'created_at']
    list_filter = ['status', 'currency', 'customer_country', 'created_at']
    search_fields = ['cinetpay_transaction_id', 'customer_email', 'order__order_number']
    readonly_fields = ['cinetpay_transaction_id', 'payment_url', 'payment_token', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction', {
            'fields': ('cinetpay_transaction_id', 'order', 'status', 'amount', 'currency')
        }),
        ('Client', {
            'fields': ('customer_name', 'customer_surname', 'customer_email', 
                      'customer_phone_number', 'customer_country')
        }),
        ('CinetPay', {
            'fields': ('payment_url', 'payment_token'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ShopifyIntegration)
class ShopifyIntegrationAdmin(admin.ModelAdmin):
    list_display = ['shop_name', 'shop_url', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['shop_name', 'shop_url']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Configuration Shopify', {
            'fields': ('shop_name', 'shop_url', 'access_token', 'is_active')
        }),
        ('Webhooks', {
            'fields': ('webhook_secret',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# === ADMINISTRATION GAMING MARKETPLACE ===

class DisputeMessageInline(admin.TabularInline):
    model = DisputeMessage
    extra = 0
    fields = ['sender', 'message', 'is_internal', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'buyer', 'seller', 'post_title', 'amount', 'status', 'has_dispute', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['buyer__username', 'seller__username', 'post__title', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def post_title(self, obj):
        return obj.post.title[:50]
    post_title.short_description = 'Produit'
    
    def has_dispute(self, obj):
        return hasattr(obj, 'dispute')
    has_dispute.boolean = True
    has_dispute.short_description = 'Litige'

@admin.register(CinetPayTransaction)
class CinetPayTransactionAdmin(admin.ModelAdmin):
    list_display = ['cinetpay_transaction_id', 'transaction_buyer', 'amount', 'status', 'created_at']
    list_filter = ['status', 'currency', 'customer_country', 'created_at']
    search_fields = ['cinetpay_transaction_id', 'customer_email', 'transaction__id']
    readonly_fields = ['cinetpay_transaction_id', 'payment_url', 'payment_token', 'created_at']
    
    def transaction_buyer(self, obj):
        return obj.transaction.buyer.username
    transaction_buyer.short_description = 'Acheteur'

@admin.register(Dispute)
class DisputeAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'transaction_info', 'opened_by', 'reason', 'status', 'priority', 'assigned_admin', 'is_overdue_display', 'created_at']
    list_filter = ['status', 'priority', 'reason', 'assigned_admin', 'created_at']
    search_fields = ['transaction__buyer__username', 'transaction__seller__username', 'transaction__post__title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'resolved_at', 'response_time_hours', 'resolution_time_hours']
    list_editable = ['status', 'priority', 'assigned_admin']
    inlines = [DisputeMessageInline]
    
    actions = ['assign_to_me', 'mark_as_investigating', 'mark_as_resolved_buyer', 'mark_as_resolved_seller']
    
    fieldsets = (
        ('Informations du litige', {
            'fields': ('id', 'transaction', 'opened_by', 'reason', 'description')
        }),
        ('Gestion administrative', {
            'fields': ('status', 'priority', 'assigned_admin', 'admin_notes')
        }),
        ('Preuves et résolution', {
            'fields': ('evidence', 'chat_logs', 'resolution', 'resolution_details')
        }),
        ('Montants financiers', {
            'fields': ('disputed_amount', 'refund_amount')
        }),
        ('Délais et métriques', {
            'fields': ('deadline', 'response_time_hours', 'resolution_time_hours', 'created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def transaction_info(self, obj):
        return f"{obj.transaction.buyer.username} → {obj.transaction.seller.username} ({obj.transaction.post.title[:30]})"
    transaction_info.short_description = 'Transaction'
    
    def is_overdue_display(self, obj):
        return obj.is_overdue
    is_overdue_display.boolean = True
    is_overdue_display.short_description = 'En retard'
    
    def assign_to_me(self, request, queryset):
        updated = queryset.update(assigned_admin=request.user)
        self.message_user(request, f'{updated} litige(s) assigné(s) à vous.')
    assign_to_me.short_description = "M'assigner ces litiges"
    
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating')
        self.message_user(request, f'{updated} litige(s) marqué(s) en enquête.')
    mark_as_investigating.short_description = "Marquer en enquête"
    
    def mark_as_resolved_buyer(self, request, queryset):
        updated = queryset.update(status='resolved_buyer', resolution='refund')
        self.message_user(request, f'{updated} litige(s) résolu(s) en faveur de l\'acheteur.')
    mark_as_resolved_buyer.short_description = "Résoudre en faveur de l'acheteur"
    
    def mark_as_resolved_seller(self, request, queryset):
        updated = queryset.update(status='resolved_seller', resolution='payout')
        self.message_user(request, f'{updated} litige(s) résolu(s) en faveur du vendeur.')
    mark_as_resolved_seller.short_description = "Résoudre en faveur du vendeur"

@admin.register(DisputeMessage)
class DisputeMessageAdmin(admin.ModelAdmin):
    list_display = ['dispute_short', 'sender', 'message_preview', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['dispute__id', 'sender__username', 'message']
    readonly_fields = ['created_at']
    
    def dispute_short(self, obj):
        return f"#{str(obj.dispute.id)[:8]}"
    dispute_short.short_description = 'Litige'
    
    def message_preview(self, obj):
        return obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
    message_preview.short_description = 'Message'


# === ADMINISTRATION SIGNALEMENTS ET MODÉRATION ===

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'reporter', 'reported_user', 'report_type', 'reason', 'status', 'admin_reviewer', 'created_at']
    list_filter = ['report_type', 'reason', 'status', 'created_at']
    search_fields = ['reporter__username', 'reported_user__username', 'description']
    readonly_fields = ['id', 'created_at']
    list_editable = ['status', 'admin_reviewer']
    
    actions = ['mark_as_investigating', 'mark_as_resolved', 'dismiss_reports']
    
    fieldsets = (
        ('Informations du signalement', {
            'fields': ('id', 'reporter', 'reported_user', 'report_type', 'reason', 'description')
        }),
        ('Contenu signalé', {
            'fields': ('highlight', 'gaming_post', 'chat_message')
        }),
        ('Gestion administrative', {
            'fields': ('status', 'admin_reviewer', 'admin_notes', 'action_taken')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def mark_as_investigating(self, request, queryset):
        updated = queryset.update(status='investigating', admin_reviewer=request.user)
        self.message_user(request, f'{updated} signalement(s) marqué(s) en enquête.')
    mark_as_investigating.short_description = "Marquer en enquête"
    
    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(status='resolved', admin_reviewer=request.user)
        self.message_user(request, f'{updated} signalement(s) résolu(s).')
    mark_as_resolved.short_description = "Marquer comme résolu"
    
    def dismiss_reports(self, request, queryset):
        updated = queryset.update(status='dismissed', admin_reviewer=request.user)
        self.message_user(request, f'{updated} signalement(s) rejeté(s).')
    dismiss_reports.short_description = "Rejeter les signalements"

@admin.register(UserWarning)
class UserWarningAdmin(admin.ModelAdmin):
    list_display = ['user', 'warning_type', 'admin', 'is_active', 'created_at']
    list_filter = ['warning_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['created_at']
    list_editable = ['is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'admin')

@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = ['user', 'ban_type', 'admin', 'is_active', 'starts_at', 'ends_at']
    list_filter = ['ban_type', 'is_active', 'starts_at']
    search_fields = ['user__username', 'reason']
    readonly_fields = ['starts_at']
    list_editable = ['is_active']
    
    actions = ['activate_bans', 'deactivate_bans']
    
    def activate_bans(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} bannissement(s) activé(s).')
    activate_bans.short_description = "Activer les bannissements"
    
    def deactivate_bans(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} bannissement(s) désactivé(s).')
    deactivate_bans.short_description = "Désactiver les bannissements"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'content']
    readonly_fields = ['created_at']
    list_editable = ['is_read']
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme lue(s).')
    mark_as_read.short_description = "Marquer comme lu"
    
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marquée(s) comme non lue(s).')
    mark_as_unread.short_description = "Marquer comme non lu"

# === ADMINISTRATION PAYOUTS ===

@admin.register(SellerPaymentInfo)
class SellerPaymentInfoAdmin(admin.ModelAdmin):
    list_display = ['user', 'preferred_payment_method', 'phone_number', 'operator', 'country', 'is_verified', 'created_at']
    list_filter = ['preferred_payment_method', 'operator', 'country', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'bank_name', 'account_holder_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'verified_at']
    list_editable = ['is_verified']
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user', 'is_verified', 'verified_at')
        }),
        ('Méthode de paiement', {
            'fields': ('preferred_payment_method', 'country')
        }),
        ('Mobile Money', {
            'fields': ('phone_number', 'operator'),
            'classes': ('collapse',)
        }),
        ('Informations bancaires', {
            'fields': ('bank_name', 'account_number', 'account_holder_name', 'swift_code', 'iban'),
            'classes': ('collapse',)
        }),
        ('Carte bancaire', {
            'fields': ('card_number', 'card_holder_name'),
            'classes': ('collapse',)
        }),
        ('Vérification', {
            'fields': ('verification_attempts', 'last_verification_attempt', 'verification_failed_reason'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'payout_type_display', 'seller_info', 'amount_display', 'recipient_info', 'status', 'created_at', 'completed_at']
    list_filter = ['payout_type', 'status', 'currency', 'recipient_operator', 'created_at', 'completed_at']
    search_fields = ['recipient_phone', 'cinetpay_payout_id', 'escrow_transaction__cinetpay_transaction__transaction__seller__username']
    readonly_fields = ['id', 'created_at', 'completed_at']
    list_editable = ['status']
    actions = ['mark_as_processing', 'mark_as_completed', 'mark_as_failed', 'export_to_csv']
    
    fieldsets = (
        ('Informations du payout', {
            'fields': ('id', 'payout_type', 'escrow_transaction', 'amount', 'currency', 'status')
        }),
        ('Informations du bénéficiaire', {
            'fields': ('recipient_phone', 'recipient_country', 'recipient_operator')
        }),
        ('Suivi CinetPay', {
            'fields': ('cinetpay_payout_id', 'created_at', 'completed_at')
        }),
    )
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def payout_type_display(self, obj):
        if obj.payout_type == 'seller_payout':
            return '💰 Paiement Vendeur'
        elif obj.payout_type == 'buyer_refund':
            return '🔄 Remboursement Acheteur'
        return obj.get_payout_type_display()
    payout_type_display.short_description = 'Type'
    
    def seller_info(self, obj):
        try:
            seller = obj.escrow_transaction.cinetpay_transaction.transaction.seller
            return f"{seller.username} ({seller.email})"
        except:
            return "N/A"
    seller_info.short_description = 'Vendeur'
    
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Montant'
    
    def recipient_info(self, obj):
        return f"{obj.recipient_phone} ({obj.recipient_country}) - {obj.recipient_operator}"
    recipient_info.short_description = 'Bénéficiaire'
    
    def mark_as_processing(self, request, queryset):
        updated = queryset.update(status='processing')
        self.message_user(request, f'{updated} payout(s) marqué(s) en cours de traitement.')
    mark_as_processing.short_description = "Marquer en cours de traitement"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} payout(s) marqué(s) comme terminé(s).')
    mark_as_completed.short_description = "Marquer comme terminé"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payout(s) marqué(s) comme échoué(s).')
    mark_as_failed.short_description = "Marquer comme échoué"
    
    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from django.utils import timezone
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="payouts_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Vendeur', 'Email Vendeur', 'Montant (EUR)', 'Montant (XOF)', 
            'Téléphone', 'Pays', 'Opérateur', 'Statut', 'Date Création', 'Date Paiement'
        ])
        
        for payout in queryset:
            try:
                seller = payout.escrow_transaction.cinetpay_transaction.transaction.seller
                seller_email = seller.email
                seller_username = seller.username
            except:
                seller_email = "N/A"
                seller_username = "N/A"
            
            # Convertir EUR en XOF (approximatif)
            amount_xof = float(payout.amount) * 655.957 if payout.currency == 'EUR' else float(payout.amount)
            
            writer.writerow([
                str(payout.id)[:8],
                seller_username,
                seller_email,
                f"{payout.amount}",
                f"{amount_xof:.0f}",
                payout.recipient_phone,
                payout.recipient_country,
                payout.recipient_operator,
                payout.get_status_display(),
                payout.created_at.strftime('%d/%m/%Y %H:%M'),
                payout.completed_at.strftime('%d/%m/%Y %H:%M') if payout.completed_at else ''
            ])
        
        return response
    export_to_csv.short_description = "Exporter en CSV"

@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    list_display = ['id_short', 'transaction_info', 'amount', 'currency', 'status', 'created_at']
    list_filter = ['status', 'currency', 'created_at']
    search_fields = ['cinetpay_transaction__transaction__seller__username', 'cinetpay_transaction__transaction__buyer__username']
    readonly_fields = ['id', 'created_at', 'released_at']
    
    def id_short(self, obj):
        return str(obj.id)[:8]
    id_short.short_description = 'ID'
    
    def transaction_info(self, obj):
        try:
            transaction = obj.cinetpay_transaction.transaction
            return f"{transaction.buyer.username} → {transaction.seller.username} ({transaction.post.title[:30]})"
        except:
            return "N/A"
    transaction_info.short_description = 'Transaction'

# Personnalisation de l'interface admin
admin.site.site_header = "Administration BLIZZ"
admin.site.site_title = "BLIZZ Admin"
admin.site.index_title = "Tableau de bord BLIZZ"