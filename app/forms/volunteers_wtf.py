from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _


class VolunteerSignToCharityCampaignForm(FlaskForm):
    organization_charity_campaign_id = SelectField(
        _('Charity Campaign'),
        validators=[DataRequired()],
        coerce=int
    )
    submit = SubmitField(_('Sign In'))


class UpdateTaskStatusForm(FlaskForm):
    status = SelectField(_('Status'), validators=[DataRequired()], choices=[])
    submit = SubmitField(_('Update Status'))
