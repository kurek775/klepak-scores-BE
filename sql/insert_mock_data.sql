ROLLBACK;

BEGIN;

-- Wipe current data (safe to re-run)
TRUNCATE TABLE results,
tour_sports,
tours,
templates,
sports,
persons,
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
-- Crews (linked to tours)
------------------------------------------------------------
INSERT INTO
    crews (id, number, tour_id)
VALUES (1, 1, 1), -- Tour 1
    (2, 2, 1), -- Tour 1
    (3, 3, 1), -- Tour 1
    (4, 1, 2);
-- Tour 2

------------------------------------------------------------
-- Users
-- sub is VARCHAR(255); if crew_id is set, tour_id must match that crew's tour (enforced by composite FK)
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
        last_login_at,
        tour_id,
        crew_id
    )
VALUES (
        1,
        'sub-admin-001',
        'admin1@example.com',
        'Alice Admin',
        NULL,
        TRUE,
        NOW() - INTERVAL '20 days',
        NOW() - INTERVAL '1 day',
        NULL,
        NULL
    ),
    (
        2,
        'sub-leader-001',
        'bob@example.com',
        'Bob Leader',
        NULL,
        FALSE,
        NOW() - INTERVAL '18 days',
        NOW() - INTERVAL '2 days',
        1,
        1
    ),
    (
        3,
        'sub-leader-002',
        'carol@example.com',
        'Carol Lead',
        NULL,
        FALSE,
        NOW() - INTERVAL '17 days',
        NOW() - INTERVAL '2 days',
        1,
        1
    ),
    (
        4,
        'sub-leader-003',
        'dave@example.com',
        'Dave Lead',
        NULL,
        FALSE,
        NOW() - INTERVAL '16 days',
        NOW() - INTERVAL '3 days',
        1,
        2
    ),
    (
        5,
        'sub-leader-004',
        'eve@example.com',
        'Eve Lead',
        NULL,
        FALSE,
        NOW() - INTERVAL '15 days',
        NOW() - INTERVAL '3 days',
        1,
        3
    ),
    (
        6,
        'sub-user-001',
        'frank@example.com',
        'Frank User',
        NULL,
        FALSE,
        NOW() - INTERVAL '12 days',
        NULL,
        1,
        NULL
    ),
    (
        7,
        'sub-user-002',
        'grace@example.com',
        'Grace User',
        NULL,
        FALSE,
        NOW() - INTERVAL '11 days',
        NULL,
        NULL,
        NULL
    ),
    (
        8,
        'sub-user-003',
        'heidi@example.com',
        'Heidi User',
        NULL,
        FALSE,
        NOW() - INTERVAL '10 days',
        NULL,
        2,
        4
    ),
    (
        9,
        'sub-user-004',
        'ivan@example.com',
        'Ivan User',
        NULL,
        FALSE,
        NOW() - INTERVAL '9 days',
        NULL,
        2,
        NULL
    );

------------------------------------------------------------
-- Persons (non-app users) assigned to crews
------------------------------------------------------------
INSERT INTO
    persons (id, name, crew_id)
VALUES
    -- Crew 1 (tour 1)
    (1, 'Paul', 1),
    (2, 'Nina', 1),
    (3, 'Oscar', 1),
    -- Crew 2 (tour 1)
    (4, 'Quinn', 2),
    (5, 'Rita', 2),
    (6, 'Sam', 2),
    -- Crew 3 (tour 1)
    (7, 'Tara', 3),
    (8, 'Uma', 3),
    (9, 'Victor', 3),
    -- Crew 4 (tour 2)
    (10, 'Wendy', 4),
    (11, 'Xavier', 4);

------------------------------------------------------------
-- Sports (unique names)
------------------------------------------------------------
INSERT INTO
    sports (id, name, metric)
VALUES (1, 'Sprint 100m', 'time'),
    (2, 'Long Jump', 'distance'),
    (3, 'Push-ups', 'reps'),
    (4, 'Swim 50m', 'time');

------------------------------------------------------------
-- Tour ↔ Sports mapping
-- Tour 1: Sprint, Long Jump, Push-ups
-- Tour 2: Sprint, Swim
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
-- Results: must reference valid (tour_id, sport_id) and persons
-- Use persons from crews belonging to the tour
------------------------------------------------------------

-- Tour 1 / Sprint 100m
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

-- Tour 1 / Long Jump
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

-- Tour 1 / Push-ups
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

-- Tour 2 / Swim 50m
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
-- Fix sequences to max(id) (helpful if you re-run seeds)
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