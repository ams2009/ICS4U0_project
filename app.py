from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'change_this_to_a_random_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reservations.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    slots = db.relationship('TimeSlot', backref='teacher', lazy=True)

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    parent_name = db.Column(db.String(100), nullable=True)
    student_name = db.Column(db.String(100), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calendar')
def shared_calendar():
    teachers = Teacher.query.all()
    is_teacher = 'teacher_id' in session
    return render_template('calendar.html', teachers=teachers, is_teacher=is_teacher)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        slot = TimeSlot.query.get_or_404(slot_id)
        if not slot.is_booked:
            slot.is_booked = True
            slot.parent_name = request.form.get('parent_name')
            slot.student_name = request.form.get('student_name')
            db.session.commit()
            return redirect(url_for('confirmation', slot_id=slot.id))

    teacher_filter = request.args.get('teacher_id', type=int)
    teachers = Teacher.query.all()
    query = TimeSlot.query
    if teacher_filter:
        query = query.filter_by(teacher_id=teacher_filter)
    slots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    return render_template('reserve.html', slots=slots, teachers=teachers, selected_teacher=teacher_filter)

@app.route('/confirmation/<int:slot_id>')
def confirmation(slot_id):
    slot = TimeSlot.query.get_or_404(slot_id)
    return render_template('confirmation.html', slot=slot)

@app.route('/teacher/auth', methods=['GET', 'POST'])
def teacher_auth():
    if 'teacher_id' in session:
        return redirect(url_for('teacher_dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'register':
            email = request.form.get('email').lower().strip()
            if not (email.startswith('p') and email.endswith('@pdsb.net')):
                flash("Only emails starting with 'p' and ending with '@pdsb.net' can register", "danger")
                return redirect(url_for('teacher_auth'))

            if Teacher.query.filter_by(email=email).first():
                flash("An account with that email already exists", "warning")
                return redirect(url_for('teacher_auth'))

            new_teacher = Teacher(
                name=request.form.get('name'),
                subject=request.form.get('subject'),
                email=email,
                password_hash=generate_password_hash(request.form.get('password'))
            )
            db.session.add(new_teacher)
            db.session.commit()
            session['teacher_id'] = new_teacher.id
            session['teacher_name'] = new_teacher.name
            return redirect(url_for('teacher_dashboard'))

        elif action == 'login':
            email = request.form.get('email').lower().strip()
            teacher = Teacher.query.filter_by(email=email).first()
            if teacher and check_password_hash(teacher.password_hash, request.form.get('password')):
                session['teacher_id'] = teacher.id
                session['teacher_name'] = teacher.name
                return redirect(url_for('teacher_dashboard'))
            else:
                flash("Incorrect email or password", "danger")

    return render_template('teacher_auth.html')

@app.route('/teacher/logout')
def teacher_logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_auth'))
    teacher = Teacher.query.get_or_404(session['teacher_id'])
    slots = TimeSlot.query.filter_by(teacher_id=teacher.id).order_by(TimeSlot.date, TimeSlot.start_time).all()
    return render_template('teacher_dashboard.html', teacher=teacher, slots=slots)

@app.route('/teacher/slot/save', methods=['POST'])
def save_slot():
    if 'teacher_id' not in session:
        return redirect(url_for('teacher_auth'))

    slot_id = request.form.get('slot_id')
    if slot_id:
        slot = TimeSlot.query.filter_by(id=slot_id, teacher_id=session['teacher_id']).first_or_404()
        slot.date = request.form.get('date')
        slot.start_time = request.form.get('start_time')
        slot.end_time = request.form.get('end_time')
        if request.form.get('clear_booking'):
            slot.is_booked = False
            slot.parent_name = None
            slot.student_name = None
    else:
        new_slot = TimeSlot(
            teacher_id=session['teacher_id'],
            date=request.form.get('date'),
            start_time=request.form.get('start_time'),
            end_time=request.form.get('end_time')
        )
        db.session.add(new_slot)

    db.session.commit()
    return redirect(request.referrer or url_for('teacher_dashboard'))

@app.route('/teacher/slot/delete/<int:slot_id>', methods=['POST'])
def delete_slot(slot_id):
    if 'teacher_id' in session:
        slot = TimeSlot.query.filter_by(id=slot_id, teacher_id=session['teacher_id']).first_or_404()
        db.session.delete(slot)
        db.session.commit()
    return redirect(request.referrer or url_for('teacher_dashboard'))

@app.route('/api/slots')
def api_slots():
    teacher_id = request.args.get('teacher_id', type=int)
    query = TimeSlot.query
    if teacher_id:
        query = query.filter_by(teacher_id=teacher_id)
    
    slots = query.all()
    logged_in_teacher = session.get('teacher_id')
    events = []

    for s in slots:
        is_owner = (logged_in_teacher == s.teacher_id)
        if s.is_booked:
            label = f"Booked ({s.student_name})" if is_owner else f"Taken - {s.teacher.name}"
        else:
            label = f"Open - {s.teacher.name}"

        events.append({
            'id': s.id,
            'title': f"{s.start_time} {label}",
            'start': f"{s.date}T{s.start_time}:00",
            'end': f"{s.date}T{s.end_time}:00",
            'color': '#C97A7E' if s.is_booked else '#A6896F',
            'extendedProps': {
                'teacher_id': s.teacher_id,
                'teacher_name': s.teacher.name,
                'subject': s.teacher.subject,
                'date': s.date,
                'start_time': s.start_time,
                'end_time': s.end_time,
                'is_booked': s.is_booked,
                'is_owner': is_owner,
                'parent_name': s.parent_name if is_owner else '',
                'student_name': s.student_name if is_owner else ''
            }
        })
    return jsonify(events)

if __name__ == "__main__":
    app.run(debug=True)
