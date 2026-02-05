// Système de notification SIMPLIFIÉ (sans Pusher)
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si l'utilisateur est connecté et pas sur une page de chat
    if (document.body.classList.contains('logged-in') && !document.body.classList.contains('chat-page')) {
        console.log('🔔 Système de notifications simplifié activé');
        
        // Désactiver Pusher - utiliser un système de polling simple
        let notificationChannel = null;
        
        // Initialiser le compteur de notifications
        let previousCount = 0;
        
        // Créer l'élément audio pour la notification sonore (DÉSACTIVÉ)
        // const notificationSound = new Audio('/static/sounds/notification.mp3');
        
        // Créer l'indicateur de notification
        const notificationIndicator = document.createElement('div');
        notificationIndicator.className = 'notification-indicator';
        notificationIndicator.innerHTML = `
            <span class="notification-count">0</span>
            <a href="/notifications/" class="notification-link">
                <i class="fas fa-bell"></i>
            </a>
        `;
        document.body.appendChild(notificationIndicator);
        
        // Mettre à jour le compteur de notification dans le menu déroulant
        function updateNotificationCountInMenu(count) {
            const menuCountElement = document.getElementById('notification-count-menu');
            const mobileCountElement = document.getElementById('notification-count-menu-mobile');
            const displayCount = count > 1000 ? '1000+' : count;
            
            if (menuCountElement) {
                menuCountElement.textContent = displayCount;
                if (count > 0) {
                    menuCountElement.style.display = 'inline-block';
                } else {
                    menuCountElement.style.display = 'none';
                }
            }
            
            if (mobileCountElement) {
                mobileCountElement.textContent = displayCount;
                if (count > 0) {
                    mobileCountElement.style.display = 'inline-block';
                } else {
                    mobileCountElement.style.display = 'none';
                }
            }
        }
        
        // Mettre à jour le compteur de notification
        function updateNotificationCount(count) {
            const countElement = document.querySelector('.notification-count');
            
            if (count > 0) {
                countElement.textContent = count > 1000 ? '1000+' : count;
                notificationIndicator.classList.add('has-notifications');
                
                // Jouer un son si de nouvelles notifications sont arrivées (DÉSACTIVÉ)
                if (count > previousCount) {
                    // notificationSound.play().catch(error => {
                    //     console.log('Erreur lors de la lecture du son:', error);
                    // });
                    
                    // Afficher une notification visuelle
                    showNotificationPopup(count - previousCount);
                }
            } else {
                countElement.textContent = '0';
                notificationIndicator.classList.remove('has-notifications');
            }
            
            previousCount = count;
        }
        
        // Écouter les nouvelles notifications en temps réel
        notificationChannel.bind('new-notification', function(data) {
            const count = data.count || 0;
            updateNotificationCount(count);
            updateNotificationCountInMenu(count);
        });
        
        // Fonction pour afficher une notification visuelle
        function showNotificationPopup(newCount) {
            const popup = document.createElement('div');
            popup.className = 'notification-popup';
            popup.innerHTML = `
                <div class="notification-popup-content">
                    <i class="fas fa-bell"></i>
                    <p>Vous avez ${newCount} nouvelle${newCount > 1 ? 's' : ''} notification${newCount > 1 ? 's' : ''}!</p>
                </div>
            `;
            document.body.appendChild(popup);
            
            // Animer l'apparition
            setTimeout(() => {
                popup.classList.add('show');
            }, 100);
            
            // Supprimer après quelques secondes
            setTimeout(() => {
                popup.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(popup);
                }, 500);
            }, 5000);
        }
        
        // Charger le nombre initial de notifications
        function loadInitialNotifications() {
            fetch('/notifications/unread/count/')
                .then(response => response.json())
                .then(data => {
                    const count = data.count || 0;
                    updateNotificationCount(count);
                    updateNotificationCountInMenu(count);
                })
                .catch(error => {
                    console.error('Erreur lors du chargement des notifications:', error);
                });
        }
        
        // Charger les notifications au démarrage
        loadInitialNotifications();
    }
});
