-- This is the source of truth for table creation or regeneration 
-- within the LangOps database which the API will query.

CREATE TABLE langops_products (
    -- LangOpsProduct fields
    id              TEXT PRIMARY KEY,
    date_created    TIMESTAMPTZ NOT NULL,

    -- TrelloData fields
    trello_id               TEXT,
    trello_url              TEXT,
    trello_title            TEXT,
    trello_product_code     TEXT,
    trello_target_language  TEXT,
    trello_due_date         TIMESTAMPTZ,
    trello_date_published   TIMESTAMPTZ,
    trello_date_last_activity TIMESTAMPTZ,
    trello_media_groups     TEXT[],
    trello_editor_url       TEXT,
    trello_article_url      TEXT,
    trello_word_count       INTEGER,

    -- YouTubeData fields
    youtube_id               TEXT,
    youtube_localized_title  TEXT,
    youtube_url              TEXT,
    youtube_duration_seconds INTEGER,

    -- CrowdinData fields
    crowdin_id                  TEXT,
    crowdin_translation_progress FLOAT,
    crowdin_approval_progress   FLOAT,
    crowdin_url                 TEXT
);