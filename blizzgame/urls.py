from django.urls import path
from . import views
from . import webhook_handlers
from . import admin_views

urlpatterns = [
    # URLs existantes pour les comptes gaming
    path('', views.index, name='index'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('create/', views.create, name='create'),
    path('product/<uuid:post_id>/', views.product_detail, name='product_detail'),
    path('delete/<uuid:post_id>/', views.delete_post, name='delete_post'),
    path('logout/', views.logout_view, name='logout'),
    
    # Authentification
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    
    # Transactions gaming
    path('initiate-transaction/<uuid:post_id>/', views.initiate_transaction, name='initiate_transaction'),
    path('transaction/<uuid:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/', views.transaction_list, name='transactions'),
    path('confirm-reception/<uuid:transaction_id>/', views.confirm_reception, name='confirm_reception'),
    path('complete-transaction/<uuid:transaction_id>/', views.complete_transaction, name='complete_transaction'),
    path('dispute-transaction/<uuid:transaction_id>/', views.dispute_transaction, name='dispute_transaction'),
    
    # Chat pour transactions (fonctionnel pour les transactions gaming)
    path('transaction/<uuid:transaction_id>/send-message/', views.send_transaction_message, name='send_transaction_message'),
    path('transaction/<uuid:transaction_id>/messages/', views.get_transaction_messages, name='get_transaction_messages'),
    
    # Chat avec Django Channels
    path('chat/transaction/<uuid:transaction_id>/', views.transaction_chat, name='transaction_chat'),
    path('chat/dispute/<uuid:dispute_id>/', views.dispute_chat, name='dispute_chat'),
    path('chat/list/', views.chat_list, name='chat_list'),
    path('chat/<uuid:chat_id>/send/', views.send_message, name='send_message'),
    path('chat/<uuid:chat_id>/upload-image/', views.upload_chat_image, name='upload_chat_image'),
    path('chat/<uuid:chat_id>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    
    # CinetPay pour les comptes gaming
    path('payment/cinetpay/<uuid:transaction_id>/', views.initiate_cinetpay_payment, name='initiate_cinetpay_payment'),
    path('payment/cinetpay/page/<uuid:transaction_id>/', views.cinetpay_payment_page, name='cinetpay_payment_page'),
    path('cinetpay/notification/', views.cinetpay_notification, name='old_cinetpay_notification'),
    path('gaming/cinetpay/notification/', views.gaming_cinetpay_notification, name='gaming_cinetpay_notification'),
    
    # Page d'accès admin
    path('admin-access/', views.admin_access_page, name='admin_access_page'),
    
    # Interface admin personnalisée pour les litiges
    path('dispute-admin/dashboard/', views.admin_dispute_dashboard, name='admin_dispute_dashboard'),
    path('dispute-admin/<uuid:dispute_id>/', views.admin_dispute_detail, name='admin_dispute_detail'),
    path('dispute-admin/<uuid:dispute_id>/assign/', views.admin_assign_dispute, name='admin_assign_dispute'),
    path('dispute-admin/<uuid:dispute_id>/notes/', views.admin_update_dispute_notes, name='admin_update_dispute_notes'),
    path('dispute-admin/<uuid:dispute_id>/request-info/', views.admin_send_information_request, name='admin_send_information_request'),
    path('information-request/<int:request_id>/respond/', views.respond_to_information_request, name='respond_to_information_request'),
    path('dispute-admin/<uuid:dispute_id>/resolve/refund/', views.admin_dispute_resolve_refund, name='admin_dispute_resolve_refund'),
    path('dispute-admin/<uuid:dispute_id>/resolve/payout/', views.admin_dispute_resolve_payout, name='admin_dispute_resolve_payout'),
    
    # Admin dispute followup (sanctions)
    path('dispute-admin/<uuid:dispute_id>/followup/', views.admin_dispute_followup, name='admin_dispute_followup'),
    path('dispute-admin/<uuid:dispute_id>/warn/', views.admin_warn_user, name='admin_warn_user'),
    path('dispute-admin/<uuid:dispute_id>/ban/', views.admin_ban_user, name='admin_ban_user'),
    path('payment/cinetpay/success/<uuid:transaction_id>/', views.cinetpay_payment_success, name='cinetpay_payment_success'),
    path('payment/cinetpay/failed/<uuid:transaction_id>/', views.cinetpay_payment_failed, name='cinetpay_payment_failed'),
    
    # Diagnostic
    path('debug/transaction/<uuid:transaction_id>/', views.debug_transaction_status, name='debug_transaction_status'),
    
    # Informations de paiement vendeur
    path('seller/payment-setup/', views.seller_payment_setup, name='seller_payment_setup'),
    path('seller/payment-reset/', views.reset_payment_info, name='reset_payment_info'),
    
    # Chat et notifications - TEMPORAIREMENT DÉSACTIVÉS POUR LE LANCEMENT
    path('chat/', views.redirect_to_index, name='chat_home'),
    path('chat/list/', views.redirect_to_index, name='chat_list'),
    path('chats/active/', views.redirect_to_index, name='get_active_chats'),
    path('submit-report/', views.redirect_to_index, name='submit_report'),
    
    # Admin routes pour signalements (intégrés dans dispute-admin) - TEMPORAIREMENT DÉSACTIVÉS
    path('dispute-admin/reports/', views.redirect_to_index, name='admin_reports_dashboard'),
    path('dispute-admin/reports/<uuid:report_id>/details/', views.redirect_to_index, name='admin_report_details'),
    path('dispute-admin/reports/warning/', views.redirect_to_index, name='admin_send_warning'),
    path('dispute-admin/reports/ban/', views.redirect_to_index, name='admin_ban_user'),
    path('dispute-admin/reports/dismiss/', views.redirect_to_index, name='admin_dismiss_report'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/mark-read/<uuid:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/unread/count/', views.unread_notifications_count, name='unread_notifications_count'),
    
    # Chat privé et groupes - TEMPORAIREMENT DÉSACTIVÉS
    path('chat/search/', views.redirect_to_index, name='user_search'),
    path('chat/private/<int:user_id>/', views.redirect_to_index, name='private_chat'),
    path('chat/private/<uuid:conversation_id>/send/', views.redirect_to_index, name='send_private_message'),
    path('chat/private/<uuid:conversation_id>/messages/', views.redirect_to_index, name='get_private_messages'),
    
    # Groupes - TEMPORAIREMENT DÉSACTIVÉS
    path('chat/groups/', views.redirect_to_index, name='group_list'),
    path('chat/group/create/', views.redirect_to_index, name='create_group'),
    path('chat/group/<uuid:group_id>/', views.redirect_to_index, name='group_chat'),
    path('chat/group/<uuid:group_id>/send/', views.redirect_to_index, name='send_group_message'),
    path('chat/group/<uuid:group_id>/messages/', views.redirect_to_index, name='get_group_messages'),
    path('chat/group/<uuid:group_id>/members/', views.redirect_to_index, name='group_members'),
    path('chat/group/<uuid:group_id>/settings/', views.redirect_to_index, name='group_settings'),
    path('chat/group/<uuid:group_id>/add-member/', views.redirect_to_index, name='add_group_member'),
    path('chat/group/<uuid:group_id>/remove-member/', views.redirect_to_index, name='remove_group_member'),
    path('chat/group/<uuid:group_id>/promote/', views.redirect_to_index, name='promote_member'),
    path('chat/group/<uuid:group_id>/leave/', views.redirect_to_index, name='leave_group'),
    
    # Amis - TEMPORAIREMENT DÉSACTIVÉS
    path('friends/', views.redirect_to_index, name='friend_requests'),
    path('friends/request/<int:user_id>/', views.redirect_to_index, name='send_friend_request'),
    path('friends/accept/<uuid:request_id>/', views.redirect_to_index, name='accept_friend_request'),
    
    # Page pour utilisateurs bannis
    path('banned/', views.banned_user_view, name='banned_user'),
    
    # API pour les notifications
    path('api/notifications/unread-count/', views.get_unread_notifications_count, name='unread_notifications_count'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    
    # API pour les notifications marketing - DÉSACTIVÉES
    path('api/marketing-notification/', views.redirect_to_index, name='get_marketing_notification'),
    path('api/marketing-notification/dismiss/', views.redirect_to_index, name='dismiss_marketing_notification'),
    path('api/marketing-notification/check/', views.redirect_to_index, name='check_marketing_notification'),
    path('friends/decline/<uuid:request_id>/', views.redirect_to_index, name='decline_friend_request'),
    path('friends/cancel/<uuid:request_id>/', views.redirect_to_index, name='cancel_friend_request'),
    
    # === URLs BOUTIQUE E-COMMERCE - TEMPORAIREMENT DÉSACTIVÉES ===
    
    # Pages principales boutique - Redirigées vers l'accueil
    path('shop/', views.redirect_to_index, name='shop_products'),
    path('shop/product/<slug:slug>/', views.redirect_to_index, name='shop_product_detail'),
    
    # Gestion du panier - Redirigées vers l'accueil
    path('shop/cart/', views.redirect_to_index, name='cart_view'),
    path('shop/cart/add/', views.redirect_to_index, name='add_to_cart'),
    path('shop/cart/update/', views.redirect_to_index, name='update_cart_item'),
    path('shop/cart/remove/', views.redirect_to_index, name='remove_from_cart'),
    
    # Processus de commande - Redirigées vers l'accueil
    path('shop/checkout/', views.redirect_to_index, name='checkout'),
    path('shop/payment/<uuid:order_id>/', views.redirect_to_index, name='shop_payment'),
    
    # CinetPay pour la boutique - Redirigées vers l'accueil
    path('shop/payment/cinetpay/initiate/<uuid:order_id>/', views.redirect_to_index, name='initiate_shop_payment'),
    path('shop/payment/cinetpay/notification/', views.redirect_to_index, name='shop_cinetpay_notification'),
    path('shop/payment/cinetpay/success/<uuid:order_id>/', views.redirect_to_index, name='shop_payment_success'),
    path('shop/payment/cinetpay/failed/<uuid:order_id>/', views.redirect_to_index, name='shop_payment_failed'),
    
    # Commandes utilisateur - Redirigées vers l'accueil
    path('shop/orders/', views.redirect_to_index, name='my_orders'),
    path('shop/order/<uuid:order_id>/', views.redirect_to_index, name='order_detail'),
    
    # Administration - Redirigée vers l'accueil
    path('admin/sync-shopify/', views.redirect_to_index, name='sync_shopify_products'),
    
    # Webhooks Shopify - Redirigées vers l'accueil
    path('webhooks/shopify/orders/', views.redirect_to_index, name='shopify_order_webhook'),
    path('webhooks/shopify/fulfillments/', views.redirect_to_index, name='shopify_fulfillment_webhook'),
    path('webhooks/shopify/refunds/', views.redirect_to_index, name='shopify_refund_webhook'),
    path('webhooks/shopify/products/create/', views.redirect_to_index, name='shopify_product_create_webhook'),
    path('webhooks/shopify/products/update/', views.redirect_to_index, name='shopify_product_update_webhook'),
    path('webhooks/shopify/products/delete/', views.redirect_to_index, name='shopify_product_delete_webhook'),
    
    # === URLs HIGHLIGHTS - TEMPORAIREMENT DÉSACTIVÉES POUR LE LANCEMENT ===
    
    # Pages principales Highlights - Redirigées vers la page d'accueil
    path('highlights/', views.redirect_to_index, name='highlights_home'),
    path('highlights/for-you/', views.redirect_to_index, name='highlights_for_you'),
    path('highlights/friends/', views.redirect_to_index, name='highlights_friends'),
    path('highlights/search/', views.redirect_to_index, name='highlights_search'),
    path('highlights/hashtag/<str:hashtag>/', views.redirect_to_index, name='highlights_hashtag'),
    
    # Gestion des Highlights - Redirigées vers la page d'accueil
    path('highlights/create/', views.redirect_to_index, name='create_highlight'),
    path('highlights/<uuid:highlight_id>/', views.redirect_to_index, name='highlight_detail'),
    path('highlights/<uuid:highlight_id>/delete/', views.redirect_to_index, name='delete_highlight'),
    
    # Actions sur les Highlights - Redirigées vers la page d'accueil
    path('highlights/<uuid:highlight_id>/appreciate/', views.redirect_to_index, name='toggle_highlight_appreciation'),
    # API Highlights - Redirigées vers la page d'accueil
    path('api/highlights/<uuid:highlight_id>/comments/', views.redirect_to_index, name='api_highlight_comments'),
    path('api/hashtag-suggestions/', views.redirect_to_index, name='hashtag_suggestions_api'),
    path('highlights/<uuid:highlight_id>/share/', views.redirect_to_index, name='share_highlight'),
    path('highlights/<uuid:highlight_id>/view/', views.redirect_to_index, name='record_highlight_view'),
    path('highlights/<uuid:highlight_id>/view-enhanced/', views.redirect_to_index, name='record_highlight_view_enhanced'),
    
    # Système d'abonnement - Redirigé vers la page d'accueil
    path('subscribe/<int:user_id>/', views.redirect_to_index, name='toggle_subscription'),
    path('subscriptions/', views.redirect_to_index, name='my_subscriptions'),
    path('subscribers/', views.redirect_to_index, name='my_subscribers'),
    
    # API pour les Highlights (AJAX) - Redirigées vers la page d'accueil
    path('api/highlights/feed/', views.redirect_to_index, name='highlights_feed_api'),
    path('api/highlights/<uuid:highlight_id>/context/', views.redirect_to_index, name='highlights_context_api'),
    path('api/highlights/<uuid:highlight_id>/comments/', views.redirect_to_index, name='highlight_comments_api'),
    
    # Gestion des devises
    path('change-currency/', views.change_currency, name='change_currency'),
    
    # URLs de vérification email
    path('verify-email/<uuid:token>/', views.verify_email, name='verify_email'),
    path('verify-email-code/', views.verify_email_code, name='verify_email_code'),
    path('resend-verification-email/', views.resend_verification_email, name='resend_verification_email'),
    path('send-verification-email/', views.send_verification_email_on_signup, name='send_verification_email_on_signup'),
    
    # URLs pour la gestion des mots de passe
    path('verify-current-password/', views.verify_current_password, name='verify_current_password'),
    path('update-password/', views.update_password, name='update_password'),
    
    # URLs pour la réinitialisation de mot de passe
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password-code/<str:email>/', views.reset_password_code, name='reset_password_code'),
    path('reset-password/<uuid:token>/', views.reset_password, name='reset_password'),
    
    # Pages légales
    path('conditions-utilisation/', views.condition_utilisation, name='condition_utilisation'),
    path('politique-confidentialite/', views.politique_confidentialite, name='politique_confidentialite'),
    
    # URLs admin pour les payouts
    path('payouts/dashboard/', admin_views.payout_dashboard, name='admin_payout_dashboard'),
    path('payouts/list/', admin_views.payout_list, name='admin_payout_list'),
    path('payouts/export-csv/', admin_views.export_payouts_csv, name='admin_export_payouts_csv'),
    path('payouts/stats-api/', admin_views.payout_stats_api, name='admin_payout_stats_api'),
    path('payouts/update-status/<uuid:payout_id>/', admin_views.update_payout_status, name='admin_update_payout_status'),
    
    # URLs admin pour les notifications vendeurs
    path('admin/pending-seller-notifications/', admin_views.pending_seller_notifications, name='pending_seller_notifications'),
    path('admin/mark-seller-notified/<uuid:transaction_id>/', admin_views.mark_seller_notified, name='mark_seller_notified'),
    
    # Webhook pour nettoyage automatique (GitHub Actions)
    path('api/cleanup-transactions/', views.webhook_cleanup_transactions, name='webhook_cleanup_transactions'),
]