// Script simple pour l'indicateur de notification
(function() {
    'use strict';
    
    console.log('Chargement du script d\'indicateur de notification');
    
    // Créer l'indicateur de notification
    function createNotificationIndicator() {
        // Vérifier si l'indicateur existe déjà
        if (document.querySelector('.notification-indicator')) {
            console.log('Indicateur déjà présent');
            return;
        }
        
        console.log('Création de l\'indicateur de notification');
        
        const indicator = document.createElement('div');
        indicator.className = 'notification-indicator';
        indicator.innerHTML = '<i class="fas fa-bell notification-link"></i>';
        indicator.onclick = function() {
            window.location.href = '/notifications/';
        };
        
        // Forcer le style
        indicator.style.position = 'fixed';
        indicator.style.bottom = '20px';
        indicator.style.right = '20px';
        indicator.style.width = '50px';
        indicator.style.height = '50px';
        indicator.style.borderRadius = '50%';
        indicator.style.backgroundColor = 'rgba(15, 23, 41, 0.9)';
        indicator.style.display = 'flex';
        indicator.style.alignItems = 'center';
        indicator.style.justifyContent = 'center';
        indicator.style.boxShadow = '0 0 15px rgba(0, 0, 0, 0.3)';
        indicator.style.zIndex = '1000';
        indicator.style.cursor = 'pointer';
        indicator.style.border = '2px solid rgba(108, 92, 231, 0.3)';
        indicator.style.transition = 'all 0.3s ease';
        
        document.body.appendChild(indicator);
        console.log('Indicateur créé et ajouté au DOM');
        
        // Vérifier les notifications
        checkUnreadNotifications(indicator);
    }
    
    // Vérifier les notifications non lues
    async function checkUnreadNotifications(indicator) {
        try {
            console.log('Vérification des notifications non lues...');
            const response = await fetch('/api/notifications/unread-count/');
            
            if (response.ok) {
                const data = await response.json();
                console.log('Nombre de notifications non lues:', data.count);
                
                if (data.count > 0) {
                    // Ajouter la classe pour les notifications non lues
                    indicator.classList.add('has-unread');
                    
                    // Créer ou mettre à jour le badge
                    let badge = indicator.querySelector('.notification-count');
                    if (!badge) {
                        badge = document.createElement('div');
                        badge.className = 'notification-count';
                        badge.style.position = 'absolute';
                        badge.style.top = '-5px';
                        badge.style.right = '-5px';
                        badge.style.backgroundColor = '#ff4757';
                        badge.style.color = 'white';
                        badge.style.width = '20px';
                        badge.style.height = '20px';
                        badge.style.borderRadius = '50%';
                        badge.style.fontSize = '12px';
                        badge.style.display = 'flex';
                        badge.style.alignItems = 'center';
                        badge.style.justifyContent = 'center';
                        badge.style.fontWeight = 'bold';
                        indicator.appendChild(badge);
                    }
                    
                    badge.textContent = data.count > 1000 ? '1000+' : data.count;
                    console.log('Badge mis à jour avec', data.count);
                } else {
                    // Supprimer la classe et le badge
                    indicator.classList.remove('has-unread');
                    const badge = indicator.querySelector('.notification-count');
                    if (badge) {
                        badge.remove();
                    }
                }
            } else {
                console.log('Erreur lors de la récupération des notifications:', response.status);
            }
        } catch (error) {
            console.log('Erreur lors de la vérification des notifications:', error);
        }
    }
    
    // Initialiser quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createNotificationIndicator);
    } else {
        createNotificationIndicator();
    }
    
    // Aussi essayer après un délai pour être sûr
    setTimeout(createNotificationIndicator, 1000);
    
})();
