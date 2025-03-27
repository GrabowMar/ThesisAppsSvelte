# 1. Imports Section
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import os

# 2. App Configuration
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.urandom(24)  # Secret key for session management

# 3. In-Memory Database (Replace with a real database in production)
users = {}

# 4. Utility Functions
def validate_registration_data(data):
    if not data.get("username") or not data.get("password"):
        return False, "Username and password are required."
    if data["username"] in users:
        return False, "Username already exists."
    return True, ""

def validate_login_data(data):
    if not data.get("username") or not data.get("password"):
        return False, "Username and password are required."
    if data["username"] not in users:
        return False, "Invalid username or password."
    if not check_password_hash(users[data["username"]]["password"], data["password"]):
        return False, "Invalid username or password."
    return True, ""

# 5. API Routes
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    is_valid, message = validate_registration_data(data)
    if not is_valid:
        return jsonify({"success": False, "message": message}), 400
    users[data["username"]] = {
        "password": generate_password_hash(data["password"]),
    }
    return jsonify({"success": True, "message": "Registration successful!"}), 201

@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    is_valid, message = validate_login_data(data)
    if not is_valid:
        return jsonify({"success": False, "message": message}), 401
    session["username"] = data["username"]
    return jsonify({"success": True, "message": "Login successful!"}), 200

@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("username", None)
    return jsonify({"success": True, "message": "Logout successful!"}), 200

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    if "username" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    return jsonify({"success": True, "message": f"Welcome, {session['username']}!"}), 200

# 6. Error Handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "message": "Internal server error"}), 500

# 7. Run the App
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5161)
