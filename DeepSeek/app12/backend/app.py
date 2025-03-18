from flask import Flask, jsonify, request, render_template
from datetime import datetime

app = Flask(__name__)

# Mock data for available time slots
time_slots = {
    "2023-10-01": ["10:00", "12:00", "14:00"],
    "2023-10-02": ["11:00", "13:00", "15:00"],
}

# Mock data for reservations
reservations = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/available-slots/<date>", methods=["GET"])
def get_available_slots(date):
    if date in time_slots:
        return jsonify(time_slots[date])
    return jsonify({"error": "No slots available for this date"}), 404

@app.route("/api/reserve", methods=["POST"])
def make_reservation():
    data = request.get_json()
    date = data.get("date")
    time = data.get("time")
    name = data.get("name")

    if not date or not time or not name:
        return jsonify({"error": "Missing required fields"}), 400

    if date not in time_slots or time not in time_slots[date]:
        return jsonify({"error": "Invalid date or time slot"}), 400

    if (date, time) in reservations:
        return jsonify({"error": "Time slot already reserved"}), 409

    reservations[(date, time)] = name
    return jsonify({"message": "Reservation successful", "reservation": {"date": date, "time": time, "name": name}}), 201

@app.route("/api/reservations", methods=["GET"])
def get_reservations():
    return jsonify([{"date": k[0], "time": k[1], "name": v} for k, v in reservations.items()])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5183)
