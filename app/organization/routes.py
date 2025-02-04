from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_babel import gettext as _
from flask_login import current_user
from sqlalchemy.orm import joinedload

from app.auth.user_service import roles_required
from app.extensions import db
from app.forms.charity_campaigns_wtf import (CharityCampaignForm,
                                             SignToCharityCampaignForm)
from app.models.address import Address
from app.models.authorities import Authorities
from app.models.charity_campaign import (CharityCampaign,
                                         OrganizationCharityCampaign)
from app.models.evaluation import Evaluation
from app.models.organization import Organization
from app.models.task import Task
from app.models.volunteer import Volunteer

bp = Blueprint('organization', __name__, template_folder='../templates/organization')


@bp.route('/')
def index():
    return render_template('organization_index.jinja')


# =================== CHARITY CAMPAIGNS ===================

@bp.route('/charity_campaigns')
def list_charity_campaigns():
    page = request.args.get('page', 1, type=int)  # Get the page number from the query params (default to 1)
    per_page = 10
    pagination = db.paginate(db.select(CharityCampaign), page=page, per_page=per_page, error_out=False)
    return render_template('list_all_charity_campaigns.jinja',
                           charity_campaigns=pagination.items,
                           pagination=pagination)


@bp.route('/organizations_charity_campaigns')
def list_organization_charity_campaigns():
    organization_charity_campaigns = db.session.scalars(db.select(OrganizationCharityCampaign)).all()
    return render_template('list_organization_charity_campaigns.jinja',
                           organization_charity_campaigns=organization_charity_campaigns)


@bp.route('charity_campaigns/<int:charity_campaign_id>')
def list_signed_organizations(charity_campaign_id):
    organization_charity_campaigns = (
        db.session.scalars(db.select(OrganizationCharityCampaign)
                           .where(OrganizationCharityCampaign.charity_campaign_id == charity_campaign_id)))
    return render_template('list_organization_charity_campaigns.jinja',
                           organization_charity_campaigns=organization_charity_campaigns)


@bp.route('charity_campaign/<int:charity_campaign_id>')
def view_campaign(charity_campaign_id):
    campaign = db.session.get(CharityCampaign, charity_campaign_id)
    referrer = request.referrer
    return render_template('view_charity_campaign.jinja',
                           campaign=campaign,
                           referrer=referrer)


@bp.route('/charity_campaign/<int:charity_campaign_id>/volunteers')
@roles_required(['organization', 'authorities'])
def manage_volunteers(charity_campaign_id):
    campaign = db.session.get(OrganizationCharityCampaign, charity_campaign_id)
    organization = db.session.get(Organization, current_user.organization.id)
    if organization.id != campaign.organization_id:
        return abort(403)
    volunteers = campaign.volunteers
    referrer = url_for('organization.list_my_charity_campaigns')
    return render_template('manage_volunteers.jinja',
                           charity_campaign_id=campaign.id,
                           volunteers=volunteers,
                           referrer=referrer)


@bp.route('/authorities/charity_campaign/<int:charity_campaign_id>/volunteers')
@roles_required(['authorities'])
def list_volunteers(charity_campaign_id):
    campaign = db.session.get(OrganizationCharityCampaign, charity_campaign_id)
    referrer = request.referrer
    return render_template('organization/list_volunteers.jinja',
                           volunteers=campaign.volunteers,
                           charity_campaign_id=charity_campaign_id,
                           referrer=referrer)

# =================== AUTHORITIES ===================


@bp.route('authorities/profile')
@roles_required(['authorities'])
def authorities_profile():
    authorities = db.session.get(Authorities, current_user.authorities.id)
    return render_template('authorities_profile.jinja',
                           authorities=authorities)


@bp.route('/authorities/<int:authorities_id>')
def view_authorities(authorities_id):
    authority = db.session.get(Authorities, authorities_id)
    referrer = request.referrer
    return render_template('view_authority.jinja',
                           authority=authority,
                           referrer=referrer)


@bp.route('authorities/<int:authorities_id>/charity_campaigns')
@roles_required(['authorities'])
def list_authorities_charity_campaigns(authorities_id):
    if current_user.type == 'authorities':
        if current_user.authorities.id != authorities_id:
            return abort(403)
    charity_campaigns = db.session.scalars(db.select(CharityCampaign)
                                           .where(CharityCampaign.authorities_id == authorities_id)).all()
    return render_template('list_charity_campaigns.jinja',
                           charity_campaigns=charity_campaigns)


@bp.route('charity_campaign/manage/<int:charity_campaign_id>', methods=['GET', 'POST'])
@roles_required(['authorities'])
def manage_charity_campaign(charity_campaign_id):
    charity_campaign = db.session.get(CharityCampaign, charity_campaign_id)
    if current_user.authorities.id == charity_campaign.authorities_id:
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            is_active = request.form.get('is_active') == 'true'

            charity_campaign.name = name
            charity_campaign.description = description
            charity_campaign.is_active = is_active

            db.session.add(charity_campaign)
            db.session.commit()
            return redirect(url_for('organization.list_authorities_charity_campaigns',
                                    authorities_id=current_user.authorities.id))
        return render_template('manage_charity_campaign.jinja',
                               campaign=charity_campaign)
    else:
        return abort(403)


@bp.route('/create_charity_campaign', methods=['GET', 'POST'])
@roles_required(['authorities'])
def create_charity_campaign():
    form = CharityCampaignForm()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        authority = db.session.scalar(db.select(Authorities).where(Authorities.user_id == current_user.id))
        new_campaign = CharityCampaign(name=name, description=description, authority=authority)
        db.session.add(new_campaign)
        db.session.commit()
        return redirect(url_for('organization.list_charity_campaigns'))
    return render_template('create_charity_campaign.jinja', form=form)

# =================== ORGANIZATIONS ===================


@bp.route('organization/profile')
@roles_required(['organization'])
def organization_profile():
    organization = db.session.get(Organization, current_user.organization.id)
    return render_template('organization_profile.jinja',
                           organization=organization)


@bp.route('organization/<int:organization_id>/profile')
@roles_required(['organization'])
def selected_organization_profile(organization_id):
    organization = db.session.get(Organization, organization_id)
    return render_template('organization_profile.jinja',
                           organization=organization)


@bp.route('/organizations')
def list_organizations():
    page = request.args.get('page', 1, type=int)  # Get the page number from the query params (default to 1)
    per_page = 10
    pagination = db.paginate(db.select(Organization), page=page, per_page=per_page, error_out=False)
    return render_template('list_organizations.jinja',
                           organizations=pagination.items,
                           pagination=pagination)


@bp.route('organization/<int:organization_id>')
def view_organization(organization_id):
    o1 = db.session.get(Organization, organization_id)
    return render_template('view_organization.jinja',
                           organization=o1)


@bp.route('/organization_charity_campaigns')
def list_my_charity_campaigns():
    organization_charity_campaigns = (
        db.session.scalars(db.select(OrganizationCharityCampaign)
                           .where(OrganizationCharityCampaign.organization_id == current_user.organization.id)).all())
    return render_template('list_organization_charity_campaigns.jinja',
                           organization_charity_campaigns=organization_charity_campaigns)


@bp.route('/sign_to_charity_campaign', methods=['GET', 'POST'])
@roles_required(['organization'])
def sign_to_charity_campaign():
    form = SignToCharityCampaignForm()
    organization = db.session.scalar(db.select(Organization)
                                     .where(Organization.user_id == current_user.id))
    stmt = db.select(CharityCampaign).options(joinedload(CharityCampaign.organizations))
    charity_campaigns = db.session.scalars(stmt).unique().all()
    form.charity_campaign_id.choices = [
        (campaign.id, campaign.name) for campaign in charity_campaigns if organization not in campaign.organizations
    ]

    if form.validate_on_submit():
        charity_campaign_id = form.charity_campaign_id.data
        charity_campaign = db.session.get(CharityCampaign, charity_campaign_id)
        new_organization_campaign = OrganizationCharityCampaign(organization=organization,
                                                                charity_campaign=charity_campaign)
        charity_campaign.organizations.append(organization)
        db.session.add(new_organization_campaign)
        db.session.commit()
        return redirect(url_for('organization.list_organization_charity_campaigns'))

    return render_template('sign_to_charity_campaign.jinja', form=form)


@bp.route('/charity_campaign/<int:organization_charity_campaign_id>/tasks/create', methods=['GET', 'POST'])
@roles_required(['organization'])
def create_task(organization_charity_campaign_id):
    organization_campaign = db.session.get(OrganizationCharityCampaign, organization_charity_campaign_id)
    organization = db.session.get(Organization, current_user.organization.id)
    if organization.id != organization_campaign.organization_id:
        return abort(403)
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        volunteer_id = request.form['volunteer_id']
        new_task = Task(name=name, description=description,
                        volunteer_id=volunteer_id, charity_campaign_id=organization_charity_campaign_id)
        db.session.add(new_task)
        db.session.commit()
        flash('Task create successfully!')
        return redirect(url_for('organization.list_my_charity_campaigns'))
    referrer = request.referrer or url_for('organization.list_my_charity_campaigns')
    return render_template('create_task_campaign.jinja',
                           volunteers=organization_campaign.volunteers,
                           campaign=organization_campaign,
                           referrer=referrer)


@bp.route('/charity_campaign/<int:organization_charity_campaign_id>/volunteer/<int:volunteer_id>/tasks/create',
          methods=['GET', 'POST'])
@roles_required(['organization'])
def create_task_specific_volunteer(organization_charity_campaign_id, volunteer_id):
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        new_task = Task(name=name, description=description,
                        volunteer_id=volunteer_id, charity_campaign_id=organization_charity_campaign_id)
        db.session.add(new_task)
        db.session.commit()
        flash('Task create successfully!')
        return redirect(url_for('organization.view_volunteer_tasks',
                                charity_campaign_id=organization_charity_campaign_id,
                                volunteer_id=volunteer_id))

    organization_campaign = db.session.get(OrganizationCharityCampaign, organization_charity_campaign_id)
    referrer = request.referrer
    return render_template('create_task_campaign.jinja',
                           volunteer_id=volunteer_id,
                           campaign=organization_campaign,
                           referrer=referrer)


@bp.route('/charity_campaign/<int:charity_campaign_id>/tasks/evaluate/<int:task_id>', methods=['GET', 'POST'])
@roles_required(['organization'])
def eval_task(charity_campaign_id, task_id):
    charity_campaign = db.session.get(OrganizationCharityCampaign, charity_campaign_id)
    if current_user.organization.id != charity_campaign.organization_id:
        return abort(403)

    task = db.session.query(Task).filter_by(id=task_id).first()
    if task is None:
        flash('Task not found.', 'warning')
        return redirect(url_for('organization.manage_volunteers', charity_campaign_id=charity_campaign_id))

    if request.method == 'POST':
        if task.status != 'completed':
            flash('You can only evaluate completed tasks!', 'warning')
            return redirect(url_for('organization.manage_volunteers', charity_campaign_id=charity_campaign_id))
        if not task.evaluation_:
            score = request.form['score']
            description = request.form['description']
            task_evaluation = Evaluation(score=score, description=description)
            task.evaluation_ = task_evaluation
            db.session.add(task)
            db.session.commit()
            flash('Evaluation added successfully!')
        else:
            flash('Task is already evaluated.')

        return redirect(url_for('organization.view_volunteer_tasks',
                                charity_campaign_id=charity_campaign_id,
                                volunteer_id=task.volunteer.id))

    referrer = request.referrer or url_for('organization.view_volunteer_tasks')
    return render_template('eval_task.jinja',
                           task=task,
                           referrer=referrer,
                           charity_campaign_id=charity_campaign_id,
                           volunteer_id=task.volunteer.id)


@bp.route('/charity_campaign/<int:charity_campaign_id>/volunteer/<int:volunteer_id>/tasks')
@roles_required(['organization', 'authorities'])
def view_volunteer_tasks(charity_campaign_id, volunteer_id):
    charity_campaign = db.session.get(OrganizationCharityCampaign, charity_campaign_id)
    if current_user.type == 'organization':
        if current_user.organization.id != charity_campaign.organization_id:
            return abort(403)
    volunteer = db.session.get(Volunteer, volunteer_id)
    status_translations = {
        'completed': _('Completed'),
        'ongoing': _('Ongoing'),
        'rejected': _('Rejected')
    }
    if current_user.type == 'organization':
        referrer = url_for('organization.manage_volunteers', charity_campaign_id=charity_campaign.id)
    else:
        referrer = request.referrer
    return render_template('organization/volunteer_tasks.jinja',
                           volunteer=volunteer,
                           charity_campaign_id=charity_campaign.id,
                           referrer=referrer,
                           status_translations=status_translations)


@bp.route('/charity_campaign/<int:organization_charity_campaign_id>/volunteer/<int:volunteer_id>/remove',
          methods=['POST'])
@roles_required(['organization'])
def remove_volunteer(organization_charity_campaign_id, volunteer_id):
    organization_campaign = db.session.get(OrganizationCharityCampaign, organization_charity_campaign_id)
    if current_user.organization.id != organization_campaign.organization_id:
        return abort(403)

    volunteer = db.session.get(Volunteer, volunteer_id)
    if volunteer in organization_campaign.volunteers:
        organization_campaign.volunteers.remove(volunteer)
        db.session.commit()
        flash('Volunteer removed successfully!')
    else:
        flash('Volunteer not found in this campaign.', 'warning')

    return redirect(url_for('organization.manage_volunteers',
                            charity_campaign_id=organization_charity_campaign_id))

# =================== VOLUNTEERS ===================


@bp.route('/volunteer_sign_to_charity_campaign', methods=['GET', 'POST'])
@roles_required(['volunteer'])
def volunteer_sign_to_charity_campaign():
    volunteer = db.session.scalar(db.select(Volunteer).where(Volunteer.user_id == current_user.id))
    if volunteer:
        if request.method == 'POST':
            organization_charity_campaign_id = request.form['organization_charity_campaign_id']
            organization_campaign = db.session.get(OrganizationCharityCampaign, organization_charity_campaign_id)

            if organization_campaign and volunteer:
                organization_campaign.volunteers.append(volunteer)
                db.session.commit()

                return redirect(url_for('organization.list_volunteer_charity_campaigns',
                                        charity_campaign_id=organization_charity_campaign_id))

        organization_charity_campaigns = db.session.scalars(db.select(OrganizationCharityCampaign)).all()
        organization_charity_campaigns = (
            [campaign for campaign in organization_charity_campaigns if volunteer not in campaign.volunteers])
        return render_template('volunteer_sign_to_charity_campaign.jinja',
                               organization_charity_campaigns=organization_charity_campaigns)
    else:
        return abort(404)


@bp.route('/volunteer/charity_campaigns', methods=['GET'])
@roles_required(['volunteer'])
def list_volunteer_charity_campaigns():
    volunteer = db.session.scalar(db.select(Volunteer).where(Volunteer.user_id == current_user.id))

    referrer = url_for('home')
    return render_template('list_volunteer_charity_campaigns.jinja',
                           organization_charity_campaigns=volunteer.campaigns,
                           volunteer=volunteer,
                           referrer=referrer)

# =================== SAMPLES ===================


@bp.route('/add_sample_organization_charity_campaign')
def add_sample_organization_charity_campaign():
    address1 = Address(street='Miejska', street_number='1a', city='Łódź', voivodeship='Łódzkie')
    authority1 = Authorities(name='Aleksander Wika', phone='758934576', approved=True, address=address1)
    sample_campaign = CharityCampaign(name="Pomoc Dla Powodzian",
                                      description="Akcja ma na celu pomoc osobą dotkniętych powodzią na Dolnym Śląsku",
                                      authority=authority1)
    organization1 = Organization(organization_name='Fundacja Siepomaga',
                                 description='Fundacja Siepomaga powstała, by osiągać to,\
                                    co na pierwszy rzut oka wydaje się niemożliwe.\
                                    Ratujemy życie i zdrowie, które wyceniono na kwoty\
                                    niemożliwe do osiągnięcia przez Potrzebujących.',
                                 approved=True, address=address1)
    sample_organization_campaign = OrganizationCharityCampaign(organization=organization1,
                                                               charity_campaign=sample_campaign)

    volunteer1 = Volunteer(first_name='Michael', last_name='Johnson', email='mjohnson@mail.com', phone='957485273')
    address2 = Address(street='Główna', street_number='4d', city='Gdańsk', voivodeship='Pomorskie')
    volunteer1.address = address2

    volunteer2 = Volunteer(first_name='Jane', last_name='Doe', email='jdoe@mail.com', phone='823903283')
    address3 = Address(street='Wiejska', street_number='2b', city='Warszawa', voivodeship='Mazowieckie')
    volunteer2.address = address3

    volunteer3 = Volunteer(first_name='Alice', last_name='Smith', email='asmith@mail.com', phone='758292375')
    address4 = Address(street='Krakowska', street_number='3c', city='Kraków', voivodeship='Małopolskie')
    volunteer3.address = address4

    sample_organization_campaign.volunteers.extend([volunteer1, volunteer2, volunteer3])

    db.session.add_all([volunteer1, volunteer2, volunteer3])
    db.session.add(sample_organization_campaign)
    db.session.commit()
    return redirect(url_for('organization.list_organization_charity_campaigns'))
