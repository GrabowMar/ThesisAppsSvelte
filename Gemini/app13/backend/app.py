# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename

# 2. App Configuration
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'  # Directory to store uploaded images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the upload directory if it doesn't exist

# 3. Database Models (Simple in-memory storage for demonstration)
# In a real app, you'd use a database like SQLite or PostgreSQL
galleries = {} # {gallery_name: [image_filename1, image_filename2, ...]}
images_metadata = {} # {image_filename: {title: "Image Title", description: "Image description", gallery: "Gallery Name"}}


# 4. Authentication Logic (Placeholder - not implemented in this example)
# In a real application, you'd have user authentication and authorization


# 5. Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 6. API Routes

@app.route('/api/images', methods=['GET'])
def list_images():
    """Lists all images and their metadata."""
    return jsonify(images_metadata)


@app.route('/api/galleries', methods=['GET'])
def list_galleries():
    """Lists all galleries."""
    return jsonify(list(galleries.keys()))


@app.route('/api/galleries/<gallery_name>', methods=['GET'])
def get_gallery(gallery_name):
    """Gets the images in a specific gallery."""
    if gallery_name in galleries:
        return jsonify(galleries[gallery_name])
    else:
        return jsonify({'error': 'Gallery not found'}), 404


@app.route('/api/galleries/<gallery_name>/images/<image_filename>', methods=['GET'])
def get_image_metadata(gallery_name, image_filename):
    """Gets metadata for a specific image."""
    if image_filename in images_metadata and images_metadata[image_filename]['gallery'] == gallery_name:
        return jsonify(images_metadata[image_filename])
    else:
        return jsonify({'error': 'Image not found'}), 404


@app.route('/api/upload', methods=['POST'])
def upload_image():
    """Uploads a new image."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    gallery_name = request.form.get('gallery', 'default')  # Get gallery name from form data
    image_title = request.form.get('title', 'Untitled')
    image_description = request.form.get('description', '')


    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Update in-memory storage
        if gallery_name not in galleries:
            galleries[gallery_name] = []
        galleries[gallery_name].append(filename)

        images_metadata[filename] = {
            'title': image_title,
            'description': image_description,
            'gallery': gallery_name
        }

        return jsonify({'message': 'File uploaded successfully', 'filename': filename, 'gallery': gallery_name}), 201
    else:
        return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):
    """Serves the image file."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)  # Serve the uploaded image

# 7. Error Handlers

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5425')), debug=True)
