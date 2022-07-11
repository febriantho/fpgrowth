from flask import Blueprint, flash, redirect, url_for, render_template, request
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Berhasil Login!' , category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home', page="home", user=current_user))
            else:
                flash('Password Salah!' , category='error')
        else:
            flash('Email Salah!' , category='error')

    return render_template('login.html')

@auth.route('/register-user', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email sudah ada!' , category='error')
        elif len(name) < 1:
            flash('nama harus diisi' , category='error')
        elif len(email) < 1:
            flash('Email harus diisi' , category='error')
        elif len(password1) < 8:
            flash('password kurang dari 8 kaerakter' , category='error')
        elif password1 != password2:
            flash('re-type password tidak sesuai dengan password' , category='error')
        else:
            new_user = User(name=name, email=email, password=generate_password_hash(password1, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            flash('Akun berhasil terdaftar!', category='success')


    return render_template('register.html')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
