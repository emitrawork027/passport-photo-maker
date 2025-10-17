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
@app.route('/api/remove-background', methods=['POST'])
def remove_background():
    """Background removal using remove.bg API"""
    try:
        print("=" * 50)
        print("BACKGROUND REMOVAL REQUEST RECEIVED")
        print("=" * 50)
        
        if 'image' not in request.files:
            print("ERROR: No image in request")
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        quality = request.form.get('quality', 'high')
        
        print(f"File name: {file.filename}")
        print(f"Quality: {quality}")
        
        if file.filename == '':
            print("ERROR: Empty filename")
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Read file
            file_content = file.read()
            file_size = len(file_content) / (1024 * 1024)
            
            print(f"File size: {file_size:.2f} MB")
            print(f"API Key present: {bool(REMOVEBG_API_KEY)}")
            print(f"API Key (first 10 chars): {REMOVEBG_API_KEY[:10]}...")
            
            # Check file size
            if file_size > 12:
                print("ERROR: File too large")
                return jsonify({
                    'error': 'Image too large',
                    'message': 'Please use an image smaller than 12MB'
                }), 400
            
            try:
                print("\n>>> Calling remove.bg API...")
                print(f">>> Endpoint: https://api.remove.bg/v1.0/removebg")
                print(f">>> Timeout: 90 seconds")
                
                # Call API
                import time
                start_time = time.time()
                
                response = requests.post(
                    'https://api.remove.bg/v1.0/removebg',
                    files={'image_file': file_content},
                    data={'size': 'auto'},
                    headers={'X-Api-Key': REMOVEBG_API_KEY},
                    timeout=90
                )
                
                elapsed_time = time.time() - start_time
                
                print(f">>> Response received in {elapsed_time:.2f} seconds")
                print(f">>> Status Code: {response.status_code}")
                print(f">>> Response Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    print(">>> SUCCESS! Processing image...")
                    
                    # Process image
                    img = Image.open(io.BytesIO(response.content))
                    print(f">>> Image size: {img.size}")
                    print(f">>> Image mode: {img.mode}")
                    
                    # Apply quality settings
                    buffered = io.BytesIO()
                    
                    if quality == 'high':
                        img.save(buffered, format="PNG", optimize=False)
                    elif quality == 'medium':
                        img = img.resize(
                            (int(img.width * 0.75), int(img.height * 0.75)), 
                            Image.LANCZOS
                        )
                        img.save(buffered, format="PNG", optimize=True)
                    else:
                        img = img.resize(
                            (int(img.width * 0.5), int(img.height * 0.5)), 
                            Image.LANCZOS
                        )
                        img.save(buffered, format="PNG", optimize=True)
                    
                    output_size = len(buffered.getvalue()) / (1024 * 1024)
                    print(f">>> Output size: {output_size:.2f} MB")
                    
                    output_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    print(">>> Sending response to client")
                    print("=" * 50)
                    
                    return jsonify({
                        'success': True,
                        'image': f'data:image/png;base64,{output_base64}'
                    })
                
                else:
                    print(f">>> ERROR: API returned {response.status_code}")
                    print(f">>> Response body: {response.text[:500]}")
                    
                    if response.status_code == 403:
                        return jsonify({
                            'error': 'API quota exceeded',
                            'message': 'Free API limit (50 images/month) reached.'
                        }), 403
                    elif response.status_code == 402:
                        return jsonify({
                            'error': 'Credits exhausted',
                            'message': 'Remove.bg API credits used up.'
                        }), 402
                    else:
                        return jsonify({
                            'error': 'API error',
                            'message': f'Service error: {response.status_code}'
                        }), response.status_code
                    
            except requests.exceptions.Timeout as timeout_err:
                print(f">>> TIMEOUT ERROR: {str(timeout_err)}")
                return jsonify({
                    'error': 'Request timeout',
                    'message': 'Processing took too long. Try smaller image.'
                }), 504
            
            except requests.exceptions.ConnectionError as conn_err:
                print(f">>> CONNECTION ERROR: {str(conn_err)}")
                return jsonify({
                    'error': 'Connection error',
                    'message': 'Cannot connect to removal service.'
                }), 503
            
            except Exception as api_error:
                print(f">>> EXCEPTION: {str(api_error)}")
                import traceback
                traceback.print_exc()
                return jsonify({
                    'error': 'Processing error',
                    'message': str(api_error)
                }), 500
        
        print("ERROR: Invalid file type")
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        print(f"FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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
        
        # Get custom dimensions (in inches)
        photo_width = float(data.get('width', 1.2))
        photo_height = float(data.get('height', 1.4))
        
        print(f"Generating sheet with photo size: {photo_width}\" x {photo_height}\"")
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        passport_photo = Image.open(io.BytesIO(img_bytes))
        
        # Calculate dimensions at 300 DPI
        passport_width_px = int(photo_width * 300)
        passport_height_px = int(photo_height * 300)
        
        print(f"Photo dimensions: {passport_width_px}px x {passport_height_px}px")
        
        passport_photo = passport_photo.resize((passport_width_px, passport_height_px), Image.LANCZOS)
        
        # Create 4x6 inch sheet at 300 DPI
        sheet_width = int(4 * 300)  # 1200 pixels
        sheet_height = int(6 * 300)  # 1800 pixels
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        # Calculate how many photos fit
        margin = 20
        available_width = sheet_width - (2 * margin)
        available_height = sheet_height - (2 * margin)
        
        cols = max(1, int(available_width / passport_width_px))
        rows = max(1, int(available_height / passport_height_px))
        
        # Limit to 12 photos maximum
        total_photos = min(cols * rows, 12)
        
        # Recalculate for even spacing
        if cols * rows > 12:
            # Try 3x4 layout for 12 photos
            cols = 3
            rows = 4
        
        print(f"Layout: {cols} cols x {rows} rows = {cols * rows} photos")
        
        spacing_x = (available_width - (cols * passport_width_px)) // (cols + 1) if cols > 1 else (available_width - passport_width_px) // 2
        spacing_y = (available_height - (rows * passport_height_px)) // (rows + 1) if rows > 1 else (available_height - passport_height_px) // 2
        
        count = 0
        for row in range(rows):
            for col in range(cols):
                if count >= 12:  # Stop at 12 photos
                    break
                x = margin + spacing_x + col * (passport_width_px + spacing_x)
                y = margin + spacing_y + row * (passport_height_px + spacing_y)
                sheet.paste(passport_photo, (x, y))
                count += 1
            if count >= 12:
                break
        
        print(f"Pasted {count} photos on sheet")
        
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
            'image': f'data:image/{format_type};base64,{img_str}',
            'photos_count': count
        })
    
    except Exception as e:
        print(f"Error in generate_passport_sheet: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-joint-sheet', methods=['POST'])
def generate_joint_sheet():
    """Generate joint photo sheet - 8 photos of 1.9x1.4 inches on 4x6 sheet"""
    try:
        print("=" * 50)
        print("JOINT PHOTO SHEET GENERATION STARTED")
        print("=" * 50)
        
        data = request.get_json()
        image_data = data.get('image')
        format_type = data.get('format', 'png')
        quality = data.get('quality', 'high')
        
        # Fixed dimensions for joint photos
        photo_width = 1.9  # inches
        photo_height = 1.4  # inches
        
        print(f"Joint photo size: {photo_width}\" x {photo_height}\"")
        print(f"Format: {format_type}, Quality: {quality}")
        
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        img_bytes = base64.b64decode(image_data)
        joint_photo = Image.open(io.BytesIO(img_bytes))
        
        print(f"Original image size: {joint_photo.size}")
        
        # Calculate dimensions at 300 DPI
        photo_width_px = int(photo_width * 300)  # 570 pixels
        photo_height_px = int(photo_height * 300)  # 420 pixels
        
        print(f"Photo dimensions: {photo_width_px}px x {photo_height_px}px")
        
        # Resize photo
        joint_photo = joint_photo.resize((photo_width_px, photo_height_px), Image.LANCZOS)
        
        # Create 4x6 inch sheet at 300 DPI
        sheet_width = int(4 * 300)  # 1200 pixels
        sheet_height = int(6 * 300)  # 1800 pixels
        sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
        
        print(f"Sheet size: {sheet_width}px x {sheet_height}px")
        
        # Layout: 2 columns x 4 rows = 8 photos
        cols = 2
        rows = 4
        
        # Calculate spacing
        margin = 15
        available_width = sheet_width - (2 * margin)
        available_height = sheet_height - (2 * margin)
        
        spacing_x = (available_width - (cols * photo_width_px)) // (cols + 1)
        spacing_y = (available_height - (rows * photo_height_px)) // (rows + 1)
        
        print(f"Layout: {cols} cols x {rows} rows = 8 photos")
        print(f"Spacing - X: {spacing_x}px, Y: {spacing_y}px")
        
        # Paste photos on sheet
        count = 0
        for row in range(rows):
            for col in range(cols):
                x = margin + spacing_x + col * (photo_width_px + spacing_x)
                y = margin + spacing_y + row * (photo_height_px + spacing_y)
                
                print(f"Photo {count + 1}: Position ({x}, {y})")
                
                sheet.paste(joint_photo, (x, y))
                count += 1
        
        print(f"Total photos pasted: {count}")
        
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
        
        output_size = len(buffered.getvalue()) / (1024 * 1024)
        print(f"Output file size: {output_size:.2f} MB")
        
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        print("SUCCESS! Joint sheet generated")
        print("=" * 50)
        
        return jsonify({
            'success': True,
            'image': f'data:image/{format_type};base64,{img_str}',
            'photos_count': count
        })
    
    except Exception as e:
        print("=" * 50)
        print(f"ERROR in generate_joint_sheet: {str(e)}")
        import traceback
        traceback.print_exc()
        print("=" * 50)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
