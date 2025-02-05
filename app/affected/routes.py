from flask import (Blueprint, flash, redirect, render_template,
                   render_template_string, request, session, url_for)
from flask_babel import gettext as _
from flask_login import current_user
from flask_mailman import EmailMessage

from app.auth.user_service import roles_required
from app.extensions import db, mail
from app.forms.requests_wtf import CreateRequestForm, UpdateRequestStatusForm
from app.models.address import Address
from app.models.affected import Affected
from app.models.authorities import Authorities
from app.models.charity_campaign import (CharityCampaign,
                                         OrganizationCharityCampaign)
from app.models.donation import DonationType
from app.models.request import Request, RequestStatus

bp = Blueprint('affected', __name__,
               template_folder='../templates/affected',
               static_folder='static',
               static_url_path='affected')


def send_status_update_email(user, request_obj):
    email_body = render_template_string(
        "Hello {{ user.first_name }},<br><br>"
        "The status of your request '{{ request_obj.name }}' "
        "has been updated to '{{ request_obj.status.value }}'.<br><br>"
        "Best regards,<br>Your Team<br>"
        "SKPH IO",
        user=user,
        request_obj=request_obj
    )

    message = EmailMessage(
        subject="Request Status Update",
        body=email_body,
        to=[user.email]
    )
    message.content_subtype = "html"

    with mail.get_connection() as connection:
        message.send(connection)


def initialize_donation_types():
    donation_types = ['Food', 'Clothes', 'Shelter', 'Medical Supplies', 'Money']
    existing_types = db.session.query(DonationType.type).all()
    existing_types = [type[0] for type in existing_types]

    for type in donation_types:
        if type not in existing_types:
            new_type = DonationType(type=type)
            db.session.add(new_type)

    db.session.commit()


@bp.route('/')
def index():
    samples_added = db.session.query(Affected).count() > 0
    affected = db.session.scalars(db.select(Affected))
    return render_template('affected.jinja', samples_added=samples_added, affected=affected.all())


@bp.route('/my-details')
@roles_required(['affected'])
def my_details():
    affected = db.session.scalar(db.select(Affected).where(Affected.user_id == current_user.id))
    if not affected:
        flash('No data found for the current user.')
        return redirect(url_for('affected.index'))

    requests = db.session.query(Request).filter_by(affected_id=affected.id).all()

    return render_template(
        'affected_auth_details.jinja', affected=affected, requests=requests, RequestStatus=RequestStatus
    )


@bp.route('/affected/<int:affected_id>')
@roles_required(['organization', 'authorities'])
def affected_details(affected_id):
    affected = db.get_or_404(Affected, affected_id)

    requests = db.session.query(Request).filter_by(affected_id=affected_id).all()

    return render_template('affected_details.jinja', affected=affected, requests=requests, RequestStatus=RequestStatus)


@bp.route('/all')
@roles_required(['organization', 'authorities'])
def fetch_all():
    affected = db.session.scalars(db.select(Affected))
    return render_template('all.jinja', affected=affected.all())


@bp.route('/select-affected', methods=['GET', 'POST'])
def select_affected():
    if request.method == 'POST':
        affected_id = request.form['affected_id']
        return redirect(url_for('affected.create_request', affected_id=affected_id))

    affected = db.session.scalars(db.select(Affected))
    return render_template('select_affected.jinja', affected=affected.all())


@bp.route('/organization-charity-campaign/requests')
@roles_required(['organization', 'authorities'])
def requests_for_org_charity_campaign():
    if 'original_referrer' not in session:
        session['original_referrer'] = request.referrer
    organization_charity_campaign_id = request.args.get('organization_charity_campaign_id', type=int)
    requests = Request.query.filter(Request.charity_campaign_id == organization_charity_campaign_id).all()
    original_referrer = session.get('original_referrer')
    return render_template('view_requests.jinja', requests=requests, referrer=original_referrer)


@bp.route('/request/create', methods=['GET', 'POST'])
@roles_required(['affected'])
def create_request():
    affected = db.session.scalar(db.select(Affected).where(Affected.user_id == current_user.id))
    if not affected:
        flash('No data found for the current user.')
        return redirect(url_for('affected.index'))

    form = CreateRequestForm()
    # translation purpose
    donation_types = [_('Food'), _('Clothes'), _('Shelter'), _('Medical Supplies')]

    form.needs.choices = [(dt.id, _(dt.type)) for dt in db.session.scalars(db.select(DonationType)).all()]
    form.charity_campaign_id.choices = [
        (cc.id, f"{cc.charity_campaign.name} - {cc.organization.organization_name}")
        for cc in db.session.scalars(db.select(OrganizationCharityCampaign)).all()
    ]
    if form.validate_on_submit():
        name = form.name.data
        status = RequestStatus.PENDING
        donation_type_id = form.needs.data
        amount = form.amount.data
        street = form.address.street.data
        street_number = form.address.street_number.data
        city = form.address.city.data
        voivodeship = form.address.voivodeship.data
        charity_campaign_id = form.charity_campaign_id.data

        new_address = Address(
            street=street,
            street_number=street_number,
            city=city,
            voivodeship=voivodeship
        )
        db.session.add(new_address)
        db.session.commit()

        new_request = Request(
            name=name,
            status=status,
            address=new_address,
            donation_type_id=donation_type_id,
            amount=amount,
            affected_id=affected.id,
            charity_campaign_id=charity_campaign_id
        )
        db.session.add(new_request)
        db.session.commit()

        return redirect(url_for('affected.my_details'))

    return render_template('create_request_wtf.jinja', form=form, affected=affected)


@bp.route('/request/edit/<int:request_id>', methods=['GET', 'POST'])
@roles_required('affected')
def edit_request(request_id):
    request_obj = db.get_or_404(Request, request_id)

    if request_obj.status != RequestStatus.PENDING:
        return redirect(url_for('affected.my_details'))

    form = CreateRequestForm(obj=request_obj)
    form.needs.choices = [(dt.id, dt.type) for dt in db.session.scalars(db.select(DonationType)).all()]
    form.charity_campaign_id.choices = [(cc.id, cc.charity_campaign.name) for cc in db.session.scalars(db.select(OrganizationCharityCampaign)).all()]

    if form.validate_on_submit():
        request_obj.name = form.name.data
        request_obj.donation_type_id = form.needs.data
        request_obj.amount = form.amount.data
        request_obj.address.street = form.address.street.data
        request_obj.address.street_number = form.address.street_number.data
        request_obj.address.city = form.address.city.data
        request_obj.address.voivodeship = form.address.voivodeship.data
        request_obj.charity_campaign_id = form.charity_campaign_id.data

        db.session.commit()

        return redirect(url_for('affected.my_details'))

    return render_template('edit_request_wtf.jinja', form=form, request=request_obj)


@bp.route('/request/update-status/<int:request_id>', methods=['GET', 'POST'])
@roles_required('organization')
def update_request_status(request_id):
    request_obj = db.get_or_404(Request, request_id)
    form = UpdateRequestStatusForm(obj=request_obj)
    form.status.choices = [(status.name, _(status.value)) for status in RequestStatus]

    if form.validate_on_submit():
        new_status = form.status.data

        request_obj.status = RequestStatus[new_status]
        db.session.commit()

        affected_user = request_obj.affected.user
        send_status_update_email(affected_user, request_obj)

        return redirect(url_for('affected.affected_details', affected_id=request_obj.affected_id))

    return render_template('update_request_status.jinja', form=form, request=request_obj, statuses=RequestStatus, referrer=request.referrer)


@bp.route('/request/delete/<int:request_id>', methods=['POST', 'GET'])
@roles_required(['organization', 'affected'])
def delete_request(request_id):
    request_obj = db.get_or_404(Request, request_id)

    if request_obj.status != RequestStatus.PENDING:
        return redirect(url_for('affected.my_details'))

    db.session.delete(request_obj.address)
    db.session.delete(request_obj)
    db.session.commit()
    if current_user.type == 'affected':
        return redirect(url_for('affected.my_details'))
    else:
        return redirect(url_for('home'))

# SAMPLES


@bp.route('/samples', methods=['POST'])
def samples():
    if db.session.query(Affected).count() > 0:
        flash('Sample data already added!')
        return redirect(url_for('affected.index'))

    with db.session() as session:
        address1 = Address(street='Miejska', street_number='1a', city='Łódź', voivodeship='Łódzkie')
        authority1 = Authorities(name='Aleksander Wika', phone='758934576', approved=True, address=address1)
        sample_campaign = CharityCampaign(
            name="Pomoc Dla Powodzian",
            description="Akcja ma na celu pomoc osobą dotkniętych powodzią na Dolnym Śląsku",
            authority=authority1
        )
        session.add(sample_campaign)
        session.flush()

        donation_type_1 = DonationType(type='Food')
        donation_type_2 = DonationType(type='Clothes')

        session.add(donation_type_1)
        session.add(donation_type_2)

        # Create sample affected individuals
        aff1 = Affected(first_name='Geto', last_name='Mill', needs='Shelter', campaign_id=sample_campaign.id)
        a1 = Address(street='Miejska', street_number='1a', city='Łódź', voivodeship='Łódzkie')
        aff1.address = a1

        aff2 = Affected(first_name='Lukas', last_name='Steven', needs='Food', campaign_id=sample_campaign.id)
        a2 = Address(street='Wiejska', street_number='2b', city='Warsaw', voivodeship='Mazowieckie')
        aff2.address = a2

        session.add(aff1)
        session.add(aff2)

        req1_address = Address(street='Pomocna', street_number='10', city='Gdańsk', voivodeship='Pomorskie')
        req2_address = Address(street='Pomocna', street_number='10', city='Gdańsk', voivodeship='Pomorskie')
        session.add(req1_address)
        session.add(req2_address)
        session.flush()

        req1 = Request(
            name='Food Assistance',
            status=RequestStatus.PENDING,
            address=req1_address,
            donation_type=donation_type_1,
            amount=10,
            affected_id=aff1.id
        )
        req2 = Request(
            name='Clothes needed',
            status=RequestStatus.PENDING,
            address=req2_address,
            donation_type=donation_type_2,
            amount=5,
            affected_id=aff2.id
        )
        session.add(req1)
        session.add(req2)
        session.commit()

    flash('Sample data added successfully!')
    return redirect(url_for('affected.index'))
