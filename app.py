import os
import calendar as pycal
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text


app = Flask(__name__)

app.secret_key = 'change_this_to_a_random_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Date formatting
@app.template_filter('format_date')
def format_date(date_str):

    if not date_str:
        return ""

    try:
        dt = datetime.strptime(str(date_str).strip(), '%Y-%m-%d')
        return f"{dt.strftime('%B')} {dt.day}, {dt.year}"

    except Exception:
        return date_str


# Time formatting
@app.template_filter('format_time')
def format_time(time_str):

    if not time_str:
        return ""

    try:
        dt = datetime.strptime(str(time_str).strip()[:5], '%H:%M')

        hour = dt.hour % 12 or 12
        ampm = "AM" if dt.hour < 12 else "PM"

        return f"{hour}:{dt.minute:02d} {ampm}"

    except Exception:
        return time_str


# Teacher database table
class Teacher(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False
    )

    subject = db.Column(
        db.String(500),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(256),
        nullable=False
    )

    slots = db.relationship(
        'TimeSlot',
        backref='teacher',
        lazy=True
    )


# Time slot database table
class TimeSlot(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    teacher_id = db.Column(
        db.Integer,
        db.ForeignKey('teacher.id'),
        nullable=False
    )

    date = db.Column(
        db.String(10),
        nullable=False
    )

    start_time = db.Column(
        db.String(5),
        nullable=False
    )

    end_time = db.Column(
        db.String(5),
        nullable=False
    )

    is_booked = db.Column(
        db.Boolean,
        default=False
    )

    parent_name = db.Column(
        db.String(100),
        nullable=True
    )

    student_name = db.Column(
        db.String(100),
        nullable=True
    )

    course = db.Column(
        db.String(200),
        nullable=True
    )


# Create database
with app.app_context():

    db.create_all()

    # Adds the course column automatically if an older database already exists
    columns = db.session.execute(
        text("PRAGMA table_info(time_slot)")
    ).fetchall()

    column_names = [
        column[1] for column in columns
    ]

    if "course" not in column_names:

        db.session.execute(
            text(
                "ALTER TABLE time_slot "
                "ADD COLUMN course VARCHAR(200)"
            )
        )

        db.session.commit()


# Homepage
@app.route('/')
def index():

    return render_template(
        'index.html'
    )


# Shared calendar
@app.route('/calendar')
def shared_calendar():

    now = datetime.now()

    year = request.args.get(
        'year',
        default=now.year,
        type=int
    )

    month = request.args.get(
        'month',
        default=now.month,
        type=int
    )

    selected_date = request.args.get(
        'date',
        default=''
    )

    teacher_filter = request.args.get(
        'teacher_id',
        type=int
    )


    # Previous and next month
    if month == 1:

        prev_month = 12
        prev_year = year - 1

    else:

        prev_month = month - 1
        prev_year = year


    if month == 12:

        next_month = 1
        next_year = year + 1

    else:

        next_month = month + 1
        next_year = year


    # Get slots
    query = TimeSlot.query

    if teacher_filter:

        query = query.filter_by(
            teacher_id=teacher_filter
        )

    all_slots = query.order_by(
        TimeSlot.date,
        TimeSlot.start_time
    ).all()


    # Count open/booked slots for each day
    slot_counts = {}

    for slot in all_slots:

        if slot.date not in slot_counts:

            slot_counts[slot.date] = {
                'open': 0,
                'booked': 0
            }

        if slot.is_booked:

            slot_counts[slot.date]['booked'] += 1

        else:

            slot_counts[slot.date]['open'] += 1


    # Build calendar
    pycal.setfirstweekday(
        pycal.SUNDAY
    )

    month_matrix = pycal.monthcalendar(
        year,
        month
    )

    month_name = datetime(
        year,
        month,
        1
    ).strftime('%B %Y')


    # Selected date slots
    if selected_date:

        day_slots = [
            slot
            for slot in all_slots
            if slot.date == selected_date
        ]

    else:

        day_slots = []


    teachers = Teacher.query.all()

    logged_in_teacher = session.get(
        'teacher_id'
    )


    return render_template(

        'calendar.html',

        month_matrix=month_matrix,

        month_name=month_name,

        year=year,

        month=month,

        prev_year=prev_year,

        prev_month=prev_month,

        next_year=next_year,

        next_month=next_month,

        slot_counts=slot_counts,

        selected_date=selected_date,

        day_slots=day_slots,

        teachers=teachers,

        selected_teacher=teacher_filter,

        is_teacher=(
            'teacher_id' in session
        ),

        logged_in_teacher=logged_in_teacher
    )


# Parent reservation page
@app.route('/reserve', methods=['GET', 'POST'])
def reserve():

    if request.method == 'POST':

        slot_id = request.form.get(
            'slot_id'
        )

        slot = TimeSlot.query.get_or_404(
            slot_id
        )

        if not slot.is_booked:

            slot.is_booked = True

            slot.parent_name = request.form.get(
                'parent_name'
            )

            slot.student_name = request.form.get(
                'student_name'
            )

            slot.course = request.form.get(
                'course'
            )

            db.session.commit()

            return redirect(
                url_for(
                    'confirmation',
                    slot_id=slot.id
                )
            )

        else:

            flash(
                "That meeting time has already been booked.",
                "warning"
            )


    teacher_filter = request.args.get(
        'teacher_id',
        type=int
    )

    teachers = Teacher.query.all()

    query = TimeSlot.query

    if teacher_filter:

        query = query.filter_by(
            teacher_id=teacher_filter
        )

    slots = query.order_by(
        TimeSlot.date,
        TimeSlot.start_time
    ).all()


    return render_template(

        'reserve.html',

        slots=slots,

        teachers=teachers,

        selected_teacher=teacher_filter
    )


# Reservation confirmation
@app.route('/confirmation/<int:slot_id>')
def confirmation(slot_id):

    slot = TimeSlot.query.get_or_404(
        slot_id
    )

    return render_template(
        'confirmation.html',
        slot=slot
    )


# Teacher registration and login
@app.route('/teacher/auth', methods=['GET', 'POST'])
def teacher_auth():

    if 'teacher_id' in session:

        return redirect(
            url_for('teacher_dashboard')
        )


    if request.method == 'POST':

        action = request.form.get(
            'action'
        )


        # REGISTER
        if action == 'register':

            email = request.form.get(
                'email'
            ).lower().strip()


            if not (
                email.startswith('p')
                and email.endswith('@pdsb.net')
            ):

                flash(
                    "Only valid PDSB teacher emails can register.",
                    "danger"
                )

                return redirect(
                    url_for('teacher_auth')
                )


            existing_teacher = Teacher.query.filter_by(
                email=email
            ).first()


            if existing_teacher:

                flash(
                    "An account with that email already exists.",
                    "warning"
                )

                return redirect(
                    url_for('teacher_auth')
                )


            # Read all classes from the registration form
            grades = request.form.getlist(
                'grade[]'
            )

            subjects = request.form.getlist(
                'subject[]'
            )

            codes = request.form.getlist(
                'code[]'
            )


            classes = []


            for grade, subject, code in zip(
                grades,
                subjects,
                codes
            ):

                grade = grade.strip()
                subject = subject.strip()
                code = code.strip()


                if subject:

                    class_name = grade + " - " + subject

                    if code:

                        class_name += (
                            " (" + code + ")"
                        )

                    classes.append(
                        class_name
                    )


            # Make one string containing all classes
            teacher_classes = ", ".join(
                classes
            )


            if not teacher_classes:

                flash(
                    "Please enter at least one class.",
                    "danger"
                )

                return redirect(
                    url_for('teacher_auth')
                )


            new_teacher = Teacher(

                name=request.form.get(
                    'name'
                ).strip(),

                subject=teacher_classes,

                email=email,

                password_hash=
                generate_password_hash(
                    request.form.get(
                        'password'
                    )
                )
            )


            db.session.add(
                new_teacher
            )

            db.session.commit()


            session['teacher_id'] = (
                new_teacher.id
            )

            session['teacher_name'] = (
                new_teacher.name
            )


            return redirect(
                url_for(
                    'teacher_dashboard'
                )
            )


        # LOGIN
        elif action == 'login':

            email = request.form.get(
                'email'
            ).lower().strip()


            teacher = Teacher.query.filter_by(
                email=email
            ).first()


            if teacher and check_password_hash(

                teacher.password_hash,

                request.form.get(
                    'password'
                )
            ):

                session['teacher_id'] = (
                    teacher.id
                )

                session['teacher_name'] = (
                    teacher.name
                )

                return redirect(
                    url_for(
                        'teacher_dashboard'
                    )
                )


            else:

                flash(
                    "Incorrect email or password.",
                    "danger"
                )


    return render_template(
        'teacher_auth.html'
    )


# Teacher logout
@app.route('/teacher/logout')
def teacher_logout():

    session.clear()

    return redirect(
        url_for('index')
    )


# Teacher dashboard
@app.route('/teacher/dashboard')
def teacher_dashboard():

    if 'teacher_id' not in session:

        return redirect(
            url_for('teacher_auth')
        )


    teacher = Teacher.query.get_or_404(
        session['teacher_id']
    )


    slots = TimeSlot.query.filter_by(

        teacher_id=teacher.id

    ).order_by(

        TimeSlot.date,
        TimeSlot.start_time

    ).all()


    return render_template(

        'teacher_dashboard.html',

        teacher=teacher,

        slots=slots
    )


# Add or update teacher slot
@app.route('/teacher/slot/save', methods=['POST'])
def save_slot():

    if 'teacher_id' not in session:

        return redirect(
            url_for('teacher_auth')
        )


    slot_id = request.form.get(
        'slot_id'
    )


    if slot_id:

        slot = TimeSlot.query.filter_by(

            id=slot_id,

            teacher_id=session[
                'teacher_id'
            ]

        ).first_or_404()


        slot.date = request.form.get(
            'date'
        )

        slot.start_time = request.form.get(
            'start_time'
        )

        slot.end_time = request.form.get(
            'end_time'
        )


        if request.form.get(
            'clear_booking'
        ):

            slot.is_booked = False

            slot.parent_name = None

            slot.student_name = None

            slot.course = None


    else:

        new_slot = TimeSlot(

            teacher_id=session[
                'teacher_id'
            ],

            date=request.form.get(
                'date'
            ),

            start_time=request.form.get(
                'start_time'
            ),

            end_time=request.form.get(
                'end_time'
            )
        )


        db.session.add(
            new_slot
        )


    db.session.commit()


    return redirect(

        request.referrer

        or url_for(
            'teacher_dashboard'
        )
    )


# Delete teacher slot
@app.route(
    '/teacher/slot/delete/<int:slot_id>',
    methods=['POST']
)
def delete_slot(slot_id):

    if 'teacher_id' in session:

        slot = TimeSlot.query.filter_by(

            id=slot_id,

            teacher_id=session[
                'teacher_id'
            ]

        ).first_or_404()


        db.session.delete(
            slot
        )

        db.session.commit()


    return redirect(

        request.referrer

        or url_for(
            'teacher_dashboard'
        )
    )


# API slot data
@app.route('/api/slots')
def api_slots():

    teacher_id = request.args.get(
        'teacher_id',
        type=int
    )


    query = TimeSlot.query


    if teacher_id:

        query = query.filter_by(
            teacher_id=teacher_id
        )


    slots = query.all()


    logged_in_teacher = session.get(
        'teacher_id'
    )


    events = []


    for slot in slots:

        is_owner = (
            logged_in_teacher
            == slot.teacher_id
        )


        if slot.is_booked:

            if is_owner:

                label = (
                    f"Booked "
                    f"({slot.student_name})"
                )

            else:

                label = (
                    f"Taken - "
                    f"{slot.teacher.name}"
                )

        else:

            label = (
                f"Open - "
                f"{slot.teacher.name}"
            )


        events.append({

            'id': slot.id,

            'title':
            f"{slot.start_time} {label}",

            'start':
            f"{slot.date}T"
            f"{slot.start_time}:00",

            'end':
            f"{slot.date}T"
            f"{slot.end_time}:00",

            'color':
            '#C97A7E'
            if slot.is_booked
            else '#A6896F',

            'extendedProps': {

                'teacher_id':
                slot.teacher_id,

                'teacher_name':
                slot.teacher.name,

                'subject':
                slot.teacher.subject,

                'course':
                slot.course
                if is_owner else '',

                'date':
                slot.date,

                'start_time':
                slot.start_time,

                'end_time':
                slot.end_time,

                'is_booked':
                slot.is_booked,

                'is_owner':
                is_owner,

                'parent_name':
                slot.parent_name
                if is_owner else '',

                'student_name':
                slot.student_name
                if is_owner else ''
            }
        })


    return jsonify(
        events
    )


if __name__ == "__main__":

    app.run(
        debug=True
    )
