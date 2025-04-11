from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_babel import lazy_gettext as _l


class RemoveTOTPForm(FlaskForm):
    totp_code = StringField(_l('TOTP Code'), validators=[DataRequired()])
    submit = SubmitField(_l('Remove TOTP'))


class VerifyTOTPForm(FlaskForm):
    totp_code = StringField(_l('TOTP Code'), validators=[DataRequired()])
    submit = SubmitField(_l('Verify'))


class SetupTOTPForm(FlaskForm):
    totp_code = StringField(_l('TOTP Code'), validators=[DataRequired()])
    submit = SubmitField(_l('Verify And Save'))
