BEGIN;

-- Clean slate
TRUNCATE TABLE results,
tour_sports,
tours,
templates,
sports,
persons,
crew_leaders,
crews,
users RESTART IDENTITY CASCADE;

------------------------------------------------------------
-- Templates
------------------------------------------------------------
INSERT INTO
    templates (
        id,
        "bgImage",
        font,
        "textPosition"
    )
VALUES (1, NULL, NULL, 'bottom-left'),
    (2, NULL, NULL, 'center');

------------------------------------------------------------
-- Tours
------------------------------------------------------------
INSERT INTO
    tours (
        id,
        year,
        part,
        theme,
        template_id
    )
VALUES (
        1,
        2025,
        'summer',
        'Beach Bash',
        1
    ),
    (
        2,
        2024,
        'spring',
        'Forest Run',
        2
    );

------------------------------------------------------------
-- Users
-- Note: OIDC sub is string (VARCHAR). Emails are UNIQUE.
------------------------------------------------------------
INSERT INTO
    users (
        id,
        sub,
        email,
        name,
        picture_url,
        is_admin,
        created_at,
        last_login_at
    )
VALUES (
        1,
        '110000000000000001',
        'admin1@example.com',
        'Alice Admin',
        NULL,
        TRUE,
        NOW() - INTERVAL '20 days',
        NOW() - INTERVAL '1 day'
    ),
    (
        2,
        '110000000000000002',
        'leader1@example.com',
        'Bob Leader',
        NULL,
        FALSE,
        NOW() - INTERVAL '18 days',
        NOW() - INTERVAL '2 days'
    ),
    (
        3,
        '110000000000000003',
        'leader2@example.com',
        'Carol Leader',
        NULL,
        FALSE,
        NOW() - INTERVAL '17 days',
        NOW() - INTERVAL '2 days'
    ),
    (
        4,
        '110000000000000004',
        'leader3@example.com',
        'Dave Leader',
        NULL,
        FALSE,
        NOW() - INTERVAL '16 days',
        NOW() - INTERVAL '3 days'
    ),
    (
        5,
        '110000000000000005',
        'leader4@example.com',
        'Eve Leader',
        NULL,
        FALSE,
        NOW() - INTERVAL '15 days',
        NOW() - INTERVAL '3 days'
    ),
    (
        6,
        '110000000000000006',
        'user1@example.com',
        'Frank User',
        NULL,
        FALSE,
        NOW() - INTERVAL '12 days',
        NULL
    ),
    (
        7,
        '110000000000000007',
        'user2@example.com',
        'Grace User',
        NULL,
        FALSE,
        NOW() - INTERVAL '11 days',
        NULL
    ),
    (
        8,
        '110000000000000008',
        'user3@example.com',
        'Heidi User',
        NULL,
        FALSE,
        NOW() - INTERVAL '10 days',
        NULL
    );

------------------------------------------------------------
-- Crews (link crews to tours via tour_id)
------------------------------------------------------------
INSERT INTO
    crews (id, number, tour_id)
VALUES (1, 1, 1), -- Tour 1 (2025 summer)
    (2, 2, 1), -- Tour 1
    (3, 3, 1), -- Tour 1
    (4, 1, 2);
-- Tour 2 (2024 spring)

------------------------------------------------------------
-- Crew leaders (many-to-many)
------------------------------------------------------------
INSERT INTO
    crew_leaders (crew_id, user_id)
VALUES (1, 2), -- Bob leads Crew 1 (Tour 1)
    (1, 3), -- Carol also leads Crew 1 (co-lead)
    (2, 4), -- Dave leads Crew 2 (Tour 1)
    (3, 5), -- Eve leads Crew 3 (Tour 1)
    (4, 3);
-- Carol also leads Crew 4 (Tour 2)

------------------------------------------------------------
-- Persons (non-logged users) assigned to crews
------------------------------------------------------------
INSERT INTO
    persons (id, name, crew_id)
VALUES (1, 'Paul', 1),
    (2, 'Nina', 1),
    (3, 'Oscar', 1),
    (4, 'Quinn', 1),
    (5, 'Rita', 2),
    (6, 'Sam', 2),
    (7, 'Tara', 2),
    (8, 'Uma', 3),
    (9, 'Victor', 3),
    (10, 'Wendy', 4),
    (11, 'Xavier', 4);

------------------------------------------------------------
-- Sports
------------------------------------------------------------
INSERT INTO
    sports (id, name, metric)
VALUES (1, 'Sprint 100m', 'time'),
    (2, 'Long Jump', 'distance'),
    (3, 'Push-ups', 'reps'),
    (4, 'Swim 50m', 'time');

-- Ensure unique on name as per schema (already present)
-- ALTER TABLE sports ADD CONSTRAINT uq_sports_name UNIQUE (name);

------------------------------------------------------------
-- Tour ↔ Sports mapping
-- Tour 1 has Sprint, Long Jump, Push-ups
-- Tour 2 has Sprint, Swim
------------------------------------------------------------
INSERT INTO
    tour_sports (
        tour_id,
        sport_id,
        position,
        is_optional
    )
VALUES (1, 1, 1, FALSE),
    (1, 2, 2, FALSE),
    (1, 3, 3, TRUE),
    (2, 1, 1, FALSE),
    (2, 4, 2, FALSE);

------------------------------------------------------------
-- Results
-- Must reference existing (tour_id, sport_id) pairs in tour_sports and persons.
-- Tour 1: persons 1..9 belong to crews 1..3 (tour 1)
------------------------------------------------------------

-- Tour 1 / Sprint 100m (lower time is better)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 1, 1, 13.21),
    (1, 1, 2, 14.02),
    (1, 1, 3, 12.88),
    (1, 1, 4, 13.75),
    (1, 1, 5, 13.90),
    (1, 1, 6, 12.70),
    (1, 1, 7, 13.10),
    (1, 1, 8, 14.50),
    (1, 1, 9, 13.65);

-- Tour 1 / Long Jump (meters)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 2, 1, 5.10),
    (1, 2, 2, 4.85),
    (1, 2, 3, 5.55),
    (1, 2, 4, 5.00),
    (1, 2, 5, 4.95),
    (1, 2, 6, 5.70),
    (1, 2, 7, 5.15),
    (1, 2, 8, 4.60),
    (1, 2, 9, 5.05);

-- Tour 1 / Push-ups (reps)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (1, 3, 1, 45),
    (1, 3, 2, 38),
    (1, 3, 3, 52),
    (1, 3, 4, 41),
    (1, 3, 5, 40),
    (1, 3, 6, 55),
    (1, 3, 7, 46),
    (1, 3, 8, 33),
    (1, 3, 9, 44);

-- Tour 2 participants: crew 4 (persons 10, 11)
-- Tour 2 / Sprint 100m
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (2, 1, 10, 13.95),
    (2, 1, 11, 14.20);

-- Tour 2 / Swim 50m (seconds)
INSERT INTO
    results (
        tour_id,
        sport_id,
        person_id,
        score
    )
VALUES (2, 4, 10, 36.50),
    (2, 4, 11, 38.10);

------------------------------------------------------------
-- Fix sequences to max(id)
------------------------------------------------------------
SELECT setval(
        pg_get_serial_sequence('users', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM users
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('crews', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM crews
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('persons', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM persons
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('sports', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM sports
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('templates', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM templates
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('tours', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM tours
            ), 1
        ), true
    );

SELECT setval(
        pg_get_serial_sequence('results', 'id'), COALESCE(
            (
                SELECT MAX(id)
                FROM results
            ), 1
        ), true
    );

COMMIT;