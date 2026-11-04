CREATE TABLE IF NOT EXISTS project_jobs (
    job_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS project_jobs_project ON project_jobs(project_id);
