from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urljoin, urlparse
from app import db
from app.models import User, Customer
from app.forms import RegistrationForm, LoginForm

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data.lower(),
            role="user",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # get user.id

        customer = Customer(
            user_id=user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
        )
        db.session.add(customer)
        db.session.commit()
        flash("Тіркелу сәтті аяқталды! Енді кіре аласыз.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form, title="Тіркелу")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Пайдаланушы аты немесе құпия сөз қате.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user, remember=form.remember.data)
        next_page = request.args.get("next")
        if next_page:
            target = urlparse(urljoin(request.host_url, next_page))
            if target.scheme not in {"http", "https"} or target.netloc != request.host:
                next_page = None
        flash(f"Қош келдіңіз, {user.username}!", "success")
        return redirect(next_page or url_for("main.index"))
    return render_template("auth/login.html", form=form, title="Кіру")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Сіз жүйеден шықтыңыз.", "info")
    return redirect(url_for("main.index"))
