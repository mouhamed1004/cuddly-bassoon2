
import os
from twilio.rest import Client

# Configuration Twilio
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_number = os.environ.get('TWILIO_PHONE_NUMBER')

def test_twilio_sms():
    """Test SMS Twilio"""
    if not all([account_sid, auth_token, twilio_number]):
        print("❌ Variables Twilio manquantes")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body="🎉 Test SMS BLIZZ Gaming 2FA ! Votre plateforme est prête !",
            from_=twilio_number,
            to="+221781613137"  # Votre numéro
        )
        
        print(f"✅ SMS envoyé ! SID: {message.sid}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    test_twilio_sms()
