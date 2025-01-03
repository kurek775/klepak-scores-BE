-- Create tables
CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    crew_id INTEGER,
    category VARCHAR
);

CREATE TABLE crews (
    id SERIAL PRIMARY KEY,
    leaders VARCHAR[],
    number INTEGER,
    password VARCHAR
);

CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    sport_id INTEGER,
    person_id INTEGER,
    score FLOAT
);

CREATE TABLE sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    metric VARCHAR
);

CREATE TABLE tours (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    part VARCHAR,
    theme VARCHAR
);

CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    bgImage BYTEA,
    font BYTEA,
    textPosition VARCHAR
);

-- Add foreign key constraints AFTER all tables are created
ALTER TABLE persons
ADD CONSTRAINT fk_crews FOREIGN KEY (crew_id) REFERENCES crews (id);

ALTER TABLE results
ADD CONSTRAINT fk_persons FOREIGN KEY (person_id) REFERENCES persons (id);

ALTER TABLE results
ADD CONSTRAINT fk_sports FOREIGN KEY (sport_id) REFERENCES sports (id);

ALTER TABLE tours
ADD CONSTRAINT fk_templates FOREIGN KEY (id) REFERENCES templates (id);
