from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, FormField
from wtforms.validators import DataRequired
from flask_babel import _


class AddressForm(FlaskForm):
    street = StringField(_('Street'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Street")})
    street_number = StringField(_('Street Number'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Street Number")})
    city = StringField(_('City'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("City")})
    voivodeship = StringField(_('Voivodeship'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Voivodeship")})


class CreateRequestForm(FlaskForm):
    name = StringField(_('Request Name'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Request Name")})
    needs = SelectField(_('Needs'), validators=[DataRequired()], coerce=int, render_kw={"class": "form-control"})
    amount = IntegerField(_('Amount'), validators=[DataRequired()], render_kw={"class": "form-control", "placeholder": _("Amount")})
    address = FormField(AddressForm)
    charity_campaign_id = SelectField(_('Charity Campaign'), coerce=int, render_kw={"class": "form-control"})
    submit = SubmitField(_('Create Request'), render_kw={"class": "btn btn-primary mt-3"})
