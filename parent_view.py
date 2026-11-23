from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, TimeSlot

parent_bp = Blueprint("parent", __name__)

@parent_bp.route("/")
def home():
    return render_template("home.html")

@parent_bp.route("/reserve", methods=["GET", "POST"])
def reserve():
    if request.method == "POST":
        slot_id = request.form.get("slot_id")
        slot = TimeSlot.query.get_or_404(slot_id)
        
        if slot.is_available:
            slot.is_available = False
            slot.parent_name = request.form.get("parent_name")
            slot.student_name = request.form.get("student_name")
            db.session.commit()
            return redirect(url_for("parent.confirm", slot_id=slot.id))
        else:
            flash("Slot already booked")

    slots = TimeSlot.query.order_by(TimeSlot.date, TimeSlot.time).all()
    return render_template("reserve.html", slots=slots)

@parent_bp.route("/confirm/<int:slot_id>")
def confirm(slot_id):
    slot = TimeSlot.query.get_or_404(slot_id)
    return render_template("confirm.html", slot=slot)
