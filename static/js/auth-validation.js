// Validation en temps réel des formulaires d'authentification
class AuthValidator {
    constructor() {
        this.initializeValidation();
    }
    
    initializeValidation() {
        // Validation du mot de passe
        const passwordInput = document.getElementById('password');
        if (passwordInput) {
            passwordInput.addEventListener('input', (e) => this.validatePassword(e.target.value));
        }
        
        // Validation de la confirmation du mot de passe
        const confirmPasswordInput = document.getElementById('confirm-password');
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', (e) => this.validatePasswordConfirmation(e.target.value));
        }
        
        // Validation de l'email
        const emailInput = document.getElementById('email');
        if (emailInput) {
            emailInput.addEventListener('input', (e) => this.validateEmail(e.target.value));
        }
        
        // Validation du nom d'utilisateur
        const usernameInput = document.getElementById('username');
        if (usernameInput) {
            usernameInput.addEventListener('input', (e) => this.validateUsername(e.target.value));
        }
    }
    
    validatePassword(password) {
        const rules = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
            noRepeat: !/(.)\1{2,}/.test(password)
        };
        
        // Mettre à jour l'indicateur de force
        this.updatePasswordStrength(password, rules);
        
        // Mettre à jour les règles
        this.updatePasswordRules(rules);
        
        return Object.values(rules).every(rule => rule);
    }
    
    updatePasswordStrength(password, rules) {
        const strengthFill = document.getElementById('strengthFill');
        const strengthText = document.getElementById('strengthText');
        
        if (!strengthFill || !strengthText) return;
        
        const validRules = Object.values(rules).filter(rule => rule).length;
        const percentage = (validRules / Object.keys(rules).length) * 100;
        
        // Mettre à jour la barre de force
        strengthFill.style.width = `${percentage}%`;
        
        // Mettre à jour la couleur et le texte
        if (percentage < 40) {
            strengthFill.className = 'strength-fill weak';
            strengthText.textContent = 'Faible';
        } else if (percentage < 70) {
            strengthFill.className = 'strength-fill medium';
            strengthText.textContent = 'Moyen';
        } else {
            strengthFill.className = 'strength-fill strong';
            strengthText.textContent = 'Fort';
        }
    }
    
    updatePasswordRules(rules) {
        const ruleElements = {
            lengthRule: rules.length,
            uppercaseRule: rules.uppercase,
            lowercaseRule: rules.lowercase,
            numberRule: rules.number,
            specialRule: rules.special
        };
        
        Object.entries(ruleElements).forEach(([ruleId, isValid]) => {
            const ruleElement = document.getElementById(ruleId);
            if (ruleElement) {
                const icon = ruleElement.querySelector('i');
                if (isValid) {
                    icon.className = 'fas fa-check-circle valid';
                    ruleElement.classList.add('valid');
                } else {
                    icon.className = 'fas fa-circle';
                    ruleElement.classList.remove('valid');
                }
            }
        });
    }
    
    validatePasswordConfirmation(confirmPassword) {
        const password = document.getElementById('password')?.value;
        const confirmInput = document.getElementById('confirm-password');
        
        if (!confirmInput) return true;
        
        if (password === confirmPassword) {
            confirmInput.setCustomValidity('');
            confirmInput.classList.remove('error');
            return true;
        } else {
            confirmInput.setCustomValidity('Les mots de passe ne correspondent pas');
            confirmInput.classList.add('error');
            return false;
        }
    }
    
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        const emailInput = document.getElementById('email');
        
        if (!emailInput) return true;
        
        if (emailRegex.test(email)) {
            emailInput.setCustomValidity('');
            emailInput.classList.remove('error');
            return true;
        } else {
            emailInput.setCustomValidity('Veuillez entrer une adresse email valide');
            emailInput.classList.add('error');
            return false;
        }
    }
    
    validateUsername(username) {
        const usernameInput = document.getElementById('username');
        
        if (!usernameInput) return true;
        
        if (username.length >= 3 && username.length <= 30) {
            usernameInput.setCustomValidity('');
            usernameInput.classList.remove('error');
            return true;
        } else {
            usernameInput.setCustomValidity('Le nom d\'utilisateur doit contenir entre 3 et 30 caractères');
            usernameInput.classList.add('error');
            return false;
        }
    }
    
    // Validation complète du formulaire
    validateForm(formId) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        const inputs = form.querySelectorAll('input[required]');
        let isValid = true;
        
        inputs.forEach(input => {
            if (input.type === 'password' && input.id === 'password') {
                if (!this.validatePassword(input.value)) {
                    isValid = false;
                }
            } else if (input.type === 'password' && input.id === 'confirm-password') {
                if (!this.validatePasswordConfirmation(input.value)) {
                    isValid = false;
                }
            } else if (input.type === 'email') {
                if (!this.validateEmail(input.value)) {
                    isValid = false;
                }
            } else if (input.id === 'username') {
                if (!this.validateUsername(input.value)) {
                    isValid = false;
                }
            }
        });
        
        return isValid;
    }
}

// Initialiser la validation quand le DOM est chargé
document.addEventListener('DOMContentLoaded', () => {
    new AuthValidator();
});
