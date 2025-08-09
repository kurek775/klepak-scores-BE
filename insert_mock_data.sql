-- USERS
INSERT INTO
    users (email, name, is_admin)
VALUES (
        'admin@example.com',
        'Admin User',
        TRUE
    ),
    (
        'leader1@example.com',
        'Alice Leader',
        FALSE
    ),
    (
        'leader2@example.com',
        'Bob Leader',
        FALSE
    ),
    (
        'leader3@example.com',
        'Charlie Leader',
        FALSE
    ),
    (
        'leader4@example.com',
        'Diana Leader',
        FALSE
    ),
    (
        'leader5@example.com',
        'Ethan Leader',
        FALSE
    ),
    (
        'leader6@example.com',
        'Fiona Leader',
        FALSE
    );

-- CREWS
INSERT INTO crews (number) VALUES (1), (2), (3);

-- CREW LEADERS
INSERT INTO
    crew_leaders (crew_id, user_id)
VALUES (1, 2),
    (1, 3), -- crew 1 leaders
    (2, 4),
    (2, 5), -- crew 2 leaders
    (3, 6),
    (3, 7);
-- crew 3 leaders

-- PERSONS
-- Crew 1
INSERT INTO
    persons (name, crew_id)
VALUES ('John Smith', 1),
    ('Emily Davis', 1),
    ('Michael Brown', 1),
    ('Sarah Wilson', 1),
    ('David Taylor', 1),
    ('Laura Thomas', 1),
    ('James Moore', 1),
    ('Anna Jackson', 1),
    ('Robert White', 1),
    ('Linda Harris', 1);

-- Crew 2
INSERT INTO
    persons (name, crew_id)
VALUES ('Chris Martin', 2),
    ('Sophia Clark', 2),
    ('Daniel Lewis', 2),
    ('Olivia Young', 2),
    ('Matthew Hall', 2),
    ('Grace Allen', 2),
    ('Anthony King', 2),
    ('Ella Scott', 2),
    ('Joshua Green', 2),
    ('Chloe Baker', 2);

-- Crew 3
INSERT INTO
    persons (name, crew_id)
VALUES ('Benjamin Adams', 3),
    ('Victoria Nelson', 3),
    ('Samuel Carter', 3),
    ('Isabella Mitchell', 3),
    ('Alexander Perez', 3),
    ('Mia Roberts', 3),
    ('William Turner', 3),
    ('Ava Phillips', 3),
    ('Joseph Campbell', 3),
    ('Sofia Parker', 3);

-- SPORTS
INSERT INTO
    sports (name, metric)
VALUES ('Running', 'time'),
    ('Swimming', 'time'),
    ('Cycling', 'distance'),
    ('Archery', 'points');

-- TOUR
INSERT INTO
    tours (year, part, theme)
VALUES (
        2025,
        'Summer',
        'Annual Games'
    );

-- TOUR_SPORTS
INSERT INTO
    tour_sports (tour_id, sport_id)
VALUES (1, 1),
    (1, 2),
    (1, 3),
    (1, 4);

-- RESULTS
-- Running times (s)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 1, 1, 12.5),
    (1, 1, 2, 13.2),
    (1, 1, 3, 14.0),
    (1, 1, 4, 15.3),
    (1, 1, 5, 13.8),
    (1, 1, 6, 14.5),
    (1, 1, 7, 12.9),
    (1, 1, 8, 13.7),
    (1, 1, 9, 14.2),
    (1, 1, 10, 15.0),
    (1, 1, 11, 12.7),
    (1, 1, 12, 13.5),
    (1, 1, 13, 14.1),
    (1, 1, 14, 15.2),
    (1, 1, 15, 13.9),
    (1, 1, 16, 14.3),
    (1, 1, 17, 12.8),
    (1, 1, 18, 13.4),
    (1, 1, 19, 14.0),
    (1, 1, 20, 15.1),
    (1, 1, 21, 12.6),
    (1, 1, 22, 13.3),
    (1, 1, 23, 14.2),
    (1, 1, 24, 15.4),
    (1, 1, 25, 13.7),
    (1, 1, 26, 14.6),
    (1, 1, 27, 12.9),
    (1, 1, 28, 13.6),
    (1, 1, 29, 14.3),
    (1, 1, 30, 15.0);

-- Swimming times (s)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 2, 1, 55.2),
    (1, 2, 2, 57.8),
    (1, 2, 3, 60.1),
    (1, 2, 4, 59.5),
    (1, 2, 5, 58.3),
    (1, 2, 6, 61.0),
    (1, 2, 7, 56.7),
    (1, 2, 8, 58.8),
    (1, 2, 9, 59.9),
    (1, 2, 10, 60.5),
    (1, 2, 11, 55.6),
    (1, 2, 12, 57.9),
    (1, 2, 13, 60.2),
    (1, 2, 14, 59.4),
    (1, 2, 15, 58.6),
    (1, 2, 16, 61.1),
    (1, 2, 17, 56.4),
    (1, 2, 18, 58.5),
    (1, 2, 19, 60.0),
    (1, 2, 20, 60.8),
    (1, 2, 21, 55.9),
    (1, 2, 22, 57.7),
    (1, 2, 23, 59.8),
    (1, 2, 24, 59.6),
    (1, 2, 25, 58.2),
    (1, 2, 26, 61.3),
    (1, 2, 27, 56.8),
    (1, 2, 28, 58.4),
    (1, 2, 29, 60.4),
    (1, 2, 30, 60.7);

-- Cycling distances (km)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 3, 1, 25.4),
    (1, 3, 2, 27.1),
    (1, 3, 3, 26.8),
    (1, 3, 4, 24.9),
    (1, 3, 5, 25.7),
    (1, 3, 6, 26.5),
    (1, 3, 7, 27.0),
    (1, 3, 8, 25.6),
    (1, 3, 9, 26.2),
    (1, 3, 10, 24.8),
    (1, 3, 11, 25.9),
    (1, 3, 12, 27.2),
    (1, 3, 13, 26.7),
    (1, 3, 14, 24.7),
    (1, 3, 15, 25.5),
    (1, 3, 16, 26.4),
    (1, 3, 17, 27.3),
    (1, 3, 18, 25.8),
    (1, 3, 19, 26.1),
    (1, 3, 20, 24.6),
    (1, 3, 21, 25.3),
    (1, 3, 22, 27.4),
    (1, 3, 23, 26.6),
    (1, 3, 24, 24.5),
    (1, 3, 25, 25.1),
    (1, 3, 26, 26.3),
    (1, 3, 27, 27.5),
    (1, 3, 28, 25.0),
    (1, 3, 29, 26.0),
    (1, 3, 30, 24.4);

-- Archery points
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 4, 1, 85),
    (1, 4, 2, 90),
    (1, 4, 3, 78),
    (1, 4, 4, 82),
    (1, 4, 5, 88),
    (1, 4, 6, 79),
    (1, 4, 7, 91),
    (1, 4, 8, 87),
    (1, 4, 9, 84),
    (1, 4, 10, 80),
    (1, 4, 11, 86),
    (1, 4, 12, 89),
    (1, 4, 13, 77),
    (1, 4, 14, 83),
    (1, 4, 15, 85),
    (1, 4, 16, 78),
    (1, 4, 17, 92),
    (1, 4, 18, 86),
    (1, 4, 19, 84),
    (1, 4, 20, 81),
    (1, 4, 21, 87),
    (1, 4, 22, 90),
    (1, 4, 23, 79),
    (1, 4, 24, 82),
    (1, 4, 25, 88),
    (1, 4, 26, 80),
    (1, 4, 27, 91),
    (1, 4, 28, 85),
    (1, 4, 29, 83),
    (1, 4, 30, 81);