DROP DATABASE theatre_db;
CREATE DATABASE theatre_db;
USE theatre_db;
CREATE TABLE users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)        NOT NULL,
    email       VARCHAR(100)        NOT NULL UNIQUE,
    customer_id VARCHAR(20)         NOT NULL UNIQUE
);

-- ─────────────────────────────────────────────
--  MOVIES
-- ─────────────────────────────────────────────
CREATE TABLE movies (
    movie_id    INT AUTO_INCREMENT PRIMARY KEY,
    movie_name  VARCHAR(100)        NOT NULL,
    genre       VARCHAR(50)
);

-- ─────────────────────────────────────────────
--  SHOWS
-- ─────────────────────────────────────────────
CREATE TABLE shows (
    show_id     INT AUTO_INCREMENT PRIMARY KEY,
    movie_id    INT                 NOT NULL,
    show_time   VARCHAR(50)         NOT NULL,
    FOREIGN KEY (movie_id) REFERENCES movies(movie_id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
--  TICKETS  (ticket_id is now our TKT-XXXX string, booked_at added)
-- ─────────────────────────────────────────────
CREATE TABLE tickets (
    ticket_id      VARCHAR(20)  PRIMARY KEY,
    user_id        INT          NOT NULL,
    show_id        INT          NOT NULL,
    seat_no        VARCHAR(10)  NOT NULL,
    payment_status VARCHAR(20)  NOT NULL DEFAULT 'Paid',
    booked_at      DATETIME     NOT NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (show_id) REFERENCES shows(show_id) ON DELETE CASCADE,
    
    UNIQUE (show_id, seat_no)
);
-- ─────────────────────────────────────────────
--  SAMPLE DATA
-- ─────────────────────────────────────────────
INSERT INTO movies (movie_name, genre) VALUES
('Avengers', 'Action'),
('Titanic',  'Romance'),
('Dhurandhar', 'Action'),
('WALL-E', 'SCI-FI');

INSERT INTO shows (movie_id, show_time) VALUES
(1, '10:00 AM'),
(1, '6:00 PM'),
(2, '3:00 PM'),
(2, '7:00 PM'),
(3, '8:00 AM'),
(3, '1:30 PM'),
(4, '2:00 PM');


-- ─────────────────────────────────────────────
--  VERIFY
-- ─────────────────────────────────────────────
SELECT * FROM movies;
SELECT * FROM shows;
CREATE TABLE tickets (ticket_id      VARCHAR(20)  PRIMARY KEY, user_id  INT   NOT NULL, show_id  INT  NOT NULL,seat_no VARCHAR(10)  NOT NULL, payment_status VARCHAR(20)  NOT NULL DEFAULT 'Paid', booked_at DATETIME NOT NULL,FOREIGN KEY (user_id)  REFERENCES users(show_id)  ON DELETE CASCADE, FOREIGN KEY (show_id)  REFERENCES shows(show_id)  ON DELETE CASCADE, UNIQUE (show_id, seat_no) );
COMMIT;

