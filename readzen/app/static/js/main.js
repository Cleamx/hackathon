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
    const resizableContainer = document.getElementById('page-resizable');
    let rulerEnabled = false;

    if (toggleBtn && ruler && contentArea && resizableContainer) {
        // Toggle Enable/Disable
        toggleBtn.addEventListener('click', () => {
            rulerEnabled = !rulerEnabled;
            toggleBtn.classList.toggle('active', rulerEnabled);

            if (rulerEnabled) {
                ruler.style.display = 'block';
                ruler.style.opacity = '0';
            } else {
                ruler.style.display = 'none';
            }
        });

        // Follow mouse inside content area
        contentArea.addEventListener('mousemove', (e) => {
            if (rulerEnabled) {
                ruler.style.opacity = '1';

                const containerRect = resizableContainer.getBoundingClientRect();

                // Position relative to the resizable container
                const relativeY = e.clientY - containerRect.top;

                // Center the ruler on cursor (36px height / 2)
                let finalTop = relativeY - 18;

                // Keep ruler within bounds
                const maxTop = resizableContainer.offsetHeight - 36;
                if (finalTop < 0) finalTop = 0;
                if (finalTop > maxTop) finalTop = maxTop;

                ruler.style.top = `${finalTop}px`;

                // Ruler takes full width of resizable container
                ruler.style.left = '0';
                ruler.style.right = '0';
                ruler.style.width = 'auto';
            }
        });

        // Hide ruler when leaving content
        contentArea.addEventListener('mouseleave', () => {
            if (rulerEnabled) {
                ruler.style.opacity = '0';
            }
        });

        // Show ruler when entering content
        contentArea.addEventListener('mouseenter', () => {
            if (rulerEnabled) {
                ruler.style.opacity = '1';
            }
        });
    }
});
