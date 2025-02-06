from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from src import db
from src.models import User
from werkzeug.security import generate_password_hash
from src.utils import allowed_file, get_secure_filename
import os

# Създаване на Blueprint за организиране на маршрутите
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
        return redirect(url_for('main.dashboard', username=username, token='123456'))
    else:
        return redirect(url_for('main.login', message='Invalid username or password'))

@main.route("/login")
def login():
    message = request.args.get('message', None)
    session['logged_in'] = True
    return render_template('login.html', title='Login', message=message)

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

@main.route('/dashboard/profile')
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

from flask import flash, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename
import os

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

