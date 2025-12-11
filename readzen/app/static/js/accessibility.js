class AccessibilityManager {
    constructor() {
        this.preferences = JSON.parse(localStorage.getItem('readzen_prefs')) || {
            theme: 'theme-light',
            font: 'default',
            syllabic: false,
            syllabicIntensity: 1
        };
        this.init();
    }

    init() {
        this.applyTheme(this.preferences.theme);
        this.applyFont(this.preferences.font);
        // Syllabic coloring is applied on specific pages where text exists
    }

    save() {
        localStorage.setItem('readzen_prefs', JSON.stringify(this.preferences));
    }

    applyTheme(theme) {
        document.body.classList.remove('theme-light', 'theme-dark', 'theme-sepia');
        document.body.classList.add(theme);
        this.preferences.theme = theme;
        this.save();
    }

    applyFont(font) {
        document.body.classList.remove('font-dyslexic', 'font-lexend');
        if (font === 'dyslexic') document.body.classList.add('font-dyslexic');
        if (font === 'lexend') document.body.classList.add('font-lexend');
        this.preferences.font = font;
        this.save();
    }

    toggleSyllabic(enabled) {
        this.preferences.syllabic = enabled;
        this.save();
        // Refresh view if applicable
        if (document.getElementById('reader-content')) {
            this.colorizeText();
        }
    }

    colorizeText() {
        const container = document.getElementById('page-content');
        if (!container) return;

        // If disabled, restore original text (requires storing original). 
        // For simplicity, we assume we reload or re-fetch text if functionality is toggled off.
        if (!this.preferences.syllabic) {
            // A full reload would be easiest for prototype to clear spans
            // But we can just reload the page or re-fetch text.
            // For now, let's assume the user reloads or we won't handle "undo" perfectly without a re-fetch.
            return;
        }

        const text = container.innerText;
        // Very naive heuristic for syllables: split by vowel-consonant patterns
        // This is purely visual and estimated for the prototype.
        const words = text.split(' ');
        const html = words.map(word => {
            return this.syllabify(word);
        }).join(' ');

        container.innerHTML = html;
    }

    syllabify(word) {
        // Heuristic: Split roughly every 2-3 chars, or use regex for CV patterns.
        // Simple alternate coloring for demo purposes:
        // Split word into chunks of 3 letters (approx syllable)
        const chunks = word.match(/.{1,3}/g) || [word];
        const colors = ['syn-red', 'syn-blue', 'syn-green'];
        return chunks.map((chunk, i) => {
            return `<span class="${colors[i % 3]}">${chunk}</span>`;
        }).join('');
    }
}

const accessibility = new AccessibilityManager();
