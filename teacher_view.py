from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, TimeSlot

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")

@teacher_bp.route("/login", methods=["POST"])
def login():
    if request.form.get("password") == "teacher123":
        session["is_teacher"] = True
        return redirect(url_for("teacher.dashboard"))
    flash("Wrong password.")
    return redirect(url_for("parent.home"))

@teacher_bp.route("/logout")
def logout():
    session.pop("is_teacher", None)
    return redirect(url_for("parent.home"))

@teacher_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if not session.get("is_teacher"):
        return redirect(url_for("parent.home"))

    if request.method == "POST":
        new_slot = TimeSlot(
            date=request.form.get("date"),
            time=request.form.get("time"),
            is_available=True
        )
        db.session.add(new_slot)
        db.session.commit()
        return redirect(url_for("teacher.dashboard"))

    slots = TimeSlot.query.order_by(TimeSlot.date, TimeSlot.time).all()
    return render_template("teacher_dashboard.html", slots=slots)

@teacher_bp.route("/edit/<int:slot_id>", methods=["POST"])
def edit_slot(slot_id):
    if not session.get("is_teacher"):
        return redirect(url_for("parent.home"))
    slot = TimeSlot.query.get_or_404(slot_id)
    slot.time = request.form.get("time")
    db.session.commit()
    return redirect(url_for("teacher.dashboard"))

@teacher_bp.route("/delete/<int:slot_id>", methods=["POST"])
def delete_slot(slot_id):
    if not session.get("is_teacher"):
        return redirect(url_for("parent.home"))
    slot = TimeSlot.query.get_or_404(slot_id)
    db.session.delete(slot)
    db.session.commit()
    return redirect(url_for("teacher.dashboard"))

