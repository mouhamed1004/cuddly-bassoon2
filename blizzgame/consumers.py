import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Transaction, Chat, Message, Dispute, DisputeMessage, Notification
from django.utils import timezone

class TransactionChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.transaction_id = self.scope['url_route']['kwargs']['transaction_id']
        self.room_group_name = f'chat_transaction_{self.transaction_id}'
        
        # Vérifier que l'utilisateur a accès à cette transaction
        if await self.check_transaction_access():
            # Rejoindre le groupe de chat
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Notifier que l'utilisateur a rejoint le chat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'username': self.scope['user'].username
                }
            )
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        # Quitter le groupe de chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing':
                await self.handle_typing()
            elif message_type == 'stop_typing':
                await self.handle_stop_typing()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_send_message(self, data):
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        
        if not content:
            return
        
        # Créer le message
        message = await self.create_message(content, message_type)
        
        if message:
            # Envoyer le message à tous les utilisateurs du groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'sender': message.sender.username,
                        'sender_id': message.sender.id,
                        'created_at': message.created_at.isoformat(),
                        'message_type': message.message_type,
                        'is_read': message.is_read
                    }
                }
            )

    async def handle_typing(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing',
                'username': self.scope['user'].username
            }
        )

    async def handle_stop_typing(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'stop_typing',
                'username': self.scope['user'].username
            }
        )
    
    async def chat_message(self, event):
        # Envoyer le message à l'utilisateur
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_joined(self, event):
        # Notifier qu'un utilisateur a rejoint
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username']
        }))

    async def typing(self, event):
        # Envoyer l'indicateur de frappe
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username']
        }))

    async def stop_typing(self, event):
        # Arrêter l'indicateur de frappe
        await self.send(text_data=json.dumps({
            'type': 'stop_typing',
            'username': event['username']
        }))

    @database_sync_to_async
    def check_transaction_access(self):
        """Vérifie que l'utilisateur a accès à cette transaction"""
        try:
            transaction = Transaction.objects.get(id=self.transaction_id)
            user = self.scope['user']
            return user == transaction.buyer or user == transaction.seller
        except Transaction.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, content, message_type):
        """Crée un message dans la base de données"""
        try:
            transaction = Transaction.objects.get(id=self.transaction_id)
            user = self.scope['user']
            
            # Récupérer ou créer le chat
            chat, created = Chat.objects.get_or_create(
                transaction=transaction,
                defaults={
                    'is_active': True,
                    'is_locked': transaction.status in ['pending', 'waiting_payment']
                }
            )
            
            # Créer le message
            message = Message.objects.create(
                chat=chat,
                sender=user,
                content=content,
                message_type=message_type
            )
            
            # Créer une notification pour l'autre utilisateur
            other_user = chat.get_other_user(user)
            if other_user:
                from .models import Notification
                Notification.objects.create(
                    user=other_user,
                    type='new_message',
                    title='Nouveau message',
                    content=f"Nouveau message de {user.username} dans la transaction",
                    transaction=transaction
                )
            
            return message
        except Exception as e:
            print(f"Erreur lors de la création du message: {e}")
            return None

class DisputeChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.dispute_id = self.scope['url_route']['kwargs']['dispute_id']
        self.room_group_name = f'chat_dispute_{self.dispute_id}'
        
        # Vérifier que l'utilisateur a accès à ce litige
        if await self.check_dispute_access():
            # Rejoindre le groupe de chat
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            
            # Notifier que l'utilisateur a rejoint le chat
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_joined',
                    'username': self.scope['user'].username
                }
            )
        else:
            await self.close()
    
    async def disconnect(self, close_code):
        # Quitter le groupe de chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing':
                await self.handle_typing()
            elif message_type == 'stop_typing':
                await self.handle_stop_typing()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))

    async def handle_send_message(self, data):
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        
        if not content:
            return
        
        # Créer le message
        message = await self.create_message(content, message_type)
        
        if message:
            # Envoyer le message à tous les utilisateurs du groupe
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': str(message.id),
                        'content': message.content,
                        'sender': message.sender.username,
                        'sender_id': message.sender.id,
                        'created_at': message.created_at.isoformat(),
                        'message_type': message.message_type,
                        'is_read': message.is_read,
                        'is_admin': message.sender.is_staff
                    }
                }
            )

    async def handle_typing(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing',
                'username': self.scope['user'].username
            }
        )

    async def handle_stop_typing(self):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'stop_typing',
                'username': self.scope['user'].username
            }
        )
    
    async def chat_message(self, event):
        # Envoyer le message à l'utilisateur
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_joined(self, event):
        # Notifier qu'un utilisateur a rejoint
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'username': event['username']
        }))

    async def typing(self, event):
        # Envoyer l'indicateur de frappe
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'username': event['username']
        }))

    async def stop_typing(self, event):
        # Arrêter l'indicateur de frappe
        await self.send(text_data=json.dumps({
            'type': 'stop_typing',
            'username': event['username']
        }))

    @database_sync_to_async
    def check_dispute_access(self):
        """Vérifie que l'utilisateur a accès à ce litige"""
        try:
            dispute = Dispute.objects.get(id=self.dispute_id)
            user = self.scope['user']
            return (user == dispute.transaction.buyer or 
                   user == dispute.transaction.seller or 
                   user.is_staff)
        except Dispute.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, content, message_type):
        """Crée un message dans la base de données"""
        try:
            dispute = Dispute.objects.get(id=self.dispute_id)
            user = self.scope['user']
            
            # Récupérer ou créer le chat
            chat, created = Chat.objects.get_or_create(
                dispute=dispute,
                defaults={
                    'is_active': True,
                    'is_locked': False
                }
            )
            
            # Créer le message
            message = Message.objects.create(
                chat=chat,
                sender=user,
                content=content,
                message_type=message_type
            )
            
            # Créer une notification pour l'autre utilisateur
            other_user = chat.get_other_user(user)
            if other_user:
                from .models import Notification
                Notification.objects.create(
                    user=other_user,
                    type='new_message',
                    title='Nouveau message',
                    content=f"Nouveau message de {user.username} dans le litige",
                    dispute=dispute
                )
            
            return message
        except Exception as e:
            print(f"Erreur lors de la création du message: {e}")
            return None