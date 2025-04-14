from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import uuid

app = Flask(__name__)
CORS(app)

# In-memory data store for demonstration purposes
artworks = {}
galleries = {}
portfolios = {}
artists = {}

# Utility function to save artwork file
def save_artwork_file(file, filename):
    file.save(os.path.join('uploads', filename))

# API Routes
@app.route('/api/artworks', methods=['POST'])
def create_artwork():
    data = request.form
    artwork_id = str(uuid.uuid4())
    artworks[artwork_id] = {
        'id': artwork_id,
        'title': data['title'],
        'description': data['description'],
        'filename': request.files['file'].filename
    }
    save_artwork_file(request.files['file'], artworks[artwork_id]['filename'])
    return jsonify(artworks[artwork_id])

@app.route('/api/artworks', methods=['GET'])
def get_artworks():
    return jsonify(list(artworks.values()))

@app.route('/api/galleries', methods=['POST'])
def create_gallery():
    data = request.get_json()
    gallery_id = str(uuid.uuid4())
    galleries[gallery_id] = {
        'id': gallery_id,
        'name': data['name'],
        'artworks': data['artworks']
    }
    return jsonify(galleries[gallery_id])

@app.route('/api/galleries', methods=['GET'])
def get_galleries():
    return jsonify(list(galleries.values()))

@app.route('/api/portfolios', methods=['POST'])
def create_portfolio():
    data = request.get_json()
    portfolio_id = str(uuid.uuid4())
    portfolios[portfolio_id] = {
        'id': portfolio_id,
        'name': data['name'],
        'galleries': data['galleries']
    }
    return jsonify(portfolios[portfolio_id])

@app.route('/api/portfolios', methods=['GET'])
def get_portfolios():
    return jsonify(list(portfolios.values()))

@app.route('/api/artists', methods=['POST'])
def create_artist():
    data = request.get_json()
    artist_id = str(uuid.uuid4())
    artists[artist_id] = {
        'id': artist_id,
        'name': data['name'],
        'bio': data['bio']
    }
    return jsonify(artists[artist_id])

@app.route('/api/artists', methods=['GET'])
def get_artists():
    return jsonify(list(artists.values()))

@app.route('/uploads/<filename>')
def get_artwork_file(filename):
    return send_from_directory('uploads', filename)

if __name__ == '__main__':
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(host='0.0.0.0', port=5055)
