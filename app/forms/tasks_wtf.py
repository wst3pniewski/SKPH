from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _


class CreateTaskForm(FlaskForm):
    name = StringField(_('Task Name'), validators=[DataRequired()])
    description = TextAreaField(_('Description'), validators=[DataRequired()])
    volunteer_id = SelectField(_('Volunteer'), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_('Create task'))


class EvaluateTaskForm(FlaskForm):
    score = SelectField(
        _('Score'),
        choices=[(str(i), str(i)) for i in range(1, 6)],
        validators=[DataRequired()],
        coerce=int
    )
    description = TextAreaField(
        _('Description'),
        validators=[DataRequired()]
    )
