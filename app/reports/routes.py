import csv
import io

from flask import Blueprint, Response, render_template, request
from flask_login import login_required

from app.extensions import db
from app.models.affected import Affected
from app.models.donor import Donor
from app.models.charity_campaign import OrganizationCharityCampaign
from app.auth.user_service import roles_required

from .chart_utils import create_bar_chart_base64
from .report_service import ReportService


bp = Blueprint("reports", __name__, template_folder="templates/reports", static_folder="../static/reports")
report_service = ReportService()


@bp.route('/ui', methods=['GET'])
@login_required
def ui():
    return render_template('reports/reports_ui.jinja')


# =================== RAPORT AFFECTED ===================
@bp.route('/affected-report', methods=['GET'])
@login_required
@roles_required(['authorities', 'organization', 'admin'])
def affected_report():
    affected_list = db.session.query(Affected).all()

    city_stats = report_service.stats_by_city()
    voiv_stats = report_service.stats_by_voivodeship()
    needs_stats = report_service.stats_by_needs()

    city_chart_b64 = create_bar_chart_base64(city_stats, "Affected wg Miasta")
    voiv_chart_b64 = create_bar_chart_base64(voiv_stats, "Affected wg Województwa")
    needs_chart_b64 = create_bar_chart_base64(needs_stats, "Affected wg Needs")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Raport Affected</title>
      <link rel="stylesheet" type="text/css" href="../../static/style.css">
    </head>
    <body class="bg-light">
      <div class="container mt-5">
        <h1 class="text-primary text-center">Raport Affected</h1>

        <h2>Wykresy</h2>
        <div>
          <img src="data:image/png;base64,{city_chart_b64}" alt="Affected by city"/>
          <img src="data:image/png;base64,{voiv_chart_b64}" alt="Affected by voiv"/>
          <img src="data:image/png;base64,{needs_chart_b64}" alt="Affected by needs"/>
        </div>

        <h2>Szczegóły</h2>
    """

    for aff in affected_list:
        city = aff.address.city if aff.address else ""
        voiv = aff.address.voivodeship if aff.address else ""
        camp_name = aff.campaign.name if aff.campaign else "Brak kampanii"
        camp_desc = aff.campaign.description if aff.campaign else ""

        html += f"""
        <div class="border p-3 mb-3 bg-white">
          <h3>Affected ID={aff.id}: {aff.first_name} {aff.last_name}</h3>
          <p>Needs: {aff.needs or ""}</p>
          <p>Adres: {city}, {voiv}</p>
          <p>Kampania: {camp_name} - {camp_desc}</p>
        """

        req_list = aff.requests
        if req_list:
            html += "<h4>Requesty:</h4><ul>"
            for r in req_list:
                donation_type_str = getattr(r, "donation_type", "N/A")
                req_city = r.req_address.city if r.req_address else ""
                req_voiv = r.req_address.voivodeship if r.req_address else ""
                html += (f"<li>ReqID={r.id}, name={r.name}, status={r.status.value},"
                         f" type={donation_type_str}, amount={r.amount}, address=({req_city},{req_voiv})</li>")
            html += "</ul>"
        else:
            html += "<p>Brak requestów.</p>"

        html += "</div>"

    html += """
        <div class="mt-4">
          <a href="/reports/affected-report-csv" class="btn btn-success">Pobierz CSV</a>
          <a href="/reports/ui" class="btn btn-secondary">Powrót</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html


@bp.route('/affected-report-csv', methods=['GET'])
@login_required
@roles_required(['authorities', 'organization', 'admin'])
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
@bp.route('/volunteer-report', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
def volunteer_report():
    volunteer_list = report_service.get_all_volunteers()
    city_stats = report_service.stats_by_city_volunteer()
    tasks_stats = report_service.stats_volunteer_task_count()

    city_chart_b64 = create_bar_chart_base64(city_stats, "Volunteer wg Miasta")
    tasks_chart_b64 = create_bar_chart_base64(tasks_stats, "Volunteer wg liczby zadań")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Raport Volunteer</title>
      <link rel="stylesheet" type="text/css" href="../../static/style.css">
    </head>
    <body class="bg-light">
      <div class="container mt-5">
        <h1 class="text-primary text-center">Raport Volunteer</h1>

        <h2>1. Wykresy</h2>
        <div class="mb-4">
          <img src="data:image/png;base64,{city_chart_b64}" alt="Volunteer by city"/>
          <img src="data:image/png;base64,{tasks_chart_b64}" alt="Volunteer tasks count"/>
        </div>

        <h2>2. Lista Volunteer</h2>
        <table class="table table-bordered">
          <thead>
            <tr><th>ID</th><th>Imię</th><th>Nazwisko</th><th>Miasto/Woj.</th><th>Liczba zadań</th></tr>
          </thead>
          <tbody>
    """

    for vol in volunteer_list:
        city = vol.address.city if vol.address else ""
        voiv = vol.address.voivodeship if vol.address else ""
        tcount = len(vol.tasks)
        html += f"""
            <tr>
              <td>{vol.id}</td>
              <td>{vol.first_name}</td>
              <td>{vol.last_name}</td>
              <td>{city}/{voiv}</td>
              <td>{tcount}</td>
            </tr>
        """

    html += """
          </tbody>
        </table>
        <div class="mt-4">
          <a href="/reports/volunteer-report-csv" class="btn btn-success">Pobierz CSV</a>
          <a href="/reports/ui" class="btn btn-secondary">Powrót</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html


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
@bp.route('/donor-report', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
def donor_report():
    donors = report_service.get_all_donors()

    type_count_stats = report_service.stats_donation_type_count()
    sums_stats = report_service.stats_donation_sums()

    items_by_type_stats = report_service.stats_donation_items_by_type()
    money_by_campaign_stats = report_service.stats_donation_money_by_campaign()

    type_chart_b64 = create_bar_chart_base64(type_count_stats, "Donations: Money vs. Items")
    sums_chart_b64 = create_bar_chart_base64(sums_stats, "Total sums: cashAmount vs. item amount")
    items_by_type_chart_b64 = create_bar_chart_base64(items_by_type_stats, "DonationItems by Type (sum of amounts)")
    money_by_campaign_chart_b64 = create_bar_chart_base64(money_by_campaign_stats, "DonationMoney by Campaign (sum)")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Raport Donor</title>
      <link rel="stylesheet" type="text/css" href="../../static/style.css">
    </head>
    <body class="bg-light">
      <div class="container mt-5">
        <h1 class="text-primary text-center">Raport Donor</h1>

        <h2>1. Podstawowe statystyki</h2>
        <div>
          <img src="data:image/png;base64,{type_chart_b64}" alt="Money vs. Items"/>
          <img src="data:image/png;base64,{sums_chart_b64}" alt="Sum Money vs. Items"/>
        </div>

        <h2>2. Dodatkowe statystyki</h2>
        <div>
          <img src="data:image/png;base64,{items_by_type_chart_b64}" alt="Items by Type"/>
          <img src="data:image/png;base64,{money_by_campaign_chart_b64}" alt="Money by Campaign"/>
        </div>

        <h2>3. Lista Donorów</h2>
        <table class="table table-bordered">
          <thead>
            <tr>
              <th>ID</th>
              <th>Imię</th>
              <th>Nazwisko</th>
              <th>Email</th>
              <th>Telefon</th>
              <th>#money</th>
              <th>#items</th>
            </tr>
          </thead>
          <tbody>
    """

    for d in donors:
        mcount = len(d.donations_money)
        icount = len(d.donations_items)
        html += f"""
            <tr>
              <td>{d.donor_id}</td>
              <td>{d.first_name}</td>
              <td>{d.last_name}</td>
              <td>{d.email}</td>
              <td>{d.phone_number}</td>
              <td>{mcount}</td>
              <td>{icount}</td>
            </tr>
        """

    html += """
          </tbody>
        </table>
        <div class="mt-4">
          <a href="/reports/donor-report-csv" class="btn btn-success">Pobierz CSV</a>
          <a href="/reports/ui" class="btn btn-secondary">Powrót</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html


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


@bp.route('/single-donor-report', methods=['GET'])
@login_required
@roles_required(['organization', 'donor', 'authorities', 'admin'])
def single_donor_report():
    donor_id = request.args.get('donor_id', type=int)
    if not donor_id:
        return "<h3>Brak parametru donor_id!</h3>", 400

    donor = db.session.get(Donor, donor_id)
    if not donor:
        return f"<h3>Donor o ID={donor_id} nie istnieje!</h3>", 404

    mlist = donor.donations_money
    ilist = donor.donations_items

    total_money_sum = sum(m.cashAmount for m in mlist)
    total_item_sum = sum(i.amount for i in ilist)
    money_count = len(mlist)
    item_count = len(ilist)

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Single Donor {donor_id}</title>
      <link rel="stylesheet" type="text/css" href="../../static/style.css">
    </head>
    <body class="bg-light">
      <div class="container mt-5">
        <h1 class="text-primary text-center">Raport Donora {donor_id}</h1>
        <p>Imię: {donor.first_name}, nazwisko: {donor.last_name}, email: {donor.email}, tel: {donor.phone_number}</p>

        <h2>Podsumowanie</h2>
        <ul>
          <li>Liczba donation_money: {money_count}</li>
          <li>Liczba donation_items: {item_count}</li>
          <li>Suma kasy: {total_money_sum}</li>
          <li>Suma itemów: {total_item_sum}</li>
        </ul>

        <h3>DonationMoney</h3>
        <table class="table table-bordered">
          <thead>
            <tr><th>ID</th><th>Opis</th><th>Data</th><th>Kwota</th><th>Kampania</th><th>Typ(str)?</th></tr>
          </thead>
          <tbody>
    """
    for dm in mlist:
        if dm.charity_campaign and dm.charity_campaign.charity_campaign:
            camp_name = dm.charity_campaign.charity_campaign.name
        else:
            camp_name = "Brak kampanii"

        donation_type_str = dm.donation_type or "N/A"
        html += f"""
            <tr>
              <td>{dm.donationMoney_id}</td>
              <td>{dm.description}</td>
              <td>{dm.donation_date}</td>
              <td>{dm.cashAmount}</td>
              <td>{camp_name}</td>
              <td>{donation_type_str}</td>
            </tr>
        """

    html += """
          </tbody>
        </table>

        <h3>DonationItem</h3>
        <table class="table table-bordered">
          <thead>
            <tr><th>ID</th><th>Opis</th><th>Data</th><th>TypID</th><th>Ilość</th><th>Kampania</th></tr>
          </thead>
          <tbody>
    """

    for di in ilist:
        if di.charity_campaign and di.charity_campaign.charity_campaign:
            camp_name = di.charity_campaign.charity_campaign.name
        else:
            camp_name = "Brak kampanii"

        donation_type_str = f"TypeID={di.donation_type_id}"
        html += f"""
            <tr>
              <td>{di.donationItem_id}</td>
              <td>{di.description}</td>
              <td>{di.donation_date}</td>
              <td>{donation_type_str}</td>
              <td>{di.amount}</td>
              <td>{camp_name}</td>
            </tr>
        """

    html += f"""
          </tbody>
        </table>
        <div class="mt-4">
          <a href="/reports/single-donor-report-csv?donor_id={donor_id}" class="btn btn-success">
            Pobierz CSV
          </a>
          <a href="/reports/ui" class="btn btn-secondary">Powrót</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html


@bp.route('/single-donor-report-csv', methods=['GET'])
@login_required
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
@bp.route('/organization-report', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
def organization_report():
    approval_stats = report_service.stats_organization_approval()
    approval_chart_b64 = create_bar_chart_base64(
        approval_stats,
        "Organization: Approved vs. Not Approved"
    )

    org_list = report_service.get_all_organizations()

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8"/>
      <title>Raport Organization</title>
      <link rel="stylesheet" type="text/css" href="../../static/style.css">
    </head>
    <body class="bg-light">
      <div class="container mt-5">
        <h1 class="text-primary text-center">Raport Organization (z kampaniami)</h1>
        <p>Statystyki dot. organizacji i ich kampanii.</p>

        <h2>1. Wykres: Approved vs. Not Approved</h2>
        <img src="data:image/png;base64,{approval_chart_b64}" alt="Org Approved" />

        <hr/>
        <h2>2. Lista Organization</h2>
        <p>Niżej: kampanie i liczba wolontariuszy.</p>
    """

    for org in org_list:
        camp_count = report_service.count_campaigns_per_organization(org)
        vol_count = report_service.count_volunteers_per_organization(org)

        html += f"""
        <div class="bg-white border p-3 mb-4">
          <h3>Organizacja: {org.organization_name or ""} (ID={org.id})</h3>
          <p><strong>Opis:</strong> {org.description or ""}</p>
          <p><strong>Approved?</strong> {org.approved}</p>
          <p><strong>Liczba kampanii:</strong> {camp_count}, <strong>Wolontariuszy:</strong> {vol_count}</p>
        """

        # Kampanie
        org_campaigns = db.session.query(OrganizationCharityCampaign).filter_by(organization_id=org.id).all()
        html += """
          <h4>Kampanie tej organizacji:</h4>
          <table class="table table-bordered">
            <thead>
              <tr>
                <th>Campaign ID</th>
                <th>Nazwa kampanii</th>
                <th>Opis kampanii</th>
                <th>Liczba wolontariuszy</th>
              </tr>
            </thead>
            <tbody>
        """
        for oc in org_campaigns:
            c = oc.charity_campaign
            camp_name = c.name if c else "Brak nazwy"
            camp_desc = c.description if c else "Brak opisu"
            volunteers_count = len(oc.volunteers)
            html += f"""
            <tr>
              <td>{oc.id}</td>
              <td>{camp_name}</td>
              <td>{camp_desc}</td>
              <td>{volunteers_count}</td>
            </tr>
            """

        html += """
            </tbody>
          </table>
        </div>
        """

    html += """
        <div class="mt-4">
          <a href="/reports/organization-report-csv" class="btn btn-success">Pobierz CSV</a>
          <a href="/reports/ui" class="btn btn-secondary">Powrót</a>
        </div>
      </div>
    </body>
    </html>
    """
    return html


@bp.route('/organization-report-csv', methods=['GET'])
@login_required
@roles_required(['organization', 'authorities', 'admin'])
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
