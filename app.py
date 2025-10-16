from flask import Flask, render_template, request, send_file, jsonify
from flask_cors import CORS
# from rembg import remove  # ✅ Commented out - not available in free tier
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os
import atexit
import shutil
from werkzeug.utils import secure_filename


app = Flask(__name__)
CORS(app)  # Enable CORS for API calls


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
    Background removal endpoint
    Note: AI-based background removal requires heavy libraries (rembg)
    which need more than 512MB RAM. This is a placeholder for demonstration.
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image provided'}), 400
        
        file = request.files['image']
        quality = request.form.get('quality', 'high')
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            input_image = file.read()
            
            # Open image
            img = Image.open(io.BytesIO(input_image))
            
            # Convert to RGBA for transparency support
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
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
            
            return jsonify({
                'success': True,
                'image': f'data:image/png;base64,{output_base64}',
                'message': 'Note: AI background removal requires upgraded hosting plan. Currently returning processed image.'
            })
        
        return jsonify({'error': 'Invalid file type'}), 400
    
    except Exception as e:
        print(f"Error in remove_background: {str(e)}")
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
        # Here you can add email sending logic or save to database
        return jsonify({'success': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Health check endpoint for Render
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    app.run(debug=DEBUG, host='0.0.0.0', port=PORT)
