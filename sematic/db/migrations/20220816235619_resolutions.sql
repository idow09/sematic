-- migrate:up

CREATE TABLE resolutions (
    root_id TEXT NOT NULL,
    status TEXT NOT NULL,
    is_detached BOOLEAN NOT NULL,
    docker_image_uri TEXT,
    settings_env_vars JSONB NOT NULL,

    PRIMARY KEY (root_id)
);

INSERT INTO resolutions (root_id, status, is_detached, docker_image_uri, settings_env_vars)
SELECT id, 'COMPLETE', TRUE, NULL, '{}' FROM runs
WHERE parent_id is NULL;

-- migrate:down

DROP TABLE resolutions;
