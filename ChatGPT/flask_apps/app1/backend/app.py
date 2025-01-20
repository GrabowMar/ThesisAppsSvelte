# Flask Backend (backend/app.py)

from flask import Flask, request, jsonify
from flask_cors import CORS
import jwt
import bcrypt
import os
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'your_secret_key_here'

users = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if email in users:
        return jsonify({'message': 'User already exists'}), 400
    
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users[email] = hashed_pw
    return jsonify({'message': 'User registered successfully'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if email not in users or not bcrypt.checkpw(password.encode('utf-8'), users[email]):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({'email': email, 'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token})

if __name__ == '__main__':
    app.run(debug=True, port=5001)
