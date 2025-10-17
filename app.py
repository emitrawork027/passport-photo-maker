from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
import os
import atexit
import shutil
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
CORS(app)

# Remove.bg API Configuration
REMOVEBG_API_KEY = 'wur8bps17aG47SXUxygcPura'

# Security Headers
@app.after_request
def set_security_headers(response):
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

PORT = int(os.environ.get('PORT', 5000))
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def cleanup_uploads():
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

# [PASTE THE REMOVE-BACKGROUND FUNCTION FROM ABOVE HERE]

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
        
        passport_width = int(1.2 * 300)
        passport_height = int(1.4 * 300)
        
        passport_photo = passport_photo.resize((passport_width, passport_height), Image.LANCZOS)
        
        sheet_width = int(4 * 300)
        sheet_height = int(6 * 300)
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
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

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Allow: /
Sitemap: https://passport-photo-maker-4.onrender.com/sitemap.xml
''', 200, {'Content-Type': 'text/plain'}

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

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
