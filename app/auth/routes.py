import base64
import os
import uuid  # Add this import
from io import BytesIO

import pyotp
import qrcode
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, session, url_for)
from flask_babel import gettext as _
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename

from app.auth.login_form import LoginForm
from app.auth.register_forms import (AffectedRegisterForm,
                                     AuthoritiesRegisterForm,
                                     DonorRegisterForm,
                                     OrganizationRegisterForm,
                                     VolunteerRegisterForm)
from app.auth.reset_password_forms import (ResetPasswordForm,
                                           ResetPasswordRequestForm)
from app.auth.user_service import roles_required, send_reset_password_email
from app.extensions import csrf, db, hcaptcha
from app.forms.totp_wtf import RemoveTOTPForm, SetupTOTPForm, VerifyTOTPForm
from app.models.address import Address
from app.models.affected import Affected
from app.models.authorities import Authorities
from app.models.donor import Donor
from app.models.organization import Organization
from app.models.user import User
from app.models.volunteer import Volunteer

bp = Blueprint('auth', __name__,
               template_folder='../templates/auth',
               static_folder='static',
               static_url_path='auth')


@bp.route('/')
def index():
    admin_user = User.query.filter_by(email="admin@skph.com").first()

    if not admin_user:
        new_admin = User(
            email="admin@skph.com",
            password_hash=generate_password_hash("haslo123"),
            type="admin"
        )
        db.session.add(new_admin)
        db.session.commit()

    if current_user.is_authenticated:
        logout_user()

    return _("Admin user created if it did not exist already.")


def get_registration_form(user_type):
    form_classes = {
        'volunteer': VolunteerRegisterForm,
        'organization': OrganizationRegisterForm,
        'donor': DonorRegisterForm,
        'affected': AffectedRegisterForm,
        'authorities': AuthoritiesRegisterForm
    }
    return form_classes.get(user_type)()


def create_user_and_related_data(form, user_type):
    user = User(email=form.email.data, type=user_type)
    user.set_password(form.password.data)
    db.session.add(user)
    db.session.commit()

    if user_type == 'donor':
        donor = Donor(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone_number=form.phone.data,
            email=form.email.data,
            user_id=user.id
        )
        db.session.add(donor)

    if user_type in ['volunteer', 'organization', 'affected', 'authorities']:
        address = Address(
            street=form.street.data,
            street_number=form.street_number.data,
            city=form.city.data,
            voivodeship=form.voivodeship.data
        )
        db.session.add(address)
        db.session.commit()

        if user_type == 'volunteer':
            volunteer = Volunteer(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=address,
                address_id=address.id,
                user_id=user.id
            )
            db.session.add(volunteer)

        elif user_type == 'organization':
            organization = Organization(
                organization_name=form.organization_name.data,
                description=form.description.data,
                address=address,
                address_id=address.id,
                user_id=user.id
            )
            db.session.add(organization)

        elif user_type == 'affected':
            affected = Affected(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                needs=form.needs.data,
                address=address,
                address_id=address.id,
                user_id=user.id
            )
            db.session.add(affected)

        elif user_type == 'authorities':
            authorities = Authorities(
                name=form.name.data,
                phone=form.phone.data,
                address=address,
                address_id=address.id,
                user_id=user.id
            )
            db.session.add(authorities)

    db.session.commit()


@bp.route('/register/<user_type>', methods=['GET', 'POST'])
def register(user_type):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = get_registration_form(user_type)
    if not form:
        abort(404)

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash(_('Email already registered. Please use a different email.'), 'danger')
            return render_template('register.jinja', form=form, user_type=user_type)

        create_user_and_related_data(form, user_type)
        flash(_('Your account has been created successfully.'))
        return redirect(url_for('auth.login'))

    return render_template('register.jinja', form=form, user_type=user_type)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash(_('You have been logged out.'), 'info')
    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        if hcaptcha.verify():
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                if user.totp_secret:
                    return redirect(url_for('auth.verify_totp', user_id=user.id))
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash(_('Invalid email or password.'), 'danger')
        else:
            flash(_('Captcha not done'), 'danger')
    # hcaptcha=hcaptcha.get_code(theme='dark')
    return render_template('login.jinja', form=form)


@bp.route('/setup-totp', methods=['GET', 'POST'])
@roles_required(['donor', 'authorities', 'organization', 'affected', 'volunteer'])
def setup_totp():
    form = SetupTOTPForm()
    if current_user.totp_secret:
        flash(_('TOTP is already set up.'), 'info')
        return redirect(url_for('auth.profile'))

    if form.validate_on_submit():
        totp_code = form.totp_code.data
        totp_secret = session.get('totp_secret')
        if not totp_secret:
            flash(_('2FA setup session expired. Please try again.'), 'warning')
            return redirect(url_for('auth.setup_totp'))

        totp = pyotp.TOTP(totp_secret)

        if totp.verify(totp_code):
            current_user.totp_secret = totp_secret
            db.session.commit()
            session.pop('totp_secret', None)
            flash(_('TOTP verified and saved. 2FA is now active!'), 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(_('Invalid OTP code.'), 'danger')
            return redirect(url_for('auth.profile'))
    else:
        totp_secret = pyotp.random_base32()
        session['totp_secret'] = totp_secret
        current_user.totp_secret = totp_secret
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(name=current_user.email, issuer_name='SKPH')

        img = qrcode.make(data=totp_uri, border=1)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return render_template('setup_totp.jinja', qr_code=img_str, form=form)


@bp.route('/remove-totp', methods=['GET', 'POST'])
@login_required
def remove_totp():
    form = RemoveTOTPForm()
    if not current_user.totp_secret:
        flash(_('2FA is not active.'), 'info')
        return redirect(url_for('auth.profile'))

    if form.validate_on_submit():
        totp_code = form.totp_code.data
        totp = pyotp.TOTP(current_user.totp_secret)

        if totp.verify(totp_code):
            current_user.totp_secret = None
            db.session.commit()
            flash(_('2FA has been removed.'), 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(_('Invalid OTP code.'), 'danger')

    return render_template('remove_totp.jinja', form=form)


@bp.route('/verify-totp/<int:user_id>', methods=['GET', 'POST'])
def verify_totp(user_id):
    user = User.query.get(user_id)
    form = VerifyTOTPForm()
    if not user:
        flash(_('User not found.'), 'danger')
        return redirect(url_for('auth.login'))

    if form.validate_on_submit():
        totp_code = form.totp_code.data
        totp = pyotp.TOTP(user.totp_secret)

        if totp.verify(totp_code):
            login_user(user)
            flash(_('2FA verified successfully! You are logged in.'), 'success')
            return redirect(url_for('home'))
        else:
            flash(_('Invalid OTP code.'), 'danger')

    return render_template('verify_totp.jinja', form=form)


@bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_password_email(user)
            flash(_('Check your email for the instructions to reset your password.'), 'info')
            return redirect(url_for('auth.login'))
        flash(_('Invalid email address.'), 'danger')

    return render_template('reset_password_request.jinja', form=form)


@bp.route('/reset-password/<token>/<user_id>', methods=['GET', 'POST'])
def reset_password(token, user_id):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.validate_reset_password_token(token, user_id)
    if not user:
        flash(_('Invalid or expired token.'), 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'), 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.jinja', form=form)


@bp.route('/register', methods=['GET'])
def register_choice():
    return render_template('register_choice.jinja')


@bp.route('/manage-users', methods=['GET', 'POST'])
@roles_required('admin')
@csrf.exempt
def manage_users():
    authorities = Authorities.query.all()
    organizations = Organization.query.all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        user_type = request.form.get('user_type')

        if user_type == 'authorities':
            user = User.query.get(user_id)
            if user and user.authorities:
                authority = user.authorities
                if action == 'approve':
                    authority.approve()
                    flash(_('Authority %(name)s approved.', name=authority.name), 'success')
                elif action == 'disapprove':
                    authority.disapprove()
                    flash(_('Authority %(name)s disapproved.', name=authority.name), 'warning')
        elif user_type == 'organization':
            user = User.query.get(user_id)
            if user and user.organization:
                organization = user.organization
                if action == 'approve':
                    organization.approve()
                    flash(_('Organization %(name)s approved.', name=organization.organization_name), 'success')
                elif action == 'disapprove':
                    organization.disapprove()
                    flash(_('Organization %(name)s disapproved.', name=organization.organization_name), 'warning')
            else:
                flash(_("Organization not found."), "danger")

        return redirect(url_for('auth.manage_users'))

    return render_template('manage_users.jinja', authorities=authorities, organizations=organizations)


@bp.route('/profile')
@login_required
def profile():
    role_urls = {
        # 'admin': url_for('admin.dashboard'),
        'affected': url_for('affected.my_details'),
        'donor': url_for('donors.donor_profile'),
        'organization': url_for('organization.organization_profile'),
        'volunteer': url_for('volunteers.volunteer_profile'),
        'authorities': url_for('organization.authorities_profile')
    }
    return redirect(role_urls[current_user.type])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@bp.route('/setup-profile-picture', methods=['POST'])
@login_required
@csrf.exempt
def setup_profile_picture():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash(_('No file part'), 'danger')
            return redirect(url_for('auth.profile'))
        file = request.files['file']
        if file.filename == '':
            flash(_('No selected file'), 'danger')
            return redirect(url_for('auth.profile'))
        if file and allowed_file(file.filename):
            if file.mimetype not in ['image/png', 'image/jpeg', 'image/gif']:
                flash(_('Invalid file type. Only PNG, JPEG, and GIF are allowed.'), 'danger')
                return redirect(url_for('auth.profile'))
            if len(file.read()) > 1 * 1024 * 1024:
                flash(_('File size exceeds 1MB limit.'), 'danger')
                return redirect(url_for('auth.profile'))
            file.seek(0)
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()
            random_filename = f"{uuid.uuid4().hex}.{file_extension}"
            upload_folder = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            file_path = os.path.join(upload_folder, random_filename)
            file.save(file_path)
            current_user.profile_picture = random_filename
            db.session.commit()
            flash(_('Profile picture updated successfully.'), 'success')
            return redirect(url_for('auth.profile'))
    return redirect(url_for('auth.profile'))


@bp.route('/delete-profile-picture', methods=['POST'])
@login_required
@csrf.exempt
def delete_profile_picture():
    if current_user.profile_picture:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
        if os.path.exists(file_path):
            os.remove(file_path)
        current_user.profile_picture = None
        db.session.commit()
        flash(_('Profile picture deleted successfully.'), 'success')
    else:
        flash(_('No profile picture to delete.'), 'warning')
    return redirect(url_for('auth.profile'))


@bp.route('/set-theme', methods=['POST'])
def set_theme():
    data = request.get_json()
    theme = data.get('theme')
    if theme in ['light', 'dark']:
        session['theme'] = theme
        return jsonify(success=True)
    return jsonify(success=False), 400
