/**
 * Google Translate Widget - Blizz
 * Définir googleTranslateElementInit (callback appelé par l'API Google)
 * et toggleTranslateWidget (bouton d'ouverture/fermeture)
 */
function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'fr',
        includedLanguages: 'en,fr,es,ar,pt,de,it,zh-CN,ja,ko,ru',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false,
        multilanguagePage: true
    }, 'google_translate_element');

    // Détecter la langue du navigateur et afficher le widget automatiquement
    const browserLang = navigator.language || navigator.userLanguage;
    const langCode = browserLang.split('-')[0];

    setTimeout(function() {
        const translateWidget = document.getElementById('google_translate_element');
        const translateBtn = document.getElementById('translateToggleBtn');

        if (langCode !== 'fr') {
            // Afficher automatiquement si la langue n'est pas français
            if (translateWidget) {
                translateWidget.classList.add('show');
            }
            if (translateBtn) {
                translateBtn.innerHTML = '<i class="fas fa-times"></i><span>Close</span>';
            }
        }

        // Ajouter la classe notranslate aux noms de jeux
        addNotranslateToGameNames();
    }, 1000);
}

function toggleTranslateWidget() {
    const widget = document.getElementById('google_translate_element');
    const btn = document.getElementById('translateToggleBtn');

    if (widget.classList.contains('show')) {
        widget.classList.remove('show');
        btn.innerHTML = '<i class="fas fa-language"></i><span>Translate</span>';
    } else {
        widget.classList.add('show');
        btn.innerHTML = '<i class="fas fa-times"></i><span>Close</span>';
    }
}

function addNotranslateToGameNames() {
    // Liste des noms de jeux à ne pas traduire
    const gameNames = ['Free Fire', 'PUBG', 'PUBG Mobile', 'Call of Duty', 'COD', 'Mobile Legends', 'Fortnite', 'FIFA', 'eFootball', 'Clash of Clans', 'Brawl Stars', 'Valorant', 'League of Legends'];

    // Parcourir tous les éléments de texte
    const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        null,
        false
    );

    let node;
    while (node = walker.nextNode()) {
        let text = node.textContent;

        gameNames.forEach(function(gameName) {
            if (text.includes(gameName)) {
                const parent = node.parentElement;
                if (parent && !parent.classList.contains('notranslate')) {
                    parent.classList.add('notranslate');
                }
            }
        });
    }
}
