from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")  # admin | user
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Optional links
    customer = db.relationship("Customer", back_populates="user", uselist=False)
    driver = db.relationship("Driver", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="customer")
    rides = db.relationship("Ride", back_populates="customer", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Customer {self.full_name}>"


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    car_model = db.Column(db.String(80), nullable=False)
    car_plate = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default="available")  # available | busy | offline
    photo = db.Column(db.String(255))  # filename
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="driver")
    rides = db.relationship("Ride", back_populates="driver", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Driver {self.full_name} ({self.car_plate})>"


class Ride(db.Model):
    __tablename__ = "rides"

    STATUS_CHOICES = ("requested", "assigned", "in_progress", "done", "cancelled")

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True)
    pickup_address = db.Column(db.String(200), nullable=False)
    dropoff_address = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="requested", index=True)
    ride_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    fare = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    customer = db.relationship("Customer", back_populates="rides")
    driver = db.relationship("Driver", back_populates="rides")

    def __repr__(self) -> str:
        return f"<Ride #{self.id} {self.status}>"
