-- This is the source of truth for table creation or regeneration. 

CREATE TABLE langops_products (
    -- LangOpsProduct fields
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_created    TIMESTAMPTZ NOT NULL,
    date_deleted    TIMESTAMPTZ,
    media_groups    TEXT[] NOT NULL,
    product_status  TEXT NOT NULL,

    -- TrelloData fields
    trello_id               TEXT UNIQUE NOT NULL,
    trello_url              TEXT NOT NULL,
    trello_title            TEXT NOT NULL,
    trello_localized_title  TEXT,
    trello_product_code     TEXT,
    trello_target_language  TEXT,
    trello_due_date         TIMESTAMPTZ,
    trello_date_published   TIMESTAMPTZ,
    trello_date_last_activity TIMESTAMPTZ,
    trello_date_archived    TIMESTAMPTZ,
    trello_editor_url       TEXT,
    trello_article_url      TEXT,
    trello_word_count       INTEGER,

    -- YouTubeData fields
    youtube_id               TEXT,
    youtube_localized_title  TEXT,
    youtube_url              TEXT,
    youtube_duration_seconds INTEGER,

    -- CrowdinData fields
    crowdin_file_id                 INTEGER,
    crowdin_project_id              INTEGER,
    crowdin_translation_progress    FLOAT,
    crowdin_approval_progress       FLOAT,
    crowdin_url                     TEXT
);

CREATE TABLE webhook_failures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_created    TIMESTAMPTZ,
    status_code     TEXT,
    data            JSONB NOT NULL
);