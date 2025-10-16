let currentLang = 'en';

// Language button click
document.addEventListener('DOMContentLoaded', () => {
    const langBtn = document.getElementById('langBtn');
    
    if (langBtn) {
        langBtn.addEventListener('click', toggleLanguage);
    }

    // Load saved language
    const savedLang = localStorage.getItem('language');
    if (savedLang) {
        currentLang = savedLang;
        updateLanguage();
    }
});

function toggleLanguage() {
    currentLang = currentLang === 'en' ? 'hi' : 'en';
    localStorage.setItem('language', currentLang);
    updateLanguage();
}

function updateLanguage() {
    const langBtn = document.getElementById('langBtn');
    
    // Update button text
    if (langBtn) {
        langBtn.textContent = currentLang === 'en' ? '🌐 HI' : '🌐 EN';
    }

    // Update all elements with data-en and data-hi
    document.querySelectorAll('[data-en][data-hi]').forEach(element => {
        const text = currentLang === 'en' ? element.getAttribute('data-en') : element.getAttribute('data-hi');
        
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            element.placeholder = text;
        } else if (element.tagName === 'OPTION') {
            element.textContent = text;
        } else {
            element.innerHTML = text;
        }
    });
    
    // NEW: Update placeholders
    document.querySelectorAll('[data-placeholder-en][data-placeholder-hi]').forEach(element => {
        const placeholder = currentLang === 'en' 
            ? element.getAttribute('data-placeholder-en') 
            : element.getAttribute('data-placeholder-hi');
        element.placeholder = placeholder;
    });
}

