import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, make_response,abort
from datetime import datetime
from flask import session
import random
import string
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import json
import pdfkit

app = Flask(__name__)
app.secret_key = 'password'
queries = {}
events = {}

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
    CREATE TABLE IF NOT EXISTS shows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    location VARCHAR(500) NOT NULL,
    event_date DATE NOT NULL,
    available_seats INT NOT NULL,
    pamphlet VARCHAR(255)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    seat_count INT NOT NULL,
    FOREIGN KEY (show_id) REFERENCES shows(id)
    )
    """)

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
    event_key VARCHAR(255) NOT NULL,
    user_id INT,
    username VARCHAR(255) NOT NULL,
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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS winners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    event_key VARCHAR(255) NOT NULL,
    rank_value INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
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
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#####
@app.route('/generate_pdf', methods=['GET'])
def generate_pdf():
    try:
        # Write queries to fetch data from the database
        query = """
            SELECT b.show_id, b.customer_name, s.id, s.title, s.start_time, s.location, s.event_date
            FROM art_shows.bookings AS b
            JOIN art_shows.shows AS s ON b.show_id = s.id
            ORDER BY b.id DESC
            LIMIT 1
        """
        
        # Execute the query
        cursor = connection.cursor()
        cursor.execute(query)
        
        # Fetch the result of the query
        data = cursor.fetchone()

        # Close the cursor
        cursor.close()

        # Pass the data to the frontend and render the template
        return render_template('generate_pdf.html', show_id=data[0], customer_name=data[1], id=data[2], title=data[3], start_time=data[4], location=data[5], event_date=data[6])
    except Exception as e:
        # Handle exceptions, such as database errors
        return str(e)
#######


@app.route('/upload_artwork', methods=['GET', 'POST'])
def upload_artwork():
    if request.method == 'POST':
        event_name = request.form['event_name']
        username = request.form['username']
        description = request.form['description']
        event_key = request.form['event_key']

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

        # Save the uploaded file in a folder named by the event_name
        folder_path = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
        try:
            os.makedirs(folder_path, exist_ok=True)  # Create the folder if it doesn't exist
        except Exception as e:
            flash(f'Error creating folder: {str(e)}')
            return redirect(request.url)

        filename = secure_filename(artwork_file.filename)
        file_path = os.path.join(folder_path, filename)
        artwork_file.save(file_path)


        # Fetch user_id from the students table based on the username
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row is None:
            flash('Student not found')
            return redirect(request.url)
        
        user_id = row[0]
        
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


        # Insert artwork details into the database
        cursor.execute("INSERT INTO artworks (filename, description, event_id, event_key, user_id, username) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (filename, description, event_id, event_key, user_id, username))
        connection.commit()

        flash('Artwork submitted successfully!')
        
        return redirect('/success')  # Redirect to a success page

    # If GET request, render the upload artwork page
    event_name = request.args.get('event_name', default='')
    username = request.args.get('username', default='')
    return render_template('upload_artwork.html', event_name=event_name, username=username)



@app.route('/view_students', methods=['POST','GET'])
def view_students():
    event_key = request.form.get('event_key')

    # Fetch the event details from the database
    cursor.execute("SELECT event_name FROM events WHERE event_key = %s", (event_key,))
    event = cursor.fetchone()

    if event:
        
        event_name = event[0]

        # Fetch the students' artworks for the specified event
        cursor.execute("SELECT * FROM artworks WHERE event_key = %s", (event_key,))
        student_rows = cursor.fetchall()

        students = []
        for student_row in student_rows:
            student = {
                'filename': student_row[1],
                'description': student_row[2],
                'user_id': student_row[5],
                'username': student_row[6]
            }
            students.append(student)

        return render_template('view_students.html', event_name=event_name, students=students)
    else:
        # Handle case where event_key is not found
        return render_template('view_students.html', error="Event not found for the given event key.")


@app.route('/view_artwork/<event_name>/<filename>')
def view_artwork(event_name, filename):
    # Construct the path to the artwork file
    artwork_path = os.path.join(app.config['UPLOAD_FOLDER'], event_name, filename)
    
    # Check if the file exists
    if os.path.exists(artwork_path):
        # Serve the file from the event subfolder
        return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], event_name, filename))
    else:
        # If the file does not exist, return a 404 error
        abort(404)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/success')
def success():
    return 'Artwork submitted successfully!'

@app.route('/fetch_event_key')
def fetch_event_key():
    event_name = request.args.get('eventName')
    cursor.execute("SELECT event_key FROM events WHERE event_name = %s", (event_name,))
    row = cursor.fetchone()
    if row:
        event_key = row[0]
        return jsonify({'eventKey': event_key})
    else:
        return jsonify({'eventKey': None})


@app.route('/')
def index():
    return render_template('home_page.html')

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

            session['username_or_email'] = username_or_email
            session['user_type'] = user_type
            return redirect(url_for(f'{user_type}_page'))
        else:
            return render_template('login.html', error='Invalid credentials. Please try again.')

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove user credentials from session
    username_or_email = session.pop('username_or_email', None)
    user_type = session.pop('user_type', None)

    # Delete user record from the database
    if username_or_email:
        cursor.execute("DELETE FROM artworks WHERE user_id IN (SELECT id FROM users WHERE username = %s OR email = %s)", (username_or_email, username_or_email))
        cursor.execute("DELETE FROM winners WHERE user_id IN (SELECT id FROM users WHERE username = %s OR email = %s)", (username_or_email, username_or_email))
        cursor.execute("DELETE FROM users WHERE username = %s OR email = %s", (username_or_email, username_or_email))
        
        connection.commit()

    # Redirect to the login page after logout
    return redirect(url_for('login'))

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

@app.route('/delete_event', methods=['POST'])
def delete_event():
    if request.method == 'POST':
        event_key = request.form.get('event_key')
        if event_key:
            try:
                # Fetch event_id using event_key
                cursor.execute("SELECT id FROM events WHERE event_key = %s", (event_key,))
                event_id = cursor.fetchone()[0]

                # Delete associated records from artworks table using event_id
                cursor.execute("DELETE FROM artworks WHERE event_id = %s", (event_id,))
                
                # Then delete the event itself
                cursor.execute("DELETE FROM events WHERE event_key = %s", (event_key,))

                cursor.execute("DELETE FROM winners WHERE event_key = %s", (event_key,))
                connection.commit()

                return "Event deleted successfully."
            except mysql.connector.Error as err:
                # Handle the error appropriately
                return f"An error occurred: {err}"
        else:
            return "Please provide an event key."
    else:
        return "Invalid request method."

######################
@app.route('/add_show', methods=['GET', 'POST'])
def add_show():
    if request.method == 'POST':
        title = request.form['title']
        start_time = request.form['start_time']
        location = request.form['location']
        event_date = request.form['event_date']
        available_seats = request.form['available_seats']
        
        # Check if the pamphlet file is present in the request
        if 'pamphlet' in request.files:
            pamphlet_file = request.files['pamphlet']
            
            # If the file is allowed and not empty, save it to the uploads folder
            if pamphlet_file and allowed_file(pamphlet_file.filename):
                filename = secure_filename(pamphlet_file.filename)
                pamphlet_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pamphlet_file.save(pamphlet_path)
            else:
                # Handle invalid file format or empty file
                return "Invalid file format or file not provided."
        else:
            # Handle case where pamphlet file is not present in the request
            return "Pamphlet file not provided."

        # Add the new event to the database
        cursor.execute("INSERT INTO shows (title, start_time, location, event_date, available_seats, pamphlet) VALUES (%s, %s, %s, %s, %s, %s)", 
                       (title, start_time, location, event_date, available_seats, filename))
        connection.commit()
        event_confirmed = True
        
        return render_template('add_show.html', event_confirmed=event_confirmed)

    return render_template('add_show.html', event_confirmed=False)

@app.route('/event_confirmed')
def event_confirmed():
    return "Event added successfully! Thank you for your interest."

@app.route('/show_details', methods=['GET', 'POST'])
@app.route('/show_details/<int:show_id>', methods=['GET', 'POST'])
def show_details(show_id=None):
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        seat_count = request.form['seat_count']

        # Assuming you have a table named 'bookings' with appropriate columns
        cursor.execute("INSERT INTO bookings (show_id, customer_name, seat_count) VALUES (%s, %s, %s)", (show_id, customer_name, seat_count))
        connection.commit()

        return render_template('show_details.html')  # Render booking confirmation page after successful booking

    else:
        if show_id is not None:
            # Fetching show details using join operation
            cursor.execute("SELECT art_shows.shows.*, bookings.customer_name, bookings.seat_count FROM art_shows.shows INNER JOIN bookings ON art_shows.shows.id = bookings.show_id WHERE art_shows.shows.id = %s", (show_id,))
            show_details = cursor.fetchone()

            if show_details:
                return render_template('show_details.html', show_details=show_details)
            else:
                return "Show not found"
        else:
            return "No show ID provided"



     
@app.route('/book/<int:show_id>', methods=['GET', 'POST'])
def book_show(show_id):
    if request.method == 'POST':
        customer_name = request.form['customer_name']
        seat_count = int(request.form['seat_count'])
        
        # Insert booking details into the database
        cursor.execute("INSERT INTO bookings (show_id, customer_name, seat_count) VALUES (%s, %s, %s)", (show_id, customer_name, seat_count))
        connection.commit()
        
        # Update available seats in the shows table
        cursor.execute("UPDATE shows SET available_seats = available_seats - %s WHERE id = %s", (seat_count, show_id))
        connection.commit()
        
        # Fetch show details for the given show_id
        cursor.execute("SELECT title, start_time, location, event_date FROM shows WHERE id = %s", (show_id,))
        show_details = cursor.fetchone()
        
        if show_details:
            show_title, start_time, location, event_date = show_details
        else:
            # Handle case where show_id doesn't exist
            return "Show not found"
        
        # Render the booking confirmation message on the same page
        return render_template('booking_page.html', show_id=show_id, show_title=show_title, start_time=start_time, location=location, event_date=event_date, booking_success=True)
    
    # Fetch show details for the given show_id
    cursor.execute("SELECT title, start_time, location, event_date, available_seats FROM shows WHERE id = %s", (show_id,))
    show_details = cursor.fetchone()
    
    if show_details:
        show_title, start_time, location, event_date, available_seats = show_details
    else:
        # Handle case where show_id doesn't exist
        return "Show not found"
    
    return render_template('booking_page.html', show_id=show_id, show_title=show_title, start_time=start_time, location=location, event_date=event_date, available_seats=available_seats)


@app.route('/booking_success')
def booking_success():
    return "Booking successful! Thank you for booking."
##############
    
@app.route('/student', methods = ['GET'])
def student_page():
    username_or_email = session.get('username_or_email')
    user_type = session.get('user_type')
    try:
        # Fetch events from the database
        cursor.execute("SELECT id, event_name, event_type, event_date, start_time, end_time, event_description FROM events")
        events = cursor.fetchall()
            
        return render_template('student_page.html', events=events,username_or_email=username_or_email, user_type=user_type)
    except Exception as e:
        # Handle any errors
        return "An error occurred while fetching events: {}".format(str(e))



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




@app.route('/teacher')
def teacher_page():
    username_or_email = session.get('username_or_email')
    user_type = session.get('user_type')
    try:
        # Fetch events from the database
        cursor.execute("SELECT id, event_name, event_type, event_date, start_time, end_time, event_description FROM events")
        events = cursor.fetchall()
            
        return render_template('teacher_page.html', events=events,username_or_email=username_or_email, user_type=user_type)
    except Exception as e:
        # Handle any errors
        return "An error occurred while fetching events: {}".format(str(e))

    

@app.route('/submit_winners', methods=['POST'])
def submit_winners():
    if request.method == 'POST':
        event_key = request.form.get('event_key')
        event_name = request.form.get('event_name')
        if event_key and event_name:
            # Get the selected winners and their ranks from the form data
            winners = []
            for i in range(1, 4):  # Assuming there are 3 winners to be ranked
                user_id = request.form.get(f'winner_id_{i}')
                rank_value = request.form.get(f'winner_rank_{i}')
                user_name = request.form.get(f'winner_username_{i}')
                if user_id and user_name and rank_value:
                    winners.append((user_id, user_name, rank_value))

            if winners:
                try:
                    # Assuming you have a database connection named `connection`
                    cursor = connection.cursor()
                    for winner in winners:
                        user_id, user_name, rank_value = winner
                        cursor.execute("INSERT INTO winners (user_id, user_name, rank_value, event_name, event_key) VALUES (%s, %s, %s, %s, %s)", (user_id, user_name, rank_value, event_name, event_key))
                    connection.commit()
                    cursor.close()
                    return "Winners' rankings updated successfully."
                except Exception as e:
                    # Handle database errors
                    return f"An error occurred: {str(e)}"
            else:
                return "No winners selected."
        else:
            return "Please provide an event key."
    else:
        return "Invalid request method."

   
    
@app.route('/show_winners', methods=['GET', 'POST'])
def show_winners(): 
    if request.method == 'POST':
        event_key = request.form.get('event_key')
        if event_key:
            cursor.execute("SELECT user_name, rank_value FROM winners WHERE event_key = %s", (event_key,))
            winners_data = cursor.fetchall()
            winners = [{'user_name': row[0], 'rank_value': row[1]} for row in winners_data]
            return render_template('show_winners.html', event_key=event_key, winners=winners)
        else:
            # Handle case where event key is not provided
            return "Please provide an event key."
    else:
        # Handle case where method is not POST
        return render_template('show_winners.html')  # Display the form for entering event key

@app.route('/show')
def show():
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM shows")  # Assuming 'shows' is your table name
    shows = cursor.fetchall()
    return render_template('show.html', shows=shows)

if __name__ == '__main__':
    app.run(debug=True)
