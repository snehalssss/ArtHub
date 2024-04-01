CREATE DATABASE arthub;
USE arthub;
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    type ENUM('student', 'teacher') NOT NULL
);

CREATE TABLE IF NOT EXISTS queries (
        id INT AUTO_INCREMENT PRIMARY KEY,
        query_text TEXT NOT NULL,
        user_role ENUM('student', 'teacher') NOT NULL
);

CREATE TABLE IF NOT EXISTS replies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        query_id INT,
        reply_text TEXT NOT NULL,
        user_role ENUM('student', 'teacher') NOT NULL,
        FOREIGN KEY (query_id) REFERENCES queries(id)
);

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
);

CREATE TABLE artworks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    description TEXT,
    event_id INT,event_name
    user_id INT,
    FOREIGN KEY (event_id) REFERENCES events(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
