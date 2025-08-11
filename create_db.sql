-- Users (Admin/Leader)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    picture_url TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

-- Crews
CREATE TABLE crews ( id SERIAL PRIMARY KEY, number INTEGER );

-- Many-to-many: which users are leaders of which crews
CREATE TABLE crew_leaders (
    crew_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    PRIMARY KEY (crew_id, user_id),
    FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Persons (non-logged users) assigned to a crew
CREATE TABLE persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    crew_id INTEGER,
    FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE SET NULL
);

-- Sports catalog
CREATE TABLE sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    metric VARCHAR -- e.g. "time", "points", "distance"
);

-- Templates (background, font, etc.)
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    bgImage BYTEA,
    font BYTEA,
    textPosition VARCHAR
);

-- Tours
CREATE TABLE tours (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    part VARCHAR, -- e.g. "spring", "summer"
    theme VARCHAR,
    template_id INTEGER,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE SET NULL
);

-- >>> m:n vazba: každá tour má N sportů <<<
CREATE TABLE tour_sports (
    tour_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    position INTEGER, -- pořadí sportu v rámci tour (volitelné)
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (tour_id, sport_id),
    FOREIGN KEY (tour_id) REFERENCES tours (id) ON DELETE CASCADE,
    FOREIGN KEY (sport_id) REFERENCES sports (id) ON DELETE RESTRICT
);

-- Results of persons in sports WITHIN a concrete tour
CREATE TABLE results (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    score DOUBLE PRECISION,
    -- Zajistí, že výsledek existuje jen pro sport, který do tour patří:
    FOREIGN KEY (tour_id, sport_id) REFERENCES tour_sports (tour_id, sport_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE,
    -- Každý člověk má max. jeden výsledek pro danou kombinaci (tour × sport)
    UNIQUE (tour_id, sport_id, person_id)
);

-- Užitečné indexy
CREATE INDEX idx_persons_crew_id ON persons (crew_id);

CREATE INDEX idx_results_person ON results (person_id);

CREATE INDEX idx_results_tour_sport ON results (tour_id, sport_id);

CREATE INDEX idx_tour_sports_tour ON tour_sports (tour_id);

CREATE INDEX idx_tour_sports_sport ON tour_sports (sport_id);

ALTER TABLE sports ADD CONSTRAINT uq_sports_name UNIQUE (name);