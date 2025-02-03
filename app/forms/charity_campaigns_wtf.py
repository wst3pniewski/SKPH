from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired


class CharityCampaignForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Create')


class SignToCharityCampaignForm(FlaskForm):
    charity_campaign_id = SelectField('Charity Campaign', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Sign In')
