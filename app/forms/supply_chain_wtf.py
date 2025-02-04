from flask_babel import lazy_gettext as _
from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ManageRequestForm(FlaskForm):
    donation_amount = IntegerField(_('Donation amount'), validators=[DataRequired(), NumberRange(min=1)])
    donation_type = SelectField(_('Donation type'), choices=[], validators=[DataRequired()])
    submit = SubmitField(_('Send to affected'))


class SelectCharityCampaignForm(FlaskForm):
    curr_charity_campaign = SelectField(_('Select charity campaign'), choices=[], validators=[DataRequired()])
    submit = SubmitField(_('Select charity campaign'))
