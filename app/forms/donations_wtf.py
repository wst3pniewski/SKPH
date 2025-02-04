from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_babel import lazy_gettext as _l


class CreateDonationForm(FlaskForm):
    description = TextAreaField(_l('Donation Description:'), validators=[DataRequired()])
    amount = DecimalField(_l('Donation Amount:'), validators=[NumberRange(min=0)], places=2)
    donation_type = SelectField(_l('Type:'), validators=[DataRequired()], coerce=int)
    organization_charity_campaign_id = SelectField(_l('Charity Campaign:'), validators=[DataRequired()], coerce=int)
    submit = SubmitField(_l('Confirm Donation'))
