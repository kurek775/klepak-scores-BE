-- Insert mock data
INSERT INTO crews (leaders, number, password) VALUES
    ('{"Alice", "Bob"}', 1, 'pass123'),
    ('{"Carol", "Dave"}', 2, 'secure456');

INSERT INTO persons (name, crew_id, category) VALUES
    ('John Doe', 1, 'A'),
    ('Jane Smith', 1, 'B'),
    ('Mark Taylor', 2, 'A'),
    ('Lucy Brown', 2, 'C');

INSERT INTO sports (name, metric) VALUES
    ('Basketball', 'Points'),
    ('Soccer', 'Goals'),
    ('Swimming', 'Seconds');

INSERT INTO results (sport_id, person_id, score) VALUES
    (1, 1, 15.5),
    (2, 2, 3.0),
    (3, 3, 120.7),
    (1, 4, 20.1);

INSERT INTO templates (bgImage, font, textPosition) VALUES
    (NULL, NULL, 'center'),
    (NULL, NULL, 'left');

INSERT INTO tours (year, part, theme) VALUES
    (2024, 'Summer', 'Adventure'),
    (2024, 'Winter', 'Mystery');
