import pusher
from django.conf import settings

# Configuration Pusher
pusher_client = pusher.Pusher(
    app_id=settings.PUSHER_APP_ID,
    key=settings.PUSHER_KEY,
    secret=settings.PUSHER_SECRET,
    cluster=settings.PUSHER_CLUSTER,
    ssl=True
)

def send_message_to_chat(transaction_id, message_data):
    """
    Envoyer un message à un canal de chat spécifique
    """
    try:
        pusher_client.trigger(
            f'transaction-chat-{transaction_id}',
            'new-message',
            message_data
        )
        return True
    except Exception as e:
        print(f"Erreur Pusher: {e}")
        return False

def send_notification_to_user(user_id, notification_data):
    """
    Envoyer une notification en temps réel à un utilisateur spécifique
    """
    try:
        # Envoyer à l'utilisateur spécifique
        pusher_client.trigger(
            f'user-notifications-{user_id}',
            'new-notification',
            notification_data
        )
        
        # Envoyer aussi sur le canal global pour l'indicateur
        pusher_client.trigger(
            'notifications',
            'new_notification',
            {
                'title': notification_data.get('title', 'Nouvelle notification'),
                'message': notification_data.get('content', ''),
                'user_id': user_id
            }
        )
        
        return True
    except Exception as e:
        print(f"Erreur Pusher notification: {e}")
        return False
