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

    for time in times:
        if time not in booked_times:
            time_options += "<option>" + time + "</option>"

    return """
    <html>
    <head>
        <title>Reservation Booking</title>

        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #27355c;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
            }

            .booking-box {
                background-color: white;
                padding: 35px;
                border-radius: 14px;
                width: 380px;
                text-align: center;
                box-shadow: 0 4px 18px rgba(0, 0, 0, 0.12);
            }

            h1 {
                margin-bottom: 10px;
            }

            .description {
                margin-bottom: 25px;
            }

            label {
                display: block;
                text-align: left;
                margin-bottom: 6px;
                font-weight: bold;
            }

            input, select {
                width: 100%;
                padding: 11px;
                margin-bottom: 18px;
                border: 1px solid #ccc;
                border-radius: 7px;
                box-sizing: border-box;
                font-size: 14px;
            }

            button {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 7px;
                font-size: 16px;
                cursor: pointer;
            }

            .note {
                font-size: 13px;
                margin-top: 15px;
            }
        </style>
    </head>

    <body>

        <div class="booking-box">

            <h1>Reservation Booking</h1>

            <p class="description">
                Enter your information and choose an available meeting time.
            </p>

            <form action="/confirmation">

                <label>Parent/Guardian Name</label>
                <input type="text" name="parent_name" required>

                <label>Student Name</label>
                <input type="text" name="student_name" required>

                <label>Choose a Time</label>

                <select name="time" required>
                    <option value="" disabled selected>Select a time</option>
                    """ + time_options + """
                </select>

                <button type="submit">Reserve Appointment</button>

            </form>

            <p class="note">
                Only available meeting times are shown.
            </p>

        </div>

    </body>
    </html>
    """
        
# reservation confirmation page
@app.route("/confirmation")
def confirmation():
    return "<h1>Reservation Confirmed</h1>"

if __name__ == "__main__":
    app.run(debug=True)

