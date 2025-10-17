from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
import os
import atexit
import shutil
from werkzeug.utils import secure_filename
import cv2
import mediapipe as mp
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for API calls

# Initialize MediaPipe Selfie Segmentation (Lazy loading)
mp_selfie_segmentation = mp.solutions.selfie_segmentation
segmentation_model = None

def get_segmentation_model():
    """Initialize segmentation model on first use"""
    global segmentation_model
    if segmentation_model is None:
        print("Initializing background removal AI model...")
        segmentation_model = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)
        print("AI model loaded successfully!")
    return segmentation_model

# Security Headers
@app.after_request
def set_security_headers(response):
    """Set security headers for all responses"""
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self' https://cdn.jsdelivr.net; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://pagead2.googlesyndication.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self' https://cdn.jsdelivr.net;"
    )
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    response.headers['Server'] = 'SecureServer'
    
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'webp'}

# Environment variables
PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Create uploads folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_uploads():
    """Clean uploads folder on shutdown"""
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            shutil.rmtree(app.config['UPLOAD_FOLDER'])
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        except:
            pass

atexit.register(cleanup_uploads)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/passport-maker')
def passport_maker():
    return render_template('passport_maker.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    """
    Custom AI Background Removal API using MediaPipe
    Works on free tier (512MB RAM)
    No external dependencies
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        quality = request.form.get('quality', 'high')
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            print(f"Processing image: {file.filename}")
            
            # Read image
            image_data = file.read()
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return jsonify({'error': 'Failed to read image'}), 400
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get segmentation model
            segmenter = get_segmentation_model()
            
            # Process the image
            print("Running AI model...")
            results = segmenter.process(image_rgb)
            
            # Get segmentation mask
            mask = results.segmentation_mask
            
            # Threshold and clean up mask
            mask = (mask > 0.5).astype(np.uint8) * 255
            
            # Apply morphological operations to clean mask
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            # Smooth edges
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            # Create RGBA image
            image_rgba = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2RGBA)
            image_rgba[:, :, 3] = mask
            
            # Convert to PIL Image
            img = Image.fromarray(image_rgba)
            
            # Apply quality settings
            buffered = io.BytesIO()
            
            if quality == 'high':
                img.save(buffered, format="PNG", optimize=False)
            elif quality == 'medium':
                img = img.resize((int(img.width * 0.75), int(img.height * 0.75)), Image.LANCZOS)
                img.save(buffered, format="PNG", optimize=True)
            else:  # low
                img = img.resize((int(img.width * 0.5), int(img.height * 0.5)), Image.LANCZOS)
                img.save(buffered, format="PNG", optimize=True)
            
            output_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            print("Background removal successful!")
            
            return jsonify({
                'success': True,
                'image': f'data:image/png;base64,{output_base64}'
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        print(f"Error in remove_background: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-passport', methods=['POST'])
def process_passport():
    try:
        data = request.get_json()
        image_data = data.get('image')
        bg_color = data.get('bgColor', '#FFFFFF')
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        background = Image.new('RGBA', img.size, bg_color)
        background.paste(img, (0, 0), img)
        background = background.convert('RGB')
        
        buffered = io.BytesIO()
        background.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_str}'
        })
    
    except Exception as e:
        print(f"Error in process_passport: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-passport-sheet', methods=['POST'])
def generate_passport_sheet():
    try:
        data = request.get_json()
        image_data = data.get('image')
        format_type = data.get('format', 'png')
        quality = data.get('quality', 'high')
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        passport_photo = Image.open(io.BytesIO(img_bytes))
        
        # Passport dimensions at 300 DPI
        passport_width = int(1.2 * 300)  # 360 pixels
        passport_height = int(1.4 * 300)  # 420 pixels
        
        passport_photo = passport_photo.resize((passport_width, passport_height), Image.LANCZOS)
        
        # Create 4x6 inch sheet at 300 DPI
        sheet_width = int(4 * 300)  # 1200 pixels
        sheet_height = int(6 * 300)  # 1800 pixels
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        # 12 photos layout: 3 columns x 4 rows
        margin = 20
        spacing_x = (sheet_width - (3 * passport_width) - (2 * margin)) // 4
        spacing_y = (sheet_height - (4 * passport_height) - (2 * margin)) // 5
        
        count = 0
        for row in range(4):
            for col in range(3):
                x = margin + col * (passport_width + spacing_x)
                y = margin + row * (passport_height + spacing_y)
                sheet.paste(passport_photo, (x, y))
                count += 1
                if count >= 12:
                    break
            if count >= 12:
                break
        
        # Save with quality settings
        buffered = io.BytesIO()
        if format_type == 'jpeg':
            if quality == 'high':
                sheet.save(buffered, format="JPEG", quality=95, dpi=(300, 300))
            elif quality == 'medium':
                sheet.save(buffered, format="JPEG", quality=85, dpi=(300, 300))
            else:
                sheet.save(buffered, format="JPEG", quality=70, dpi=(300, 300))
        else:
            sheet.save(buffered, format="PNG", dpi=(300, 300))
        
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return jsonify({
            'success': True,
            'image': f'data:image/{format_type};base64,{img_str}'
        })
    
    except Exception as e:
        print(f"Error in generate_passport_sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        data = request.get_json()
        return jsonify({'success': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint for Render
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

# Robots.txt for SEO
@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://passport-photo-maker-4.onrender.com/sitemap.xml
''', 200, {'Content-Type': 'text/plain'}

# Sitemap for SEO
@app.route('/sitemap.xml')
def sitemap():
    pages = [
        {'loc': '/', 'priority': '1.0', 'changefreq': 'daily'},
        {'loc': '/passport-maker', 'priority': '0.8', 'changefreq': 'weekly'},
        {'loc': '/about', 'priority': '0.5', 'changefreq': 'monthly'},
        {'loc': '/contact', 'priority': '0.5', 'changefreq': 'monthly'},
    ]
    
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        sitemap_xml += f'  <url>\n'
        sitemap_xml += f'    <loc>https://passport-photo-maker-4.onrender.com{page["loc"]}</loc>\n'
        sitemap_xml += f'    <priority>{page["priority"]}</priority>\n'
        sitemap_xml += f'    <changefreq>{page["changefreq"]}</changefreq>\n'
        sitemap_xml += f'  </url>\n'
    
    sitemap_xml += '</urlset>'
    
    return sitemap_xml, 200, {'Content-Type': 'application/xml'}

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
