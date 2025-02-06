import csv
import io
import json

import pandas as pd
import plotly.express as px
from flask import (Blueprint, Response, current_app, has_request_context,
                   render_template, request, session)
from flask_babel import lazy_gettext as _l
from flask_login import login_required
from plotly.utils import PlotlyJSONEncoder

from app.auth.user_service import roles_required
from app.extensions import db
from app.models.address import Address
from app.models.affected import Affected
from app.models.charity_campaign import CharityCampaign, OrganizationCharityCampaign
from app.models.donation import DonationItem, DonationMoney, DonationType
from app.models.donor import Donor
from app.models.item_stock import ItemStock
from app.models.request import Request
from app.models.task import Task
from app.models.volunteer import Volunteer

from .report_service import ReportService

bp = Blueprint("reports", __name__,
               template_folder="../templates/reports",
               static_folder="../static/reports")
report_service = ReportService()


def get_theme() -> str:
    try:
        if not has_request_context():
            return 'plotly'
        theme = session.get('theme', 'light')
        return 'plotly_white' if theme == 'light' else 'plotly_dark'
    except Exception as e:
        current_app.logger.error(f"Error getting theme: {e}")
        return 'plotly'


@bp.route('/')
@login_required
def ui():
    return render_template('reports.jinja')


# =================== RAPORT AFFECTED ===================
@bp.route('/affected-report')
@roles_required(['authorities', 'organization'])
def affected_report():
    campaign_id = request.args.get('campaign_id', type=int)
    if not campaign_id:
        message = _l('Please specify campaign id!')
        return f'<h3>{message}</h3>', 400

    campaign = OrganizationCharityCampaign.query.get(campaign_id)
    if not campaign:
        message = _l('There is no campaign with specified id!')
        return f'<h3>{message}</h3>', 400

    theme = get_theme()

    city_stats = db.session.query(
        Address.city, db.func.count(Affected.id)
    ).join(Affected).group_by(Address.city).all()

    cities = [city[0] for city in city_stats]
    cities_counts = [city[1] for city in city_stats]
    df_city_stats = pd.DataFrame({'city': cities, 'affected_count': cities_counts})

    requests_stats = db.session.query(
        Affected.id, db.func.count(Request.id)
    ).join(Request, Affected.id == Request.affected_id).filter(
        Request.charity_campaign_id == campaign_id).group_by(Affected.id).all()

    requests_affected_id = [str(tasks[0]) for tasks in requests_stats]
    requests_count = [tasks[1] for tasks in requests_stats]
    df_requests_count = pd.DataFrame({
        'affected_id': pd.Series(requests_affected_id, dtype='object'),
        'requests_count': requests_count
    })

    requests_status_stats = db.session.query(
        Request.status, db.func.count(Request.id)
    ).join(Affected).filter(Request.charity_campaign_id == campaign_id).group_by(Request.status).all()

    statuses = [str(status[0].value) for status in requests_status_stats]
    statuses_counts = [status[1] for status in requests_status_stats]
    df_requests_status_stats = pd.DataFrame({'status': statuses, 'requests_count': statuses_counts})

    requests_donation_type_stats = db.session.query(
        DonationType.type, db.func.count(Request.id)
    ).join(Request, DonationType.id == Request.donation_type_id).filter(
        Request.charity_campaign_id == campaign_id).group_by(DonationType.type).all()

    donation_types = [donation_type[0] for donation_type in requests_donation_type_stats]
    donation_types_counts = [donation_type[1] for donation_type in requests_donation_type_stats]
    df_requests_donation_type_stats = pd.DataFrame({'request_type': donation_types, 'requests_count': donation_types_counts})

    voiv_stats = db.session.query(
        Address.voivodeship, db.func.count(Affected.id)
    ).join(Affected).group_by(Address.voivodeship).all()

    voivodeships = [voiv[0] for voiv in voiv_stats]
    voivodeships_counts = [voiv[1] for voiv in voiv_stats]
    df_voiv_stats = pd.DataFrame({'voivodeship': voivodeships, 'affected_count': voivodeships_counts})

    city_chart = px.bar(df_city_stats, x='city', y='affected_count', title='Affected by city', color='city', template=theme)
    requests_chart = px.bar(df_requests_count, x='affected_id', y='requests_count', title='Requests by affected', color='affected_id', template=theme)
    requests_status_chart = px.bar(df_requests_status_stats, x='status', y='requests_count', title='Requests by Status', color='status', template=theme)
    requests_donation_type_chart = px.bar(df_requests_donation_type_stats, x='request_type', y='requests_count', title='Requests by Type', color='request_type', template=theme)
    voiv_chart = px.bar(df_voiv_stats, x='voivodeship', y='affected_count', title='Affected by voivodeship', color='voivodeship', template=theme)

    city_chart_json = json.dumps(city_chart, cls=PlotlyJSONEncoder)
    requests_chart_json = json.dumps(requests_chart, cls=PlotlyJSONEncoder)
    requests_status_chart_json = json.dumps(requests_status_chart, cls=PlotlyJSONEncoder)
    requests_donation_type_chart_json = json.dumps(requests_donation_type_chart, cls=PlotlyJSONEncoder)
    voiv_chart_json = json.dumps(voiv_chart, cls=PlotlyJSONEncoder)
    city_stats_html = df_city_stats.to_html(justify='left', index=False, classes='table table-bordered')
    requests_stats_html = df_requests_count.to_html(justify='left', index=False, classes='table table-bordered')
    requests_status_stats_html = df_requests_status_stats.to_html(justify='left', index=False, classes='table table-bordered')
    requests_donation_type_stats_html = df_requests_donation_type_stats.to_html(justify='left', index=False, classes='table table-bordered')
    voiv_stats_html = df_voiv_stats.to_html(justify='left', index=False, classes='table table-bordered')
    return render_template('affected_report.jinja',
                           campaign=campaign,
                           city_stats_html=city_stats_html,
                           requests_stats_html=requests_stats_html,
                           requests_status_stats_html=requests_status_stats_html,
                           requests_donation_type_stats_html=requests_donation_type_stats_html,
                           city_chart_json=city_chart_json,
                           requests_chart_json=requests_chart_json,
                           requests_status_chart_json=requests_status_chart_json,
                           requests_donation_type_chart_json=requests_donation_type_chart_json,
                           voiv_stats_html=voiv_stats_html,
                           voiv_chart_json=voiv_chart_json)


@bp.route('/affected-report-csv')
@roles_required(['authorities', 'organization'])
def affected_report_csv():
    affected_list = db.session.query(Affected).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "FirstName", "LastName", "Needs", "City", "Voiv", "Campaign", "RequestsCount"])

    for aff in affected_list:
        city = aff.address.city if aff.address else ""
        voiv = aff.address.voivodeship if aff.address else ""
        camp_name = aff.campaign.name if aff.campaign else ""
        req_count = len(aff.requests) if aff.requests else 0

        writer.writerow([aff.id, aff.first_name, aff.last_name, aff.needs or "", city, voiv, camp_name, req_count])

    csv_data = output.getvalue()
    output.close()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=affected_report.csv"})

# =================== RAPORT VOLUNTEER ===================


@bp.route('/volunteer-report')
@roles_required(['organization', 'authorities'])
def volunteer_report():
    campaign_id = request.args.get('campaign_id', type=int)
    if not campaign_id:
        message = _l('Please specify campaign id!')
        return f'<h3>{message}</h3>', 400

    campaign = OrganizationCharityCampaign.query.get(campaign_id)
    if not campaign:
        message = _l('There is no camapign with specified id!')
        return f'<h3>{message}</h3>', 400

    theme = get_theme()

    city_stats = db.session.query(
        Address.city, db.func.count(Volunteer.id)
    ).join(Volunteer).join(Volunteer.campaigns).filter(OrganizationCharityCampaign.id == campaign_id).group_by(Address.city).all()

    cities = [city[0] for city in city_stats]
    cities_counts = [city[1] for city in city_stats]
    df_city_stats = pd.DataFrame({'city': cities, 'volunteers_count': cities_counts})

    tasks_stats = db.session.query(
        Volunteer.id, db.func.count(Task.id)
    ).join(Task, Volunteer.id == Task.volunteer_id).join(
        Volunteer.campaigns).filter(
            OrganizationCharityCampaign.id == campaign_id).group_by(Volunteer.id).all()

    tasks_volunteer_id = [tasks[0] for tasks in tasks_stats]
    tasks_count = [tasks[1] for tasks in tasks_stats]
    df_tasks_count = pd.DataFrame({
        'volunteer_id': pd.Series(tasks_volunteer_id, dtype='object'),
        'tasks_count': tasks_count
    })

    tasks_status_stats = db.session.query(
        Task.status, db.func.count(Task.id)
    ).join(Volunteer).join(
        Volunteer.campaigns).filter(
            OrganizationCharityCampaign.id == campaign_id).group_by(Task.status).all()

    statuses = [status[0] for status in tasks_status_stats]
    statuses_counts = [status[1] for status in tasks_status_stats]
    df_tasks_status_stats = pd.DataFrame({'status': statuses, 'tasks_count': statuses_counts})

    city_chart = px.bar(df_city_stats, x='city', y='volunteers_count', title='Volunteers by city', color='city', template=theme)
    tasks_chart = px.bar(df_tasks_count, x='volunteer_id', y='tasks_count', title='Tasks by volunteers', color='volunteer_id', template=theme)
    tasks_status_chart = px.bar(df_tasks_status_stats, x='status', y='tasks_count', title='Tasks by Status', color='status', template=theme)  # New line

    city_chart_json = json.dumps(city_chart, cls=PlotlyJSONEncoder)
    tasks_chart_json = json.dumps(tasks_chart, cls=PlotlyJSONEncoder)
    tasks_status_chart_json = json.dumps(tasks_status_chart, cls=PlotlyJSONEncoder)  # New line
    city_stats_html = df_city_stats.to_html(justify='left', index=False, classes='table table-bordered')
    tasks_stats_html = df_tasks_count.to_html(justify='left', index=False, classes='table table-bordered')
    tasks_status_stats_html = df_tasks_status_stats.to_html(justify='left', index=False, classes='table table-bordered')  # New line
    return render_template('volunteers_report.jinja',
                           city_stats_html=city_stats_html,
                           tasks_stats_html=tasks_stats_html,
                           tasks_status_stats_html=tasks_status_stats_html,
                           city_chart_json=city_chart_json,
                           tasks_chart_json=tasks_chart_json,
                           tasks_status_chart_json=tasks_status_chart_json)


@bp.route('/volunteer-report-csv', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
def volunteer_report_csv():
    volunteer_list = report_service.get_all_volunteers()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Imię", "Nazwisko", "Miasto", "Województwo", "TasksCount"])

    for vol in volunteer_list:
        city = vol.address.city if vol.address else ""
        voiv = vol.address.voivodeship if vol.address else ""
        tcount = len(vol.tasks)
        writer.writerow([vol.id, vol.first_name, vol.last_name, city, voiv, tcount])

    csv_data = output.getvalue()
    output.close()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=volunteer_report.csv"})
# =================== RAPORT DONOR ===================


@bp.route('/donors-report')
@roles_required(['organization', 'authorities'])
def donors_report():
    campaign_id = request.args.get('campaign_id', type=int)
    if not campaign_id:
        message = _l('Please specify campaign id!')
        return f'<h3>{message}</h3>', 400

    campaign = OrganizationCharityCampaign.query.get(campaign_id)
    if not campaign:
        message = _l('There is no campaign with specified id!')
        return f'<h3>{message}</h3>', 400

    theme = get_theme()

    donation_money_count_stats = DonationMoney.query.filter(
        DonationMoney.charity_campaign_id == campaign_id).count()

    donation_item_count_stats = DonationItem.query.filter(
        DonationItem.charity_campaign_id == campaign_id).count()

    df_donations_types = pd.DataFrame({
        'donation_type': ['money', 'item'],
        'count': [donation_money_count_stats, donation_item_count_stats]
    })

    donations_money = DonationMoney.query.filter(
        DonationMoney.charity_campaign_id == campaign_id).all()

    donations_item_all = DonationItem.query.filter(
        DonationItem.charity_campaign_id == campaign_id).all()

    donations_id = [donation.donationMoney_id for donation in donations_money]
    donations_amount = [donation.cashAmount for donation in donations_money]

    df_donations_money = pd.DataFrame({
        'donation_id': donations_id,
        'amount': donations_amount
    })

    df_donations_money_stats = df_donations_money.describe(exclude=[int])

    donations_item = db.session.query(
        DonationType.type, db.func.count(DonationItem.donationItem_id)
    ).join(DonationItem, DonationItem.donation_type_id == DonationType.id).filter(
        DonationItem.charity_campaign_id == campaign_id
    ).group_by(DonationType.type).all()

    donations_type = [donation[0] for donation in donations_item]
    donations_count = [donation[1] for donation in donations_item]

    df_donations_item = pd.DataFrame({
        'donation_type': donations_type,
        'donation_count': donations_count,
    })

    donations_types_chart = px.bar(df_donations_types, x='donation_type', y='count',
                                   title='Donations by type', template=theme)

    donations_money_chart = px.scatter(df_donations_money, x='donation_id', y='amount',
                                       title='Money donations by amount', template=theme)

    donations_item_chart = px.bar(df_donations_item, x='donation_type', y='donation_count',
                                  color='donation_type', title='Item donations by type', template=theme)

    donations_types_chart_json = json.dumps(donations_types_chart, cls=PlotlyJSONEncoder)
    donations_money_chart_json = json.dumps(donations_money_chart, cls=PlotlyJSONEncoder)
    donations_item_chart_json = json.dumps(donations_item_chart, cls=PlotlyJSONEncoder)

    donations_types_html = df_donations_types.to_html(justify='left', index=False,
                                                      classes='table table-bordered')

    donations_money_html = df_donations_money.to_html(justify='left', index=False,
                                                      classes='table table-bordered')

    donations_money_stats_html = df_donations_money_stats.to_html(justify='left',
                                                                  classes='table table-bordered')

    donations_item_html = df_donations_item.to_html(justify='left', index=False,
                                                    classes='table table-bordered')

    return render_template('donors_report.jinja',
                           donations_money=donations_money,
                           donations_item=donations_item_all,
                           donations_types_chart_json=donations_types_chart_json,
                           donations_money_chart_json=donations_money_chart_json,
                           donations_item_chart_json=donations_item_chart_json,
                           donations_types_html=donations_types_html,
                           donations_money_html=donations_money_html,
                           donations_money_stats_html=donations_money_stats_html,
                           donations_item_html=donations_item_html
                           )


@bp.route('/donor-report-csv', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
def donor_report_csv():
    donors = report_service.get_all_donors()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["DonorID", "Name", "Surname", "Email", "PhoneNumber", "#money", "#items"])

    for d in donors:
        mcount = len(d.donations_money)
        icount = len(d.donations_items)
        writer.writerow([d.donor_id, d.first_name, d.last_name, d.email, d.phone_number, mcount, icount])

    csv_data = output.getvalue()
    output.close()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-disposition": "attachment; filename=donor_report.csv"})


@bp.route('/donor-report')
@roles_required(['organization', 'donor', 'authorities'])
def donor_report():
    donor_id = request.args.get('donor_id', type=int)

    if not donor_id:
        message = _l('Please specify donor id!')
        return f'<h3>{message}</h3>', 400

    donor = db.session.get(Donor, donor_id)

    if not donor:
        message = _l('There is no donor with specified id!')
        return f'<h3>{message}</h3>', 400

    theme = get_theme()

    donations_item_query = db.session.query(
        DonationType.type.label('donation_type'), db.func.count(DonationItem.id).label('donation_count')
    ).join(DonationItem, DonationItem.donation_type_id == DonationType.id).filter(
        DonationItem.donor_id == donor_id
    ).group_by(DonationType.type)

    donations_money_query = db.session.query(
        DonationType.type.label('donation_type'), db.func.count(DonationMoney.id).label('donation_count')
    ).join(DonationMoney, DonationMoney.donation_type_id == DonationType.id).filter(
        DonationMoney.donor_id == donor_id
    ).group_by(DonationType.type)

    donations_union_query = donations_item_query.union(donations_money_query).subquery()

    donations_item = db.session.query(
        donations_union_query.c.donation_type, db.func.sum(donations_union_query.c.donation_count)
    ).group_by(donations_union_query.c.donation_type).all()

    donations_type = [donation[0] for donation in donations_item]
    donations_count = [donation[1] for donation in donations_item]

    df_donations_item = pd.DataFrame({
        'donation_type': donations_type,
        'donation_count': donations_count,
    })

    donations_money = donor.donations_money
    donations_item = donor.donations_items

    donations_money_sum = sum(donation.cashAmount for donation in donations_money)
    donations_money_count = len(donations_money)

    donations_item_count = len(donations_item)

    all_donations_count = donations_money_count + donations_item_count

    donations_type_chart = px.bar(df_donations_item, x='donation_type', y='donation_count', title='Donations by Type', template=theme)
    donations_type_chart_json = json.dumps(donations_type_chart, cls=PlotlyJSONEncoder)

    return render_template('donor_report.jinja',
                           donor=donor,
                           all_donations_count=all_donations_count,
                           donations_money_sum=donations_money_sum,
                           df_donations_item=df_donations_item,
                           donations_type_chart_json=donations_type_chart_json)


@bp.route('/single-donor-report-csv')
@roles_required(['organization', 'donor', 'authorities', 'admin'])
def single_donor_report_csv():
    donor_id = request.args.get('donor_id', type=int)
    if not donor_id:
        return "Brak parametru donor_id", 400

    donor = db.session.get(Donor, donor_id)
    if not donor:
        return f"Donor o ID={donor_id} nie istnieje!", 404

    output = io.StringIO()
    fieldnames = ["kind", "donation_id", "description", "donation_date",
                  "donation_type_or_id", "amount", "campaign_name"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for dm in donor.donations_money:
        if dm.charity_campaign and dm.charity_campaign.charity_campaign:
            camp_name = dm.charity_campaign.charity_campaign.name
        else:
            camp_name = "Brak kampanii"

        row = {
            "kind": "MONEY",
            "donation_id": dm.donationMoney_id,
            "description": dm.description,
            "donation_date": dm.donation_date,
            "donation_type_or_id": dm.donation_type or "N/A",
            "amount": dm.cashAmount,
            "campaign_name": camp_name
        }
        writer.writerow(row)

    for di in donor.donations_items:
        if di.charity_campaign and di.charity_campaign.charity_campaign:
            camp_name = di.charity_campaign.charity_campaign.name
        else:
            camp_name = "Brak kampanii"

        row = {
            "kind": "ITEM",
            "donation_id": di.donationItem_id,
            "description": di.description,
            "donation_date": di.donation_date,
            "donation_type_or_id": f"TypeID={di.donation_type_id}",
            "amount": di.amount,
            "campaign_name": camp_name
        }
        writer.writerow(row)

    csv_data = output.getvalue()
    output.close()
    return Response(csv_data, mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename=donor_{donor_id}_report.csv"})


# =================== RAPORT ORGANIZATION ===================
@bp.route('/organization-report')
@roles_required(['organization', 'authorities'])
def organization_report():
    campaign_id = request.args.get('campaign_id', type=int)
    if not campaign_id:
        message = _l('Please specify campaign id!')
        return f'<h3>{message}</h3>', 400

    campaign = CharityCampaign.query.get(campaign_id)
    if not campaign:
        message = _l('There is no campaign with specified id!')
        return f'<h3>{message}</h3>', 400

    theme = get_theme()

    org_campaigns = db.session.query(OrganizationCharityCampaign).filter_by(charity_campaign_id=campaign_id).all()

    org_data = []
    for org_campaign in org_campaigns:
        org = org_campaign.organization

        item_stocks = db.session.query(
            ItemStock.item_type_id, db.func.sum(ItemStock.amount)
        ).filter(ItemStock.organization_charity_campaign_id == org_campaign.id).group_by(ItemStock.item_type_id).all()

        item_stock_data = {item_type_id: amount for item_type_id, amount in item_stocks}

        affected_requests_count = db.session.query(db.func.count(Request.id)).join(Affected).filter(
            Request.charity_campaign_id == org_campaign.id).scalar()

        volunteer_tasks_count = db.session.query(db.func.count(Task.id)).join(Volunteer).filter(
            Task.charity_campaign_id == org_campaign.id).scalar()

        volunteers_count = db.session.query(db.func.count(Volunteer.id)).filter(
            Volunteer.campaigns.any(OrganizationCharityCampaign.id == org.id)
        ).scalar()

        donations_money_count = db.session.query(db.func.count(DonationMoney.donationMoney_id)).filter(
            DonationMoney.charity_campaign_id == org.id).scalar()

        donations_item_count = db.session.query(db.func.count(DonationItem.donationItem_id)).filter(
            DonationItem.charity_campaign_id == org.id).scalar()

        org_data.append({
            'organization': org.organization_name,
            'item_stock_data': item_stock_data,
            'affected_requests_count': affected_requests_count,
            'volunteer_tasks_count': volunteer_tasks_count,
            'volunteers_count': volunteers_count,
            'donations_money_count': donations_money_count,
            'donations_item_count': donations_item_count
        })

    df_org_data = pd.DataFrame(org_data)

    item_stock_chart = px.bar(df_org_data.explode('item_stock_data'), x='organization', y='item_stock_data', title='Item Stock by Organization', template=theme)
    affected_requests_chart = px.bar(df_org_data, x='organization', y='affected_requests_count', title='Affected Requests by Organization', template=theme)
    volunteer_tasks_chart = px.bar(df_org_data, x='organization', y='volunteer_tasks_count', title='Volunteer Tasks by Organization', template=theme)
    donations_chart = px.bar(df_org_data, x='organization', y=['donations_money_count', 'donations_item_count'], title='Donations by Organization', template=theme)

    item_stock_chart_json = json.dumps(item_stock_chart, cls=PlotlyJSONEncoder)
    affected_requests_chart_json = json.dumps(affected_requests_chart, cls=PlotlyJSONEncoder)
    volunteer_tasks_chart_json = json.dumps(volunteer_tasks_chart, cls=PlotlyJSONEncoder)
    donations_chart_json = json.dumps(donations_chart, cls=PlotlyJSONEncoder)

    return render_template('organization_report.jinja',
                           campaign=campaign,
                           org_data=org_data,
                           item_stock_chart_json=item_stock_chart_json,
                           affected_requests_chart_json=affected_requests_chart_json,
                           volunteer_tasks_chart_json=volunteer_tasks_chart_json,
                           donations_chart_json=donations_chart_json,
                           theme=theme)


@bp.route('/organization-report-csv')
@roles_required(['organization', 'authorities'])
def organization_report_csv():
    org_list = report_service.get_all_organizations()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "Description", "Approved?", "Campaigns Count", "Volunteers Count"])

    for org in org_list:
        camp_count = report_service.count_campaigns_per_organization(org)
        vol_count = report_service.count_volunteers_per_organization(org)
        writer.writerow([
            org.id,
            org.organization_name or "",
            org.description or "",
            org.approved,
            camp_count,
            vol_count
        ])

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=organization_report.csv"}
    )
