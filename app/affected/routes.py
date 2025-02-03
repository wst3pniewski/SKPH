from flask import (Blueprint, flash, redirect, render_template,
                   render_template_string, request, url_for)
from flask_login import current_user, login_required
from flask_mailman import EmailMessage

from app.auth.user_service import roles_required
from app.extensions import csrf, db, mail
from app.models.address import Address
from app.models.affected import Affected
from app.models.authorities import Authorities
from app.models.charity_campaign import CharityCampaign
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
    donation_types = ['Food', 'Clothes', 'Shelter', 'Medical Supplies']
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


@bp.route('/all')
@login_required
@roles_required(['organization', 'authorities'])
def fetch_all():
    affected = db.session.scalars(db.select(Affected))
    return render_template('all.jinja', affected=affected.all())


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
            req_address=req1_address,
            donation_type=donation_type_1,
            amount=10,
            affected_id=aff1.id
        )
        req2 = Request(
            name='Clothes needed',
            status=RequestStatus.PENDING,
            req_address=req2_address,
            donation_type=donation_type_2,
            amount=5,
            affected_id=aff2.id
        )
        session.add(req1)
        session.add(req2)
        session.commit()

    flash('Sample data added successfully!')
    return redirect(url_for('affected.index'))


@bp.route('/select_affected', methods=['GET', 'POST'])
def select_affected():
    if request.method == 'POST':
        affected_id = request.form['affected_id']
        return redirect(url_for('affected.create_request', affected_id=affected_id))

    affected = db.session.scalars(db.select(Affected))
    return render_template('select_affected.jinja', affected=affected.all())


@bp.route('/request/create', methods=['GET', 'POST'])
@login_required
@roles_required(['affected'])
@csrf.exempt
def create_request():
    affected = db.session.scalar(db.select(Affected).where(Affected.user_id == current_user.id))
    if not affected:
        flash('No data found for the current user.')
        return redirect(url_for('affected.index'))

    if request.method == 'POST':
        name = request.form['name']
        status = RequestStatus.PENDING
        donation_type_id = int(request.form.get('needs'))
        amount = int(request.form['amount'])
        street = request.form['street']
        street_number = request.form['street_number']
        city = request.form['city']
        voivodeship = request.form['voivodeship']

        # Validation
        if not all([name, donation_type_id, amount, street, street_number, city, voivodeship]):
            flash('All fields are required.')
            return redirect(url_for('affected.create_request'))

        # Create new address
        new_address = Address(
            street=street,
            street_number=street_number,
            city=city,
            voivodeship=voivodeship
        )
        db.session.add(new_address)
        db.session.commit()

        # Create new request
        new_request = Request(
            name=name,
            status=status,
            req_address=new_address,
            donation_type_id=donation_type_id,
            amount=amount,
            affected_id=affected.id
        )
        db.session.add(new_request)
        db.session.commit()

        return redirect(url_for('affected.my_details'))

    donation_types = db.session.scalars(db.select(DonationType)).all()
    return render_template('create_request.jinja', affected=affected, donation_types=donation_types)


@bp.route('/requests')
@login_required
@roles_required(['organization', 'authorities'])
def all_requests():
    requests = db.session.scalars(db.select(Request)).all()

    return render_template('all_requests.jinja', requests=requests)


@bp.route('/affected/<int:affected_id>')
@login_required
@roles_required(['organization', 'authorities'])
def affected_details(affected_id):
    affected = db.get_or_404(Affected, affected_id)

    requests = db.session.query(Request).filter_by(affected_id=affected_id).all()

    return render_template('affected_details.jinja', affected=affected, requests=requests, RequestStatus=RequestStatus)


@bp.route('/my_details')
@login_required
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


@bp.route('/select_campaign', methods=['GET', 'POST'])
@login_required
@roles_required(['affected'])
def select_campaign():
    affected = db.session.scalar(db.select(Affected).where(Affected.user_id == current_user.id))
    if not affected:
        flash('No data found for the current user.')
        return redirect(url_for('affected.index'))

    if request.method == 'POST':
        campaign_id = request.form.get('campaign_id')
        affected.campaign_id = campaign_id
        db.session.commit()
        flash('Campaign selected successfully.')
        return redirect(url_for('affected.my_details'))

    campaigns = db.session.scalars(db.select(CharityCampaign)).all()
    return render_template('select_campaign.jinja', affected=affected, campaigns=campaigns)


@bp.route('/request/edit/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    request_obj = db.get_or_404(Request, request_id)

    if request_obj.status != RequestStatus.PENDING:
        return redirect(url_for('affected.my_details'))

    if request.method == 'POST':
        name = request.form.get('name')
        donation_type_id = request.form.get('donation_type')
        amount = request.form.get('amount')
        street = request.form.get('street')
        street_number = request.form.get('street_number')
        city = request.form.get('city')
        voivodeship = request.form.get('voivodeship')

        if not all([name, donation_type_id, amount, street, street_number, city, voivodeship]):
            flash('All fields are required.')
            return redirect(url_for('affected.edit_request', request_id=request_id))

        donation_type_id = int(donation_type_id)
        amount = int(amount)

        request_obj.name = name
        request_obj.donation_type_id = donation_type_id
        request_obj.amount = amount
        request_obj.req_address.street = street
        request_obj.req_address.street_number = street_number
        request_obj.req_address.city = city
        request_obj.req_address.voivodeship = voivodeship

        db.session.commit()

        return redirect(url_for('affected.my_details'))

    donation_types = db.session.scalars(db.select(DonationType)).all()
    return render_template('edit_request.jinja', request=request_obj, donation_types=donation_types)


@bp.route('/request/update_status/<int:request_id>', methods=['GET', 'POST'])
@login_required
@roles_required(['organization', 'authorities'])
def update_request_status(request_id):
    request_obj = db.get_or_404(Request, request_id)

    if request.method == 'POST':
        new_status = request.form.get('status')
        if new_status not in RequestStatus.__members__:
            return redirect(url_for('affected.update_request_status', request_id=request_id))

        request_obj.status = RequestStatus[new_status]
        db.session.commit()

        affected_user = request_obj.affected.user
        send_status_update_email(affected_user, request_obj)

        return redirect(url_for('affected.affected_details', affected_id=request_obj.affected_id))

    return render_template('update_request_status.jinja', request=request_obj, statuses=RequestStatus)


@bp.route('/request/delete/<int:request_id>', methods=['POST', 'GET'])
@login_required
def delete_request(request_id):
    request_obj = db.get_or_404(Request, request_id)

    if request_obj.status != RequestStatus.PENDING:
        return redirect(url_for('affected.my_details'))

    db.session.delete(request_obj.req_address)
    db.session.delete(request_obj)
    db.session.commit()

    return redirect(url_for('affected.my_details'))
