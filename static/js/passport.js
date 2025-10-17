const passportImageInput = document.getElementById('passportImageInput');
const passportUploadSection = document.getElementById('passportUploadSection');
const passportEditor = document.getElementById('passportEditor');
const passportFinal = document.getElementById('passportFinal');
const passportLoading = document.getElementById('passportLoading');
const passportCanvas = document.getElementById('passportCanvas');
const ctx = passportCanvas.getContext('2d');

let currentImage = null;
let zoom = 1;
let posX = 0;
let posY = 0;
let currentBgColor = '#FFFFFF';
let backgroundRemoved = false;
let currentPhotoWidth = 1.2;
let currentPhotoHeight = 1.4;

// Initial canvas dimensions
const PASSPORT_WIDTH = 1.2 * 300;
const PASSPORT_HEIGHT = 1.4 * 300;

passportCanvas.width = PASSPORT_WIDTH;
passportCanvas.height = PASSPORT_HEIGHT;

// Photo size selector
document.getElementById('photoSizeSelect').addEventListener('change', function() {
    const customInputs = document.getElementById('customSizeInputs');
    if (this.value === 'custom') {
        customInputs.style.display = 'block';
        updateCanvasSize();
    } else {
        customInputs.style.display = 'none';
        const [width, height] = this.value.split(',').map(parseFloat);
        currentPhotoWidth = width;
        currentPhotoHeight = height;
        updateCanvasSize();
    }
});

// Custom size inputs
document.getElementById('customWidth').addEventListener('input', updateCanvasSize);
document.getElementById('customHeight').addEventListener('input', updateCanvasSize);

function updateCanvasSize() {
    const sizeSelect = document.getElementById('photoSizeSelect');
    if (sizeSelect.value === 'custom') {
        currentPhotoWidth = parseFloat(document.getElementById('customWidth').value) || 1.2;
        currentPhotoHeight = parseFloat(document.getElementById('customHeight').value) || 1.4;
    }
    
    passportCanvas.width = currentPhotoWidth * 300;
    passportCanvas.height = currentPhotoHeight * 300;
    drawCanvas();
}

// Image upload
passportImageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
            currentImage = img;
            passportUploadSection.style.display = 'none';
            passportEditor.style.display = 'block';
            drawCanvas();
        };
        img.src = e.target.result;
    };
    reader.readAsDataURL(file);
});

// Sliders
document.getElementById('zoomSlider').addEventListener('input', (e) => {
    zoom = parseFloat(e.target.value);
    drawCanvas();
});

document.getElementById('posXSlider').addEventListener('input', (e) => {
    posX = parseInt(e.target.value);
    drawCanvas();
});

document.getElementById('posYSlider').addEventListener('input', (e) => {
    posY = parseInt(e.target.value);
    drawCanvas();
});

// Color buttons with active state
document.querySelectorAll('.color-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        document.querySelectorAll('.color-btn').forEach(b => {
            b.style.border = b.style.background === '#FFFFFF' || b.style.background.includes('#FFFFFF') ? '2px solid #e5e7eb' : 'none';
        });
        this.style.border = '3px solid #000';
        currentBgColor = this.getAttribute('data-color');
        drawCanvas();
    });
});

document.getElementById('customColor').addEventListener('input', (e) => {
    currentBgColor = e.target.value;
    document.querySelectorAll('.color-btn').forEach(b => {
        b.style.border = b.style.background === '#FFFFFF' ? '2px solid #e5e7eb' : 'none';
    });
    drawCanvas();
});

// Remove background
document.getElementById('removeBackgroundBtn').addEventListener('click', async () => {
    if (!currentImage) return;

    passportLoading.style.display = 'block';

    const canvas = document.createElement('canvas');
    canvas.width = currentImage.width;
    canvas.height = currentImage.height;
    const tempCtx = canvas.getContext('2d');
    tempCtx.drawImage(currentImage, 0, 0);
    const imageData = canvas.toDataURL('image/png');

    try {
        const response = await fetch('/api/remove-background', {
            method: 'POST',
            body: (() => {
                const formData = new FormData();
                const blob = dataURItoBlob(imageData);
                formData.append('image', blob, 'photo.png');
                return formData;
            })()
        });

        const result = await response.json();

        if (result.success) {
            const img = new Image();
            img.onload = () => {
                currentImage = img;
                backgroundRemoved = true;
                passportLoading.style.display = 'none';
                drawCanvas();
            };
            img.src = result.image;
        } else {
            throw new Error(result.message || 'Background removal failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error removing background: ' + error.message);
        passportLoading.style.display = 'none';
    }
});

// Generate passport sheet with confetti animation
document.getElementById('generatePassportBtn').addEventListener('click', async () => {
    passportLoading.style.display = 'block';

    try {
        const imageData = passportCanvas.toDataURL('image/png');

        const response = await fetch('/api/process-passport', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image: imageData,
                bgColor: currentBgColor
            })
        });

        const result = await response.json();

        if (result.success) {
            const sheetResponse = await fetch('/api/generate-passport-sheet', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    image: result.image,
                    format: 'png',
                    width: currentPhotoWidth,
                    height: currentPhotoHeight
                })
            });

            const sheetResult = await sheetResponse.json();

            if (sheetResult.success) {
                document.getElementById('finalPassportSheet').src = sheetResult.image;
                passportLoading.style.display = 'none';
                passportEditor.style.display = 'none';
                passportFinal.style.display = 'block';
                
                // Show success animation with confetti
                showSuccessAnimation();
            }
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error generating passport sheet');
        passportLoading.style.display = 'none';
    }
});

function drawCanvas() {
    if (!currentImage) return;

    const canvasWidth = passportCanvas.width;
    const canvasHeight = passportCanvas.height;

    ctx.fillStyle = currentBgColor;
    ctx.fillRect(0, 0, canvasWidth, canvasHeight);

    const imgAspect = currentImage.width / currentImage.height;
    const canvasAspect = canvasWidth / canvasHeight;

    let drawWidth, drawHeight;

    if (imgAspect > canvasAspect) {
        drawHeight = canvasHeight * zoom;
        drawWidth = drawHeight * imgAspect;
    } else {
        drawWidth = canvasWidth * zoom;
        drawHeight = drawWidth / imgAspect;
    }

    const x = (canvasWidth - drawWidth) / 2 + posX;
    const y = (canvasHeight - drawHeight) / 2 + posY;

    ctx.drawImage(currentImage, x, y, drawWidth, drawHeight);
}

function downloadPassport(format) {
    const img = document.getElementById('finalPassportSheet');
    const link = document.createElement('a');
    link.download = `passport-photo-sheet.${format}`;
    link.href = img.src;
    link.click();
}

function resetPassportMaker() {
    passportFinal.style.display = 'none';
    passportEditor.style.display = 'none';
    passportUploadSection.style.display = 'block';
    passportImageInput.value = '';
    currentImage = null;
    zoom = 1;
    posX = 0;
    posY = 0;
    backgroundRemoved = false;
    currentPhotoWidth = 1.2;
    currentPhotoHeight = 1.4;
    document.getElementById('photoSizeSelect').value = '1.2,1.4';
    document.getElementById('customSizeInputs').style.display = 'none';
}

function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(',')[1]);
    const mimeString = dataURI.split(',')[0].split(':')[1].split(';')[0];
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

// Confetti animation functions
function showSuccessAnimation() {
    const overlay = document.getElementById('successOverlay');
    
    // Clear previous confetti
    overlay.innerHTML = '';
    
    // Create confetti pieces
    const colors = ['red', 'blue', 'green', 'yellow', 'purple', 'pink', 'orange', 'teal'];
    for (let i = 0; i < 50; i++) {
        const confetti = document.createElement('div');
        confetti.className = `confetti confetti-${colors[Math.floor(Math.random() * colors.length)]}`;
        confetti.style.left = Math.random() * 100 + '%';
        confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';
        confetti.style.animationDelay = (Math.random() * 2) + 's';
        overlay.appendChild(confetti);
    }
    
    // Create success box
    const successBox = document.createElement('div');
    successBox.className = 'success-box';
    successBox.innerHTML = `
        <div class="success-emoji">🎉</div>
        <h2 class="success-title">Passport Photo Ready!</h2>
        <p class="success-message">
            Your 4" x 6" sheet with 12 passport photos<br>
            (${currentPhotoWidth}" x ${currentPhotoHeight}" each at 300 DPI) is ready!
        </p>
        <button class="success-btn" onclick="closeSuccessOverlay()">
            <span>✓</span> Continue
        </button>
    `;
    overlay.appendChild(successBox);
    
    // Show overlay
    overlay.classList.add('active');
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        closeSuccessOverlay();
    }, 5000);
}

function closeSuccessOverlay() {
    document.getElementById('successOverlay').classList.remove('active');
}
