from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import os

# App Configuration
app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///networking.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'

# Initialize Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.String(500))
    skills = db.Column(db.String(200))

class Connection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    connection_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    company = db.Column(db.String(100), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)

class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement = db.Column(db.String(200), nullable=False)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    new_user = User(username=data['username'], password=hashed_password, email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully!"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity={'username': user.username, 'id': user.id})
        return jsonify(access_token=access_token), 200
    else:
        return jsonify({"message": "Invalid credentials!"}), 401


@app.route('/profile', methods=['POST'])
@jwt_required()
def create_profile():
    current_user = get_jwt_identity()
    data = request.get_json()
    new_profile = Profile(user_id=current_user['id'], bio=data['bio'], skills=data['skills'])
    db.session.add(new_profile)
    db.session.commit()
    return jsonify({"message": "Profile created successfully!"}), 201

@app.route('/connections', methods=['POST'])
@jwt_required()
def add_connection():
    current_user = get_jwt_identity()
    data = request.get_json()
    new_connection = Connection(user_id=current_user['id'], connection_id=data['connection_id'])
    db.session.add(new_connection)
    db.session.commit()
    return jsonify({"message": "Connection added successfully!"}), 201

@app.route('/jobs', methods=['POST'])
def post_job():
    data = request.get_json()
    new_job = Job(title=data['title'], description=data['description'], company=data['company'])
    db.session.add(new_job)
    db.session.commit()
    return jsonify({"message": "Job posted successfully!"}), 201

@app.route('/achievements', methods=['POST'])
@jwt_required()
def add_achievement():
    current_user = get_jwt_identity()
    data = request.get_json()
    new_achievement = Achievement(user_id=current_user['id'], achievement=data['achievement'])
    db.session.add(new_achievement)
    db.session.commit()
    return jsonify({"message": "Achievement added successfully!"}), 201

@app.route('/messages', methods=['POST'])
@jwt_required()
def send_message():
    current_user = get_jwt_identity()
    data = request.get_json()
    new_message = Message(sender_id=current_user['id'], receiver_id=data['receiver_id'], content=data['content'])
    db.session.add(new_message)
    db.session.commit()
    return jsonify({"message": "Message sent successfully!"}), 201

@app.errorhandler(404)
def not_found(e):
    return jsonify({"message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"message": "Internal server error"}), 500

if __name__ == '__main__':
    db.create_all()
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5127')))

