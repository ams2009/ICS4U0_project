from flask import Flask

app = Flask(__name__)
# homepage
@app.route("/")
def home():
    return "<h1>Reservation System</h1>"

if __name__ == "__main__":
    app.run(debug=True)
# booking page
@app.route("/booking")
def booking():
    return "<h1>Reservation Booking</h1>"
# reservation confirmation page
@app.route("/confirmation")
def confirmation():
    return "<h1>Reservation Confirmed</h1>"



