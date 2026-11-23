from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class TimeSlot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    parent_name = db.Column(db.String(100), nullable=True)
    student_name = db.Column(db.String(100), nullable=True)