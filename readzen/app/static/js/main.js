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

    // Reader Page Logic is now handled within reader.html specific script.
});


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
                // Ensure we use the page-content as reference
                const rect = contentArea.getBoundingClientRect();

                // Calculate position relative to the content area
                const relativeY = e.clientY - rect.top;

                // Clamp within bounds (0 to height)
                const clampedY = Math.max(0, Math.min(relativeY, rect.height));

                // Position relative to the container if needed because of structure
                // But actually, ruler is child of reading-container which contains page-content?
                // Wait, in reader.html:
                // <div id="reader-container" style="position: relative;">
                //     <div id="page-content" class="page-frame">...</div>
                //     <div id="reading-ruler" ...></div>
                // </div>
                // So ruler is absolute in reader-container.
                // page-content moves inside reader-container?
                // Actually they are siblings. page-content usually has margin: 0 auto.
                // We want the ruler to be ON TOP of page-content visually.
                // It's probably easier if we check boundaries.

                // Let's set the ruler width/left to match page-content too ?
                // The user said "ne doit pas depasser la feuille" (must not exceed the sheet).

                ruler.style.width = `${rect.width}px`;
                ruler.style.left = `${contentArea.offsetLeft}px`;

                // Logic: 
                // e.clientY is relative to viewport.
                // We want to place ruler at that Y, but relative to the OffsetParent (reader-container).

                const containerRect = document.getElementById('reader-container').getBoundingClientRect();
                const offsetY = e.clientY - containerRect.top;

                // Clamp to page-content vertical bounds relative to container
                const minTop = contentArea.offsetTop;
                const maxTop = contentArea.offsetTop + contentArea.offsetHeight;

                let finalTop = offsetY;
                if (finalTop < minTop) finalTop = minTop;
                if (finalTop > maxTop) finalTop = maxTop;

                ruler.style.top = `${finalTop}px`;
            }
        });
    }
});
