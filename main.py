import os

from flask import Flask, url_for, render_template, request
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.exceptions import abort
from werkzeug.utils import redirect

from data import db_session
from data.users import User
from data.wallpapers import Wallpapers
from forms import *

from urllib.parse import unquote


app = Flask(__name__)
app.config['SECRET_KEY'] = 'njfpFmfFYn7DFN8h6F0'
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    session = db_session.create_session()
    wps = session.query(Wallpapers)
    return render_template('index.html', title='Главная', wps=wps[::-1])


@app.route('/create_wp', methods=['GET', 'POST'])
def create_wp():
    if request.method == 'POST':
        session = db_session.create_session()
        wps = Wallpapers()
        wps.title = unquote(request.form['title'])
        wps.content = unquote(request.form['content'])
        current_user.wps.append(wps)
        session.merge(current_user)
        session.commit()
    return render_template('create_wp.html', title='Создать обои')


@app.route('/account')
def account():
    session = db_session.create_session()
    if current_user.is_authenticated:
        wps = session.query(Wallpapers).filter(Wallpapers.user == current_user)
        return render_template('account.html', title='Аккаунт', wps=wps[::-1])
    else:
        return render_template('account.html', title='Аккаунт')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        session = db_session.create_session()
        if session.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        user = session.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/account")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/wp_delete/<int:id>', methods=['GET', 'POST'])
@login_required
def wp_delete(id):
    session = db_session.create_session()
    wps = session.query(Wallpapers).filter(Wallpapers.id == id,
                                      Wallpapers.user == current_user).first()
    if wps:
        session.delete(wps)
        session.commit()
    else:
        abort(404)
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/WPMaker.sqlite")
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)


if __name__ == '__main__':
    main()
