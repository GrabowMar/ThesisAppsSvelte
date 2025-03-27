# 1. Imports Section
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid
import datetime
import json
from werkzeug.utils import secure_filename

# 2. App Configuration
app = Flask(__name__)
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'thumbnails'), exist_ok=True)

# 3. Database Setup (using a simple JSON file for this implementation)
DB_FILE = 'gallery_db.json'

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return {"images": [], "galleries": []}

def save_db(db):
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)

# Initialize DB if it doesn't exist
if not os.path.exists(DB_FILE):
    initial_db = {
        "images": [],
        "galleries": [
            {
                "id": "default",
                "name": "Default Gallery",
                "description": "The default gallery",
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }
        ]
    }
    save_db(initial_db)

# 5. Utility Functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 6. API Routes
@app.route('/api/galleries', methods=['GET'])
def get_galleries():
    """Get all galleries"""
    db = load_db()
    return jsonify(db["galleries"])

@app.route('/api/galleries', methods=['POST'])
def create_gallery():
    """Create a new gallery"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Gallery name is required"}), 400
    
    gallery_id = str(uuid.uuid4())
    now = datetime.datetime.now().isoformat()
    
    new_gallery = {
        "id": gallery_id,
        "name": data["name"],
        "description": data.get("description", ""),
        "created_at": now,
        "updated_at": now
    }
    
    db = load_db()
    db["galleries"].append(new_gallery)
    save_db(db)
    
    return jsonify(new_gallery), 201

@app.route('/api/galleries/<gallery_id>', methods=['GET'])
def get_gallery(gallery_id):
    """Get a specific gallery and its images"""
    db = load_db()
    
    # Find gallery
    gallery = next((g for g in db["galleries"] if g["id"] == gallery_id), None)
    if not gallery:
        return jsonify({"error": "Gallery not found"}), 404
    
    # Find images in this gallery
    gallery_images = [img for img in db["images"] if img["gallery_id"] == gallery_id]
    
    return jsonify({
        "gallery": gallery,
        "images": gallery_images
    })

@app.route('/api/galleries/<gallery_id>', methods=['PUT'])
def update_gallery(gallery_id):
    """Update a gallery's details"""
    data = request.get_json()
    db = load_db()
    
    for i, gallery in enumerate(db["galleries"]):
        if gallery["id"] == gallery_id:
            db["galleries"][i].update({
                "name": data.get("name", gallery["name"]),
                "description": data.get("description", gallery["description"]),
                "updated_at": datetime.datetime.now().isoformat()
            })
            save_db(db)
            return jsonify(db["galleries"][i])
    
    return jsonify({"error": "Gallery not found"}), 404

@app.route('/api/galleries/<gallery_id>', methods=['DELETE'])
def delete_gallery(gallery_id):
    """Delete a gallery"""
    db = load_db()
    
    # Don't allow deleting the default gallery
    if gallery_id == "default":
        return jsonify({"error": "Cannot delete the default gallery"}), 400
    
    # Move images to default gallery
    for image in db["images"]:
        if image["gallery_id"] == gallery_id:
            image["gallery_id"] = "default"
    
    # Remove the gallery
    db["galleries"] = [g for g in db["galleries"] if g["id"] != gallery_id]
    save_db(db)
    
    return "", 204

@app.route('/api/images', methods=['GET'])
def get_all_images():
    """Get all images (with optional gallery_id filter)"""
    gallery_id = request.args.get('gallery_id')
    db = load_db()
    
    if gallery_id:
        images = [img for img in db["images"] if img["gallery_id"] == gallery_id]
    else:
        images = db["images"]
        
    return jsonify(images)

@app.route('/api/images', methods=['POST'])
def upload_image():
    """Upload a new image"""
    gallery_id = request.form.get('gallery_id', 'default')
    
    # Validate gallery exists
    db = load_db()
    gallery = next((g for g in db["galleries"] if g["id"] == gallery_id), None)
    if not gallery:
        return jsonify({"error": "Gallery not found"}), 404
    
    # Check if the post request has the file part
    if 'image' not in request.files:
        return jsonify({"error": "No image part in the request"}), 400
    
    file = request.files['image']
    # If user doesn't select a file
    if file.filename == '':
        return jsonify({"error": "No image selected"}), 400
    
    if file and allowed_file(file.filename):
        # Create a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        image_id = str(uuid.uuid4())
        filename = f"{image_id}.{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file
        file.save(file_path)
        
        # Create image record
        new_image = {
            "id": image_id,
            "filename": filename,
            "original_filename": secure_filename(file.filename),
            "title": request.form.get('title', ''),
            "description": request.form.get('description', ''),
            "gallery_id": gallery_id,
            "uploaded_at": datetime.datetime.now().isoformat(),
            "file_size": os.path.getsize(file_path),
            "mime_type": file.content_type
        }
        
        db["images"].append(new_image)
        save_db(db)
        
        return jsonify(new_image), 201
    
    return jsonify({"error": "File type not allowed"}), 400

@app.route('/api/images/<image_id>', methods=['GET'])
def get_image_details(image_id):
    """Get details for a specific image"""
    db = load_db()
    image = next((img for img in db["images"] if img["id"] == image_id), None)
    
    if not image:
        return jsonify({"error": "Image not found"}), 404
        
    return jsonify(image)

@app.route('/api/images/<image_id>', methods=['PUT'])
def update_image(image_id):
    """Update image metadata"""
    data = request.get_json()
    db = load_db()
    
    for i, image in enumerate(db["images"]):
        if image["id"] == image_id:
            # Only update these fields
            if "title" in data:
                db["images"][i]["title"] = data["title"]
            if "description" in data:
                db["images"][i]["description"] = data["description"]
            if "gallery_id" in data:
                # Verify the gallery exists
                gallery = next((g for g in db["galleries"] if g["id"] == data["gallery_id"]), None)
                if not gallery:
                    return jsonify({"error": "Target gallery not found"}), 400
                db["images"][i]["gallery_id"] = data["gallery_id"]
            
            save_db(db)
            return jsonify(db["images"][i])
    
    return jsonify({"error": "Image not found"}), 404

@app.route('/api/images/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """Delete an image"""
    db = load_db()
    
    image = next((img for img in db["images"] if img["id"] == image_id), None)
    if not image:
        return jsonify({"error": "Image not found"}), 404
    
    # Delete the physical file
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        # Continue even if file deletion fails
        print(f"Error deleting file: {e}")
    
    # Remove from database
    db["images"] = [img for img in db["images"] if img["id"] != image_id]
    save_db(db)
    
    return "", 204

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 7. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500

# Run the app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5345')), debug=True)
