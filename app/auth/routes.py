import base64
from io import BytesIO
import pyotp
import qrcode
from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for, session, current_app)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import uuid  # Add this import

from app.auth.register_forms import (AffectedRegisterForm,
                                     AuthoritiesRegisterForm,
                                     DonorRegisterForm,
                                     OrganizationRegisterForm,
                                     VolunteerRegisterForm)
from app.auth.reset_password_forms import (ResetPasswordForm,
                                           ResetPasswordRequestForm)
from app.auth.user_service import roles_required, send_reset_password_email
from app.extensions import db
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

    return "Admin user created if it did not exist already."


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
            name=form.first_name.data,
            surname=form.last_name.data,
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
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('register.jinja', form=form, user_type=user_type)

        create_user_and_related_data(form, user_type)
        return redirect(url_for('auth.login'))

    return render_template('register.jinja', form=form, user_type=user_type)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if user.totp_secret:
                return redirect(url_for('auth.verify_totp', user_id=user.id))
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.jinja')


@bp.route('/setup-totp', methods=['GET', 'POST'])
@roles_required(['donor', 'authorities', 'organization', 'affected', 'volunteer'])
def setup_totp():
    if current_user.totp_secret:
        flash('TOTP is already set up.', 'info')
        return redirect(url_for('auth.profile'))

    if request.method == 'POST':
        totp_code = request.form['totp_code']
        totp_secret = session.get('totp_secret')
        if not totp_secret:
            flash('TOTP setup session expired. Please try again.', 'warning')
            return redirect(url_for('auth.setup_totp'))

        totp = pyotp.TOTP(totp_secret)

        if totp.verify(totp_code):
            current_user.totp_secret = totp_secret
            db.session.commit()
            session.pop('totp_secret', None)
            flash('TOTP verified and saved. 2-fa set properly.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Invalid TOTP code.', 'danger')
            return redirect(url_for('auth.profile'))
    else:
        totp_secret = pyotp.random_base32()
        session['totp_secret'] = totp_secret
        current_user.totp_secret = totp_secret
        totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(name=current_user.email, issuer_name='SKPH')

        img = qrcode.make(totp_uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return render_template('setup_totp.jinja', qr_code=img_str)


@bp.route('/verify-totp/<int:user_id>', methods=['GET', 'POST'])
def verify_totp(user_id):
    user = User.query.get(user_id)
    # if not user:
    #     flash('User not found.', 'danger')
    #     return redirect(url_for('login'))

    if request.method == 'POST':
        totp_code = request.form['totp_code']
        totp = pyotp.TOTP(user.totp_secret)

        if totp.verify(totp_code):
            login_user(user)
            flash('TOTP verified. Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid TOTP code.', 'danger')

    return render_template('verify_totp.jinja')


@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_password_email(user)
            flash('Check your email for the instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        flash('Invalid email address.', 'danger')

    return render_template('reset_password_request.jinja', form=form)


@bp.route('/reset_password/<token>/<user_id>', methods=['GET', 'POST'])
def reset_password(token, user_id):
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    user = User.validate_reset_password_token(token, user_id)
    if not user:
        flash('Invalid or expired token.', 'danger')
        return redirect(url_for('auth.reset_password_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.jinja', form=form)


@bp.route('/register', methods=['GET'])
def register_choice():
    return render_template('register_choice.jinja')


@bp.route('/manage_users', methods=['GET', 'POST'])
@roles_required('admin')
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
                    flash(f'Authority {authority.name} approved.', 'success')
                elif action == 'disapprove':
                    authority.disapprove()
                    flash(f'Authority {authority.name} disapproved.', 'warning')
        elif user_type == 'organization':
            user = User.query.get(user_id)
            if user and user.organization:
                organization = user.organization
                if action == 'approve':
                    organization.approve()
                    flash(f'Organization {organization.organization_name} approved.', 'success')
                elif action == 'disapprove':
                    organization.disapprove()
                    flash(f'Organization {organization.organization_name} disapproved.', 'warning')
            else:
                flash("Organization not found.", "danger")

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


@bp.route('/remove_totp', methods=['GET', 'POST'])
@login_required
def remove_totp():
    if not current_user.totp_secret:
        flash('TOTP is not set up.', 'info')
        return redirect(url_for('auth.profile'))

    current_user.totp_secret = None
    db.session.commit()
    flash('TOTP has been removed.', 'success')
    return redirect(url_for('auth.profile'))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}


@bp.route('/setup_profile_picture', methods=['GET', 'POST'])
@login_required
def setup_profile_picture():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            if file.mimetype not in ['image/png', 'image/jpeg', 'image/gif']:
                flash('Invalid file type. Only PNG, JPEG, and GIF are allowed.', 'danger')
                return redirect(request.url)
            if len(file.read()) > 1 * 1024 * 1024:
                flash('File size exceeds 1MB limit.', 'danger')
                return redirect(request.url)
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
            flash('Profile picture updated successfully.', 'success')
            return redirect(url_for('auth.profile'))
    return render_template('setup_profile_picture.jinja')


@bp.route('/delete_profile_picture', methods=['POST'])
@login_required
def delete_profile_picture():
    if current_user.profile_picture:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], current_user.profile_picture)
        if os.path.exists(file_path):
            os.remove(file_path)
        current_user.profile_picture = None
        db.session.commit()
        flash('Profile picture deleted successfully.', 'success')
    else:
        flash('No profile picture to delete.', 'warning')
    return redirect(url_for('auth.profile'))
