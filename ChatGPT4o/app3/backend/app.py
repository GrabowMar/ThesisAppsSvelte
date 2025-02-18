from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

FEEDBACK_FILE = "feedback.json"

def load_feedback():
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, "r") as file:
            return json.load(file)
    return []

def save_feedback(data):
    with open(FEEDBACK_FILE, "w") as file:
        json.dump(data, file, indent=4)

@app.route("/submit-feedback", methods=["POST"])
def submit_feedback():
    try:
        data = request.get_json()
        
        # Validate input
        if not all(k in data for k in ["name", "email", "feedback"]):
            return jsonify({"error": "Missing required fields."}), 400

        feedback_list = load_feedback()
        feedback_list.append(data)
        save_feedback(feedback_list)

        return jsonify({"message": "Feedback submitted successfully."}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/feedback", methods=["GET"])
def get_feedback():
    try:
        feedback_list = load_feedback()
        return jsonify(feedback_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5005)