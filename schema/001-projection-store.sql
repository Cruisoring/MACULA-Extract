PRAGMA application_id = 1297428784;
PRAGMA user_version = 1;

CREATE TABLE projection_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    store_protocol TEXT NOT NULL,
    ddl_sha256 TEXT NOT NULL
) STRICT;

CREATE TABLE candidate (
    candidate_id TEXT PRIMARY KEY NOT NULL CHECK (
        length(candidate_id) = 71 AND substr(candidate_id, 1, 7) = 'sha256:'
        AND substr(candidate_id, 8) NOT GLOB '*[^0-9a-f]*'
    ),
    record_json TEXT NOT NULL CHECK (json_valid(record_json))
) STRICT;

CREATE TABLE evaluation (
    evaluation_id TEXT PRIMARY KEY NOT NULL CHECK (
        length(evaluation_id) = 76 AND substr(evaluation_id, 1, 12) = 'eval-sha256:'
        AND substr(evaluation_id, 13) NOT GLOB '*[^0-9a-f]*'
    ),
    candidate_id TEXT NOT NULL REFERENCES candidate(candidate_id),
    evaluator_label TEXT NOT NULL,
    event_key TEXT NOT NULL,
    supersedes TEXT REFERENCES evaluation(evaluation_id),
    record_json TEXT NOT NULL CHECK (json_valid(record_json)),
    UNIQUE (evaluator_label, event_key),
    CHECK (supersedes IS NULL OR supersedes <> evaluation_id)
) STRICT;

CREATE TRIGGER metadata_no_insert BEFORE INSERT ON projection_metadata
WHEN EXISTS (SELECT 1 FROM projection_metadata)
BEGIN SELECT RAISE(ABORT, 'projection metadata is immutable'); END;
CREATE TRIGGER metadata_no_update BEFORE UPDATE ON projection_metadata
BEGIN SELECT RAISE(ABORT, 'projection metadata is immutable'); END;
CREATE TRIGGER metadata_no_delete BEFORE DELETE ON projection_metadata
BEGIN SELECT RAISE(ABORT, 'projection metadata is immutable'); END;

CREATE TRIGGER candidate_no_replace BEFORE INSERT ON candidate
WHEN EXISTS (SELECT 1 FROM candidate WHERE candidate_id = NEW.candidate_id)
BEGIN SELECT RAISE(ABORT, 'candidate identity already exists'); END;
CREATE TRIGGER candidate_no_update BEFORE UPDATE ON candidate
BEGIN SELECT RAISE(ABORT, 'candidate records are append-only'); END;
CREATE TRIGGER candidate_no_delete BEFORE DELETE ON candidate
BEGIN SELECT RAISE(ABORT, 'candidate records are append-only'); END;

CREATE TRIGGER evaluation_no_replace BEFORE INSERT ON evaluation
WHEN EXISTS (
    SELECT 1 FROM evaluation WHERE evaluation_id = NEW.evaluation_id
    OR (evaluator_label = NEW.evaluator_label AND event_key = NEW.event_key)
)
BEGIN SELECT RAISE(ABORT, 'evaluation identity or human event already exists'); END;
CREATE TRIGGER evaluation_no_update BEFORE UPDATE ON evaluation
BEGIN SELECT RAISE(ABORT, 'evaluation records are append-only'); END;
CREATE TRIGGER evaluation_no_delete BEFORE DELETE ON evaluation
BEGIN SELECT RAISE(ABORT, 'evaluation records are append-only'); END;
