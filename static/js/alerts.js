/**
 * Système d'alertes stylisées global
 * Remplace les alert() natives par des alertes personnalisées
 */

// Configuration
const ALERT_CONFIG = {
    autoHide: true,
    duration: 5000, // 5 secondes
    maxAlerts: 5, // Maximum d'alertes simultanées
    position: 'top-right' // top-right, top-left, bottom-right, bottom-left
};

// Compteur d'alertes
let alertCount = 0;

/**
 * Affiche une alerte stylisée
 * @param {string} message - Message à afficher
 * @param {string} type - Type d'alerte (success, error, warning, info)
 * @param {string} title - Titre optionnel
 * @param {Object} options - Options supplémentaires
 */
function showCustomAlert(message, type = 'info', title = '', options = {}) {
    // Supprimer les alertes en trop
    const existingAlerts = document.querySelectorAll('.custom-alert');
    if (existingAlerts.length >= ALERT_CONFIG.maxAlerts) {
        existingAlerts[0].remove();
    }
    
    // Créer l'alerte
    const alert = document.createElement('div');
    alert.className = `custom-alert ${type}`;
    alert.id = `alert-${Date.now()}`;
    
    // Icône selon le type
    const icons = {
        success: 'fas fa-check-circle',
        error: 'fas fa-exclamation-triangle',
        warning: 'fas fa-exclamation-circle',
        info: 'fas fa-info-circle'
    };
    
    // Contenu
    const content = title ? 
        `<div class="alert-content">
            <div class="alert-title">${title}</div>
            <div class="alert-message">${message}</div>
        </div>` :
        `<div class="alert-content">${message}</div>`;
    
    alert.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        ${content}
        <button class="alert-close" onclick="closeCustomAlert('${alert.id}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    // Ajouter au DOM
    document.body.appendChild(alert);
    alertCount++;
    
    // Positionner l'alerte
    positionAlert(alert);
    
    // Auto-suppression
    if (ALERT_CONFIG.autoHide) {
        setTimeout(() => {
            closeCustomAlert(alert.id);
        }, options.duration || ALERT_CONFIG.duration);
    }
    
    // Callback onShow
    if (options.onShow && typeof options.onShow === 'function') {
        options.onShow(alert);
    }
    
    return alert;
}

/**
 * Ferme une alerte
 * @param {string} alertId - ID de l'alerte à fermer
 */
function closeCustomAlert(alertId) {
    const alert = document.getElementById(alertId);
    if (alert) {
        alert.classList.add('hide');
        setTimeout(() => {
            if (alert.parentElement) {
                alert.remove();
                alertCount--;
                repositionAlerts();
            }
        }, 300);
    }
}

/**
 * Positionne une alerte
 * @param {HTMLElement} alert - Élément alerte
 */
function positionAlert(alert) {
    const alerts = document.querySelectorAll('.custom-alert');
    const index = Array.from(alerts).indexOf(alert);
    
    if (ALERT_CONFIG.position === 'top-right') {
        alert.style.top = `${20 + (index * 80)}px`;
        alert.style.right = '20px';
    } else if (ALERT_CONFIG.position === 'top-left') {
        alert.style.top = `${20 + (index * 80)}px`;
        alert.style.left = '20px';
    } else if (ALERT_CONFIG.position === 'bottom-right') {
        alert.style.bottom = `${20 + (index * 80)}px`;
        alert.style.right = '20px';
    } else if (ALERT_CONFIG.position === 'bottom-left') {
        alert.style.bottom = `${20 + (index * 80)}px`;
        alert.style.left = '20px';
    }
}

/**
 * Repositionne toutes les alertes
 */
function repositionAlerts() {
    const alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach((alert, index) => {
        positionAlert(alert);
    });
}

/**
 * Ferme toutes les alertes
 */
function closeAllAlerts() {
    const alerts = document.querySelectorAll('.custom-alert');
    alerts.forEach(alert => {
        closeCustomAlert(alert.id);
    });
}

/**
 * Affiche une alerte de succès
 * @param {string} message - Message
 * @param {string} title - Titre optionnel
 * @param {Object} options - Options
 */
function showSuccessAlert(message, title = '', options = {}) {
    return showCustomAlert(message, 'success', title, options);
}

/**
 * Affiche une alerte d'erreur
 * @param {string} message - Message
 * @param {string} title - Titre optionnel
 * @param {Object} options - Options
 */
function showErrorAlert(message, title = '', options = {}) {
    return showCustomAlert(message, 'error', title, options);
}

/**
 * Affiche une alerte d'avertissement
 * @param {string} message - Message
 * @param {string} title - Titre optionnel
 * @param {Object} options - Options
 */
function showWarningAlert(message, title = '', options = {}) {
    return showCustomAlert(message, 'warning', title, options);
}

/**
 * Affiche une alerte d'information
 * @param {string} message - Message
 * @param {string} title - Titre optionnel
 * @param {Object} options - Options
 */
function showInfoAlert(message, title = '', options = {}) {
    return showCustomAlert(message, 'info', title, options);
}

/**
 * Affiche une alerte de validation de formulaire
 * @param {string} message - Message
 * @param {HTMLElement} field - Champ de formulaire
 */
function showFormAlert(message, field = null) {
    // Supprimer les alertes de formulaire existantes
    const existingAlerts = document.querySelectorAll('.form-alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Créer l'alerte
    const alert = document.createElement('div');
    alert.className = 'form-alert';
    alert.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
    `;
    
    // Insérer après le champ ou au début du formulaire
    if (field) {
        field.parentNode.insertBefore(alert, field.nextSibling);
        field.focus();
    } else {
        const form = document.querySelector('form');
        if (form) {
            form.insertBefore(alert, form.firstChild);
        }
    }
    
    // Auto-suppression
    setTimeout(() => {
        if (alert.parentElement) {
            alert.remove();
        }
    }, 5000);
    
    return alert;
}

/**
 * Affiche une alerte inline
 * @param {string} message - Message
 * @param {HTMLElement} container - Conteneur
 */
function showInlineAlert(message, container) {
    const alert = document.createElement('div');
    alert.className = 'inline-alert';
    alert.innerHTML = `
        <i class="fas fa-exclamation-triangle"></i>
        <span>${message}</span>
    `;
    
    if (container) {
        container.appendChild(alert);
    }
    
    return alert;
}

/**
 * Affiche une modale de confirmation stylisée
 * @param {string} message - Message de confirmation
 * @param {string} title - Titre de la confirmation
 * @param {Function} onConfirm - Callback si confirmé
 * @param {Function} onCancel - Callback si annulé
 */
function showCustomConfirm(message, title = 'Confirmation', onConfirm = null, onCancel = null) {
    return new Promise((resolve) => {
        // Créer la modale
        const modal = document.createElement('div');
        modal.className = 'confirmation-modal';
        modal.id = `confirm-${Date.now()}`;
        
        modal.innerHTML = `
            <div class="confirmation-content">
                <div class="confirmation-icon">
                    <i class="fas fa-question-circle"></i>
                </div>
                <div class="confirmation-title">${title}</div>
                <div class="confirmation-message">${message}</div>
                <div class="confirmation-buttons">
                    <button class="confirmation-btn confirm" onclick="handleConfirm('${modal.id}', true)">
                        <i class="fas fa-check"></i> Confirmer
                    </button>
                    <button class="confirmation-btn cancel" onclick="handleConfirm('${modal.id}', false)">
                        <i class="fas fa-times"></i> Annuler
                    </button>
                </div>
            </div>
        `;
        
        // Ajouter au DOM
        document.body.appendChild(modal);
        
        // Gérer les événements
        window.handleConfirm = function(modalId, confirmed) {
            const modalElement = document.getElementById(modalId);
            if (modalElement) {
                modalElement.classList.add('hide');
                setTimeout(() => {
                    if (modalElement.parentElement) {
                        modalElement.remove();
                    }
                    resolve(confirmed);
                    
                    // Appeler les callbacks
                    if (confirmed && onConfirm) {
                        onConfirm();
                    } else if (!confirmed && onCancel) {
                        onCancel();
                    }
                }, 300);
            }
        };
        
        // Fermer avec Escape
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                handleConfirm(modal.id, false);
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // Fermer en cliquant sur le fond
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                handleConfirm(modal.id, false);
            }
        });
    });
}

/**
 * Remplace les confirm() natives
 */
function replaceNativeConfirms() {
    // Sauvegarder l'original
    window.originalConfirm = window.confirm;
    
    // Remplacer par notre système
    window.confirm = function(message) {
        return showCustomConfirm(message, 'Confirmation');
    };
}

/**
 * Remplace les alert() natives
 */
function replaceNativeAlerts() {
    // Sauvegarder l'original
    window.originalAlert = window.alert;
    
    // Remplacer par notre système
    window.alert = function(message) {
        showErrorAlert(message, 'Alerte');
    };
}

/**
 * Initialise le système d'alertes
 */
function initAlertSystem() {
    // Remplacer les alert() natives
    replaceNativeAlerts();
    
    // Remplacer les confirm() natives
    replaceNativeConfirms();
    
    // Gérer les messages Django
    const messages = document.querySelectorAll('.messages .alert');
    messages.forEach(message => {
        const text = message.textContent.trim();
        const type = message.classList.contains('alert-success') ? 'success' :
                    message.classList.contains('alert-danger') ? 'error' :
                    message.classList.contains('alert-warning') ? 'warning' : 'info';
        
        showCustomAlert(text, type);
        message.style.display = 'none'; // Masquer l'original
    });
    
    console.log('✅ Système d\'alertes stylisées initialisé');
}

// Initialiser au chargement
document.addEventListener('DOMContentLoaded', initAlertSystem);

// Exporter les fonctions globalement
window.showCustomAlert = showCustomAlert;
window.closeCustomAlert = closeCustomAlert;
window.closeAllAlerts = closeAllAlerts;
window.showSuccessAlert = showSuccessAlert;
window.showErrorAlert = showErrorAlert;
window.showWarningAlert = showWarningAlert;
window.showInfoAlert = showInfoAlert;
window.showFormAlert = showFormAlert;
window.showInlineAlert = showInlineAlert;
window.showCustomConfirm = showCustomConfirm;
