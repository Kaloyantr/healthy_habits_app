import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from src import db
from src.models import User, Health
from werkzeug.utils import secure_filename
from src.utils import allowed_file
import plotly.graph_objects as go
from datetime import datetime
from plyer import notification
import bcrypt
import json

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template('index.html')

@main.route("/register")
def register():
    return render_template('register.html')

from sqlalchemy.exc import IntegrityError
from flask import session, redirect, url_for, flash

@main.route("/register_action", methods=['POST'])
def register_action():
    if request.method == 'POST':
        if 'firstname' not in request.form or 'surname' not in request.form:
            session['message'] = {'text': "Missing required fields.", 'type': 'error'}
            return redirect(url_for('main.register'))

        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        firstname = request.form['firstname']
        surname = request.form['surname']
        profilepic = "static/images/profile.jpg"
        
        salt = bcrypt.gensalt()  # Генериране на сол
        hashed_password = bcrypt.hashpw(password, salt)  # Хеширане на паролата

        existing_user = db.session.query(User).filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                notification.notify(
                title="Health Habits",
                message="The username is taken.",
                app_icon='sameName.ico',
                timeout=5
                )
            elif existing_user.email == email:
                notification.notify(
                title="Health Habits",
                message="The email is taken.",
                app_icon='sameName.ico',
                timeout=5
                )
            return redirect(url_for('main.register'))

        new_user = User(username=username, email=email, firstname=firstname, surname=surname, password=hashed_password, profilepic=profilepic)

        try:
            db.session.add(new_user)
            db.session.commit()
            session['message'] = {'text': "Registration successful!", 'type': 'success'}
            return redirect(url_for('main.login'))
        except IntegrityError:
            db.session.rollback()
            session['message'] = {'text': "There was an error with the registration. Please try again.", 'type': 'error'}
            return redirect(url_for('main.register'))

    return render_template('register.html')



@main.route("/login_action", methods=['POST'])
def login_action():
    if request.method != 'POST':
        return redirect(url_for('main.login', message='Invalid method'))
    user = User.query.filter_by(username=request.form['username']).first()

    if user and bcrypt.checkpw(request.form['password'].encode('utf-8'), user.password):
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
            user_id = session.get('id')
            user_health_data = Health.query.filter_by(userid = user_id).all()
            for data in user_health_data:
                db.session.delete(data) 
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
    specific_user_id = session('id')
    
    dates_data = db.session.query(Health.date).filter(Health.user_id == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    steps_data = db.session.query(Health.steps).filter(Health.user_id == specific_user_id).all()
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
    specific_user_id = session('id')
    
    dates_data = db.session.query(Health.date).filter(Health.user_id == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    pulse_data = db.session.query(Health.heartrate).filter(Health.user_id == specific_user_id).all()
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
    specific_user_id = session('id')
    
    dates_data = db.session.query(Health.date).filter(Health.user_id == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    stress_data = db.session.query(Health.stress).filter(Health.user_id == specific_user_id).all()
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
    specific_user_id = session('id')
    
    dates_data = db.session.query(Health.date).filter(Health.user_id == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    calories_data = db.session.query(Health.calories).filter(Health.user_id == specific_user_id).all()
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
    specific_user_id = session('id')
    dates_data = db.session.query(Health.date).filter(Health.user_id == specific_user_id).all()
    date_list = [row[0].date() for row in dates_data]
    sleep_data = db.session.query(Health.sleephours).filter(Health.user_id == specific_user_id).all()
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

@main.route("/give_advice", methods=["GET"])
def give_advice():
    user_id = session.get('id')  # Получаваме ID от сесията
    
    if not user_id:
        return "Няма данни за потребителя", 400  # Ако няма потребител в сесията
    
    user = User.query.filter_by(id=user_id).first()

    # Ако няма данни за потребителя
    if not user:
        return "Няма данни за потребителя", 400
    
    # Получаване на данни за стъпки и калории от базата
    steps_data = db.session.query(Health.sleephours).filter(Health.userid == user_id).all()
    steps_list = [row[0] for row in steps_data]  # Преобразуваме резултата в списък
    av_steps = sum(steps_list) / len(steps_list) if len(steps_list) > 0 else 0  # Средна стойност за стъпките
    
    calories_data = db.session.query(Health.calories).filter(Health.userid == user_id).all()
    calories_list = [row[0] for row in calories_data]  # Преобразуваме резултата в списък
    av_cal = sum(calories_list) / len(calories_list) if len(calories_list) > 0 else 0  # Средна стойност за калориите
    
    weight = user.weight if user.weight else 72  # По подразбиране стойност
    height = user.height if user.height else 1.75  # По подразбиране стойност
    age = user.age if user.age else 25  # По подразбиране стойност
    
    A = (av_steps / 10000) + (av_cal / 2500)
    BMI = weight / (height ** 2)
    E = 100 / BMI
    
    health_score = (A + E) / 2
    
    if health_score > 80:
        advice = "Вашето здраве е отлично! Продължавайте с активния начин на живот. Поддържайте стреса на ниско ниво и се опитайте да запазите здравословното си тегло."
    elif 50 < health_score <= 80:
        advice = "Здравето ви е добро, но има място за подобрения. Помислете за увеличаване на физическата активност, намаляване на стреса и подобряване на съня."
    else:
        advice = "Вашето здравословно състояние не е на ниво, което бихте искали. Препоръчваме ви да се консултирате с лекар за съвети, да започнете с по-здравословен начин на живот, да намалите стреса и да увеличите физическата активност."
    
    return redirect(url_for('main.give_advice', advice=advice))


@main.route('/upload', methods=['POST'])
def upload_json():
    if 'jsonfile' not in request.files:
        return {"error": "No file part"}, 400
    
    file = request.files['jsonfile']
    
    user_id = session.get('id')
    
    if file.filename == '':
        return {"error": "No selected file"}, 400

    try:
        json_data = json.load(file)

        activity = json_data.get("activity", {})
        calories_data = activity.get("calories", [])
        steps_data = activity.get("steps", [])
        heart_rate_data = json_data.get("heartRate", [])

        # Премахване на старите данни на потребителя преди да добавим новите
        user_health_data = Health.query.filter_by(userid=user_id).all()
        for data in user_health_data:
            db.session.delete(data)

        # Добавяне на новите данни в базата
        for entry in calories_data:
            date = datetime.strptime(entry["date"], "%Y-%m-%d")
            calories = entry["calories"]

            # Извличане на съответните стъпки за същата дата
            steps = next((s["steps"] for s in steps_data if s["date"] == entry["date"]), 0)

            # Извличане на среден пулс за същата дата
            hr_entry = next((h for h in heart_rate_data if h["date"] == entry["date"]), None)
            avg_hr = hr_entry.get("average", 0.0) if hr_entry else 0

            # Проверка дали съществува запис с тази дата
            existing_record = Health.query.filter_by(userid=user_id, date=date).first()

            if existing_record:
                # Ако съществува запис, актуализираме данните
                existing_record.steps = steps
                existing_record.heartrate = avg_hr
                existing_record.calories = calories
            else:
                # Ако не съществува запис, създаваме нов
                health_record = Health(
                    userid=user_id,
                    date=date,
                    steps=steps,
                    heartrate=avg_hr,
                    calories=calories
                )
                db.session.add(health_record)

        db.session.commit()

        # Вземане на информация за потребителя
        user = User.query.filter_by(id=user_id).first()
        name = user.firstname
        if user.profilepic and user.profilepic != "static/images/profile.jpg":
            picadres = user.profilepic.replace('static/','')
        else:
            picadres = 'images/profile.jpg'

        return render_template('dashboard.html', name=name, profilepic=picadres)

    except Exception as e:
        return jsonify({"error": f"Грешка: {str(e)}"}), 500

@main.route('/metrics', methods=['GET', 'POST'], endpoint='metrics')
def metrics():
    # Проверка за наличност на потребител в сесията
    username = session.get('username')
    if not username:
        flash("Моля, влезте в профила си.")
        return redirect(url_for('main.login'))
    
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("Потребителят не е намерен!")
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        # Извличане на данните от формата
        height = request.form.get('height')
        weight = request.form.get('weight')
        age = request.form.get('age')
        gender = request.form.get('gender')
        
        try:
            user.height = float(height)
            user.weight = float(weight)
            user.age = int(age)
        except ValueError:
            flash("Моля, въведете валидни стойности за ръст, тегло и възраст.")
            return redirect(url_for('main.metrics'))
        
        user.gender = gender
        
        db.session.commit()
        flash("Мерките са запазени успешно!")
        return redirect(url_for('main.dashboard'))
    
    # Ако е GET заявка, рендираме формата с предварително попълнени данни от потребителя
    return render_template('metrics.html', user=user)
