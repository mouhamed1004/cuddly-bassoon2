"""
Gestionnaires de webhooks pour Shopify
Traitement des événements de commande, paiement et expédition
"""

import json
import hmac
import hashlib
import base64
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Order, ShopifyIntegration
# Shopify désactivé - Pas nécessaire pour le moment
# from .shopify_utils import update_order_from_shopify_webhook, upsert_product_from_shopify_payload, deactivate_product_by_shopify_id
from .models import Product
from decimal import Decimal
from django.utils import timezone

logger = logging.getLogger(__name__)

def verify_shopify_webhook(request, webhook_secret):
    """
    Vérifie l'authenticité d'un webhook Shopify
    """
    try:
        signature = request.headers.get('X-Shopify-Hmac-Sha256')
        if not signature:
            return False
        
        body = request.body
        digest = hmac.new(webhook_secret.encode('utf-8'), body, hashlib.sha256).digest()
        computed_signature = base64.b64encode(digest).decode('utf-8')
        return hmac.compare_digest(signature, computed_signature)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification du webhook: {e}")
        return False

@csrf_exempt
@require_POST
def shopify_order_webhook(request):
    """
    Webhook pour les mises à jour de commandes Shopify
    """
    try:
        # Récupérer l'intégration Shopify active
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            logger.error("Aucune intégration Shopify active")
            return HttpResponse("No active integration", status=400)
        
        # Vérifier la signature si un secret est configuré
        if integration.webhook_secret:
            if not verify_shopify_webhook(request, integration.webhook_secret):
                logger.error("Signature webhook invalide")
                return HttpResponse("Invalid signature", status=401)
        
        # Traiter les données du webhook
        webhook_data = json.loads(request.body)
        logger.info(f"Webhook Shopify reçu: {webhook_data.get('id')}")
        
        # Shopify désactivé - Pas nécessaire pour le moment
        # update_order_from_shopify_webhook(webhook_data)
        logger.info("Webhook Shopify ignoré (Shopify désactivé)")
        
        return HttpResponse("OK", status=200)
        
    except json.JSONDecodeError:
        logger.error("Données JSON invalides dans le webhook")
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Erreur dans shopify_order_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_product_create_webhook(request):
    try:
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            return HttpResponse("No active integration", status=400)
        if integration.webhook_secret and not verify_shopify_webhook(request, integration.webhook_secret):
            return HttpResponse("Invalid signature", status=401)
        data = json.loads(request.body)
        # Shopify désactivé - Pas nécessaire pour le moment
        # product = upsert_product_from_shopify_payload(data)
        logger.info("Webhook Shopify product create ignoré (Shopify désactivé)")
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error(f"Erreur product_create_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_product_update_webhook(request):
    try:
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            return HttpResponse("No active integration", status=400)
        if integration.webhook_secret and not verify_shopify_webhook(request, integration.webhook_secret):
            return HttpResponse("Invalid signature", status=401)
        data = json.loads(request.body)
        # Shopify désactivé - Pas nécessaire pour le moment
        # product = upsert_product_from_shopify_payload(data)
        logger.info("Webhook Shopify product update ignoré (Shopify désactivé)")
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error(f"Erreur product_update_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_product_delete_webhook(request):
    try:
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            return HttpResponse("No active integration", status=400)
        if integration.webhook_secret and not verify_shopify_webhook(request, integration.webhook_secret):
            return HttpResponse("Invalid signature", status=401)
        data = json.loads(request.body)
        shopify_id = data.get('id')
        # Shopify désactivé - Pas nécessaire pour le moment
        # if shopify_id:
        #     deactivate_product_by_shopify_id(str(shopify_id))
        logger.info("Webhook Shopify product delete ignoré (Shopify désactivé)")
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error(f"Erreur product_delete_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_fulfillment_webhook(request):
    """
    Webhook pour les mises à jour d'expédition Shopify
    """
    try:
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            return HttpResponse("No active integration", status=400)
        
        if integration.webhook_secret:
            if not verify_shopify_webhook(request, integration.webhook_secret):
                return HttpResponse("Invalid signature", status=401)
        
        webhook_data = json.loads(request.body)
        order_id = str(webhook_data.get('order_id'))
        
        # Trouver la commande locale
        order = Order.objects.filter(shopify_order_id=order_id).first()
        if order:
            order.status = 'shipped'
            order.shopify_fulfillment_status = 'fulfilled'
            order.save()
            
            logger.info(f"Commande {order.order_number} marquée comme expédiée")
        
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        logger.error(f"Erreur dans shopify_fulfillment_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_refund_webhook(request):
    """
    Webhook pour les remboursements Shopify
    """
    try:
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            return HttpResponse("No active integration", status=400)
        
        if integration.webhook_secret:
            if not verify_shopify_webhook(request, integration.webhook_secret):
                return HttpResponse("Invalid signature", status=401)
        
        webhook_data = json.loads(request.body)
        order_id = str(webhook_data.get('order_id'))
        
        # Trouver la commande locale
        order = Order.objects.filter(shopify_order_id=order_id).first()
        if order:
            order.status = 'refunded'
            order.payment_status = 'refunded'
            order.save()
            
            # Mettre à jour la transaction CinetPay si elle existe
            if hasattr(order, 'cinetpay_transaction'):
                order.cinetpay_transaction.status = 'refunded'
                order.cinetpay_transaction.save()
            
            logger.info(f"Commande {order.order_number} remboursée")
        
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        logger.error(f"Erreur dans shopify_refund_webhook: {e}")
        return HttpResponse("Internal error", status=500)

@csrf_exempt
@require_POST
def shopify_product_update_webhook(request):
    """
    Webhook pour les mises à jour de produits Shopify
    Synchronise automatiquement les prix et informations produit
    """
    try:
        # Récupérer l'intégration Shopify active
        integration = ShopifyIntegration.objects.filter(is_active=True).first()
        if not integration:
            logger.error("Aucune intégration Shopify active")
            return HttpResponse("No active integration", status=400)
        
        # Vérifier la signature si un secret est configuré
        if integration.webhook_secret:
            if not verify_shopify_webhook(request, integration.webhook_secret):
                logger.error("Signature webhook invalide")
                return HttpResponse("Invalid signature", status=401)
        
        # Parser les données du webhook
        webhook_data = json.loads(request.body)
        shopify_product_id = str(webhook_data.get('id'))
        
        if not shopify_product_id:
            logger.error("ID produit manquant dans le webhook")
            return HttpResponse("Missing product ID", status=400)
        
        # Trouver le produit local
        local_product = Product.objects.filter(
            shopify_product_id=shopify_product_id
        ).first()
        
        if not local_product:
            logger.warning(f"Produit local non trouvé pour Shopify ID: {shopify_product_id}")
            # Créer le produit s'il n'existe pas
            try:
                upsert_product_from_shopify_payload(webhook_data)
                logger.info(f"Nouveau produit créé depuis webhook: {webhook_data.get('title', 'N/A')}")
            except Exception as e:
                logger.error(f"Erreur création produit depuis webhook: {e}")
            return HttpResponse("OK", status=200)
        
        # Mettre à jour le produit existant
        updated = _update_product_from_webhook(local_product, webhook_data)
        
        if updated:
            logger.info(f"Produit mis à jour depuis webhook: {local_product.name}")
        else:
            logger.info(f"Aucune mise à jour nécessaire pour: {local_product.name}")
        
        return HttpResponse("OK", status=200)
        
    except json.JSONDecodeError:
        logger.error("Données JSON invalides dans le webhook")
        return HttpResponse("Invalid JSON", status=400)
    except Exception as e:
        logger.error(f"Erreur dans shopify_product_update_webhook: {e}")
        return HttpResponse("Internal error", status=500)

def _update_product_from_webhook(local_product, shopify_data):
    """
    Met à jour un produit local depuis les données webhook Shopify
    Retourne True si des modifications ont été apportées
    """
    updated = False
    
    try:
        # Récupérer le prix depuis la première variante
        variants = shopify_data.get('variants', [])
        if variants:
            first_variant = variants[0]
            shopify_price = first_variant.get('price')
            
            if shopify_price is not None and shopify_price != '':
                try:
                    new_price = Decimal(str(shopify_price))
                    if local_product.price != new_price:
                        old_price = local_product.price
                        local_product.price = new_price
                        updated = True
                        logger.info(f"Prix mis à jour: {old_price} -> {new_price} pour {local_product.name}")
                except (ValueError, TypeError):
                    logger.error(f"Prix invalide dans webhook: {shopify_price}")
            
            # Mettre à jour compare_price si disponible
            compare_price = first_variant.get('compare_at_price')
            if compare_price and compare_price != '':
                try:
                    new_compare_price = Decimal(str(compare_price))
                    if local_product.compare_price != new_compare_price:
                        local_product.compare_price = new_compare_price
                        updated = True
                except (ValueError, TypeError):
                    pass
        
        # Mettre à jour le nom si différent
        new_title = shopify_data.get('title', '')
        if new_title and local_product.name != new_title:
            local_product.name = new_title
            updated = True
        
        # Mettre à jour la description si différente
        new_description = shopify_data.get('body_html', '')
        if new_description and local_product.description != new_description:
            local_product.description = new_description
            updated = True
        
        # Mettre à jour le statut
        shopify_status = shopify_data.get('status', 'active')
        new_status = 'active' if shopify_status == 'active' else 'inactive'
        if local_product.status != new_status:
            local_product.status = new_status
            updated = True
        
        # Sauvegarder si des modifications ont été apportées
        if updated:
            local_product.updated_at = timezone.now()
            local_product.save()
        
        return updated
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du produit depuis webhook: {e}")
        return False