from flask import Flask

app = Flask(__name__)
# homepage
@app.route("/")
def home():
    return "<h1>Reservation System</h1>"

# booking page
@app.route("/booking")
def booking():
    return """
    <h1>Reservation Booking</h1>

    <p>Parent/Guardian name:</p>
    <input type="text">
    
    <p>Student Name:</p>
    <input type="text">

    <p>Choose a Time:</p>
    <select>
        <option>5:00 pm</option>
        <option>5:15 pm</option>
        <option>5:30 pm</option>
        <option>5:45 pm</option>
        <option>6:00 pm</option>
    </select>

    <br><br>
    <button>Reserve</button>
    """
        
# reservation confirmation page
@app.route("/confirmation")
def confirmation():
    return "<h1>Reservation Confirmed</h1>"

if __name__ == "__main__":
    app.run(debug=True)

