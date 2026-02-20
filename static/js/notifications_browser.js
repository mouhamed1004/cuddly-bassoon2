/**
 * Système de notifications navigateur pour Blizz Gaming
 * Gère les notifications natives du navigateur + notifications visuelles
 */

document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si l'utilisateur est connecté
    const isLoggedIn = document.querySelector('.blizz-navbar .nav-links') || 
                       document.querySelector('[href*="logout"]') || 
                       document.querySelector('[href*="profile"]') ||
                       document.body.classList.contains('logged-in');
    
    // Ne pas activer sur les pages de chat (elles ont leur propre système)
    if (!isLoggedIn || document.body.classList.contains('chat-page')) {
        console.log('🔔 Notifications navigateur désactivées (non connecté ou page de chat)');
        return;
    }
    
    console.log('🔔 Initialisation du système de notifications navigateur');
    
    // Si on est sur la page notifications, réinitialiser le compteur
    if (window.location.pathname === '/notifications/') {
        console.log('📄 Page notifications détectée - Réinitialisation du compteur');
        localStorage.setItem('blizz_last_notif_count', '0');
    }
    
    // ========================================
    // VARIABLES GLOBALES
    // ========================================
    
    // Récupérer le compteur précédent depuis localStorage
    let previousNotificationCount = parseInt(localStorage.getItem('blizz_last_notif_count') || '0', 10);
    let notificationPermission = Notification.permission; // 'granted', 'denied', 'default'
    let pollingInterval = null;
    
    // ========================================
    // FONCTIONS DE GESTION DES PERMISSIONS
    // ========================================
    
    /**
     * Vérifie si les notifications navigateur sont supportées
     */
    function isNotificationSupported() {
        return 'Notification' in window;
    }
    
    /**
     * Demande la permission pour les notifications navigateur
     */
    async function requestNotificationPermission() {
        if (!isNotificationSupported()) {
            console.warn('⚠️ Les notifications navigateur ne sont pas supportées');
            return 'unsupported';
        }
        
        // Si déjà accordée ou refusée, retourner l'état actuel
        if (notificationPermission === 'granted' || notificationPermission === 'denied') {
            return notificationPermission;
        }
        
        try {
            // Demander la permission
            const permission = await Notification.requestPermission();
            notificationPermission = permission;
            console.log('🔔 Permission notifications:', permission);
            
            // Mettre à jour le bouton
            updateEnableButton();
            
            // Afficher une notification de test si accordée
            if (permission === 'granted') {
                showBrowserNotification(
                    'Notifications activées !',
                    'Vous recevrez maintenant des notifications de Blizz Gaming'
                );
            }
            
            return permission;
        } catch (error) {
            console.error('❌ Erreur lors de la demande de permission:', error);
            return 'error';
        }
    }
    
    // ========================================
    // FONCTIONS D'AFFICHAGE DES NOTIFICATIONS
    // ========================================
    
    /**
     * Affiche une notification navigateur native
     */
    function showBrowserNotification(title, message, options = {}) {
        if (!isNotificationSupported()) {
            console.warn('⚠️ Notifications navigateur non supportées');
            return false;
        }
        
        if (notificationPermission !== 'granted') {
            console.log('🔔 Permission non accordée, affichage notification visuelle');
            return false;
        }
        
        try {
            const notification = new Notification(title, {
                body: message,
                icon: '/static/favicon.ico',
                badge: '/static/favicon.ico',
                tag: 'blizz-notification-' + Date.now(),
                requireInteraction: false,
                silent: false,
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
            
            console.log('✅ Notification navigateur affichée:', title);
            return true;
        } catch (error) {
            console.error('❌ Erreur affichage notification navigateur:', error);
            return false;
        }
    }
    
    /**
     * Affiche une notification visuelle (fallback)
     */
    function showVisualNotification(message) {
        const notification = document.createElement('div');
        notification.className = 'blizz-notification-popup';
        notification.innerHTML = `
            <div class="blizz-notification-content">
                <i class="fas fa-bell"></i>
                <p>${message}</p>
            </div>
        `;
        
        // Styles inline
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(108, 92, 231, 0.4);
            z-index: 10000;
            cursor: pointer;
            opacity: 0;
            transform: translateX(400px);
            transition: all 0.3s ease;
        `;
        
        notification.querySelector('.blizz-notification-content').style.cssText = `
            display: flex;
            align-items: center;
            gap: 0.75rem;
        `;
        
        // Rediriger au clic
        notification.addEventListener('click', () => {
            window.location.href = '/notifications/';
        });
        
        document.body.appendChild(notification);
        
        // Animer l'apparition
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Supprimer après 5 secondes
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 5000);
        
        console.log('✅ Notification visuelle affichée');
    }
    
    /**
     * Affiche une notification (navigateur ou visuelle selon disponibilité)
     */
    function showNotification(title, message) {
        const browserShown = showBrowserNotification(title, message);
        
        // Si la notification navigateur n'a pas pu être affichée, utiliser le fallback visuel
        if (!browserShown) {
            showVisualNotification(message);
        }
        
        // Jouer un son si disponible
        if (window.playNotificationSound) {
            window.playNotificationSound();
        }
    }
    
    // ========================================
    // INTERFACE UTILISATEUR
    // ========================================
    
    /**
     * Injecte les styles pour l'animation de pulsation (une seule fois)
     */
    function injectPulseStyles() {
        if (document.getElementById('blizz-notification-pulse-styles')) return;
        const style = document.createElement('style');
        style.id = 'blizz-notification-pulse-styles';
        style.textContent = `
            @keyframes blizz-notif-pulse-ring {
                0% { transform: scale(0.8); opacity: 0.6; }
                100% { transform: scale(1.8); opacity: 0; }
            }
            .notification-indicator-wrapper .blizz-pulse-ring {
                position: absolute;
                left: 50%;
                top: 50%;
                width: 50px;
                height: 50px;
                margin-left: -25px;
                margin-top: -25px;
                border-radius: 50%;
                border: 2px solid rgba(108, 92, 231, 0.6);
                pointer-events: none;
                opacity: 0;
            }
            .notification-indicator-wrapper.has-notifications .blizz-pulse-ring {
                animation: blizz-notif-pulse-ring 1.8s ease-out infinite;
            }
            .notification-indicator-wrapper.has-notifications .blizz-pulse-ring:nth-child(2) {
                animation-delay: 0.6s;
            }
            .notification-indicator-wrapper.has-notifications .blizz-pulse-ring:nth-child(3) {
                animation-delay: 1.2s;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Crée l'indicateur de notifications flottant (aligné sous le bouton WhatsApp)
     */
    function createNotificationIndicator() {
        injectPulseStyles();

        const wrapper = document.createElement('div');
        wrapper.className = 'notification-indicator-wrapper';

        // Anneaux de pulsation (visibles quand has-notifications)
        for (let i = 0; i < 3; i++) {
            const ring = document.createElement('div');
            ring.className = 'blizz-pulse-ring';
            wrapper.appendChild(ring);
        }

        const indicator = document.createElement('div');
        indicator.className = 'notification-indicator';
        indicator.innerHTML = `
            <span class="notification-count">0</span>
            <a href="/notifications/" class="notification-link">
                <i class="fas fa-bell"></i>
            </a>
        `;

        // Styles inline pour le wrapper (position fixe)
        wrapper.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9998;
            width: 50px;
            height: 50px;
        `;

        // Styles inline pour l'indicateur flottant
        indicator.style.cssText = `
            position: relative;
            width: 100%;
            height: 100%;
            background: rgba(15, 23, 41, 0.9);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 0 15px rgba(0, 0, 0, 0.3);
            cursor: pointer;
            transition: all 0.3s ease;
            border: 2px solid rgba(108, 92, 231, 0.35);
        `;
        
        // Style pour le compteur (badge rouge allongé)
        const badge = indicator.querySelector('.notification-count');
        badge.style.cssText = `
            position: absolute;
            top: -6px;
            right: -6px;
            background: #e74c3c;
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 999px;
            min-width: 22px;
            height: 18px;
            display: none;
            border: 2px solid #0f0f23;
            line-height: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-sizing: border-box;
            text-align: center;
        `;
        
        // Style pour le lien
        const link = indicator.querySelector('.notification-link');
        link.style.cssText = `
            color: #fff;
            font-size: 20px;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
        `;
        
        // Animation au survol
        indicator.addEventListener('mouseenter', () => {
            indicator.style.transform = 'translateY(-2px)';
            indicator.style.boxShadow = '0 5px 15px rgba(108, 92, 231, 0.3)';
        });

        indicator.addEventListener('mouseleave', () => {
            indicator.style.transform = 'translateY(0)';
            indicator.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';
        });

        wrapper.appendChild(indicator);
        document.body.appendChild(wrapper);

        // Responsive (mêmes règles que le bouton WhatsApp en mobile)
        const mq = window.matchMedia('(max-width: 768px)');
        const applyMobile = () => {
            if (mq.matches) {
                wrapper.style.right = '15px';
                wrapper.style.bottom = '20px';
            } else {
                wrapper.style.right = '20px';
                wrapper.style.bottom = '20px';
            }
        };
        applyMobile();
        mq.addEventListener('change', applyMobile);
        
        return indicator;
    }
    
    /**
     * Crée le bouton d'activation des notifications
     */
    function createEnableButton() {
        const button = document.createElement('button');
        button.className = 'blizz-enable-notifications-btn';
        button.innerHTML = '<i class="fas fa-bell-slash"></i> Activer les notifications';
        
        // Styles inline
        button.style.cssText = `
            background: var(--primary-color, #6c5ce7);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
            margin-left: 1rem;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
        `;
        
        button.addEventListener('mouseenter', () => {
            button.style.transform = 'translateY(-2px)';
            button.style.boxShadow = '0 5px 15px rgba(108, 92, 231, 0.3)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'translateY(0)';
            button.style.boxShadow = 'none';
        });
        
        // Gérer le clic
        button.addEventListener('click', async (e) => {
            e.stopPropagation();
            const permission = await requestNotificationPermission();
            
            if (permission === 'denied') {
                showVisualNotification('Notifications bloquées. Activez-les dans les paramètres de votre navigateur.');
            } else if (permission === 'unsupported') {
                showVisualNotification('Votre navigateur ne supporte pas les notifications.');
            }
        });
        
        // Ajouter au menu
        const menu = document.querySelector('.blizz-navbar .nav-links');
        if (menu) {
            menu.appendChild(button);
        }
        
        return button;
    }
    
    /**
     * Met à jour l'état du bouton d'activation
     */
    function updateEnableButton() {
        const button = document.querySelector('.blizz-enable-notifications-btn');
        if (!button) return;
        
        if (notificationPermission === 'granted') {
            button.innerHTML = '<i class="fas fa-bell"></i> Notifications activées';
            button.style.background = '#28a745';
        } else if (notificationPermission === 'denied') {
            button.innerHTML = '<i class="fas fa-bell-slash"></i> Notifications bloquées';
            button.style.background = '#e74c3c';
            button.disabled = true;
        } else {
            button.innerHTML = '<i class="fas fa-bell-slash"></i> Activer les notifications';
            button.style.background = 'var(--primary-color, #6c5ce7)';
        }
    }
    
    /**
     * Met à jour le compteur de notifications
     */
    function updateNotificationCount(count) {
        const badge = document.querySelector('.notification-count');
        const indicator = document.querySelector('.notification-indicator');
        const wrapper = document.querySelector('.notification-indicator-wrapper');
        
        if (!badge || !indicator) return;
        
        if (count > 0) {
            badge.textContent = count > 999 ? '999+' : count;
            badge.style.display = 'block';
            if (wrapper) wrapper.classList.add('has-notifications');
        } else {
            badge.textContent = '0';
            badge.style.display = 'none';
            if (wrapper) wrapper.classList.remove('has-notifications');
        }
    }
    
    // ========================================
    // POLLING DES NOTIFICATIONS
    // ========================================
    
    /**
     * Vérifie les nouvelles notifications
     */
    async function checkForNewNotifications() {
        try {
            console.log('🔍 Vérification des notifications...');
            const response = await fetch('/notifications/unread/count/');
            const data = await response.json();
            
            console.log('📊 Données reçues:', data);
            console.log('📊 Compteur précédent:', previousNotificationCount);
            
            if (data.count !== undefined) {
                const currentCount = data.count;
                
                // Si de nouvelles notifications sont arrivées
                if (currentCount > previousNotificationCount && previousNotificationCount > 0) {
                    const newCount = currentCount - previousNotificationCount;
                    console.log(`🔔 ${newCount} nouvelle(s) notification(s) détectée(s)!`);
                    console.log(`🔔 Permission actuelle: ${notificationPermission}`);
                    
                    // Afficher la notification
                    showNotification(
                        'Blizz Gaming',
                        `Vous avez ${newCount} nouvelle${newCount > 1 ? 's' : ''} notification${newCount > 1 ? 's' : ''}`
                    );
                }
                
                // Mettre à jour le compteur
                updateNotificationCount(currentCount);
                previousNotificationCount = currentCount;
                
                // Sauvegarder dans localStorage pour persister entre les pages
                localStorage.setItem('blizz_last_notif_count', currentCount.toString());
                
                console.log('✅ Compteur mis à jour:', currentCount);
            }
        } catch (error) {
            console.error('❌ Erreur lors de la vérification des notifications:', error);
        }
    }
    
    /**
     * Démarre le polling des notifications
     */
    function startNotificationPolling() {
        // Vérifier immédiatement
        checkForNewNotifications();
        
        // Puis vérifier toutes les 15 secondes
        pollingInterval = setInterval(checkForNewNotifications, 15000);
        
        console.log('✅ Polling des notifications démarré (toutes les 15 secondes)');
    }
    
    /**
     * Arrête le polling des notifications
     */
    function stopNotificationPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
            console.log('🛑 Polling des notifications arrêté');
        }
    }
    
    // ========================================
    // INITIALISATION
    // ========================================
    
    // Créer l'interface
    const notificationIndicator = createNotificationIndicator();
    const enableButton = createEnableButton();
    
    // Mettre à jour l'état initial du bouton
    updateEnableButton();
    
    // Démarrer le polling
    startNotificationPolling();
    
    // Demander automatiquement la permission après 3 secondes (une seule fois par session)
    if (!sessionStorage.getItem('blizz-notification-permission-asked')) {
        setTimeout(async () => {
            if (notificationPermission === 'default') {
                await requestNotificationPermission();
            }
            sessionStorage.setItem('blizz-notification-permission-asked', 'true');
        }, 3000);
    }
    
    // Arrêter le polling quand l'utilisateur quitte la page
    window.addEventListener('beforeunload', stopNotificationPolling);
    
    console.log('✅ Système de notifications navigateur initialisé');
});
