import random
from flask import Blueprint, render_template, redirect, url_for
from flask import request
from task import Task
from flask_login import login_required, current_user
from models import db, Task, User, Visit, Waitlist
# import datetime
import datetime

# Create a blueprint
main_blueprint = Blueprint('main', __name__)


def log_visit(page, user_id):
    """Log a visit to a page by a user."""
    visit = Visit(page=page, user=user_id)
    db.session.add(visit)
    db.session.commit()


###############################################################################
# Routes
###############################################################################


@main_blueprint.route('/', methods=['GET'])
def index():
    log_visit(page='index', user_id=current_user.id if current_user.is_authenticated else None)

    # print all visits
    visits = Visit.query.all()
    for visit in visits:
        print(f"Visit: {visit.page}, User ID: {visit.user}, Timestamp: {visit.timestamp}")

    return render_template('index.html')

@main_blueprint.route('/invitation', methods=['GET', 'POST'])
def invitation():

    if request.method == 'POST':
        email = request.form['email']
        log_visit(page='waitlist_signup', user_id=current_user.id if current_user.is_authenticated else None)
        # Here you would send a verification email and add to waitlist
        print(f"Sending invitation to {email}")
    else:
        log_visit(page='invitation', user_id=current_user.id if current_user.is_authenticated else None)
    return render_template('invitation.html')


@main_blueprint.route('/todo', methods=['GET', 'POST'])
@login_required
def todo():
    log_visit(page='todo', user_id=current_user.id if current_user.is_authenticated else None)
    return render_template('todo.html')


@main_blueprint.route('/dashboard', methods=['GET', 'POST'])
# @login_required
def dashboard():
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=6)
    last_week_start = today - datetime.timedelta(days=13)
    last_week_end = today - datetime.timedelta(days=7)

    # Visits
    visits = Visit.query.order_by(Visit.timestamp.desc()).all()
    for v in visits:
        v.date = v.timestamp.strftime('%Y-%m-%d') if v.timestamp else ''
    visits_today = Visit.query.filter(db.func.date(Visit.timestamp) == today).count()
    total_users = User.query.count()
    tasks = Task.query.all()
    users = User.query.all()
    waitlist = Waitlist.query.filter(Waitlist.timestamp >= week_ago).all()

    # New users this week
    new_users = 0  # No date_created, so set to 0 or remove metric

    # Visits per day for index page (this week and last week)
    week_visits = []
    two_week_visits = []
    chart_week = [(today - datetime.timedelta(days=i)).strftime('%a') for i in range(6, -1, -1)]
    for i in range(6, -1, -1):
        day = today - datetime.timedelta(days=i)
        week_visits.append(Visit.query.filter(db.func.date(Visit.timestamp) == day, Visit.page == 'index').count())
        two_week_visits.append(Visit.query.filter(db.func.date(Visit.timestamp) == (day - datetime.timedelta(days=7)), Visit.page == 'index').count())

    # Bar chart: visits today for each page
    page_names = ['index', 'login-g', 'callback', 'user-name', 'license', 'waitlist', 'state-not-found', 'State-mismatch']
    page_visits = [Visit.query.filter(db.func.date(Visit.timestamp) == today, Visit.page == page).count() for page in page_names]

    # Productivity change
    week_total = sum(week_visits)
    two_week_total = sum(two_week_visits)
    productivity_change = ((week_total - two_week_total) / two_week_total * 100) if two_week_total else 0

    return render_template('admin.html',
                           date=datetime.datetime.now().strftime("%B %d, %Y"),
                           total_users=total_users,
                           new_users=new_users,
                           visits_today=visits_today,
                           productivity_change=productivity_change,
                           visits=visits,
                           chart_week=chart_week,
                           week_notes=week_visits,
                           two_week_notes=two_week_visits,
                           week_visits=week_visits,
                           two_week_visits=two_week_visits,
                           users=users,
                           tasks=tasks,
                           waitlist=waitlist,
                           page_visits=page_visits
                           )


@main_blueprint.route('/api/v1/tasks', methods=['GET'])
@login_required
def api_get_tasks():
    log_visit(page='api_get_tasks', user_id=current_user.id if current_user.is_authenticated else None)
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return {
        "tasks": [task.to_dict() for task in tasks]
    }


@main_blueprint.route('/api/v1/tasks', methods=['POST'])
@login_required
def api_create_task():
    log_visit(page='create_task', user_id=current_user.id if current_user.is_authenticated else None)
    data = request.get_json()
    new_task = Task(title=data['title'], user_id=current_user.id)
    db.session.add(new_task)
    db.session.commit()
    return {
        "task": new_task.to_dict()
    }, 201


@main_blueprint.route('/api/v1/tasks/<int:task_id>', methods=['PATCH'])
@login_required
def api_toggle_task(task_id):
    log_visit(page='toggle_task', user_id=current_user.id if current_user.is_authenticated else None)
    task = Task.query.get(task_id)

    if task is None:
        return {"error": "Task not found"}, 404

    task.toggle()
    db.session.commit()

    return {"task": task.to_dict()}, 200


@main_blueprint.route('/remove/<int:task_id>')
@login_required
def remove(task_id):
    log_visit(page='delete_task', user_id=current_user.id if current_user.is_authenticated else None)
    task = Task.query.get(task_id)

    if task is None:
        return redirect(url_for('main.todo'))

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for('main.todo'))