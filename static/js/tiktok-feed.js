/**
 * TikTok-like Feed System pour les Highlights
 * Gestion du chargement à la demande et de la navigation directe
 */

class TikTokFeed {
    constructor() {
        this.highlights = [];
        this.currentIndex = 0;
        this.loading = false;
        this.hasMore = true;
        this.feedType = 'for_you';
        this.container = document.getElementById('highlightsViewer');
        this.loadMode = 'initial';
        this.targetHighlightId = null;
        this.cache = new Map(); // Cache pour les highlights
        this.maxCacheSize = 20;
        
        this.init();
    }

    init() {
        // Récupérer les paramètres depuis le template
        this.feedType = window.feedType || 'for_you';
        this.loadMode = window.loadMode || 'initial';
        this.targetHighlightId = window.targetHighlightId;
        
        // Initialiser selon le mode
        if (this.loadMode === 'direct' && this.targetHighlightId) {
            this.loadDirectHighlight(this.targetHighlightId);
        } else {
            this.loadInitialHighlights();
        }
        
        this.setupEventListeners();
        this.setupIntersectionObserver();
        
        // Gestion périodique du cache intelligent
        setInterval(() => {
            this.manageIntelligentCache();
        }, 30000); // Toutes les 30 secondes
        
        // Optimisation de la qualité vidéo au démarrage
        this.optimizeVideoQuality();
    }

    setupEventListeners() {
        // Navigation par clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                this.previousHighlight();
            } else if (e.key === 'ArrowDown') {
                e.preventDefault();
                this.nextHighlight();
            }
        });

        // Navigation tactile
        this.setupSwipeNavigation();
        
        // Navigation par les flèches
        const prevArrow = document.querySelector('.prev-arrow');
        const nextArrow = document.querySelector('.next-arrow');
        
        if (prevArrow) {
            prevArrow.addEventListener('click', () => this.previousHighlight());
        }
        if (nextArrow) {
            nextArrow.addEventListener('click', () => this.nextHighlight());
        }
    }

    setupSwipeNavigation() {
        let startY = 0;
        let endY = 0;
        let isScrolling = false;
        
        this.container.addEventListener('touchstart', (e) => {
            if (isScrolling || this.loading) return;
            startY = e.touches[0].clientY;
        });
        
        this.container.addEventListener('touchend', (e) => {
            if (isScrolling || this.loading) return;
            endY = e.changedTouches[0].clientY;
            const diffY = startY - endY;
            
            if (Math.abs(diffY) > 100) {
                isScrolling = true;
                
                if (diffY > 0) {
                    // Swipe vers le haut - vidéo suivante
                    this.nextHighlight();
                } else {
                    // Swipe vers le bas - vidéo précédente
                    this.previousHighlight();
                }
                
                setTimeout(() => {
                    isScrolling = false;
                }, 500);
            }
        });
    }

    setupIntersectionObserver() {
        // Observer pour détecter quand charger plus de contenu
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const highlightCard = entry.target;
                    const index = parseInt(highlightCard.dataset.index);
                    
                    // Mettre à jour l'index actuel
                    this.currentIndex = index;
                    
                    // Si on approche de la fin, charger plus
                    if (index >= this.highlights.length - 2 && this.hasMore && !this.loading) {
                        this.loadMoreHighlights();
                    }
                    
                    // Jouer la vidéo visible
                    this.playVisibleVideo(highlightCard);
                    
                    // Précharger les vidéos adjacentes
                    this.preloadAdjacentVideos(index);
                    
                    // Nettoyer les vidéos éloignées
                    this.cleanupDistantVideos(index);
                }
            });
        }, {
            threshold: 0.5
        });

        // Observer les cartes existantes
        this.observeExistingCards(observer);
    }

    observeExistingCards(observer) {
        const cards = this.container.querySelectorAll('.highlight-card');
        cards.forEach(card => observer.observe(card));
    }

    async loadDirectHighlight(highlightId) {
        try {
            this.loading = true;
            console.log('Loading direct highlight:', highlightId);
            
            const response = await fetch(`/api/highlights/${highlightId}/context/?type=${this.feedType}`);
            const data = await response.json();
            
            if (data.success) {
                this.highlights = data.highlights;
                this.currentIndex = data.target_index;
                this.clearContainer();
                this.renderHighlights(this.highlights);
                this.scrollToIndex(this.currentIndex, true);
                
                // Mettre à jour l'URL
                this.updateURL();
            } else {
                console.error('Erreur lors du chargement direct:', data.error);
                this.showError('Impossible de charger ce highlight');
            }
        } catch (error) {
            console.error('Erreur réseau:', error);
            this.showError('Erreur de connexion');
        } finally {
            this.loading = false;
        }
    }

    async loadInitialHighlights() {
        try {
            this.loading = true;
            
            // Charger depuis le template si des highlights sont déjà présents
            const existingCards = this.container.querySelectorAll('.highlight-card');
            if (existingCards.length > 0) {
                // Convertir les highlights existants en format API
                this.highlights = this.parseExistingHighlights(existingCards);
                this.hasMore = true; // Supposer qu'il y en a plus
            } else {
                // Charger via API
                const response = await fetch(`/api/highlights/feed/?limit=3&offset=0&type=${this.feedType}`);
                const data = await response.json();
                
                if (data.success) {
                    this.highlights = data.highlights;
                    this.hasMore = data.has_more;
                    this.clearContainer();
                    this.renderHighlights(this.highlights);
                }
            }
            
            if (this.highlights.length > 0) {
                this.scrollToIndex(0, true);
            }
            
        } catch (error) {
            console.error('Erreur chargement initial:', error);
            this.showError('Erreur lors du chargement');
        } finally {
            this.loading = false;
        }
    }

    async loadMoreHighlights() {
        if (this.loading || !this.hasMore) return;
        
        try {
            this.loading = true;
            const offset = this.highlights.length;
            
            const response = await fetch(`/api/highlights/feed/?limit=5&offset=${offset}&type=${this.feedType}`);
            const data = await response.json();
            
            if (data.success && data.highlights.length > 0) {
                const newHighlights = data.highlights;
                this.highlights.push(...newHighlights);
                this.hasMore = data.has_more;
                
                // Render nouveaux highlights
                this.renderHighlights(newHighlights, true);
                
                // Re-setup intersection observer pour les nouveaux éléments
                const observer = new IntersectionObserver(this.setupIntersectionObserver);
                this.observeExistingCards(observer);
            } else {
                this.hasMore = false;
            }
        } catch (error) {
            console.error('Erreur chargement plus:', error);
        } finally {
            this.loading = false;
        }
    }

    parseExistingHighlights(cards) {
        const highlights = [];
        cards.forEach((card, index) => {
            const video = card.querySelector('video');
            const author = card.querySelector('.username')?.textContent.replace('@', '');
            const caption = card.querySelector('.caption')?.textContent;
            
            highlights.push({
                id: card.dataset.highlightId,
                video_url: video?.src || video?.dataset.originalSrc,
                caption: caption || '',
                author: {
                    username: author || 'Unknown'
                },
                // Autres données peuvent être extraites si nécessaire
            });
        });
        return highlights;
    }

    renderHighlights(highlights, append = false) {
        if (!append) {
            this.clearContainer();
        }
        
        const startIndex = append ? this.highlights.length - highlights.length : 0;
        
        highlights.forEach((highlight, index) => {
            const actualIndex = startIndex + index;
            const card = this.createHighlightCard(highlight, actualIndex);
            this.container.appendChild(card);
        });
    }

    createHighlightCard(highlight, index) {
        const card = document.createElement('div');
        card.className = 'highlight-card';
        card.dataset.highlightId = highlight.id;
        card.dataset.index = index;
        card.id = `highlight-${highlight.id}`;
        
        const appreciationButtons = this.createAppreciationButtons(highlight);
        
        card.innerHTML = `
            <div class="video-container">
                <video 
                    class="highlight-video" 
                    preload="metadata" 
                    loop 
                    playsinline
                    muted
                    data-highlight-id="${highlight.id}"
                    data-original-src="${highlight.video_url}"
                    poster=""
                >
                    <source src="${highlight.video_url}" type="video/mp4">
                </video>
                
                <div class="actions-overlay">
                    <div class="compact-actions">
                        <div class="user-profile">
                            <div class="profile-pic" onclick="viewProfile('${highlight.author.username}')">
                                <img src="${highlight.author.avatar || '/static/images/default.png'}" alt="Profile">
                            </div>
                            <button class="follow-btn" onclick="toggleFollow('${highlight.author.id}')">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>

                        ${appreciationButtons}

                        <div class="action-buttons">
                            <div class="dropdown-menu">
                                <button class="dropdown-btn" onclick="toggleDropdown('${highlight.id}')">
                                    <i class="fas fa-ellipsis-h"></i>
                                </button>
                                <div class="dropdown-content" id="dropdown-${highlight.id}">
                                    <button class="dropdown-item" onclick="shareHighlight('${highlight.id}')">
                                        <i class="fas fa-share"></i> Partager
                                    </button>
                                    <button class="dropdown-item" onclick="downloadHighlight('${highlight.id}')">
                                        <i class="fas fa-download"></i> Télécharger
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="video-info-overlay">
                    <div class="user-info">
                        <span class="username">@${highlight.author.username}</span>
                        <div class="caption-container">
                            <p class="caption">${highlight.caption || "Aucun titre"}</p>
                        </div>
                        ${this.createHashtagsDisplay(highlight.hashtags)}
                    </div>
                </div>

                <div class="progress-bar">
                    <div class="progress-fill"></div>
                </div>
            </div>
        `;
        
        // Setup video events
        const video = card.querySelector('video');
        this.setupVideoEvents(video);
        
        return card;
    }

    createAppreciationButtons(highlight) {
        if (!window.userAuthenticated) return '';
        
        const appreciationLevels = [
            { level: 6, emoji: '🤩', label: 'Extraordinaire' },
            { level: 5, emoji: '😲', label: 'Très bien' },
            { level: 4, emoji: '😮', label: 'Bien' },
            { level: 3, emoji: '🙂', label: 'Moyen' },
            { level: 2, emoji: '🤢', label: 'Pas terrible' },
            { level: 1, emoji: '🤮', label: 'Extrêmement nul' }
        ];
        
        let buttons = '<div class="appreciation-container" data-highlight-id="' + highlight.id + '"><div class="appreciation-buttons">';
        
        appreciationLevels.forEach(level => {
            const count = highlight.appreciation_counts?.[level.level] || 0;
            const selected = highlight.user_appreciation?.appreciation_level === level.level ? 'selected' : '';
            
            buttons += `
                <button class="appreciation-button ${selected}" data-level="${level.level}" data-highlight-id="${highlight.id}">
                    <span class="appreciation-emoji">${level.emoji}</span>
                    <div class="appreciation-count">${count}</div>
                    <div class="appreciation-tooltip">${level.label}</div>
                </button>
            `;
        });
        
        buttons += '</div></div>';
        return buttons;
    }

    createHashtagsDisplay(hashtags) {
        if (!hashtags || hashtags.length === 0) return '';
        
        let html = '<div class="hashtags-display">';
        hashtags.slice(0, 5).forEach(hashtag => {
            html += `<span class="hashtag-tag" onclick="searchHashtag('${hashtag}')">#${hashtag}</span>`;
        });
        
        if (hashtags.length > 5) {
            html += `<span class="hashtag-more">+${hashtags.length - 5} autres</span>`;
        }
        
        html += '</div>';
        return html;
    }

    setupVideoEvents(video) {
        const progressFill = video.closest('.video-container').querySelector('.progress-fill');
        
        video.addEventListener('timeupdate', () => {
            if (video.duration) {
                const progress = (video.currentTime / video.duration) * 100;
                progressFill.style.width = progress + '%';
            }
        });
        
        video.addEventListener('ended', () => {
            // Auto-play next video
            setTimeout(() => {
                this.nextHighlight();
            }, 1000);
        });
        
        // Lazy load video source
        video.addEventListener('loadstart', () => {
            if (!video.src && video.dataset.originalSrc) {
                video.src = video.dataset.originalSrc;
                video.load();
            }
        });
    }

    nextHighlight() {
        if (this.currentIndex < this.highlights.length - 1) {
            this.currentIndex++;
            this.scrollToIndex(this.currentIndex);
        } else if (this.hasMore && !this.loading) {
            // Charger plus et passer au suivant
            this.loadMoreHighlights().then(() => {
                if (this.currentIndex < this.highlights.length - 1) {
                    this.currentIndex++;
                    this.scrollToIndex(this.currentIndex);
                }
            });
        }
    }

    previousHighlight() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.scrollToIndex(this.currentIndex);
        }
    }

    scrollToIndex(index, instant = false) {
        const targetCard = this.container.querySelector(`[data-index="${index}"]`);
        if (!targetCard) return;
        
        // Arrêter les autres vidéos
        this.pauseAllVideos();
        
        // Scroll vers la carte cible
        targetCard.scrollIntoView({ 
            behavior: instant ? 'auto' : 'smooth',
            block: 'start'
        });
        
        // Jouer la vidéo après un délai
        setTimeout(() => {
            this.playVisibleVideo(targetCard);
            this.updateURL();
        }, instant ? 100 : 500);
    }

    playVisibleVideo(card) {
        const video = card.querySelector('video');
        if (video) {
            // Ensure video source is loaded
            if (!video.src && video.dataset.originalSrc) {
                video.src = video.dataset.originalSrc;
                video.load();
            }
            
            if (video.paused && video.readyState >= 2) {
                video.play().catch(e => console.log('Autoplay prevented:', e));
            }
        }
    }

    pauseAllVideos() {
        const videos = this.container.querySelectorAll('video');
        videos.forEach(video => {
            if (!video.paused) {
                video.pause();
            }
        });
    }

    updateURL() {
        if (this.highlights[this.currentIndex]) {
            const highlightId = this.highlights[this.currentIndex].id;
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('highlight', highlightId);
            window.history.replaceState({}, '', newUrl);
        }
    }

    clearContainer() {
        this.container.innerHTML = '';
    }

    showError(message) {
        if (window.showCustomAlert) {
            window.showCustomAlert('Erreur', message, 'error');
        } else {
            alert(message);
        }
    }

    // Cache management
    addToCache(highlightId, data) {
        if (this.cache.size >= this.maxCacheSize) {
            const firstKey = this.cache.keys().next().value;
            this.cache.delete(firstKey);
        }
        this.cache.set(highlightId, data);
    }

    getFromCache(highlightId) {
        return this.cache.get(highlightId);
    }

    // Préchargement intelligent des vidéos adjacentes
    preloadAdjacentVideos(currentIndex) {
        const preloadRange = 2; // Précharger 2 vidéos avant et après
        
        for (let i = Math.max(0, currentIndex - preloadRange); 
             i <= Math.min(this.highlights.length - 1, currentIndex + preloadRange); 
             i++) {
            
            if (i === currentIndex) continue; // Skip current video
            
            const card = this.container.querySelector(`[data-index="${i}"]`);
            if (!card) continue;
            
            const video = card.querySelector('video');
            if (!video) continue;
            
            // S'assurer que la vidéo a une source
            if (!video.src && video.dataset.originalSrc) {
                video.src = video.dataset.originalSrc;
            }
            
            // Précharger les métadonnées seulement
            if (video.readyState < 1 && video.src) {
                video.preload = 'metadata';
                video.load();
            }
        }
    }

    // Nettoyage des vidéos éloignées pour économiser la mémoire
    cleanupDistantVideos(currentIndex) {
        const cleanupRange = 5; // Nettoyer les vidéos à plus de 5 positions
        
        const cards = this.container.querySelectorAll('.highlight-card');
        cards.forEach((card, cardIndex) => {
            const index = parseInt(card.dataset.index);
            
            if (Math.abs(index - currentIndex) > cleanupRange) {
                const video = card.querySelector('video');
                if (video && !video.paused) {
                    video.pause();
                    video.currentTime = 0;
                }
                
                // Optionnellement, on peut aussi supprimer la source pour économiser la mémoire
                // Mais cela ralentira le rechargement si l'utilisateur revient
                // if (video && video.src) {
                //     video.removeAttribute('src');
                //     video.load();
                // }
            }
        });
    }

    // Méthode pour précharger une vidéo spécifique
    preloadVideo(video) {
        if (!video || video.readyState >= 1) return;
        
        // Définir la source si elle n'est pas définie
        if (!video.src && video.dataset.originalSrc) {
            video.src = video.dataset.originalSrc;
        }
        
        // Précharger les métadonnées
        video.preload = 'metadata';
        
        // Charger les métadonnées en arrière-plan
        if (video.src && video.readyState < 1) {
            video.load();
        }
    }

    // Méthode pour optimiser la qualité vidéo selon la bande passante
    optimizeVideoQuality() {
        // Simple détection de la qualité de connexion
        if ('connection' in navigator) {
            const connection = navigator.connection;
            const effectiveType = connection.effectiveType;
            
            // Ajuster la qualité selon la connexion
            let quality = 'auto';
            switch (effectiveType) {
                case 'slow-2g':
                case '2g':
                    quality = 'low';
                    break;
                case '3g':
                    quality = 'medium';
                    break;
                case '4g':
                    quality = 'high';
                    break;
            }
            
            // Appliquer la qualité (cette logique dépendrait du serveur)
            console.log('Qualité vidéo optimisée:', quality);
        }
    }

    // Méthode pour gérer la mise en cache intelligente
    manageIntelligentCache() {
        // Prioriser les vidéos récemment vues et celles à proximité
        const priorityVideos = [];
        const currentIndex = this.currentIndex;
        
        // Ajouter les vidéos proches à la priorité
        for (let i = Math.max(0, currentIndex - 3); 
             i <= Math.min(this.highlights.length - 1, currentIndex + 3); 
             i++) {
            if (this.highlights[i]) {
                priorityVideos.push(this.highlights[i].id);
            }
        }
        
        // Nettoyer le cache des vidéos non prioritaires
        for (const [videoId, data] of this.cache.entries()) {
            if (!priorityVideos.includes(videoId)) {
                this.cache.delete(videoId);
            }
        }
    }
}

// Initialiser le feed quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    window.tiktokFeed = new TikTokFeed();
});

// Fonction globale pour la compatibilité avec les fonctions existantes
function nextHighlight() {
    if (window.tiktokFeed) {
        window.tiktokFeed.nextHighlight();
    }
}

function previousHighlight() {
    if (window.tiktokFeed) {
        window.tiktokFeed.previousHighlight();
    }
}
