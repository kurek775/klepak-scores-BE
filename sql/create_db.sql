BEGIN;

-- ========= TEMPLATES =========
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    "bgImage" BYTEA,
    font BYTEA,
    "textPosition" VARCHAR
);

-- ========= TOURS =========
CREATE TABLE IF NOT EXISTS tours (
    id SERIAL PRIMARY KEY,
    year INTEGER,
    part VARCHAR, -- e.g. "spring", "summer"
    theme VARCHAR,
    template_id INTEGER,
    FOREIGN KEY (template_id) REFERENCES templates (id) ON DELETE SET NULL
);

-- ========= CREWS (linked to tours) =========
CREATE TABLE IF NOT EXISTS crews (
    id SERIAL PRIMARY KEY,
    number INTEGER,
    tour_id INTEGER,
    CONSTRAINT fk_crews_tour FOREIGN KEY (tour_id) REFERENCES tours (id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- For composite FK from users(tour_id, crew_id) -> crews(tour_id, id)
CREATE UNIQUE INDEX IF NOT EXISTS uq_crews_tour_id_id ON crews (tour_id, id);

CREATE INDEX IF NOT EXISTS idx_crews_tour_id ON crews (tour_id);

-- ========= USERS =========
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    sub VARCHAR(255) UNIQUE, -- OIDC subject (string)
    email VARCHAR UNIQUE NOT NULL,
    name VARCHAR,
    picture_url TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP,
    tour_id INTEGER,
    crew_id INTEGER,
    CONSTRAINT fk_users_tour FOREIGN KEY (tour_id) REFERENCES tours (id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_users_crew FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE SET NULL ON UPDATE CASCADE,
    -- Ensure crew belongs to the same tour as user
    CONSTRAINT fk_users_crew_in_tour FOREIGN KEY (tour_id, crew_id) REFERENCES crews (tour_id, id) ON DELETE SET NULL ON UPDATE CASCADE,
    -- If crew is set, tour must be set
    CONSTRAINT chk_users_crew_requires_tour CHECK (
        crew_id IS NULL
        OR tour_id IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_users_tour_id ON users (tour_id);

CREATE INDEX IF NOT EXISTS idx_users_crew_id ON users (crew_id);

-- ========= PERSONS (members of crews, not app users) =========
CREATE TABLE IF NOT EXISTS persons (
    id SERIAL PRIMARY KEY,
    name VARCHAR,
    crew_id INTEGER,
    FOREIGN KEY (crew_id) REFERENCES crews (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_persons_crew_id ON persons (crew_id);

-- ========= SPORTS =========
CREATE TABLE IF NOT EXISTS sports (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    metric VARCHAR
);

ALTER TABLE sports ADD CONSTRAINT uq_sports_name UNIQUE (name);

-- ========= TOUR_SPORTS (m:n tour ↔ sport) =========
CREATE TABLE IF NOT EXISTS tour_sports (
    tour_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    position INTEGER, -- order within tour (optional)
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (tour_id, sport_id),
    FOREIGN KEY (tour_id) REFERENCES tours (id) ON DELETE CASCADE,
    FOREIGN KEY (sport_id) REFERENCES sports (id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_tour_sports_tour ON tour_sports (tour_id);

CREATE INDEX IF NOT EXISTS idx_tour_sports_sport ON tour_sports (sport_id);

-- ========= RESULTS (by person within a concrete tour/sport) =========
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    tour_id INTEGER NOT NULL,
    sport_id INTEGER NOT NULL,
    person_id INTEGER NOT NULL,
    score DOUBLE PRECISION,
    -- Ensure (tour_id, sport_id) is valid for the tour:
    FOREIGN KEY (tour_id, sport_id) REFERENCES tour_sports (tour_id, sport_id) ON DELETE CASCADE,
    FOREIGN KEY (person_id) REFERENCES persons (id) ON DELETE CASCADE,
    UNIQUE (tour_id, sport_id, person_id)
);

CREATE INDEX IF NOT EXISTS idx_results_person ON results (person_id);

CREATE INDEX IF NOT EXISTS idx_results_tour_sport ON results (tour_id, sport_id);

COMMIT;