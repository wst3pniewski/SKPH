from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ManageRequestForm(FlaskForm):
    donation_amount = IntegerField(_l('Donation amount'), validators=[DataRequired(), NumberRange(min=1)])
    donation_type = SelectField(_l('Donation type'), choices=[], validators=[DataRequired()])
    submit = SubmitField(_l('Send to affected'))


class SelectCharityCampaignForm(FlaskForm):
    curr_charity_campaign = SelectField(_l('Select charity campaign'), choices=[], validators=[DataRequired()])
    submit = SubmitField(_l('Select charity campaign'))
