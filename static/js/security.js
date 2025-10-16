// ============================================
// SECURITY PROTECTION SCRIPT
// ============================================

// Disable Right Click
document.addEventListener('contextmenu', function(e) {
    e.preventDefault();
    showSecurityAlert('Right-click is disabled for security!');
    return false;
});

// Disable Keyboard Shortcuts
document.addEventListener('keydown', function(e) {
    // F12 - Developer Tools
    if (e.keyCode === 123) {
        e.preventDefault();
        showSecurityAlert('Developer tools are disabled!');
        return false;
    }
    
    // Ctrl+Shift+I - DevTools
    if (e.ctrlKey && e.shiftKey && e.keyCode === 73) {
        e.preventDefault();
        showSecurityAlert('Developer tools are disabled!');
        return false;
    }
    
    // Ctrl+Shift+J - Console
    if (e.ctrlKey && e.shiftKey && e.keyCode === 74) {
        e.preventDefault();
        showSecurityAlert('Console access is disabled!');
        return false;
    }
    
    // Ctrl+U - View Source
    if (e.ctrlKey && e.keyCode === 85) {
        e.preventDefault();
        showSecurityAlert('View source is disabled!');
        return false;
    }
    
    // Ctrl+S - Save Page
    if (e.ctrlKey && e.keyCode === 83) {
        e.preventDefault();
        showSecurityAlert('Saving page is disabled!');
        return false;
    }
    
    // Ctrl+Shift+C - Inspect Element
    if (e.ctrlKey && e.shiftKey && e.keyCode === 67) {
        e.preventDefault();
        return false;
    }
    
    // Ctrl+A - Select All (on images)
    if (e.ctrlKey && e.keyCode === 65) {
        if (e.target.tagName === 'IMG') {
            e.preventDefault();
            return false;
        }
    }
});

// Disable Text Selection
document.addEventListener('selectstart', function(e) {
    if (e.target.tagName === 'INPUT' || 
        e.target.tagName === 'TEXTAREA' || 
        e.target.isContentEditable) {
        return true;
    }
    e.preventDefault();
    return false;
});

// Disable Copy
document.addEventListener('copy', function(e) {
    if (e.target.tagName === 'INPUT' || 
        e.target.tagName === 'TEXTAREA') {
        return true;
    }
    e.preventDefault();
    showSecurityAlert('Copying content is disabled!');
    return false;
});

// Disable Cut
document.addEventListener('cut', function(e) {
    if (e.target.tagName === 'INPUT' || 
        e.target.tagName === 'TEXTAREA') {
        return true;
    }
    e.preventDefault();
    return false;
});

// Disable Drag
document.addEventListener('dragstart', function(e) {
    if (e.target.tagName === 'IMG') {
        e.preventDefault();
        return false;
    }
});

// Detect DevTools Opening
(function() {
    let devtools = { isOpen: false, orientation: null };
    const threshold = 160;
    
    const checkDevTools = function() {
        const widthThreshold = window.outerWidth - window.innerWidth > threshold;
        const heightThreshold = window.outerHeight - window.innerHeight > threshold;
        const orientation = widthThreshold ? 'vertical' : 'horizontal';
        
        if (!(heightThreshold && widthThreshold) &&
            ((window.Firebug && window.Firebug.chrome && window.Firebug.chrome.isInitialized) ||
            widthThreshold || heightThreshold)) {
            if (!devtools.isOpen || devtools.orientation !== orientation) {
                devtools.isOpen = true;
                devtools.orientation = orientation;
                blockDevTools();
            }
        } else {
            if (devtools.isOpen) {
                devtools.isOpen = false;
                devtools.orientation = null;
            }
        }
    };
    
    setInterval(checkDevTools, 500);
})();

function blockDevTools() {
    document.body.innerHTML = `
        <div style="
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            text-align: center;
            padding: 20px;
        ">
            <div style="
                background: rgba(255,255,255,0.1);
                padding: 40px;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                max-width: 500px;
            ">
                <div style="font-size: 80px; margin-bottom: 20px;">🔒</div>
                <h1 style="font-size: 32px; margin-bottom: 10px;">Developer Tools Detected!</h1>
                <p style="font-size: 18px; opacity: 0.9; line-height: 1.6;">
                    For security reasons, developer tools are not allowed on this website.
                </p>
                <p style="font-size: 16px; opacity: 0.8; margin-top: 20px;">
                    Please close the developer tools to continue.
                </p>
            </div>
        </div>
    `;
}

// Show Security Alert
function showSecurityAlert(message) {
    const existingAlert = document.querySelector('.security-alert');
    if (existingAlert) existingAlert.remove();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = 'security-alert';
    alertDiv.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            padding: 15px 25px;
            border-radius: 12px;
            z-index: 999999;
            font-weight: 600;
            box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
            animation: slideInRight 0.3s ease-out;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 10px;
        ">
            <span style="font-size: 20px;">🔒</span>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 3000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Disable Console Methods
(function() {
    const noop = function() {};
    const methods = ['log', 'debug', 'info', 'warn', 'error', 'table', 'trace', 'dir', 'group', 'groupCollapsed', 'groupEnd', 'clear'];
    
    methods.forEach(function(method) {
        console[method] = noop;
    });
    
    // Show warning in console (will be cleared immediately but shows intent)
    setTimeout(function() {
        const style = 'color: red; font-size: 40px; font-weight: bold; text-shadow: 2px 2px 0px black;';
        console.log('%cSTOP!', style);
        console.log('%cThis is a browser feature intended for developers only.', 'font-size: 18px; color: red;');
        console.log('%cIf someone told you to copy-paste something here, it is a scam!', 'font-size: 16px; font-weight: bold; color: red;');
        console.log('%cPasting anything here could give attackers access to your account.', 'font-size: 14px;');
    }, 0);
})();

// Prevent Frame Embedding (Anti-Clickjacking)
if (window.top !== window.self) {
    window.top.location = window.self.location;
}

// Disable Print Screen (Limited effectiveness but shows intent)
document.addEventListener('keyup', function(e) {
    if (e.key === 'PrintScreen') {
        navigator.clipboard.writeText('');
        showSecurityAlert('Screenshots are discouraged on this website!');
    }
});

// Monitor for suspicious activity
(function() {
    let debuggerActive = false;
    
    setInterval(function() {
        const before = new Date();
        debugger;
        const after = new Date();
        
        if (after - before > 100) {
            if (!debuggerActive) {
                debuggerActive = true;
                blockDevTools();
            }
        } else {
            debuggerActive = false;
        }
    }, 1000);
})();

console.log('%c🔒 Security Active', 'color: green; font-size: 16px; font-weight: bold;');
