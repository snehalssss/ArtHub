from flask import Flask, request, jsonify,render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ghibli'
app.config['MYSQL_DB'] = 'art_shows'
mysql = MySQL(app)

# API endpoints

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_show', methods=['POST'])
def create_show():
    # Establish MySQL connection within the request handler function
    cur = mysql.connection.cursor()
    
    data = request.json
    title = data['title']
    date = data['date']
    venue = data['venue']
    tickets_available = data['tickets_available']

    cur.execute("INSERT INTO art_show (title, date, venue, tickets_available) VALUES (%s, %s, %s, %s)",
                (title, date, venue, tickets_available))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Art show created successfully'}), 201

@app.route('/book_tickets', methods=['POST'])
def book_tickets():
    # Establish MySQL connection within the request handler function
    cur = mysql.connection.cursor()
    
    data = request.json
    show_id = data['show_id']
    user_name = data['user_name']
    tickets_booked = data['tickets_booked']

    cur.execute("SELECT tickets_available FROM art_show WHERE id = %s", (show_id,))
    show = cur.fetchone()
    if show and show[0] >= tickets_booked:
        cur.execute("UPDATE art_show SET tickets_available = tickets_available - %s WHERE id = %s",
                    (tickets_booked, show_id))
        cur.execute("INSERT INTO booking (show_id, user_name, tickets_booked) VALUES (%s, %s, %s)",
                    (show_id, user_name, tickets_booked))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message': 'Tickets booked successfully'}), 201
    else:
        cur.close()
        return jsonify({'error': 'Not enough tickets available'}), 400

@app.route('/shows', methods=['GET'])
def get_shows():
    # Establish MySQL connection within the request handler function
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM art_show")
    shows = cur.fetchall()
    cur.close()
    return jsonify({'shows': shows})

@app.route('/bookings', methods=['GET'])
def get_bookings():
    # Establish MySQL connection within the request handler function
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT * FROM booking")
    bookings = cur.fetchall()
    cur.close()
    return jsonify({'bookings': bookings})

if __name__ == '__main__':
    app.run(debug=True)
