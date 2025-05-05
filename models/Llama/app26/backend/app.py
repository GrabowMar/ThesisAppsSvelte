# app.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# In-memory data store for demonstration purposes
data_store = {
    "carbon_footprint": [],
    "sustainability_challenges": [],
    "resource_consumption": [],
    "eco_friendly_tips": [],
    "progress": [],
    "community_impact": [],
    "recycling_and_waste_reduction": []
}

# API Routes
@app.route('/api/carbon-footprint', methods=['GET', 'POST'])
def carbon_footprint():
    if request.method == 'GET':
        return jsonify(data_store["carbon_footprint"])
    elif request.method == 'POST':
        data = request.json
        data_store["carbon_footprint"].append(data)
        return jsonify(data), 201

@app.route('/api/sustainability-challenges', methods=['GET', 'POST'])
def sustainability_challenges():
    if request.method == 'GET':
        return jsonify(data_store["sustainability_challenges"])
    elif request.method == 'POST':
        data = request.json
        data_store["sustainability_challenges"].append(data)
        return jsonify(data), 201

@app.route('/api/resource-consumption', methods=['GET', 'POST'])
def resource_consumption():
    if request.method == 'GET':
        return jsonify(data_store["resource_consumption"])
    elif request.method == 'POST':
        data = request.json
        data_store["resource_consumption"].append(data)
        return jsonify(data), 201

@app.route('/api/eco-friendly-tips', methods=['GET'])
def eco_friendly_tips():
    return jsonify(data_store["eco_friendly_tips"])

@app.route('/api/progress', methods=['GET', 'POST'])
def progress():
    if request.method == 'GET':
        return jsonify(data_store["progress"])
    elif request.method == 'POST':
        data = request.json
        data_store["progress"].append(data)
        return jsonify(data), 201

@app.route('/api/community-impact', methods=['GET'])
def community_impact():
    return jsonify(data_store["community_impact"])

@app.route('/api/recycling-and-waste-reduction', methods=['GET', 'POST'])
def recycling_and_waste_reduction():
    if request.method == 'GET':
        return jsonify(data_store["recycling_and_waste_reduction"])
    elif request.method == 'POST':
        data = request.json
        data_store["recycling_and_waste_reduction"].append(data)
        return jsonify(data), 201

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5051')))
