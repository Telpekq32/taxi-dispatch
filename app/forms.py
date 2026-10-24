from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    TextAreaField,
    FloatField,
    DateTimeLocalField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Length,
    EqualTo,
    Optional,
    NumberRange,
    ValidationError,
    Regexp,
)
from app.models import User, Driver


class RegistrationForm(FlaskForm):
    username = StringField(
        "Пайдаланушы аты",
        validators=[DataRequired(), Length(min=3, max=64)],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(), Length(max=120)],
    )
    password = PasswordField(
        "Құпия сөз",
        validators=[DataRequired(), Length(min=6, max=128)],
    )
    password2 = PasswordField(
        "Құпия сөзді қайталаңыз",
        validators=[DataRequired(), EqualTo("password", message="Құпия сөздер сәйкес келмейді")],
    )
    full_name = StringField(
        "Толық аты-жөні",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    phone = StringField(
        "Телефон",
        validators=[
            DataRequired(),
            Length(min=10, max=20),
            Regexp(r"^[\d\+\-\(\)\s]+$", message="Телефон форматы дұрыс емес"),
        ],
    )
    submit = SubmitField("Тіркелу")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError("Бұл пайдаланушы аты бос емес.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Бұл email тіркелген.")


class LoginForm(FlaskForm):
    username = StringField("Пайдаланушы аты", validators=[DataRequired()])
    password = PasswordField("Құпия сөз", validators=[DataRequired()])
    remember = BooleanField("Есте сақтау")
    submit = SubmitField("Кіру")


class CustomerForm(FlaskForm):
    full_name = StringField(
        "Толық аты-жөні",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    phone = StringField(
        "Телефон",
        validators=[
            DataRequired(),
            Length(min=10, max=20),
            Regexp(r"^[\d\+\-\(\)\s]+$", message="Телефон форматы дұрыс емес"),
        ],
    )
    address = StringField("Мекенжай", validators=[Optional(), Length(max=200)])
    submit = SubmitField("Сақтау")


class DriverForm(FlaskForm):
    full_name = StringField(
        "Толық аты-жөні",
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    phone = StringField(
        "Телефон",
        validators=[
            DataRequired(),
            Length(min=10, max=20),
            Regexp(r"^[\d\+\-\(\)\s]+$", message="Телефон форматы дұрыс емес"),
        ],
    )
    license_number = StringField(
        "Жүргізуші куәлігі",
        validators=[DataRequired(), Length(min=5, max=50)],
    )
    car_model = StringField(
        "Көлік моделі",
        validators=[DataRequired(), Length(min=2, max=80)],
    )
    car_plate = StringField(
        "Мемлекеттік нөмір",
        validators=[DataRequired(), Length(min=4, max=20)],
    )
    status = SelectField(
        "Статус",
        choices=[
            ("available", "Бос"),
            ("busy", "Бос емес"),
            ("offline", "Оффлайн"),
        ],
        validators=[DataRequired()],
    )
    photo = FileField(
        "Фото",
        validators=[
            Optional(),
            FileAllowed(["jpg", "jpeg", "png", "gif"], "Тек сурет файлдары!"),
        ],
    )
    submit = SubmitField("Сақтау")

    def __init__(self, original_license=None, original_plate=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_license = original_license
        self.original_plate = original_plate

    def validate_license_number(self, field):
        if field.data != self.original_license:
            if Driver.query.filter_by(license_number=field.data).first():
                raise ValidationError("Бұл куәлік нөмірі тіркелген.")

    def validate_car_plate(self, field):
        if field.data != self.original_plate:
            if Driver.query.filter_by(car_plate=field.data).first():
                raise ValidationError("Бұл нөмір тіркелген.")


class RideForm(FlaskForm):
    customer_id = SelectField("Клиент", coerce=int, validators=[DataRequired()])
    driver_id = SelectField("Жүргізуші", coerce=int, validators=[Optional()])
    pickup_address = StringField(
        "Алып кету мекенжайы",
        validators=[DataRequired(), Length(min=5, max=200)],
    )
    dropoff_address = StringField(
        "Түсіру мекенжайы",
        validators=[DataRequired(), Length(min=5, max=200)],
    )
    status = SelectField(
        "Статус",
        choices=[
            ("requested", "Сұралған"),
            ("assigned", "Тағайындалған"),
            ("in_progress", "Жолда"),
            ("done", "Аяқталған"),
            ("cancelled", "Болдырылмаған"),
        ],
        validators=[DataRequired()],
    )
    ride_date = DateTimeLocalField(
        "Күні мен уақыты",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    fare = FloatField(
        "Баға (₸)",
        validators=[Optional(), NumberRange(min=0, max=1000000)],
        default=0.0,
    )
    notes = TextAreaField("Ескертпе", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Сақтау")


class RideRequestForm(FlaskForm):
    """Клиент өз бетінше тапсырыс беруі үшін"""
    pickup_address = StringField(
        "Алып кету мекенжайы",
        validators=[DataRequired(), Length(min=5, max=200)],
    )
    dropoff_address = StringField(
        "Түсіру мекенжайы",
        validators=[DataRequired(), Length(min=5, max=200)],
    )
    ride_date = DateTimeLocalField(
        "Күні мен уақыты",
        format="%Y-%m-%dT%H:%M",
        validators=[DataRequired()],
    )
    notes = TextAreaField("Ескертпе", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Тапсырыс беру")


class SearchFilterForm(FlaskForm):
    q = StringField("Іздеу", validators=[Optional(), Length(max=100)])
    status = SelectField(
        "Статус",
        choices=[
            ("", "Барлығы"),
            ("requested", "Сұралған"),
            ("assigned", "Тағайындалған"),
            ("in_progress", "Жолда"),
            ("done", "Аяқталған"),
            ("cancelled", "Болдырылмаған"),
        ],
        validators=[Optional()],
    )
    date_from = StringField("Күннен", validators=[Optional()])
    date_to = StringField("Күнге дейін", validators=[Optional()])
    sort = SelectField(
        "Сұрыптау",
        choices=[
            ("newest", "Жаңадан ескіге"),
            ("oldest", "Ескіден жаңаға"),
            ("fare_desc", "Баға ↓"),
            ("fare_asc", "Баға ↑"),
        ],
        default="newest",
    )
    submit = SubmitField("Қолдану")
