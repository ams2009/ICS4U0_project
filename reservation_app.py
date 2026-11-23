from flask import Flask

app = Flask(__name__)
booked_times = []

# homepage
@app.route("/")
def home():
    return "<h1>Reservation System</h1>"

# booking page - amelina
@app.route("/booking")
def booking():
    times = ["5:00 pm", "5:15 pm", "5:30 pm", "5:45 pm", "6:00 pm"]

    time_options = ""

    for time in times :
        if time not in booked_times:
            time_options += "<option>" + time + "</option>"
    
    return """
    <h1>Reservation Booking</h1>

    <p>Please enter your information and choose an available meeting time.</p>

    <form action="/confirmation">
    <p>Parent/Guardian name:</p>
    <input type="text"
    name="parent_name" required> 
    
    <p>Student Name:</p>
    <input type="text"
    name="student_name" required>

    <p>Choose a Time:</p>
    <select name="time" required>
        <option value= "" disabled
        selected>Select a time</option>
        """ + time_options + """ 
    </select>

    <br><br>
    <button type="submit">Reserve</button>
    </form>
    """
        
# reservation confirmation page
@app.route("/confirmation")
def confirmation():
    return "<h1>Reservation Confirmed</h1>"

if __name__ == "__main__":
    app.run(debug=True)

