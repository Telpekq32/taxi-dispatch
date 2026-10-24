import os

from app import create_app, db
from app.models import User, Customer, Driver, Ride

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "User": User,
        "Customer": Customer,
        "Driver": Driver,
        "Ride": Ride,
    }


if __name__ == "__main__":
    app.run(
        debug=os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"},
        host=os.getenv("FLASK_HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
    )
