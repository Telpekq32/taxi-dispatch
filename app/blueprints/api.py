from datetime import datetime, timezone
import math
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.models import Ride, Driver, Customer

api_bp = Blueprint("api", __name__)


def ride_to_dict(ride: Ride) -> dict:
    return {
        "id": ride.id,
        "customer_id": ride.customer_id,
        "customer_name": ride.customer.full_name if ride.customer else None,
        "driver_id": ride.driver_id,
        "driver_name": ride.driver.full_name if ride.driver else None,
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "status": ride.status,
        "ride_date": ride.ride_date.isoformat() if ride.ride_date else None,
        "fare": ride.fare,
        "notes": ride.notes,
        "created_at": ride.created_at.isoformat() if ride.created_at else None,
    }


def driver_to_dict(d: Driver) -> dict:
    return {
        "id": d.id,
        "full_name": d.full_name,
        "phone": d.phone,
        "license_number": d.license_number,
        "car_model": d.car_model,
        "car_plate": d.car_plate,
        "status": d.status,
        "photo": d.photo,
    }


def customer_to_dict(c: Customer) -> dict:
    return {
        "id": c.id,
        "full_name": c.full_name,
        "phone": c.phone,
        "address": c.address,
    }


def _valid_address(value):
    return isinstance(value, str) and 5 <= len(value.strip()) <= 200


def _active_rides_for_driver(driver_id, exclude_ride_id=None):
    query = Ride.query.filter(
        Ride.driver_id == driver_id,
        Ride.status.in_(("assigned", "in_progress")),
    )
    if exclude_ride_id is not None:
        query = query.filter(Ride.id != exclude_ride_id)
    return query.count()


def _sync_driver_status(driver_id):
    if driver_id is None:
        return
    driver = db.session.get(Driver, driver_id)
    if driver and driver.status != "offline":
        driver.status = "busy" if _active_rides_for_driver(driver_id) else "available"


# ---------- RIDES ----------
@api_bp.route("/rides", methods=["GET"])
@login_required
def api_rides_list():
    """GET /api/rides — list rides (admin: all, user: own). Supports ?status=&page="""
    status = request.args.get("status")
    if status and status not in Ride.STATUS_CHOICES:
        return jsonify({"error": f"Invalid status. Allowed: {Ride.STATUS_CHOICES}"}), 400
    page = request.args.get("page", 1, type=int)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 100)

    query = Ride.query
    if not current_user.is_admin:
        if not current_user.customer:
            return jsonify({"error": "No customer profile"}), 403
        query = query.filter_by(customer_id=current_user.customer.id)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Ride.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify(
        {
            "items": [ride_to_dict(r) for r in pagination.items],
            "total": pagination.total,
            "page": pagination.page,
            "pages": pagination.pages,
        }
    )


@api_bp.route("/rides", methods=["POST"])
@login_required
def api_rides_create():
    """POST /api/rides — create a ride request"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400
    pickup = data.get("pickup_address")
    dropoff = data.get("dropoff_address")
    if not _valid_address(pickup) or not _valid_address(dropoff):
        return jsonify({"error": "pickup_address and dropoff_address must be 5–200 characters"}), 400
    pickup, dropoff = pickup.strip(), dropoff.strip()
    notes = data.get("notes")
    if notes is not None and (not isinstance(notes, str) or len(notes) > 500):
        return jsonify({"error": "notes must be a string of at most 500 characters"}), 400
    try:
        fare = float(data.get("fare", 0) or 0)
    except (TypeError, ValueError):
        return jsonify({"error": "fare must be a number between 0 and 1000000"}), 400
    if not math.isfinite(fare) or not 0 <= fare <= 1_000_000:
        return jsonify({"error": "fare must be a number between 0 and 1000000"}), 400

    if current_user.is_admin:
        customer_id = data.get("customer_id")
        if not customer_id:
            return jsonify({"error": "customer_id required for admin"}), 400
        if not isinstance(customer_id, int) or isinstance(customer_id, bool):
            return jsonify({"error": "customer_id must be an integer"}), 400
        customer = db.session.get(Customer, customer_id)
        if not customer:
            return jsonify({"error": "Customer not found"}), 404
    else:
        if not current_user.customer:
            return jsonify({"error": "No customer profile"}), 403
        customer_id = current_user.customer.id

    ride_date = datetime.now(timezone.utc)
    if data.get("ride_date"):
        if not isinstance(data["ride_date"], str):
            return jsonify({"error": "ride_date must be a valid ISO 8601 date"}), 400
        try:
            ride_date = datetime.fromisoformat(data["ride_date"].replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return jsonify({"error": "ride_date must be a valid ISO 8601 date"}), 400

    ride = Ride(
        customer_id=customer_id,
        pickup_address=pickup,
        dropoff_address=dropoff,
        status="requested",
        ride_date=ride_date,
        notes=notes,
        fare=fare,
    )
    db.session.add(ride)
    db.session.commit()
    return jsonify(ride_to_dict(ride)), 201


@api_bp.route("/rides/<int:id>", methods=["GET"])
@login_required
def api_ride_detail(id):
    ride = db.session.get(Ride, id)
    if not ride:
        return jsonify({"error": "Not found"}), 404
    if not current_user.is_admin:
        if not current_user.customer or ride.customer_id != current_user.customer.id:
            return jsonify({"error": "Forbidden"}), 403
    return jsonify(ride_to_dict(ride))


@api_bp.route("/rides/<int:id>", methods=["PUT", "PATCH"])
@login_required
def api_ride_update(id):
    """PUT/PATCH /api/rides/<id> — update status / assign driver (admin)"""
    if not current_user.is_admin:
        return jsonify({"error": "Admin only"}), 403
    ride = db.session.get(Ride, id)
    if not ride:
        return jsonify({"error": "Not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "A JSON object is required"}), 400
    old_driver_id = ride.driver_id
    if "status" in data:
        if data["status"] not in Ride.STATUS_CHOICES:
            return jsonify({"error": f"Invalid status. Allowed: {Ride.STATUS_CHOICES}"}), 400
        valid_next = {
            "requested": ("requested", "assigned", "cancelled"),
            "assigned": ("assigned", "in_progress", "done", "cancelled"),
            "in_progress": ("in_progress", "done", "cancelled"),
            "done": ("done",),
            "cancelled": ("cancelled",),
        }
        if data["status"] not in valid_next[ride.status]:
            return jsonify({"error": f"Cannot change status from {ride.status} to {data['status']}"}), 400
        ride.status = data["status"]
    if "driver_id" in data:
        driver_id = data["driver_id"]
        if driver_id is not None and (not isinstance(driver_id, int) or isinstance(driver_id, bool)):
            return jsonify({"error": "driver_id must be an integer or null"}), 400
        if driver_id is not None and ride.status in ("done", "cancelled"):
            return jsonify({"error": "A completed or cancelled ride cannot be assigned"}), 400
        if driver_id is None:
            ride.driver_id = None
        else:
            driver = db.session.get(Driver, driver_id)
            if not driver:
                return jsonify({"error": "Driver not found"}), 404
            if driver.status == "offline":
                return jsonify({"error": "Driver is offline"}), 409
            if driver_id != old_driver_id and _active_rides_for_driver(driver_id):
                return jsonify({"error": "Driver already has an active ride"}), 409
            ride.driver_id = driver.id
            if ride.status == "requested":
                ride.status = "assigned"
    if "fare" in data:
        try:
            fare = float(data["fare"])
        except (TypeError, ValueError):
            return jsonify({"error": "fare must be a number between 0 and 1000000"}), 400
        if not math.isfinite(fare) or not 0 <= fare <= 1_000_000:
            return jsonify({"error": "fare must be a number between 0 and 1000000"}), 400
        ride.fare = fare
    if "notes" in data:
        if data["notes"] is not None and (not isinstance(data["notes"], str) or len(data["notes"]) > 500):
            return jsonify({"error": "notes must be a string of at most 500 characters"}), 400
        ride.notes = data["notes"]

    if ride.status in ("assigned", "in_progress") and not ride.driver_id:
        return jsonify({"error": "An active ride must have an assigned driver"}), 400

    if old_driver_id and old_driver_id != ride.driver_id:
        _sync_driver_status(old_driver_id)
    if ride.driver_id:
        _sync_driver_status(ride.driver_id)

    db.session.commit()
    return jsonify(ride_to_dict(ride))


@api_bp.route("/rides/<int:id>", methods=["DELETE"])
@login_required
def api_ride_delete(id):
    if not current_user.is_admin:
        return jsonify({"error": "Admin only"}), 403
    ride = db.session.get(Ride, id)
    if not ride:
        return jsonify({"error": "Not found"}), 404
    if ride.driver_id:
        driver_id = ride.driver_id
    else:
        driver_id = None
    db.session.delete(ride)
    if driver_id:
        db.session.flush()
        _sync_driver_status(driver_id)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200


# ---------- DRIVERS ----------
@api_bp.route("/drivers", methods=["GET"])
@login_required
def api_drivers_list():
    """GET /api/drivers — list drivers. ?status=available"""
    status = request.args.get("status")
    query = Driver.query
    if status:
        query = query.filter_by(status=status)
    drivers = query.order_by(Driver.full_name).all()
    return jsonify({"items": [driver_to_dict(d) for d in drivers], "total": len(drivers)})


@api_bp.route("/drivers/<int:id>", methods=["GET"])
@login_required
def api_driver_detail(id):
    driver = db.session.get(Driver, id)
    if not driver:
        return jsonify({"error": "Not found"}), 404
    return jsonify(driver_to_dict(driver))


# ---------- CUSTOMERS ----------
@api_bp.route("/customers", methods=["GET"])
@login_required
def api_customers_list():
    if not current_user.is_admin:
        return jsonify({"error": "Admin only"}), 403
    customers = Customer.query.order_by(Customer.full_name).all()
    return jsonify({"items": [customer_to_dict(c) for c in customers], "total": len(customers)})
