from flask import Blueprint, render_template, request, redirect, url_for

reservation_bp = Blueprint('reservation', __name__)

# Note: Import db, Teacher, and TimeSlot from your models or app
from models import db, Teacher, TimeSlot

@reservation_bp.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        slot = TimeSlot.query.get_or_404(slot_id)
        if not slot.is_booked:
            slot.is_booked = True
            slot.parent_name = request.form.get('parent_name')
            slot.student_name = request.form.get('student_name')
            db.session.commit()
            return redirect(url_for('reservation.confirmation', slot_id=slot.id))

    teacher_filter = request.args.get('teacher_id', type=int)
    teachers = Teacher.query.all()
    query = TimeSlot.query
    if teacher_filter:
        query = query.filter_by(teacher_id=teacher_filter)
    slots = query.order_by(TimeSlot.date, TimeSlot.start_time).all()
    return render_template('reserve.html', slots=slots, teachers=teachers, selected_teacher=teacher_filter)

@reservation_bp.route('/confirmation/<int:slot_id>')
def confirmation(slot_id):
    slot = TimeSlot.query.get_or_404(slot_id)
    return render_template('confirmation.html', slot=slot)

