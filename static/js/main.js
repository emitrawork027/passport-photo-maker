const uploadBox = document.getElementById('uploadBox');
const imageInput = document.getElementById('imageInput');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const originalImage = document.getElementById('originalImage');
const processedImage = document.getElementById('processedImage');
const qualitySelect = document.getElementById('qualitySelect');

let processedImageData = null;

// Load background removal library dynamically
let removeBackgroundLib = null;

async function loadBackgroundRemovalLibrary() {
    if (removeBackgroundLib) return removeBackgroundLib;
    
    try {
        const module = await import('https://cdn.jsdelivr.net/npm/@imgly/background-removal@1.4.5/dist/browser.js');
        removeBackgroundLib = module.default;
        console.log('Background removal library loaded successfully');
        return removeBackgroundLib;
    } catch (error) {
        console.error('Failed to load background removal library:', error);
        throw new Error('Failed to load required library. Please refresh the page.');
    }
}

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
        loadingText.textContent = 'Loading AI model... This may take a moment on first use.';
    }

    try {
        // Load the background removal library
        const removeBackground = await loadBackgroundRemovalLibrary();
        
        // Update loading message
        if (loadingText) {
            loadingText.textContent = 'Processing image... Please wait 10-30 seconds.';
        }

        // Create blob from file
        const imageUrl = URL.createObjectURL(file);
        
        // Configure based on quality setting
        const quality = qualitySelect.value;
        let config = {
            output: {
                format: 'png',
                quality: 0.8
            }
        };

        // Adjust model based on quality
        if (quality === 'high') {
            config.model = 'medium'; // Better quality but slower
        } else if (quality === 'medium') {
            config.model = 'small'; // Balanced
        } else {
            config.model = 'small'; // Fast
            config.output.quality = 0.6;
        }

        // Remove background using client-side AI
        const blob = await removeBackground(imageUrl, config);
        
        // Convert blob to base64
        const reader2 = new FileReader();
        reader2.onloadend = function() {
            processedImageData = reader2.result;
            processedImage.src = processedImageData;
            loading.style.display = 'none';
            resultSection.style.display = 'block';
        };
        reader2.readAsDataURL(blob);
        
        // Clean up
        URL.revokeObjectURL(imageUrl);

    } catch (error) {
        console.error('Error:', error);
        alert('Error processing image: ' + error.message + '\n\nPlease try again or use a smaller image.');
        loading.style.display = 'none';
        uploadBox.style.display = 'block';
    }
}

function downloadImage(format) {
    if (!processedImageData) return;

    const link = document.createElement('a');
    link.download = `background-removed.${format}`;
    
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
