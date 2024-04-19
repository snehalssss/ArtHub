create database arthub;
use arthub;

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    type ENUM('student', 'teacher') NOT NULL
);

CREATE TABLE events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    organizer VARCHAR(255) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    event_description TEXT
);

CREATE TABLE artworks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    description TEXT,
    event_id INT,
    event_key VARCHAR(255) NOT NULL,
    user_id INT,
    username VARCHAR(255) NOT NULL,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE winners (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    event_name VARCHAR(255) NOT NULL,
    event_key VARCHAR(255) NOT NULL,
    rank_value INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS shows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    location VARCHAR(500) NOT NULL,
    event_date DATE NOT NULL,
    available_seats INT NOT NULL
    pamphlet VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    show_id INT NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    seat_count INT NOT NULL,
    FOREIGN KEY (show_id) REFERENCES shows(id)
);