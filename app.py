from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from flask import flash
from flask import send_from_directory
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)

# File path for the CSV file
CSV_FILE_PATH = 'users.csv'
EVENTS_CSV_FILE_PATH = 'events.csv'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_artwork', methods=['GET', 'POST'])
def upload_artwork():
    if request.method == 'POST':
        event_name = request.form['event_name']
        username = request.form['username']
        return render_template('upload_artwork.html', event_name=event_name, username=username)

    return redirect(url_for('student_page'))

@app.route('/submit_artwork', methods=['POST'])
def submit_artwork():
    # Check if the 'artwork' file is included in the request
    if 'artwork' not in request.files:
        flash('No file part')
        return redirect(request.url)

    artwork_file = request.files['artwork']
    description = request.form['description']
    event_name = request.form['event_name']
    username = request.form['username']

    # Check if the artwork_file is not empty and is an allowed file type
    if artwork_file and allowed_file(artwork_file.filename):
        filename = secure_filename(artwork_file.filename)
        artwork_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Check if the database file for the current event exists
        artwork_csv_path = f'{event_name}_artworks.csv'
        if not os.path.exists(artwork_csv_path):
            # If not, create the database file and write the header
            with open(artwork_csv_path, 'w', newline='') as csvfile:
                fieldnames = ['artwork', 'description', 'event_name', 'username']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

        # Append artwork details to the CSV file specific to the event
        with open(artwork_csv_path, 'a', newline='') as csvfile:
            fieldnames = ['artwork', 'description', 'event_name', 'username']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'artwork': filename, 'description': description, 'event_name': event_name, 'username': username})

        return 'Artwork submitted successfully!'

    return 'Invalid file format'



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if not os.path.exists(EVENTS_CSV_FILE_PATH):
    with open(EVENTS_CSV_FILE_PATH, 'w', newline='') as csvfile:
        fieldnames = ['organizer', 'event_name', 'event_type', 'event_date', 'event_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()


# Check if the CSV file exists, create it if not
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
        fieldnames = ['username', 'password', 'email', 'type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        # Check if the username or email exists in the CSV file
        with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for user in reader:
                if (user['username'] == username_or_email or user['email'] == username_or_email) and user['password'] == password:
                    user_type = user['type']
                    return redirect(url_for(f'{user_type}_page'))

        return render_template('login.html', error='Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']

        # Check if the username or email is already taken
        with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            if any(u['username'] == username or u['email'] == email for u in reader):
                return render_template('register.html', error='Username or email already taken. Choose another.')

        # Add the new user to the CSV file
        with open(CSV_FILE_PATH, 'a', newline='') as csvfile:
            fieldnames = ['username', 'password', 'email', 'type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({'username': username, 'password': password, 'email': email, 'type': user_type})

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/add_event', methods=['POST'])
def add_event():
    if request.method == 'POST':
        organizer = request.form['organizer']
        event_name = request.form['event_name']
        event_type = request.form['event_type']
        event_date = request.form['event_date']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        event_description = request.form['event_description']

        # Parse the timing data to datetime objects
        start_time = datetime.strptime(start_time_str, "%H:%M")
        end_time = datetime.strptime(end_time_str, "%H:%M")

        # Format the timing data for display and writing to the CSV file
        formatted_start_time = start_time.strftime("%I:%M %p")
        formatted_end_time = end_time.strftime("%I:%M %p")

        # Add the new event to the CSV file
        with open(EVENTS_CSV_FILE_PATH, 'a', newline='') as csvfile:
            fieldnames = ['organizer', 'event_name', 'event_type', 'event_date', 'start_time', 'end_time', 'event_description']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow({
                'organizer': organizer,
                'event_name': event_name,
                'event_type': event_type,
                'event_date': event_date,
                'start_time': formatted_start_time,
                'end_time': formatted_end_time,
                'event_description': event_description
            })

        return redirect(url_for('teacher_page'))

    return render_template('teacher_page.html')
    
@app.route('/student')
def student_page():
    # Read events from the CSV file
    events = []
    with open(EVENTS_CSV_FILE_PATH, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        events = list(reader)

    return render_template('student_page.html', events=events)

@app.route('/apply_event/<event_name>/<username>')
def apply_event(event_name, username):
    return render_template('upload_artwork.html', event_name=event_name, username=username)


@app.route('/teacher')
def teacher_page():
    return render_template('teacher_page.html')

if __name__ == '__main__':
    app.run(debug=True)
