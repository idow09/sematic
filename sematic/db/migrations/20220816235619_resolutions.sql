-- migrate:up

CREATE TABLE resolutions (
    root_id TEXT NOT NULL,
    status TEXT NOT NULL,
    is_detached INTEGER NOT NULL,

    PRIMARY KEY (root_id)
);

INSERT INTO resolutions (root_id, status, is_detached)
SELECT id, 'COMPLETE', 1 FROM runs
WHERE parent_id is NULL;

-- migrate:down

DROP TABLE resolutions;
