from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class RemoveTOTPForm(FlaskForm):
    totp_code = StringField('TOTP Code', validators=[DataRequired()])
    submit = SubmitField('Remove TOTP')


class VerifyTOTPForm(FlaskForm):
    totp_code = StringField('TOTP Code', validators=[DataRequired()])
    submit = SubmitField('Verify')


class SetupTOTPForm(FlaskForm):
    totp_code = StringField('TOTP Code', validators=[DataRequired()])
    submit = SubmitField('Verify And Save')
