from datetime import date

from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_login import current_user

from app.auth.user_service import roles_required
from app.extensions import csrf, db
from app.models.address import Address
from app.models.authorities import Authorities
from app.models.charity_campaign import (CharityCampaign,
                                         OrganizationCharityCampaign)
from app.models.donation import DonationItem, DonationMoney, DonationType
from app.models.donor import Donor
from app.models.item_stock import ItemStock
from app.models.organization import Organization

bp = Blueprint('donors', __name__,
               template_folder='../templates/donors',
               static_folder='static',
               static_url_path='donors')


@bp.route('/')
def index():
    samples_added = db.session.query(Donor).count() > 0
    return render_template('donors.jinja', samples_added=samples_added)


@bp.route('/donor/profile')
@roles_required(['donor'])
def donor_profile():
    donor = db.session.get(Donor, current_user.donor.donor_id)
    return render_template('donor_profile.jinja', donor=donor)


@bp.route('/all')
@roles_required(['authorities'])
def fetch_donors():
    donors = db.session.scalars(db.select(Donor))
    return render_template('donor_view.jinja', donors=donors.all())


@bp.route('/donation/create', methods=['GET', 'POST'])
@roles_required(['donor'])
@csrf.exempt
def create_donation():
    donor = db.session.scalar(db.select(Donor).where(Donor.donor_id == current_user.donor.donor_id))
    charity_campaigns = db.session.scalars(db.select(OrganizationCharityCampaign)).all()
    donation_type = db.session.scalars(db.select(DonationType)).all()
    if request.method == 'POST':
        description = request.form['description']
        type_d = request.form['donation_type']
        charity_campaign = request.form['organization_charity_campaign_id']
        amount = request.form['amount']
        if type_d == 'Money':
            money_type = DonationType.query.filter(DonationType.type == 'Money').first()

            new_donation_money = DonationMoney(
                description=description,
                donation_date=date.today(),
                donation_type=money_type,
                cashAmount=amount,
                donor=donor,
                charity_campaign_id=charity_campaign
            )
            db.session.add(new_donation_money)

            curr_stock = ItemStock.query.join(DonationType, ItemStock.item_type_id == DonationType.id) \
                .filter(ItemStock.organization_charity_campaign_id == charity_campaign, DonationType.type == 'Money') \
                .first()

            if curr_stock is None:
                new_stock = ItemStock(item_type=money_type,
                                      organization_charity_campaign_id=charity_campaign,
                                      amount=amount)
                db.session.add(new_stock)
            else:
                curr_stock.amount += float(amount)
                db.session.add(curr_stock)

            db.session.commit()
            flash('Donation created successfully')
        else:
            new_donation_item = DonationItem(
                description=description,
                donation_date=date.today(),
                donation_type_id=type_d,
                amount=amount,
                donor_id=donor.donor_id,
                charity_campaign_id=charity_campaign
            )
            db.session.add(new_donation_item)
            curr_stock = ItemStock.query.join(DonationType, ItemStock.item_type_id == DonationType.id) \
                .filter(ItemStock.organization_charity_campaign_id == charity_campaign,
                        DonationType.id == type_d) \
                .first()
            if curr_stock is None:
                new_stock = ItemStock(item_type_id=type_d,
                                      organization_charity_campaign_id=charity_campaign,
                                      amount=amount)
                db.session.add(new_stock)

            else:
                curr_stock.amount += float(amount)
                db.session.add(curr_stock)

            db.session.commit()
            flash('Donation created successfully')

        return redirect(url_for('home', donor_id=donor.donor_id))
    return render_template('create_donation.jinja',
                           charity_campaigns=charity_campaigns,
                           ItemDonationType=donation_type)


@bp.route('/donations')
@roles_required(['donor', 'organization', 'authorities'])
def list_donations():
    donor = db.session.scalar(db.select(Donor).where(Donor.donor_id == current_user.donor.donor_id))
    if current_user.type == 'donor':
        if current_user.donor.donor_id != donor.donor_id:
            return abort(403)

    donor = db.session.get(Donor, donor.donor_id)
    if Donor is None:
        return 'Donor not found', 404

    donations_money = db.session.scalars(
        db.select(DonationMoney).where(DonationMoney.donor_id == donor.donor_id)
    )
    donations_items = db.session.scalars(
        db.select(DonationItem).where(DonationItem.donor_id == donor.donor_id)
    )

    return render_template('donations.jinja', donations_money=donations_money.all(), donor=donor,
                           donations_items=donations_items.all())


@bp.route('/confirm/<int:id>', methods=['POST'])
def confirm_point(donation_item_id):
    donation = db.session.scalar(db.select(DonationItem).filter(DonationItem.donationItem_id == donation_item_id))
    if not donation:
        flash("Nie znaleziono przedmiotu o podanym ID.")
        return redirect('/')

    flash(str(donation.return_confirmation()))
    return redirect('/donors/donations')


@bp.route('/confirm-money/<int:id>', methods=['POST'])
def confirm_money(donation_money_id):
    donation = db.session.scalar(db.select(DonationMoney).filter(DonationMoney.donationMoney_id == donation_money_id))
    if not donation:
        flash("Nie znaleziono przedmiotu o podanym ID.")
        return redirect('/')

    flash(str(donation.return_confirmation()))
    return redirect('/donors/donations')


@bp.route('/samples', methods=['POST'])
def donor_samples():
    new_donor = Donor(
        first_name="John",
        last_name="Doe",
        phone_number="123456789",
        email="john.doe@example.com",
        user_id=current_user.id
    )
    db.session.add(new_donor)
    db.session.commit()
    db.session.refresh(new_donor)

    address2 = Address(street='Kimbal', street_number='1a', city='Łódź', voivodeship='Łódzkie')
    authority2 = Authorities(name='Aleksander alkohol', phone='758934576', approved=True, address=address2)
    sample_campaign2 = CharityCampaign(
        name="Pomoc Dla Powodzian",
        description="Akcja ma na celu pomoc osobą dotkniętych powodzią na Dolnym Śląsku",
        authority=authority2)
    organization2 = Organization(
        organization_name='Fundacja Sieniepomaga',
        description='Fundacja Sieniepomaga powstała, by nie pomagac to,\
              co na pierwszy rzut oka wydaje się możliwe.\
              nie ratujemy życia i zdrowia, które wyceniono na kwoty\
              niemożliwe do osiągnięcia przez Potrzebujących.',
        approved=True, address=address2)

    sample_organization_campaign2 = OrganizationCharityCampaign(
        organization=organization2,
        charity_campaign=sample_campaign2)

    db.session.add(sample_campaign2)
    db.session.add(organization2)
    db.session.add(sample_organization_campaign2)

    db.session.commit()
    db.session.refresh(organization2)
    db.session.refresh(sample_organization_campaign2)
    db.session.refresh(sample_campaign2)

    new_donation_money = DonationMoney(
        description='duza kasa',
        donation_date=date.today(),
        donation_type="Money",
        cashAmount=1000,
        donor_id=new_donor.donor_id,
        charity_campaign_id=sample_organization_campaign2.id
    )
    db.session.add(new_donation_money)

    new_donation_item = DonationItem(
        description='elo',
        donation_date=date.today(),
        donation_type_id=1,
        amount=15,
        donor_id=new_donor.donor_id,
        charity_campaign_id=sample_organization_campaign2.id  # Ensure this ID exists
    )
    db.session.add(new_donation_item)
    db.session.commit()
    del new_donation_item
    del new_donation_money

    return redirect(url_for('donors.index'))
