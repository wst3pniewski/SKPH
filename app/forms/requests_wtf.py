from flask_babel import _
from flask_wtf import FlaskForm
from wtforms import (FormField, IntegerField, SelectField, StringField,
                     SubmitField)
from wtforms.validators import DataRequired

from .address_wtf import AddressForm


class CreateRequestForm(FlaskForm):
    name = StringField(_('Request Name'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Request Name")})
    needs = SelectField(_('Needs'), validators=[DataRequired()], coerce=int, render_kw={"class": "form-control"})
    amount = IntegerField(_('Amount'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Amount")})
    address = FormField(AddressForm)
    charity_campaign_id = SelectField(_('Charity Campaign'), coerce=int, render_kw={"class": "form-control"})
    submit = SubmitField(_('Create Request'), render_kw={"class": "btn btn-primary mt-3"})


class UpdateRequestStatusForm(FlaskForm):
    status = SelectField(_('Status'), validators=[DataRequired()])
    submit = SubmitField(_('Update'))
