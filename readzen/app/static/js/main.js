document.addEventListener('DOMContentLoaded', () => {
    // Theme Handling
    const themes = ['theme-light', 'theme-dark', 'theme-sepia'];
    let currentThemeIndex = 0;

    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', () => {
            document.body.classList.remove(themes[currentThemeIndex]);
            currentThemeIndex = (currentThemeIndex + 1) % themes.length;
            document.body.classList.add(themes[currentThemeIndex]);
        });
    }

    const fontBtn = document.getElementById('font-toggle');
    if (fontBtn) {
        fontBtn.addEventListener('click', () => {
            document.body.classList.toggle('font-dyslexic');
        });
    }

    // File Upload (Index Page)
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);

            document.getElementById('upload-status').classList.remove('hidden');

            try {
                const response = await fetch('/api/documents/', {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    window.location.href = `/reader/${data.id}`;
                } else {
                    alert('Upload failed');
                }
            } catch (err) {
                console.error(err);
                alert('Error uploading file');
            }
        });
    }

    // Reader Page Polling and Logic
    const readerContent = document.getElementById('reader-content');
    if (readerContent && typeof DOC_ID !== 'undefined') {
        if (typeof INITIAL_STATUS !== 'undefined' && INITIAL_STATUS !== 'completed') {
            pollStatus(DOC_ID);
        } else {
            calculateReadingTime();
        }

        // TTS
        const ttsBtn = document.getElementById('tts-btn');
        if (ttsBtn) {
            ttsBtn.addEventListener('click', () => {
                const text = readerContent.innerText;
                const utterance = new SpeechSynthesisUtterance(text);
                window.speechSynthesis.speak(utterance);
            });
        }
    }
});

async function pollStatus(docId) {
    const contentDiv = document.getElementById('reader-content');
    contentDiv.innerText = "Processing OCR... Please wait.";

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/documents/${docId}`);
            const data = await res.json();

            if (data.status === 'completed') {
                clearInterval(interval);
                // Fetch text
                const textRes = await fetch(`/api/documents/${docId}/text`);
                const textData = await textRes.json();
                contentDiv.innerText = textData.text;
                calculateReadingTime();
            } else if (data.status === 'failed') {
                clearInterval(interval);
                contentDiv.innerText = "Processing failed.";
            }
        } catch (e) {
            console.error(e);
        }
    }, 2000);
}

function calculateReadingTime() {
    const readerContent = document.getElementById('reader-content');
    // Guard clause: if element doesn't exist, stop.
    if (!readerContent) return;

    const text = readerContent.innerText;
    const words = text.trim().split(/\s+/).length;
    const wpm = 200;
    const minutes = Math.ceil(words / wpm);
    const readingTimeSpan = document.getElementById('reading-time');
    if (readingTimeSpan) {
        readingTimeSpan.innerText = `Est. reading time: ${minutes} min`;
    }
}

// Reading Ruler Logic
document.addEventListener('DOMContentLoaded', () => {
    const ruler = document.getElementById('reading-ruler');
    const toggleBtn = document.getElementById('ruler-toggle');
    const contentArea = document.getElementById('page-content');
    let rulerEnabled = false;

    if (toggleBtn && ruler && contentArea) {
        // Toggle Enable/Disable
        toggleBtn.addEventListener('click', () => {
            rulerEnabled = !rulerEnabled;
            toggleBtn.classList.toggle('active', rulerEnabled);

            // If toggling on while mouse is already over content, show it
            if (rulerEnabled && contentArea.matches(':hover')) {
                ruler.style.display = 'block';
            } else {
                ruler.style.display = 'none';
            }
        });

        // Show when entering content
        contentArea.addEventListener('mouseenter', () => {
            if (rulerEnabled) ruler.style.display = 'block';
        });

        // Hide when leaving content
        contentArea.addEventListener('mouseleave', () => {
            if (rulerEnabled) ruler.style.display = 'none';
        });

        // Follow mouse inside content
        contentArea.addEventListener('mousemove', (e) => {
            if (rulerEnabled) {
                // Since ruler is absolute inside #reader-container (parent of contentArea? No, they are siblings or nested)
                // Wait, I put ruler in #reader-container. contentArea is #page-content.
                // Let's use #reader-container as the reference frame.
                const container = document.getElementById('reader-container');
                const rect = container.getBoundingClientRect();

                // Calculate Y relative to the container top
                // e.clientY is viewport Y. rect.top is viewport Y of container.
                // We also need to account for scroll INSIDE the container if it scrolls? 
                // Usually text page scrolls with window.
                // If absolute positioned, it moves with scroll. So we just map to the point on the element.

                const relativeY = e.clientY - rect.top;
                ruler.style.top = `${relativeY}px`;
            }
        });
    }
});
