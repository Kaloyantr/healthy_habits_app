import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from src import db
from src.models import User, Health
from werkzeug.utils import secure_filename
from src.utils import allowed_file
import plotly.graph_objects as go
from datetime import datetime

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template('index.html')

@main.route("/register")
def register():
    return render_template('register.html')

@main.route("/register_action", methods=['POST'])
def register_action():
    if request.method == 'POST':

        if 'firstname' not in request.form or 'surname' not in request.form:
            flash("Missing required fields.", "error")
            return redirect(url_for('main.register'))
        # Вземаме данните от формата
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        firstname = request.form['firstname']
        surname = request.form['surname']
        profilepic = "static/images/profile.jpg"

        #hashed_password = generate_password_hash(password, method='sha256')

        new_user = User(username=username, email=email, firstname=firstname, surname=surname, password=password, profilepic = profilepic)
        
        db.session.add(new_user)
        db.session.commit()

        print(f"New user: {username}, {email}")
        print("Registration successful!")
        return redirect(url_for('main.login', message='Succesfull registration!'))

    return render_template('register.html')

@main.route("/login_action", methods=['POST'])
def login_action():
    if request.method != 'POST':
        return redirect(url_for('main.login', message='Invalid method'))
    user = User.query.filter_by(username=request.form['username']).first()

    if user and request.form['password'] == user.password:
        username = user.username
        session['id'] = user.id
        session['username'] = user.username
        session['firstname'] = user.firstname
        return redirect(url_for('main.startmenu', username=username, token='123456'))
    else:
        return redirect(url_for('main.login', message='Invalid username or password'))

@main.route("/login")
def login():
    message = request.args.get('message', None)
    session['logged_in'] = True
    return render_template('login.html', title='Login', message=message)

@main.route('/startmenu')
def startmenu():
    if 'id' not in session:
        return redirect(url_for('main.login'))  # Пренасочва към логин страницата, ако потребителят не е логнат

    user = User.query.filter_by(id=session['id']).first()
    name = user.firstname
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace('static/','')
        #profilepic = url_for('static', profilepic = picadres)
    else:
        picadres = 'images/profile.jpg'
    
    return render_template('startmenu.html', name=name, profilepic=picadres)

@main.route("/user_page")
def user_page():
    if not session.get("logged_in"):  # Ако няма активна сесия
        return redirect(url_for("main.login")) 
    return render_template('in_app.html')

@main.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

@main.route('/dashboard')
def dashboard():
    if 'id' not in session:
        return redirect(url_for('main.login'))  # Пренасочва към логин страницата, ако потребителят не е логнат

    user = User.query.filter_by(id=session['id']).first()
    name = user.firstname
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace('static/','')
        #profilepic = url_for('static', profilepic = picadres)
    else:
        picadres = 'images/profile.jpg'
    
    return render_template('dashboard.html', name=name, profilepic=picadres)

@main.route('/profile')
def profile():
    user = User.query.filter_by(username=session.get('username')).first()
    username = user.username
    email = user.email
    if user.profilepic and user.profilepic != "static/images/profile.jpg":
        picadres = user.profilepic.replace('static/','')
        #profilepic = url_for('static', profilepic = picadres)
    else:
        picadres = "images/profile.jpg"
    return render_template('profile.html', username=username, email=email, profilepic=picadres)

@main.route('/editprofile', methods=['GET', 'POST'])
def editprofile():
    from flask import current_app
    username = session.get('username')
    current_user = User.query.filter_by(username=username).first()
    
    if not current_user:
        flash("Потребителят не е намерен!")
        return redirect(url_for('main.profile'))

    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        
        # Проверка за задължителни полета
        if not firstname or not lastname or not email:
            flash('Моля попълнете всички полета.')
            return redirect(url_for('main.editprofile'))

        # Проверка за уникалност на потребителското име
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Потребителското име вече съществува.')
            return redirect(url_for('main.editprofile'))

        file = request.files.get('profilepic')
        profile_pic_path = None
        
        if file and file.filename != "":
            if allowed_file(file.filename, current_app.config.get('ALLOWED_EXTENSIONS')):
                filename = secure_filename(file.filename)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(upload_path)
                profile_pic_path = url_for('static', filename='uploads/' + filename)
            else:
                flash('Невалиден формат на файл. Моля качете снимка с .png, .jpg, .jpeg или .gif формат.')
                return redirect(url_for('main.editprofile'))
        
        # Актуализиране на данните за потребителя
        current_user.firstname = firstname
        current_user.surname = lastname
        current_user.username = username
        current_user.email = email
        if profile_pic_path:
            current_user.profilepic = profile_pic_path
        
        db.session.commit()
        flash("Промените са запазени успешно!")
        return redirect(url_for('main.profile'))
    
    return render_template('editprofile.html', user=current_user)

@main.route("/delete_profile", methods=["POST"])
def delete_profile():
    if 'id' in session:
        username = session.get('username')
        current_user = User.query.filter_by(username=username).first()
        try:
            # Изтриваме потребителя от базата данни
            db.session.delete(current_user)
            db.session.commit()
            flash("Вашият профил беше успешно изтрит.", "success")
            
            session.clear()  # Допълнително изчистване на сесията
            return redirect(url_for('main.login'))  # Пренасочваме към логин страницата

        except Exception as e:
            db.session.rollback()  # В случай на грешка, връщаме промените в базата
            flash(f"Грешка при изтриването на профила: {str(e)}", "danger")
            return redirect(url_for('main.dashboard'))  # Пренасочваме обратно към dashboard

    else:
        flash("Не сте логнати.", "danger")
        return redirect(url_for('main.login'))  # Пренасочваме към логин страницата, ако потребителят не е логнат

@main.route("/view_steps_graph", methods=["GET"])
def view_steps_graph():
    dates_data = db.session.query(Health.date).all()
    date_list = [row[0].date() for row in dates_data]
    steps_data = db.session.query(Health.steps).all()
    steps_list = [int(row[0]) for row in steps_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=steps_list, mode='lines+markers', name='Steps',line=dict(shape='hvh',color='#e8d0c1')))

    fig.update_layout(
        #title=dict(text="Steps Over Time", font=dict(size=60, color='#b05408')),
        xaxis_title='Time(d)',
        yaxis_title='Steps',
        plot_bgcolor='#27403a',
        paper_bgcolor='rgba(176, 84, 8, 0)',
        xaxis=dict(tickfont=dict(size = 15, color='#b05408')),
        yaxis=dict(tickfont=dict(size = 15, color="#b05408"))
    )

    # Генериране на HTML за графиката
    graph_html = fig.to_html(full_html=False)

    return render_template('graph.html',name = "Steps", graph_html=graph_html)
 
@main.route("/view_pulse_graph", methods=["GET"])
def view_pulse_graph():
    dates_data = db.session.query(Health.date).all()
    date_list = [row[0].date() for row in dates_data]
    pulse_data = db.session.query(Health.heartrate).all()
    pulse_list = [int(row[0]) for row in pulse_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=pulse_list, mode='lines+markers', name='Heart rate'))

    fig.update_layout(
        title='Heart Rate',
        xaxis_title='Time(d)',
        yaxis_title='Pulse(bpm)',
    )

    # Генериране на HTML за графиката
    graph_html = fig.to_html(full_html=False)

    return render_template('graph.html', name = 'Pulse', graph_html=graph_html)

@main.route("/view_stress_graph", methods=["GET"])
def view_stress_graph():
    dates_data = db.session.query(Health.date).all()
    date_list = [row[0].date() for row in dates_data]
    stress_data = db.session.query(Health.stress).all()
    stress_list = [int(row[0]) for row in stress_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=stress_list, mode='lines+markers', name='Stress', line=dict(shape='hvh')))

    fig.update_layout(
        title='Stress',
        xaxis_title='Time(d)',
        yaxis_title='Stress',
        plot_bgcolor='rgba(230, 230, 250, 0.8)',  # Светло лилав фон
        paper_bgcolor='rgba(240, 248, 255, 0.9)',
    )

    # Генериране на HTML за графиката
    graph_html = fig.to_html(full_html=False)

    return render_template('graph.html', name = 'Stress levels', graph_html=graph_html)

@main.route("/view_calories_graph", methods=["GET"])
def view_calories_graph():
    dates_data = db.session.query(Health.date).all()
    date_list = [row[0].date() for row in dates_data]
    calories_data = db.session.query(Health.calories).all()
    calories_list = [int(row[0]) for row in calories_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=calories_list, mode='lines+markers', name='Heart rate', line=dict(shape='hvh')))

    fig.update_layout(
        title='Calories',
        xaxis_title='Time(d)',
        yaxis_title='Calories(cal)',
    )

    # Генериране на HTML за графиката
    graph_html = fig.to_html(full_html=False)

    return render_template('graph.html', name = 'Calories', graph_html=graph_html)

@main.route("/view_sleep_graph", methods=["GET"])
def view_sleep_graph():
    dates_data = db.session.query(Health.date).all()
    date_list = [row[0].date() for row in dates_data]
    sleep_data = db.session.query(Health.sleephours).all()
    sleep_list = [int(row[0]) for row in sleep_data]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=date_list, y=sleep_list, mode='lines+markers', name='Sleep hours', line=dict(shape='hvh')))

    fig.update_layout(
        title='Sleep hours',
        xaxis_title='Time(d)',
        yaxis_title='Sleep(hours)',
    )

    # Генериране на HTML за графиката
    graph_html = fig.to_html(full_html=False)

    return render_template('graph.html', name = 'Sleep records', graph_html=graph_html)

@main.route("/give_advice", methods=["POST"])
def give_advice():
    pass

@main.route('/upload', methods=['POST'])
def upload_json():
    import json

    if 'jsonfile' not in request.files:
        return {"error": "No file part"}, 400
    
    file = request.files['jsonfile']

    db.session.query(Health).delete()

    db.session.commit()

    if file.filename == '':
        return {"error": "No selected file"}, 400

    try:
        json_data = json.load(file)

        activity = json_data.get("activity", {})
        calories_data = activity.get("calories", [])
        steps_data = activity.get("steps", [])

        heart_rate_data = json_data.get("heartRate", [])

        for entry in calories_data:
            date = datetime.strptime(entry["date"], "%Y-%m-%d")
            calories = entry["calories"]

            steps = next((s["steps"] for s in steps_data if s["date"] == entry["date"]), 0)

            hr_entry = next((h for h in heart_rate_data if h["date"] == entry["date"]), None)

            if hr_entry:
                avg_hr = hr_entry.get("average", 0.0)
            else:
                avg_hr = 0

            health_record = Health(
                userid=session['id'],
                date=date,
                steps=steps,
                heartrate=avg_hr,
                calories=calories
            )

            db.session.add(health_record)

        db.session.commit()
    
        user = User.query.filter_by(id=session['id']).first()
        name = user.firstname
        if user.profilepic and user.profilepic != "static/images/profile.jpg":
            picadres = user.profilepic.replace('static/','')
        else:
            picadres = 'images/profile.jpg'
    
        return render_template('dashboard.html', name=name, profilepic=picadres)

    except Exception as e:
        return jsonify({"error": f"Грешка: {str(e)}"}), 500
