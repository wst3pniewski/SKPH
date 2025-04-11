from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class CreateTaskForm(FlaskForm):
    name = StringField(_l('Task Name'), validators=[DataRequired()])
    description = TextAreaField(_l('Description'), validators=[DataRequired()])
    volunteer_id = SelectField(_l('Volunteer'), coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Create task'))


class EvaluateTaskForm(FlaskForm):
    score = SelectField(
        _l('Score'),
        choices=[(str(i), str(i)) for i in range(1, 6)],
        validators=[DataRequired()],
        coerce=int
    )
    description = TextAreaField(
        _l('Description'),
        validators=[DataRequired()]
    )
