# 1. Imports Section
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from datetime import datetime

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 3. Database Models (Simulated)
artists_db = []
artworks_db = []
galleries_db = []
exhibitions_db = []

# 4. Utility Functions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_id():
    return str(datetime.now().timestamp()).replace('.', '')

# 5. API Routes

# Artist Routes
@app.route('/api/artist', methods=['POST'])
def create_artist():
    data = request.json
    if not data or not data.get('name'):
        return jsonify({'error': 'Name is required'}), 400
    
    artist = {
        'id': generate_id(),
        'name': data['name'],
        'bio': data.get('bio', ''),
        'contact': data.get('contact', ''),
        'social_links': data.get('social_links', {})
    }
    artists_db.append(artist)
    return jsonify(artist), 201

@app.route('/api/artist/<artist_id>', methods=['GET', 'PUT', 'DELETE'])
def artist_handler(artist_id):
    artist = next((a for a in artists_db if a['id'] == artist_id), None)
    if not artist:
        return jsonify({'error': 'Artist not found'}), 404
    
    if request.method == 'GET':
        return jsonify(artist)
    
    elif request.method == 'PUT':
        data = request.json
        artist.update({
            'name': data.get('name', artist['name']),
            'bio': data.get('bio', artist['bio']),
            'contact': data.get('contact', artist['contact']),
            'social_links': data.get('social_links', artist['social_links'])
        })
        return jsonify(artist)
    
    elif request.method == 'DELETE':
        artists_db.remove(artist)
        return jsonify({'message': 'Artist deleted'}), 200

# Artwork Routes
@app.route('/api/artwork', methods=['GET', 'POST'])
def artwork_handler():
    if request.method == 'GET':
        return jsonify(artworks_db)
    
    elif request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            data = request.form.to_dict()
            artwork = {
                'id': generate_id(),
                'artist_id': data.get('artist_id'),
                'title': data.get('title', 'Untitled'),
                'description': data.get('description', ''),
                'medium': data.get('medium', ''),
                'creation_date': data.get('creation_date', ''),
                'category': data.get('category', 'General'),
                'image_url': f'/api/uploads/{filename}',
                'is_featured': data.get('is_featured', 'false').lower() == 'true'
            }
            artworks_db.append(artwork)
            return jsonify(artwork), 201
        else:
            return jsonify({'error': 'File type not allowed'}), 400

# Serve uploaded files
@app.route('/api/uploads/<filename>')
def uploaded_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

# Gallery Routes
@app.route('/api/gallery', methods=['GET', 'POST'])
def gallery_handler():
    if request.method == 'GET':
        return jsonify(galleries_db)
    
    elif request.method == 'POST':
        data = request.json
        if not data or not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        
        gallery = {
            'id': generate_id(),
            'artist_id': data['artist_id'],
            'name': data['name'],
            'description': data.get('description', ''),
            'artwork_ids': data.get('artwork_ids', [])
        }
        galleries_db.append(gallery)
        return jsonify(gallery), 201

# 6. Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5215')))
