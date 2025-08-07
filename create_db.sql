-- Authenticated users: Admins and Leaders (login via Google OAuth)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    picture_url TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Crews (no login, no password needed)
CREATE TABLE crews ( id SERIAL PRIMARY KEY, number INTEGER );

-- Many-to-many relation: which users are leaders of which crews
CREATE TABLE crew_leaders (
    crew_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (crew_id, user_id),
    FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Persons: basic non-logged-in users assigned to a crew
CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    crew_id INTEGER,
    FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE SET NULL
);

-- Sports catalog
CREATE TABLE sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    metric VARCHAR
);

-- Results of persons in sports
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    sport_id INTEGER,
    person_id INTEGER,
    score FLOAT,
    FOREIGN KEY (sport_id) REFERENCES sports (id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE
);

-- Tour metadata
CREATE TABLE tours (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    part VARCHAR,
    theme VARCHAR
);

-- Template settings (background, font, etc.)
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    bgImage BYTEA,
    font BYTEA,
    textPosition VARCHAR
);

-- Optional link: each tour references a template by ID
ALTER TABLE tours
ADD CONSTRAINT fk_templates FOREIGN KEY (id) REFERENCES templates (id);