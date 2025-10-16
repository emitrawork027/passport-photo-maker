const uploadBox = document.getElementById('uploadBox');
const imageInput = document.getElementById('imageInput');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const originalImage = document.getElementById('originalImage');
const processedImage = document.getElementById('processedImage');
const qualitySelect = document.getElementById('qualitySelect');

let processedImageData = null;

// Drag and drop
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    uploadBox.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

['dragenter', 'dragover'].forEach(eventName => {
    uploadBox.addEventListener(eventName, () => {
        uploadBox.classList.add('dragover');
    }, false);
});

['dragleave', 'drop'].forEach(eventName => {
    uploadBox.addEventListener(eventName, () => {
        uploadBox.classList.remove('dragover');
    }, false);
});

uploadBox.addEventListener('drop', handleDrop, false);
uploadBox.addEventListener('click', () => imageInput.click());

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

imageInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

async function handleFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    
    if (!file.type.startsWith('image/')) {
        alert('Please upload an image file');
        return;
    }

    // Show original image
    const reader = new FileReader();
    reader.onload = (e) => {
        originalImage.src = e.target.result;
    };
    reader.readAsDataURL(file);

    uploadBox.style.display = 'none';
    loading.style.display = 'block';
    
    // Update loading message
    const loadingText = loading.querySelector('p');
    if (loadingText) {
        loadingText.textContent = 'Processing your image...';
    }

    // Use server-side processing (simple and reliable)
    const formData = new FormData();
    formData.append('image', file);
    formData.append('quality', qualitySelect.value);

    try {
        const response = await fetch('/api/remove-background', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            processedImageData = result.image;
            processedImage.src = result.image;
            loading.style.display = 'none';
            resultSection.style.display = 'block';
            
            // Show message if background removal not available
            if (result.message) {
                setTimeout(() => {
                    alert(result.message);
                }, 500);
            }
        } else {
            throw new Error(result.error || 'Processing failed');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error processing image. Please try again or use a smaller image.');
        loading.style.display = 'none';
        uploadBox.style.display = 'block';
    }
}

function downloadImage(format) {
    if (!processedImageData) return;

    const link = document.createElement('a');
    link.download = `processed-image.${format}`;
    
    if (format === 'jpg') {
        const img = new Image();
        img.onload = () => {
            const canvas = document.createElement('canvas');
            canvas.width = img.width;
            canvas.height = img.height;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            link.href = canvas.toDataURL('image/jpeg', 0.95);
            link.click();
        };
        img.src = processedImageData;
    } else {
        link.href = processedImageData;
        link.click();
    }
}

function resetUploader() {
    uploadBox.style.display = 'block';
    resultSection.style.display = 'none';
    imageInput.value = '';
    processedImageData = null;
}
