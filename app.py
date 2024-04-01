import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from datetime import datetime
from flask import session
import random
import string
from werkzeug.utils import secure_filename
import os
import json


app = Flask(__name__)
app.secret_key = 'password'
queries = {}

# Establish MySQL connection
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="password",
    database="arthub"
)
cursor = connection.cursor()

# Check if the database tables exist, if not, create them
def create_tables():
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        type ENUM('student', 'teacher') NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INT AUTO_INCREMENT PRIMARY KEY,
        organizer VARCHAR(255) NOT NULL,
        event_name VARCHAR(255) NOT NULL,
        event_type VARCHAR(255) NOT NULL,
        event_date DATE NOT NULL,
        start_time TIME NOT NULL,
        end_time TIME NOT NULL,
        event_description TEXT,
        event_key VARCHAR(10) NOT NULL UNIQUE
    )
""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artworks (
        id INT AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        description TEXT,
        event_id INT,
        user_id INT,
        FOREIGN KEY (event_id) REFERENCES events(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS queries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        query_text TEXT NOT NULL,
        user_role ENUM('student', 'teacher') NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS replies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        query_id INT,
        reply_text TEXT NOT NULL,
        user_role ENUM('student', 'teacher') NOT NULL,
        FOREIGN KEY (query_id) REFERENCES queries(id)
    )
    """)

create_tables()
############
@app.route('/submit_query', methods=['POST'])
def submit_query():
    query = request.form['query']
    query_id = len(queries) + 1
    queries[query_id] = {'query': query, 'replies': []}
    return jsonify({'success': True, 'query_id': query_id})

@app.route('/submit_reply/<int:query_id>', methods=['POST'])
def submit_reply(query_id):
    reply = request.form['reply']
    queries[query_id]['replies'].append(reply)
    return jsonify({'success': True})

@app.route('/get_queries')
def get_queries():
    return jsonify(queries)

@app.route('/student_page')
def query():
    return render_template('student_page.html')

###########
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_artwork', methods=['GET', 'POST'])
def upload_artwork():
    if request.method == 'POST':
        event_name = request.form['event_name']
        username = request.form['username']
        description = request.form['description']
        
        # Retrieve student ID from the database
        cursor.execute("SELECT id FROM students WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row is None:
            flash('Student not found')
            return redirect(request.url)
        
        student_id = row[0]  # Assuming username is unique

        # Retrieve event ID from the database
        cursor.execute("SELECT id FROM events WHERE event_name = %s", (event_name,))
        row = cursor.fetchone()
        if row is None:
            flash('Event not found')
            return redirect(request.url)
        
        event_id = row[0]  # Assuming event_name is unique

        # Check if the 'artwork' file is included in the request
        if 'artwork' not in request.files:
            flash('No file part')
            return redirect(request.url)

        artwork_file = request.files['artwork']

        # Ensure artwork_file is not empty and is an allowed file type
        if artwork_file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(artwork_file.filename):
            flash('Invalid file format')
            return redirect(request.url)

        # Save the uploaded file
        filename = secure_filename(artwork_file.filename)
        artwork_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Insert artwork details into the database
        cursor.execute("INSERT INTO artworks (artwork_filename, description, student_id, event_id) VALUES (%s, %s, %s, %s)", (filename, description, student_id, event_id))
        connection.commit()

        flash('Artwork submitted successfully!')
        return redirect('/success')  # Redirect to a success page

    # If GET request, render the upload artwork page
    event_name = request.args.get('event_name', default='')
    username = request.args.get('username', default='')
    return render_template('upload_artwork.html', event_name=event_name, username=username)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/success')
def success():
    return 'Artwork submitted successfully!'

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username_or_email']
        password = request.form['password']

        # Check if the username or email exists in the database
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s AND password = %s", (username_or_email, username_or_email, password))
        user = cursor.fetchone()

        if user:
            user_type = user[4]  # Assuming the type is stored in the 5th column
            return redirect(url_for(f'{user_type}_page'))
        else:
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
        cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            return render_template('register.html', error='Username or email already taken. Choose another.')

        # Add the new user to the database
        cursor.execute("INSERT INTO users (username, password, email, type) VALUES (%s, %s, %s, %s)", (username, password, email, user_type))
        connection.commit()

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
        start_time = datetime.strptime(start_time_str, "%H:%M").strftime("%H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%H:%M").strftime("%H:%M:%S")

        # Generate a random event key
        event_key = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Add the new event to the database
        cursor.execute("INSERT INTO events (organizer, event_name, event_type, event_date, start_time, end_time, event_description, event_key) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (organizer, event_name, event_type, event_date, start_time, end_time, event_description, event_key))
        connection.commit()

        # Return the event key in the response
        return json.dumps({"This is your event key": event_key}), 200  # Return the event key in JSON format

    return render_template('teacher_page.html')
    
@app.route('/student')
def student_page():
    try:
        # Fetch events from the database
        cursor.execute("SELECT id, event_name, event_type, event_date, start_time, end_time, event_description FROM events")
        events = cursor.fetchall()
            
        return render_template('student_page.html', events=events)
    except Exception as e:
        # Handle any errors
        return "An error occurred while fetching events: {}".format(str(e))

@app.route('/fetch_events')
def fetch_events():
    try:
        # Fetch events from the database
        cursor.execute("SELECT id, event_name, event_type, event_date, start_time, end_time, event_description FROM events")
        events = cursor.fetchall()

        # Convert events to a list of dictionaries
        event_dicts = []
        for event in events:
            event_dict = {
                'id': event[0],
                'event_name': event[1],
                'event_type': event[2],
                'event_date': event[3],
                'start_time': event[4],
                'end_time': event[5],
                'event_description': event[6]
            }
            event_dicts.append(event_dict)

        # Return events as JSON
        return jsonify(event_dicts)
    except Exception as e:
        # Handle any errors
        return jsonify({'error': str(e)})

@app.route('/apply_event/<event_name>')
def apply_event(event_name):
    # Retrieve the username of the logged-in student from the session
    username = session.get('username')
    if not username:
        # Handle the case where the username is not found in the session
        flash('Please log in to apply to events.')
        return redirect(url_for('login'))

    # Fetch the event details including the event key from the database
    cursor.execute("SELECT event_key FROM events WHERE event_name = %s", (event_name,))
    row = cursor.fetchone()
    if row:
        event_key = row[0]
    else:
        flash('Event not found')
        return redirect(url_for('student_page'))

    return render_template('upload_artwork.html', event_name=event_name, event_key=event_key, username=username)


@app.route('/view_applied_students', methods=['GET', 'POST'])
def view_applied_students():
    if request.method == 'POST':
        event_key = request.form['event_key']
        
        # Retrieve event details using the provided key
        cursor.execute("SELECT * FROM events WHERE event_key = %s", (event_key,))
        event = cursor.fetchone()
        
        if event:
            event_id = event['id']
            
            # Retrieve applied students for the event
            cursor.execute("SELECT * FROM student_applications WHERE event_id = %s", (event_id,))
            applied_students = cursor.fetchall()
            
            # Display the list of applied students to the teacher
            return render_template('applied_students.html', applied_students=applied_students)
        else:
            flash('Event key not found')
    
    return render_template('enter_event_key.html')

@app.route('/teacher')
def teacher_page():
    return render_template('teacher_page.html')

if __name__ == '__main__':
    app.run(debug=True)