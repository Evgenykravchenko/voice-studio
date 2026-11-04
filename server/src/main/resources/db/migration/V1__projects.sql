CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    title TEXT NOT NULL,
    scene_count INTEGER NOT NULL,
    document TEXT NOT NULL,
    create_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS projects_updated ON projects(updated_at DESC, id);
