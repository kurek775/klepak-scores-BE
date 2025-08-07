-- USERS (admin and leaders)
INSERT INTO
    users (
        email,
        name,
        picture_url,
        is_admin
    )
VALUES (
        'admin@example.com',
        'Alice Admin',
        'https://example.com/alice.jpg',
        TRUE
    ),
    (
        'leader1@example.com',
        'Bob Leader',
        'https://example.com/bob.jpg',
        FALSE
    ),
    (
        'leader2@example.com',
        'Clara Leader',
        'https://example.com/clara.jpg',
        FALSE
    );

-- CREWS
INSERT INTO crews (number) VALUES (101), (102);

-- CREW_LEADERS (assign leaders to crews)
INSERT INTO
    crew_leaders (crew_id, user_id)
VALUES (1, 2), -- Bob is leader of crew 101
    (2, 3);
-- Clara is leader of crew 102

-- PERSONS (non-login users assigned to crews)
INSERT INTO
    persons (name, crew_id)
VALUES ('Tom Basic', 1),
    ('Jerry Basic', 1),
    ('Anna Basic', 2),
    ('Mike Basic', 2);

-- SPORTS
INSERT INTO
    sports (name, metric)
VALUES ('Running', 'time'),
    ('Swimming', 'distance');

-- RESULTS (some sport scores for persons)
INSERT INTO
    results (sport_id, person_id, score)
VALUES (1, 1, 12.5), -- Tom Basic ran in 12.5 seconds
    (2, 2, 100.0), -- Jerry swam 100m
    (1, 3, 13.2), -- Anna ran
    (2, 4, 90.0);
-- Mike swam

-- TEMPLATES
INSERT INTO
    templates (bgImage, font, textPosition)
VALUES (
        E'\\xDEADBEEF',
        E'\\xF00DBABE',
        'top-left'
    );

-- TOURS
INSERT INTO
    tours (id, year, part, theme)
VALUES (
        1,
        2025,
        'Spring',
        'Adventure Time'
    );