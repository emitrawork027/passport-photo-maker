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

// Passport dimensions: 1.2 inch x 1.4 inch at 300 DPI
const PASSPORT_WIDTH = 1.2 * 300; // 360px
const PASSPORT_HEIGHT = 1.4 * 300; // 420px

passportCanvas.width = PASSPORT_WIDTH;
passportCanvas.height = PASSPORT_HEIGHT;

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

// Color buttons
document.querySelectorAll('.color-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        currentBgColor = btn.getAttribute('data-color');
        drawCanvas();
    });
});

document.getElementById('customColor').addEventListener('input', (e) => {
    currentBgColor = e.target.value;
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
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error removing background');
        passportLoading.style.display = 'none';
    }
});

// Generate passport sheet
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
                    format: 'png'
                })
            });

            const sheetResult = await sheetResponse.json();

            if (sheetResult.success) {
                document.getElementById('finalPassportSheet').src = sheetResult.image;
                passportLoading.style.display = 'none';
                passportEditor.style.display = 'none';
                passportFinal.style.display = 'block';
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

    ctx.fillStyle = currentBgColor;
    ctx.fillRect(0, 0, PASSPORT_WIDTH, PASSPORT_HEIGHT);

    const imgAspect = currentImage.width / currentImage.height;
    const canvasAspect = PASSPORT_WIDTH / PASSPORT_HEIGHT;

    let drawWidth, drawHeight;

    if (imgAspect > canvasAspect) {
        drawHeight = PASSPORT_HEIGHT * zoom;
        drawWidth = drawHeight * imgAspect;
    } else {
        drawWidth = PASSPORT_WIDTH * zoom;
        drawHeight = drawWidth / imgAspect;
    }

    const x = (PASSPORT_WIDTH - drawWidth) / 2 + posX;
    const y = (PASSPORT_HEIGHT - drawHeight) / 2 + posY;

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
