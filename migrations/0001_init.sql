DROP TABLE IF EXISTS workouts;
DROP TABLE IF EXISTS exercises;
DROP TABLE IF EXISTS sets;
DROP TABLE IF EXISTS syncs;
DROP TABLE IF EXISTS workout_exercises;

CREATE TABLE IF NOT EXISTS workouts
(
    id      TEXT NOT NULL PRIMARY KEY,
    start   TEXT NOT NULL,
    "end"   TEXT,
    user_id TEXT NOT NULL,
    name    TEXT
);

CREATE TABLE IF NOT EXISTS exercises
(
    name             TEXT NOT NULL PRIMARY KEY,
    category         TEXT NOT NULL,
    target           TEXT NOT NULL,
    asset            TEXT,
    asset_width      INT,
    asset_height     INT,
    thumbnail        TEXT,
    thumbnail_width  INT,
    thumbnail_height INT,
    user_id          TEXT
);

CREATE TABLE IF NOT EXISTS syncs
(
    table_name TEXT NOT NULL PRIMARY KEY,
    synced_at  TEXT DEFAULT (datetime('now') || '+00:00')
);

CREATE TABLE IF NOT EXISTS workout_exercises
(
    workout_id     TEXT NOT NULL REFERENCES workouts (id) ON DELETE CASCADE,
    exercise_id    TEXT NOT NULL REFERENCES exercises (name) ON DELETE CASCADE,
    id             TEXT NOT NULL PRIMARY KEY,
    exercise_order INT
);

CREATE TABLE IF NOT EXISTS sets
(
    exercise_id TEXT    NOT NULL REFERENCES workout_exercises (id) ON DELETE CASCADE,
    id          TEXT    NOT NULL PRIMARY KEY,
    completed   INTEGER NOT NULL DEFAULT 0,
    weight      REAL,  -- kgs
    reps        INT,
    duration    REAL,  -- seconds
    distance    REAL   -- kilometers
);

DROP TABLE IF EXISTS templates;
CREATE TABLE IF NOT EXISTS templates
(
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT,
    user_id         TEXT,
    order_in_parent INTEGER,
    created_at      TEXT NOT NULL DEFAULT (datetime('now') || '+00:00')
);

DROP TABLE IF EXISTS template_exercises;
CREATE TABLE IF NOT EXISTS template_exercises
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES templates ON DELETE CASCADE,
    exercise_id TEXT    NOT NULL REFERENCES exercises ON DELETE CASCADE,
    description TEXT
);

CREATE INDEX IF NOT EXISTS user_idx ON templates (user_id);

DROP TABLE IF EXISTS exercise_details;
CREATE TABLE IF NOT EXISTS exercise_details
(
    exercise_name TEXT NOT NULL REFERENCES exercises ON DELETE CASCADE,
    user_id       TEXT NOT NULL,
    rest_timer    INTEGER,
    PRIMARY KEY (exercise_name, user_id)
);
