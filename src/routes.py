from flask import Blueprint, render_template, request, redirect, url_for

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
        # Вземаме данните от формата
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # TODO: Добави логика за запис в базата данни тук
        print(f"New user: {username}, {email}")
        print("Registration successful!")

    return render_template('login.html')

@main.route("/login_action", methods=['POST'])
def login_action():
    if request.method != 'POST':
        return redirect(url_for('main.login', message='Invalid method'))

    if request.form['username'] == 'admin' and request.form['password'] == 'admin':
        username = request.form['username']
        return redirect(url_for('main.user_page', name=username, token='123456'))
    else:
        return redirect(url_for('main.login', message='Invalid username or password'))

@main.route("/login")
def login():
    message = request.args.get('message', None)
    return render_template('login.html', title='Login', message=message)

@main.route("/user_page")
def user_page():
    return render_template('in_app.html')

@main.route('/logout')
def logout():
    return redirect(url_for('main.login'))
