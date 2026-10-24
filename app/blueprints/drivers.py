from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Driver, Ride
from app.forms import DriverForm
from app.utils import save_upload, delete_upload
from config import Config

drivers_bp = Blueprint("drivers", __name__, url_prefix="/drivers")


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@drivers_bp.route("/")
@login_required
def list_drivers():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "")

    query = Driver.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Driver.full_name.ilike(like),
                Driver.phone.ilike(like),
                Driver.car_plate.ilike(like),
                Driver.license_number.ilike(like),
            )
        )
    if status:
        query = query.filter_by(status=status)

    query = query.order_by(Driver.full_name)
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    drivers = pagination.items

    return render_template(
        "drivers/list.html",
        title="Жүргізушілер",
        drivers=drivers,
        pagination=pagination,
        q=q,
        status=status,
    )


@drivers_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_driver():
    admin_required()
    form = DriverForm()
    if form.validate_on_submit():
        photo_name = save_upload(form.photo.data) if form.photo.data else None
        driver = Driver(
            full_name=form.full_name.data,
            phone=form.phone.data,
            license_number=form.license_number.data,
            car_model=form.car_model.data,
            car_plate=form.car_plate.data,
            status=form.status.data,
            photo=photo_name,
        )
        db.session.add(driver)
        db.session.commit()
        flash("Жүргізуші қосылды.", "success")
        return redirect(url_for("drivers.list_drivers"))
    return render_template("drivers/form.html", title="Жаңа жүргізуші", form=form)


@drivers_bp.route("/<int:id>")
@login_required
def detail_driver(id):
    driver = db.session.get(Driver, id) or abort(404)
    recent_rides = driver.rides.order_by(Ride.created_at.desc()).limit(10).all()
    return render_template(
        "drivers/detail.html",
        title=driver.full_name,
        driver=driver,
        recent_rides=recent_rides,
    )


@drivers_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_driver(id):
    admin_required()
    driver = db.session.get(Driver, id) or abort(404)
    form = DriverForm(
        obj=driver,
        original_license=driver.license_number,
        original_plate=driver.car_plate,
    )
    if form.validate_on_submit():
        driver.full_name = form.full_name.data
        driver.phone = form.phone.data
        driver.license_number = form.license_number.data
        driver.car_model = form.car_model.data
        driver.car_plate = form.car_plate.data
        driver.status = form.status.data
        if form.photo.data:
            delete_upload(driver.photo)
            driver.photo = save_upload(form.photo.data)
        db.session.commit()
        flash("Жүргізуші жаңартылды.", "success")
        return redirect(url_for("drivers.detail_driver", id=driver.id))
    return render_template(
        "drivers/form.html",
        title=f"Өңдеу: {driver.full_name}",
        form=form,
        driver=driver,
    )


@drivers_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_driver(id):
    admin_required()
    driver = db.session.get(Driver, id) or abort(404)
    from app.models import Ride
    active = Ride.query.filter(
        Ride.driver_id == driver.id,
        Ride.status.in_(["requested", "assigned", "in_progress"]),
    ).count()
    if active:
        flash("Белсенді тапсырыстары бар жүргізушіні жоюға болмайды.", "danger")
        return redirect(url_for("drivers.detail_driver", id=id))
    delete_upload(driver.photo)
    db.session.delete(driver)
    db.session.commit()
    flash("Жүргізуші жойылды.", "info")
    return redirect(url_for("drivers.list_drivers"))
