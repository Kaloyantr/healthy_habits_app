import os
import bcrypt
import json
import plotly.graph_objects as go
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from src import db
from src.models import User, Health
from src.weather import get_weather
from src.utils import allowed_file
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/register")
def register():
    return render_template("register.html")

@main.route("/register_action", methods=["POST"])
def register_action():
    if request.method == "POST":
        if "firstname" not in request.form or "surname" not in request.form:
            session["message"] = {"text": "Missing required fields.", "type": "error"}
            return redirect(url_for("main.register"))

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"].encode("utf-8")
        firstname = request.form["firstname"]
        surname = request.form["surname"]
        profilepic = "static/images/profile.jpg"
        
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password, salt)

        existing_user = db.session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                session["message"] = {"text": "Username already exists", "type": "error"}
            elif existing_user.email == email:
                session["message"] = {"text": "Email already exists", "type": "error"}
            return redirect(url_for("main.register"))

        new_user = User(username=username, email=email, firstname=firstname, surname=surname, password=hashed_password, profilepic=profilepic)

        try:
            db.session.add(new_user)
            db.session.commit()
            session["message"] = {"text": "Registration successful!", "type": "success"}
            return redirect(url_for("main.login"))
        except IntegrityError:
            db.session.rollback()
            session["message"] = {"text": "There was an error with the registration. Please try again.", "type": "error"}
            return redirect(url_for("main.register"))

    return render_template("register.html")

@main.route("/login_action", methods=["POST"])
def login_action():
    if request.method != "POST":
        return redirect(url_for("main.login", message="Invalid method"))
    user = User.query.filter_by(username=request.form["username"]).first()

    if user and bcrypt.checkpw(request.form["password"].encode("utf-8"), user.password):
        username = user.username
        session["id"] = user.id
        session["username"] = user.username
        session["firstname"] = user.firstname
        return redirect(url_for("main.startmenu", username=username, token="123456"))
    else:
        session["message"] = {"text": "Invalid username or password", "type": "error"}
        return redirect(url_for("main.login"))

@main.route("/login")
def login():
    message = request.args.get("message", None)
    session["logged_in"] = True
    return render_template("login.html", title="Login", message=message)

@main.route("/startmenu")
def startmenu():
    if "id" not in session:
        return redirect(url_for("main.login"))

    user = User.query.filter_by(id=session["id"]).first()
    name = user.firstname
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace("static/","")
    else:
        picadres = "images/profile.jpg"
    
    return render_template("startmenu.html", name=name, profilepic=picadres)

@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))

@main.route("/dashboard")
def dashboard():
    if "id" not in session:
        return redirect(url_for("main.login"))

    user = User.query.filter_by(id=session["id"]).first()
    name = user.firstname
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace("static/","")
    else:
        picadres = "images/profile.jpg"
    
    return render_template("dashboard.html", name=name, profilepic=picadres)

@main.route("/profile")
def profile():
    user = User.query.filter_by(username=session.get("username")).first()
    username = user.username
    email = user.email
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace("static/","")
    else:
        picadres = "images/profile.jpg"
    return render_template("profile.html", username=username, email=email, profilepic=picadres)

@main.route("/editprofile", methods=["GET", "POST"])
def editprofile():
    from flask import current_app
    username = session.get("username")
    current_user = User.query.filter_by(username=username).first()
    
    if not current_user:
        flash("User not found")
        return redirect(url_for("main.profile"))

    if request.method == "POST":
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        username = request.form.get("username")
        email = request.form.get("email")
        
        if not firstname or not lastname or not email:
            flash("Please enter all forms.")
            return redirect(url_for("main.editprofile"))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash("Username already exists.")
            return redirect(url_for("main.editprofile"))

        file = request.files.get("profilepic")
        profile_pic_path = None
        
        if file and file.filename != "":
            if allowed_file(file.filename, current_app.config.get("ALLOWED_EXTENSIONS")):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                file.save(upload_path)
                profile_pic_path = url_for("static", filename="uploads/" + filename)
            else:
                flash("Not correct format.Please upload a .png, .jpg, .jpeg или .gif format.")
                return redirect(url_for("main.editprofile"))
        
        current_user.firstname = firstname
        current_user.surname = lastname
        current_user.username = username
        current_user.email = email
        if profile_pic_path:
            current_user.profilepic = profile_pic_path
        
        db.session.commit()
        flash("Changes are saved!")
        return redirect(url_for("main.profile"))
    
    return render_template("editprofile.html", user=current_user)

@main.route("/delete_profile", methods=["POST"])
def delete_profile():
    if "id" in session:
        username = session.get("username")
        current_user = User.query.filter_by(username=username).first()
        try:
            user_id = session.get("id")
            user_health_data = Health.query.filter_by(userid = user_id).all()
            for data in user_health_data:
                db.session.delete(data) 
            db.session.delete(current_user)
            db.session.commit()
            flash("Your profile was deleted!", "success")
            
            session.clear()
            return redirect(url_for("main.login"))

        except Exception as e:
            db.session.rollback()
            flash(f"Fail during deleting profile: {str(e)}", "danger")
            return redirect(url_for("main.dashboard"))

    else:
        flash("Not logged in.", "danger")
        return redirect(url_for("main.login"))

@main.route("/view_steps_graph", methods=["GET"])
def view_steps_graph():
    specific_user_id = session["id"]
    
    dates_data = db.session.query(Health.date).filter(Health.userid == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    steps_data = db.session.query(Health.steps).filter(Health.userid == specific_user_id).all()
    steps_list = [int(row[0]) for row in steps_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=steps_list, mode="lines+markers", name="Steps",line=dict(shape="hvh",color="#e8d0c1")))

    fig.update_layout(
        xaxis_title="Time(d)",
        yaxis_title="Steps",
        plot_bgcolor="#27403a",
        paper_bgcolor="rgba(176, 84, 8, 0)",
        xaxis=dict(tickfont=dict(size = 15, color="#b05408")),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )

    graph_html = fig.to_html(full_html=False)

    return render_template("graph.html",name = "Steps", graph_html=graph_html)

@main.route("/view_pulse_graph", methods=["GET"])
def view_pulse_graph():
    specific_user_id = session["id"]
    
    dates_data = db.session.query(Health.date).filter(Health.userid == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    pulse_data = db.session.query(Health.heartrate).filter(Health.userid == specific_user_id).all()
    pulse_list = [int(row[0]) for row in pulse_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=pulse_list, mode="lines+markers", name="Heart rate",line=dict(color="#e8d0c1")))

    fig.update_layout(
        title="Heart Rate",
        xaxis_title="Time(d)",
        yaxis_title="Pulse(bpm)",
        plot_bgcolor="#27403a",
        paper_bgcolor="rgba(176, 84, 8, 0)",
        xaxis=dict(tickfont=dict(size = 15, color="#b05408")),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )

    graph_html = fig.to_html(full_html=False)

    return render_template("graph.html", name = "Pulse", graph_html=graph_html)

@main.route("/view_stress_graph", methods=["GET"])
def view_stress_graph():
    specific_user_id = session["id"]
    
    dates_data = db.session.query(Health.date).filter(Health.userid == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    stress_data = db.session.query(Health.stress).filter(Health.userid == specific_user_id).all()
    stress_list = [int(row[0]) for row in stress_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=stress_list, mode="lines+markers", name="Stress", line=dict(shape="hvh")))

    fig.update_layout(
        title="Stress",
        xaxis_title="Time(d)",
        yaxis_title="Stress",
        plot_bgcolor="#27403a",
        paper_bgcolor="rgba(176, 84, 8, 0)",
        xaxis=dict(tickfont=dict(size = 15, color="#b05408")),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )

    graph_html = fig.to_html(full_html=False)

    return render_template("graph.html", name = "Stress levels", graph_html=graph_html)

@main.route("/view_calories_graph", methods=["GET"])
def view_calories_graph():
    specific_user_id = session["id"]
    dates_data = db.session.query(Health.date).filter(Health.userid == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    calories_data = db.session.query(Health.calories).filter(Health.userid == specific_user_id).all()
    calories_list = [int(row[0]) for row in calories_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=calories_list, mode="lines+markers", name="Heart rate", line=dict(shape="hvh")))

    fig.update_layout(
        title="Calories",
        xaxis_title="Time(d)",
        yaxis_title="Calories(cal)",
        plot_bgcolor="#27403a",
        paper_bgcolor="rgba(176, 84, 8, 0)",
        xaxis=dict(tickfont=dict(size = 15, color="#b05408")),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )
    graph_html = fig.to_html(full_html=False)
    return render_template("graph.html", name = "Calories", graph_html=graph_html)

@main.route("/view_sleep_graph", methods=["GET"])
def view_sleep_graph():
    specific_user_id = session["id"]
    dates_data = db.session.query(Health.date).filter(Health.userid == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    sleep_data = db.session.query(Health.sleephours).filter(Health.userid == specific_user_id).all()
    sleep_list = [int(row[0]) for row in sleep_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=sleep_list, mode="lines+markers", name="Sleep hours", line=dict(shape="hvh")))

    fig.update_layout(
        title="Sleep hours",
        xaxis_title="Time(d)",
        yaxis_title="Sleep(hours)",
        plot_bgcolor="#27403a",
        paper_bgcolor="rgba(176, 84, 8, 0)",
        xaxis=dict(tickfont=dict(size = 15, color="#b05408")),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )
    graph_html = fig.to_html(full_html=False)
    return render_template("graph.html", name = "Sleep records", graph_html=graph_html)

@main.route("/give_advice", methods=["POST", "GET"])
def give_advice():
    user_id = session.get("id")  
    
    if not user_id:
        return "No user data.", 400  

    user = User.query.filter_by(id=user_id).first()

    if not user:
        return "No user data.", 400
    
    sleephours_data = db.session.query(Health.sleephours).filter(Health.userid == user_id).all()
    sleephours_list = [row[0] for row in sleephours_data]
    av_sleep = sum(sleephours_list) / len(sleephours_list) if len(sleephours_list) > 0 else 0  
    
    calories_data = db.session.query(Health.calories).filter(Health.userid == user_id).all()
    calories_list = [row[0] for row in calories_data]
    av_cal = sum(calories_list) / len(calories_list) if len(calories_list) > 0 else 0  
    
    weight = user.weight if user.weight else 72  
    height = user.height if user.height else 1.75

    A = (av_sleep / 8) + (av_cal / 2500)
    BMI = weight / (height ** 2)
    E = 100 / BMI
    
    health_score = (A + E) / 2
    
    temp, cond = get_weather("Sofia")
    
    if temp > 10:
        msg = f"The temprature is {temp}°C and the condition is {cond} so you can go for a walk at the local park."
    else:
        msg = f"The temprature is {temp}°C and the condition is {cond} so you can go to fitness or some indoor activity."
    
    if health_score > 80:
        advice = f"Your health is excellent! Keep up your active lifestyle.{msg}"
    elif 50 < health_score <= 80:
        advice = f"Your health is good, but there is room for improvement.{msg}"
    else:
        advice = f"Your health condition can be improved. Consider adopting a healthier lifestyle.{msg}"
        
    session["advice"] = advice  
    return redirect(url_for("main.startmenu", username=session.get("username"), token=""))

@main.route("/upload", methods=["POST"])
def upload_json():
    if "jsonfile" not in request.files:
        return {"error": "No file part"}, 400
    
    file = request.files["jsonfile"]
    
    user_id = session.get("id")
    
    if file.filename == "":
        return {"error": "No selected file"}, 400

    try:
        json_data = json.load(file)

        activity = json_data.get("activity", {})
        calories_data = activity.get("calories", [])
        steps_data = activity.get("steps", [])
        heart_rate_data = json_data.get("heartRate", [])

        user_health_data = Health.query.filter_by(userid=user_id).all()
        for data in user_health_data:
            db.session.delete(data)

        for entry in calories_data:
            date = datetime.strptime(entry["date"], "%Y-%m-%d")
            calories = entry["calories"]

            steps = next((s["steps"] for s in steps_data if s["date"] == entry["date"]), 0)

            hr_entry = next((h for h in heart_rate_data if h["date"] == entry["date"]), None)
            avg_hr = hr_entry.get("average", 0.0) if hr_entry else 0

            existing_record = Health.query.filter_by(userid=user_id, date=date).first()

            if existing_record:
                existing_record.steps = steps
                existing_record.heartrate = avg_hr
                existing_record.calories = calories
            else:
                health_record = Health(
                    userid=user_id,
                    date=date,
                    steps=steps,
                    heartrate=avg_hr,
                    calories=calories
                )
                db.session.add(health_record)

        db.session.commit()

        user = User.query.filter_by(id=user_id).first()
        name = user.firstname
        if user.profilepic and user.profilepic != "static/images/profile.jpg":
            picadres = user.profilepic.replace("static/","")
        else:
            picadres = "images/profile.jpg"

        return render_template("dashboard.html", name=name, profilepic=picadres)

    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@main.route("/metrics", methods=["GET", "POST"], endpoint="metrics")
def metrics():
    username = session.get("username")
    if not username:
        return redirect(url_for("main.login"))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        return redirect(url_for("main.login"))
    
    if request.method == "POST":
        height = request.form.get("height")
        weight = request.form.get("weight")
        age = request.form.get("age")
        gender = request.form.get("gender")
        
        try:
            user.height = float(height)
            user.weight = float(weight)
            user.age = int(age)
        except ValueError:
            return redirect(url_for("main.metrics"))
        
        user.gender = gender
        
        db.session.commit()
        return redirect(url_for("main.startmenu"))
    
    return render_template("metrics.html", user=user)
