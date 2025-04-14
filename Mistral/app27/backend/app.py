from flask import Flask, jsonify, request
from flask_cors import CORS
import os
app = Flask(__name__)
CORS(app)
# Assuming we use SQLAlchemy for ORM
from flask_sqlalchemy import SQLAlchemy

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sports_team.db'
db = SQLAlchemy(app)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    position = db.Column(db.String(50))
    performance = db.Column(db.String(100))
    health_status = db.Column(db.String(50))

class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule = db.Column(db.String(100))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    opponent = db.Column(db.String(100))
    result = db.Column(db.String(50))

db.create_all()
# For simplicity, let's assume a basic token-based authentication
auth_token = "your_secure_token"

def authenticate():
    token = request.headers.get('Authorization')
    if token != auth_token:
        return False
    return True
# None specified
@app.route('/players', methods=['GET', 'POST'])
def manage_players():
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        data = request.json
        new_player = Player(name=data['name'], position=data['position'],
                            performance=data['performance'], health_status=data['health_status'])
        db.session.add(new_player)
        db.session.commit()
        return jsonify({"message": "Player added", "player": data}), 201

    players = Player.query.all()
    return jsonify([{"id": player.id, "name": player.name, "position": player.position,
                     "performance": player.performance, "health_status": player.health_status}
                    for player in players])

@app.route('/trainings', methods=['GET', 'POST'])
def manage_trainings():
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        data = request.json
        new_training = Training(schedule=data['schedule'])
        db.session.add(new_training)
        db.session.commit()
        return jsonify({"message": "Training scheduled", "training": data}), 201

    trainings = Training.query.all()
    return jsonify([{"id": training.id, "schedule": training.schedule} for training in trainings])

@app.route('/matches', methods=['GET', 'POST'])
def manage_matches():
    if not authenticate():
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        data = request.json
        new_match = Match(date=data['date'], opponent=data['opponent'], result=data['result'])
        db.session.add(new_match)
        db.session.commit()
        return jsonify({"message": "Match scheduled", "match": data}), 201

    matches = Match.query.all()
    return jsonify([{"id": match.id, "date": match.date, "opponent": match.opponent, "result": match.result}
                    for match in matches])
@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404

@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=str(e)), 500
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5133')))

