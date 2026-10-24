"""Initialize database and seed demo data."""
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models import User, Customer, Driver, Ride

app = create_app()


def seed():
    with app.app_context():
        db.create_all()

        # Seed demo records only when missing; initialization must never erase user data.
        admin = User.query.filter_by(username="admin").first()
        if admin is None:
            admin = User(username="admin", email="admin@taxi.local", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)

        user1 = User(username="user1", email="user1@taxi.local", role="user")
        existing_user = User.query.filter_by(username="user1").first()
        if existing_user is None:
            user1.set_password("user123")
            db.session.add(user1)
            db.session.flush()
        else:
            user1 = existing_user

        customer1 = Customer.query.filter_by(user_id=user1.id).first()
        if customer1 is None:
            customer1 = Customer(
                user_id=user1.id,
                full_name="Айдар Нұрланұлы",
                phone="+7 701 111 22 33",
                address="Алматы, Абай 10",
            )
            db.session.add(customer1)

        c2 = Customer.query.filter_by(phone="+7 702 222 33 44").first()
        if c2 is None:
            c2 = Customer(full_name="Гүлнар Сәтбаева", phone="+7 702 222 33 44", address="Астана, Қабанбай 5")
            db.session.add(c2)
        c3 = Customer.query.filter_by(phone="+7 705 333 44 55").first()
        if c3 is None:
            c3 = Customer(full_name="Ерлан Қасымов", phone="+7 705 333 44 55")
            db.session.add(c3)

        drivers = []
        for full_name, phone, license_number, car_model, car_plate, status in [
            ("Бауыржан Төлеуов", "+7 777 100 20 30", "KZ-DRV-001", "Toyota Camry", "123 ABC 01", "available"),
            ("Серік Жұмабеков", "+7 777 200 30 40", "KZ-DRV-002", "Hyundai Elantra", "456 DEF 02", "available"),
            ("Азамат Қалиев", "+7 777 300 40 50", "KZ-DRV-003", "Kia Optima", "789 GHI 03", "offline"),
        ]:
            driver = Driver.query.filter_by(license_number=license_number).first()
            if driver is None:
                driver = Driver(full_name=full_name, phone=phone, license_number=license_number,
                                car_model=car_model, car_plate=car_plate, status=status)
                db.session.add(driver)
            drivers.append(driver)
        db.session.flush()
        d1, d2, _d3 = drivers

        now = datetime.now(timezone.utc)
        if Ride.query.count() == 0:
            rides = [
                Ride(
                    customer_id=customer1.id,
                    driver_id=d1.id,
                    pickup_address="Абай даңғылы 150, Алматы",
                    dropoff_address="Достық даңғылы 45, Алматы",
                    status="done",
                    ride_date=now - timedelta(days=2),
                    fare=2500,
                    notes="Аяқталған сапар",
                ),
                Ride(
                    customer_id=c2.id,
                    driver_id=None,
                    pickup_address="Қабанбай батыр 10, Астана",
                    dropoff_address="Есіл ауданы, Астана",
                    status="requested",
                    ride_date=now + timedelta(hours=2),
                    fare=0,
                ),
                Ride(
                    customer_id=c3.id,
                    driver_id=d2.id,
                    pickup_address="Мега центр, Алматы",
                    dropoff_address="Аэропорт, Алматы",
                    status="assigned",
                    ride_date=now + timedelta(hours=1),
                    fare=4500,
                ),
                Ride(
                    customer_id=customer1.id,
                    driver_id=None,
                    pickup_address="Сәтбаев көшесі 22",
                    dropoff_address="Тимирязев 15",
                    status="requested",
                    ride_date=now,
                    fare=0,
                    notes="Жедел керек",
                ),
            ]
            db.session.add_all(rides)
            d2.status = "busy"
        db.session.commit()

        print("=" * 50)
        print("Database initialized successfully!")
        print("=" * 50)
        print("Test accounts:")
        print("  Admin  → username: admin   password: admin123")
        print("  User   → username: user1   password: user123")
        print("=" * 50)
        print("Drivers:", Driver.query.count())
        print("Customers:", Customer.query.count())
        print("Rides:", Ride.query.count())


if __name__ == "__main__":
    seed()
