from flask import (Blueprint, abort, flash, redirect, render_template, request,
                   url_for)
from flask_babel import gettext as _
from flask_login import current_user

from app.auth.user_service import roles_required
from app.extensions import db
from app.models.address import Address
from app.models.evaluation import Evaluation
from app.models.task import Task
from app.models.volunteer import Volunteer
from app.forms.volunteers_wtf import UpdateTaskStatusForm

bp = Blueprint('volunteers', __name__,
               template_folder='../templates/volunteers',
               static_folder='static',
               static_url_path='volunteers')


@bp.route('volunteer/profile')
@roles_required(['volunteer'])
def volunteer_profile():
    volunteer = db.session.get(Volunteer, current_user.volunteer.id)
    return render_template('volunteer_profile.jinja', volunteer=volunteer)


@bp.route('task/update-status/<int:task_id>', methods=['GET', 'POST'])
@roles_required(['volunteer'])
def update_task_status(task_id):
    task = db.session.get(Task, task_id)
    volunteer = db.session.scalar(db.select(Volunteer).where(Volunteer.user_id == current_user.id))
    if not task or not volunteer:
        return abort(404)
    if task.volunteer_id != volunteer.id:
        return abort(403)

    form = UpdateTaskStatusForm()
    form.status.choices = [(status, _(status.capitalize())) for status in task.AVAILABLE_STATUS]

    if form.validate_on_submit():
        task.status = form.status.data
        db.session.commit()
        return redirect(url_for('volunteers.list_my_tasks'))

    referrer = url_for('volunteers.list_my_tasks')
    return render_template('update_task_status.jinja', task=task, form=form, referrer=referrer)


@bp.route('volunteer/charity_campaign/<int:charity_campaign_id>/tasks')
@roles_required(['volunteer'])
def list_tasks_by_charity_campaign(charity_campaign_id):
    volunteer = db.session.scalar(db.select(Volunteer).where(Volunteer.user_id == current_user.id))
    if volunteer is None:
        return 'Volunteer not found', 404
    status_translations = {
        'completed': _('Completed'),
        'ongoing': _('Ongoing'),
        'rejected': _('Rejected')
    }
    referrer = request.referrer
    return render_template('volunteer_tasks.jinja',
                           volunteer=volunteer,
                           charity_campaign_id=charity_campaign_id,
                           status_translations=status_translations,
                           referrer=referrer)


@bp.route('/tasks')
@roles_required(['volunteer'])
def list_my_tasks():
    volunteer = db.session.scalar(db.select(Volunteer).where(Volunteer.user_id == current_user.id))
    status_translations = {
        'completed': _('Completed'),
        'ongoing': _('Ongoing'),
        'rejected': _('Rejected')
    }
    referrer = url_for('home')
    return render_template('volunteer_tasks.jinja',
                           volunteer=volunteer,
                           status_translations=status_translations,
                           referrer=referrer)

# =================== NOT USED ===================


@bp.route('/')
def index():
    samples_added = db.session.query(Volunteer).count() > 0
    return render_template('volunteers.jinja', samples_added=samples_added)


@bp.route('/all')
def fetch_all():
    volunteers = db.session.scalars(db.select(Volunteer))
    return render_template('view.jinja', volunteers=volunteers.all())


@bp.route('/tasks/<int:volunteer_id>')
@roles_required(['volunteer'])
def list_tasks(volunteer_id):
    volunteer = db.session.get(Volunteer, volunteer_id)
    if volunteer is None:
        return 'Volunteer not found', 404
    return render_template('tasks.jinja', volunteer=volunteer)


@bp.route('/tasks/create', methods=['GET', 'POST'])
def create_task():
    volunteers = db.session.scalars(db.select(Volunteer))
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        volunteer_id = request.form['volunteer_id']

        new_task = Task(name=name, description=description, volunteer_id=volunteer_id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('volunteers.index'))

    return render_template('create_task.jinja', volunteers=volunteers.all())


@bp.route('/tasks/evaluate/<int:task_id>', methods=['GET', 'POST'])
def eval_task(task_id):
    task = db.session.query(Task).filter_by(id=task_id).first()
    if task is None:
        flash('Task not found.')
        return redirect(url_for('volunteers.fetch_all'))

    if request.method == 'POST':
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
        return redirect(url_for('volunteers.list_tasks', volunteer_id=task.volunteer.id))

    return render_template('eval_task.jinja', task=task)


# =================== SAMPLES ===================

@bp.route('/samples', methods=['POST'])
def samples():
    if db.session.query(Volunteer).count() > 0:
        flash('Sample data already added!')
        return redirect(url_for('volunteers.index'))

    with db.session() as session:
        v1 = Volunteer(first_name='John', last_name='Black', email='jblack@mail.com', phone='111111111')
        a1 = Address(street='Miejska', street_number='1a', city='Łódź', voivodeship='Łódzkie')
        v1.address = a1
        t1 = Task(name='Test task', description='TestDesc', volunteer=v1)
        v1.tasks.append(t1)

        v2 = Volunteer(first_name='Sam', last_name='Smith', email='ssmith@mail.com', phone='222222222')
        a2 = Address(street='Wiejska', street_number='2b', city='Warsaw', voivodeship='Mazowieckie')
        v2.address = a2
        t2 = Task(name='Test task 2', description='TestDesc2', volunteer=v2)
        t3 = Task(name='Test task 3', description='TestDesc3', volunteer=v2)
        v2.tasks.append(t2)
        v2.tasks.append(t3)

        session.add(v1)
        session.add(v2)
        session.commit()

    flash('Sample data added successfully!')
    return redirect(url_for('volunteers.index'))
