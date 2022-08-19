-- migrate:up

ALTER TABLE runs ADD COLUMN external_jobs_json_encodable JSONB;

-- migrate:down

ALTER TABLE runs DROP COLUMN external_jobs_json_encodable;
