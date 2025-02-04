from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import (FormField, IntegerField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import DataRequired

from .address_wtf import AddressForm


class CreateRequestForm(FlaskForm):
    name = StringField(_l('Request Name'), validators=[DataRequired()])
    needs = SelectField(_l('Needs'), validators=[DataRequired()], coerce=int)
    amount = IntegerField(_l('Amount'), validators=[DataRequired()])
    address = FormField(AddressForm)
    charity_campaign_id = SelectField(_l('Charity Campaign'), coerce=int)
    submit = SubmitField(_l('Create Request'))


class UpdateRequestStatusForm(FlaskForm):
    status = SelectField(_l('Status'), validators=[DataRequired()])
    submit = SubmitField(_l('Update'))
