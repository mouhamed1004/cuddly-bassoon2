/**
 * Système de notifications sonores pour BLIZZ
 * Utilise le fichier song_notif.wav pour les notifications
 */

class NotificationSoundManager {
    constructor() {
        this.audio = null;
        this.isEnabled = true;
        this.volume = 0.5;
        this.initializeAudio();
    }

    /**
     * Initialise l'audio avec le fichier de notification
     */
    initializeAudio() {
        try {
            this.audio = new Audio('/static/sounds/song_notif.wav');
            this.audio.volume = this.volume;
            this.audio.preload = 'auto';
        } catch (e) {
            console.warn('Impossible de charger le fichier audio de notification:', e);
            this.isEnabled = false;
        }
    }

    /**
     * Joue le son de notification
     */
    play() {
        if (!this.isEnabled || !this.audio) {
            return;
        }

        try {
            // Réinitialiser l'audio pour permettre la lecture multiple
            this.audio.currentTime = 0;
            this.audio.play().catch(error => {
                console.warn('Impossible de jouer le son de notification:', error);
            });
        } catch (e) {
            console.warn('Erreur lors de la lecture du son:', e);
        }
    }

    /**
     * Active ou désactive les notifications sonores
     */
    setEnabled(enabled) {
        this.isEnabled = enabled;
        localStorage.setItem('notificationSoundEnabled', enabled);
    }

    /**
     * Vérifie si les notifications sonores sont activées
     */
    isSoundEnabled() {
        const stored = localStorage.getItem('notificationSoundEnabled');
        return stored !== null ? stored === 'true' : true; // Par défaut activé
    }

    /**
     * Définit le volume des notifications
     */
    setVolume(volume) {
        this.volume = Math.max(0, Math.min(1, volume));
        if (this.audio) {
            this.audio.volume = this.volume;
        }
        localStorage.setItem('notificationSoundVolume', this.volume);
    }

    /**
     * Récupère le volume des notifications
     */
    getVolume() {
        const stored = localStorage.getItem('notificationSoundVolume');
        return stored !== null ? parseFloat(stored) : 0.5;
    }
}

// Instance globale du gestionnaire de notifications sonores
window.notificationSoundManager = new NotificationSoundManager();

// Restaurer les paramètres sauvegardés
window.notificationSoundManager.setEnabled(window.notificationSoundManager.isSoundEnabled());
window.notificationSoundManager.setVolume(window.notificationSoundManager.getVolume());

/**
 * Fonction utilitaire pour jouer le son de notification
 * Peut être appelée depuis n'importe où dans l'application
 */
window.playNotificationSound = function() {
    window.notificationSoundManager.play();
};

/**
 * Fonction pour jouer le son lors de l'arrivée de nouvelles notifications
 */
window.playNotificationSoundForNewNotification = function(notificationType) {
    // Jouer le son pour tous les types de notifications importantes
    const importantTypes = [
        'transaction_started',
        'new_message', 
        'transaction_update',
        'dispute_created',
        'purchase_intent'
    ];

    if (importantTypes.includes(notificationType)) {
        window.playNotificationSound();
    }
};

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = NotificationSoundManager;
}
