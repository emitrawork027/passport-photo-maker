document.addEventListener('DOMContentLoaded', () => {
    const themeBtn = document.getElementById('themeBtn');
    const themeModal = document.getElementById('themeModal');
    const themeOptions = document.querySelectorAll('.theme-option');

    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'default';
    document.body.setAttribute('data-theme', savedTheme);

    // Toggle theme modal
    if (themeBtn) {
        themeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            themeModal.classList.toggle('active');
        });
    }

    // Close modal when clicking outside
    document.addEventListener('click', (e) => {
        if (themeModal && !themeModal.contains(e.target) && e.target !== themeBtn) {
            themeModal.classList.remove('active');
        }
    });

    // Theme selection
    themeOptions.forEach(option => {
        option.addEventListener('click', () => {
            const theme = option.getAttribute('data-theme');
            document.body.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            themeModal.classList.remove('active');
        });
    });
});
