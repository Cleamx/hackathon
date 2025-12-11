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

        // Update cleanText if new content is provided
        if (newText) {
            this.cleanText = newText;
        } else if (!this.cleanText) {
            this.cleanText = container.innerText;
        }

        // 1. Render Markdown to HTML using marked.js
        // Configure marked to handle breaks if needed
        if (typeof marked !== 'undefined') {
            container.innerHTML = marked.parse(this.cleanText);
        } else {
            // Fallback if marked failed to load
            container.innerText = this.cleanText;
        }

        // 2. Apply Accessibility Transformations to Text Nodes only
        this.applyAccessibilityToContainer(container);

        // 3. Post-Process: Try to merge orphan images into tables
        // Heuristic: If we see a table, then look at subsequent elements. 
        // If we see an image, checks if the table has "empty" cells or cells with "Ref" that might need an image.
        // Simplified: Inspect table rows. If a cell mentions "Figure" or "Image" or is just a "Ref" column, 
        // pull the next available image from the DOM into it.
        this.embedImagesInTables(container);
    }

    embedImagesInTables(container) {
        // Find all tables
        const tables = container.querySelectorAll('table');
        tables.forEach(table => {
            // Find all P tags containing IMGs that immediately follow the table
            // We look at siblings of the table
            let nextNode = table.nextElementSibling;
            const imagesToMove = [];

            // Limit search to next 100 siblings to find ALL images
            // (Previous limit of 10 caused missing images and sync shifts if there was padding text)
            let checks = 0;
            while (nextNode && checks < 100) {
                if (nextNode.tagName === 'P' && nextNode.querySelector('img')) {
                    const img = nextNode.querySelector('img');
                    imagesToMove.push({ note: nextNode, img: img });
                } else if (nextNode.tagName === 'IMG') {
                    imagesToMove.push({ note: nextNode, img: nextNode });
                } else if (['H1', 'H2', 'TABLE'].includes(nextNode.tagName)) {
                    // Stop if we hit a MAJOR section break, but allow H3/Text to be skipped
                    // This ensures we don't steal images from the next chapter
                    break;
                }
                nextNode = nextNode.nextElementSibling;
                checks++;
            }

            if (imagesToMove.length === 0) return;

            // Strategy: 
            // Iterate rows. If we find a cell that looks like an image placeholder, put image there.
            // Or just fill the last column?
            const rows = table.querySelectorAll('tr');
            let imgIndex = 0;

            for (let i = 0; i < rows.length; i++) {
                if (imgIndex >= imagesToMove.length) break;

                const row = rows[i];
                const cells = row.querySelectorAll('td');
                if (cells.length === 0) continue; // Skip header

                // Target: First Column (often the Ref/Name column)
                const targetCell = cells[0];
                const text = targetCell.innerText.trim();

                // Sync Logic:
                // We have fewer images than rows ("il manque des images").
                // We must only put an image if the line actually "looks" like a reference.
                // Patterns:
                // 1. Keywords: "Fig", "Image", "Ref".
                // 2. IDs: Short uppercase codes (e.g. "XJ-900", "A12"), common in catalogs.
                // 3. Not empty.

                // Regex for ID: Allow #, and slightly longer codes.
                // Also simple length check: If text is short (< 50 chars), it's likely a Ref/Code/Name, 
                // whereas a Description would be longer.

                const isIdLike = /^[#A-Z0-9\-\.\/\s]{2,25}$/i.test(text);
                const isShort = text.length > 1 && text.length < 50;
                const hasKeyword = /(fig|image|photo|view|ref|#)/i.test(text);

                // If it looks like a Ref (ID pattern OR Short Text) AND we have images left
                if ((isIdLike || hasKeyword || isShort) && imgIndex < imagesToMove.length) {
                    // Move the next available image here
                    const { note, img } = imagesToMove[imgIndex];

                    const container = document.createElement('div');
                    container.style.marginTop = "8px";
                    container.style.textAlign = "center"; // Center in cell
                    container.appendChild(img);

                    targetCell.appendChild(container);

                    // Cleanup origin
                    if (note.tagName === 'P' && note.innerText.trim() === '') {
                        note.remove();
                    }

                    imgIndex++;
                }
                // Else: Skip this row (it remains "seule" as requested)
            }
        });
    }

    applyAccessibilityToContainer(container) {
        // TreeWalker to traverse only text nodes
        const walker = document.createTreeWalker(
            container,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: function (node) {
                    // Skip empty/whitespace only
                    if (!node.nodeValue.trim()) return NodeFilter.FILTER_SKIP;
                    // Skip script/style tags just in case
                    if (node.parentNode.tagName === 'SCRIPT' || node.parentNode.tagName === 'STYLE') return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );

        const nodesToProcess = [];
        while (walker.nextNode()) {
            nodesToProcess.push(walker.currentNode);
        }

        // Process nodes (replace text node with span containing styled HTML)
        nodesToProcess.forEach(node => {
            const originalText = node.nodeValue;

            // Process the text (Syllables, Phonemes, etc.)
            // Note: processWord returns HTML string (e.g. <span class="syll">...</span>)
            // But processWord works on words. We need to split the text node.

            const words = originalText.split(/(\s+)/); // Split keeping delimiters
            const processedHTML = words.map(w => {
                // If whitespace, return as is
                if (/^\s+$/.test(w)) return w;
                return this.processWord(w);
            }).join('');

            // Create a temp container to parse the new HTML
            const span = document.createElement('span');
            span.innerHTML = processedHTML;

            // Unpack the span to avoid unnecessary nesting? 
            // Better to keep it or replace the text node with the children.
            // Text node can be replaced by multiple nodes.
            node.replaceWith(...span.childNodes);
        });
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
