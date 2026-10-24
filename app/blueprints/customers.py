from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from app import db
from app.models import Customer, Ride
from app.forms import CustomerForm
from config import Config

customers_bp = Blueprint("customers", __name__, url_prefix="/customers")


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@customers_bp.route("/")
@login_required
def list_customers():
    admin_required()
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()

    query = Customer.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(
                Customer.full_name.ilike(like),
                Customer.phone.ilike(like),
                Customer.address.ilike(like),
            )
        )
    query = query.order_by(Customer.full_name)
    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)

    return render_template(
        "customers/list.html",
        title="Клиенттер",
        customers=pagination.items,
        pagination=pagination,
        q=q,
    )


@customers_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_customer():
    admin_required()
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            full_name=form.full_name.data,
            phone=form.phone.data,
            address=form.address.data,
        )
        db.session.add(customer)
        db.session.commit()
        flash("Клиент қосылды.", "success")
        return redirect(url_for("customers.list_customers"))
    return render_template("customers/form.html", title="Жаңа клиент", form=form)


@customers_bp.route("/<int:id>")
@login_required
def detail_customer(id):
    customer = db.session.get(Customer, id) or abort(404)
    if not current_user.is_admin:
        if not current_user.customer or current_user.customer.id != customer.id:
            abort(403)
    recent_rides = (
        Ride.query.filter_by(customer_id=customer.id)
        .order_by(Ride.created_at.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "customers/detail.html",
        title=customer.full_name,
        customer=customer,
        recent_rides=recent_rides,
    )


@customers_bp.route("/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_customer(id):
    customer = db.session.get(Customer, id) or abort(404)
    # Admin or own profile
    if not current_user.is_admin:
        if not current_user.customer or current_user.customer.id != customer.id:
            abort(403)
    form = CustomerForm(obj=customer)
    if form.validate_on_submit():
        customer.full_name = form.full_name.data
        customer.phone = form.phone.data
        customer.address = form.address.data
        db.session.commit()
        flash("Клиент жаңартылды.", "success")
        return redirect(url_for("customers.detail_customer", id=customer.id))
    return render_template(
        "customers/form.html",
        title=f"Өңдеу: {customer.full_name}",
        form=form,
        customer=customer,
    )


@customers_bp.route("/<int:id>/delete", methods=["POST"])
@login_required
def delete_customer(id):
    admin_required()
    customer = db.session.get(Customer, id) or abort(404)
    active = Ride.query.filter(
        Ride.customer_id == customer.id,
        Ride.status.in_(["requested", "assigned", "in_progress"]),
    ).count()
    if active:
        flash("Белсенді тапсырыстары бар клиентті жоюға болмайды.", "danger")
        return redirect(url_for("customers.detail_customer", id=id))
    db.session.delete(customer)
    db.session.commit()
    flash("Клиент жойылды.", "info")
    return redirect(url_for("customers.list_customers"))
