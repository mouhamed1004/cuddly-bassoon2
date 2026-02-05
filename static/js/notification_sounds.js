// Gestion des sons de notification et indicateurs visuels
class NotificationManager {
    constructor() {
        this.audioContext = null;
        this.notificationSound = null;
        this.initAudio();
        this.setupNotificationIndicator();
        this.checkUnreadNotifications();
    }

    initAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            this.createNotificationSound();
        } catch (e) {
            console.log('Audio non supporté');
        }
    }

    // Sons de notification désactivés
    createNotificationSound() {
        // Désactivé
    }

    playNotificationSound() {
        // Désactivé
    }

    setupNotificationIndicator() {
        // Créer l'indicateur de notification s'il n'existe pas
        if (!document.querySelector('.notification-indicator')) {
            const indicator = document.createElement('div');
            indicator.className = 'notification-indicator';
            indicator.innerHTML = '<i class="fas fa-bell notification-link"></i>';
            indicator.onclick = () => window.location.href = '/notifications/';
            indicator.style.display = 'flex'; // S'assurer qu'il est visible
            document.body.appendChild(indicator);
            console.log('Indicateur de notification créé');
        }
    }

    async checkUnreadNotifications() {
        try {
            const response = await fetch('/api/notifications/unread-count/');
            if (response.ok) {
                const data = await response.json();
                this.updateNotificationIndicator(data.count > 0, data.count);
            }
        } catch (e) {
            console.log('Erreur lors de la vérification des notifications');
        }
    }

    updateNotificationIndicator(hasUnread, count = 0) {
        const indicator = document.querySelector('.notification-indicator');
        if (!indicator) return;

        if (hasUnread) {
            indicator.classList.add('has-unread');
            if (count > 0) {
                let badge = indicator.querySelector('.notification-count');
                if (!badge) {
                    badge = document.createElement('div');
                    badge.className = 'notification-count';
                    indicator.appendChild(badge);
                }
                badge.textContent = count > 1000 ? '1000+' : count;
            }
        } else {
            indicator.classList.remove('has-unread');
            const badge = indicator.querySelector('.notification-count');
            if (badge) badge.remove();
        }
    }

    showNotificationPopup(title, message) {
        const popup = document.createElement('div');
        popup.className = 'notification-popup';
        popup.innerHTML = `
            <div class="notification-popup-content">
                <i class="fas fa-bell"></i>
                <p>${message}</p>
            </div>
        `;
        
        document.body.appendChild(popup);
        
        setTimeout(() => popup.classList.add('show'), 100);
        
        setTimeout(() => {
            popup.classList.remove('show');
            setTimeout(() => popup.remove(), 500);
        }, 3000);
    }
}

// Initialiser le gestionnaire de notifications
const notificationManager = new NotificationManager();

// Écouter les nouvelles notifications via Pusher
if (typeof Pusher !== 'undefined') {
    const pusher = new Pusher('6c5ea23d443700ec8467', {
        cluster: 'eu'
    });
    
    const channel = pusher.subscribe('notifications');
    
    channel.bind('new_notification', function(data) {
        // Son désactivé
        notificationManager.showNotificationPopup(data.title, data.message);
        notificationManager.checkUnreadNotifications();
    });
}

// Vérifier les notifications à la connexion
document.addEventListener('DOMContentLoaded', function() {
    // Forcer la création de l'indicateur
    notificationManager.setupNotificationIndicator();
    notificationManager.checkUnreadNotifications();
});

// Aussi s'exécuter immédiatement si le DOM est déjà chargé
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        notificationManager.setupNotificationIndicator();
        notificationManager.checkUnreadNotifications();
    });
} else {
    // DOM déjà chargé
    notificationManager.setupNotificationIndicator();
    notificationManager.checkUnreadNotifications();
}
