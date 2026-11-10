-- Skema riwayat run AgentForge (SQLite).
-- Satu baris di runs untuk setiap eksekusi workflow, dan satu baris
-- di run_steps untuk setiap langkah agent di dalam run itu.

CREATE TABLE IF NOT EXISTS runs (
    run_id          TEXT PRIMARY KEY,
    workflow        TEXT NOT NULL,
    title           TEXT NOT NULL,
    status          TEXT NOT NULL,
    mode            TEXT NOT NULL,
    reviewer_score  INTEGER NOT NULL,
    revision_rounds INTEGER NOT NULL DEFAULT 0,
    total_tokens    INTEGER NOT NULL DEFAULT 0,
    total_cost_usd  REAL NOT NULL DEFAULT 0,
    final_output    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS run_steps (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id            TEXT NOT NULL REFERENCES runs(run_id),
    step_id           TEXT NOT NULL,
    agent             TEXT NOT NULL,
    action            TEXT NOT NULL,
    model             TEXT NOT NULL,
    mode              TEXT NOT NULL,
    prompt_tokens     INTEGER NOT NULL DEFAULT 0,
    completion_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd          REAL NOT NULL DEFAULT 0,
    status            TEXT NOT NULL,
    attempts          INTEGER NOT NULL DEFAULT 1,
    duration_ms       INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_run_steps_run ON run_steps(run_id);
