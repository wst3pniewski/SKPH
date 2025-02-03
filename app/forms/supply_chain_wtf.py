from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class ManageRequestForm(FlaskForm):
    donation_amount = IntegerField('Donation amount', validators=[DataRequired(), NumberRange(min=1)])
    donation_type = SelectField('Donation type', choices=[], validators=[DataRequired()])
    submit = SubmitField('Send to affected')


class SelectCharityCampaignForm(FlaskForm):
    curr_charity_campaign = SelectField('Select charity campaign', choices=[], validators=[DataRequired()])
    submit = SubmitField('Select charity campaign')
