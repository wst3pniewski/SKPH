from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_babel import lazy_gettext as _l


class LoginForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()], render_kw={"class": "form-control", "placeholder": _l("Enter your email")})
    password = PasswordField(_l('Password'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _l("Enter your password")})
    submit = SubmitField(_l('Login'), render_kw={"class": "btn btn-primary"})
