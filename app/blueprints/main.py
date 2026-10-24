from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Ride, Driver, Customer
from sqlalchemy import func
from app import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    stats = None
    if current_user.is_authenticated and current_user.is_admin:
        stats = {
            "rides_total": Ride.query.count(),
            "rides_requested": Ride.query.filter_by(status="requested").count(),
            "rides_done": Ride.query.filter_by(status="done").count(),
            "drivers": Driver.query.count(),
            "customers": Customer.query.count(),
            "available_drivers": Driver.query.filter_by(status="available").count(),
        }
    return render_template("index.html", title="Басты бет", stats=stats)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.is_admin:
        recent_rides = (
            Ride.query.order_by(Ride.created_at.desc()).limit(8).all()
        )
        pending = Ride.query.filter_by(status="requested").order_by(Ride.created_at.asc()).all()
        in_progress = Ride.query.filter(Ride.status.in_(["assigned", "in_progress"])).count()
        return render_template(
            "admin/dashboard.html",
            title="Админ панелі",
            recent_rides=recent_rides,
            pending=pending,
            in_progress=in_progress,
        )
    # Ordinary user
    customer = current_user.customer
    my_rides = []
    if customer:
        my_rides = (
            Ride.query.filter_by(customer_id=customer.id)
            .order_by(Ride.created_at.desc())
            .limit(10)
            .all()
        )
    return render_template(
        "dashboard.html",
        title="Менің тапсырыстарым",
        my_rides=my_rides,
        customer=customer,
    )
