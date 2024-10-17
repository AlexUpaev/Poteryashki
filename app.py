import base64
from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy  # type: ignore
import sys
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///poteryashki.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Us_user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    N_name = db.Column(db.String(20), nullable=False)
    Surname = db.Column(db.String(20), nullable=False)
    Email = db.Column(db.String(50), unique=True, nullable=False)  # Обеспечиваем уникальность email
    Password = db.Column(db.String(128), nullable=False)  # Увеличен размер для хранения хешированного пароля
    Role = db.Column(db.String(20), nullable=False)

class Midding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Photo = db.Column(db.Text, nullable=False)
    Name = db.Column(db.String(20), nullable=False)
    Surname = db.Column(db.String(20), nullable=False)
    Patronymic = db.Column(db.String(20), nullable=True)
    DataOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.String(10), nullable=False)
    Description = db.Column(db.Text, nullable=True)
    DataOfLastAppearance = db.Column(db.Date, nullable=False)
    PlaceOfLastAppearance = db.Column(db.String(50), nullable=False)

@app.route("/zayavka", methods=['POST', 'GET'])
def zayavka():
    if request.method == 'POST':
        try:
            # Обработка файла фото
            photo_file = request.files.get('Photo')
            photo = base64.b64encode(photo_file.read()).decode('utf-8') if photo_file else None

            # Получение данных формы
            name = request.form['Name']
            surname = request.form['Surname']
            patronymic = request.form['Patronymic']
            data_of_birth = request.form['DataOfBirth']
            gender = request.form['Gender']
            description = request.form['Description']
            data_of_last_appearance = request.form['DataOfLastAppearance']
            place_of_last_appearance = request.form['PlaceOfLastAppearance']

            # Создание объекта заявки
            post = Midding(
                Photo=photo, 
                Name=name, 
                Surname=surname, 
                Patronymic=patronymic,
                DataOfBirth=datetime.strptime(data_of_birth, '%Y-%m-%d'),
                Gender=gender, 
                Description=description,
                DataOfLastAppearance=datetime.strptime(data_of_last_appearance, '%Y-%m-%d'),
                PlaceOfLastAppearance=place_of_last_appearance
            )

            # Добавление заявки в базу данных
            db.session.add(post)
            db.session.commit()
            flash('Заявка успешно добавлена!', 'success')
            return redirect('/')
        
        except Exception as e:
            db.session.rollback()  # Откат изменений при ошибке
            flash(f'При добавлении заявки произошла ошибка: {str(e)}', 'danger')
            return redirect('/zayavka')
    else:
        return render_template('zayavka.html')

@app.route("/index")
@app.route("/")  # Обработчик
def index():
    return render_template("index.html")

@app.route("/spisock")
def spisock():
    posts = Midding.query.all()
    return render_template('spisock.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route("/register", methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form['Email']
        password = request.form['Password']
        confirm_password = request.form['confirm_password']
        
        # Проверка, совпадают ли пароли
        if password != confirm_password:
            flash('Пароли не совпадают. Пожалуйста, попробуйте снова.', 'danger')
            return render_template('register.html', name=request.form['N_name'], surname=request.form['Surname'],
                                   email=email, role=request.form['Role'])
        
        # Проверка, существует ли уже пользователь с таким email
        existing_user = Us_user.query.filter_by(Email=email).first()
        if existing_user:
            flash('Аккаунт с данным email уже зарегистрирован.', 'danger')
            return render_template('register.html', name=request.form['N_name'], surname=request.form['Surname'],
                                   email=email, role=request.form['Role'])

        # Если пароли совпадают и email уникальный, продолжаем регистрацию
        try:
            name = request.form['N_name']
            surname = request.form['Surname']
            role = request.form['Role']
            
            # Хеширование пароля перед сохранением
            hashed_password = generate_password_hash(password)
            
            # Создание нового пользователя
            new_user = Us_user(
                N_name=name,
                Surname=surname,
                Email=email,
                Password=hashed_password,
                Role=role
            )
            
            # Добавление пользователя в базу данных
            db.session.add(new_user)
            db.session.commit()
            
            flash('Регистрация прошла успешно!', 'success')
            return redirect('/')
        except Exception as e:
            db.session.rollback()  # Откат при ошибке
            flash(f'Ошибка при регистрации: {str(e)}', 'danger')
            return render_template('register.html', name=request.form['N_name'], surname=request.form['Surname'],
                                   email=email, role=request.form['Role'])
    else:
        return render_template('register.html')

if __name__ == "__main__":  # Запуск на локальном устройстве
    app.run(debug=True)  # Отображение ошибок
