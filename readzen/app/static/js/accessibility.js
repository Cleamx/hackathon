class AccessibilityManager {
    constructor() {
        // Default Preferences
        const defaults = {
            theme: 'theme-light',
            font: 'default',
            // Syllables
            syllabic: false,
            syllAlternation: false,
            syllUnderline: false,
            // Phonemes
            phonemesEnabled: false,
            activePhonemes: {}, // { 'an': '#ff0000', ... }
            // Silent Letters
            silentLetters: false,
            // Semantic
            semanticProper: false,
            semanticDate: false,
            semanticConcept: false
        };

        this.preferences = { ...defaults, ...JSON.parse(localStorage.getItem('readzen_prefs') || '{}') };

        // Define common phonemes
        this.phonemeList = ['an', 'on', 'in', 'ou', 'oi', 'eu', 'ai', 'ui', 'gn', 'ill', 'eau', 'au', 'en'];
        // Default colors if not set
        this.defaultColors = ['#E57373', '#64B5F6', '#81C784', '#FFD54F', '#BA68C8', '#4DB6AC', '#FF8A65', '#A1887F', '#90A4AE', '#9575CD', '#4DD0E1', '#AED581', '#FFB74D'];

        // Profile Presets
        this.profiles = {
            'dyslexie': {
                font: 'dyslexic',
                theme: 'theme-light',
                syllabic: true,
                syllAlternation: true,
                syllUnderline: false,
                phonemesEnabled: true,
                silentLetters: true
            },
            'malvoyance': {
                font: 'lexend',
                theme: 'theme-dark',
                syllabic: false,
                phonemesEnabled: false,
                silentLetters: false,
            },
            'tda': {
                font: 'lexend',
                theme: 'theme-sepia',
                syllabic: true,
                syllAlternation: false,
                syllUnderline: true,
                phonemesEnabled: false,
                silentLetters: false
            },
            'fatigue': {
                font: 'lexend',
                theme: 'theme-sepia',
                syllabic: false,
                phonemesEnabled: false,
                silentLetters: false
            },
            'lecture-rapide': {
                font: 'default',
                theme: 'theme-light',
                syllabic: false,
                phonemesEnabled: false,
                silentLetters: false
            }
        };

        this.init();
    }

    setProfile(profileId) {
        const profile = this.profiles[profileId];
        if (!profile) return;

        // Apply settings from profile
        if (profile.font) this.applyFont(profile.font);
        if (profile.theme) this.applyTheme(profile.theme);

        // Update boolean toggles
        this.preferences.syllabic = profile.syllabic ?? false;
        this.preferences.syllAlternation = profile.syllAlternation ?? false;
        this.preferences.syllUnderline = profile.syllUnderline ?? false;
        this.preferences.phonemesEnabled = profile.phonemesEnabled ?? false;
        this.preferences.silentLetters = profile.silentLetters ?? false;

        // Save and Refresh
        this.save();

        // If we are on the settings page, we might need to refresh the UI toggles.
        // The simplest way is to reload the page or dispatch an event, 
        // but since we are modifying the data underlying the UI, a reload is safest for this prototype.
        if (window.location.pathname.includes('accessibility')) {
            window.location.reload();
        } else {
            this.refreshView();
        }
    }

    init() {
        this.applyTheme(this.preferences.theme);
        this.applyFont(this.preferences.font);
    }

    save() {
        localStorage.setItem('readzen_prefs', JSON.stringify(this.preferences));
    }

    // --- UI Helpers ---

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

    renderPhonemeList(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;
        container.innerHTML = '';

        this.phonemeList.forEach((pho, index) => {
            const isActive = this.preferences.activePhonemes[pho] !== undefined;
            const color = this.preferences.activePhonemes[pho] || this.defaultColors[index % this.defaultColors.length];

            const div = document.createElement('div');
            div.className = 'phoneme-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = isActive;
            checkbox.onchange = (e) => this.togglePhonemeItem(pho, e.target.checked, color);

            const label = document.createElement('span');
            label.innerText = pho;

            const colorInput = document.createElement('input');
            colorInput.type = 'color';
            colorInput.className = 'phoneme-color';
            colorInput.value = color;
            // If checked, updating color updates the text immediately
            colorInput.onchange = (e) => {
                if (checkbox.checked) {
                    this.togglePhonemeItem(pho, true, e.target.value);
                }
            };

            div.appendChild(checkbox);
            div.appendChild(label);
            div.appendChild(colorInput);
            container.appendChild(div);
        });
    }

    // --- Toggles ---

    toggleSyllabic(enabled) {
        this.preferences.syllabic = enabled;
        // Reset sub-options if disabled? No, keep them as user pref.
        const opts = document.getElementById('syllable-options');
        if (opts) opts.style.display = enabled ? 'block' : 'none';

        this.save();
        this.refreshView();
    }

    setSyllableOption(option, value) {
        if (option === 'alternation') this.preferences.syllAlternation = value;
        if (option === 'underline') this.preferences.syllUnderline = value;
        this.save();
        this.refreshView();
    }

    togglePhonemes(enabled) {
        this.preferences.phonemesEnabled = enabled;
        const list = document.getElementById('phoneme-list');
        if (list) list.style.display = enabled ? 'grid' : 'none';

        // If enabling for first time and no active phonemes, maybe select all? 
        // For now, let user select.
        this.save();
        this.refreshView();
    }

    togglePhonemeItem(pho, active, color) {
        if (active) {
            this.preferences.activePhonemes[pho] = color;
        } else {
            delete this.preferences.activePhonemes[pho];
        }
        this.save();
        this.refreshView();
    }

    toggleSilentLetters(enabled) {
        this.preferences.silentLetters = enabled;
        this.save();
        this.refreshView();
    }

    toggleSemantic(type, enabled) {
        if (type === 'proper') this.preferences.semanticProper = enabled;
        if (type === 'date') this.preferences.semanticDate = enabled;
        if (type === 'concept') this.preferences.semanticConcept = enabled;
        this.save();
        this.refreshView();
    }

    refreshView() {
        if (document.getElementById('page-content')) {
            this.colorizeText();
        }
    }

    // --- Text Processing Core ---

    colorizeText(newText = null) {
        const container = document.getElementById('page-content');
        if (!container) return;

        // Update cleanText if new content is provided (e.g. pagination)
        if (newText) {
            this.cleanText = newText;
        }
        // Fallback: If no cache exists, try to grab from DOM
        else if (!this.cleanText) {
            this.cleanText = container.innerText;
        }

        let html = '';

        // Process paragraph by paragraph to preserve structure if any
        // Assuming plain text content for now from the existing reader logic
        const paragraphs = this.cleanText.split('\n\n');

        html = paragraphs.map(p => {
            // Check for Title marker (from backend)
            if (p.startsWith('### ')) {
                const titleText = p.replace('### ', '');
                return `<h2 class="chapter-title">${this.processWord(titleText)}</h2>`;
            }

            // 1. Process words
            const words = p.split(/\s+/);
            const content = words.map(word => `<span class="read-word">${this.processWord(word)}</span>`).join(' ');
            return `<p>${content}</p>`; // Wrap in P tags for better spacing
        }).join('');

        container.innerHTML = html;
    }

    processWord(word) {
        if (!word.trim()) return word;

        let processed = word;

        // MODE 1: Syllables
        if (this.preferences.syllabic) {
            const syllables = this.getSyllables(word);
            processed = syllables.map((syll, index) => {
                let classes = ['syll'];
                // Alternation
                if (this.preferences.syllAlternation) {
                    const altIndex = (index % 3) + 1;
                    classes.push(`syll-alt-${altIndex}`);
                }
                // Underline
                if (this.preferences.syllUnderline) {
                    classes.push('syll-underlined');
                }

                // Content of syllable
                let content = syll;
                // Apply internal highlighters (Phonemes/Silent) INSIDE syllable
                content = this.applyInternalHighlights(content);

                return `<span class="${classes.join(' ')}">${content}</span>`;
            }).join('');
        } else {
            // No syllabic split, just apply highlights to whole word
            processed = this.applyInternalHighlights(word);
        }

        return processed;
    }

    applyInternalHighlights(text) {
        let res = text;

        // Phonemes
        if (this.preferences.phonemesEnabled) {
            for (const [mid, color] of Object.entries(this.preferences.activePhonemes)) {
                // Regex: Match phoneme only if NOT inside an HTML tag.
                // Pattern: (mid) followed by NO closing bracket '>' before an opening bracket '<'.
                const regex = new RegExp(`(${mid})(?![^<]*>)`, 'gi');

                // Use a safe class name 'dys-ph' to avoid recursive matching on 'phoneme'
                res = res.replace(regex, `<span class="dys-ph" style="color: ${color}">$1</span>`);
            }
        }

        // Silent Letters (Heuristic)
        if (this.preferences.silentLetters) {
            const silentRegex = /([estdxz])$/i;
            res = res.replace(silentRegex, '<span class="silent-letter">$1</span>');
        }

        // --- Semantic Highlighting ---
        // Warning: This is heuristic-based and applied visually.

        // 1. Proper Nouns (Capitalized words not at start of sentence, rough approximation)
        // We can't easily check "start of sentence" here since we process word-by-word or chunks.
        // Actually, if we process `text` which is the whole paragraph in previous context, we could do better.
        // But `applyInternalHighlights` is called per SYLLABLE or WORD.
        // If called per word, we lose context.
        // Let's assume input `text` is a word or syllable.
        // If it's a Proper Noun, it starts with Capital. But so do sentence starts.
        // Without full NLP, we'll just highlight ALL Capitalized words that aren't obviously common small words?
        // Or we accept the noise.
        // Better: Check if `text` matches [A-Z][a-z]+
        if (this.preferences.semanticProper) {
            // Very naive: anything starting with Uppercase.
            // Ideally we'd skip the first word of a sentence, but we don't know it here.
            // Highlight: Pastel Blue background or bold blue text.
            if (/^[A-Z][a-z]+/.test(text)) {
                res = `<span class="semantic-proper">${res}</span>`;
            }
        }

        // 2. Dates / Numbers
        if (this.preferences.semanticDate) {
            // Digits 1990, 2024, or 12/12
            if (/\d+/.test(text)) {
                res = `<span class="semantic-date">${res}</span>`;
            }
        }

        // 3. Concepts (Long words > 8 chars)
        if (this.preferences.semanticConcept) {
            // Strip tags if any (though we usually add tags outside, here we are inside logic)
            // `text` might already have span tags if we chained them?
            // `applyInternalHighlights` is called at the leaf level.
            // Note: If we already wrapped it in semantic-proper, this might double wrap.
            // Basic heuristic: length check on clean text.
            const clean = text.replace(/<[^>]*>/g, '');
            if (clean.length > 8) {
                res = `<span class="semantic-concept">${res}</span>`;
            }
        }

        return res;
    }

    getSyllables(word) {
        // Simple regex splitter for CV patterns
        // This splits before Consonant-Vowel patterns roughly.
        // It's a heuristic.
        // A better one: https://stackoverflow.com/questions/5613382/javascript-regex-to-split-words-into-syllables
        // For French, roughly:
        const syllableRegex = /[^aeiouy]*[aeiouy]+(?:[^aeiouy]*$|[^aeiouy](?=[^aeiouy]))?/gi;
        return word.match(syllableRegex) || [word];
    }
}

const accessibility = new AccessibilityManager();
