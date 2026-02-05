// Système de notification SIMPLIFIÉ (sans Pusher)
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si l'utilisateur est connecté (vérifier la présence d'éléments d'authentification)
    const isLoggedIn = document.querySelector('.blizz-navbar .nav-links') || 
                       document.querySelector('[href*="logout"]') || 
                       document.querySelector('[href*="profile"]') ||
                       document.body.classList.contains('logged-in');
    
    if (isLoggedIn && !document.body.classList.contains('chat-page')) {
        console.log('🔔 Système de notifications simplifié activé');
        
        // Initialiser le compteur de notifications
        let previousCount = 0;
        
        // Gestion des notifications navigateur
        let browserNotificationPermission = 'default';
        
        // Fonction pour demander la permission des notifications
        function requestNotificationPermission() {
            if ('Notification' in window) {
                Notification.requestPermission().then(function(permission) {
                    browserNotificationPermission = permission;
                    console.log('🔔 Permission notifications:', permission);
                    
                    if (permission === 'granted') {
                        showBrowserNotification('Notifications activées', 'Vous recevrez maintenant des notifications de Blizz Gaming');
                    }
                });
            }
        }
        
        // Fonction pour afficher une notification navigateur
        function showBrowserNotification(title, message, options = {}) {
            if (browserNotificationPermission === 'granted' && 'Notification' in window) {
                const notification = new Notification(title, {
                    body: message,
                    icon: '/static/images/logo.png', // Icône Blizz
                    badge: '/static/images/logo.png',
                    tag: 'blizz-notification',
                    requireInteraction: false,
                    ...options
                });
                
                // Rediriger vers les notifications au clic
                notification.onclick = function() {
                    window.focus();
                    window.location.href = '/notifications/';
                    notification.close();
                };
                
                // Fermer automatiquement après 5 secondes
                setTimeout(() => notification.close(), 5000);
                
                return notification;
            }
            return null;
        }
        
        // Créer l'élément audio pour la notification sonore (DÉSACTIVÉ)
        // const notificationSound = new Audio('/static/sounds/notification.mp3');
        
        // Créer l'indicateur de notification
        const notificationIndicator = document.createElement('div');
        notificationIndicator.className = 'notification-indicator';
        notificationIndicator.innerHTML = `
            <i class="fas fa-bell"></i>
            <span class="notification-count">0</span>
        `;
        
        // Ajouter l'indicateur au menu
        const menu = document.querySelector('.blizz-navbar .nav-links');
        if (menu) {
            menu.appendChild(notificationIndicator);
        }
        
        // Rendre l'indicateur cliquable pour aller aux notifications
        notificationIndicator.style.cursor = 'pointer';
        notificationIndicator.addEventListener('click', function() {
            window.location.href = '/notifications/';
        });
        
        // Ajouter un bouton pour activer les notifications navigateur
        const enableNotificationsBtn = document.createElement('button');
        enableNotificationsBtn.className = 'enable-notifications-btn';
        enableNotificationsBtn.innerHTML = '<i class="fas fa-bell-slash"></i> Activer les notifications';
        enableNotificationsBtn.style.cssText = `
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-left: 1rem;
        `;
        
        // Ajouter le bouton à côté de l'indicateur
        if (menu) {
            menu.appendChild(enableNotificationsBtn);
        }
        
        // Gérer le clic sur le bouton d'activation
        enableNotificationsBtn.addEventListener('click', function() {
            requestNotificationPermission();
        });
        
        // Fonction pour mettre à jour le compteur
        function updateNotificationCount(count) {
            const countElement = notificationIndicator.querySelector('.notification-count');
            if (countElement) {
                countElement.textContent = count > 1000 ? '1000+' : count;
                if (count > 0) {
                    notificationIndicator.classList.add('has-notifications');
                } else {
                    notificationIndicator.classList.remove('has-notifications');
                }
            }
        }
        
        // Gestion des notifications navigateur (API Notification)
        function canUseBrowserNotifications() {
            return 'Notification' in window;
        }

        function requestBrowserPermissionIfNeeded() {
            if (!canUseBrowserNotifications()) return Promise.resolve('unsupported');
            const current = Notification.permission; // 'granted' | 'denied' | 'default'
            if (current === 'granted' || current === 'denied') {
                return Promise.resolve(current);
            }
            try {
                return Notification.requestPermission();
            } catch (e) {
                // Safari older
                return new Promise(resolve => {
                    Notification.requestPermission(resolve);
                });
            }
        }

        function showBrowserNotification(title, message) {
            if (!canUseBrowserNotifications()) return false;
            if (Notification.permission !== 'granted') return false;
            try {
                const n = new Notification(title || 'Blizz Gaming', {
                    body: message || 'Vous avez de nouvelles notifications',
                    icon: '/static/images/logo.png',
                    badge: '/static/images/logo.png',
                    tag: 'blizz-notification',
                    requireInteraction: false,
                    silent: false
                });
                n.onclick = function() {
                    try { 
                        window.focus(); 
                    } catch (_) {}
                    window.location.href = '/notifications/';
                    this.close();
                };
                
                // Fermer automatiquement après 5 secondes
                setTimeout(() => n.close(), 5000);
                
                return true;
            } catch (e) {
                console.log('Erreur notification navigateur:', e);
                return false;
            }
        }

        // Fallback visuel interne
        function showInlineNotification(message) {
            const notification = document.createElement('div');
            notification.className = 'notification-popup';
            notification.innerHTML = `
                <div class="notification-popup-content" style="cursor: pointer;">
                    <i class="fas fa-bell"></i>
                    <p>${message}</p>
                </div>
            `;
            notification.addEventListener('click', function() {
                window.location.href = '/notifications/';
            });

            document.body.appendChild(notification);
            setTimeout(() => notification.classList.add('show'), 100);
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 500);
            }, 3000);
        }

        // API unifiée pour afficher une notification utilisateur
        function showNotification(title, message) {
            // Tenter la notif navigateur si possible
            const usedBrowser = showBrowserNotification(title, message);
            if (!usedBrowser) {
                // Fallback visuel interne
                showInlineNotification(message || 'Vous avez de nouvelles notifications');
            }
        }
        
        // Fonction pour jouer le son de notification
        function playNotificationSound() {
            // Utiliser le gestionnaire de notifications sonores global
            if (window.playNotificationSound) {
                window.playNotificationSound();
            }
        }
        
        // Charger le compteur initial
        fetch('/notifications/unread/count/')
            .then(response => response.json())
            .then(data => {
                if (data.count !== undefined) {
                    updateNotificationCount(data.count);
                    previousCount = data.count;
                }
            })
            .catch(error => {
                console.log('🔔 Erreur lors du chargement des notifications:', error);
            });
        
        // Polling simple pour les nouvelles notifications (toutes les 30 secondes)
        setInterval(() => {
            fetch('/notifications/unread/count/')
                .then(response => response.json())
                .then(data => {
                    if (data.count !== undefined && data.count > previousCount) {
                        updateNotificationCount(data.count);
                        // Demander la permission si nécessaire avant d'afficher
                        requestBrowserPermissionIfNeeded().finally(() => {
                            showNotification('Blizz', 'Vous avez de nouvelles notifications');
                        });
                        playNotificationSound();
                        previousCount = data.count;
                    }
                })
                .catch(error => {
                    console.log('🔔 Erreur lors de la vérification des notifications:', error);
                });
        }, 30000); // Vérifier toutes les 30 secondes

        // Ajouter un bouton pour activer les notifications navigateur
        const enableNotificationsBtn = document.createElement('button');
        enableNotificationsBtn.className = 'enable-notifications-btn';
        enableNotificationsBtn.innerHTML = '<i class="fas fa-bell-slash"></i> Activer les notifications';
        enableNotificationsBtn.style.cssText = `
            background: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-left: 1rem;
            transition: all 0.3s ease;
        `;
        
        // Ajouter le bouton à côté de l'indicateur
        const menu = document.querySelector('.blizz-navbar .nav-links');
        if (menu) {
            menu.appendChild(enableNotificationsBtn);
        }
        
        // Gérer le clic sur le bouton d'activation
        enableNotificationsBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            requestBrowserPermissionIfNeeded().then(state => {
                if (state === 'granted') {
                    showBrowserNotification('Blizz Gaming', 'Notifications activées ! Vous recevrez maintenant des notifications système.');
                    enableNotificationsBtn.innerHTML = '<i class="fas fa-bell"></i> Notifications activées';
                    enableNotificationsBtn.style.background = '#28a745';
                } else if (state === 'denied') {
                    showInlineNotification('Notifications navigateur bloquées. Activez-les dans les paramètres de votre navigateur.');
                } else {
                    showInlineNotification('Permission requise pour les notifications navigateur.');
                }
            });
        });
        
        // Demander automatiquement la permission au chargement (une seule fois par session)
        if (!sessionStorage.getItem('notification-permission-asked')) {
            setTimeout(() => {
                requestBrowserPermissionIfNeeded().then(state => {
                    if (state === 'granted') {
                        showBrowserNotification('Blizz Gaming', 'Notifications activées ! Vous recevrez des notifications pour vos transactions et messages.');
                        enableNotificationsBtn.innerHTML = '<i class="fas fa-bell"></i> Notifications activées';
                        enableNotificationsBtn.style.background = '#28a745';
                    } else if (state === 'denied') {
                        // Ne pas harceler l'utilisateur
                        console.log('🔔 Notifications refusées par l\'utilisateur');
                    }
                    sessionStorage.setItem('notification-permission-asked', 'true');
                });
            }, 2000); // Attendre 2 secondes après le chargement
        }
        
        // Rendre l'indicateur cliquable pour aller aux notifications
        notificationIndicator.style.cursor = 'pointer';
        notificationIndicator.addEventListener('click', function() {
            window.location.href = '/notifications/';
        });
        
        console.log('✅ Système de notifications simplifié initialisé');
    } else {
        console.log('🔔 Système de notifications non activé - utilisateur non connecté ou page de chat');
    }
});
