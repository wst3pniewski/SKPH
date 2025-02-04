from flask_babel import _
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class AddressForm(FlaskForm):
    street = StringField(_('Street'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Street")})
    street_number = StringField(_('Street Number'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Street Number")})
    city = StringField(_('City'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("City")})
    voivodeship = StringField(_('Voivodeship'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Voivodeship")})
