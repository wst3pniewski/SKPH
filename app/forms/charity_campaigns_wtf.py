from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class CharityCampaignForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    submit = SubmitField(_l('Create'))


class SignToCharityCampaignForm(FlaskForm):
    charity_campaign_id = SelectField(_l('Charity Campaign'), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Sign In'))


class ManageCharityCampaignForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    is_active = BooleanField(_l('Active'))
    submit = SubmitField(_l('Save'))
