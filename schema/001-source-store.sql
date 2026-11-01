PRAGMA foreign_keys = ON;
PRAGMA recursive_triggers = ON;

CREATE TABLE schema_version (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    version INTEGER NOT NULL CHECK (version = 1),
    ddl_sha256 TEXT COLLATE BINARY NOT NULL,
    parser_contract_sha256 TEXT COLLATE BINARY NOT NULL,
    locator_contract_sha256 TEXT COLLATE BINARY NOT NULL
) STRICT;

CREATE TABLE dataset_snapshot (
    snapshot_id INTEGER PRIMARY KEY,
    source_family TEXT COLLATE BINARY NOT NULL CHECK (length(source_family) > 0),
    edition TEXT COLLATE BINARY NOT NULL CHECK (length(edition) > 0),
    repository_uri TEXT COLLATE BINARY NOT NULL CHECK (length(repository_uri) > 0),
    revision TEXT COLLATE BINARY NOT NULL
        CHECK (length(revision) IN (40, 64) AND revision NOT GLOB '*[^0-9a-f]*'),
    manifest_sha256 TEXT COLLATE BINARY NOT NULL
        CHECK (length(manifest_sha256) = 64 AND manifest_sha256 NOT GLOB '*[^0-9A-F]*'),
    UNIQUE (edition, repository_uri, revision, manifest_sha256)
) STRICT;

CREATE TABLE book (
    book_id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES dataset_snapshot(snapshot_id),
    source_book_code TEXT COLLATE BINARY NOT NULL CHECK (length(source_book_code) > 0),
    book_ordinal INTEGER NOT NULL CHECK (book_ordinal > 0),
    source_book_name TEXT COLLATE BINARY,
    UNIQUE (snapshot_id, source_book_code),
    UNIQUE (book_id, snapshot_id)
) STRICT;

CREATE TABLE source_file (
    file_id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL REFERENCES dataset_snapshot(snapshot_id),
    book_id INTEGER,
    relative_path TEXT COLLATE BINARY NOT NULL
        CHECK (length(relative_path) > 0 AND substr(relative_path, 1, 1) NOT IN ('/', '\')
            AND instr(relative_path, '\') = 0 AND instr(relative_path, ':') = 0
            AND relative_path NOT IN ('.', '..')
            AND relative_path NOT LIKE '../%' AND relative_path NOT LIKE '%/../%'
            AND relative_path NOT LIKE '%/..'),
    source_format TEXT COLLATE BINARY NOT NULL CHECK (length(source_format) > 0),
    original_bytes BLOB NOT NULL,
    sha256 TEXT COLLATE BINARY NOT NULL
        CHECK (length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9A-F]*'),
    byte_size INTEGER NOT NULL CHECK (byte_size >= 0 AND byte_size = length(original_bytes)),
    encoding_evidence TEXT COLLATE BINARY,
    FOREIGN KEY (book_id, snapshot_id) REFERENCES book(book_id, snapshot_id),
    UNIQUE (snapshot_id, relative_path),
    UNIQUE (file_id, book_id)
) STRICT;

CREATE INDEX source_file_checksum ON source_file(sha256);

CREATE TABLE xml_element (
    element_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES source_file(file_id),
    parent_element_id INTEGER CHECK (parent_element_id IS NULL OR parent_element_id <> element_id),
    namespace_uri TEXT COLLATE BINARY NOT NULL,
    local_name TEXT COLLATE BINARY NOT NULL CHECK (length(local_name) > 0),
    qualified_name TEXT COLLATE BINARY,
    prefix TEXT COLLATE BINARY,
    sibling_ordinal INTEGER NOT NULL CHECK (sibling_ordinal >= 0),
    locator_scheme TEXT COLLATE BINARY NOT NULL CHECK (locator_scheme = 'macula.xml-expanded-ordinal-path'),
    locator_version INTEGER NOT NULL CHECK (locator_version = 1),
    locator TEXT COLLATE BINARY NOT NULL
        CHECK (json_valid(locator) AND json_type(locator) = 'array' AND json_array_length(locator) > 0),
    diagnostic_line INTEGER CHECK (diagnostic_line > 0),
    diagnostic_column INTEGER CHECK (diagnostic_column > 0),
    CHECK ((qualified_name IS NULL AND prefix IS NULL)
        OR (qualified_name IS NOT NULL AND prefix IS NOT NULL
            AND qualified_name = CASE WHEN prefix = '' THEN local_name ELSE prefix || ':' || local_name END)),
    FOREIGN KEY (parent_element_id, file_id) REFERENCES xml_element(element_id, file_id),
    UNIQUE (element_id, file_id),
    UNIQUE (file_id, parent_element_id, sibling_ordinal),
    UNIQUE (file_id, locator_scheme, locator_version, locator)
) STRICT;

CREATE UNIQUE INDEX xml_document_root ON xml_element(file_id) WHERE parent_element_id IS NULL;
CREATE INDEX xml_element_parent ON xml_element(parent_element_id, sibling_ordinal);

CREATE TABLE xml_attribute (
    attribute_id INTEGER PRIMARY KEY,
    element_id INTEGER NOT NULL REFERENCES xml_element(element_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    namespace_uri TEXT COLLATE BINARY NOT NULL,
    local_name TEXT COLLATE BINARY NOT NULL CHECK (length(local_name) > 0),
    qualified_name TEXT COLLATE BINARY,
    prefix TEXT COLLATE BINARY,
    value TEXT COLLATE BINARY NOT NULL,
    CHECK ((qualified_name IS NULL AND prefix IS NULL)
        OR (qualified_name IS NOT NULL AND prefix IS NOT NULL
            AND qualified_name = CASE WHEN prefix = '' THEN local_name ELSE prefix || ':' || local_name END)),
    UNIQUE (element_id, ordinal),
    UNIQUE (element_id, namespace_uri, local_name)
) STRICT;

CREATE INDEX xml_attribute_name ON xml_attribute(namespace_uri, local_name, element_id);

CREATE TABLE xml_content (
    content_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES source_file(file_id),
    owner_element_id INTEGER,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    kind TEXT COLLATE BINARY NOT NULL CHECK (kind IN ('element', 'text', 'cdata', 'comment', 'pi')),
    child_element_id INTEGER,
    value TEXT COLLATE BINARY,
    pi_target TEXT COLLATE BINARY,
    CHECK ((kind = 'element' AND child_element_id IS NOT NULL AND value IS NULL AND pi_target IS NULL)
        OR (kind IN ('text', 'cdata', 'comment') AND child_element_id IS NULL AND value IS NOT NULL AND pi_target IS NULL)
        OR (kind = 'pi' AND child_element_id IS NULL AND value IS NOT NULL
            AND pi_target IS NOT NULL AND length(pi_target) > 0)),
    CHECK (owner_element_id IS NOT NULL OR kind <> 'cdata'),
    CHECK (owner_element_id IS NOT NULL OR kind <> 'text'
        OR trim(value, char(9) || char(10) || char(13) || ' ') = ''),
    FOREIGN KEY (owner_element_id, file_id) REFERENCES xml_element(element_id, file_id),
    FOREIGN KEY (child_element_id, file_id) REFERENCES xml_element(element_id, file_id),
    UNIQUE (owner_element_id, ordinal),
    UNIQUE (child_element_id)
) STRICT;

CREATE UNIQUE INDEX xml_document_content ON xml_content(file_id, ordinal) WHERE owner_element_id IS NULL;
CREATE INDEX xml_content_owner ON xml_content(owner_element_id, ordinal);

CREATE TABLE sentence (
    sentence_id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    element_id INTEGER NOT NULL UNIQUE,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    ref_raw TEXT COLLATE BINARY,
    FOREIGN KEY (file_id, book_id) REFERENCES source_file(file_id, book_id),
    FOREIGN KEY (element_id, file_id) REFERENCES xml_element(element_id, file_id),
    UNIQUE (file_id, ordinal)
) STRICT;

CREATE INDEX sentence_ref ON sentence(file_id, ref_raw);

CREATE TABLE tree (
    tree_id INTEGER PRIMARY KEY,
    sentence_id INTEGER NOT NULL REFERENCES sentence(sentence_id),
    element_id INTEGER NOT NULL UNIQUE REFERENCES xml_element(element_id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    UNIQUE (sentence_id, ordinal)
) STRICT;

CREATE TABLE syntax_node (
    node_id INTEGER PRIMARY KEY,
    tree_id INTEGER NOT NULL REFERENCES tree(tree_id),
    element_id INTEGER NOT NULL UNIQUE REFERENCES xml_element(element_id),
    parent_node_id INTEGER CHECK (parent_node_id IS NULL OR parent_node_id <> node_id),
    sibling_ordinal INTEGER NOT NULL CHECK (sibling_ordinal >= 0),
    upstream_node_id TEXT COLLATE BINARY,
    id_raw TEXT COLLATE BINARY,
    cat TEXT COLLATE BINARY,
    rule TEXT COLLATE BINARY,
    cl_type TEXT COLLATE BINARY,
    start_raw TEXT COLLATE BINARY,
    end_raw TEXT COLLATE BINARY,
    head_raw TEXT COLLATE BINARY,
    length_raw TEXT COLLATE BINARY,
    FOREIGN KEY (parent_node_id, tree_id) REFERENCES syntax_node(node_id, tree_id),
    UNIQUE (node_id, tree_id),
    UNIQUE (tree_id, parent_node_id, sibling_ordinal)
) STRICT;

CREATE UNIQUE INDEX syntax_root_order ON syntax_node(tree_id, sibling_ordinal) WHERE parent_node_id IS NULL;
CREATE INDEX syntax_node_upstream ON syntax_node(tree_id, upstream_node_id);

CREATE TABLE token (
    token_id INTEGER PRIMARY KEY,
    node_id INTEGER NOT NULL UNIQUE,
    tree_id INTEGER NOT NULL REFERENCES tree(tree_id),
    book_id INTEGER NOT NULL REFERENCES book(book_id),
    tree_leaf_ordinal INTEGER NOT NULL CHECK (tree_leaf_ordinal >= 0),
    canonical_ordinal INTEGER NOT NULL CHECK (canonical_ordinal >= 0),
    chapter INTEGER NOT NULL CHECK (chapter > 0),
    verse INTEGER NOT NULL CHECK (verse > 0),
    verse_token_ordinal INTEGER NOT NULL CHECK (verse_token_ordinal > 0),
    xml_id TEXT COLLATE BINARY,
    morph_id TEXT COLLATE BINARY,
    ref_raw TEXT COLLATE BINARY,
    source_direct_text TEXT COLLATE BINARY NOT NULL,
    unicode_raw TEXT COLLATE BINARY,
    normalized_form TEXT COLLATE BINARY,
    unicode_lemma TEXT COLLATE BINARY,
    language_raw TEXT COLLATE BINARY,
    case_raw TEXT COLLATE BINARY,
    gender_raw TEXT COLLATE BINARY,
    number_raw TEXT COLLATE BINARY,
    person_raw TEXT COLLATE BINARY,
    tense_raw TEXT COLLATE BINARY,
    voice_raw TEXT COLLATE BINARY,
    mood_raw TEXT COLLATE BINARY,
    type_raw TEXT COLLATE BINARY,
    degree_raw TEXT COLLATE BINARY,
    has_det_raw TEXT COLLATE BINARY,
    functional_tag TEXT COLLATE BINARY,
    formal_tag TEXT COLLATE BINARY,
    strong_number TEXT COLLATE BINARY,
    english TEXT COLLATE BINARY,
    mandarin TEXT COLLATE BINARY,
    gloss TEXT COLLATE BINARY,
    lex_domain_raw TEXT COLLATE BINARY,
    ln_raw TEXT COLLATE BINARY,
    frame_raw TEXT COLLATE BINARY,
    referent_raw TEXT COLLATE BINARY,
    subject_referent_raw TEXT COLLATE BINARY,
    notes_raw TEXT COLLATE BINARY,
    lowfat_exception_raw TEXT COLLATE BINARY,
    status_raw TEXT COLLATE BINARY,
    FOREIGN KEY (node_id, tree_id) REFERENCES syntax_node(node_id, tree_id),
    UNIQUE (token_id, tree_id),
    UNIQUE (tree_id, tree_leaf_ordinal),
    UNIQUE (tree_id, canonical_ordinal)
) STRICT;

CREATE INDEX token_scripture ON token(book_id, chapter, verse, verse_token_ordinal);
CREATE INDEX token_xml_id ON token(tree_id, xml_id);
CREATE INDEX token_morph_id ON token(tree_id, morph_id);
CREATE INDEX token_lemma ON token(unicode_lemma);

CREATE TABLE node_token_membership (
    node_id INTEGER NOT NULL,
    token_id INTEGER NOT NULL,
    tree_id INTEGER NOT NULL,
    PRIMARY KEY (node_id, token_id),
    FOREIGN KEY (node_id, tree_id) REFERENCES syntax_node(node_id, tree_id),
    FOREIGN KEY (token_id, tree_id) REFERENCES token(token_id, tree_id)
) STRICT;

CREATE INDEX membership_token ON node_token_membership(token_id, node_id);

CREATE VIEW expected_node_token_membership AS
WITH RECURSIVE ancestors(node_id, token_id, tree_id, parent_node_id) AS (
    SELECT n.node_id, t.token_id, t.tree_id, n.parent_node_id
    FROM token t JOIN syntax_node n ON n.node_id = t.node_id
    UNION
    SELECT n.node_id, a.token_id, a.tree_id, n.parent_node_id
    FROM ancestors a JOIN syntax_node n ON n.node_id = a.parent_node_id AND n.tree_id = a.tree_id
)
SELECT node_id, token_id, tree_id FROM ancestors;

CREATE TRIGGER membership_ancestry BEFORE INSERT ON node_token_membership BEGIN
    SELECT RAISE(ABORT, 'membership requires an actual descendant leaf')
    WHERE NOT EXISTS (
        SELECT 1 FROM expected_node_token_membership
        WHERE node_id = NEW.node_id AND token_id = NEW.token_id AND tree_id = NEW.tree_id
    );
END;

CREATE TRIGGER membership_no_update BEFORE UPDATE ON node_token_membership BEGIN
    SELECT RAISE(ABORT, 'rebuild membership by delete and ancestry-derived insert');
END;

CREATE VIEW typed_attribute_mirror AS
SELECT 'sentence' AS record_kind, sentence_id AS record_id, element_id,
    'ref_raw' AS column_name, '' AS namespace_uri, 'ref' AS local_name, ref_raw AS mirror_value FROM sentence
UNION ALL SELECT 'syntax_node', node_id, element_id, 'upstream_node_id', '', 'nodeId', upstream_node_id FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'id_raw', '', 'Id', id_raw FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'cat', '', 'Cat', cat FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'rule', '', 'Rule', rule FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'cl_type', '', 'ClType', cl_type FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'start_raw', '', 'Start', start_raw FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'end_raw', '', 'End', end_raw FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'head_raw', '', 'Head', head_raw FROM syntax_node
UNION ALL SELECT 'syntax_node', node_id, element_id, 'length_raw', '', 'Length', length_raw FROM syntax_node
UNION ALL SELECT 'token', t.token_id, n.element_id, 'xml_id', 'http://www.w3.org/XML/1998/namespace', 'id', t.xml_id FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'morph_id', '', 'morphId', t.morph_id FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'ref_raw', '', 'ref', t.ref_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'unicode_raw', '', 'Unicode', t.unicode_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'normalized_form', '', 'NormalizedForm', t.normalized_form FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'unicode_lemma', '', 'UnicodeLemma', t.unicode_lemma FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'language_raw', '', 'Language', t.language_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'case_raw', '', 'Case', t.case_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'gender_raw', '', 'Gender', t.gender_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'number_raw', '', 'Number', t.number_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'person_raw', '', 'Person', t.person_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'tense_raw', '', 'Tense', t.tense_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'voice_raw', '', 'Voice', t.voice_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'mood_raw', '', 'Mood', t.mood_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'type_raw', '', 'Type', t.type_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'degree_raw', '', 'Degree', t.degree_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'has_det_raw', '', 'HasDet', t.has_det_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'functional_tag', '', 'FunctionalTag', t.functional_tag FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'formal_tag', '', 'FormalTag', t.formal_tag FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'strong_number', '', 'StrongNumber', t.strong_number FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'english', '', 'English', t.english FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'mandarin', '', 'Mandarin', t.mandarin FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'gloss', '', 'Gloss', t.gloss FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'lex_domain_raw', '', 'LexDomain', t.lex_domain_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'ln_raw', '', 'LN', t.ln_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'frame_raw', '', 'Frame', t.frame_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'referent_raw', '', 'Ref', t.referent_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'subject_referent_raw', '', 'SubjRef', t.subject_referent_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'notes_raw', '', 'Notes', t.notes_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'lowfat_exception_raw', '', 'LowfatException', t.lowfat_exception_raw FROM token t JOIN syntax_node n USING (node_id)
UNION ALL SELECT 'token', t.token_id, n.element_id, 'status_raw', '', 'status', t.status_raw FROM token t JOIN syntax_node n USING (node_id);

CREATE TRIGGER snapshot_no_update BEFORE UPDATE ON dataset_snapshot BEGIN SELECT RAISE(ABORT, 'immutable source snapshot'); END;
CREATE TRIGGER snapshot_no_delete BEFORE DELETE ON dataset_snapshot BEGIN SELECT RAISE(ABORT, 'immutable source snapshot'); END;
CREATE TRIGGER file_no_update BEFORE UPDATE ON source_file BEGIN SELECT RAISE(ABORT, 'immutable source archive'); END;
CREATE TRIGGER file_no_delete BEFORE DELETE ON source_file BEGIN SELECT RAISE(ABORT, 'immutable source archive'); END;
CREATE TRIGGER element_no_update BEFORE UPDATE ON xml_element BEGIN SELECT RAISE(ABORT, 'immutable XML occurrence'); END;
CREATE TRIGGER element_no_delete BEFORE DELETE ON xml_element BEGIN SELECT RAISE(ABORT, 'immutable XML occurrence'); END;
CREATE TRIGGER attribute_no_update BEFORE UPDATE ON xml_attribute BEGIN SELECT RAISE(ABORT, 'immutable XML attribute'); END;
CREATE TRIGGER attribute_no_delete BEFORE DELETE ON xml_attribute BEGIN SELECT RAISE(ABORT, 'immutable XML attribute'); END;
CREATE TRIGGER content_no_update BEFORE UPDATE ON xml_content BEGIN SELECT RAISE(ABORT, 'immutable XML content'); END;
CREATE TRIGGER content_no_delete BEFORE DELETE ON xml_content BEGIN SELECT RAISE(ABORT, 'immutable XML content'); END;
CREATE TRIGGER book_no_update BEFORE UPDATE ON book BEGIN SELECT RAISE(ABORT, 'immutable source book'); END;
CREATE TRIGGER book_no_delete BEFORE DELETE ON book BEGIN SELECT RAISE(ABORT, 'immutable source book'); END;
CREATE TRIGGER sentence_no_update BEFORE UPDATE ON sentence BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER sentence_no_delete BEFORE DELETE ON sentence BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER tree_no_update BEFORE UPDATE ON tree BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER tree_no_delete BEFORE DELETE ON tree BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER node_no_update BEFORE UPDATE ON syntax_node BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER node_no_delete BEFORE DELETE ON syntax_node BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER token_no_update BEFORE UPDATE ON token BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER token_no_delete BEFORE DELETE ON token BEGIN SELECT RAISE(ABORT, 'immutable source mirror'); END;
CREATE TRIGGER version_no_update BEFORE UPDATE ON schema_version BEGIN SELECT RAISE(ABORT, 'immutable schema identity'); END;
CREATE TRIGGER version_no_delete BEFORE DELETE ON schema_version BEGIN SELECT RAISE(ABORT, 'immutable schema identity'); END;
