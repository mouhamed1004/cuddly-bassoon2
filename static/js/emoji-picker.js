/**
 * Sélecteur d'emojis réutilisable pour BLIZZ
 * Compatible avec tous les champs de texte et textarea
 */

class EmojiPicker {
    constructor() {
        this.emojis = {
            'smileys': {
                'name': 'Smileys & Émotions',
                'icon': '😀',
                'emojis': [
                    '😀', '😃', '😄', '😁', '😆', '😅', '🤣', '😂', '🙂', '🙃',
                    '😉', '😊', '😇', '😍', '🤩', '😘', '😗', '😚',
                    '😙', '😋', '😛', '😜', '🤪', '😝', '🤑', '🤗', '🤭',
                    '🤫', '🤔', '🤐', '🤨', '😐', '😑', '😶', '😏', '😒', '🙄',
                    '😬', '😔', '😪', '🤤', '😴', '😷', '🤒', '🤕', '🤢',
                    '🤮', '🤧', '😵', '🤯', '🤠', '😈', '👿', '💩', '🔥'
                ]
            },
            'gestures': {
                'name': 'Gestes & Corps',
                'icon': '👍',
                'emojis': [
                    '👍', '👎', '👌', '✌️', '🤞', '🤟', '🤘', '🤙',
                    '👈', '👉', '👆', '👇', '👋', '🤚', '🖐️', '✋',
                    '🖖', '👏', '🙌', '🤝', '👐', '🤜', '🤛', '✊', '👊',
                    '💪', '✍️', '🙏', '💄', '💋'
                ]
            },
            'gaming': {
                'name': 'Gaming & Guerre',
                'icon': '🎮',
                'emojis': [
                    '🎮', '🕹️', '🎯', '🎲', '🃏', '🎰', '🏆', '🥇', '🥈',
                    '🥉', '🏅', '🎖️', '⚽', '🏀', '🏈', '⚾', '🎾',
                    '🏐', '🏉', '🎱', '🏓', '🏸', '🏒', '🏑',
                    '🏏', '🥅', '⛳', '🏹', '🎣', '🥊', '🥋',
                    '💀', '☠️', '⚔️', '🗡️', '🔫', '🛡️', '⚰️', '🔥', '💥',
                    '💣', '🧨', '🔪', '🪓', '⛏️', '🔨', '🏴‍☠️', '👹', '👺'
                ]
            },
            'objects': {
                'name': 'Objets',
                'icon': '📱',
                'emojis': [
                    '📱', '💻', '⌨️', '🖥️', '🖨️', '🖱️', '💽', '💾', '💿',
                    '📀', '📼', '📷', '📸', '📹', '🎥', '📞', '☎️', '📠',
                    '📺', '📻', '⏱️', '⏰', '⏳', '⌛', '📡', '🔋', '🔌', 
                    '💡', '🔦', '🕯️'
                ]
            },
            'symbols': {
                'name': 'Symboles',
                'icon': '❤️',
                'emojis': [
                    '❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '💔',
                    '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟', '☮️',
                    '⚡', '💥', '💢', '💨', '💫', '💦', '🔥', '❄️', '💧', 
                    '🌊', '⭐', '🌟', '✨', '☄️'
                ]
            },
            'flags': {
                'name': 'Drapeaux',
                'icon': '🏳️',
                'emojis': this.generateFlagEmojis([
                    'FR', 'CI', 'SN', 'ML', 'BF', 'NE', 'TD', 'CM', 'GA', 'CG',
                    'CD', 'CF', 'DJ', 'KM', 'MG', 'MU', 'SC', 'MA', 'TN', 'DZ',
                    'EG', 'LY', 'SD', 'ET', 'ER', 'SO', 'KE', 'UG', 'RW', 'BI',
                    'TZ', 'MZ', 'ZW', 'ZA', 'BW', 'NA', 'ZM', 'AO', 'GH', 'NG',
                    'BJ', 'TG', 'LR', 'SL', 'GN', 'GW', 'CV', 'GM', 'US', 'GB',
                    'DE', 'ES', 'IT', 'NL', 'BE', 'CH', 'AT', 'PT', 'SE', 'NO',
                    'DK', 'FI', 'PL', 'CZ', 'HU', 'RO', 'BG', 'GR', 'TR', 'RU',
                    'CA', 'MX', 'BR', 'AR', 'CL', 'CO', 'PE', 'VE', 'EC', 'UY',
                    'JP', 'KR', 'CN', 'IN', 'TH', 'VN', 'PH', 'ID', 'MY', 'SG',
                    'AU', 'NZ', 'IL', 'SA', 'AE', 'IR', 'IQ', 'JO'
                ])
            }
        };
        
        this.currentInput = null;
        this.picker = null;
        this.isVisible = false;
        this.currentTrigger = null;
        this.recentEmojis = JSON.parse(localStorage.getItem('blizz_recent_emojis') || '[]');
        this.createPicker();
    }

    // Fonction pour générer les emojis drapeaux à partir des codes pays
    generateFlagEmojis(countryCodes) {
        return countryCodes.map(code => {
            const codePoints = code
                .toUpperCase()
                .split('')
                .map(char => 127397 + char.charCodeAt(0));
            return String.fromCodePoint(...codePoints);
        });
    }

    // Fonction pour détecter si un emoji est un drapeau
    isFlagEmoji(emoji) {
        // Les drapeaux sont composés de deux caractères Unicode dans la plage 127462-127487
        if (emoji.length < 2) return false;
        const codePoint1 = emoji.codePointAt(0);
        const codePoint2 = emoji.codePointAt(2);
        return codePoint1 >= 127462 && codePoint1 <= 127487 && 
               codePoint2 >= 127462 && codePoint2 <= 127487;
    }

    createPicker() {
        // Créer le conteneur principal
        this.picker = document.createElement('div');
        this.picker.className = 'emoji-picker';
        
        // Forcer la forme rectangulaire avec style inline
        this.picker.style.cssText = `
            position: absolute;
            width: 320px;
            height: 350px;
            background: #1a1a2e;
            border: 2px solid #6c5ce7;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
            z-index: 10000;
            display: none;
            flex-direction: column;
            backdrop-filter: blur(10px);
            overflow: hidden;
        `;
        
        this.picker.innerHTML = `
            <div class="emoji-picker-header">
                <div class="emoji-categories">
                    <button class="category-btn active" data-category="recent" title="Récemment utilisés">
                        🕒
                    </button>
                    ${Object.keys(this.emojis).map(key => 
                        `<button class="category-btn" data-category="${key}" title="${this.emojis[key].name}">
                            ${this.emojis[key].icon}
                        </button>`
                    ).join('')}
                </div>
            </div>
            <div class="emoji-picker-content">
                <div class="emoji-grid"></div>
            </div>
        `;

        // Ajouter les styles
        this.addStyles();
        
        // Ajouter au body temporairement (sera déplacé lors de l'affichage)
        document.body.appendChild(this.picker);
        
        // Ajouter les événements
        this.addEventListeners();
        
        // Afficher les emojis récents par défaut
        this.showRecentEmojis();
    }

    addStyles() {
        // Supprimer les anciens styles s'ils existent
        const existingStyles = document.getElementById('emoji-picker-styles');
        if (existingStyles) {
            existingStyles.remove();
        }
        
        const styles = document.createElement('style');
        styles.id = 'emoji-picker-styles';
        styles.textContent = `
            .emoji-picker {
                position: absolute;
                width: 320px !important;
                height: 350px !important;
                background: var(--dark-blue, #1a1a2e);
                border: 2px solid var(--primary-color, #6c5ce7);
                border-radius: 12px !important;
                border-top-left-radius: 12px !important;
                border-top-right-radius: 12px !important;
                border-bottom-left-radius: 12px !important;
                border-bottom-right-radius: 12px !important;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
                z-index: 10000;
                display: none;
                flex-direction: column;
                backdrop-filter: blur(10px);
                overflow: hidden;
            }

            .emoji-picker.show {
                display: flex;
            }

            .emoji-picker-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px;
                border-bottom: 1px solid rgba(108, 92, 231, 0.3);
                background: rgba(255, 255, 255, 0.05);
            }

            .emoji-categories {
                display: flex;
                gap: 5px;
            }

            .category-btn {
                background: none;
                border: none;
                font-size: 16px;
                padding: 8px;
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.2s ease;
                color: rgba(255, 255, 255, 0.7);
                width: 35px;
                height: 35px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .category-btn:hover,
            .category-btn.active {
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.1);
            }



            .emoji-picker-content {
                flex: 1;
                overflow-y: auto;
                overflow-x: hidden;
                padding: 10px 15px 10px 10px;
            }

            .emoji-picker-content::-webkit-scrollbar {
                width: 8px;
            }

            .emoji-picker-content::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }

            .emoji-picker-content::-webkit-scrollbar-thumb {
                background: var(--primary-color, #6c5ce7);
                border-radius: 4px;
                transition: background 0.2s ease;
            }

            .emoji-picker-content::-webkit-scrollbar-thumb:hover {
                background: rgba(108, 92, 231, 0.8);
            }

            .emoji-grid {
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 6px;
                width: calc(100% - 8px);
                padding-right: 5px;
            }

            .emoji-btn {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                font-size: 18px;
                padding: 6px;
                border-radius: 50%;
                cursor: pointer;
                transition: all 0.2s ease;
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-family: "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", "Twemoji", "EmojiOne Mozilla", sans-serif !important;
                font-variant-emoji: emoji !important;
                font-feature-settings: normal;
                text-rendering: optimizeQuality;
                -webkit-font-smoothing: antialiased;
                -moz-osx-font-smoothing: grayscale;
            }
            
            .emoji-btn.flag-emoji {
                font-size: 16px;
                font-family: "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", "Twemoji", sans-serif !important;
            }

            .emoji-btn:hover {
                background: rgba(108, 92, 231, 0.3);
                transform: scale(1.2);
            }

            .emoji-trigger {
                background: linear-gradient(45deg, var(--primary-color, #6c5ce7), var(--secondary-color, #a29bfe));
                border: none;
                color: white;
                width: 35px;
                height: 35px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                box-shadow: 0 2px 10px rgba(108, 92, 231, 0.3);
            }

            .emoji-trigger:hover {
                transform: scale(1.1);
                box-shadow: 0 4px 15px rgba(108, 92, 231, 0.5);
            }

            @media (max-width: 768px) {
                .emoji-picker {
                    width: 280px;
                    height: 350px;
                    bottom: 60px;
                    right: 10px;
                }
                
                .emoji-grid {
                    grid-template-columns: repeat(6, 1fr);
                }
            }
        `;
        document.head.appendChild(styles);
    }

    addEventListeners() {
        // Navigation par catégories
        this.picker.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.target.dataset.category;
                
                if (category === 'recent') {
                    this.showRecentEmojis();
                } else {
                    this.showCategory(category);
                }
                
                // Mettre à jour l'état actif
                this.picker.querySelectorAll('.category-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });

        // Fermer en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (this.isVisible && !this.picker.contains(e.target) && !e.target.classList.contains('emoji-trigger')) {
                this.hide();
            }
        });
    }

    showCategory(categoryKey) {
        const category = this.emojis[categoryKey];
        const grid = this.picker.querySelector('.emoji-grid');
        
        grid.innerHTML = category.emojis.map(emoji => 
            `<button class="emoji-btn" data-emoji="${emoji}">${emoji}</button>`
        ).join('');

        // Ajouter les événements de clic sur les emojis
        grid.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.insertEmoji(e.target.dataset.emoji);
            });
        });
    }

    showRecentEmojis() {
        const grid = this.picker.querySelector('.emoji-grid');
        
        if (this.recentEmojis.length === 0) {
            grid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: rgba(255,255,255,0.5); padding: 20px;">Aucun emoji récent</div>';
            return;
        }

        grid.innerHTML = this.recentEmojis.map(emoji => 
            `<button class="emoji-btn" data-emoji="${emoji}">${emoji}</button>`
        ).join('');

        // Ajouter les événements de clic sur les emojis
        grid.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.insertEmoji(e.target.dataset.emoji);
            });
        });
    }

    searchEmojis(query) {
        if (!query.trim()) {
            this.showCategory('smileys');
            return;
        }

        const allEmojis = [];
        Object.values(this.emojis).forEach(category => {
            allEmojis.push(...category.emojis);
        });

        // Recherche simple par correspondance (on pourrait améliorer avec des mots-clés)
        const filteredEmojis = allEmojis.filter(emoji => 
            emoji.includes(query) || this.getEmojiKeywords(emoji).some(keyword => 
                keyword.toLowerCase().includes(query.toLowerCase())
            )
        );

        const grid = this.picker.querySelector('.emoji-grid');
        grid.innerHTML = filteredEmojis.map(emoji => 
            `<button class="emoji-btn" data-emoji="${emoji}">${emoji}</button>`
        ).join('');

        // Ajouter les événements
        grid.querySelectorAll('.emoji-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.insertEmoji(e.target.dataset.emoji);
            });
        });
    }

    getEmojiKeywords(emoji) {
        // Mots-clés simples pour la recherche
        const keywords = {
            '😀': ['sourire', 'heureux', 'content'],
            '😂': ['rire', 'mdr', 'drole'],
            '❤️': ['coeur', 'amour', 'rouge'],
            '👍': ['pouce', 'bien', 'ok'],
            '🎮': ['jeu', 'gaming', 'manette'],
            '🔥': ['feu', 'chaud', 'top'],
            '💪': ['muscle', 'force', 'fort'],
            '🏆': ['trophee', 'victoire', 'gagne']
        };
        return keywords[emoji] || [];
    }

    insertEmoji(emoji) {
        if (!this.currentInput) return;

        const start = this.currentInput.selectionStart;
        const end = this.currentInput.selectionEnd;
        const text = this.currentInput.value;
        
        this.currentInput.value = text.substring(0, start) + emoji + text.substring(end);
        this.currentInput.selectionStart = this.currentInput.selectionEnd = start + emoji.length;
        
        // Ajouter aux emojis récents
        this.addToRecent(emoji);
        
        // Déclencher l'événement input pour les frameworks qui l'écoutent
        this.currentInput.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Remettre le focus sur l'input
        this.currentInput.focus();
        
        // NE PAS fermer le picker pour permettre plusieurs emojis
        // this.hide();
    }

    addToRecent(emoji) {
        // Supprimer l'emoji s'il existe déjà
        this.recentEmojis = this.recentEmojis.filter(e => e !== emoji);
        
        // Ajouter en première position
        this.recentEmojis.unshift(emoji);
        
        // Garder seulement les 5 derniers
        this.recentEmojis = this.recentEmojis.slice(0, 5);
        
        // Sauvegarder dans localStorage
        localStorage.setItem('blizz_recent_emojis', JSON.stringify(this.recentEmojis));
    }

    show(inputElement, triggerElement = null) {
        this.currentInput = inputElement;
        this.currentTrigger = triggerElement;
        
        // Forcer le style rectangulaire avant affichage
        this.picker.style.borderRadius = '12px';
        this.picker.style.width = '320px';
        this.picker.style.height = '350px';
        
        this.picker.style.display = 'flex';
        this.isVisible = true;
        
        // Positionner près du bouton trigger
        if (triggerElement) {
            this.positionNearTrigger(triggerElement);
        } else {
            this.positionNearInput(inputElement);
        }
    }

    hide() {
        this.picker.style.display = 'none';
        this.isVisible = false;
        this.currentInput = null;
        this.currentTrigger = null;
    }

    positionNearInput(inputElement) {
        const rect = inputElement.getBoundingClientRect();
        
        // Position par défaut : en bas à droite de l'input
        let top = rect.bottom + 10;
        let left = rect.right - 320; // largeur du picker
        
        // Ajustements si le picker sort de l'écran
        if (left < 10) left = 10;
        if (top + 350 > window.innerHeight) {
            top = rect.top - 360; // au-dessus de l'input
        }
        
        this.picker.style.top = `${top}px`;
        this.picker.style.left = `${left}px`;
    }

    positionNearTrigger(triggerElement) {
        // Utiliser position absolue par rapport à la fenêtre
        const triggerRect = triggerElement.getBoundingClientRect();
        
        // Positionner AU-DESSUS du bouton
        let top = triggerRect.top - 360; // 350px de hauteur + 10px de marge
        let left = triggerRect.left;
        
        // Ajustements pour éviter le débordement
        if (left + 320 > window.innerWidth) {
            left = triggerRect.right - 320;
        }
        if (left < 10) left = 10;
        
        // Si pas assez de place en haut, positionner en haut de la fenêtre
        if (top < 10) {
            top = 10;
        }
        
        // Position absolue par rapport à la fenêtre
        this.picker.style.position = 'fixed';
        this.picker.style.top = `${top}px`;
        this.picker.style.left = `${left}px`;
        this.picker.style.zIndex = '10000';
        
        // Attacher au body pour éviter les problèmes de conteneur
        if (this.picker.parentNode !== document.body) {
            document.body.appendChild(this.picker);
        }
    }

    // Méthode statique pour initialiser le picker global
    static init() {
        if (window.emojiPickerInstance) {
            return window.emojiPickerInstance;
        }
        window.emojiPickerInstance = new EmojiPicker();
        return window.emojiPickerInstance;
    }

    // Méthode pour ajouter le bouton emoji à un input
    static addToInput(inputElement, position = 'after') {
        const picker = EmojiPicker.init();
        
        // Créer un bouton emoji avec styles appropriés
        const emojiBtn = document.createElement('button');
        emojiBtn.className = 'emoji-btn';
        emojiBtn.innerHTML = '😀'; // Utiliser innerHTML au lieu de textContent pour les emojis Unicode
        emojiBtn.style.cssText = `
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s ease;
        `;
        
        // Ajouter l'événement de clic
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            if (picker.isVisible) {
                picker.hide();
            } else {
                picker.show(inputElement, trigger);
            }
        });

        // Positionner le bouton selon la position demandée
        if (position === 'before') {
            inputElement.parentNode.insertBefore(trigger, inputElement);
        } else if (position === 'inside') {
            // Pour les inputs avec position relative et le bouton en absolute
            inputElement.style.paddingRight = '45px';
            trigger.style.position = 'absolute';
            trigger.style.right = '8px';
            trigger.style.top = '50%';
            trigger.style.transform = 'translateY(-50%)';
            trigger.style.zIndex = '1000';
            
            const wrapper = inputElement.parentNode;
            if (wrapper.style.position !== 'relative') {
                wrapper.style.position = 'relative';
            }
            wrapper.appendChild(trigger);
        } else {
            // Position 'after' par défaut
            inputElement.parentNode.insertBefore(trigger, inputElement.nextSibling);
        }
        
        return trigger;
    }
}

// Auto-initialisation
document.addEventListener('DOMContentLoaded', () => {
    EmojiPicker.init();
});

// Export pour utilisation modulaire
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EmojiPicker;
}
