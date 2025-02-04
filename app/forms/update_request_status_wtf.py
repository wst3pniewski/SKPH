from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class UpdateRequestStatusForm(FlaskForm):
    status = SelectField(_l('Status'), validators=[DataRequired()])
    submit = SubmitField(_l('Update'))
