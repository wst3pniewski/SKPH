from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class AddressForm(FlaskForm):
    street = StringField(_l('Street'), validators=[DataRequired()])
    street_number = StringField(_l('Street Number'), validators=[DataRequired()])
    city = StringField(_l('City'), validators=[DataRequired()])
    voivodeship = StringField(_l('Voivodeship'), validators=[DataRequired()])
