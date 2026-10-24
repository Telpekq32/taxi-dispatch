from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.models import Ride, Customer, Driver
from app.forms import RideForm, RideRequestForm, SearchFilterForm
from config import Config

rides_bp = Blueprint("rides", __name__, url_prefix="/rides")


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@rides_bp.route("/")
@login_required
def list_rides():
    form = SearchFilterForm(request.args, meta={"csrf": False})
    page = request.args.get("page", 1, type=int)
    per_page = Config.ITEMS_PER_PAGE

    query = Ride.query

    # Non-admin sees only own rides
    if not current_user.is_admin:
        if not current_user.customer:
            flash("Клиент профилі табылмады.", "warning")
            return redirect(url_for("main.dashboard"))
        query = query.filter_by(customer_id=current_user.customer.id)

    # Search
    if form.q.data:
        q = f"%{form.q.data.strip()}%"
        query = query.filter(
            or_(
                Ride.pickup_address.ilike(q),
                Ride.dropoff_address.ilike(q),
                Ride.notes.ilike(q),
            )
        )

    # Filter by status
    if form.status.data:
        query = query.filter(Ride.status == form.status.data)

    # Filter by date range
    if form.date_from.data:
        try:
            dt_from = datetime.strptime(form.date_from.data, "%Y-%m-%d")
            query = query.filter(Ride.ride_date >= dt_from)
        except ValueError:
            pass
    if form.date_to.data:
        try:
            dt_to = datetime.strptime(form.date_to.data, "%Y-%m-%d")
            # include whole day
            dt_to = dt_to.replace(hour=23, minute=59, second=59)
            query = query.filter(Ride.ride_date <= dt_to)
        except ValueError:
            pass

    # Sort
    sort = form.sort.data or "newest"
    if sort == "oldest":
        query = query.order_by(Ride.ride_date.asc())
    elif sort == "fare_desc":
        query = query.order_by(Ride.fare.desc())
    elif sort == "fare_asc":
        query = query.order_by(Ride.fare.asc())
    else:
        query = query.order_by(Ride.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    rides = pagination.items

    return render_template(
        "rides/list.html",
        title="Тапсырыстар",
        rides=rides,
        pagination=pagination,
        form=form,
    )


@rides_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_ride():
    if current_user.is_admin:
        form = RideForm()
        form.customer_id.choices = [
            (c.id, f"{c.full_name} ({c.phone})") for c in Customer.query.order_by(Customer.full_name).all()
        ]
        form.driver_id.choices = [(0, "— Таңдалмаған —")] + [
            (d.id, f"{d.full_name} ({d.car_plate})")
            for d in Driver.query.filter(Driver.status != "offline").order_by(Driver.full_name).all()
        ]
        if form.validate_on_submit():
            driver_id = form.driver_id.data if form.driver_id.data and form.driver_id.data != 0 else None
            ride = Ride(
                customer_id=form.customer_id.data,
                driver_id=driver_id,
                pickup_address=form.pickup_address.data,
                dropoff_address=form.dropoff_address.data,
                status=form.status.data,
                ride_date=form.ride_date.data,
                fare=form.fare.data or 0.0,
                notes=form.notes.data,
            )
            if driver_id and form.status.data == "requested":
                ride.status = "assigned"
            db.session.add(ride)
            if driver_id:
                driver = db.session.get(Driver, driver_id)
                if driver:
                    driver.status = "busy"
            db.session.commit()
            flash("Тапсырыс сәтті құрылды.", "success")
            return redirect(url_for("rides.list_rides"))
    else:
        # Ordinary user requests a ride
        if not current_user.customer:
            flash("Клиент профилі жоқ. Админге хабарласыңыз.", "warning")
            return redirect(url_for("main.dashboard"))
        form = RideRequestForm()
        if form.validate_on_submit():
            ride = Ride(
                customer_id=current_user.customer.id,
                pickup_address=form.pickup_address.data,
                dropoff_address=form.dropoff_address.data,
                status="requested",
                ride_date=form.ride_date.data,
                notes=form.notes.data,
            )
            db.session.add(ride)
            db.session.commit()
            flash("Тапсырысыңыз қабылданды! Жүргізуші тағайындалады.", "success")
            return redirect(url_for("rides.list_rides"))

    return render_template(
        "rides/form.html",
        title="Жаңа тапсырыс",
        form=form,
        is_admin=current_user.is_admin,
    )


@rides_bp.route("/<int:id>")
@login_required
def detail_ride(id):
    ride = db.session.get(Ride, id) or abort(404)
    if not current_user.is_admin:
        if not current_user.customer or ride.customer_id != current_user.customer.id:
            abort(403)
    available_drivers = []
    if current_user.is_admin:
        available_drivers = (
            Driver.query.filter(Driver.status.in_(["available", "busy"]))
            .order_by(Driver.status.asc(), Driver.full_name.asc())
            .all()
        )
    return render_template(
        "rides/detail.html",
        title=f"Тапсырыс #{ride.id}",
        ride=ride,
        available_drivers=available_drivers,
    )


@rides_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_ride(id):
    admin_required()
    ride = db.session.get(Ride, id) or abort(404)
    form = RideForm(obj=ride)
    form.customer_id.choices = [
        (c.id, f"{c.full_name} ({c.phone})") for c in Customer.query.order_by(Customer.full_name).all()
    ]
    form.driver_id.choices = [(0, "— Таңдалмаған —")] + [
        (d.id, f"{d.full_name} ({d.car_plate})")
        for d in Driver.query.order_by(Driver.full_name).all()
    ]
    if request.method == "GET":
        form.driver_id.data = ride.driver_id or 0
        if ride.ride_date:
            form.ride_date.data = ride.ride_date

    if form.validate_on_submit():
        old_driver_id = ride.driver_id
        new_driver_id = form.driver_id.data if form.driver_id.data and form.driver_id.data != 0 else None

        ride.customer_id = form.customer_id.data
        ride.driver_id = new_driver_id
        ride.pickup_address = form.pickup_address.data
        ride.dropoff_address = form.dropoff_address.data
        ride.status = form.status.data
        ride.ride_date = form.ride_date.data
        ride.fare = form.fare.data or 0.0
        ride.notes = form.notes.data

        # Update driver statuses
        if old_driver_id and old_driver_id != new_driver_id:
            old_d = db.session.get(Driver, old_driver_id)
            if old_d:
                old_d.status = "available"
        if new_driver_id:
            new_d = db.session.get(Driver, new_driver_id)
            if new_d and ride.status in ("assigned", "in_progress"):
                new_d.status = "busy"
            elif new_d and ride.status in ("done", "cancelled"):
                new_d.status = "available"

        if ride.status in ("done", "cancelled") and ride.driver_id:
            d = db.session.get(Driver, ride.driver_id)
            if d:
                d.status = "available"

        db.session.commit()
        flash("Тапсырыс жаңартылды.", "success")
        return redirect(url_for("rides.detail_ride", id=ride.id))

    return render_template(
        "rides/form.html",
        title=f"Тапсырысты өңдеу #{ride.id}",
        form=form,
        is_admin=True,
        ride=ride,
    )


@rides_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_ride(id):
    admin_required()
    ride = db.session.get(Ride, id) or abort(404)
    if ride.driver_id:
        driver = db.session.get(Driver, ride.driver_id)
        if driver:
            driver.status = "available"
    db.session.delete(ride)
    db.session.commit()
    flash("Тапсырыс жойылды.", "info")
    return redirect(url_for("rides.list_rides"))


@rides_bp.route("/<int:id>/assign/<int:driver_id>", methods=["POST"])
@login_required
def assign_driver(id, driver_id):
    admin_required()
    ride = db.session.get(Ride, id) or abort(404)
    driver = db.session.get(Driver, driver_id) or abort(404)
    if ride.status not in ("requested", "assigned"):
        flash("Бұл тапсырысқа жүргізуші тағайындауға болмайды.", "warning")
        return redirect(url_for("rides.detail_ride", id=id))

    if ride.driver_id:
        old = db.session.get(Driver, ride.driver_id)
        if old:
            old.status = "available"

    ride.driver_id = driver.id
    ride.status = "assigned"
    driver.status = "busy"
    db.session.commit()
    flash(f"Жүргізуші {driver.full_name} тағайындалды.", "success")
    return redirect(url_for("rides.detail_ride", id=id))


@rides_bp.route("/<int:id>/status/<status>", methods=["POST"])
@login_required
def change_status(id, status):
    """Admin: бір батырмамен статус өзгерту (assigned → in_progress → done / cancelled)."""
    admin_required()
    ride = db.session.get(Ride, id) or abort(404)
    allowed = {
        "in_progress": ("assigned",),
        "done": ("assigned", "in_progress"),
        "cancelled": ("requested", "assigned", "in_progress"),
        "assigned": ("requested",),
    }
    if status not in allowed:
        flash("Жарамсыз статус.", "danger")
        return redirect(url_for("rides.detail_ride", id=id))
    if ride.status not in allowed[status]:
        flash(f"Қазіргі статус ({ride.status}) бұл әрекетке жарамайды.", "warning")
        return redirect(url_for("rides.detail_ride", id=id))

    if status == "in_progress" and not ride.driver_id:
        flash("Алдымен жүргізуші тағайындаңыз.", "warning")
        return redirect(url_for("rides.detail_ride", id=id))

    ride.status = status

    if status in ("done", "cancelled") and ride.driver_id:
        driver = db.session.get(Driver, ride.driver_id)
        if driver:
            driver.status = "available"

    if status == "in_progress" and ride.driver_id:
        driver = db.session.get(Driver, ride.driver_id)
        if driver:
            driver.status = "busy"

    db.session.commit()

    messages = {
        "in_progress": "Сапар басталды — жүргізуші жолда.",
        "done": "Сапар аяқталды. Жүргізуші бос болды.",
        "cancelled": "Тапсырыс болдырылмады.",
        "assigned": "Жүргізуші тағайындалды.",
    }
    flash(messages.get(status, "Статус жаңартылды."), "success")
    return redirect(url_for("rides.detail_ride", id=id))


@rides_bp.route("/<int:id>/assign", methods=["POST"])
@login_required
def assign_driver_form(id):
    """Admin: формадан жүргізуші таңдап тағайындау."""
    admin_required()
    ride = db.session.get(Ride, id) or abort(404)
    driver_id = request.form.get("driver_id", type=int)
    if not driver_id:
        flash("Жүргізуші таңдаңыз.", "warning")
        return redirect(url_for("rides.detail_ride", id=id))
    return assign_driver(id, driver_id)
