from flask import Blueprint, render_template, jsonify

# Създаване на Blueprint за организиране на маршрутите
main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/api/health", methods=["GET"])
def health_status():
    return jsonify({"status": "OK", "message": "Healthy Habits App is running!"})
