import tempfile
from datetime import date

from flask import (Blueprint, abort, flash, redirect, render_template,
                   send_file, url_for)
from flask_babel import gettext as _
from flask_login import current_user
from fpdf import FPDF

from app.auth.user_service import roles_required
from app.extensions import db
from app.forms.donations_wtf import CreateDonationForm
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
def create_donation():
    form = CreateDonationForm()
    form.donation_type.choices = [(item.id, _(item.type)) for item in db.session.scalars(db.select(DonationType)).all()]
    form.organization_charity_campaign_id.choices = [(campaign.id, f"{campaign.charity_campaign.name} ({campaign.organization.organization_name})") for campaign in db.session.scalars(db.select(OrganizationCharityCampaign)).all()]

    if form.validate_on_submit():
        description = form.description.data
        donation_type = form.donation_type.data
        charity_campaign_id = form.organization_charity_campaign_id.data
        amount = form.amount.data

        donor = db.session.scalar(db.select(Donor).where(Donor.donor_id == current_user.donor.donor_id))
        charity_campaign = OrganizationCharityCampaign.query.get(charity_campaign_id)
        money_type = DonationType.query.filter(DonationType.type == 'Money').scalar()

        if donation_type == money_type.id:
            new_donation_money = DonationMoney(
                description=description,
                donation_date=date.today(),
                donation_type=money_type,
                cashAmount=amount,
                donor=donor,
                charity_campaign_id=charity_campaign_id
            )
            charity_campaign.donations_money.append(new_donation_money)
            db.session.add(new_donation_money)

            curr_stock = ItemStock.query.join(DonationType, ItemStock.item_type_id == DonationType.id) \
                .filter(ItemStock.organization_charity_campaign_id == charity_campaign_id, DonationType.type == 'Money') \
                .first()

            if curr_stock is None:
                new_stock = ItemStock(item_type=money_type,
                                      organization_charity_campaign_id=charity_campaign_id,
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
                donation_type_id=donation_type,
                amount=amount,
                donor_id=donor.donor_id,
                charity_campaign_id=charity_campaign_id
            )
            db.session.add(new_donation_item)
            curr_stock = ItemStock.query.join(DonationType, ItemStock.item_type_id == DonationType.id) \
                .filter(ItemStock.organization_charity_campaign_id == charity_campaign_id,
                        DonationType.id == donation_type) \
                .first()
            if curr_stock is None:
                new_stock = ItemStock(item_type_id=donation_type,
                                      organization_charity_campaign_id=charity_campaign_id,
                                      amount=amount)
                db.session.add(new_stock)
            else:
                curr_stock.amount += float(amount)
                db.session.add(curr_stock)

            db.session.commit()
            flash('Donation created successfully')

        return redirect(url_for('home', donor_id=donor.donor_id))
    return render_template('create_donation.jinja', form=form)


@bp.route('/donations')
@roles_required(['donor', 'organization', 'authorities'])
def list_donations():
    donor = Donor.query.filter(Donor.user_id == current_user.id).first()
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
    return redirect(url_for('donors.list_donations'))


@bp.route('/download-pdf/<int:donation_money_id>', methods=['GET'])
def download_pdf(donation_money_id):
    donation = db.session.scalar(db.select(DonationMoney).filter(DonationMoney.donationMoney_id == donation_money_id))
    if not donation:
        flash("Nie znaleziono przedmiotu o podanym ID.")
        return redirect('/')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add SKPH header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SKPH - Crisis Management System", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Thank you for your generous donation!", ln=True, align='C')
    pdf.ln(10)

    # Donation details
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Donation Confirmation", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)

    # Table headers
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, txt="Field", border=1, align='C')
    pdf.cell(140, 10, txt="Details", border=1, align='C')
    pdf.ln(10)

    # Table content
    pdf.set_font("Arial", size=12)
    pdf.cell(50, 10, txt="Description", border=1)
    pdf.cell(140, 10, txt=donation.description, border=1)
    pdf.ln(10)
    pdf.cell(50, 10, txt="Amount", border=1)
    pdf.cell(140, 10, txt=str(donation.cashAmount), border=1)
    pdf.ln(10)
    pdf.cell(50, 10, txt="Date", border=1)
    pdf.cell(140, 10, txt=str(donation.donation_date), border=1)
    pdf.ln(10)
    pdf.cell(50, 10, txt="Donor ID", border=1)
    pdf.cell(140, 10, txt=str(donation.donor_id), border=1)
    pdf.ln(10)
    pdf.cell(50, 10, txt="Charity Campaign ID", border=1)
    pdf.cell(140, 10, txt=str(donation.charity_campaign_id), border=1)
    pdf.ln(10)

    # Footer
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="SKPH - Crisis Management System", ln=True, align='C')
    pdf.cell(200, 10, txt="Contact us at: support@skph.org", ln=True, align='C')
    pdf.cell(200, 10, txt="Visit our website: www.skph.org", ln=True, align='C')

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
        pdf_output = tmpfile.name
        pdf.output(pdf_output)

    response = send_file(pdf_output, as_attachment=True)
    return response


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
