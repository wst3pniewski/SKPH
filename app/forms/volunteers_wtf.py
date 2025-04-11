from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class VolunteerSignToCharityCampaignForm(FlaskForm):
    organization_charity_campaign_id = SelectField(
        _l('Charity Campaign'),
        validators=[DataRequired()],
        coerce=int
    )
    submit = SubmitField(_l('Sign In'))


class UpdateTaskStatusForm(FlaskForm):
    status = SelectField(_l('Status'), validators=[DataRequired()], choices=[])
    submit = SubmitField(_l('Update Status'))
